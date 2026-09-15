from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ResearchPage:
    page_id: str
    project_id: str
    doc_id: str

    page_idx: int
    page_num: int | None = None

    page_text: str | None = None

    total_block_count: int | None = None
    searchable_block_count: int | None = None
    has_searchable_text: bool | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: datetime | None = None
    updated_at: datetime | None = None
