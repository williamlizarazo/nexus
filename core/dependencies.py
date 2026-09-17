from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from memory_core.bootstrap import (
    MemoryRuntimeConfigurationError,
    build_memory_runtime_from_env,
)

from core.config import AppConfig


@dataclass(slots=True)
class AppDependencies:
    """External capabilities available to appmemoria."""

    episode_repository: Any | None = None
    research_activity_source: Any | None = None
    research_project_source: Any | None = None
    organization_directory_repository: Any | None = None
    vector_store: Any | None = None
    llm_provider: Any | None = None
    embedding_provider: Any | None = None
    memory_runtime_error: str | None = None


def build_dependencies(
    config: AppConfig,
) -> AppDependencies:
    """Build dependencies available to appmemoria."""

    _ = config

    try:
        runtime = build_memory_runtime_from_env()

    except MemoryRuntimeConfigurationError as exc:
        return AppDependencies(
            memory_runtime_error=str(exc),
        )

    return AppDependencies(
        episode_repository=runtime.episode_repository,
        research_activity_source=(
            runtime.research_activity_source
        ),
        research_project_source=getattr(
            runtime,
            "research_project_source",
            None,
        ),
        organization_directory_repository=getattr(
            runtime,
            "organization_directory_repository",
            None,
        ),
    )
