from __future__ import annotations

from typing import Any

from sqlalchemy import Text, bindparam, cast, column, func, or_, select, table, text

from app.ports.repositories import SegmentsRepositoryPort
from app.repositories.common import execute_paginated_query, to_json_recordset
from app.repositories.session_provider import ConnectionProvider, open_connection_scope

COUNCIL_SPEECH_SEGMENTS = table(
    "council_speech_segments",
    column("id"),
    column("council"),
    column("committee"),
    column("session"),
    column("meeting_no"),
    column("meeting_no_combined"),
    column("meeting_date"),
    column("content"),
    column("summary"),
    column("subject"),
    column("tag"),
    column("importance"),
    column("moderator"),
    column("questioner"),
    column("answerer"),
    column("party"),
    column("constituency"),
    column("department"),
    column("dedupe_hash"),
    column("created_at"),
    column("updated_at"),
)


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
    conditions = []
    params: dict[str, Any] = {}

    if q:
        q_bind: Any = bindparam("q")
        conditions.append(
            or_(
                cast(COUNCIL_SPEECH_SEGMENTS.c.council, Text).ilike(q_bind),
                cast(COUNCIL_SPEECH_SEGMENTS.c.committee, Text).ilike(q_bind),
                cast(COUNCIL_SPEECH_SEGMENTS.c["session"], Text).ilike(q_bind),
                cast(COUNCIL_SPEECH_SEGMENTS.c.content, Text).ilike(q_bind),
                cast(COUNCIL_SPEECH_SEGMENTS.c.summary, Text).ilike(q_bind),
                cast(COUNCIL_SPEECH_SEGMENTS.c.subject, Text).ilike(q_bind),
                cast(COUNCIL_SPEECH_SEGMENTS.c.party, Text).ilike(q_bind),
                cast(COUNCIL_SPEECH_SEGMENTS.c.constituency, Text).ilike(q_bind),
                cast(COUNCIL_SPEECH_SEGMENTS.c.department, Text).ilike(q_bind),
                cast(COUNCIL_SPEECH_SEGMENTS.c.tag, Text).ilike(q_bind),
                cast(COUNCIL_SPEECH_SEGMENTS.c.questioner, Text).ilike(q_bind),
                cast(COUNCIL_SPEECH_SEGMENTS.c.answerer, Text).ilike(q_bind),
            )
        )
        params["q"] = f"%{q}%"

    if council:
        conditions.append(COUNCIL_SPEECH_SEGMENTS.c.council == bindparam("council"))
        params["council"] = council

    if committee:
        conditions.append(COUNCIL_SPEECH_SEGMENTS.c.committee == bindparam("committee"))
        params["committee"] = committee

    if session:
        conditions.append(COUNCIL_SPEECH_SEGMENTS.c["session"] == bindparam("session"))
        params["session"] = session

    if meeting_no:
        conditions.append(COUNCIL_SPEECH_SEGMENTS.c.meeting_no_combined == bindparam("meeting_no"))
        params["meeting_no"] = meeting_no

    if importance is not None:
        conditions.append(COUNCIL_SPEECH_SEGMENTS.c.importance == bindparam("importance"))
        params["importance"] = importance

    if party:
        conditions.append(COUNCIL_SPEECH_SEGMENTS.c.party == bindparam("party"))
        params["party"] = party

    if constituency:
        conditions.append(COUNCIL_SPEECH_SEGMENTS.c.constituency == bindparam("constituency"))
        params["constituency"] = constituency

    if department:
        conditions.append(COUNCIL_SPEECH_SEGMENTS.c.department == bindparam("department"))
        params["department"] = department

    if date_from:
        conditions.append(COUNCIL_SPEECH_SEGMENTS.c.meeting_date >= bindparam("date_from"))
        params["date_from"] = date_from

    if date_to:
        conditions.append(COUNCIL_SPEECH_SEGMENTS.c.meeting_date <= bindparam("date_to"))
        params["date_to"] = date_to

    list_stmt = (
        select(
            COUNCIL_SPEECH_SEGMENTS.c.id,
            COUNCIL_SPEECH_SEGMENTS.c.council,
            COUNCIL_SPEECH_SEGMENTS.c.committee,
            COUNCIL_SPEECH_SEGMENTS.c["session"],
            COUNCIL_SPEECH_SEGMENTS.c.meeting_no_combined.label("meeting_no"),
            COUNCIL_SPEECH_SEGMENTS.c.meeting_date,
            COUNCIL_SPEECH_SEGMENTS.c.summary,
            COUNCIL_SPEECH_SEGMENTS.c.subject,
            COUNCIL_SPEECH_SEGMENTS.c.tag,
            COUNCIL_SPEECH_SEGMENTS.c.importance,
            COUNCIL_SPEECH_SEGMENTS.c.moderator,
            COUNCIL_SPEECH_SEGMENTS.c.questioner,
            COUNCIL_SPEECH_SEGMENTS.c.answerer,
            COUNCIL_SPEECH_SEGMENTS.c.party,
            COUNCIL_SPEECH_SEGMENTS.c.constituency,
            COUNCIL_SPEECH_SEGMENTS.c.department,
        )
        .order_by(
            func.coalesce(COUNCIL_SPEECH_SEGMENTS.c.meeting_date, COUNCIL_SPEECH_SEGMENTS.c.created_at).desc(),
            COUNCIL_SPEECH_SEGMENTS.c.id.desc(),
        )
        .limit(bindparam("limit"))
        .offset(bindparam("offset"))
    )

    count_stmt = select(func.count().label("total")).select_from(COUNCIL_SPEECH_SEGMENTS)

    if conditions:
        for condition in conditions:
            list_stmt = list_stmt.where(condition)
            count_stmt = count_stmt.where(condition)

    return execute_paginated_query(
        list_stmt=list_stmt,
        count_stmt=count_stmt,
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
