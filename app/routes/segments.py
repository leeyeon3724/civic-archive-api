from datetime import date
from typing import Any

from fastapi import APIRouter, Body, Query

from app.errors import http_error
from app.repositories.segments_repository import (
    delete_segment as delete_segment_item,
    get_segment as get_segment_item,
    insert_segments,
    list_segments as list_segments_items,
)
from app.schemas import (
    DeleteResponse,
    ErrorResponse,
    InsertResponse,
    SegmentsInsertPayload,
    SegmentsItemDetail,
    SegmentsListResponse,
)
from app.services.segments_service import normalize_segment

ERROR_RESPONSES = {
    400: {"model": ErrorResponse},
    401: {"model": ErrorResponse},
    404: {"model": ErrorResponse},
    422: {"model": ErrorResponse},
    429: {"model": ErrorResponse},
    500: {"model": ErrorResponse},
}

router = APIRouter(tags=["segments"])


@router.post(
    "/api/segments",
    summary="Insert speech segments",
    response_model=InsertResponse,
    status_code=201,
    responses=ERROR_RESPONSES,
)
def save_segments(
    payload: SegmentsInsertPayload = Body(
        ...,
        examples=[
            {
                "council": "seoul",
                "committee": "budget",
                "session": "301",
                "meeting_no": "301 4차",
                "meeting_date": "2026-02-17",
                "content": "segment text",
                "importance": 2,
            }
        ],
    )
):
    payload_items = payload if isinstance(payload, list) else [payload]
    items: list[dict[str, Any]] = [normalize_segment(item.model_dump()) for item in payload_items]
    inserted = insert_segments(items)
    return InsertResponse(inserted=inserted)


@router.get(
    "/api/segments",
    summary="List speech segments",
    response_model=SegmentsListResponse,
    responses=ERROR_RESPONSES,
)
def list_segments(
    q: str | None = Query(default=None),
    council: str | None = Query(default=None),
    committee: str | None = Query(default=None),
    session: str | None = Query(default=None),
    meeting_no: str | None = Query(default=None),
    importance: int | None = Query(default=None, ge=1, le=3),
    party: str | None = Query(default=None),
    constituency: str | None = Query(default=None),
    department: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=200),
    date_from: date | None = Query(default=None, alias="from"),
    date_to: date | None = Query(default=None, alias="to"),
):
    rows, total = list_segments_items(
        q=q,
        council=council,
        committee=committee,
        session=session,
        meeting_no=meeting_no,
        importance=importance,
        party=party,
        constituency=constituency,
        department=department,
        date_from=date_from.isoformat() if date_from else None,
        date_to=date_to.isoformat() if date_to else None,
        page=page,
        size=size,
    )

    return SegmentsListResponse(page=page, size=size, total=total, items=rows)


@router.get(
    "/api/segments/{item_id}",
    summary="Get speech segment detail",
    response_model=SegmentsItemDetail,
    responses=ERROR_RESPONSES,
)
def get_segment(item_id: int):
    row = get_segment_item(item_id)
    if not row:
        raise http_error(404, "NOT_FOUND", "Not Found")
    return SegmentsItemDetail(**row)


@router.delete(
    "/api/segments/{item_id}",
    summary="Delete speech segment",
    response_model=DeleteResponse,
    responses=ERROR_RESPONSES,
)
def delete_segment(item_id: int):
    deleted = delete_segment_item(item_id)
    if not deleted:
        raise http_error(404, "NOT_FOUND", "Not Found")
    return DeleteResponse(status="deleted", id=item_id)
