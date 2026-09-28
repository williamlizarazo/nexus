from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from memory_core.domain.nexus_graph import (
    GraphEdge,
    GraphNode,
)


@runtime_checkable
class GraphProjectionRepository(Protocol):
    """
    Puerto agnóstico para persistir y recuperar la proyección NEXUS.

    El dominio no conoce Supabase, PostgreSQL ni NetworkX.
    """

    def list_nodes(
        self,
        *,
        active_only: bool = True,
    ) -> list[GraphNode]:
        ...

    def list_edges(
        self,
        *,
        active_only: bool = True,
    ) -> list[GraphEdge]:
        ...

    def upsert_nodes(
        self,
        nodes: Sequence[GraphNode],
    ) -> None:
        ...

    def upsert_edges(
        self,
        edges: Sequence[GraphEdge],
    ) -> None:
        ...
