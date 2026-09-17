from __future__ import annotations

from typing import Protocol

from memory_core.domain.research_project import (
    ResearchProject,
)


class ResearchProjectSource(Protocol):
    """
    Fuente de proyectos de investigación.

    Permite resolver el puente:
    usuario -> proyectos.
    """

    def get_project(
        self,
        project_id: str,
    ) -> ResearchProject | None:
        ...

    def list_projects(
        self,
        owner_user_id: str | None = None,
        limit: int = 500,
    ) -> list[ResearchProject]:
        ...
