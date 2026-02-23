from __future__ import annotations

from datetime import date, datetime
from typing import TypedDict


class NewsArticleUpsertDTO(TypedDict):
    source: str | None
    title: str
    url: str
    published_at: datetime | None
    author: str | None
    summary: str | None
    content: str | None
    keywords: object | None


class NewsArticleRecordDTO(TypedDict, total=False):
    id: int
    source: str | None
    title: str
    url: str
    published_at: datetime | None
    author: str | None
    summary: str | None
    content: str | None
    keywords: object | None
    created_at: datetime
    updated_at: datetime


class MinutesUpsertDTO(TypedDict):
    council: str
    committee: str | None
    session: str | None
    meeting_no: int | None
    meeting_no_combined: str | None
    url: str
    meeting_date: date | None
    content: str | None
    tag: object | None
    attendee: object | None
    agenda: object | None


class MinutesRecordDTO(TypedDict, total=False):
    id: int
    council: str
    committee: str | None
    session: str | None
    meeting_no: str | None
    url: str
    meeting_date: date | None
    content: str | None
    tag: object | None
    attendee: object | None
    agenda: object | None
    created_at: datetime
    updated_at: datetime


class SegmentUpsertDTO(TypedDict):
    council: str
    committee: str | None
    session: str | None
    meeting_no: int | None
    meeting_no_combined: str | None
    meeting_date: date | None
    content: str | None
    summary: str | None
    subject: str | None
    tag: object | None
    importance: int | None
    moderator: object | None
    questioner: object | None
    answerer: object | None
    party: str | None
    constituency: str | None
    department: str | None
    dedupe_hash: str
    dedupe_hash_legacy: str | None


class SegmentRecordDTO(TypedDict, total=False):
    id: int
    council: str
    committee: str | None
    session: str | None
    meeting_no: str | None
    meeting_date: date | None
    content: str | None
    summary: str | None
    subject: str | None
    tag: object | None
    importance: int | None
    moderator: object | None
    questioner: object | None
    answerer: object | None
    party: str | None
    constituency: str | None
    department: str | None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# List query objects — eliminate per-layer parameter fan-out (P11-3)
# ---------------------------------------------------------------------------

class _PaginationQuery(TypedDict):
    """Required pagination fields shared by all list query types."""

    page: int
    size: int


class NewsListQuery(_PaginationQuery, total=False):
    q: str | None
    source: str | None
    date_from: str | None
    date_to: str | None


class MinutesListQuery(_PaginationQuery, total=False):
    q: str | None
    council: str | None
    committee: str | None
    session: str | None
    meeting_no: str | None
    date_from: str | None
    date_to: str | None


class SegmentsListQuery(_PaginationQuery, total=False):
    q: str | None
    council: str | None
    committee: str | None
    session: str | None
    meeting_no: str | None
    importance: int | None
    party: str | None
    constituency: str | None
    department: str | None
    date_from: str | None
    date_to: str | None
