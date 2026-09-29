from __future__ import annotations

from typing import Protocol, runtime_checkable

from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
)


@runtime_checkable
class NexusBackfillSource(Protocol):
    """
    Puerto agnóstico para obtener los hechos fuente
    necesarios para construir la proyección NEXUS.
    """

    def load_snapshot(
        self,
    ) -> NexusBackfillSnapshot:
        ...
