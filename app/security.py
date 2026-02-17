from __future__ import annotations

import hmac
import logging
import threading
import time
from ipaddress import ip_address, ip_network
from typing import Any, Callable

from fastapi import Header, Request

from app.errors import http_error
from app.security_jwt import (
    authorize_claims_for_request as _authorize_claims_for_request_impl,
    extract_values_set as _extract_values_set_impl,
    required_scope_for_method as _required_scope_for_method_impl,
    validate_jwt_hs256 as _validate_jwt_hs256_impl,
)

redis_module: Any | None
RedisBaseError: type[Exception]
RedisNoScriptError: type[Exception]

try:
    import redis as redis_module
    from redis.exceptions import NoScriptError as RedisNoScriptError
    from redis.exceptions import RedisError as RedisBaseError
except ImportError:  # pragma: no cover - exercised only when redis is unavailable.
    redis_module = None

    class _RedisBaseError(Exception):
        pass

    class _RedisNoScriptError(_RedisBaseError):
        pass

    RedisBaseError = _RedisBaseError
    RedisNoScriptError = _RedisNoScriptError

# Backward-compatible aliases for existing tests/runtime monkeypatch hooks.
redis = redis_module
RedisError = RedisBaseError
NoScriptError = RedisNoScriptError

logger = logging.getLogger("civic_archive.security")


class InMemoryRateLimiter:
    """Fixed-window limiter keyed by client identity."""

    def __init__(self, requests_per_minute: int) -> None:
        self.requests_per_minute = max(0, requests_per_minute)
        self._lock = threading.Lock()
        self._windows: dict[str, tuple[int, int]] = {}

    @property
    def enabled(self) -> bool:
        return self.requests_per_minute > 0

    def allow(self, key: str) -> bool:
        if not self.enabled:
            return True

        now_window = int(time.time() // 60)
        with self._lock:
            prev_window, count = self._windows.get(key, (now_window, 0))
            if prev_window != now_window:
                prev_window, count = now_window, 0

            count += 1
            self._windows[key] = (prev_window, count)
            self._prune(now_window)
            return count <= self.requests_per_minute

    def _prune(self, now_window: int) -> None:
        if len(self._windows) < 4096:
            return
        min_window = now_window - 1
        self._windows = {k: v for k, v in self._windows.items() if v[0] >= min_window}


class RedisRateLimiter:
    """Redis-backed fixed-window limiter keyed by client identity."""

    _WINDOW_SCRIPT = """
local current = redis.call("INCR", KEYS[1])
if current == 1 then
  redis.call("EXPIRE", KEYS[1], tonumber(ARGV[1]))
end
return current
"""

    def __init__(
        self,
        *,
        requests_per_minute: int,
        redis_url: str,
        key_prefix: str,
        window_seconds: int,
        failure_cooldown_seconds: int,
        fail_open: bool,
        monotonic: Callable[[], float] | None = None,
    ) -> None:
        self.requests_per_minute = max(0, requests_per_minute)
        self.key_prefix = key_prefix
        self.window_seconds = max(1, window_seconds)
        self.failure_cooldown_seconds = max(1, int(failure_cooldown_seconds))
        self.fail_open = bool(fail_open)
        self._monotonic = monotonic or time.monotonic
        self._script_sha: str | None = None
        self._client: Any | None = None
        self._degraded_until = 0.0

        if not self.enabled:
            return

        if redis is None:
            raise RuntimeError("redis package is required for RATE_LIMIT_BACKEND=redis.")

        self._client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
            decode_responses=False,
        )

    @property
    def enabled(self) -> bool:
        return self.requests_per_minute > 0

    def allow(self, key: str) -> bool:
        if not self.enabled:
            return True
        if self._client is None:
            return True

        now = self._monotonic()
        if now < self._degraded_until:
            return self.fail_open

        bucket = int(time.time() // 60)
        redis_key = f"{self.key_prefix}:{bucket}:{key}"

        try:
            current = int(self._eval_counter(redis_key))
        except RedisBaseError:
            self._degraded_until = now + float(self.failure_cooldown_seconds)
            logger.warning(
                "rate_limit_redis_error",
                extra={
                    "fail_open": self.fail_open,
                    "cooldown_seconds": self.failure_cooldown_seconds,
                },
            )
            return self.fail_open

        self._degraded_until = 0.0
        return current <= self.requests_per_minute

    def _eval_counter(self, redis_key: str) -> int:
        assert self._client is not None
        if self._script_sha is None:
            self._script_sha = self._client.script_load(self._WINDOW_SCRIPT)

        try:
            return int(self._client.evalsha(self._script_sha, 1, redis_key, self.window_seconds))
        except RedisNoScriptError:
            return int(self._client.eval(self._WINDOW_SCRIPT, 1, redis_key, self.window_seconds))


def _extract_values_set(claims: dict, *keys: str) -> set[str]:
    return _extract_values_set_impl(claims, *keys)


def _required_scope_for_method(config, method: str) -> str | None:
    return _required_scope_for_method_impl(config, method)


def _validate_jwt_hs256(token: str, config) -> dict:
    return _validate_jwt_hs256_impl(token, config)


def _authorize_claims_for_request(request: Request, claims: dict, config) -> None:
    _authorize_claims_for_request_impl(request, claims, config)


def _parse_trusted_proxy_networks(cidrs: list[str]) -> list:
    networks = []
    for raw in cidrs:
        value = (raw or "").strip()
        if not value:
            continue
        try:
            networks.append(ip_network(value, strict=False))
        except ValueError as exc:
            raise RuntimeError(f"Invalid TRUSTED_PROXY_CIDRS entry: {value}") from exc
    return networks


def _remote_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _is_trusted_proxy(remote_ip: str, trusted_proxy_networks: list) -> bool:
    if not trusted_proxy_networks:
        return False
    try:
        remote_addr = ip_address(remote_ip)
    except ValueError:
        return False
    return any(remote_addr in network for network in trusted_proxy_networks)


def _client_key(request: Request, *, trusted_proxy_networks: list) -> str:
    remote_ip = _remote_ip(request)
    if not _is_trusted_proxy(remote_ip, trusted_proxy_networks):
        return remote_ip

    forwarded_for = request.headers.get("X-Forwarded-For")
    if not forwarded_for:
        return remote_ip

    first_hop = forwarded_for.split(",")[0].strip()
    if not first_hop:
        return remote_ip
    try:
        ip_address(first_hop)
        return first_hop
    except ValueError:
        return remote_ip


def _build_rate_limiter(config):
    if config.rate_limit_backend == "redis":
        redis_url = (config.REDIS_URL or "").strip()
        if not redis_url:
            raise RuntimeError("RATE_LIMIT_BACKEND=redis requires REDIS_URL to be set.")
        return RedisRateLimiter(
            requests_per_minute=config.RATE_LIMIT_PER_MINUTE,
            redis_url=redis_url,
            key_prefix=config.RATE_LIMIT_REDIS_PREFIX,
            window_seconds=config.RATE_LIMIT_REDIS_WINDOW_SECONDS,
            failure_cooldown_seconds=config.RATE_LIMIT_REDIS_FAILURE_COOLDOWN_SECONDS,
            fail_open=config.RATE_LIMIT_FAIL_OPEN,
        )
    if config.rate_limit_backend == "memory":
        return InMemoryRateLimiter(config.RATE_LIMIT_PER_MINUTE)
    raise RuntimeError("RATE_LIMIT_BACKEND must be one of: memory, redis.")


def check_rate_limit_backend_health(config) -> tuple[bool, str | None]:
    backend = config.rate_limit_backend
    if backend == "memory":
        return True, "memory backend"

    if config.RATE_LIMIT_PER_MINUTE <= 0:
        return True, "rate limit disabled"

    redis_url = (config.REDIS_URL or "").strip()
    if not redis_url:
        return False, "REDIS_URL is not set"
    if redis is None:
        return False, "redis package is not available"

    try:
        client = redis.Redis.from_url(
            redis_url,
            socket_connect_timeout=0.2,
            socket_timeout=0.2,
            decode_responses=False,
        )
        client.ping()
        return True, None
    except RedisBaseError as exc:
        return False, str(exc)


def build_api_key_dependency(config) -> Callable:
    expected_key = config.API_KEY or ""
    require_api_key = bool(config.REQUIRE_API_KEY)

    async def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
        if not require_api_key:
            return
        if not x_api_key or not hmac.compare_digest(x_api_key, expected_key):
            raise http_error(401, "UNAUTHORIZED", "Unauthorized")

    return verify_api_key


def build_jwt_dependency(config) -> Callable:
    require_jwt = bool(config.REQUIRE_JWT)

    async def verify_jwt(
        request: Request,
        authorization: str | None = Header(default=None, alias="Authorization"),
    ) -> None:
        if not require_jwt:
            return

        if not authorization:
            raise http_error(401, "UNAUTHORIZED", "Unauthorized")
        scheme, _, value = authorization.partition(" ")
        token = value.strip()
        if scheme.lower() != "bearer" or not token:
            raise http_error(401, "UNAUTHORIZED", "Unauthorized")

        claims = _validate_jwt_hs256(token, config)
        _authorize_claims_for_request(request, claims, config)
        request.state.auth_claims = claims

    return verify_jwt


def build_rate_limit_dependency(config) -> Callable:
    limiter = _build_rate_limiter(config)
    trusted_proxy_networks = _parse_trusted_proxy_networks(config.trusted_proxy_cidrs_list)

    async def verify_rate_limit(request: Request) -> None:
        if not limiter.enabled:
            return
        if not limiter.allow(_client_key(request, trusted_proxy_networks=trusted_proxy_networks)):
            raise http_error(429, "RATE_LIMITED", "Too Many Requests")

    return verify_rate_limit
