from conftest import StubResult

from app.repositories import news_repository
from app.repositories import session_provider as session_provider_module


def test_open_connection_scope_uses_default_database_engine(db_module, monkeypatch, make_engine):
    engine = make_engine(lambda _statement, _params: StubResult())
    monkeypatch.setattr(db_module, "engine", engine)

    with session_provider_module.open_connection_scope() as conn:
        conn.execute("SELECT 1")

    assert len(engine.connection.calls) == 1


def test_repository_function_accepts_explicit_connection_provider(db_module, monkeypatch, make_engine):
    default_engine = make_engine(lambda _statement, _params: StubResult())
    injected_engine = make_engine(
        lambda statement, _params: StubResult(rows=[{"id": 7}]) if "from news_articles where id=:id" in str(statement).lower() else StubResult()
    )
    monkeypatch.setattr(db_module, "engine", default_engine)

    row = news_repository.get_article(7, connection_provider=injected_engine.begin)
    assert row == {"id": 7}
    assert len(default_engine.connection.calls) == 0
    assert len(injected_engine.connection.calls) == 1


def test_set_connection_provider_overrides_repository_default(db_module, monkeypatch, make_engine):
    default_engine = make_engine(lambda _statement, _params: StubResult(rows=[]))
    injected_engine = make_engine(
        lambda statement, _params: StubResult(rows=[{"id": 21}]) if "from news_articles where id=:id" in str(statement).lower() else StubResult()
    )
    monkeypatch.setattr(db_module, "engine", default_engine)

    session_provider_module.set_connection_provider(injected_engine.begin)
    try:
        row = news_repository.get_article(21)
    finally:
        session_provider_module.reset_connection_provider()

    assert row == {"id": 21}
    assert len(default_engine.connection.calls) == 0
    assert len(injected_engine.connection.calls) == 1
