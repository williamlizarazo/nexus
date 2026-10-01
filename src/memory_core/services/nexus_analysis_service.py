from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import networkx as nx

from memory_core.analysis.nexus_metrics import (
    NexusNetworkMetrics,
    NexusNetworkMetricsAnalyzer,
)
from memory_core.analysis.nexus_networkx import (
    NexusNetworkXGraphBuilder,
)
from memory_core.analysis.nexus_project_projection import (
    NexusProjectProjectionBuilder,
)
from memory_core.analysis.nexus_unit_projection import (
    NexusUnitProjectionBuilder,
)
from memory_core.analysis.nexus_user_projection import (
    NexusUserProjectionBuilder,
)
from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
)
from memory_core.domain.nexus_graph import (
    NexusGraphSnapshot,
)


@dataclass(frozen=True, slots=True)
class NexusAnalysisResult:
    """
    Resultado consolidado de la capa analítica NEXUS.
    """

    structural_graph: nx.MultiDiGraph
    user_graph: nx.Graph
    project_graph: nx.Graph
    unit_graph: nx.Graph

    structural_metrics: NexusNetworkMetrics
    user_metrics: NexusNetworkMetrics
    project_metrics: NexusNetworkMetrics
    unit_metrics: NexusNetworkMetrics


class NexusAnalysisService:
    """
    Orquesta la construcción de grafos y métricas analíticas NEXUS.

    La UI no necesita conocer los builders individuales ni ejecutar
    directamente lógica de NetworkX.
    """

    def __init__(
        self,
        *,
        reference_date: date,
    ) -> None:
        self._reference_date = reference_date

    def analyze(
        self,
        *,
        source_snapshot: NexusBackfillSnapshot,
        graph_snapshot: NexusGraphSnapshot,
    ) -> NexusAnalysisResult:

        # --------------------------------------------------------
        # STRUCTURAL GRAPH
        # --------------------------------------------------------

        structural_graph = (
            NexusNetworkXGraphBuilder.build(
                graph_snapshot,
                active_only=True,
            )
        )

        # --------------------------------------------------------
        # DERIVED PROJECTIONS
        # --------------------------------------------------------

        user_graph = (
            NexusUserProjectionBuilder.build(
                source_snapshot,
            )
        )

        project_graph = (
            NexusProjectProjectionBuilder.build(
                source_snapshot,
            )
        )

        unit_graph = (
            NexusUnitProjectionBuilder.build(
                source_snapshot,
                reference_date=self._reference_date,
            )
        )

        # --------------------------------------------------------
        # METRICS
        # --------------------------------------------------------

        structural_metrics = (
            NexusNetworkMetricsAnalyzer.analyze(
                structural_graph,
            )
        )

        user_metrics = (
            NexusNetworkMetricsAnalyzer.analyze(
                user_graph,
            )
        )

        project_metrics = (
            NexusNetworkMetricsAnalyzer.analyze(
                project_graph,
            )
        )

        unit_metrics = (
            NexusNetworkMetricsAnalyzer.analyze(
                unit_graph,
            )
        )

        return NexusAnalysisResult(
            structural_graph=structural_graph,
            user_graph=user_graph,
            project_graph=project_graph,
            unit_graph=unit_graph,
            structural_metrics=structural_metrics,
            user_metrics=user_metrics,
            project_metrics=project_metrics,
            unit_metrics=unit_metrics,
        )
