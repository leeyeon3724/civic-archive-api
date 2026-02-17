from __future__ import annotations

from typing import Any, Dict

from app.utils import bad_request, parse_datetime


def normalize_article(item: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(item, dict):
        raise bad_request("각 아이템은 JSON 객체여야 합니다.")

    title = item.get("title")
    url = item.get("url")
    if not title or not url:
        raise bad_request("필수 필드 누락: title, url")

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
