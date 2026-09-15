from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

from .common import utc_now


@dataclass(slots=True)
class ResearchEpisodeAnalysis:
    episode_id: str
    version: int

    analysis_id: str = field(default_factory=lambda: str(uuid4()))

    summary: str | None = None

    entities: list[dict[str, Any]] = field(default_factory=list)
    relations: list[dict[str, Any]] = field(default_factory=list)
    topics: list[dict[str, Any]] = field(default_factory=list)

    open_questions: list[dict[str, Any]] = field(default_factory=list)
    contradictions: list[dict[str, Any]] = field(default_factory=list)

    structure: dict[str, Any] = field(default_factory=dict)

    source_fingerprint: str | None = None

    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None

    schema_version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    created_at: datetime = field(default_factory=utc_now)
