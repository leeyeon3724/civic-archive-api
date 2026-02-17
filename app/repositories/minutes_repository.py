from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app.ports.repositories import MinutesRepositoryPort
from app.repositories.common import accumulate_upsert_result, build_where_clause, execute_paginated_query
from app.repositories.session_provider import ConnectionProvider, open_connection_scope


def upsert_minutes(
    items: List[Dict[str, Any]],
    *,
    connection_provider: ConnectionProvider | None = None,
) -> Tuple[int, int]:
    inserted = 0
    updated = 0

    sql = text(
        """
        INSERT INTO council_minutes
          (council, committee, "session", meeting_no, meeting_no_combined, url, meeting_date, content, tag, attendee, agenda)
        VALUES
          (:council, :committee, :session, :meeting_no, :meeting_no_combined, :url, :meeting_date, :content,
           CAST(:tag AS jsonb), CAST(:attendee AS jsonb), CAST(:agenda AS jsonb))
        ON CONFLICT (url) DO UPDATE SET
          council = EXCLUDED.council,
          committee = EXCLUDED.committee,
          "session" = EXCLUDED."session",
          meeting_no = EXCLUDED.meeting_no,
          meeting_no_combined = EXCLUDED.meeting_no_combined,
          meeting_date = EXCLUDED.meeting_date,
          content = EXCLUDED.content,
          tag = EXCLUDED.tag,
          attendee = EXCLUDED.attendee,
          agenda = EXCLUDED.agenda,
          updated_at = CURRENT_TIMESTAMP
        RETURNING (xmax = 0) AS inserted
        """
    )

    with open_connection_scope(connection_provider) as conn:
        for minute in items:
            params = {
                "council": minute.get("council"),
                "committee": minute.get("committee"),
                "session": minute.get("session"),
                "meeting_no": minute.get("meeting_no"),
                "meeting_no_combined": minute.get("meeting_no_combined"),
                "url": minute.get("url"),
                "meeting_date": minute.get("meeting_date"),
                "content": minute.get("content"),
                "tag": json.dumps(minute.get("tag")) if minute.get("tag") is not None else None,
                "attendee": json.dumps(minute.get("attendee")) if minute.get("attendee") is not None else None,
                "agenda": json.dumps(minute.get("agenda")) if minute.get("agenda") is not None else None,
            }
            result = conn.execute(sql, params)
            inserted, updated = accumulate_upsert_result(result, inserted=inserted, updated=updated)

    return inserted, updated


def list_minutes(
    *,
    q: Optional[str],
    council: Optional[str],
    committee: Optional[str],
    session: Optional[str],
    meeting_no: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    page: int,
    size: int,
    connection_provider: ConnectionProvider | None = None,
) -> Tuple[List[Dict[str, Any]], int]:
    where = []
    params: Dict[str, Any] = {}

    if q:
        where.append(
            "(" 
            "council ILIKE :q OR committee ILIKE :q OR \"session\" ILIKE :q "
            "OR content ILIKE :q OR CAST(agenda AS TEXT) ILIKE :q"
            ")"
        )
        params["q"] = f"%{q}%"

    if council:
        where.append("council = :council")
        params["council"] = council

    if committee:
        where.append("committee = :committee")
        params["committee"] = committee

    if session:
        where.append('"session" = :session')
        params["session"] = session

    if meeting_no:
        where.append("meeting_no_combined = :meeting_no")
        params["meeting_no"] = meeting_no

    if date_from:
        where.append("meeting_date >= :date_from")
        params["date_from"] = date_from

    if date_to:
        where.append("meeting_date <= :date_to")
        params["date_to"] = date_to

    where_sql = build_where_clause(where)

    list_sql = f"""
        SELECT
            id, council, committee, "session",
            meeting_no_combined AS meeting_no,
            url, meeting_date, tag, attendee, agenda, created_at, updated_at
        FROM council_minutes
        {where_sql}
        ORDER BY COALESCE(meeting_date, created_at) DESC, id DESC
        LIMIT :limit OFFSET :offset
        """

    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM council_minutes
        {where_sql}
        """

    return execute_paginated_query(
        list_sql=list_sql,
        count_sql=count_sql,
        params=params,
        page=page,
        size=size,
        connection_provider=connection_provider,
    )


def get_minutes(
    item_id: int,
    *,
    connection_provider: ConnectionProvider | None = None,
) -> Optional[Dict[str, Any]]:
    sql = text(
        """
        SELECT id, council, committee, "session", meeting_no_combined AS meeting_no,
               url, meeting_date, content, tag, attendee, agenda, created_at, updated_at
        FROM council_minutes
        WHERE id=:id
        """
    )

    with open_connection_scope(connection_provider) as conn:
        row = conn.execute(sql, {"id": item_id}).mappings().first()

    return dict(row) if row else None


def delete_minutes(
    item_id: int,
    *,
    connection_provider: ConnectionProvider | None = None,
) -> bool:
    with open_connection_scope(connection_provider) as conn:
        result = conn.execute(text("DELETE FROM council_minutes WHERE id=:id"), {"id": item_id})

    return result.rowcount > 0


class MinutesRepository(MinutesRepositoryPort):
    def __init__(self, *, connection_provider: ConnectionProvider | None = None) -> None:
        self._connection_provider = connection_provider

    def upsert_minutes(self, items: List[Dict[str, Any]]) -> Tuple[int, int]:
        return upsert_minutes(items, connection_provider=self._connection_provider)

    def list_minutes(
        self,
        *,
        q: Optional[str],
        council: Optional[str],
        committee: Optional[str],
        session: Optional[str],
        meeting_no: Optional[str],
        date_from: Optional[str],
        date_to: Optional[str],
        page: int,
        size: int,
    ) -> Tuple[List[Dict[str, Any]], int]:
        return list_minutes(
            q=q,
            council=council,
            committee=committee,
            session=session,
            meeting_no=meeting_no,
            date_from=date_from,
            date_to=date_to,
            page=page,
            size=size,
            connection_provider=self._connection_provider,
        )

    def get_minutes(self, item_id: int) -> Optional[Dict[str, Any]]:
        return get_minutes(item_id, connection_provider=self._connection_provider)

    def delete_minutes(self, item_id: int) -> bool:
        return delete_minutes(item_id, connection_provider=self._connection_provider)
