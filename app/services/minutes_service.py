from __future__ import annotations

from typing import Any

from app.repositories.minutes_repository import (
    delete_minutes as repository_delete_minutes,
    get_minutes as repository_get_minutes,
    list_minutes as repository_list_minutes,
    upsert_minutes as repository_upsert_minutes,
)
from app.utils import bad_request, combine_meeting_no, parse_date


def normalize_minutes(item: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise bad_request("각 아이템은 JSON 객체여야 합니다.")

    council = item.get("council")
    url = item.get("url")
    if not council or not url:
        raise bad_request("필수 필드 누락: council, url")

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
        "url": url,
        "meeting_date": meeting_date.date() if meeting_date else None,
        "content": item.get("content"),
        "tag": item.get("tag"),
        "attendee": item.get("attendee"),
        "agenda": item.get("agenda"),
    }


def upsert_minutes(items: list[dict[str, Any]]) -> tuple[int, int]:
    return repository_upsert_minutes(items)


def list_minutes(
    *,
    q: str | None,
    council: str | None,
    committee: str | None,
    session: str | None,
    meeting_no: str | None,
    date_from: str | None,
    date_to: str | None,
    page: int,
    size: int,
) -> tuple[list[dict[str, Any]], int]:
    return repository_list_minutes(
        q=q,
        council=council,
        committee=committee,
        session=session,
        meeting_no=meeting_no,
        date_from=date_from,
        date_to=date_to,
        page=page,
        size=size,
    )


def get_minutes(item_id: int) -> dict[str, Any] | None:
    return repository_get_minutes(item_id)


def delete_minutes(item_id: int) -> bool:
    return repository_delete_minutes(item_id)
