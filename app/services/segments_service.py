from __future__ import annotations

from typing import Any, Dict, Optional

from app.utils import bad_request, combine_meeting_no, parse_date


def normalize_segment(item: Dict[str, Any]) -> Dict[str, Any]:
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


def parse_importance_value(raw: Any, *, required: bool) -> Optional[int]:
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


def parse_importance_query(raw: Optional[str]) -> Optional[int]:
    if raw is None:
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise bad_request("importance는 정수여야 합니다.")
    if value not in (1, 2, 3):
        raise bad_request("importance는 1,2,3 중 하나여야 합니다.")
    return value
