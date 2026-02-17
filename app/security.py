from __future__ import annotations

import hmac
import threading
import time
from typing import Callable

from fastapi import Header, Request

from app.errors import http_error


class InMemoryRateLimiter:
    """Simple fixed-window rate limiter keyed by client identity."""

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
            return count <= self.requests_per_minute


def build_api_key_dependency(config) -> Callable:
    expected_key = config.API_KEY or ""
    require_api_key = bool(config.REQUIRE_API_KEY)

    async def verify_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key")) -> None:
        if not require_api_key:
            return
        if not x_api_key or not hmac.compare_digest(x_api_key, expected_key):
            raise http_error(401, "UNAUTHORIZED", "Unauthorized")

    return verify_api_key


def build_rate_limit_dependency(config) -> Callable:
    limiter = InMemoryRateLimiter(config.RATE_LIMIT_PER_MINUTE)

    async def verify_rate_limit(request: Request) -> None:
        if not limiter.enabled:
            return

        client_host = request.client.host if request.client else "unknown"
        if not limiter.allow(client_host):
            raise http_error(429, "RATE_LIMITED", "Too Many Requests")

    return verify_rate_limit
