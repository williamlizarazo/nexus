from __future__ import annotations

import networkx as nx

from memory_core.domain.nexus_graph import (
    NexusGraphSnapshot,
)


class NexusNetworkXGraphBuilder:
    """
    Convierte una proyección neutral NEXUS en un MultiDiGraph.

    La estructura de dominio permanece agnóstica de NetworkX.
    """

    @staticmethod
    def build(
        snapshot: NexusGraphSnapshot,
        *,
        active_only: bool = True,
    ) -> nx.MultiDiGraph:

        graph = nx.MultiDiGraph()

        included_nodes: set[str] = set()

        for node in snapshot.nodes:
            if active_only and not node.active:
                continue

            graph.add_node(
                node.node_key,
                node_type=node.node_type,
                entity_id=node.entity_id,
                label=node.label,
                metadata=dict(node.metadata),
                active=node.active,
            )

            included_nodes.add(
                node.node_key
            )

        for edge in snapshot.edges:
            if active_only and not edge.active:
                continue

            if (
                edge.source_key
                not in included_nodes
                or edge.target_key
                not in included_nodes
            ):
                continue

            graph.add_edge(
                edge.source_key,
                edge.target_key,
                relation_type=(
                    edge.relation_type
                ),
                metadata=dict(
                    edge.metadata
                ),
                active=edge.active,
            )

        return graph
