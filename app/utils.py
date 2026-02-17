from datetime import date, datetime

from fastapi import HTTPException

from app.errors import http_error


def bad_request(message: str) -> HTTPException:
    return http_error(400, "BAD_REQUEST", message)


def parse_datetime(dt: str | datetime | date | None) -> datetime | None:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return dt
    if isinstance(dt, date):
        return datetime.combine(dt, datetime.min.time())
    for fmt in ["%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
        try:
            return datetime.strptime(dt, fmt)
        except ValueError:
            continue
    raise bad_request(f"published_at 형식 오류: {dt}")


def parse_date(d: str | datetime | date | None) -> datetime | None:
    if d is None:
        return None
    if isinstance(d, datetime):
        return d
    if isinstance(d, date):
        return datetime.combine(d, datetime.min.time())
    try:
        return datetime.strptime(d, "%Y-%m-%d")
    except ValueError:
        raise bad_request(f"meeting_date 형식 오류(YYYY-MM-DD): {d}")


def combine_meeting_no(session_val, meeting_no_raw, meeting_no_int) -> str | None:
    if isinstance(meeting_no_raw, str) and meeting_no_raw.strip():
        return meeting_no_raw.strip()
    if meeting_no_int is not None and session_val:
        return f"{session_val} {int(meeting_no_int)}차"
    if meeting_no_int is not None:
        return f"{int(meeting_no_int)}차"
    return session_val
