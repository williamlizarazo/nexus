from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SUPPORTED_NODE_TYPES = frozenset(
    {
        "organizational_unit",
        "user",
        "project",
        "document",
        "page",
    }
)

SUPPORTED_RELATION_TYPES = frozenset(
    {
        "BELONGS_TO",
        "WORKS_ON",
        "USES",
        "CONTAINS",
    }
)


@dataclass(frozen=True, slots=True)
class GraphNode:
    """
    Representación neutral de un nodo NEXUS.

    No conoce Supabase, PostgreSQL, NetworkX ni nombres de tablas físicas.
    """

    node_key: str
    node_type: str
    entity_id: str
    label: str
    metadata: dict[str, Any] = field(default_factory=dict)
    active: bool = True

    def __post_init__(self) -> None:
        if self.node_type not in SUPPORTED_NODE_TYPES:
            raise ValueError(
                f"Unsupported NEXUS node type: {self.node_type}"
            )


@dataclass(frozen=True, slots=True)
class GraphEdge:
    """
    Representación neutral de una relación estructural NEXUS.
    """

    source_key: str
    relation_type: str
    target_key: str
    metadata: dict[str, Any] = field(default_factory=dict)
    active: bool = True

    def __post_init__(self) -> None:
        if self.relation_type not in SUPPORTED_RELATION_TYPES:
            raise ValueError(
                f"Unsupported NEXUS relation type: {self.relation_type}"
            )

        if self.source_key == self.target_key:
            raise ValueError(
                "NEXUS edge cannot connect a node to itself"
            )


@dataclass(frozen=True, slots=True)
class NexusGraphSnapshot:
    """
    Proyección neutral completa del grafo NEXUS.

    Esta estructura será el límite entre persistencia y herramientas
    posteriores como NetworkX o la visualización PyShiny.
    """

    nodes: tuple[GraphNode, ...] = ()
    edges: tuple[GraphEdge, ...] = ()
