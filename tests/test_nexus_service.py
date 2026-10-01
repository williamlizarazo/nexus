from datetime import date

from core.dependencies import AppDependencies
from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
    NexusSourceProject,
    NexusSourceProjectMembership,
    NexusSourceUser,
)
from services.nexus_service import (
    NexusService,
)


REFERENCE_DATE = date(2026, 10, 1)


class FakeNexusSource:
    def __init__(
        self,
        snapshot: NexusBackfillSnapshot,
    ):
        self.snapshot = snapshot
        self.calls = 0

    def load_snapshot(
        self,
    ) -> NexusBackfillSnapshot:
        self.calls += 1
        return self.snapshot


def _source_snapshot():
    return NexusBackfillSnapshot(
        users=(
            NexusSourceUser(
                user_id="user-1",
                email=None,
                full_name="Usuario 1",
                functional_role=None,
                status="active",
            ),
        ),
        units=(),
        user_unit_memberships=(),
        projects=(
            NexusSourceProject(
                project_id="project-1",
                owner_user_id="user-1",
                name="Proyecto 1",
                description=None,
                status="active",
                deleted_at=None,
            ),
        ),
        project_memberships=(
            NexusSourceProjectMembership(
                project_id="project-1",
                user_id="user-1",
                role="owner",
            ),
        ),
        annotated_pages=(),
    )


def test_nexus_service_reports_source_availability():
    unavailable = NexusService(
        AppDependencies()
    )

    assert unavailable.source_available is False

    source = FakeNexusSource(
        _source_snapshot()
    )

    available = NexusService(
        AppDependencies(
            nexus_backfill_source=source
        )
    )

    assert available.source_available is True


def test_nexus_service_returns_none_without_source():
    service = NexusService(
        AppDependencies()
    )

    assert (
        service.build_analysis(
            reference_date=REFERENCE_DATE,
        )
        is None
    )


def test_nexus_service_builds_real_analysis():
    source = FakeNexusSource(
        _source_snapshot()
    )

    service = NexusService(
        AppDependencies(
            nexus_backfill_source=source
        )
    )

    result = service.build_analysis(
        reference_date=REFERENCE_DATE,
    )

    assert result is not None
    assert source.calls == 1

    assert (
        result.structural_metrics.node_count
        == 2
    )
    assert (
        result.structural_metrics.edge_count
        == 1
    )

    assert (
        result.user_metrics.node_count
        == 1
    )
    assert (
        result.project_metrics.node_count
        == 1
    )
    assert (
        result.unit_metrics.node_count
        == 0
    )
