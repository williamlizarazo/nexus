from datetime import date

import networkx as nx

from memory_core.analysis.nexus_unit_projection import (
    NexusUnitProjectionBuilder,
)
from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
    NexusSourceAnnotatedPage,
    NexusSourceProject,
    NexusSourceProjectMembership,
    NexusSourceUnit,
    NexusSourceUser,
    NexusSourceUserUnitMembership,
)


REFERENCE_DATE = date(2026, 9, 30)


def _snapshot():
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
        units=(
            NexusSourceUnit(
                unit_id="unit-1",
                name="Unidad 1",
                unit_type="office",
                status="active",
            ),
            NexusSourceUnit(
                unit_id="unit-2",
                name="Unidad 2",
                unit_type="office",
                status="active",
            ),
        ),
        user_unit_memberships=(
            NexusSourceUserUnitMembership(
                user_id="user-1",
                unit_id="unit-1",
                status="active",
                is_primary=True,
                valid_from=date(2026, 1, 1),
                valid_to=None,
            ),
            NexusSourceUserUnitMembership(
                user_id="user-2",
                unit_id="unit-2",
                status="active",
                is_primary=True,
                valid_from=date(2026, 1, 1),
                valid_to=None,
            ),
        ),
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
                project_id="project-1",
                user_id="user-2",
                role="member",
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


def test_unit_projection_returns_undirected_graph():
    graph = NexusUnitProjectionBuilder.build(
        _snapshot(),
        reference_date=REFERENCE_DATE,
    )

    assert isinstance(graph, nx.Graph)
    assert not graph.is_directed()


def test_units_share_project_document_and_page():
    graph = NexusUnitProjectionBuilder.build(
        _snapshot(),
        reference_date=REFERENCE_DATE,
    )

    data = graph[
        "organizational_unit:unit-1"
    ][
        "organizational_unit:unit-2"
    ]

    assert data["shared_project_count"] == 1
    assert data["shared_document_count"] == 1
    assert data["shared_page_count"] == 1


def test_expired_membership_is_excluded():
    snapshot = _snapshot()

    snapshot = NexusBackfillSnapshot(
        users=snapshot.users,
        units=snapshot.units,
        user_unit_memberships=(
            NexusSourceUserUnitMembership(
                user_id="user-1",
                unit_id="unit-1",
                status="active",
                is_primary=True,
                valid_from=date(2025, 1, 1),
                valid_to=date(2025, 12, 31),
            ),
            snapshot.user_unit_memberships[1],
        ),
        projects=snapshot.projects,
        project_memberships=snapshot.project_memberships,
        annotated_pages=snapshot.annotated_pages,
    )

    graph = NexusUnitProjectionBuilder.build(
        snapshot,
        reference_date=REFERENCE_DATE,
    )

    assert not graph.has_edge(
        "organizational_unit:unit-1",
        "organizational_unit:unit-2",
    )
