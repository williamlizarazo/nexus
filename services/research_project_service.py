from __future__ import annotations

from memory_core.domain.research_project import (
    ResearchProject,
)

from core.dependencies import (
    AppDependencies,
)


class ResearchProjectService:
    """
    Servicio de aplicación para resolver:
    usuario -> proyectos.
    """

    def __init__(
        self,
        dependencies: AppDependencies,
    ) -> None:
        self._dependencies = (
            dependencies
        )

    @property
    def available(self) -> bool:
        return (
            self._dependencies
            .research_project_source
            is not None
        )

    def list_projects_for_user(
        self,
        user_id: str,
        *,
        limit: int = 500,
    ) -> list[ResearchProject]:
        source = (
            self._dependencies
            .research_project_source
        )

        if source is None:
            return []

        normalized_user_id = str(
            user_id or ""
        ).strip()

        if not normalized_user_id:
            return []

        return source.list_projects(
            owner_user_id=(
                normalized_user_id
            ),
            limit=limit,
        )
