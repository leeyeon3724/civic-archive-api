from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from sqlalchemy import text

from app.repositories.session_provider import ConnectionProvider, open_connection_scope


def accumulate_upsert_result(result, *, inserted: int, updated: int) -> tuple[int, int]:
    inserted_flag = None

    scalar = getattr(result, "scalar", None)
    if callable(scalar):
        try:
            inserted_flag = scalar()
        except Exception:
            inserted_flag = None

    if inserted_flag is True:
        return inserted + 1, updated
    if inserted_flag is False:
        return inserted, updated + 1

    rowcount = getattr(result, "rowcount", 0)
    if rowcount == 1:
        return inserted + 1, updated
    if rowcount == 2:
        return inserted, updated + 1
    return inserted, updated


def build_where_clause(where: list[str]) -> str:
    return (" WHERE " + " AND ".join(where)) if where else ""


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def to_json_recordset(items: list[dict[str, Any]]) -> str:
    return json.dumps(items, ensure_ascii=False, default=_json_default, separators=(",", ":"))


def execute_paginated_query(
    *,
    list_sql: str,
    count_sql: str,
    params: dict[str, Any],
    page: int,
    size: int,
    connection_provider: ConnectionProvider,
) -> tuple[list[dict[str, Any]], int]:
    with open_connection_scope(connection_provider) as conn:
        rows = conn.execute(
            text(list_sql),
            {**params, "limit": size, "offset": (page - 1) * size},
        ).mappings().all()
        total = conn.execute(text(count_sql), params).scalar() or 0

    return [dict(row) for row in rows], int(total)
