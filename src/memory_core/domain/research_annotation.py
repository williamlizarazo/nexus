from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ResearchAnnotation:
    annotation_id: str
    project_id: str

    annotation_type: str

    created_by: str | None = None
    trace_id: str | None = None

    body: str | None = None
    selected_text: str | None = None

    doc_id: str | None = None
    page_idx: int | None = None
    page_num: int | None = None
    chunk_id: str | None = None

    tags: list[str] = field(default_factory=list)
    status: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None