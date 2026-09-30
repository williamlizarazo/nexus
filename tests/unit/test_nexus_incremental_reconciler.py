from datetime import date

from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
    NexusSourceProject,
    NexusSourceUser,
)
from memory_core.domain.nexus_graph import (
    GraphEdge,
    GraphNode,
)
from memory_core.domain.nexus_incremental import NexusAffectedScope
from memory_core.services.nexus_incremental_reconciler import (
    NexusIncrementalReconciler,
)
from memory_core.services.nexus_projector import NexusProjector


class FakeSource:
    def __init__(self, snapshot):
        self.snapshot = snapshot

    def load_scope(self, *, scope):
        return self.snapshot


class FakeRepository:
    def __init__(self, *, nodes=(), edges=()):
        self.nodes = list(nodes)
        self.edges = list(edges)

        self.upserted_nodes = []
        self.upserted_edges = []
        self.deactivated_nodes = []
        self.deactivated_edges = []

    def list_nodes(self, *, active_only=True):
        return list(self.nodes)

    def list_edges(self, *, active_only=True):
        return list(self.edges)

    def upsert_nodes(self, nodes):
        self.upserted_nodes.extend(nodes)

    def upsert_edges(self, edges):
        self.upserted_edges.extend(edges)

    def deactivate_nodes(self, node_keys):
        self.deactivated_nodes.extend(node_keys)

    def deactivate_edges(self, edge_keys):
        self.deactivated_edges.extend(edge_keys)


def _project_snapshot():
    return NexusBackfillSnapshot(
        users=(
            NexusSourceUser(
                user_id="user-1",
                email="one@example.com",
                full_name="User One",
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
                name="Proyecto",
                description=None,
                status="active",
                deleted_at=None,
            ),
        ),
        project_memberships=(),
        annotated_pages=(),
    )


def test_reconciler_deactivates_stale_project_edges():
    repository = FakeRepository(
        nodes=(
            GraphNode(
                node_key="project:project-1",
                node_type="project",
                entity_id="project-1",
                label="Proyecto",
            ),
        ),
        edges=(
            GraphEdge(
                source_key="user:user-2",
                relation_type="WORKS_ON",
                target_key="project:project-1",
            ),
            GraphEdge(
                source_key="project:project-1",
                relation_type="USES",
                target_key="document:doc-1",
            ),
        ),
    )

    reconciler = NexusIncrementalReconciler(
        source=FakeSource(
            _project_snapshot()
        ),
        projector=NexusProjector(
            reference_date=date(
                2026,
                9,
                30,
            )
        ),
        repository=repository,
    )

    reconciler.reconcile(
        scope=NexusAffectedScope(
            project_ids=(
                "project-1",
            ),
        )
    )

    assert set(
        repository.deactivated_edges
    ) == {
        (
            "user:user-2",
            "WORKS_ON",
            "project:project-1",
        ),
        (
            "project:project-1",
            "USES",
            "document:doc-1",
        ),
    }


def test_reconciler_deactivates_missing_project_node():
    repository = FakeRepository(
        nodes=(
            GraphNode(
                node_key="project:project-1",
                node_type="project",
                entity_id="project-1",
                label="Proyecto",
            ),
        ),
    )

    reconciler = NexusIncrementalReconciler(
        source=FakeSource(
            NexusBackfillSnapshot(
                users=(),
                units=(),
                user_unit_memberships=(),
                projects=(),
                project_memberships=(),
                annotated_pages=(),
            )
        ),
        projector=NexusProjector(
            reference_date=date(
                2026,
                9,
                30,
            )
        ),
        repository=repository,
    )

    reconciler.reconcile(
        scope=NexusAffectedScope(
            project_ids=(
                "project-1",
            ),
        )
    )

    assert repository.deactivated_nodes == [
        "project:project-1"
    ]


def test_reconciler_does_not_incrementally_remove_document_topology():
    repository = FakeRepository(
        nodes=(
            GraphNode(
                node_key="document:doc-1",
                node_type="document",
                entity_id="doc-1",
                label="Documento",
            ),
            GraphNode(
                node_key="page:doc-1:3",
                node_type="page",
                entity_id="doc-1:3",
                label="Página 4",
            ),
        ),
        edges=(
            GraphEdge(
                source_key="document:doc-1",
                relation_type="CONTAINS",
                target_key="page:doc-1:3",
            ),
        ),
    )

    reconciler = NexusIncrementalReconciler(
        source=FakeSource(
            _project_snapshot()
        ),
        projector=NexusProjector(
            reference_date=date(
                2026,
                9,
                30,
            )
        ),
        repository=repository,
    )

    reconciler.reconcile(
        scope=NexusAffectedScope(
            project_ids=(
                "project-1",
            ),
        )
    )

    assert repository.deactivated_nodes == []
    assert repository.deactivated_edges == []


def test_reconciler_upserts_expected_projection():
    repository = FakeRepository()

    reconciler = NexusIncrementalReconciler(
        source=FakeSource(
            _project_snapshot()
        ),
        projector=NexusProjector(
            reference_date=date(
                2026,
                9,
                30,
            )
        ),
        repository=repository,
    )

    reconciler.reconcile(
        scope=NexusAffectedScope(
            project_ids=(
                "project-1",
            ),
        )
    )

    assert {
        node.node_key
        for node in repository.upserted_nodes
    } == {
        "user:user-1",
        "project:project-1",
    }
