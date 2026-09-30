from __future__ import annotations

from typing import Protocol, runtime_checkable

from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
)
from memory_core.domain.nexus_incremental import (
    NexusAffectedScope,
)


@runtime_checkable
class NexusIncrementalSource(Protocol):

    def load_scope(
        self,
        *,
        scope: NexusAffectedScope,
    ) -> NexusBackfillSnapshot:
        ...
