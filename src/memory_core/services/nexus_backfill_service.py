from __future__ import annotations

from memory_core.contracts.nexus_backfill_source import (
    NexusBackfillSource,
)
from memory_core.contracts.nexus_graph_projection import (
    GraphProjectionRepository,
)
from memory_core.domain.nexus_graph import (
    NexusGraphSnapshot,
)
from memory_core.services.nexus_projector import (
    NexusProjector,
)


class NexusBackfillService:
    """
    Orquesta el backfill histórico de la proyección NEXUS.

    El servicio coordina fuente, proyector y repositorio sin conocer
    detalles de Supabase, PostgreSQL ni del esquema físico.
    """

    def __init__(
        self,
        *,
        source: NexusBackfillSource,
        projector: NexusProjector,
        repository: GraphProjectionRepository,
    ) -> None:
        self._source = source
        self._projector = projector
        self._repository = repository

    def run(
        self,
    ) -> NexusGraphSnapshot:
        """
        Ejecuta una proyección histórica completa.

        Los nodos se persisten antes que las aristas para respetar
        la integridad referencial de la proyección.
        """

        source_snapshot = (
            self._source.load_snapshot()
        )

        graph_snapshot = (
            self._projector.project(
                source_snapshot
            )
        )

        self._repository.upsert_nodes(
            graph_snapshot.nodes
        )

        self._repository.upsert_edges(
            graph_snapshot.edges
        )

        return graph_snapshot
