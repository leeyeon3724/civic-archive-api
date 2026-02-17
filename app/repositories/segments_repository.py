from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import text

from app.repositories.common import build_where_clause, execute_paginated_query
from app.repositories.session_provider import ConnectionProvider, open_connection_scope


def insert_segments(
    items: List[Dict[str, Any]],
    *,
    connection_provider: ConnectionProvider | None = None,
) -> int:
    sql = text(
        """
        INSERT INTO council_speech_segments
          (council, committee, "session", meeting_no, meeting_no_combined, meeting_date,
           content, summary, subject, tag, importance, moderator, questioner, answerer,
           party, constituency, department, dedupe_hash)
        VALUES
          (:council, :committee, :session, :meeting_no, :meeting_no_combined, :meeting_date,
           :content, :summary, :subject, CAST(:tag AS jsonb), :importance,
           CAST(:moderator AS jsonb), CAST(:questioner AS jsonb), CAST(:answerer AS jsonb),
           :party, :constituency, :department, :dedupe_hash)
        ON CONFLICT (dedupe_hash) DO NOTHING
        """
    )

    inserted = 0
    with open_connection_scope(connection_provider) as conn:
        for segment in items:
            params = {
                "council": segment.get("council"),
                "committee": segment.get("committee"),
                "session": segment.get("session"),
                "meeting_no": segment.get("meeting_no"),
                "meeting_no_combined": segment.get("meeting_no_combined"),
                "meeting_date": segment.get("meeting_date"),
                "content": segment.get("content"),
                "summary": segment.get("summary"),
                "subject": segment.get("subject"),
                "tag": json.dumps(segment.get("tag")) if segment.get("tag") is not None else None,
                "importance": segment.get("importance"),
                "moderator": json.dumps(segment.get("moderator")) if segment.get("moderator") is not None else None,
                "questioner": json.dumps(segment.get("questioner")) if segment.get("questioner") is not None else None,
                "answerer": json.dumps(segment.get("answerer")) if segment.get("answerer") is not None else None,
                "party": segment.get("party"),
                "constituency": segment.get("constituency"),
                "department": segment.get("department"),
                "dedupe_hash": segment.get("dedupe_hash"),
            }
            result = conn.execute(sql, params)
            inserted += max(0, int(result.rowcount or 0))

    return inserted


def list_segments(
    *,
    q: Optional[str],
    council: Optional[str],
    committee: Optional[str],
    session: Optional[str],
    meeting_no: Optional[str],
    importance: Optional[int],
    party: Optional[str],
    constituency: Optional[str],
    department: Optional[str],
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
    connection_provider: ConnectionProvider | None = None,
) -> Optional[Dict[str, Any]]:
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
    connection_provider: ConnectionProvider | None = None,
) -> bool:
    with open_connection_scope(connection_provider) as conn:
        result = conn.execute(text("DELETE FROM council_speech_segments WHERE id=:id"), {"id": item_id})

    return result.rowcount > 0
