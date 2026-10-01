import networkx as nx

from memory_core.analysis.nexus_metrics import (
    NexusNetworkMetricsAnalyzer,
)


def _graph():
    graph = nx.Graph()

    graph.add_edge("A", "B")
    graph.add_edge("B", "C")
    graph.add_node("D")

    return graph


def test_metrics_reports_graph_summary():
    metrics = NexusNetworkMetricsAnalyzer.analyze(
        _graph()
    )

    assert metrics.node_count == 4
    assert metrics.edge_count == 2
    assert metrics.connected_component_count == 2
    assert metrics.isolate_count == 1


def test_metrics_reports_density():
    metrics = NexusNetworkMetricsAnalyzer.analyze(
        _graph()
    )

    assert metrics.density == nx.density(
        _graph()
    )


def test_metrics_reports_degree_centrality():
    metrics = NexusNetworkMetricsAnalyzer.analyze(
        _graph()
    )

    values = dict(
        metrics.degree_centrality
    )

    assert values["A"] == 1 / 3
    assert values["B"] == 2 / 3
    assert values["C"] == 1 / 3
    assert values["D"] == 0.0


def test_metrics_reports_betweenness_centrality():
    metrics = NexusNetworkMetricsAnalyzer.analyze(
        _graph()
    )

    values = dict(
        metrics.betweenness_centrality
    )

    assert values["B"] > values["A"]
    assert values["B"] > values["C"]
    assert values["D"] == 0.0


def test_metrics_supports_directed_graph():
    graph = nx.MultiDiGraph()

    graph.add_edge("A", "B")
    graph.add_edge("B", "C")

    metrics = NexusNetworkMetricsAnalyzer.analyze(
        graph
    )

    assert metrics.node_count == 3
    assert metrics.edge_count == 2
    assert metrics.connected_component_count == 1
