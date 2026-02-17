from __future__ import annotations

from typing import Any, Dict, Tuple

from sqlalchemy import text

from app import database


def accumulate_upsert_result(result, *, inserted: int, updated: int) -> Tuple[int, int]:
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


def execute_paginated_query(
    *,
    list_sql: str,
    count_sql: str,
    params: Dict[str, Any],
    page: int,
    size: int,
) -> Tuple[list[dict[str, Any]], int]:
    with database.engine.begin() as conn:
        rows = conn.execute(
            text(list_sql),
            {**params, "limit": size, "offset": (page - 1) * size},
        ).mappings().all()
        total = conn.execute(text(count_sql), params).scalar() or 0

    return [dict(row) for row in rows], int(total)
