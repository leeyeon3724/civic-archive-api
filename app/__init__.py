import logging
from typing import Any

from fastapi import Depends, FastAPI
from sqlalchemy import text

from app.bootstrap import (
    register_core_middleware,
    register_domain_routes,
    register_exception_handlers,
    register_system_routes,
    validate_startup_config,
)
from app.config import Config
from app.database import init_db
from app.logging_config import configure_logging
from app.observability import register_observability
from app.security import (
    build_api_key_dependency,
    build_jwt_dependency,
    build_rate_limit_dependency,
    check_rate_limit_backend_health,
)
from app.version import APP_VERSION

OPENAPI_TAGS: list[dict[str, str]] = [
    {"name": "system", "description": "System and health endpoints"},
    {"name": "news", "description": "News ingestion and search"},
    {"name": "minutes", "description": "Council minutes ingestion and search"},
    {"name": "segments", "description": "Speech segment ingestion and search"},
]

logger = logging.getLogger("civic_archive.api")


def create_app(config: Config | None = None) -> FastAPI:
    if config is None:
        config = Config()

    configure_logging(level=config.LOG_LEVEL, json_logs=config.LOG_JSON)

    api = FastAPI(
        title="Civic Archive API",
        version=APP_VERSION,
        description="Local council archive API with FastAPI + PostgreSQL",
        openapi_tags=OPENAPI_TAGS,
    )
    api.state.config = config

    validate_startup_config(config)
    register_core_middleware(api, config)

    db_engine = init_db(
        config.database_url,
        pool_size=config.DB_POOL_SIZE,
        max_overflow=config.DB_MAX_OVERFLOW,
        pool_timeout_seconds=config.DB_POOL_TIMEOUT_SECONDS,
        pool_recycle_seconds=config.DB_POOL_RECYCLE_SECONDS,
        connect_timeout_seconds=config.DB_CONNECT_TIMEOUT_SECONDS,
        statement_timeout_ms=config.DB_STATEMENT_TIMEOUT_MS,
    )
    api.state.db_engine = db_engine
    api.state.connection_provider = db_engine.begin

    register_observability(api)

    api_key_dependency = build_api_key_dependency(config)
    jwt_dependency = build_jwt_dependency(config)
    rate_limit_dependency = build_rate_limit_dependency(config)
    protected_dependencies: list[Any] = [
        Depends(api_key_dependency),
        Depends(jwt_dependency),
        Depends(rate_limit_dependency),
    ]

    def db_health_check() -> tuple[bool, str | None]:
        try:
            with api.state.connection_provider() as conn:
                conn.execute(text("SELECT 1"))
            return True, None
        except Exception as exc:
            return False, str(exc)

    register_domain_routes(api, protected_dependencies=protected_dependencies)
    register_system_routes(
        api,
        protected_dependencies=protected_dependencies,
        db_health_check=db_health_check,
        rate_limit_health_check=lambda: check_rate_limit_backend_health(config),
    )
    register_exception_handlers(api, logger=logger)

    return api
