from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.observability import (
    _build_request_log_payload,
    _metric_status_label,
    _status_code_from_exception,
)


def test_status_code_from_exception_maps_validation_http_and_unknown():
    validation_exc = RequestValidationError(
        [
            {
                "loc": ("query", "page"),
                "msg": "value is not a valid integer",
                "type": "type_error.integer",
            }
        ]
    )
    assert _status_code_from_exception(validation_exc) == 400

    http_exc = StarletteHTTPException(status_code=403, detail="Forbidden")
    assert _status_code_from_exception(http_exc) == 403

    assert _status_code_from_exception(RuntimeError("boom")) == 500


def test_metric_status_label_falls_back_for_invalid_status():
    assert _metric_status_label(200) == "200"
    assert _metric_status_label(599) == "599"
    assert _metric_status_label(0) == "000"
    assert _metric_status_label(700) == "000"


def test_build_request_log_payload_has_consistent_shape():
    payload = _build_request_log_payload(
        request_id="req-1",
        method="POST",
        path="/api/news",
        status_code=201,
        elapsed_seconds=0.1234,
        client_ip="127.0.0.1",
    )

    assert payload == {
        "request_id": "req-1",
        "method": "POST",
        "path": "/api/news",
        "status_code": 201,
        "duration_ms": 123.4,
        "client_ip": "127.0.0.1",
    }
