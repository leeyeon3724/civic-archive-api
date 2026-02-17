from unittest.mock import patch

from fastapi.testclient import TestClient
from conftest import StubResult

from app import create_app
from app.config import Config


def _metric_counter_value(metrics_text: str, *, method: str, path: str, status_code: str) -> float:
    prefix = (
        "civic_archive_http_requests_total{"
        f'method="{method}",path="{path}",status_code="{status_code}"'
        "} "
    )
    for line in metrics_text.splitlines():
        if line.startswith(prefix):
            return float(line[len(prefix) :])
    return 0.0


def test_metrics_uses_route_template_label_for_payload_guard_failure(make_engine):
    with patch("app.database.create_engine", return_value=make_engine(lambda *_: StubResult())):
        app = create_app(Config(MAX_REQUEST_BODY_BYTES=64))

    with TestClient(app) as tc:
        before_metrics = tc.get("/metrics")
        assert before_metrics.status_code == 200
        before_echo_413 = _metric_counter_value(
            before_metrics.text, method="POST", path="/api/echo", status_code="413"
        )
        before_unmatched_413 = _metric_counter_value(
            before_metrics.text, method="POST", path="/_unmatched", status_code="413"
        )

        oversized = tc.post(
            "/api/echo",
            content='{"payload":"' + ("x" * 200) + '"}',
            headers={"Content-Type": "application/json"},
        )
        assert oversized.status_code == 413
        assert oversized.json()["code"] == "PAYLOAD_TOO_LARGE"

        after_metrics = tc.get("/metrics")
        assert after_metrics.status_code == 200
        after_echo_413 = _metric_counter_value(
            after_metrics.text, method="POST", path="/api/echo", status_code="413"
        )
        after_unmatched_413 = _metric_counter_value(
            after_metrics.text, method="POST", path="/_unmatched", status_code="413"
        )

        assert after_echo_413 == before_echo_413 + 1
        assert after_unmatched_413 == before_unmatched_413
