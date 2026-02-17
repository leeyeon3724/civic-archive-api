from datetime import date, datetime

from fastapi import HTTPException

from app.errors import http_error
from app.parsing import parse_date_value, parse_datetime_value


def bad_request(message: str) -> HTTPException:
    return http_error(400, "BAD_REQUEST", message)


def parse_datetime(dt: str | datetime | date | None) -> datetime | None:
    try:
        return parse_datetime_value(dt)
    except ValueError:
        raise bad_request(f"published_at format error: {dt}")


def parse_date(d: str | datetime | date | None) -> datetime | None:
    try:
        parsed = parse_date_value(d)
    except ValueError:
        raise bad_request(f"meeting_date format error (YYYY-MM-DD): {d}")
    if parsed is None:
        return None
    return datetime.combine(parsed, datetime.min.time())


def combine_meeting_no(session_val, meeting_no_raw, meeting_no_int) -> str | None:
    if isinstance(meeting_no_raw, str) and meeting_no_raw.strip():
        return meeting_no_raw.strip()
    if meeting_no_int is not None and session_val:
        return f"{session_val} {int(meeting_no_int)}\ucc28"
    if meeting_no_int is not None:
        return f"{int(meeting_no_int)}\ucc28"
    return session_val
