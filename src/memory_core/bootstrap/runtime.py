from __future__ import annotations

from dataclasses import dataclass

from memory_core.contracts.episode_repository import (
    EpisodeRepository,
)
from memory_core.contracts.research_activity_source import (
    ResearchActivitySource,
)
from memory_core.contracts.research_project_source import (
    ResearchProjectSource,
)
from memory_core.organization import (
    OrganizationDirectoryRepository,
)


@dataclass(frozen=True, slots=True)
class MemoryRuntime:
    """
    Capacidades de memoria disponibles para una aplicacion.

    No conoce proveedores concretos ni infraestructura.
    """

    episode_repository: EpisodeRepository
    research_activity_source: ResearchActivitySource
    organization_directory_repository: OrganizationDirectoryRepository | None = None
    research_project_source: ResearchProjectSource | None = None
