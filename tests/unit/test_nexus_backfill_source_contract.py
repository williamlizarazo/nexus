from memory_core.contracts.nexus_backfill_source import (
    NexusBackfillSource,
)
from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
)


class FakeNexusBackfillSource:

    def load_snapshot(
        self,
    ) -> NexusBackfillSnapshot:
        return NexusBackfillSnapshot()


def test_structural_source_implements_nexus_backfill_contract():
    source = FakeNexusBackfillSource()

    assert isinstance(
        source,
        NexusBackfillSource,
    )


def test_contract_exposes_load_snapshot():
    assert "load_snapshot" in dir(
        NexusBackfillSource
    )
