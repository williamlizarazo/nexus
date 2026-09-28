import pytest

from memory_core.domain.nexus_graph import (
    GraphEdge,
    GraphNode,
    NexusGraphSnapshot,
)


def test_graph_node_preserves_neutral_node_data():
    node = GraphNode(
        node_key="user:user-1",
        node_type="user",
        entity_id="user-1",
        label="Usuario Uno",
        metadata={"functional_role": "Analista"},
    )

    assert node.node_key == "user:user-1"
    assert node.node_type == "user"
    assert node.entity_id == "user-1"
    assert node.label == "Usuario Uno"
    assert node.metadata == {"functional_role": "Analista"}
    assert node.active is True


def test_graph_edge_preserves_neutral_edge_data():
    edge = GraphEdge(
        source_key="user:user-1",
        relation_type="WORKS_ON",
        target_key="project:project-1",
        metadata={"source": "project_assignment"},
    )

    assert edge.source_key == "user:user-1"
    assert edge.relation_type == "WORKS_ON"
    assert edge.target_key == "project:project-1"
    assert edge.metadata == {"source": "project_assignment"}
    assert edge.active is True


def test_graph_snapshot_contains_nodes_and_edges():
    user = GraphNode(
        node_key="user:user-1",
        node_type="user",
        entity_id="user-1",
        label="Usuario Uno",
    )

    project = GraphNode(
        node_key="project:project-1",
        node_type="project",
        entity_id="project-1",
        label="Proyecto Uno",
    )

    edge = GraphEdge(
        source_key=user.node_key,
        relation_type="WORKS_ON",
        target_key=project.node_key,
    )

    snapshot = NexusGraphSnapshot(
        nodes=(user, project),
        edges=(edge,),
    )

    assert snapshot.nodes == (user, project)
    assert snapshot.edges == (edge,)
    assert len(snapshot.nodes) == 2
    assert len(snapshot.edges) == 1


@pytest.mark.parametrize(
    "node_type",
    [
        "organizational_unit",
        "user",
        "project",
        "document",
        "page",
    ],
)
def test_graph_node_accepts_supported_node_types(node_type):
    node = GraphNode(
        node_key=f"{node_type}:1",
        node_type=node_type,
        entity_id="1",
        label="Nodo",
    )

    assert node.node_type == node_type


def test_graph_node_rejects_unsupported_node_type():
    with pytest.raises(ValueError, match="Unsupported NEXUS node type"):
        GraphNode(
            node_key="annotation:1",
            node_type="annotation",
            entity_id="1",
            label="Anotación",
        )


@pytest.mark.parametrize(
    "relation_type",
    [
        "BELONGS_TO",
        "WORKS_ON",
        "USES",
        "CONTAINS",
    ],
)
def test_graph_edge_accepts_supported_relation_types(relation_type):
    edge = GraphEdge(
        source_key="source:1",
        relation_type=relation_type,
        target_key="target:1",
    )

    assert edge.relation_type == relation_type


def test_graph_edge_rejects_unsupported_relation_type():
    with pytest.raises(ValueError, match="Unsupported NEXUS relation type"):
        GraphEdge(
            source_key="user:1",
            relation_type="ANNOTATED",
            target_key="page:1",
        )


def test_graph_edge_rejects_self_relation():
    with pytest.raises(ValueError, match="cannot connect a node to itself"):
        GraphEdge(
            source_key="user:1",
            relation_type="WORKS_ON",
            target_key="user:1",
        )
