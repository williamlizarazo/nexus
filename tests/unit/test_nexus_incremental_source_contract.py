from memory_core.contracts.nexus_incremental_source import (
    NexusIncrementalSource,
)
from memory_core.domain.nexus_backfill import NexusBackfillSnapshot
from memory_core.domain.nexus_incremental import NexusAffectedScope


class FakeIncrementalSource:
    def load_scope(
        self,
        *,
        scope: NexusAffectedScope,
    ) -> NexusBackfillSnapshot:
        return NexusBackfillSnapshot(
            users=(),
            units=(),
            user_unit_memberships=(),
            projects=(),
            project_memberships=(),
            annotated_pages=(),
        )


def test_incremental_source_contract_is_runtime_checkable():
    source = FakeIncrementalSource()

    assert isinstance(
        source,
        NexusIncrementalSource,
    )


def test_incremental_source_returns_existing_backfill_snapshot():
    source = FakeIncrementalSource()

    snapshot = source.load_scope(
        scope=NexusAffectedScope(
            project_ids=("project-1",),
        )
    )

    assert isinstance(
        snapshot,
        NexusBackfillSnapshot,
    )
    assert snapshot.projects == ()
