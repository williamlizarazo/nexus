from datetime import date, datetime, timezone

import pytest

from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
    NexusSourceAnnotatedPage,
    NexusSourceProject,
    NexusSourceProjectMembership,
    NexusSourceUnit,
    NexusSourceUser,
    NexusSourceUserUnitMembership,
)
from memory_core.services.nexus_projector import NexusProjector


REFERENCE_DATE = date(2026, 9, 28)


def _projector() -> NexusProjector:
    return NexusProjector(
        reference_date=REFERENCE_DATE,
    )


def _nodes_by_key(graph):
    return {
        node.node_key: node
        for node in graph.nodes
    }


def _edges_by_key(graph):
    return {
        (
            edge.source_key,
            edge.relation_type,
            edge.target_key,
        ): edge
        for edge in graph.edges
    }


def test_projector_creates_user_unit_and_project_nodes():
    snapshot = NexusBackfillSnapshot(
        users=(
            NexusSourceUser(
                user_id="user-1",
                email="persona@jep.gov.co",
                full_name="Persona Uno",
                functional_role="Analista",
                status="active",
            ),
        ),
        units=(
            NexusSourceUnit(
                unit_id="unit-1",
                name="Magistratura X",
                unit_type="magistratura",
                status="active",
            ),
        ),
        projects=(
            NexusSourceProject(
                project_id="project-1",
                owner_user_id="user-1",
                name="Proyecto Uno",
                description="Proyecto de prueba",
                status="active",
            ),
        ),
    )

    graph = _projector().project(snapshot)
    nodes = _nodes_by_key(graph)

    assert set(nodes) == {
        "user:user-1",
        "organizational_unit:unit-1",
        "project:project-1",
    }

    assert nodes["user:user-1"].node_type == "user"
    assert nodes["user:user-1"].label == "Persona Uno"

    assert (
        nodes["organizational_unit:unit-1"].node_type
        == "organizational_unit"
    )
    assert (
        nodes["organizational_unit:unit-1"].label
        == "Magistratura X"
    )

    assert nodes["project:project-1"].node_type == "project"
    assert nodes["project:project-1"].label == "Proyecto Uno"


def test_project_is_preserved_without_annotations():
    snapshot = NexusBackfillSnapshot(
        users=(
            NexusSourceUser(
                user_id="user-1",
                email="persona@jep.gov.co",
            ),
        ),
        projects=(
            NexusSourceProject(
                project_id="project-1",
                owner_user_id="user-1",
                name="Proyecto sin actividad",
            ),
        ),
    )

    graph = _projector().project(snapshot)

    assert (
        "project:project-1"
        in _nodes_by_key(graph)
    )

    assert not any(
        node.node_type in {"document", "page"}
        for node in graph.nodes
    )


def test_projector_creates_belongs_to_only_for_current_membership():
    snapshot = NexusBackfillSnapshot(
        users=(
            NexusSourceUser(
                user_id="user-1",
                email="persona@jep.gov.co",
            ),
        ),
        units=(
            NexusSourceUnit(
                unit_id="unit-current",
                name="Unidad Vigente",
                unit_type="magistratura",
            ),
            NexusSourceUnit(
                unit_id="unit-expired",
                name="Unidad Expirada",
                unit_type="direccion",
            ),
            NexusSourceUnit(
                unit_id="unit-future",
                name="Unidad Futura",
                unit_type="direccion",
            ),
            NexusSourceUnit(
                unit_id="unit-inactive",
                name="Unidad Inactiva",
                unit_type="direccion",
            ),
        ),
        user_unit_memberships=(
            NexusSourceUserUnitMembership(
                user_id="user-1",
                unit_id="unit-current",
                status="active",
                is_primary=True,
                valid_from=date(2026, 1, 1),
                valid_to=None,
            ),
            NexusSourceUserUnitMembership(
                user_id="user-1",
                unit_id="unit-expired",
                status="active",
                valid_from=date(2025, 1, 1),
                valid_to=date(2026, 1, 31),
            ),
            NexusSourceUserUnitMembership(
                user_id="user-1",
                unit_id="unit-future",
                status="active",
                valid_from=date(2027, 1, 1),
            ),
            NexusSourceUserUnitMembership(
                user_id="user-1",
                unit_id="unit-inactive",
                status="inactive",
            ),
        ),
    )

    graph = _projector().project(snapshot)
    edges = _edges_by_key(graph)

    assert set(edges) == {
        (
            "user:user-1",
            "BELONGS_TO",
            "organizational_unit:unit-current",
        ),
    }

    edge = edges[
        (
            "user:user-1",
            "BELONGS_TO",
            "organizational_unit:unit-current",
        )
    ]

    assert edge.metadata["is_primary"] is True


def test_projector_creates_works_on_from_project_membership():
    snapshot = NexusBackfillSnapshot(
        users=(
            NexusSourceUser(
                user_id="user-1",
                email="persona@jep.gov.co",
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

    graph = _projector().project(snapshot)
    edges = _edges_by_key(graph)

    key = (
        "user:user-1",
        "WORKS_ON",
        "project:project-1",
    )

    assert key in edges
    assert edges[key].metadata["role"] == "owner"


def test_annotated_page_creates_document_page_and_structural_edges():
    snapshot = NexusBackfillSnapshot(
        users=(
            NexusSourceUser(
                user_id="user-1",
                email="persona@jep.gov.co",
            ),
        ),
        projects=(
            NexusSourceProject(
                project_id="project-1",
                owner_user_id="user-1",
                name="Proyecto Uno",
            ),
        ),
        annotated_pages=(
            NexusSourceAnnotatedPage(
                project_id="project-1",
                doc_id="doc-1",
                document_label="Documento Uno.pdf",
                page_idx=12,
                page_num=13,
                annotation_count=3,
            ),
        ),
    )

    graph = _projector().project(snapshot)
    nodes = _nodes_by_key(graph)
    edges = _edges_by_key(graph)

    assert "document:doc-1" in nodes
    assert "page:doc-1:12" in nodes

    assert nodes["document:doc-1"].label == "Documento Uno.pdf"
    assert nodes["page:doc-1:12"].node_type == "page"
    assert nodes["page:doc-1:12"].entity_id == "doc-1:12"

    assert (
        "project:project-1",
        "USES",
        "document:doc-1",
    ) in edges

    assert (
        "document:doc-1",
        "CONTAINS",
        "page:doc-1:12",
    ) in edges


def test_same_document_and_page_are_shared_across_projects():
    snapshot = NexusBackfillSnapshot(
        users=(
            NexusSourceUser(
                user_id="user-1",
                email="uno@jep.gov.co",
            ),
            NexusSourceUser(
                user_id="user-2",
                email="dos@jep.gov.co",
            ),
        ),
        projects=(
            NexusSourceProject(
                project_id="project-1",
                owner_user_id="user-1",
                name="Proyecto Uno",
            ),
            NexusSourceProject(
                project_id="project-2",
                owner_user_id="user-2",
                name="Proyecto Dos",
            ),
        ),
        annotated_pages=(
            NexusSourceAnnotatedPage(
                project_id="project-1",
                doc_id="doc-shared",
                document_label="Documento Compartido.pdf",
                page_idx=5,
                page_num=6,
            ),
            NexusSourceAnnotatedPage(
                project_id="project-2",
                doc_id="doc-shared",
                document_label="Documento Compartido.pdf",
                page_idx=5,
                page_num=6,
            ),
        ),
    )

    graph = _projector().project(snapshot)

    document_nodes = [
        node
        for node in graph.nodes
        if node.node_type == "document"
    ]

    page_nodes = [
        node
        for node in graph.nodes
        if node.node_type == "page"
    ]

    assert len(document_nodes) == 1
    assert len(page_nodes) == 1

    uses_edges = [
        edge
        for edge in graph.edges
        if edge.relation_type == "USES"
    ]

    contains_edges = [
        edge
        for edge in graph.edges
        if edge.relation_type == "CONTAINS"
    ]

    assert len(uses_edges) == 2
    assert len(contains_edges) == 1


def test_duplicate_annotated_page_does_not_duplicate_topology():
    snapshot = NexusBackfillSnapshot(
        users=(
            NexusSourceUser(
                user_id="user-1",
                email="persona@jep.gov.co",
            ),
        ),
        projects=(
            NexusSourceProject(
                project_id="project-1",
                owner_user_id="user-1",
                name="Proyecto Uno",
            ),
        ),
        annotated_pages=(
            NexusSourceAnnotatedPage(
                project_id="project-1",
                doc_id="doc-1",
                document_label="Documento.pdf",
                page_idx=4,
                page_num=5,
                annotation_count=1,
            ),
            NexusSourceAnnotatedPage(
                project_id="project-1",
                doc_id="doc-1",
                document_label="Documento.pdf",
                page_idx=4,
                page_num=5,
                annotation_count=4,
            ),
        ),
    )

    graph = _projector().project(snapshot)

    assert len(
        [
            node
            for node in graph.nodes
            if node.node_type == "document"
        ]
    ) == 1

    assert len(
        [
            node
            for node in graph.nodes
            if node.node_type == "page"
        ]
    ) == 1

    assert len(
        [
            edge
            for edge in graph.edges
            if edge.relation_type == "USES"
        ]
    ) == 1

    assert len(
        [
            edge
            for edge in graph.edges
            if edge.relation_type == "CONTAINS"
        ]
    ) == 1


def test_projection_is_deterministic_regardless_of_source_order():
    user_1 = NexusSourceUser(
        user_id="user-1",
        email="uno@jep.gov.co",
    )

    user_2 = NexusSourceUser(
        user_id="user-2",
        email="dos@jep.gov.co",
    )

    project_1 = NexusSourceProject(
        project_id="project-1",
        owner_user_id="user-1",
        name="Proyecto Uno",
    )

    project_2 = NexusSourceProject(
        project_id="project-2",
        owner_user_id="user-2",
        name="Proyecto Dos",
    )

    page_1 = NexusSourceAnnotatedPage(
        project_id="project-1",
        doc_id="doc-1",
        document_label="Documento Uno.pdf",
        page_idx=0,
        page_num=1,
    )

    page_2 = NexusSourceAnnotatedPage(
        project_id="project-2",
        doc_id="doc-2",
        document_label="Documento Dos.pdf",
        page_idx=2,
        page_num=3,
    )

    first = NexusBackfillSnapshot(
        users=(user_1, user_2),
        projects=(project_1, project_2),
        annotated_pages=(page_1, page_2),
    )

    second = NexusBackfillSnapshot(
        users=(user_2, user_1),
        projects=(project_2, project_1),
        annotated_pages=(page_2, page_1),
    )

    projector = _projector()

    assert projector.project(first) == projector.project(second)


def test_projector_rejects_project_membership_with_unknown_user():
    snapshot = NexusBackfillSnapshot(
        projects=(
            NexusSourceProject(
                project_id="project-1",
                owner_user_id="user-missing",
                name="Proyecto Uno",
            ),
        ),
        project_memberships=(
            NexusSourceProjectMembership(
                project_id="project-1",
                user_id="user-missing",
                role="owner",
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="Unknown NEXUS user",
    ):
        _projector().project(snapshot)


def test_deleted_project_is_preserved_as_inactive_node():
    snapshot = NexusBackfillSnapshot(
        users=(
            NexusSourceUser(
                user_id="user-1",
                email="persona@jep.gov.co",
            ),
        ),
        projects=(
            NexusSourceProject(
                project_id="project-1",
                owner_user_id="user-1",
                name="Proyecto eliminado",
                status="deleted",
                deleted_at=datetime(
                    2026,
                    9,
                    1,
                    tzinfo=timezone.utc,
                ),
            ),
        ),
    )

    graph = _projector().project(snapshot)

    node = _nodes_by_key(graph)["project:project-1"]

    assert node.active is False
    assert node.metadata["status"] == "deleted"
