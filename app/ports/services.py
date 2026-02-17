from __future__ import annotations

from typing import Any, Protocol


class NewsServicePort(Protocol):
    def normalize_article(self, item: dict[str, Any]) -> dict[str, Any]:
        ...

    def upsert_articles(self, items: list[dict[str, Any]]) -> tuple[int, int]:
        ...

    def list_articles(
        self,
        *,
        q: str | None,
        source: str | None,
        date_from: str | None,
        date_to: str | None,
        page: int,
        size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        ...

    def get_article(self, item_id: int) -> dict[str, Any] | None:
        ...

    def delete_article(self, item_id: int) -> bool:
        ...


class MinutesServicePort(Protocol):
    def normalize_minutes(self, item: dict[str, Any]) -> dict[str, Any]:
        ...

    def upsert_minutes(self, items: list[dict[str, Any]]) -> tuple[int, int]:
        ...

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
        ...

    def get_minutes(self, item_id: int) -> dict[str, Any] | None:
        ...

    def delete_minutes(self, item_id: int) -> bool:
        ...


class SegmentsServicePort(Protocol):
    def normalize_segment(self, item: dict[str, Any]) -> dict[str, Any]:
        ...

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
