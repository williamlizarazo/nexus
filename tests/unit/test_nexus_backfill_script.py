from __future__ import annotations

from datetime import date

import pytest

from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
    NexusSourceProject,
    NexusSourceProjectMembership,
    NexusSourceUser,
)
from memory_core.scripts.backfill_nexus import (
    execute_backfill,
    parse_reference_date,
)
from memory_core.services.nexus_projector import (
    NexusProjector,
)


class FakeSource:

    def __init__(
        self,
        snapshot: NexusBackfillSnapshot,
    ) -> None:
        self.snapshot = snapshot
        self.calls = 0

    def load_snapshot(
        self,
    ) -> NexusBackfillSnapshot:
        self.calls += 1
        return self.snapshot


class FakeRepository:

    def __init__(self) -> None:
        self.nodes = ()
        self.edges = ()
        self.events = []

    def upsert_nodes(
        self,
        nodes,
    ) -> None:
        self.events.append(
            "upsert_nodes"
        )
        self.nodes = tuple(nodes)

    def upsert_edges(
        self,
        edges,
    ) -> None:
        self.events.append(
            "upsert_edges"
        )
        self.edges = tuple(edges)

    def list_nodes(
        self,
        *,
        active_only: bool = True,
    ):
        if not active_only:
            return list(self.nodes)

        return [
            node
            for node in self.nodes
            if node.active
        ]

    def list_edges(
        self,
        *,
        active_only: bool = True,
    ):
        if not active_only:
            return list(self.edges)

        return [
            edge
            for edge in self.edges
            if edge.active
        ]


def _snapshot() -> NexusBackfillSnapshot:
    return NexusBackfillSnapshot(
        users=(
            NexusSourceUser(
                user_id="user-1",
                email="uno@jep.gov.co",
            ),
        ),
        projects=(
            NexusSourceProject(
                project_id="project-1",
                owner_user_id="user-1",
                name="Proyecto Uno",
            ),
        ),
        project_memberships=(
            NexusSourceProjectMembership(
                project_id="project-1",
                user_id="user-1",
                role="owner",
            ),
        ),
    )


def test_parse_reference_date():
    result = parse_reference_date(
        "2026-09-29"
    )

    assert result == date(
        2026,
        9,
        29,
    )


def test_parse_reference_date_rejects_invalid_value():
    with pytest.raises(
        ValueError,
        match="reference date",
    ):
        parse_reference_date(
            "29-09-2026"
        )


def test_dry_run_projects_without_writing():
    source = FakeSource(
        _snapshot()
    )

    repository = FakeRepository()

    report = execute_backfill(
        source=source,
        projector=NexusProjector(
            reference_date=date(
                2026,
                9,
                29,
            )
        ),
        repository=repository,
        reference_date=date(
            2026,
            9,
            29,
        ),
        write=False,
    )

    assert source.calls == 1

    assert repository.events == []

    assert report.written is False

    assert report.source_users == 1
    assert report.source_projects == 1

    assert report.projected_nodes == 2
    assert report.projected_edges == 1

    assert report.node_types == (
        ("project", 1),
        ("user", 1),
    )

    assert report.relation_types == (
        ("WORKS_ON", 1),
    )

    assert report.persisted_nodes is None
    assert report.persisted_edges is None


def test_write_run_persists_nodes_before_edges():
    source = FakeSource(
        _snapshot()
    )

    repository = FakeRepository()

    report = execute_backfill(
        source=source,
        projector=NexusProjector(
            reference_date=date(
                2026,
                9,
                29,
            )
        ),
        repository=repository,
        reference_date=date(
            2026,
            9,
            29,
        ),
        write=True,
    )

    assert source.calls == 1

    assert repository.events == [
        "upsert_nodes",
        "upsert_edges",
    ]

    assert report.written is True

    assert report.projected_nodes == 2
    assert report.projected_edges == 1

    assert report.persisted_nodes == 2
    assert report.persisted_edges == 1


def test_write_run_is_repeatable_with_upsert_repository():
    source = FakeSource(
        _snapshot()
    )

    repository = FakeRepository()

    projector = NexusProjector(
        reference_date=date(
            2026,
            9,
            29,
        )
    )

    first = execute_backfill(
        source=source,
        projector=projector,
        repository=repository,
        reference_date=date(
            2026,
            9,
            29,
        ),
        write=True,
    )

    second = execute_backfill(
        source=source,
        projector=projector,
        repository=repository,
        reference_date=date(
            2026,
            9,
            29,
        ),
        write=True,
    )

    assert first.persisted_nodes == 2
    assert second.persisted_nodes == 2

    assert first.persisted_edges == 1
    assert second.persisted_edges == 1


def test_write_requires_repository():
    with pytest.raises(
        ValueError,
        match="repository",
    ):
        execute_backfill(
            source=FakeSource(
                _snapshot()
            ),
            projector=NexusProjector(
                reference_date=date(
                    2026,
                    9,
                    29,
                )
            ),
            repository=None,
            reference_date=date(
                2026,
                9,
                29,
            ),
            write=True,
        )


def test_admin_key_accepts_supabase_key(monkeypatch):
    from memory_core.scripts import (
        backfill_nexus as backfill_script,
    )

    for variable_name in (
        "NEXUS_SUPABASE_ADMIN_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_SECRET_KEY",
        "SUPABASE_KEY",
    ):
        monkeypatch.delenv(
            variable_name,
            raising=False,
        )

    monkeypatch.setenv(
        "SUPABASE_KEY",
        "sb_secret_test_key",
    )

    assert (
        backfill_script._read_admin_key()
        == "sb_secret_test_key"
    )


def test_admin_key_rejects_publishable_key(monkeypatch):
    from memory_core.scripts import (
        backfill_nexus as backfill_script,
    )

    for variable_name in (
        "NEXUS_SUPABASE_ADMIN_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_SECRET_KEY",
        "SUPABASE_KEY",
    ):
        monkeypatch.delenv(
            variable_name,
            raising=False,
        )

    monkeypatch.setenv(
        "NEXUS_SUPABASE_ADMIN_KEY",
        "sb_publishable_test_key",
    )

    with pytest.raises(
        RuntimeError,
        match="publishable",
    ):
        backfill_script._read_admin_key()
