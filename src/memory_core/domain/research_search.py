from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ResearchSearch:
    search_id: str
    project_id: str

    search_type: str
    original_query: str

    created_by: str | None = None
    trace_id: str | None = None

    executed_query: str | None = None
    query_source: str | None = None
    status: str | None = None

    result_count: int | None = None
    elapsed_ms: float | None = None

    payload: dict[str, Any] = field(default_factory=dict)

    created_at: datetime | None = None
    updated_at: datetime | None = None