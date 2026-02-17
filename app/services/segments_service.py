from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from typing import Any, Protocol

from app.repositories.segments_repository import SegmentsRepository
from app.repositories.session_provider import ConnectionProvider
from app.utils import bad_request, combine_meeting_no, parse_date


class SegmentsRepositoryPort(Protocol):
    def insert_segments(self, items: list[dict[str, Any]]) -> int:
        ...

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
        ...

    def get_segment(self, item_id: int) -> dict[str, Any] | None:
        ...

    def delete_segment(self, item_id: int) -> bool:
        ...


def _canonical_json_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [_canonical_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _canonical_json_value(value[key]) for key in sorted(value)}
    return value


def _build_segment_dedupe_hash(item: dict[str, Any]) -> str:
    canonical_payload = _canonical_json_value(
        {
            "council": item.get("council"),
            "committee": item.get("committee"),
            "session": item.get("session"),
            "meeting_no": item.get("meeting_no"),
            "meeting_no_combined": item.get("meeting_no_combined"),
            "meeting_date": item.get("meeting_date"),
            "content": item.get("content"),
            "summary": item.get("summary"),
            "subject": item.get("subject"),
            "tag": item.get("tag"),
            "importance": item.get("importance"),
            "moderator": item.get("moderator"),
            "questioner": item.get("questioner"),
            "answerer": item.get("answerer"),
            "party": item.get("party"),
            "constituency": item.get("constituency"),
            "department": item.get("department"),
        }
    )
    encoded = json.dumps(canonical_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _normalize_segment(item: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise bad_request("Each item must be a JSON object.")

    council = item.get("council")
    if not council:
        raise bad_request("Missing required field: council")

    session = item.get("session")
    meeting_no_raw = item.get("meeting_no")

    meeting_no_int = None
    if meeting_no_raw is not None and not isinstance(meeting_no_raw, str):
        try:
            meeting_no_int = int(meeting_no_raw)
        except (TypeError, ValueError):
            meeting_no_int = None

    meeting_date = parse_date(item.get("meeting_date"))

    normalized = {
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
    normalized["dedupe_hash"] = _build_segment_dedupe_hash(normalized)
    return normalized


def parse_importance_value(raw: Any, *, required: bool) -> int | None:
    if raw is None:
        if required:
            raise bad_request("importance must be one of 1, 2, 3.")
        return None

    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise bad_request("importance must be an integer (1, 2, 3).")

    if value not in (1, 2, 3):
        raise bad_request("importance must be one of 1, 2, 3.")

    return value


def parse_importance_query(raw: str | None) -> int | None:
    if raw is None:
        return None
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise bad_request("importance must be an integer.")
    if value not in (1, 2, 3):
        raise bad_request("importance must be one of 1, 2, 3.")
    return value


class SegmentsService:
    def __init__(self, *, repository: SegmentsRepositoryPort) -> None:
        self._repository = repository

    def normalize_segment(self, item: dict[str, Any]) -> dict[str, Any]:
        return _normalize_segment(item)

    def insert_segments(self, items: list[dict[str, Any]]) -> int:
        return self._repository.insert_segments(items)

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
        return self._repository.list_segments(
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

    def get_segment(self, item_id: int) -> dict[str, Any] | None:
        return self._repository.get_segment(item_id)

    def delete_segment(self, item_id: int) -> bool:
        return self._repository.delete_segment(item_id)


def build_segments_service(
    *,
    repository: SegmentsRepositoryPort | None = None,
    connection_provider: ConnectionProvider | None = None,
) -> SegmentsService:
    selected_repository = repository or SegmentsRepository(connection_provider=connection_provider)
    return SegmentsService(repository=selected_repository)


def normalize_segment(item: dict[str, Any]) -> dict[str, Any]:
    return _normalize_segment(item)


def insert_segments(
    items: list[dict[str, Any]],
    *,
    service: SegmentsService | None = None,
    connection_provider: ConnectionProvider | None = None,
) -> int:
    active_service = service or build_segments_service(connection_provider=connection_provider)
    return active_service.insert_segments(items)


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
    service: SegmentsService | None = None,
    connection_provider: ConnectionProvider | None = None,
) -> tuple[list[dict[str, Any]], int]:
    active_service = service or build_segments_service(connection_provider=connection_provider)
    return active_service.list_segments(
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


def get_segment(
    item_id: int,
    *,
    service: SegmentsService | None = None,
    connection_provider: ConnectionProvider | None = None,
) -> dict[str, Any] | None:
    active_service = service or build_segments_service(connection_provider=connection_provider)
    return active_service.get_segment(item_id)


def delete_segment(
    item_id: int,
    *,
    service: SegmentsService | None = None,
    connection_provider: ConnectionProvider | None = None,
) -> bool:
    active_service = service or build_segments_service(connection_provider=connection_provider)
    return active_service.delete_segment(item_id)
