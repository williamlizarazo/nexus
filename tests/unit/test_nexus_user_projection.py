import networkx as nx

from memory_core.analysis.nexus_user_projection import (
    NexusUserProjectionBuilder,
)
from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
    NexusSourceAnnotatedPage,
    NexusSourceProject,
    NexusSourceProjectMembership,
    NexusSourceUser,
)


def _snapshot() -> NexusBackfillSnapshot:
    return NexusBackfillSnapshot(
        users=(
            NexusSourceUser(
                user_id="user-1",
                email="one@example.com",
                full_name="User One",
                functional_role=None,
                status="active",
            ),
            NexusSourceUser(
                user_id="user-2",
                email="two@example.com",
                full_name="User Two",
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
                annotation_count=2,
            ),
        ),
    )


def test_user_projection_returns_undirected_graph():
    graph = NexusUserProjectionBuilder.build(
        _snapshot()
    )

    assert isinstance(graph, nx.Graph)
    assert not graph.is_directed()


def test_user_projection_contains_users():
    graph = NexusUserProjectionBuilder.build(
        _snapshot()
    )

    assert set(graph.nodes) == {
        "user:user-1",
        "user:user-2",
    }


def test_users_connected_by_shared_document_and_page():
    graph = NexusUserProjectionBuilder.build(
        _snapshot()
    )

    data = graph[
        "user:user-1"
    ][
        "user:user-2"
    ]

    assert data["shared_project_count"] == 0
    assert data["shared_document_count"] == 1
    assert data["shared_page_count"] == 1

    assert data["shared_documents"] == (
        "doc-A",
    )

    assert data["shared_pages"] == (
        ("doc-A", 3),
    )


def test_users_in_same_project_report_shared_project():
    snapshot = _snapshot()

    snapshot = NexusBackfillSnapshot(
        users=snapshot.users,
        units=(),
        user_unit_memberships=(),
        projects=snapshot.projects,
        project_memberships=(
            NexusSourceProjectMembership(
                project_id="project-1",
                user_id="user-1",
                role="owner",
            ),
            NexusSourceProjectMembership(
                project_id="project-1",
                user_id="user-2",
                role="member",
            ),
        ),
        annotated_pages=snapshot.annotated_pages,
    )

    graph = NexusUserProjectionBuilder.build(
        snapshot
    )

    data = graph[
        "user:user-1"
    ][
        "user:user-2"
    ]

    assert data["shared_project_count"] == 1
    assert data["shared_projects"] == (
        "project-1",
    )


def test_users_without_shared_evidence_are_not_connected():
    snapshot = NexusBackfillSnapshot(
        users=_snapshot().users,
        units=(),
        user_unit_memberships=(),
        projects=_snapshot().projects,
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
                document_label=None,
                page_idx=1,
                page_num=2,
                annotation_count=1,
            ),
            NexusSourceAnnotatedPage(
                project_id="project-2",
                doc_id="doc-B",
                document_label=None,
                page_idx=1,
                page_num=2,
                annotation_count=1,
            ),
        ),
    )

    graph = NexusUserProjectionBuilder.build(
        snapshot
    )

    assert not graph.has_edge(
        "user:user-1",
        "user:user-2",
    )
