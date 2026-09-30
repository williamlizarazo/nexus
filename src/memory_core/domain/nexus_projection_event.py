from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class NexusProjectionEvent:
    event_id: str

    event_type: str
    source_table: str
    source_operation: str
    source_record_key: str

    project_id: str | None
    user_id: str | None
    unit_id: str | None
    doc_id: str | None
    page_idx: int | None

    old_values: dict[str, Any] | None
    new_values: dict[str, Any] | None

    status: str
    priority: int

    attempts: int
    max_attempts: int

    available_at: datetime

    claimed_by: str | None
    claimed_at: datetime | None
    lease_until: datetime | None

    processed_at: datetime | None
    last_error: str | None

    created_at: datetime
    updated_at: datetime
