from datetime import date
from typing import Any

from fastapi import APIRouter, Body, Query

from app.errors import http_error
from app.routes.common import ERROR_RESPONSES
from app.schemas import (
    DeleteResponse,
    NewsItemDetail,
    NewsListResponse,
    NewsUpsertPayload,
    UpsertResponse,
)
from app.repositories.news_repository import delete_article, get_article, list_articles, upsert_articles
from app.services.news_service import normalize_article

router = APIRouter(tags=["news"])


@router.post(
    "/api/news",
    summary="Upsert news items",
    response_model=UpsertResponse,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def save_news(
    payload: NewsUpsertPayload = Body(
        ...,
        examples=[
            {
                "source": "local-news",
                "title": "City budget hearing update",
                "url": "https://example.com/news/100",
                "published_at": "2026-02-17T09:30:00Z",
            },
            [
                {
                    "source": "local-news",
                    "title": "City budget hearing update",
                    "url": "https://example.com/news/100",
                },
                {
                    "source": "daily",
                    "title": "Council vote summary",
                    "url": "https://example.com/news/101",
                },
            ],
        ],
    )
):
    payload_items = payload if isinstance(payload, list) else [payload]
    items: list[dict[str, Any]] = [normalize_article(item.model_dump()) for item in payload_items]
    inserted, updated = upsert_articles(items)
    return UpsertResponse(inserted=inserted, updated=updated)


@router.get(
    "/api/news",
    summary="List news items",
    response_model=NewsListResponse,
    responses=ERROR_RESPONSES,
)
def list_news(
    q: str | None = Query(default=None, description="title/summary/content partial text"),
    source: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=200),
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
):
    rows, total = list_articles(
        q=q,
        source=source,
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
        page=page,
        size=size,
    )

    return NewsListResponse(page=page, size=size, total=total, items=rows)


@router.get(
    "/api/news/{item_id}",
    summary="Get news item detail",
    response_model=NewsItemDetail,
    responses=ERROR_RESPONSES,
)
def get_news(item_id: int):
    row = get_article(item_id)
    if not row:
        raise http_error(404, "NOT_FOUND", "Not Found")
    return NewsItemDetail(**row)


@router.delete(
    "/api/news/{item_id}",
    summary="Delete news item",
    response_model=DeleteResponse,
    responses=ERROR_RESPONSES,
)
def delete_news(item_id: int):
    deleted = delete_article(item_id)
    if not deleted:
        raise http_error(404, "NOT_FOUND", "Not Found")
    return DeleteResponse(status="deleted", id=item_id)
