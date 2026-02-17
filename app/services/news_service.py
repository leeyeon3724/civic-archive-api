from __future__ import annotations

from typing import Any

from app.ports.repositories import NewsRepositoryPort
from app.ports.services import NewsServicePort
from app.repositories.news_repository import NewsRepository
from app.repositories.session_provider import ConnectionProvider, ensure_connection_provider
from app.utils import bad_request, parse_datetime


def _normalize_article(item: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise bad_request("Each item must be a JSON object.")

    title = item.get("title")
    url = item.get("url")
    if not title or not url:
        raise bad_request("Missing required fields: title, url")

    return {
        "source": item.get("source"),
        "title": title,
        "url": url,
        "published_at": parse_datetime(item.get("published_at")),
        "author": item.get("author"),
        "summary": item.get("summary"),
        "content": item.get("content"),
        "keywords": item.get("keywords"),
    }


class NewsService(NewsServicePort):
    def __init__(self, *, repository: NewsRepositoryPort) -> None:
        self._repository = repository

    def normalize_article(self, item: dict[str, Any]) -> dict[str, Any]:
        return _normalize_article(item)

    def upsert_articles(self, items: list[dict[str, Any]]) -> tuple[int, int]:
        return self._repository.upsert_articles(items)

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
        return self._repository.list_articles(
            q=q,
            source=source,
            date_from=date_from,
            date_to=date_to,
            page=page,
            size=size,
        )

    def get_article(self, item_id: int) -> dict[str, Any] | None:
        return self._repository.get_article(item_id)

    def delete_article(self, item_id: int) -> bool:
        return self._repository.delete_article(item_id)


def build_news_service(
    *,
    connection_provider: ConnectionProvider,
    repository: NewsRepositoryPort | None = None,
) -> NewsServicePort:
    selected_repository = repository or NewsRepository(connection_provider=connection_provider)
    return NewsService(repository=selected_repository)


def normalize_article(item: dict[str, Any]) -> dict[str, Any]:
    return _normalize_article(item)


def upsert_articles(
    items: list[dict[str, Any]],
    *,
    service: NewsServicePort | None = None,
    connection_provider: ConnectionProvider | None = None,
) -> tuple[int, int]:
    active_service = service or build_news_service(connection_provider=ensure_connection_provider(connection_provider))
    return active_service.upsert_articles(items)


def list_articles(
    *,
    q: str | None,
    source: str | None,
    date_from: str | None,
    date_to: str | None,
    page: int,
    size: int,
    service: NewsServicePort | None = None,
    connection_provider: ConnectionProvider | None = None,
) -> tuple[list[dict[str, Any]], int]:
    active_service = service or build_news_service(connection_provider=ensure_connection_provider(connection_provider))
    return active_service.list_articles(
        q=q,
        source=source,
        date_from=date_from,
        date_to=date_to,
        page=page,
        size=size,
    )


def get_article(
    item_id: int,
    *,
    service: NewsServicePort | None = None,
    connection_provider: ConnectionProvider | None = None,
) -> dict[str, Any] | None:
    active_service = service or build_news_service(connection_provider=ensure_connection_provider(connection_provider))
    return active_service.get_article(item_id)


def delete_article(
    item_id: int,
    *,
    service: NewsServicePort | None = None,
    connection_provider: ConnectionProvider | None = None,
) -> bool:
    active_service = service or build_news_service(connection_provider=ensure_connection_provider(connection_provider))
    return active_service.delete_article(item_id)
