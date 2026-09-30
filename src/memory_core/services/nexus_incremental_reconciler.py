from __future__ import annotations

from memory_core.contracts.nexus_incremental_graph_projection import (
    IncrementalGraphProjectionRepository,
)
from memory_core.contracts.nexus_incremental_source import (
    NexusIncrementalSource,
)
from memory_core.domain.nexus_graph import GraphEdge, GraphNode
from memory_core.domain.nexus_incremental import NexusAffectedScope
from memory_core.services.nexus_projector import NexusProjector


class NexusIncrementalReconciler:
    """
    Reconcilia una porción afectada de la proyección NEXUS.

    La fuente incremental carga el contexto necesario.
    NexusProjector conserva las reglas canónicas de proyección.
    Este servicio compara la topología esperada con la activa
    y desactiva únicamente relaciones/nodos cuyo alcance puede
    determinarse de forma segura.
    """

    def __init__(
        self,
        *,
        source: NexusIncrementalSource,
        projector: NexusProjector,
        repository: IncrementalGraphProjectionRepository,
    ) -> None:
        self._source = source
        self._projector = projector
        self._repository = repository

    def reconcile(
        self,
        *,
        scope: NexusAffectedScope,
    ) -> None:

        if self._scope_is_empty(scope):
            return

        source_snapshot = self._source.load_scope(
            scope=scope,
        )

        expected = self._projector.project(
            source_snapshot
        )

        current_nodes = self._repository.list_nodes(
            active_only=True,
        )

        current_edges = self._repository.list_edges(
            active_only=True,
        )

        stale_node_keys = self._stale_node_keys(
            scope=scope,
            current=current_nodes,
            expected=list(expected.nodes),
        )

        stale_edge_keys = self._stale_edge_keys(
            scope=scope,
            current=current_edges,
            expected=list(expected.edges),
        )

        # Primero mantenemos/creamos la topología esperada.
        self._repository.upsert_nodes(
            expected.nodes
        )

        self._repository.upsert_edges(
            expected.edges
        )

        # Después desactivamos aquello que dejó de ser válido
        # dentro del alcance que podemos reconciliar con seguridad.
        self._repository.deactivate_edges(
            stale_edge_keys
        )

        self._repository.deactivate_nodes(
            stale_node_keys
        )

    # ============================================================
    # NODES
    # ============================================================

    @staticmethod
    def _stale_node_keys(
        *,
        scope: NexusAffectedScope,
        current: list[GraphNode],
        expected: list[GraphNode],
    ) -> list[str]:

        expected_keys = {
            node.node_key
            for node in expected
        }

        stale: list[str] = []

        project_ids = set(
            scope.project_ids
        )

        user_ids = set(
            scope.user_ids
        )

        unit_ids = set(
            scope.unit_ids
        )

        for node in current:

            directly_scoped = (
                (
                    node.node_type == "project"
                    and node.entity_id in project_ids
                )
                or (
                    node.node_type == "user"
                    and node.entity_id in user_ids
                )
                or (
                    node.node_type
                    == "organizational_unit"
                    and node.entity_id in unit_ids
                )
            )

            if (
                directly_scoped
                and node.node_key
                not in expected_keys
            ):
                stale.append(
                    node.node_key
                )

        return sorted(
            set(stale)
        )

    # ============================================================
    # EDGES
    # ============================================================

    @staticmethod
    def _stale_edge_keys(
        *,
        scope: NexusAffectedScope,
        current: list[GraphEdge],
        expected: list[GraphEdge],
    ) -> list[
        tuple[str, str, str]
    ]:

        expected_keys = {
            (
                edge.source_key,
                edge.relation_type,
                edge.target_key,
            )
            for edge in expected
        }

        project_keys = {
            f"project:{project_id}"
            for project_id
            in scope.project_ids
        }

        user_keys = {
            f"user:{user_id}"
            for user_id
            in scope.user_ids
        }

        unit_keys = {
            (
                "organizational_unit:"
                f"{unit_id}"
            )
            for unit_id
            in scope.unit_ids
        }

        stale: list[
            tuple[str, str, str]
        ] = []

        for edge in current:

            key = (
                edge.source_key,
                edge.relation_type,
                edge.target_key,
            )

            in_safe_scope = False

            if (
                edge.relation_type
                == "WORKS_ON"
            ):
                in_safe_scope = (
                    edge.target_key
                    in project_keys
                    or edge.source_key
                    in user_keys
                )

            elif (
                edge.relation_type
                == "USES"
            ):
                in_safe_scope = (
                    edge.source_key
                    in project_keys
                )

            elif (
                edge.relation_type
                == "BELONGS_TO"
            ):
                in_safe_scope = (
                    edge.source_key
                    in user_keys
                    or edge.target_key
                    in unit_keys
                )

            # CONTAINS se omite deliberadamente.
            # Documento/página puede ser compartido
            # por varios proyectos.

            if (
                in_safe_scope
                and key not in expected_keys
            ):
                stale.append(
                    key
                )

        return sorted(
            set(stale)
        )

    # ============================================================
    # HELPERS
    # ============================================================

    @staticmethod
    def _scope_is_empty(
        scope: NexusAffectedScope,
    ) -> bool:

        return not (
            scope.project_ids
            or scope.user_ids
            or scope.unit_ids
        )
