from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ResearchDocument:
    document_row_id: str
    project_id: str
    doc_id: str

    source_blob: str | None = None
    display_name: str | None = None

    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: datetime | None = None
    updated_at: datetime | None = None
