from __future__ import annotations

from fastapi import Request

from app.ports.services import MinutesServicePort, NewsServicePort, SegmentsServicePort
from app.repositories.session_provider import ConnectionProvider, get_connection_provider
from app.services.minutes_service import build_minutes_service
from app.services.news_service import build_news_service
from app.services.segments_service import build_segments_service


def get_request_connection_provider(request: Request) -> ConnectionProvider:
    state_provider = getattr(request.app.state, "connection_provider", None)
    if callable(state_provider):
        return state_provider
    return get_connection_provider()


def get_news_service(request: Request) -> NewsServicePort:
    return build_news_service(connection_provider=get_request_connection_provider(request))


def get_minutes_service(request: Request) -> MinutesServicePort:
    return build_minutes_service(connection_provider=get_request_connection_provider(request))


def get_segments_service(request: Request) -> SegmentsServicePort:
    return build_segments_service(connection_provider=get_request_connection_provider(request))
