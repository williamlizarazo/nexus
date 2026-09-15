from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ResearchSearchResult:
    result_id: str
    project_id: str
    trace_id: str

    result_key: str | None = None
    doc_id: str | None = None
    chunk_id: str | None = None

    rank_position: int | None = None
    score: float | None = None

    page_idx_start: int | None = None
    page_idx_end: int | None = None
    page_num_start: int | None = None
    page_num_end: int | None = None

    role: str | None = None
    source_number: int | None = None
    version_number: int | None = None
    window_role: str | None = None

    payload: dict[str, Any] = field(default_factory=dict)

    created_at: datetime | None = None
    updated_at: datetime | None = None