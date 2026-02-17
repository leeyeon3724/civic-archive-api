from __future__ import annotations

from typing import Any

from app.ports.repositories import MinutesRepositoryPort
from app.ports.services import MinutesServicePort
from app.repositories.minutes_repository import MinutesRepository
from app.repositories.session_provider import ConnectionProvider, ensure_connection_provider
from app.utils import bad_request, combine_meeting_no, parse_date


def _normalize_minutes(item: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise bad_request("Each item must be a JSON object.")

    council = item.get("council")
    url = item.get("url")
    if not council or not url:
        raise bad_request("Missing required fields: council, url")

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


class MinutesService:
    def __init__(self, *, repository: MinutesRepositoryPort) -> None:
        self._repository = repository

    def normalize_minutes(self, item: dict[str, Any]) -> dict[str, Any]:
        return _normalize_minutes(item)

    def upsert_minutes(self, items: list[dict[str, Any]]) -> tuple[int, int]:
        return self._repository.upsert_minutes(items)

    def list_minutes(
        self,
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
        return self._repository.list_minutes(
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

    def get_minutes(self, item_id: int) -> dict[str, Any] | None:
        return self._repository.get_minutes(item_id)

    def delete_minutes(self, item_id: int) -> bool:
        return self._repository.delete_minutes(item_id)


def build_minutes_service(
    *,
    connection_provider: ConnectionProvider,
    repository: MinutesRepositoryPort | None = None,
) -> MinutesServicePort:
    selected_repository = repository or MinutesRepository(connection_provider=connection_provider)
    return MinutesService(repository=selected_repository)


def normalize_minutes(item: dict[str, Any]) -> dict[str, Any]:
    return _normalize_minutes(item)


def upsert_minutes(
    items: list[dict[str, Any]],
    *,
    service: MinutesServicePort | None = None,
    connection_provider: ConnectionProvider | None = None,
) -> tuple[int, int]:
    active_service = service or build_minutes_service(connection_provider=ensure_connection_provider(connection_provider))
    return active_service.upsert_minutes(items)


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
    service: MinutesServicePort | None = None,
    connection_provider: ConnectionProvider | None = None,
) -> tuple[list[dict[str, Any]], int]:
    active_service = service or build_minutes_service(connection_provider=ensure_connection_provider(connection_provider))
    return active_service.list_minutes(
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


def get_minutes(
    item_id: int,
    *,
    service: MinutesServicePort | None = None,
    connection_provider: ConnectionProvider | None = None,
) -> dict[str, Any] | None:
    active_service = service or build_minutes_service(connection_provider=ensure_connection_provider(connection_provider))
    return active_service.get_minutes(item_id)


def delete_minutes(
    item_id: int,
    *,
    service: MinutesServicePort | None = None,
    connection_provider: ConnectionProvider | None = None,
) -> bool:
    active_service = service or build_minutes_service(connection_provider=ensure_connection_provider(connection_provider))
    return active_service.delete_minutes(item_id)
