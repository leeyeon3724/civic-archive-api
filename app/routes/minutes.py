from datetime import date
from typing import Any

from fastapi import APIRouter, Body, Query

from app.errors import http_error
from app.routes.common import ERROR_RESPONSES
from app.schemas import DeleteResponse, MinutesItemDetail, MinutesListResponse, MinutesUpsertPayload, UpsertResponse
from app.services.minutes_service import (
    delete_minutes as delete_minutes_item,
    get_minutes as get_minutes_item,
    list_minutes as list_minutes_items,
    normalize_minutes,
    upsert_minutes,
)

router = APIRouter(tags=["minutes"])


@router.post(
    "/api/minutes",
    summary="Upsert minutes items",
    response_model=UpsertResponse,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def save_minutes(
    payload: MinutesUpsertPayload = Body(
        ...,
        examples=[
            {
                "council": "seoul",
                "committee": "budget",
                "session": "301",
                "meeting_no": "301 4차",
                "url": "https://example.com/minutes/100",
                "meeting_date": "2026-02-17",
            }
        ],
    )
):
    payload_items = payload if isinstance(payload, list) else [payload]
    items: list[dict[str, Any]] = [normalize_minutes(item.model_dump()) for item in payload_items]
    inserted, updated = upsert_minutes(items)
    return UpsertResponse(inserted=inserted, updated=updated)


@router.get(
    "/api/minutes",
    summary="List minutes items",
    response_model=MinutesListResponse,
    responses=ERROR_RESPONSES,
)
def list_minutes(
    q: str | None = Query(default=None),
    council: str | None = Query(default=None),
    committee: str | None = Query(default=None),
    session: str | None = Query(default=None),
    meeting_no: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=200),
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
):
    rows, total = list_minutes_items(
        q=q,
        council=council,
        committee=committee,
        session=session,
        meeting_no=meeting_no,
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
        page=page,
        size=size,
    )

    return MinutesListResponse(page=page, size=size, total=total, items=rows)


@router.get(
    "/api/minutes/{item_id}",
    summary="Get minutes item detail",
    response_model=MinutesItemDetail,
    responses=ERROR_RESPONSES,
)
def get_minutes(item_id: int):
    row = get_minutes_item(item_id)
    if not row:
        raise http_error(404, "NOT_FOUND", "Not Found")
    return MinutesItemDetail(**row)


@router.delete(
    "/api/minutes/{item_id}",
    summary="Delete minutes item",
    response_model=DeleteResponse,
    responses=ERROR_RESPONSES,
)
def delete_minutes(item_id: int):
    deleted = delete_minutes_item(item_id)
    if not deleted:
        raise http_error(404, "NOT_FOUND", "Not Found")
    return DeleteResponse(status="deleted", id=item_id)
