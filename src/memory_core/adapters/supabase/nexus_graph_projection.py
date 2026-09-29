from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from supabase import Client

from memory_core.domain.nexus_graph import (
    GraphEdge,
    GraphNode,
)


class SupabaseGraphProjectionRepository:
    """
    Adaptador Supabase para la proyección estructural NEXUS.

    Persiste GraphNode y GraphEdge en nexus_nodes y nexus_edges
    sin conocer las reglas mediante las cuales se construyó el grafo.
    """

    def __init__(
        self,
        client: Client,
        *,
        read_page_size: int = 1000,
        write_batch_size: int = 500,
    ) -> None:
        if read_page_size < 1:
            raise ValueError(
                "read_page_size must be greater than zero"
            )

        if write_batch_size < 1:
            raise ValueError(
                "write_batch_size must be greater than zero"
            )

        self._client = client
        self._read_page_size = read_page_size
        self._write_batch_size = write_batch_size

    # ============================================================
    # READ
    # ============================================================

    def list_nodes(
        self,
        *,
        active_only: bool = True,
    ) -> list[GraphNode]:

        rows = self._fetch_all(
            table_name="nexus_nodes",
            columns=(
                "node_key,"
                "node_type,"
                "entity_id,"
                "label,"
                "metadata,"
                "active"
            ),
            order_by=(
                "node_key",
            ),
            active_only=active_only,
        )

        return [
            self._node_from_row(
                row
            )
            for row in rows
        ]

    def list_edges(
        self,
        *,
        active_only: bool = True,
    ) -> list[GraphEdge]:

        rows = self._fetch_all(
            table_name="nexus_edges",
            columns=(
                "source_key,"
                "relation_type,"
                "target_key,"
                "metadata,"
                "active"
            ),
            order_by=(
                "source_key",
                "relation_type",
                "target_key",
            ),
            active_only=active_only,
        )

        return [
            self._edge_from_row(
                row
            )
            for row in rows
        ]

    # ============================================================
    # WRITE
    # ============================================================

    def upsert_nodes(
        self,
        nodes: Sequence[GraphNode],
    ) -> None:

        rows = [
            {
                "node_key": node.node_key,
                "node_type": node.node_type,
                "entity_id": node.entity_id,
                "label": node.label,
                "metadata": dict(
                    node.metadata
                ),
                "active": node.active,
            }
            for node in sorted(
                nodes,
                key=lambda item: (
                    item.node_key
                ),
            )
        ]

        self._upsert_batches(
            table_name="nexus_nodes",
            rows=rows,
            on_conflict="node_key",
        )

    def upsert_edges(
        self,
        edges: Sequence[GraphEdge],
    ) -> None:

        rows = [
            {
                "source_key": edge.source_key,
                "relation_type": (
                    edge.relation_type
                ),
                "target_key": edge.target_key,
                "metadata": dict(
                    edge.metadata
                ),
                "active": edge.active,
            }
            for edge in sorted(
                edges,
                key=lambda item: (
                    item.source_key,
                    item.relation_type,
                    item.target_key,
                ),
            )
        ]

        self._upsert_batches(
            table_name="nexus_edges",
            rows=rows,
            on_conflict=(
                "source_key,"
                "relation_type,"
                "target_key"
            ),
        )

    # ============================================================
    # DATABASE HELPERS
    # ============================================================

    def _fetch_all(
        self,
        *,
        table_name: str,
        columns: str,
        order_by: tuple[str, ...],
        active_only: bool,
    ) -> list[dict[str, Any]]:

        rows: list[
            dict[str, Any]
        ] = []

        start = 0

        while True:
            query = (
                self._client
                .table(table_name)
                .select(columns)
            )

            if active_only:
                query = query.eq(
                    "active",
                    True,
                )

            for column in order_by:
                query = query.order(
                    column
                )

            end = (
                start
                + self._read_page_size
                - 1
            )

            response = (
                query
                .range(
                    start,
                    end,
                )
                .execute()
            )

            batch = list(
                response.data or []
            )

            rows.extend(
                batch
            )

            if (
                len(batch)
                < self._read_page_size
            ):
                break

            start += (
                self._read_page_size
            )

        return rows

    def _upsert_batches(
        self,
        *,
        table_name: str,
        rows: list[
            dict[str, Any]
        ],
        on_conflict: str,
    ) -> None:

        if not rows:
            return

        for start in range(
            0,
            len(rows),
            self._write_batch_size,
        ):
            batch = rows[
                start:
                start
                + self._write_batch_size
            ]

            (
                self._client
                .table(table_name)
                .upsert(
                    batch,
                    on_conflict=on_conflict,
                )
                .execute()
            )

    # ============================================================
    # ROW MAPPING
    # ============================================================

    @staticmethod
    def _node_from_row(
        row: dict[str, Any],
    ) -> GraphNode:

        return GraphNode(
            node_key=str(
                row["node_key"]
            ),
            node_type=str(
                row["node_type"]
            ),
            entity_id=str(
                row["entity_id"]
            ),
            label=str(
                row["label"]
            ),
            metadata=dict(
                row.get("metadata")
                or {}
            ),
            active=bool(
                row.get(
                    "active",
                    True,
                )
            ),
        )

    @staticmethod
    def _edge_from_row(
        row: dict[str, Any],
    ) -> GraphEdge:

        return GraphEdge(
            source_key=str(
                row["source_key"]
            ),
            relation_type=str(
                row["relation_type"]
            ),
            target_key=str(
                row["target_key"]
            ),
            metadata=dict(
                row.get("metadata")
                or {}
            ),
            active=bool(
                row.get(
                    "active",
                    True,
                )
            ),
        )
