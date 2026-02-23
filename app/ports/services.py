from __future__ import annotations

from typing import Protocol

from app.ports.dto import (
    MinutesListQuery,
    MinutesRecordDTO,
    MinutesUpsertDTO,
    NewsArticleRecordDTO,
    NewsArticleUpsertDTO,
    NewsListQuery,
    SegmentRecordDTO,
    SegmentsListQuery,
    SegmentUpsertDTO,
)


class NewsServicePort(Protocol):
    def normalize_article(self, item: dict[str, object]) -> NewsArticleUpsertDTO:
        ...

    def upsert_articles(self, items: list[NewsArticleUpsertDTO]) -> tuple[int, int]:
        ...

    def list_articles(self, query: NewsListQuery) -> tuple[list[NewsArticleRecordDTO], int]:
        ...

    def get_article(self, item_id: int) -> NewsArticleRecordDTO | None:
        ...

    def delete_article(self, item_id: int) -> bool:
        ...


class MinutesServicePort(Protocol):
    def normalize_minutes(self, item: dict[str, object]) -> MinutesUpsertDTO:
        ...

    def upsert_minutes(self, items: list[MinutesUpsertDTO]) -> tuple[int, int]:
        ...

    def list_minutes(self, query: MinutesListQuery) -> tuple[list[MinutesRecordDTO], int]:
        ...

    def get_minutes(self, item_id: int) -> MinutesRecordDTO | None:
        ...

    def delete_minutes(self, item_id: int) -> bool:
        ...


class SegmentsServicePort(Protocol):
    def normalize_segment(self, item: dict[str, object]) -> SegmentUpsertDTO:
        ...

    def insert_segments(self, items: list[SegmentUpsertDTO]) -> int:
        ...

    def list_segments(self, query: SegmentsListQuery) -> tuple[list[SegmentRecordDTO], int]:
        ...

    def get_segment(self, item_id: int) -> SegmentRecordDTO | None:
        ...

    def delete_segment(self, item_id: int) -> bool:
        ...
