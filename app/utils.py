from datetime import date, datetime
from typing import Any, Callable, Mapping, Optional, Tuple, TypeVar

from fastapi import HTTPException, Request

from app.errors import http_error

T = TypeVar("T")


def bad_request(message: str) -> HTTPException:
    return http_error(400, "BAD_REQUEST", message)


def parse_datetime(dt: Optional[str]) -> Optional[datetime]:
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


def parse_date(d: Optional[str]) -> Optional[datetime]:
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


def parse_int_query_arg(
    query_params: Mapping[str, Any],
    name: str,
    *,
    default: int,
    min_value: int,
    max_value: Optional[int] = None,
) -> int:
    raw = query_params.get(name, str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise bad_request(f"{name}는 정수여야 합니다.")

    if value < min_value:
        raise bad_request(f"{name}는 {min_value} 이상이어야 합니다.")

    if max_value is not None and value > max_value:
        raise bad_request(f"{name}는 {max_value} 이하여야 합니다.")

    return value


def parse_pagination(query_params: Mapping[str, Any]) -> Tuple[int, int]:
    page = parse_int_query_arg(query_params, "page", default=1, min_value=1)
    size = parse_int_query_arg(query_params, "size", default=20, min_value=1, max_value=200)
    return page, size


def parse_date_query_arg(query_params: Mapping[str, Any], name: str) -> Optional[str]:
    raw = query_params.get(name)
    if raw is None or raw == "":
        return None

    try:
        datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        raise bad_request(f"{name}은 YYYY-MM-DD 형식이어야 합니다.")

    return str(raw)


def normalize_payload(payload, normalizer: Callable[[dict], T]) -> Tuple[T, ...]:
    if isinstance(payload, list):
        return tuple(normalizer(item) for item in payload)
    if isinstance(payload, dict):
        return (normalizer(payload),)
    raise bad_request("요청 형식 오류: 객체 또는 배열이어야 합니다.")


def combine_meeting_no(session_val, meeting_no_raw, meeting_no_int) -> Optional[str]:
    if isinstance(meeting_no_raw, str) and meeting_no_raw.strip():
        return meeting_no_raw.strip()
    if meeting_no_int is not None and session_val:
        return f"{session_val} {int(meeting_no_int)}차"
    if meeting_no_int is not None:
        return f"{int(meeting_no_int)}차"
    return session_val


async def read_json_payload(request: Request, *, require_json_content_type: bool, parse_error_message: str) -> Any:
    content_type = request.headers.get("content-type", "")
    if require_json_content_type and "application/json" not in content_type.lower():
        raise bad_request("JSON 본문이 필요합니다.")

    try:
        payload = await request.json()
    except Exception:
        raise bad_request(parse_error_message)

    if payload is None:
        raise bad_request(parse_error_message)

    return payload
