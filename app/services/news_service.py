from __future__ import annotations

from typing import Any

from app.repositories.news_repository import (
    delete_article as repository_delete_article,
    get_article as repository_get_article,
    list_articles as repository_list_articles,
    upsert_articles as repository_upsert_articles,
)
from app.utils import bad_request, parse_datetime


def normalize_article(item: dict[str, Any]) -> dict[str, Any]:
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


def upsert_articles(items: list[dict[str, Any]]) -> tuple[int, int]:
    return repository_upsert_articles(items)


def list_articles(
    *,
    q: str | None,
    source: str | None,
    date_from: str | None,
    date_to: str | None,
    page: int,
    size: int,
) -> tuple[list[dict[str, Any]], int]:
    return repository_list_articles(
        q=q,
        source=source,
        date_from=date_from,
        date_to=date_to,
        page=page,
        size=size,
    )


def get_article(item_id: int) -> dict[str, Any] | None:
    return repository_get_article(item_id)


def delete_article(item_id: int) -> bool:
    return repository_delete_article(item_id)
