from memory_core.contracts.nexus_graph_projection import (
    GraphProjectionRepository,
)
from memory_core.domain.nexus_graph import GraphEdge, GraphNode


class FakeGraphProjectionRepository:

    def list_nodes(
        self,
        *,
        active_only: bool = True,
    ) -> list[GraphNode]:
        return []

    def list_edges(
        self,
        *,
        active_only: bool = True,
    ) -> list[GraphEdge]:
        return []

    def upsert_nodes(
        self,
        nodes,
    ) -> None:
        return None

    def upsert_edges(
        self,
        edges,
    ) -> None:
        return None


def test_structural_repository_implements_graph_projection_contract():
    repository = FakeGraphProjectionRepository()

    assert isinstance(
        repository,
        GraphProjectionRepository,
    )


def test_contract_exposes_read_and_write_operations():
    expected = {
        "list_nodes",
        "list_edges",
        "upsert_nodes",
        "upsert_edges",
    }

    assert expected.issubset(
        set(dir(GraphProjectionRepository))
    )
