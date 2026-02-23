import logging

import pytest
from conftest import build_test_config
from fastapi import FastAPI, HTTPException, Query
from fastapi.testclient import TestClient

import app.bootstrap.routes as bootstrap_routes_module
from app.bootstrap.exception_handlers import register_exception_handlers
from app.bootstrap.middleware import register_core_middleware
from app.bootstrap.routes import register_domain_routes
from app.bootstrap.system_routes import register_system_routes
from app.bootstrap.validation import validate_startup_config


def test_validation_module_rejects_invalid_rate_limit_backend():
    with pytest.raises(RuntimeError, match="RATE_LIMIT_BACKEND must be one of: memory, redis."):
        validate_startup_config(build_test_config(RATE_LIMIT_BACKEND="invalid"))


# --- P11-1: 메모리 레이트 리미터 다중 워커 안전성 ---

def _strict_base_config(**overrides):
    """strict mode에서 기존 검증을 통과하는 최소 유효 설정."""
    base = {
        "SECURITY_STRICT_MODE": True,
        "REQUIRE_API_KEY": True,
        "API_KEY": "valid-key-for-testing-purposes-only",
        "ALLOWED_HOSTS": "api.example.com",
        "CORS_ALLOW_ORIGINS": "https://app.example.com",
        "RATE_LIMIT_PER_MINUTE": 60,
        "RATE_LIMIT_BACKEND": "redis",
        "REDIS_URL": "redis://localhost:6379/0",
        "POSTGRES_PASSWORD": "secure-test-password-123",
    }
    base.update(overrides)
    return build_test_config(**base)


def test_validation_strict_mode_rejects_memory_backend_with_rate_limit():
    with pytest.raises(RuntimeError, match="RATE_LIMIT_BACKEND=redis"):
        validate_startup_config(_strict_base_config(RATE_LIMIT_BACKEND="memory"))


def test_validation_strict_mode_allows_redis_backend():
    # redis backend + strict mode — should not raise
    validate_startup_config(_strict_base_config())


def test_validation_strict_mode_allows_memory_backend_when_rate_limit_disabled():
    # memory backend is acceptable when rate limiting is off (RATE_LIMIT_PER_MINUTE=0)
    # strict mode requires RATE_LIMIT_PER_MINUTE > 0, so this combination itself
    # fails strict mode at the rate-limit check — not at the memory-backend check.
    with pytest.raises(RuntimeError, match="Strict security mode requires RATE_LIMIT_PER_MINUTE > 0"):
        validate_startup_config(
            _strict_base_config(RATE_LIMIT_BACKEND="memory", RATE_LIMIT_PER_MINUTE=0)
        )


def test_validation_non_strict_memory_backend_emits_warning(caplog):
    config = build_test_config(
        APP_ENV="staging",
        RATE_LIMIT_BACKEND="memory",
        RATE_LIMIT_PER_MINUTE=60,
    )
    with caplog.at_level(logging.WARNING, logger="civic_archive.validation"):
        validate_startup_config(config)
    messages = [r.getMessage() for r in caplog.records]
    assert "rate_limit_memory_backend_multi_worker_risk" in messages


def test_validation_non_strict_memory_backend_no_warning_when_rate_limit_disabled(caplog):
    config = build_test_config(
        APP_ENV="staging",
        RATE_LIMIT_BACKEND="memory",
        RATE_LIMIT_PER_MINUTE=0,  # rate limiting is off — warning must not fire
    )
    with caplog.at_level(logging.WARNING, logger="civic_archive.validation"):
        validate_startup_config(config)
    messages = [r.getMessage() for r in caplog.records]
    assert "rate_limit_memory_backend_multi_worker_risk" not in messages


# --- P11-2: 보안 기본값 시작 시 불변 검증 ---

def test_validation_warns_when_auth_disabled_in_non_development_env(caplog):
    config = build_test_config(
        APP_ENV="staging",
        REQUIRE_API_KEY=False,
        REQUIRE_JWT=False,
    )
    with caplog.at_level(logging.WARNING, logger="civic_archive.validation"):
        validate_startup_config(config)
    messages = [r.getMessage() for r in caplog.records]
    assert "auth_disabled_in_non_development" in messages


def test_validation_no_auth_warning_in_development_env(caplog):
    config = build_test_config(
        APP_ENV="development",
        REQUIRE_API_KEY=False,
        REQUIRE_JWT=False,
    )
    with caplog.at_level(logging.WARNING, logger="civic_archive.validation"):
        validate_startup_config(config)
    messages = [r.getMessage() for r in caplog.records]
    assert "auth_disabled_in_non_development" not in messages


def test_validation_no_auth_warning_when_api_key_enabled(caplog):
    config = build_test_config(
        APP_ENV="staging",
        REQUIRE_API_KEY=True,
        API_KEY="some-api-key",
        REQUIRE_JWT=False,
    )
    with caplog.at_level(logging.WARNING, logger="civic_archive.validation"):
        validate_startup_config(config)
    messages = [r.getMessage() for r in caplog.records]
    assert "auth_disabled_in_non_development" not in messages


def test_validation_no_auth_warning_in_test_env(caplog):
    # APP_ENV="test" (default build_test_config) must never emit the warning
    config = build_test_config(REQUIRE_API_KEY=False, REQUIRE_JWT=False)
    with caplog.at_level(logging.WARNING, logger="civic_archive.validation"):
        validate_startup_config(config)
    messages = [r.getMessage() for r in caplog.records]
    assert "auth_disabled_in_non_development" not in messages


def test_validation_strict_mode_rejects_missing_auth():
    with pytest.raises(RuntimeError, match="Strict security mode requires REQUIRE_API_KEY=1 or REQUIRE_JWT=1"):
        validate_startup_config(
            _strict_base_config(REQUIRE_API_KEY=False, REQUIRE_JWT=False)
        )


def test_validation_strict_mode_rejects_zero_rate_limit():
    with pytest.raises(RuntimeError, match="Strict security mode requires RATE_LIMIT_PER_MINUTE > 0"):
        validate_startup_config(_strict_base_config(RATE_LIMIT_PER_MINUTE=0))


def test_routes_module_forwards_protected_dependencies(monkeypatch):
    api = FastAPI()
    captured = {}
    marker_dependency = object()

    def fake_register_routes(app, *, dependencies=None):
        captured["app"] = app
        captured["dependencies"] = dependencies

    monkeypatch.setattr(bootstrap_routes_module, "register_routes", fake_register_routes)
    register_domain_routes(api, protected_dependencies=[marker_dependency])

    assert captured["app"] is api
    assert captured["dependencies"] == [marker_dependency]


def test_middleware_module_enforces_request_size_guard():
    api = FastAPI()
    register_core_middleware(api, build_test_config(MAX_REQUEST_BODY_BYTES=64))

    @api.get("/status")
    async def status():
        return {"status": "ok"}

    @api.post("/api/echo")
    async def echo(request_body: dict):
        return request_body

    with TestClient(api) as client:
        health = client.get("/status")
        assert health.status_code == 200
        assert health.json() == {"status": "ok"}

        oversized = client.post(
            "/api/echo",
            content='{"payload":"' + ("x" * 200) + '"}',
            headers={"Content-Type": "application/json"},
        )
        assert oversized.status_code == 413
        error_body = oversized.json()
        assert error_body["code"] == "PAYLOAD_TOO_LARGE"
        assert error_body["details"]["max_request_body_bytes"] == 64


def test_system_routes_module_readiness_and_echo():
    api = FastAPI()
    register_system_routes(
        api,
        protected_dependencies=[],
        db_health_check=lambda: (True, None),
        rate_limit_health_check=lambda: (False, "redis down"),
    )

    with TestClient(api) as client:
        ready = client.get("/health/ready")
        assert ready.status_code == 503
        readiness_body = ready.json()
        assert readiness_body["status"] == "degraded"
        assert readiness_body["checks"]["database"]["ok"] is True
        assert readiness_body["checks"]["rate_limit_backend"]["ok"] is False

        echo = client.post("/api/echo", json={"hello": "world"})
        assert echo.status_code == 200
        assert echo.json() == {"you_sent": {"hello": "world"}}


# --- P11-6: 기본 DB 패스워드 시작 시 경고 ---


def test_validation_non_strict_default_db_password_emits_warning_in_staging(caplog):
    config = build_test_config(APP_ENV="staging", POSTGRES_PASSWORD="change_me")
    with caplog.at_level(logging.WARNING, logger="civic_archive.validation"):
        validate_startup_config(config)
    messages = [r.getMessage() for r in caplog.records]
    assert "default_db_password_detected" in messages


def test_validation_non_strict_default_db_password_no_warning_in_development(caplog):
    config = build_test_config(APP_ENV="development", POSTGRES_PASSWORD="change_me")
    with caplog.at_level(logging.WARNING, logger="civic_archive.validation"):
        validate_startup_config(config)
    messages = [r.getMessage() for r in caplog.records]
    assert "default_db_password_detected" not in messages


def test_validation_non_strict_changed_db_password_no_warning_in_staging(caplog):
    config = build_test_config(APP_ENV="staging", POSTGRES_PASSWORD="secure-password-123")
    with caplog.at_level(logging.WARNING, logger="civic_archive.validation"):
        validate_startup_config(config)
    messages = [r.getMessage() for r in caplog.records]
    assert "default_db_password_detected" not in messages


def test_validation_strict_mode_rejects_default_db_password():
    with pytest.raises(RuntimeError, match="POSTGRES_PASSWORD"):
        validate_startup_config(_strict_base_config(POSTGRES_PASSWORD="change_me"))


def test_exception_handlers_module_normalizes_errors():
    api = FastAPI()
    register_exception_handlers(api, logger=logging.getLogger("test.bootstrap.handlers"))

    @api.get("/validation")
    async def validation_route(page: int = Query(...)):
        return {"page": page}

    @api.get("/http")
    async def http_route():
        raise HTTPException(status_code=404, detail="Not Found")

    @api.get("/boom")
    async def boom_route():
        raise RuntimeError("boom")

    with TestClient(api, raise_server_exceptions=False) as client:
        validation = client.get("/validation?page=abc")
        assert validation.status_code == 400
        assert validation.json()["code"] == "VALIDATION_ERROR"

        http_error = client.get("/http")
        assert http_error.status_code == 404
        assert http_error.json()["code"] == "NOT_FOUND"

        boom = client.get("/boom")
        assert boom.status_code == 500
        assert boom.json()["code"] == "INTERNAL_ERROR"
