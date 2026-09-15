from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class ResearchActivity:
    id: str
    project_id: str
    activity_id: str
    activity_type: str

    created_by: str | None = None
    description: str | None = None

    trace_id: str | None = None
    document_id: str | None = None
    page_key: str | None = None

    payload: dict[str, Any] = field(default_factory=dict)

    created_at: datetime | None = None