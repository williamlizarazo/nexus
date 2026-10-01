from __future__ import annotations

from datetime import date

from core.dependencies import (
    AppDependencies,
)
from memory_core.services.nexus_analysis_service import (
    NexusAnalysisResult,
    NexusAnalysisService,
)
from memory_core.services.nexus_projector import (
    NexusProjector,
)


class NexusService:
    """
    Servicio de aplicación para el análisis NEXUS.

    Coordina la fuente canónica, la proyección estructural
    y la capa analítica de memory_core.
    """

    def __init__(
        self,
        dependencies: AppDependencies,
    ) -> None:
        self._dependencies = dependencies

    @property
    def source_available(
        self,
    ) -> bool:
        return (
            self._dependencies
            .nexus_backfill_source
            is not None
        )

    def build_analysis(
        self,
        *,
        reference_date: date,
    ) -> NexusAnalysisResult | None:

        source = (
            self._dependencies
            .nexus_backfill_source
        )

        if source is None:
            return None

        source_snapshot = (
            source.load_snapshot()
        )

        graph_snapshot = NexusProjector(
            reference_date=reference_date
        ).project(
            source_snapshot
        )

        return NexusAnalysisService(
            reference_date=reference_date
        ).analyze(
            source_snapshot=source_snapshot,
            graph_snapshot=graph_snapshot,
        )
