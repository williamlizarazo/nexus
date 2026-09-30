from memory_core.contracts.nexus_incremental_graph_projection import (
    IncrementalGraphProjectionRepository,
)


def test_incremental_graph_projection_contract_exposes_deactivation():
    methods = {
        name
        for name in dir(
            IncrementalGraphProjectionRepository
        )
    }

    assert "list_nodes" in methods
    assert "list_edges" in methods
    assert "upsert_nodes" in methods
    assert "upsert_edges" in methods
    assert "deactivate_nodes" in methods
    assert "deactivate_edges" in methods
