from __future__ import annotations

from typing import Any, Callable

from fastapi import Body, FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import text

import app.database as database
from app.schemas import EchoResponse, ErrorResponse, HealthResponse, ReadinessCheck, ReadinessResponse


def register_system_routes(
    api: FastAPI,
    *,
    config,
    protected_dependencies: list[Any],
    rate_limit_health_check: Callable[[], tuple[bool, str | None]],
) -> None:
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
        rate_limit_ok, rate_limit_detail = rate_limit_health_check()
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
            413: {"model": ErrorResponse},
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

