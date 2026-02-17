from conftest import StubResult


from app.services.providers import get_minutes_service, get_segments_service


def _assert_not_found_error(payload):
    assert payload["error"] == "Not Found"
    assert payload["code"] == "NOT_FOUND"
    assert payload["message"] == "Not Found"
    assert payload.get("request_id")


def test_app_init_does_not_execute_manual_ddl(app_instance):
    calls = app_instance._bootstrap_engine_for_test.connection.calls
    ddl_calls = [c for c in calls if "create table" in c["statement"].lower()]
    assert len(ddl_calls) == 0


def test_list_news_invalid_pagination_returns_400(client):
    bad_page = client.get("/api/news?page=abc")
    assert bad_page.status_code == 400
    assert bad_page.get_json()["code"] == "VALIDATION_ERROR"

    bad_size = client.get("/api/news?size=500")
    assert bad_size.status_code == 400
    assert bad_size.get_json()["code"] == "VALIDATION_ERROR"


def test_list_minutes_invalid_pagination_and_date_returns_400(client):
    bad_page = client.get("/api/minutes?page=0")
    assert bad_page.status_code == 400
    assert bad_page.get_json()["code"] == "VALIDATION_ERROR"

    bad_date = client.get("/api/minutes?from=2025/01/01")
    assert bad_date.status_code == 400
    assert bad_date.get_json()["code"] == "VALIDATION_ERROR"


def test_list_segments_invalid_pagination_returns_400(client):
    bad_page = client.get("/api/segments?page=abc")
    assert bad_page.status_code == 400
    assert bad_page.get_json()["code"] == "VALIDATION_ERROR"

    bad_size = client.get("/api/segments?size=0")
    assert bad_size.status_code == 400
    assert bad_size.get_json()["code"] == "VALIDATION_ERROR"


def test_upsert_minutes_counts_insert_and_update(minutes_module, make_connection_provider):
    def handler(statement, _params):
        sql = str(statement).lower()
        if "insert into council_minutes" in sql:
            return StubResult(rows=[{"inserted": 1, "updated": 2}])
        return StubResult()

    connection_provider, _ = make_connection_provider(handler)

    inserted, updated = minutes_module.upsert_minutes(
        [
            {"council": "c1", "url": "u1"},
            {"council": "c2", "url": "u2"},
            {"council": "c3", "url": "u3"},
        ],
        connection_provider=connection_provider,
    )
    assert inserted == 1
    assert updated == 2


def test_save_minutes_accepts_object_and_list(client, override_dependency):
    class FakeMinutesService:
        def normalize_minutes(self, item):
            return item

        def upsert_minutes(self, items):
            return (len(items), 0)

    override_dependency(get_minutes_service, lambda: FakeMinutesService())

    one = client.post("/api/minutes", json={"council": "A", "url": "u1"})
    assert one.status_code == 201
    assert one.get_json() == {"inserted": 1, "updated": 0}

    many = client.post(
        "/api/minutes",
        json=[{"council": "A", "url": "u2"}, {"council": "A", "url": "u3"}],
    )
    assert many.status_code == 201
    assert many.get_json() == {"inserted": 2, "updated": 0}


def test_save_minutes_rejects_invalid_json_body(client):
    resp = client.post("/api/minutes", data="{invalid", content_type="application/json")
    assert resp.status_code == 400
    assert resp.get_json()["code"] in {"BAD_REQUEST", "VALIDATION_ERROR"}


def test_list_minutes_returns_paginated_payload_and_filter_params(client, use_stub_connection_provider):
    def handler(statement, _params):
        sql = str(statement).lower()
        if "select count(*) as total" in sql:
            return StubResult(scalar_value=1)
        if "from council_minutes" in sql:
            return StubResult(
                rows=[
                    {
                        "id": 101,
                        "council": "A",
                        "committee": "B",
                        "session": "C",
                        "meeting_no": "C 1th",
                        "url": "https://example.com/m/101",
                        "meeting_date": "2025-01-01",
                        "tag": "[]",
                        "attendee": "{}",
                        "agenda": "[]",
                        "created_at": "2025-01-01 00:00:00",
                        "updated_at": "2025-01-01 00:00:00",
                    }
                ]
            )
        return StubResult()

    engine = use_stub_connection_provider(handler)

    resp = client.get(
        "/api/minutes?page=2&size=1&q=budget&council=A&committee=B&session=C&meeting_no=C%201th&from=2025-01-01&to=2025-01-31"
    )
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["page"] == 2
    assert data["size"] == 1
    assert data["total"] == 1
    assert data["items"][0]["id"] == 101

    first_select = next(
        c for c in engine.connection.calls if isinstance(c.get("params"), dict) and "limit" in c["params"]
    )
    assert first_select["params"]["limit"] == 1
    assert first_select["params"]["offset"] == 1
    assert first_select["params"]["q"] == "%budget%"
    assert first_select["params"]["council"] == "A"
    assert first_select["params"]["committee"] == "B"
    assert first_select["params"]["session"] == "C"
    assert first_select["params"]["meeting_no"] == "C 1th"
    assert first_select["params"]["date_from"] == "2025-01-01"
    assert first_select["params"]["date_to"] == "2025-01-31"


def test_get_minutes_success_and_404(client, use_stub_connection_provider):
    def handler(statement, params):
        sql = str(statement).lower()
        if "from council_minutes" in sql and "where id=:id" in sql and params["id"] == 1:
            return StubResult(
                rows=[
                    {
                        "id": 1,
                        "council": "A",
                        "committee": None,
                        "session": None,
                        "meeting_no": None,
                        "url": "u1",
                        "meeting_date": None,
                        "content": None,
                        "tag": None,
                        "attendee": None,
                        "agenda": None,
                        "created_at": "2025-01-01 00:00:00",
                        "updated_at": "2025-01-01 00:00:00",
                    }
                ]
            )
        if "from council_minutes" in sql and "where id=:id" in sql and params["id"] == 2:
            return StubResult(rows=[])
        return StubResult()

    use_stub_connection_provider(handler)

    ok_resp = client.get("/api/minutes/1")
    assert ok_resp.status_code == 200
    assert ok_resp.get_json()["id"] == 1

    miss_resp = client.get("/api/minutes/2")
    assert miss_resp.status_code == 404
    _assert_not_found_error(miss_resp.get_json())


def test_delete_minutes_success_and_not_found(client, use_stub_connection_provider):
    def handler(statement, params):
        sql = str(statement).lower()
        if "delete from council_minutes" in sql and params["id"] == 1:
            return StubResult(rowcount=1)
        if "delete from council_minutes" in sql and params["id"] == 2:
            return StubResult(rowcount=0)
        return StubResult()

    use_stub_connection_provider(handler)

    ok_resp = client.delete("/api/minutes/1")
    assert ok_resp.status_code == 200
    assert ok_resp.get_json() == {"status": "deleted", "id": 1}

    miss_resp = client.delete("/api/minutes/2")
    assert miss_resp.status_code == 404
    _assert_not_found_error(miss_resp.get_json())


def test_save_segments_accepts_object_and_list(client, override_dependency):
    class FakeSegmentsService:
        def normalize_segment(self, item):
            return item

        def insert_segments(self, items):
            return len(items)

    override_dependency(get_segments_service, lambda: FakeSegmentsService())

    one = client.post("/api/segments", json={"council": "A"})
    assert one.status_code == 201
    assert one.get_json() == {"inserted": 1}

    many = client.post("/api/segments", json=[{"council": "A"}, {"council": "B"}])
    assert many.status_code == 201
    assert many.get_json() == {"inserted": 2}


def test_save_segments_rejects_invalid_json_body(client):
    resp = client.post("/api/segments", data="{invalid", content_type="application/json")
    assert resp.status_code == 400
    assert resp.get_json()["code"] in {"BAD_REQUEST", "VALIDATION_ERROR"}


def test_list_segments_returns_paginated_payload_and_filter_params(client, use_stub_connection_provider):
    def handler(statement, _params):
        sql = str(statement).lower()
        if "select count(*) as total" in sql:
            return StubResult(scalar_value=1)
        if "from council_speech_segments" in sql:
            return StubResult(
                rows=[
                    {
                        "id": 501,
                        "council": "A",
                        "committee": "B",
                        "session": "C",
                        "meeting_no": "C 1th",
                        "meeting_date": "2025-01-02",
                        "summary": "s",
                        "subject": "sub",
                        "tag": "[]",
                        "importance": 2,
                        "moderator": "{}",
                        "questioner": "{}",
                        "answerer": "{}",
                        "party": "P",
                        "constituency": "X",
                        "department": "D",
                    }
                ]
            )
        return StubResult()

    engine = use_stub_connection_provider(handler)

    resp = client.get(
        "/api/segments?page=2&size=1&q=budget&council=A&committee=B&session=C&meeting_no=C%201th&importance=2&party=P&constituency=X&department=D&from=2025-01-01&to=2025-01-31"
    )
    data = resp.get_json()

    assert resp.status_code == 200
    assert data["page"] == 2
    assert data["size"] == 1
    assert data["total"] == 1
    assert data["items"][0]["id"] == 501

    first_select = next(
        c for c in engine.connection.calls if isinstance(c.get("params"), dict) and "limit" in c["params"]
    )
    assert first_select["params"]["limit"] == 1
    assert first_select["params"]["offset"] == 1
    assert first_select["params"]["q"] == "%budget%"
    assert first_select["params"]["council"] == "A"
    assert first_select["params"]["committee"] == "B"
    assert first_select["params"]["session"] == "C"
    assert first_select["params"]["meeting_no"] == "C 1th"
    assert first_select["params"]["importance"] == 2
    assert first_select["params"]["party"] == "P"
    assert first_select["params"]["constituency"] == "X"
    assert first_select["params"]["department"] == "D"
    assert first_select["params"]["date_from"] == "2025-01-01"
    assert first_select["params"]["date_to"] == "2025-01-31"


def test_get_segment_success_and_404(client, use_stub_connection_provider):
    def handler(statement, params):
        sql = str(statement).lower()
        if "from council_speech_segments" in sql and "where id=:id" in sql and params["id"] == 1:
            return StubResult(
                rows=[
                    {
                        "id": 1,
                        "council": "A",
                        "committee": None,
                        "session": None,
                        "meeting_no": None,
                        "meeting_date": None,
                        "content": None,
                        "summary": None,
                        "subject": None,
                        "tag": None,
                        "importance": None,
                        "moderator": None,
                        "questioner": None,
                        "answerer": None,
                        "party": None,
                        "constituency": None,
                        "department": None,
                        "created_at": "2025-01-01 00:00:00",
                        "updated_at": "2025-01-01 00:00:00",
                    }
                ]
            )
        if "from council_speech_segments" in sql and "where id=:id" in sql and params["id"] == 2:
            return StubResult(rows=[])
        return StubResult()

    use_stub_connection_provider(handler)

    ok_resp = client.get("/api/segments/1")
    assert ok_resp.status_code == 200
    assert ok_resp.get_json()["id"] == 1

    miss_resp = client.get("/api/segments/2")
    assert miss_resp.status_code == 404
    _assert_not_found_error(miss_resp.get_json())


def test_delete_segment_success_and_not_found(client, use_stub_connection_provider):
    def handler(statement, params):
        sql = str(statement).lower()
        if "delete from council_speech_segments" in sql and params["id"] == 1:
            return StubResult(rowcount=1)
        if "delete from council_speech_segments" in sql and params["id"] == 2:
            return StubResult(rowcount=0)
        return StubResult()

    use_stub_connection_provider(handler)

    ok_resp = client.delete("/api/segments/1")
    assert ok_resp.status_code == 200
    assert ok_resp.get_json() == {"status": "deleted", "id": 1}

    miss_resp = client.delete("/api/segments/2")
    assert miss_resp.status_code == 404
    _assert_not_found_error(miss_resp.get_json())
