from __future__ import annotations

from typing import Any

from fastapi import FastAPI

from app.routes import register_routes


def register_domain_routes(api: FastAPI, *, protected_dependencies: list[Any]) -> None:
    register_routes(api, dependencies=protected_dependencies)

