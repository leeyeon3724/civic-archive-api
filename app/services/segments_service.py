from __future__ import annotations

from typing import Any

from app.repositories.segments_repository import (
    delete_segment as repository_delete_segment,
    get_segment as repository_get_segment,
    insert_segments as repository_insert_segments,
    list_segments as repository_list_segments,
)
from app.utils import bad_request, combine_meeting_no, parse_date


def normalize_segment(item: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise bad_request("각 아이템은 JSON 객체여야 합니다.")

    council = item.get("council")
    if not council:
        raise bad_request("필수 필드 누락: council")

    session = item.get("session")
    meeting_no_raw = item.get("meeting_no")

    meeting_no_int = None
    if meeting_no_raw is not None and not isinstance(meeting_no_raw, str):
        try:
            meeting_no_int = int(meeting_no_raw)
        except (TypeError, ValueError):
            meeting_no_int = None

    meeting_date = parse_date(item.get("meeting_date"))

    return {
        "council": council,
        "committee": item.get("committee"),
        "session": session,
        "meeting_no": meeting_no_int,
        "meeting_no_combined": combine_meeting_no(session, meeting_no_raw, meeting_no_int),
        "meeting_date": meeting_date.date() if meeting_date else None,
        "content": item.get("content"),
        "summary": item.get("summary"),
        "subject": item.get("subject"),
        "tag": item.get("tag"),
        "importance": parse_importance_value(item.get("importance"), required=False),
        "moderator": item.get("moderator"),
        "questioner": item.get("questioner"),
        "answerer": item.get("answerer"),
        "party": item.get("party"),
        "constituency": item.get("constituency"),
        "department": item.get("department"),
    }


def parse_importance_value(raw: Any, *, required: bool) -> int | None:
    if raw is None:
        if required:
            raise bad_request("importance는 1,2,3 중 정수여야 합니다.")
        return None

    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise bad_request("importance는 1,2,3 중 정수여야 합니다.")

    if value not in (1, 2, 3):
        raise bad_request("importance는 1,2,3 중 하나여야 합니다.")

    return value


def parse_importance_query(raw: str | None) -> int | None:
    if raw is None:
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise bad_request("importance는 정수여야 합니다.")
    if value not in (1, 2, 3):
        raise bad_request("importance는 1,2,3 중 하나여야 합니다.")
    return value


def insert_segments(items: list[dict[str, Any]]) -> int:
    return repository_insert_segments(items)


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
) -> tuple[list[dict[str, Any]], int]:
    return repository_list_segments(
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
    )


def get_segment(item_id: int) -> dict[str, Any] | None:
    return repository_get_segment(item_id)


def delete_segment(item_id: int) -> bool:
    return repository_delete_segment(item_id)
