from __future__ import annotations

from dataclasses import dataclass

from memory_core.contracts.episode_repository import (
    EpisodeRepository,
)
from memory_core.contracts.research_activity_source import (
    ResearchActivitySource,
)


@dataclass(frozen=True, slots=True)
class MemoryRuntime:
    """
    Capacidades de memoria disponibles para una aplicación.

    No conoce proveedores concretos ni infraestructura.
    """

    episode_repository: EpisodeRepository
    research_activity_source: ResearchActivitySource
