from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from .common import utc_now


@dataclass(slots=True)
class ResearchEpisode:
    scope_type: str
    scope_id: str

    episode_id: str = field(default_factory=lambda: str(uuid4()))
    actor_id: str | None = None

    started_at: datetime = field(default_factory=utc_now)
    ended_at: datetime | None = None

    status: str = "open"

    grouping_version: str = "episodic_v1"
    schema_version: int = 1

    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
