import logging

from fastapi import Body, Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.trustedhost import TrustedHostMiddleware

import app.database as database
from app.config import Config
from app.database import init_db
from app.errors import error_response, normalize_http_exception
from app.logging_config import configure_logging
from app.observability import register_observability
from app.routes import register_routes
from app.schemas import EchoResponse, ErrorResponse, HealthResponse, ReadinessCheck, ReadinessResponse
from app.security import (
    build_api_key_dependency,
    build_jwt_dependency,
    build_rate_limit_dependency,
    check_rate_limit_backend_health,
)
from app.version import APP_VERSION

OPENAPI_TAGS = [
    {"name": "system", "description": "System and health endpoints"},
    {"name": "news", "description": "News ingestion and search"},
    {"name": "minutes", "description": "Council minutes ingestion and search"},
    {"name": "segments", "description": "Speech segment ingestion and search"},
]

logger = logging.getLogger("civic_archive.api")


def create_app(config=None):
    if config is None:
        config = Config()

    configure_logging(level=config.LOG_LEVEL, json_logs=config.LOG_JSON)

    api = FastAPI(
        title="Civic Archive API",
        version=APP_VERSION,
        description="Local council archive API with FastAPI + PostgreSQL",
        openapi_tags=OPENAPI_TAGS,
    )

    if config.BOOTSTRAP_TABLES_ON_STARTUP:
        raise RuntimeError("BOOTSTRAP_TABLES_ON_STARTUP is disabled. Run 'alembic upgrade head' before startup.")
    if config.REQUIRE_API_KEY and not (config.API_KEY or "").strip():
        raise RuntimeError("REQUIRE_API_KEY=1 requires API_KEY to be set.")
    if config.REQUIRE_JWT and not (config.JWT_SECRET or "").strip():
        raise RuntimeError("REQUIRE_JWT=1 requires JWT_SECRET to be set.")
    if config.REQUIRE_JWT and (config.JWT_ALGORITHM or "").strip().upper() != "HS256":
        raise RuntimeError("JWT_ALGORITHM must be HS256.")
    if config.rate_limit_backend not in {"memory", "redis"}:
        raise RuntimeError("RATE_LIMIT_BACKEND must be one of: memory, redis.")
    if config.rate_limit_backend == "redis" and not (config.REDIS_URL or "").strip():
        raise RuntimeError("RATE_LIMIT_BACKEND=redis requires REDIS_URL to be set.")
    if config.RATE_LIMIT_REDIS_FAILURE_COOLDOWN_SECONDS <= 0:
        raise RuntimeError("RATE_LIMIT_REDIS_FAILURE_COOLDOWN_SECONDS must be greater than 0.")
    if config.DB_POOL_SIZE <= 0:
        raise RuntimeError("DB_POOL_SIZE must be greater than 0.")
    if config.DB_MAX_OVERFLOW < 0:
        raise RuntimeError("DB_MAX_OVERFLOW must be greater than or equal to 0.")
    if config.DB_POOL_TIMEOUT_SECONDS <= 0:
        raise RuntimeError("DB_POOL_TIMEOUT_SECONDS must be greater than 0.")
    if config.DB_POOL_RECYCLE_SECONDS <= 0:
        raise RuntimeError("DB_POOL_RECYCLE_SECONDS must be greater than 0.")
    if config.DB_CONNECT_TIMEOUT_SECONDS <= 0:
        raise RuntimeError("DB_CONNECT_TIMEOUT_SECONDS must be greater than 0.")
    if config.DB_STATEMENT_TIMEOUT_MS <= 0:
        raise RuntimeError("DB_STATEMENT_TIMEOUT_MS must be greater than 0.")
    if config.strict_security_mode:
        if not (config.REQUIRE_API_KEY or config.REQUIRE_JWT):
            raise RuntimeError("Strict security mode requires REQUIRE_API_KEY=1 or REQUIRE_JWT=1.")
        if "*" in config.allowed_hosts_list:
            raise RuntimeError("Strict security mode requires explicit ALLOWED_HOSTS (wildcard is not allowed).")
        if "*" in config.cors_allow_origins_list:
            raise RuntimeError("Strict security mode requires explicit CORS_ALLOW_ORIGINS (wildcard is not allowed).")
        if config.RATE_LIMIT_PER_MINUTE <= 0:
            raise RuntimeError("Strict security mode requires RATE_LIMIT_PER_MINUTE > 0.")

    api.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_allow_origins_list,
        allow_methods=config.cors_allow_methods_list,
        allow_headers=config.cors_allow_headers_list,
    )
    api.add_middleware(TrustedHostMiddleware, allowed_hosts=config.allowed_hosts_list)

    init_db(
        config.DATABASE_URL,
        pool_size=config.DB_POOL_SIZE,
        max_overflow=config.DB_MAX_OVERFLOW,
        pool_timeout_seconds=config.DB_POOL_TIMEOUT_SECONDS,
        pool_recycle_seconds=config.DB_POOL_RECYCLE_SECONDS,
        connect_timeout_seconds=config.DB_CONNECT_TIMEOUT_SECONDS,
        statement_timeout_ms=config.DB_STATEMENT_TIMEOUT_MS,
    )
    register_observability(api)

    api_key_dependency = build_api_key_dependency(config)
    jwt_dependency = build_jwt_dependency(config)
    rate_limit_dependency = build_rate_limit_dependency(config)
    protected_dependencies = [Depends(api_key_dependency), Depends(jwt_dependency), Depends(rate_limit_dependency)]
    register_routes(api, dependencies=protected_dependencies)

    def _db_ready() -> tuple[bool, str | None]:
        if database.engine is None:
            return False, "database engine is not initialized"
        try:
            with database.engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            return True, None
        except Exception as exc:
            return False, str(exc)

    @api.get("/", tags=["system"])
    async def hello_world():
        return PlainTextResponse("API Server Available")

    @api.get("/health/live", tags=["system"], response_model=HealthResponse, responses={500: {"model": ErrorResponse}})
    async def health_live():
        return HealthResponse(status="ok")

    @api.get("/health", tags=["system"], response_model=HealthResponse, responses={500: {"model": ErrorResponse}})
    async def health():
        return await health_live()

    @api.get(
        "/health/ready",
        tags=["system"],
        response_model=ReadinessResponse,
        responses={500: {"model": ErrorResponse}, 503: {"model": ReadinessResponse}},
    )
    async def health_ready():
        db_ok, db_detail = _db_ready()
        rate_limit_ok, rate_limit_detail = check_rate_limit_backend_health(config)
        checks = {
            "database": ReadinessCheck(ok=db_ok, detail=db_detail),
            "rate_limit_backend": ReadinessCheck(ok=rate_limit_ok, detail=rate_limit_detail),
        }
        payload = ReadinessResponse(
            status="ok" if db_ok and rate_limit_ok else "degraded",
            checks=checks,
        )
        if db_ok and rate_limit_ok:
            return payload
        return JSONResponse(status_code=503, content=payload.model_dump())

    @api.post(
        "/api/echo",
        tags=["system"],
        summary="Echo request payload",
        dependencies=protected_dependencies,
        response_model=EchoResponse,
        responses={
            400: {"model": ErrorResponse},
            401: {"model": ErrorResponse},
            403: {"model": ErrorResponse},
            429: {"model": ErrorResponse},
            500: {"model": ErrorResponse},
        },
    )
    async def echo(request: Request, _payload: dict = Body(default_factory=dict)):
        try:
            data = await request.json()
        except Exception:
            data = {}
        if data is None:
            data = {}
        return EchoResponse(you_sent=data)

    @api.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return normalize_http_exception(request, exc)

    @api.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        message = "; ".join(err.get("msg", "invalid request") for err in exc.errors())
        return error_response(
            request,
            status_code=400,
            code="VALIDATION_ERROR",
            message=message or "invalid request",
            details=exc.errors(),
        )

    @api.exception_handler(Exception)
    async def server_error_handler(request: Request, exc: Exception):
        logger.exception("unhandled_exception", extra={"request_id": getattr(request.state, "request_id", None)})
        return error_response(
            request,
            status_code=500,
            code="INTERNAL_ERROR",
            message="Internal Server Error",
        )

    return api
