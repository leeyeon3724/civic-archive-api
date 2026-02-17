from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app import create_app
from app.config import Config

pytestmark = pytest.mark.integration


def _skip_if_not_enabled():
    if os.getenv("RUN_INTEGRATION") != "1":
        pytest.skip("Integration tests require RUN_INTEGRATION=1 and a running PostgreSQL instance.")


def _build_jwt(secret: str, claims: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}

    def _encode(value: dict) -> str:
        raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")

    header_b64 = _encode(header)
    payload_b64 = _encode(claims)
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"{header_b64}.{payload_b64}.{signature_b64}"


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


@pytest.fixture(scope="session")
def integration_client():
    _skip_if_not_enabled()
    app = create_app(Config())
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def clean_tables(integration_client):
    _skip_if_not_enabled()
    app = integration_client.app
    with app.state.connection_provider() as conn:
        conn.execute(
            text(
                """
                TRUNCATE TABLE
                  news_articles,
                  council_minutes,
                  council_speech_segments
                RESTART IDENTITY
                """
            )
        )


def test_news_upsert_and_update(integration_client):
    payload = {
        "source": "integration",
        "title": "integration news",
        "url": "https://example.com/news/int-1",
        "published_at": "2026-02-17T10:00:00Z",
    }
    first = integration_client.post("/api/news", json=payload)
    assert first.status_code == 201
    assert first.json() == {"inserted": 1, "updated": 0}

    payload["title"] = "integration news updated"
    second = integration_client.post("/api/news", json=payload)
    assert second.status_code == 201
    assert second.json() == {"inserted": 0, "updated": 1}

    listed = integration_client.get("/api/news", params={"source": "integration"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["title"] == "integration news updated"


def test_news_batch_with_duplicate_url_is_stable(integration_client):
    payload = [
        {
            "source": "integration-dup",
            "title": "integration dup news v1",
            "url": "https://example.com/news/int-dup-1",
            "published_at": "2026-02-17T10:00:00Z",
        },
        {
            "source": "integration-dup",
            "title": "integration dup news v2",
            "url": "https://example.com/news/int-dup-1",
            "published_at": "2026-02-17T10:00:00Z",
        },
    ]
    saved = integration_client.post("/api/news", json=payload)
    assert saved.status_code == 201
    assert saved.json() == {"inserted": 1, "updated": 0}

    listed = integration_client.get("/api/news", params={"source": "integration-dup"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["title"] == "integration dup news v2"


def test_news_date_range_includes_full_to_date(integration_client):
    payload = {
        "source": "integration-date-boundary",
        "title": "integration boundary news",
        "url": "https://example.com/news/int-boundary-1",
        "published_at": "2026-02-17T10:00:00Z",
    }
    saved = integration_client.post("/api/news", json=payload)
    assert saved.status_code == 201
    assert saved.json() == {"inserted": 1, "updated": 0}

    listed = integration_client.get(
        "/api/news",
        params={
            "source": "integration-date-boundary",
            "from": "2026-02-17",
            "to": "2026-02-17",
        },
    )
    assert listed.status_code == 200
    body = listed.json()
    assert body["total"] == 1
    assert body["items"][0]["url"] == "https://example.com/news/int-boundary-1"


def test_minutes_upsert_and_filter(integration_client):
    payload = {
        "council": "seoul",
        "committee": "budget",
        "session": "301",
        "meeting_no": "301 4th",
        "url": "https://example.com/minutes/int-1",
        "meeting_date": "2026-02-17",
        "content": "minutes integration",
    }
    saved = integration_client.post("/api/minutes", json=payload)
    assert saved.status_code == 201
    assert saved.json() == {"inserted": 1, "updated": 0}

    listed = integration_client.get("/api/minutes", params={"council": "seoul", "from": "2026-02-01"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["council"] == "seoul"


def test_minutes_batch_with_duplicate_url_is_stable(integration_client):
    payload = [
        {
            "council": "seoul",
            "committee": "budget",
            "session": "301",
            "meeting_no": "301 4th",
            "url": "https://example.com/minutes/int-dup-1",
            "meeting_date": "2026-02-17",
            "content": "minutes integration v1",
        },
        {
            "council": "seoul",
            "committee": "plenary",
            "session": "301",
            "meeting_no": "301 4th",
            "url": "https://example.com/minutes/int-dup-1",
            "meeting_date": "2026-02-17",
            "content": "minutes integration v2",
        },
    ]
    saved = integration_client.post("/api/minutes", json=payload)
    assert saved.status_code == 201
    assert saved.json() == {"inserted": 1, "updated": 0}

    listed = integration_client.get("/api/minutes", params={"council": "seoul"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["committee"] == "plenary"


def test_segments_insert_and_filter(integration_client):
    payload = {
        "council": "seoul",
        "committee": "budget",
        "session": "301",
        "meeting_no": "301 4th",
        "meeting_date": "2026-02-17",
        "content": "segment integration",
        "importance": 2,
        "party": "party-a",
    }
    saved = integration_client.post("/api/segments", json=payload)
    assert saved.status_code == 201
    assert saved.json() == {"inserted": 1}

    duplicate = integration_client.post("/api/segments", json=payload)
    assert duplicate.status_code == 201
    assert duplicate.json() == {"inserted": 0}

    listed = integration_client.get("/api/segments", params={"importance": 2, "party": "party-a"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["importance"] == 2


def test_error_schema_contains_standard_fields(integration_client):
    missing = integration_client.get("/api/news/99999")
    assert missing.status_code == 404
    body = missing.json()
    assert body["code"] == "NOT_FOUND"
    assert body["message"] == "Not Found"
    assert body["error"] == "Not Found"
    assert body.get("request_id")
    assert missing.headers.get("X-Request-Id") == body["request_id"]


def test_request_id_passthrough(integration_client):
    req_id = "integration-request-id-1"
    resp = integration_client.get("/health", headers={"X-Request-Id": req_id})
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-Id") == req_id


def test_metrics_endpoint_available(integration_client):
    resp = integration_client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in (resp.headers.get("content-type") or "")
    assert "civic_archive_http_requests_total" in resp.text


def test_runtime_jwt_authorization_path():
    _skip_if_not_enabled()
    secret = "integration-jwt-secret"
    now = int(time.time())
    read_token = _build_jwt(
        secret,
        {
            "sub": "integration-read",
            "scope": "archive:read",
            "exp": now + 300,
        },
    )
    write_token = _build_jwt(
        secret,
        {
            "sub": "integration-write",
            "scope": "archive:write archive:read",
            "exp": now + 300,
        },
    )
    app = create_app(Config(REQUIRE_JWT=True, JWT_SECRET=secret))
    with TestClient(app) as client:
        unauthorized = client.post("/api/echo", json={"hello": "world"})
        assert unauthorized.status_code == 401
        assert unauthorized.json()["code"] == "UNAUTHORIZED"

        forbidden = client.post(
            "/api/echo",
            json={"hello": "world"},
            headers={"Authorization": f"Bearer {read_token}"},
        )
        assert forbidden.status_code == 403
        assert forbidden.json()["code"] == "FORBIDDEN"

        authorized = client.post(
            "/api/echo",
            json={"hello": "world"},
            headers={"Authorization": f"Bearer {write_token}"},
        )
        assert authorized.status_code == 200
        assert authorized.json() == {"you_sent": {"hello": "world"}}


def test_payload_guard_returns_standard_413_shape():
    _skip_if_not_enabled()
    app = create_app(Config(MAX_REQUEST_BODY_BYTES=64))
    with TestClient(app) as client:
        body = '{"payload":"' + ("x" * 200) + '"}'
        response = client.post(
            "/api/echo",
            content=body,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 413
        payload = response.json()
        assert payload["code"] == "PAYLOAD_TOO_LARGE"
        assert payload["message"] == "Payload Too Large"
        assert payload["error"] == "Payload Too Large"
        assert payload["details"]["max_request_body_bytes"] == 64
        assert payload["details"]["content_length"] > 64
        assert payload.get("request_id")
        assert response.headers.get("X-Request-Id") == payload["request_id"]


def test_metrics_label_for_guard_failure_uses_route_template():
    _skip_if_not_enabled()
    app = create_app(Config(MAX_REQUEST_BODY_BYTES=64))
    with TestClient(app) as client:
        before = client.get("/metrics")
        assert before.status_code == 200
        before_echo_413 = _metric_counter_value(
            before.text, method="POST", path="/api/echo", status_code="413"
        )
        before_unmatched_413 = _metric_counter_value(
            before.text, method="POST", path="/_unmatched", status_code="413"
        )

        oversized = client.post(
            "/api/echo",
            content='{"payload":"' + ("x" * 200) + '"}',
            headers={"Content-Type": "application/json"},
        )
        assert oversized.status_code == 413
        assert oversized.json()["code"] == "PAYLOAD_TOO_LARGE"

        after = client.get("/metrics")
        assert after.status_code == 200
        after_echo_413 = _metric_counter_value(
            after.text, method="POST", path="/api/echo", status_code="413"
        )
        after_unmatched_413 = _metric_counter_value(
            after.text, method="POST", path="/_unmatched", status_code="413"
        )

        assert after_echo_413 == before_echo_413 + 1
        assert after_unmatched_413 == before_unmatched_413
