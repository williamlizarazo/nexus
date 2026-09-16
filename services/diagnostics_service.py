from __future__ import annotations

from dataclasses import dataclass

from core.dependencies import AppDependencies


@dataclass(frozen=True, slots=True)
class DependencyStatus:
    episode_repository: bool
    research_activity_source: bool
    vector_store: bool
    llm_provider: bool
    embedding_provider: bool


class DiagnosticsService:
    def __init__(self, dependencies: AppDependencies) -> None:
        self._dependencies = dependencies

    def get_dependency_status(self) -> DependencyStatus:
        return DependencyStatus(
            episode_repository=self._dependencies.episode_repository is not None,
            research_activity_source=(
                self._dependencies.research_activity_source is not None
            ),
            vector_store=self._dependencies.vector_store is not None,
            llm_provider=self._dependencies.llm_provider is not None,
            embedding_provider=self._dependencies.embedding_provider is not None,
        )
