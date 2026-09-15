from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ResearchChunk:
    chunk_row_id: str
    project_id: str
    chunk_id: str
    doc_id: str

    chunk_text: str | None = None

    page_idx_start: int | None = None
    page_idx_end: int | None = None
    page_num_start: int | None = None
    page_num_end: int | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: datetime | None = None
    updated_at: datetime | None = None
