from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from .common import utc_now


@dataclass(slots=True)
class ResearchEpisodeItem:
    episode_id: str
    source_type: str
    source_id: str

    item_id: str = field(default_factory=lambda: str(uuid4()))

    role: str | None = None
    occurred_at: datetime | None = None

    membership_method: str = "deterministic"
    membership_reason: str | None = None
    membership_score: float | None = None

    schema_version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=utc_now)
