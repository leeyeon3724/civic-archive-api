from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app import create_app
from app.config import Config
from app.database import init_db
import app.database as database

pytestmark = pytest.mark.integration


def _skip_if_not_enabled():
    if os.getenv("RUN_INTEGRATION") != "1":
        pytest.skip("Integration tests require RUN_INTEGRATION=1 and a running PostgreSQL instance.")


@pytest.fixture(scope="session")
def integration_client():
    _skip_if_not_enabled()
    app = create_app(Config())
    with TestClient(app) as client:
        yield client


@pytest.fixture(autouse=True)
def clean_tables():
    _skip_if_not_enabled()
    if database.engine is None:
        init_db(Config().DATABASE_URL)
    with database.engine.begin() as conn:
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
