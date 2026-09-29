from __future__ import annotations

import pytest

from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
)
from memory_core.domain.nexus_graph import (
    GraphEdge,
    GraphNode,
    NexusGraphSnapshot,
)
from memory_core.services.nexus_backfill_service import (
    NexusBackfillService,
)


class FakeSource:

    def __init__(
        self,
        snapshot: NexusBackfillSnapshot,
        events: list[str],
    ) -> None:
        self._snapshot = snapshot
        self._events = events
        self.calls = 0

    def load_snapshot(
        self,
    ) -> NexusBackfillSnapshot:
        self.calls += 1
        self._events.append(
            "source.load_snapshot"
        )
        return self._snapshot


class FakeProjector:

    def __init__(
        self,
        graph: NexusGraphSnapshot,
        events: list[str],
    ) -> None:
        self._graph = graph
        self._events = events
        self.received_snapshot = None

    def project(
        self,
        snapshot: NexusBackfillSnapshot,
    ) -> NexusGraphSnapshot:
        self.received_snapshot = snapshot
        self._events.append(
            "projector.project"
        )
        return self._graph


class FakeRepository:

    def __init__(
        self,
        events: list[str],
        *,
        fail_nodes: bool = False,
    ) -> None:
        self._events = events
        self._fail_nodes = fail_nodes

        self.received_nodes = None
        self.received_edges = None

    def list_nodes(
        self,
        *,
        active_only: bool = True,
    ):
        return []

    def list_edges(
        self,
        *,
        active_only: bool = True,
    ):
        return []

    def upsert_nodes(
        self,
        nodes,
    ) -> None:
        self._events.append(
            "repository.upsert_nodes"
        )

        if self._fail_nodes:
            raise RuntimeError(
                "node write failed"
            )

        self.received_nodes = tuple(
            nodes
        )

    def upsert_edges(
        self,
        edges,
    ) -> None:
        self._events.append(
            "repository.upsert_edges"
        )

        self.received_edges = tuple(
            edges
        )


def _graph() -> NexusGraphSnapshot:
    return NexusGraphSnapshot(
        nodes=(
            GraphNode(
                node_key="user:user-1",
                node_type="user",
                entity_id="user-1",
                label="Usuario Uno",
            ),
            GraphNode(
                node_key="project:project-1",
                node_type="project",
                entity_id="project-1",
                label="Proyecto Uno",
            ),
        ),
        edges=(
            GraphEdge(
                source_key="user:user-1",
                relation_type="WORKS_ON",
                target_key="project:project-1",
                metadata={
                    "role": "owner",
                },
            ),
        ),
    )


def test_backfill_service_runs_complete_pipeline_in_order():
    events = []

    source_snapshot = (
        NexusBackfillSnapshot()
    )

    projected_graph = _graph()

    source = FakeSource(
        source_snapshot,
        events,
    )

    projector = FakeProjector(
        projected_graph,
        events,
    )

    repository = FakeRepository(
        events,
    )

    service = NexusBackfillService(
        source=source,
        projector=projector,
        repository=repository,
    )

    result = service.run()

    assert result == projected_graph

    assert source.calls == 1

    assert (
        projector.received_snapshot
        is source_snapshot
    )

    assert repository.received_nodes == (
        projected_graph.nodes
    )

    assert repository.received_edges == (
        projected_graph.edges
    )

    assert events == [
        "source.load_snapshot",
        "projector.project",
        "repository.upsert_nodes",
        "repository.upsert_edges",
    ]


def test_backfill_service_supports_empty_graph():
    events = []

    snapshot = NexusBackfillSnapshot()

    graph = NexusGraphSnapshot()

    repository = FakeRepository(
        events
    )

    service = NexusBackfillService(
        source=FakeSource(
            snapshot,
            events,
        ),
        projector=FakeProjector(
            graph,
            events,
        ),
        repository=repository,
    )

    result = service.run()

    assert result == graph
    assert repository.received_nodes == ()
    assert repository.received_edges == ()


def test_backfill_service_does_not_write_edges_when_node_write_fails():
    events = []

    service = NexusBackfillService(
        source=FakeSource(
            NexusBackfillSnapshot(),
            events,
        ),
        projector=FakeProjector(
            _graph(),
            events,
        ),
        repository=FakeRepository(
            events,
            fail_nodes=True,
        ),
    )

    with pytest.raises(
        RuntimeError,
        match="node write failed",
    ):
        service.run()

    assert events == [
        "source.load_snapshot",
        "projector.project",
        "repository.upsert_nodes",
    ]


def test_backfill_service_can_be_run_repeatedly():
    events = []

    snapshot = NexusBackfillSnapshot()
    graph = _graph()

    repository = FakeRepository(
        events
    )

    service = NexusBackfillService(
        source=FakeSource(
            snapshot,
            events,
        ),
        projector=FakeProjector(
            graph,
            events,
        ),
        repository=repository,
    )

    first = service.run()
    second = service.run()

    assert first == graph
    assert second == graph

    assert events.count(
        "repository.upsert_nodes"
    ) == 2

    assert events.count(
        "repository.upsert_edges"
    ) == 2
