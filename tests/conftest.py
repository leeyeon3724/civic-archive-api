from typing import Any, Callable, Dict, List, Optional
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


def pytest_addoption(parser):
    parser.addoption(
        "--base-url",
        default="http://localhost:8000",
        help="E2E 테스트 대상 서버 URL (기본: http://localhost:8000)",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "e2e: 라이브 서버 대상 E2E 테스트")
    config.addinivalue_line("markers", "integration: PostgreSQL 컨테이너 기반 통합 테스트")


class StubResult:
    def __init__(
        self,
        *,
        rowcount: int = 0,
        rows: Optional[List[Dict[str, Any]]] = None,
        scalar_value: Optional[Any] = None,
    ) -> None:
        self.rowcount = rowcount
        self._rows = rows or []
        self._scalar_value = scalar_value

    def mappings(self) -> "StubResult":
        return self

    def all(self) -> List[Dict[str, Any]]:
        return self._rows

    def first(self) -> Optional[Dict[str, Any]]:
        return self._rows[0] if self._rows else None

    def scalar(self) -> Optional[Any]:
        return self._scalar_value


class StubConnection:
    def __init__(self, handler: Callable[[Any, Optional[Dict[str, Any]]], StubResult]) -> None:
        self._handler = handler
        self.calls: List[Dict[str, Any]] = []

    def execute(self, statement: Any, params: Optional[Dict[str, Any]] = None) -> StubResult:
        self.calls.append({"statement": str(statement), "params": params})
        return self._handler(statement, params)


class StubBeginContext:
    def __init__(self, connection: StubConnection) -> None:
        self._connection = connection

    def __enter__(self) -> StubConnection:
        return self._connection

    def __exit__(self, exc_type, exc_value, traceback) -> bool:
        return False


class StubEngine:
    def __init__(self, handler: Optional[Callable[[Any, Optional[Dict[str, Any]]], StubResult]] = None) -> None:
        if handler is None:
            def _default_handler(_statement, _params):
                return StubResult()

            handler = _default_handler
        self.connection = StubConnection(handler)

    def begin(self) -> StubBeginContext:
        return StubBeginContext(self.connection)


class ResponseAdapter:
    def __init__(self, response):
        self._response = response

    @property
    def status_code(self):
        return self._response.status_code

    def get_json(self):
        return self._response.json()

    def json(self):
        return self._response.json()

    def __getattr__(self, item):
        return getattr(self._response, item)


class ClientAdapter:
    def __init__(self, client: TestClient):
        self._client = client

    @staticmethod
    def _normalize_kwargs(kwargs: Dict[str, Any]) -> Dict[str, Any]:
        normalized = dict(kwargs)
        content_type = normalized.pop("content_type", None)
        if content_type:
            headers = dict(normalized.get("headers") or {})
            headers["Content-Type"] = content_type
            normalized["headers"] = headers
            if "data" in normalized and "content" not in normalized:
                normalized["content"] = normalized.pop("data")
        return normalized

    def get(self, *args, **kwargs):
        return ResponseAdapter(self._client.get(*args, **self._normalize_kwargs(kwargs)))

    def post(self, *args, **kwargs):
        return ResponseAdapter(self._client.post(*args, **self._normalize_kwargs(kwargs)))

    def delete(self, *args, **kwargs):
        return ResponseAdapter(self._client.delete(*args, **self._normalize_kwargs(kwargs)))

    def request(self, *args, **kwargs):
        return ResponseAdapter(self._client.request(*args, **self._normalize_kwargs(kwargs)))


@pytest.fixture(scope="session")
def app_instance():
    import_engine = StubEngine()
    with patch("app.database.create_engine", return_value=import_engine):
        from app import create_app

        api = create_app()
    api._bootstrap_engine_for_test = import_engine
    return api


@pytest.fixture(scope="session")
def db_module():
    from app import database

    return database


@pytest.fixture(scope="session")
def utils_module():
    from app import utils

    return utils


@pytest.fixture(scope="session")
def news_module():
    from app.routes import news

    return news


@pytest.fixture(scope="session")
def minutes_module():
    from app.routes import minutes

    return minutes


@pytest.fixture(scope="session")
def segments_module():
    from app.routes import segments

    return segments


@pytest.fixture
def client(app_instance):
    with TestClient(app_instance) as tc:
        yield ClientAdapter(tc)


@pytest.fixture
def make_engine():
    def _factory(handler: Callable[[Any, Optional[Dict[str, Any]]], StubResult]) -> StubEngine:
        return StubEngine(handler=handler)

    return _factory
