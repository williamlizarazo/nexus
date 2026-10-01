from __future__ import annotations

from dataclasses import dataclass

import networkx as nx


@dataclass(frozen=True, slots=True)
class NexusNetworkMetrics:
    node_count: int
    edge_count: int
    density: float
    connected_component_count: int
    isolate_count: int

    degree_centrality: tuple[
        tuple[str, float],
        ...,
    ]

    betweenness_centrality: tuple[
        tuple[str, float],
        ...,
    ]


class NexusNetworkMetricsAnalyzer:
    """
    Calcula métricas estructurales neutrales sobre grafos NEXUS.

    Para medidas de centralidad se colapsan aristas paralelas,
    evitando que un MultiGraph aumente artificialmente el grado
    únicamente por representar varios tipos de relación.
    """

    @staticmethod
    def analyze(
        graph: nx.Graph,
    ) -> NexusNetworkMetrics:

        node_count = graph.number_of_nodes()
        edge_count = graph.number_of_edges()

        density = nx.density(graph)

        connected_component_count = (
            NexusNetworkMetricsAnalyzer
            ._component_count(graph)
        )

        isolate_count = sum(
            1
            for _ in nx.isolates(graph)
        )

        simple_graph = (
            NexusNetworkMetricsAnalyzer
            ._simple_graph(graph)
        )

        degree = nx.degree_centrality(
            simple_graph
        )

        betweenness = (
            nx.betweenness_centrality(
                simple_graph,
                normalized=True,
                weight=None,
            )
        )

        return NexusNetworkMetrics(
            node_count=node_count,
            edge_count=edge_count,
            density=density,
            connected_component_count=(
                connected_component_count
            ),
            isolate_count=isolate_count,
            degree_centrality=tuple(
                sorted(
                    (
                        str(node),
                        float(value),
                    )
                    for node, value
                    in degree.items()
                )
            ),
            betweenness_centrality=tuple(
                sorted(
                    (
                        str(node),
                        float(value),
                    )
                    for node, value
                    in betweenness.items()
                )
            ),
        )

    @staticmethod
    def _component_count(
        graph: nx.Graph,
    ) -> int:

        if graph.number_of_nodes() == 0:
            return 0

        if graph.is_directed():
            return (
                nx.number_weakly_connected_components(
                    graph
                )
            )

        return nx.number_connected_components(
            graph
        )

    @staticmethod
    def _simple_graph(
        graph: nx.Graph,
    ) -> nx.Graph:

        if graph.is_directed():
            simple = nx.DiGraph()
        else:
            simple = nx.Graph()

        simple.add_nodes_from(
            graph.nodes(data=True)
        )

        simple.add_edges_from(
            (
                source,
                target,
            )
            for source, target
            in graph.edges()
        )

        return simple
