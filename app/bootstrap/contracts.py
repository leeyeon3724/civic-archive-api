from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeAlias

ProtectedDependencies: TypeAlias = list[Any]
RateLimitHealthCheck: TypeAlias = Callable[[], tuple[bool, str | None]]
