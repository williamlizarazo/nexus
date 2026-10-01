from __future__ import annotations

from typing import Any

from memory_core.services.nexus_analysis_service import (
    NexusAnalysisResult,
)


class NexusPresenter:
    """
    Convierte el resultado analítico NEXUS en estructuras
    simples consumibles por PyShiny.
    """

    def __init__(
        self,
        result: NexusAnalysisResult,
    ) -> None:
        self._result = result

    def kpis(
        self,
    ) -> dict[str, int | float]:
        return {
            "structural_nodes": (
                self._result
                .structural_metrics
                .node_count
            ),
            "structural_edges": (
                self._result
                .structural_metrics
                .edge_count
            ),
            "structural_components": (
                self._result
                .structural_metrics
                .connected_component_count
            ),
            "structural_isolates": (
                self._result
                .structural_metrics
                .isolate_count
            ),
            "structural_density": (
                self._result
                .structural_metrics
                .density
            ),
            "users": (
                self._result
                .user_metrics
                .node_count
            ),
            "projects": (
                self._result
                .project_metrics
                .node_count
            ),
            "units": (
                self._result
                .unit_metrics
                .node_count
            ),
        }

    def graph_payload(
        self,
        graph_name: str,
    ) -> dict[str, list[dict[str, Any]]]:

        graph, _metrics = self._resolve_graph(
            graph_name
        )

        nodes = []

        for node_id, data in graph.nodes(
            data=True
        ):
            row = {
                "id": str(node_id),
                **dict(data),
            }

            row.setdefault(
                "label",
                str(node_id),
            )

            nodes.append(row)

        nodes.sort(
            key=lambda row: row["id"]
        )

        edges = []

        if graph.is_multigraph():
            iterator = graph.edges(
                keys=True,
                data=True,
            )

            for (
                source,
                target,
                key,
                data,
            ) in iterator:
                edges.append(
                    {
                        "source": str(source),
                        "target": str(target),
                        "key": str(key),
                        **dict(data),
                    }
                )

        else:
            for (
                source,
                target,
                data,
            ) in graph.edges(data=True):
                edges.append(
                    {
                        "source": str(source),
                        "target": str(target),
                        **dict(data),
                    }
                )

        edges.sort(
            key=lambda row: (
                row["source"],
                row["target"],
                row.get("key", ""),
            )
        )

        return {
            "nodes": nodes,
            "edges": edges,
        }

    def centrality_rows(
        self,
        graph_name: str,
    ) -> list[dict[str, Any]]:

        graph, metrics = self._resolve_graph(
            graph_name
        )

        degree = dict(
            metrics.degree_centrality
        )

        betweenness = dict(
            metrics.betweenness_centrality
        )

        rows = []

        for node_id, data in graph.nodes(
            data=True
        ):
            node_key = str(node_id)

            rows.append(
                {
                    "node": node_key,
                    "label": (
                        data.get("label")
                        or node_key
                    ),
                    "degree_centrality": (
                        degree.get(
                            node_key,
                            0.0,
                        )
                    ),
                    "betweenness_centrality": (
                        betweenness.get(
                            node_key,
                            0.0,
                        )
                    ),
                }
            )

        rows.sort(
            key=lambda row: (
                -row[
                    "degree_centrality"
                ],
                -row[
                    "betweenness_centrality"
                ],
                row["label"],
            )
        )

        return rows

    def network_kpis(
        self,
        graph_name: str,
    ) -> dict[str, int | float]:

        _graph, metrics = self._resolve_graph(
            graph_name
        )

        return {
            "nodes": metrics.node_count,
            "edges": metrics.edge_count,
            "components": (
                metrics.connected_component_count
            ),
            "isolates": metrics.isolate_count,
            "density": metrics.density,
        }

    def _resolve_graph(
        self,
        graph_name: str,
    ):
        normalized = (
            graph_name
            .strip()
            .lower()
        )

        if normalized == "structural":
            return (
                self._result.structural_graph,
                self._result.structural_metrics,
            )

        if normalized == "users":
            return (
                self._result.user_graph,
                self._result.user_metrics,
            )

        if normalized == "projects":
            return (
                self._result.project_graph,
                self._result.project_metrics,
            )

        if normalized == "units":
            return (
                self._result.unit_graph,
                self._result.unit_metrics,
            )

        raise ValueError(
            f"Unknown graph: {graph_name}"
        )
