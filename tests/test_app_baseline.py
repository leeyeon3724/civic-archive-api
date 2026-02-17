from datetime import datetime
from unittest.mock import patch

import pytest
from conftest import StubResult
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import create_app
from app.config import Config
from app.version import APP_VERSION

def _assert_not_found_error(payload):
    assert payload["error"] == "Not Found"
    assert payload["code"] == "NOT_FOUND"
    assert payload["message"] == "Not Found"
    assert payload.get("request_id")


def _assert_standard_error_shape(payload):
    assert isinstance(payload.get("code"), str) and payload["code"]
    assert isinstance(payload.get("message"), str) and payload["message"]
    assert isinstance(payload.get("error"), str) and payload["error"]
    assert isinstance(payload.get("request_id"), str) and payload["request_id"]


def test_parse_datetime_accepts_supported_formats(utils_module):
    assert utils_module.parse_datetime("2025-08-16T10:32:00Z") == datetime(2025, 8, 16, 10, 32, 0)
    assert utils_module.parse_datetime("2025-08-16 10:32:00") == datetime(2025, 8, 16, 10, 32, 0)
    assert utils_module.parse_datetime("2025-08-16T10:32:00") == datetime(2025, 8, 16, 10, 32, 0)


def test_parse_datetime_rejects_invalid_format(utils_module):
    with pytest.raises(HTTPException):
        utils_module.parse_datetime("16-08-2025")


def test_normalize_article_requires_title_and_url(news_module):
    with pytest.raises(HTTPException):
        news_module.normalize_article({"title": "only-title"})


def test_normalize_minutes_preserves_string_meeting_no(minutes_module):
    result = minutes_module.normalize_minutes(
        {
            "council": "Sample Council",
            "url": "https://example.com/minutes/1",
            "meeting_no": "Session-A-12",
        }
    )
    assert result["meeting_no"] is None
    assert result["meeting_no_combined"] == "Session-A-12"


def test_normalize_minutes_converts_numeric_meeting_no(minutes_module):
    result = minutes_module.normalize_minutes(
        {
            "council": "Sample Council",
            "session": "29th",
            "url": "https://example.com/minutes/2",
            "meeting_no": 3,
        }
    )
    assert result["meeting_no"] == 3
    assert result["meeting_no_combined"] == "29th 3차"


def test_normalize_segment_validates_importance(segments_module):
    ok = segments_module.normalize_segment({"council": "A", "importance": "2"})
    assert ok["importance"] == 2

    with pytest.raises(HTTPException):
        segments_module.normalize_segment({"council": "A", "importance": "invalid"})

    with pytest.raises(HTTPException):
        segments_module.normalize_segment({"council": "A", "importance": 4})


def test_upsert_articles_counts_insert_and_update(db_module, news_module, monkeypatch, make_engine):
    rowcounts = iter([1, 2, 1])

    def handler(statement, _params):
        sql = str(statement).lower()
        if "insert into news_articles" in sql:
            return StubResult(rowcount=next(rowcounts))
        return StubResult()

    monkeypatch.setattr(db_module, "engine", make_engine(handler))

    inserted, updated = news_module.upsert_articles(
        [
            {"title": "n1", "url": "u1"},
            {"title": "n2", "url": "u2"},
            {"title": "n3", "url": "u3"},
        ]
    )
    assert inserted == 2
    assert updated == 1


def test_insert_segments_returns_inserted_count(db_module, segments_module, monkeypatch, make_engine):
    def handler(_statement, _params):
        return StubResult(rowcount=1)

    monkeypatch.setattr(db_module, "engine", make_engine(handler))

    inserted = segments_module.insert_segments([{"council": "A"}, {"council": "B"}])
    assert inserted == 2


def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}
    assert resp.headers.get("X-Request-Id")


def test_request_id_is_propagated_when_client_sends_header(client):
    request_id = "test-request-id-123"
    resp = client.get("/health", headers={"X-Request-Id": request_id})
    assert resp.status_code == 200
    assert resp.headers.get("X-Request-Id") == request_id


def test_validation_error_returns_standard_error_with_details(client):
    request_id = "test-validation-request-id"
    resp = client.get("/api/news?page=abc", headers={"X-Request-Id": request_id})
    assert resp.status_code == 400
    payload = resp.get_json()
    _assert_standard_error_shape(payload)
    assert payload["code"] == "VALIDATION_ERROR"
    assert isinstance(payload.get("details"), list)
    assert resp.headers.get("X-Request-Id") == request_id
    assert payload["request_id"] == request_id


def test_save_news_accepts_object_and_list(client, news_module, monkeypatch):
    monkeypatch.setattr(news_module, "upsert_articles", lambda items: (len(items), 0))

    one = client.post("/api/news", json={"title": "t1", "url": "u1"})
    assert one.status_code == 201
    assert one.get_json() == {"inserted": 1, "updated": 0}

    many = client.post(
        "/api/news",
        json=[{"title": "t2", "url": "u2"}, {"title": "t3", "url": "u3"}],
    )
    assert many.status_code == 201
    assert many.get_json() == {"inserted": 2, "updated": 0}


def test_save_news_rejects_invalid_json_body(client):
    resp = client.post("/api/news", data="{invalid", content_type="application/json")
    assert resp.status_code == 400
    payload = resp.get_json()
    assert payload["code"] in {"BAD_REQUEST", "VALIDATION_ERROR"}
    assert "error" in payload


def test_save_minutes_requires_json(client):
    resp = client.post("/api/minutes", data="plain text", content_type="text/plain")
    assert resp.status_code == 400
    payload = resp.get_json()
    assert payload["code"] in {"BAD_REQUEST", "VALIDATION_ERROR"}


def test_save_segments_requires_json(client):
    resp = client.post("/api/segments", data="plain text", content_type="text/plain")
    assert resp.status_code == 400
    payload = resp.get_json()
    assert payload["code"] in {"BAD_REQUEST", "VALIDATION_ERROR"}


def test_list_news_returns_paginated_payload(client, db_module, monkeypatch, make_engine):
    def handler(statement, _params):
        sql = str(statement).lower()
        if "select count(*) as total" in sql:
            return StubResult(scalar_value=1)
        if "from news_articles" in sql:
            return StubResult(
                rows=[
                    {
                        "id": 10,
                        "source": "paper",
                        "title": "budget news",
                        "url": "https://example.com/n/10",
                        "published_at": "2025-01-01 00:00:00",
                        "author": "author",
                        "summary": "summary",
                        "keywords": '["budget"]',
                        "created_at": "2025-01-01 00:00:00",
                        "updated_at": "2025-01-01 00:00:00",
                    }
                ]
            )
        return StubResult()

    engine = make_engine(handler)
    monkeypatch.setattr(db_module, "engine", engine)

    resp = client.get("/api/news?page=2&size=1&q=budget")
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["page"] == 2
    assert data["size"] == 1
    assert data["total"] == 1
    assert data["items"][0]["id"] == 10

    first_select = next(c for c in engine.connection.calls if "from news_articles" in c["statement"].lower())
    assert first_select["params"]["limit"] == 1
    assert first_select["params"]["offset"] == 1
    assert first_select["params"]["q"] == "%budget%"


def test_get_news_404_when_not_found(client, db_module, monkeypatch, make_engine):
    def handler(statement, _params):
        sql = str(statement).lower()
        if "from news_articles where id=:id" in sql:
            return StubResult(rows=[])
        return StubResult()

    monkeypatch.setattr(db_module, "engine", make_engine(handler))

    resp = client.get("/api/news/999")
    assert resp.status_code == 404
    _assert_not_found_error(resp.get_json())


def test_delete_news_success_and_not_found(client, db_module, monkeypatch, make_engine):
    def handler(statement, params):
        sql = str(statement).lower()
        if "delete from news_articles" in sql and params["id"] == 1:
            return StubResult(rowcount=1)
        if "delete from news_articles" in sql and params["id"] == 2:
            return StubResult(rowcount=0)
        return StubResult()

    monkeypatch.setattr(db_module, "engine", make_engine(handler))

    ok_resp = client.delete("/api/news/1")
    assert ok_resp.status_code == 200
    assert ok_resp.get_json() == {"status": "deleted", "id": 1}

    miss_resp = client.delete("/api/news/2")
    assert miss_resp.status_code == 404
    _assert_not_found_error(miss_resp.get_json())


def test_list_segments_rejects_invalid_importance(client):
    resp = client.get("/api/segments?importance=high")
    assert resp.status_code == 400
    payload = resp.get_json()
    assert payload["code"] == "VALIDATION_ERROR"
    assert "error" in payload


def test_unknown_route_returns_json_404(client):
    resp = client.get("/no-such-route")
    assert resp.status_code == 404
    payload = resp.get_json()
    _assert_not_found_error(payload)
    assert resp.headers.get("X-Request-Id")
    assert payload["request_id"] == resp.headers.get("X-Request-Id")


def test_metrics_endpoint_exposes_prometheus_text(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in (resp.headers.get("content-type") or "")
    body = resp.text
    assert "civic_archive_http_requests_total" in body
    assert "civic_archive_http_request_duration_seconds" in body


def test_metrics_uses_low_cardinality_label_for_unmatched_route(client):
    unmatched_path = "/no-such-route-cardinality-unique-case"
    missing = client.get(unmatched_path)
    assert missing.status_code == 404

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    body = metrics.text
    assert 'path="/_unmatched"' in body
    assert f'path="{unmatched_path}"' not in body


def test_openapi_version_uses_app_version_constant(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    assert resp.get_json()["info"]["version"] == APP_VERSION


def test_api_key_required_for_protected_endpoint(make_engine):
    with patch("app.database.create_engine", return_value=make_engine(lambda *_: StubResult())):
        app = create_app(
            Config(
                REQUIRE_API_KEY=True,
                API_KEY="top-secret",
            )
        )

    with TestClient(app) as tc:
        unauthorized = tc.post("/api/echo", json={"hello": "world"})
        assert unauthorized.status_code == 401
        body = unauthorized.json()
        assert body["code"] == "UNAUTHORIZED"
        assert body["message"] == "Unauthorized"
        assert body.get("request_id")

        authorized = tc.post("/api/echo", json={"hello": "world"}, headers={"X-API-Key": "top-secret"})
        assert authorized.status_code == 200
        assert authorized.json() == {"you_sent": {"hello": "world"}}


def test_rate_limit_enforced_for_protected_endpoint(make_engine):
    with patch("app.database.create_engine", return_value=make_engine(lambda *_: StubResult())):
        app = create_app(
            Config(
                RATE_LIMIT_PER_MINUTE=1,
            )
        )

    with TestClient(app) as tc:
        first = tc.post("/api/echo", json={"n": 1})
        assert first.status_code == 200

        second = tc.post("/api/echo", json={"n": 2})
        assert second.status_code == 429
        body = second.json()
        assert body["code"] == "RATE_LIMITED"
        assert body["message"] == "Too Many Requests"
        assert body.get("request_id")


def test_rate_limit_backend_rejects_invalid_value(make_engine):
    with patch("app.database.create_engine", return_value=make_engine(lambda *_: StubResult())):
        with pytest.raises(RuntimeError):
            create_app(
                Config(
                    RATE_LIMIT_BACKEND="invalid-backend",
                    RATE_LIMIT_PER_MINUTE=1,
                )
            )


def test_rate_limit_redis_backend_requires_redis_url(make_engine):
    with patch("app.database.create_engine", return_value=make_engine(lambda *_: StubResult())):
        with pytest.raises(RuntimeError):
            create_app(
                Config(
                    RATE_LIMIT_BACKEND="redis",
                    RATE_LIMIT_PER_MINUTE=1,
                    REDIS_URL=None,
                )
            )


def test_rate_limit_redis_backend_is_usable_with_custom_limiter(make_engine):
    class FakeRedisRateLimiter:
        def __init__(self, *, requests_per_minute: int, redis_url: str, key_prefix: str, window_seconds: int) -> None:
            assert requests_per_minute == 1
            assert redis_url == "redis://localhost:6379/0"
            assert key_prefix == "test-prefix"
            assert window_seconds == 70
            self.enabled = True
            self.calls = 0

        def allow(self, _key: str) -> bool:
            self.calls += 1
            return self.calls <= 1

    with patch("app.database.create_engine", return_value=make_engine(lambda *_: StubResult())), patch(
        "app.security.RedisRateLimiter",
        FakeRedisRateLimiter,
    ):
        app = create_app(
            Config(
                RATE_LIMIT_BACKEND="redis",
                REDIS_URL="redis://localhost:6379/0",
                RATE_LIMIT_REDIS_PREFIX="test-prefix",
                RATE_LIMIT_REDIS_WINDOW_SECONDS=70,
                RATE_LIMIT_PER_MINUTE=1,
            )
        )

    with TestClient(app) as tc:
        first = tc.post("/api/echo", json={"n": 1})
        assert first.status_code == 200

        second = tc.post("/api/echo", json={"n": 2})
        assert second.status_code == 429
