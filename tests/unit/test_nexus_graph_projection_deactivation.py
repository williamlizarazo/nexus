from memory_core.adapters.supabase.nexus_graph_projection import (
    SupabaseGraphProjectionRepository,
)


def test_supabase_graph_repository_exposes_incremental_deactivation():
    assert hasattr(
        SupabaseGraphProjectionRepository,
        "deactivate_nodes",
    )

    assert hasattr(
        SupabaseGraphProjectionRepository,
        "deactivate_edges",
    )
