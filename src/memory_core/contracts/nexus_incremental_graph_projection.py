from collections.abc import Sequence

from memory_core.contracts.nexus_graph_projection import (
    GraphProjectionRepository,
)
from memory_core.domain.nexus_graph import (
    GraphEdge,
    GraphNode,
)


class IncrementalGraphProjectionRepository(
    GraphProjectionRepository,
):
    def deactivate_nodes(
        self,
        node_keys: Sequence[str],
    ) -> None:
        ...

    def deactivate_edges(
        self,
        edge_keys: Sequence[
            tuple[str, str, str]
        ],
    ) -> None:
        ...
