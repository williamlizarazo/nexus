from datetime import date

import networkx as nx

from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
    NexusSourceAnnotatedPage,
    NexusSourceProject,
    NexusSourceProjectMembership,
    NexusSourceUser,
)
from memory_core.domain.nexus_graph import (
    GraphEdge,
    GraphNode,
    NexusGraphSnapshot,
)
from memory_core.services.nexus_analysis_service import (
    NexusAnalysisService,
)


REFERENCE_DATE = date(2026, 9, 30)


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
            NexusSourceUser(
                user_id="user-2",
                email=None,
                full_name="Usuario 2",
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
            NexusSourceProject(
                project_id="project-2",
                owner_user_id="user-2",
                name="Proyecto 2",
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
            NexusSourceProjectMembership(
                project_id="project-2",
                user_id="user-2",
                role="owner",
            ),
        ),
        annotated_pages=(
            NexusSourceAnnotatedPage(
                project_id="project-1",
                doc_id="doc-A",
                document_label="Documento A",
                page_idx=3,
                page_num=4,
                annotation_count=1,
            ),
            NexusSourceAnnotatedPage(
                project_id="project-2",
                doc_id="doc-A",
                document_label="Documento A",
                page_idx=3,
                page_num=4,
                annotation_count=1,
            ),
        ),
    )


def _graph_snapshot():
    return NexusGraphSnapshot(
        nodes=(
            GraphNode(
                node_key="user:user-1",
                node_type="user",
                entity_id="user-1",
                label="Usuario 1",
            ),
            GraphNode(
                node_key="project:project-1",
                node_type="project",
                entity_id="project-1",
                label="Proyecto 1",
            ),
        ),
        edges=(
            GraphEdge(
                source_key="user:user-1",
                relation_type="WORKS_ON",
                target_key="project:project-1",
            ),
        ),
    )


def test_analysis_service_builds_all_graphs():
    service = NexusAnalysisService(
        reference_date=REFERENCE_DATE,
    )

    result = service.analyze(
        source_snapshot=_source_snapshot(),
        graph_snapshot=_graph_snapshot(),
    )

    assert isinstance(
        result.structural_graph,
        nx.MultiDiGraph,
    )

    assert isinstance(
        result.user_graph,
        nx.Graph,
    )

    assert isinstance(
        result.project_graph,
        nx.Graph,
    )

    assert isinstance(
        result.unit_graph,
        nx.Graph,
    )


def test_analysis_service_computes_metrics():
    service = NexusAnalysisService(
        reference_date=REFERENCE_DATE,
    )

    result = service.analyze(
        source_snapshot=_source_snapshot(),
        graph_snapshot=_graph_snapshot(),
    )

    assert result.structural_metrics.node_count == 2
    assert result.structural_metrics.edge_count == 1

    assert result.user_metrics.node_count == 2
    assert result.user_metrics.edge_count == 1

    assert result.project_metrics.node_count == 2
    assert result.project_metrics.edge_count == 1

    assert result.unit_metrics.node_count == 0
    assert result.unit_metrics.edge_count == 0


def test_analysis_service_preserves_shared_evidence():
    service = NexusAnalysisService(
        reference_date=REFERENCE_DATE,
    )

    result = service.analyze(
        source_snapshot=_source_snapshot(),
        graph_snapshot=_graph_snapshot(),
    )

    user_edge = result.user_graph[
        "user:user-1"
    ][
        "user:user-2"
    ]

    assert user_edge["shared_document_count"] == 1
    assert user_edge["shared_page_count"] == 1
