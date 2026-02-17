from __future__ import annotations

import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.exceptions import HTTPException as StarletteHTTPException

REQUEST_COUNT = Counter(
    "civic_archive_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "civic_archive_http_request_duration_seconds",
    "HTTP request latency (seconds)",
    ["method", "path"],
)
ALLOWED_HTTP_METHOD_LABELS = {"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"}
MAX_PATH_LABEL_LENGTH = 96

logger = logging.getLogger("civic_archive.api")


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)
    if route_path:
        return str(route_path)
    return "/_unmatched"


def _metric_method_label(method: str | None) -> str:
    normalized = (method or "").upper()
    if normalized in ALLOWED_HTTP_METHOD_LABELS:
        return normalized
    return "OTHER"


def _metric_path_label(request: Request) -> str:
    path = _route_template(request)
    if len(path) > MAX_PATH_LABEL_LENGTH:
        return "/_label_too_long"
    return path


def _metric_status_label(status_code: int) -> str:
    if 100 <= int(status_code) <= 599:
        return str(int(status_code))
    return "000"


def register_observability(api: FastAPI) -> None:
    @api.middleware("http")
    async def request_observability(request: Request, call_next):
        request_id = request.headers.get("X-Request-Id") or str(uuid4())
        request.state.request_id = request_id
        started = time.perf_counter()
        client_ip = request.client.host if request.client else None

        try:
            response = await call_next(request)
        except Exception as exc:
            elapsed = time.perf_counter() - started
            method = _metric_method_label(request.method)
            path = _metric_path_label(request)
            status_code = 500
            if isinstance(exc, RequestValidationError):
                status_code = 400
            elif isinstance(exc, StarletteHTTPException):
                status_code = int(exc.status_code)
            status_label = _metric_status_label(status_code)

            REQUEST_COUNT.labels(method, path, status_label).inc()
            REQUEST_LATENCY.labels(method, path).observe(elapsed)
            log_payload = {
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(elapsed * 1000, 2),
                "client_ip": client_ip,
            }
            if status_code >= 500:
                logger.exception(
                    "request_failed",
                    extra=log_payload,
                )
            else:
                logger.warning(
                    "request_failed",
                    extra=log_payload,
                )
            raise

        elapsed = time.perf_counter() - started
        method = _metric_method_label(request.method)
        path = _metric_path_label(request)
        status_code = int(response.status_code)
        status_label = _metric_status_label(status_code)
        REQUEST_COUNT.labels(method, path, status_label).inc()
        REQUEST_LATENCY.labels(method, path).observe(elapsed)
        response.headers["X-Request-Id"] = request_id

        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": path,
                "status_code": status_code,
                "duration_ms": round(elapsed * 1000, 2),
                "client_ip": client_ip,
            },
        )
        return response

    @api.get("/metrics", tags=["system"], include_in_schema=False)
    async def metrics() -> Response:
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
