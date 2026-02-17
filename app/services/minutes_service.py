from __future__ import annotations

from typing import Any, Dict

from app.utils import bad_request, combine_meeting_no, parse_date


def normalize_minutes(item: Dict[str, Any]) -> Dict[str, Any]:
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
