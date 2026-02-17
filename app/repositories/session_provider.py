from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import Any, TypeAlias

import app.database as database

ConnectionScope: TypeAlias = AbstractContextManager[Any]
ConnectionProvider: TypeAlias = Callable[[], ConnectionScope]


def _default_connection_provider() -> ConnectionScope:
    if database.engine is None:
        raise RuntimeError("database engine is not initialized")
    return database.engine.begin()


_connection_provider: ConnectionProvider = _default_connection_provider


def get_connection_provider() -> ConnectionProvider:
    return _connection_provider


def set_connection_provider(provider: ConnectionProvider) -> None:
    global _connection_provider
    _connection_provider = provider


def reset_connection_provider() -> None:
    global _connection_provider
    _connection_provider = _default_connection_provider


def open_connection_scope(provider: ConnectionProvider | None = None) -> ConnectionScope:
    selected_provider = provider or get_connection_provider()
    return selected_provider()
