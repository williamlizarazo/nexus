import networkx as nx

from memory_core.analysis.nexus_networkx import (
    NexusNetworkXGraphBuilder,
)
from memory_core.domain.nexus_graph import (
    GraphEdge,
    GraphNode,
    NexusGraphSnapshot,
)


def _snapshot() -> NexusGraphSnapshot:
    return NexusGraphSnapshot(
        nodes=(
            GraphNode(
                node_key="user:user-1",
                node_type="user",
                entity_id="user-1",
                label="Usuario Uno",
                metadata={
                    "functional_role": "analyst",
                },
            ),
            GraphNode(
                node_key="project:project-1",
                node_type="project",
                entity_id="project-1",
                label="Proyecto Uno",
            ),
            GraphNode(
                node_key="document:doc-1",
                node_type="document",
                entity_id="doc-1",
                label="Documento Uno",
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
            GraphEdge(
                source_key="project:project-1",
                relation_type="USES",
                target_key="document:doc-1",
            ),
        ),
    )


def test_builder_returns_multidigraph():
    graph = NexusNetworkXGraphBuilder.build(
        _snapshot()
    )

    assert isinstance(
        graph,
        nx.MultiDiGraph,
    )


def test_builder_preserves_nodes_and_attributes():
    graph = NexusNetworkXGraphBuilder.build(
        _snapshot()
    )

    assert set(graph.nodes) == {
        "user:user-1",
        "project:project-1",
        "document:doc-1",
    }

    assert (
        graph.nodes["user:user-1"]["node_type"]
        == "user"
    )

    assert (
        graph.nodes["user:user-1"]["entity_id"]
        == "user-1"
    )

    assert (
        graph.nodes["user:user-1"]["label"]
        == "Usuario Uno"
    )

    assert (
        graph.nodes["user:user-1"]["metadata"]
        == {
            "functional_role": "analyst",
        }
    )


def test_builder_preserves_relation_type_and_metadata():
    graph = NexusNetworkXGraphBuilder.build(
        _snapshot()
    )

    data = graph.get_edge_data(
        "user:user-1",
        "project:project-1",
    )

    assert data is not None
    assert len(data) == 1

    edge = next(
        iter(data.values())
    )

    assert edge["relation_type"] == "WORKS_ON"
    assert edge["metadata"] == {
        "role": "owner",
    }


def test_builder_can_exclude_inactive_topology():
    snapshot = NexusGraphSnapshot(
        nodes=(
            GraphNode(
                node_key="user:user-1",
                node_type="user",
                entity_id="user-1",
                label="Activo",
                active=True,
            ),
            GraphNode(
                node_key="user:user-2",
                node_type="user",
                entity_id="user-2",
                label="Inactivo",
                active=False,
            ),
        ),
        edges=(),
    )

    graph = NexusNetworkXGraphBuilder.build(
        snapshot,
        active_only=True,
    )

    assert set(graph.nodes) == {
        "user:user-1",
    }


def test_builder_ignores_edges_with_filtered_endpoint():
    snapshot = NexusGraphSnapshot(
        nodes=(
            GraphNode(
                node_key="user:user-1",
                node_type="user",
                entity_id="user-1",
                label="Activo",
                active=True,
            ),
            GraphNode(
                node_key="project:project-1",
                node_type="project",
                entity_id="project-1",
                label="Inactivo",
                active=False,
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

    graph = NexusNetworkXGraphBuilder.build(
        snapshot,
        active_only=True,
    )

    assert graph.number_of_edges() == 0
