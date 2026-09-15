from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from .common import utc_now


@dataclass(slots=True)
class ResearchEpisodeEdge:
    episode_id: str
    source_item_id: str
    target_item_id: str
    relation_type: str

    edge_id: str = field(default_factory=lambda: str(uuid4()))

    relation_score: float | None = None

    rule_version: str = "episodic_v1"
    schema_version: int = 1

    evidence: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=utc_now)
