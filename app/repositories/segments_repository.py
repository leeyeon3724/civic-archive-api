from __future__ import annotations

from typing import Any

from sqlalchemy import text

from app.ports.repositories import SegmentsRepositoryPort
from app.repositories.common import build_where_clause, execute_paginated_query, to_json_recordset
from app.repositories.session_provider import ConnectionProvider, open_connection_scope


def insert_segments(
    items: list[dict[str, Any]],
    *,
    connection_provider: ConnectionProvider,
) -> int:
    if not items:
        return 0

    payload_rows = [
        {
            "council": segment.get("council"),
            "committee": segment.get("committee"),
            "session": segment.get("session"),
            "meeting_no": segment.get("meeting_no"),
            "meeting_no_combined": segment.get("meeting_no_combined"),
            "meeting_date": segment.get("meeting_date"),
            "content": segment.get("content"),
            "summary": segment.get("summary"),
            "subject": segment.get("subject"),
            "tag": segment.get("tag"),
            "importance": segment.get("importance"),
            "moderator": segment.get("moderator"),
            "questioner": segment.get("questioner"),
            "answerer": segment.get("answerer"),
            "party": segment.get("party"),
            "constituency": segment.get("constituency"),
            "department": segment.get("department"),
            "dedupe_hash": segment.get("dedupe_hash"),
        }
        for segment in items
    ]

    sql = text(
        """
        WITH payload AS (
            SELECT *
            FROM jsonb_to_recordset(CAST(:items AS jsonb))
              AS p(
                council text,
                committee text,
                session text,
                meeting_no integer,
                meeting_no_combined text,
                meeting_date date,
                content text,
                summary text,
                subject text,
                tag jsonb,
                importance integer,
                moderator jsonb,
                questioner jsonb,
                answerer jsonb,
                party text,
                constituency text,
                department text,
                dedupe_hash text
              )
        ),
        inserted_rows AS (
            INSERT INTO council_speech_segments
              (council, committee, "session", meeting_no, meeting_no_combined, meeting_date,
               content, summary, subject, tag, importance, moderator, questioner, answerer,
               party, constituency, department, dedupe_hash)
            SELECT
              council,
              committee,
              session,
              meeting_no,
              meeting_no_combined,
              meeting_date,
              content,
              summary,
              subject,
              tag,
              importance,
              moderator,
              questioner,
              answerer,
              party,
              constituency,
              department,
              dedupe_hash
            FROM payload
            ON CONFLICT (dedupe_hash) DO NOTHING
            RETURNING 1
        )
        SELECT COUNT(*) AS inserted
        FROM inserted_rows
        """
    )

    with open_connection_scope(connection_provider) as conn:
        row = conn.execute(sql, {"items": to_json_recordset(payload_rows)}).mappings().first() or {}

    return int(row.get("inserted") or 0)


def list_segments(
    *,
    q: str | None,
    council: str | None,
    committee: str | None,
    session: str | None,
    meeting_no: str | None,
    importance: int | None,
    party: str | None,
    constituency: str | None,
    department: str | None,
    date_from: str | None,
    date_to: str | None,
    page: int,
    size: int,
    connection_provider: ConnectionProvider,
) -> tuple[list[dict[str, Any]], int]:
    where = []
    params: dict[str, Any] = {}

    if q:
        where.append(
            "(" 
            "council ILIKE :q OR committee ILIKE :q OR \"session\" ILIKE :q "
            "OR content ILIKE :q OR summary ILIKE :q OR subject ILIKE :q "
            "OR party ILIKE :q OR constituency ILIKE :q OR department ILIKE :q "
            "OR CAST(tag AS TEXT) ILIKE :q "
            "OR CAST(questioner AS TEXT) ILIKE :q "
            "OR CAST(answerer AS TEXT) ILIKE :q"
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

    if importance is not None:
        where.append("importance = :importance")
        params["importance"] = importance

    if party:
        where.append("party = :party")
        params["party"] = party

    if constituency:
        where.append("constituency = :constituency")
        params["constituency"] = constituency

    if department:
        where.append("department = :department")
        params["department"] = department

    if date_from:
        where.append("meeting_date >= :date_from")
        params["date_from"] = date_from

    if date_to:
        where.append("meeting_date <= :date_to")
        params["date_to"] = date_to

    where_sql = build_where_clause(where)

    list_sql = f"""
        SELECT
            id, council, committee, "session", meeting_no_combined AS meeting_no, meeting_date,
            summary, subject, tag, importance, moderator, questioner, answerer,
            party, constituency, department
        FROM council_speech_segments
        {where_sql}
        ORDER BY COALESCE(meeting_date, created_at) DESC, id DESC
        LIMIT :limit OFFSET :offset
        """

    count_sql = f"""
        SELECT COUNT(*) AS total
        FROM council_speech_segments
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


def get_segment(
    item_id: int,
    *,
    connection_provider: ConnectionProvider,
) -> dict[str, Any] | None:
    sql = text(
        """
        SELECT id, council, committee, "session",
               meeting_no_combined AS meeting_no, meeting_date,
               content, summary, subject, tag, importance,
               moderator, questioner, answerer,
               party, constituency, department,
               created_at, updated_at
        FROM council_speech_segments
        WHERE id=:id
        """
    )

    with open_connection_scope(connection_provider) as conn:
        row = conn.execute(sql, {"id": item_id}).mappings().first()

    return dict(row) if row else None


def delete_segment(
    item_id: int,
    *,
    connection_provider: ConnectionProvider,
) -> bool:
    with open_connection_scope(connection_provider) as conn:
        result = conn.execute(text("DELETE FROM council_speech_segments WHERE id=:id"), {"id": item_id})

    return result.rowcount > 0


class SegmentsRepository(SegmentsRepositoryPort):
    def __init__(self, *, connection_provider: ConnectionProvider) -> None:
        self._connection_provider = connection_provider

    def insert_segments(self, items: list[dict[str, Any]]) -> int:
        return insert_segments(items, connection_provider=self._connection_provider)

    def list_segments(
        self,
        *,
        q: str | None,
        council: str | None,
        committee: str | None,
        session: str | None,
        meeting_no: str | None,
        importance: int | None,
        party: str | None,
        constituency: str | None,
        department: str | None,
        date_from: str | None,
        date_to: str | None,
        page: int,
        size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        return list_segments(
            q=q,
            council=council,
            committee=committee,
            session=session,
            meeting_no=meeting_no,
            importance=importance,
            party=party,
            constituency=constituency,
            department=department,
            date_from=date_from,
            date_to=date_to,
            page=page,
            size=size,
            connection_provider=self._connection_provider,
        )

    def get_segment(self, item_id: int) -> dict[str, Any] | None:
        return get_segment(item_id, connection_provider=self._connection_provider)

    def delete_segment(self, item_id: int) -> bool:
        return delete_segment(item_id, connection_provider=self._connection_provider)
