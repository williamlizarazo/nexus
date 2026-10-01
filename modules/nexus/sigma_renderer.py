from __future__ import annotations

import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import networkx as nx
from ipysigma import Sigma


NODE_COLOR_PALETTE = {
    "user": "#2563eb",
    "project": "#7c3aed",
    "document": "#16a34a",
    "page": "#f59e0b",
    "organizational_unit": "#dc2626",
    "unknown": "#6b7280",
}


NODE_BASE_SIZE = {
    "user": 12.0,
    "organizational_unit": 11.0,
    "project": 8.0,
    "document": 7.0,
    "page": 5.5,
    "unknown": 6.0,
}


NODE_LABEL_SIZE = {
    "user": 14.0,
    "organizational_unit": 13.0,
    "project": 11.0,
    "document": 10.0,
    "page": 9.0,
    "unknown": 9.0,
}


RELATION_LABELS = {
    "WORKS_ON": "trabaja en",
    "BELONGS_TO": "pertenece a",
    "USES": "usa",
    "CONTAINS": "contiene",
}


LAYOUT_SETTINGS = {
    "structural": {
        "adjustSizes": True,
        "barnesHutOptimize": True,
        "barnesHutTheta": 0.5,
        "edgeWeightInfluence": 0.3,
        "gravity": 0.35,
        "linLogMode": False,
        "outboundAttractionDistribution": True,
        "scalingRatio": 8.0,
        "slowDown": 1.2,
        "strongGravityMode": False,
    },
    "users": {
        "adjustSizes": True,
        "barnesHutOptimize": True,
        "gravity": 0.4,
        "linLogMode": True,
        "scalingRatio": 10.0,
        "slowDown": 1.0,
    },
    "projects": {
        "adjustSizes": True,
        "barnesHutOptimize": True,
        "gravity": 0.6,
        "linLogMode": True,
        "scalingRatio": 7.0,
        "slowDown": 1.2,
    },
    "units": {
        "adjustSizes": True,
        "barnesHutOptimize": True,
        "gravity": 0.5,
        "linLogMode": True,
        "scalingRatio": 10.0,
        "slowDown": 1.0,
    },
}


START_LAYOUT_SECONDS = {
    "structural": 8,
    "users": 4,
    "projects": 8,
    "units": 4,
}


def _json_safe(
    value: Any,
) -> Any:
    if value is None:
        return None

    if isinstance(
        value,
        (str, int, float, bool),
    ):
        return value

    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }

    if isinstance(
        value,
        (list, tuple, set, frozenset),
    ):
        return [
            _json_safe(item)
            for item in value
        ]

    return str(value)


def _node_type(
    node_id: str,
    attributes: dict[str, Any],
) -> str:
    explicit = attributes.get(
        "node_type"
    )

    if explicit:
        return str(explicit)

    prefix = node_id.split(
        ":",
        1,
    )[0]

    if prefix in NODE_COLOR_PALETTE:
        return prefix

    return "unknown"


def _shared_count(
    attributes: dict[str, Any],
    singular: str,
) -> int:
    direct_key = (
        f"shared_{singular}_count"
    )

    value = attributes.get(
        direct_key
    )

    if isinstance(
        value,
        (int, float),
    ):
        return int(value)

    plural_key = (
        f"shared_{singular}s"
    )

    values = attributes.get(
        plural_key
    )

    if isinstance(
        values,
        (list, tuple, set, frozenset, dict),
    ):
        return len(values)

    return 0


def _projection_relation_label(
    attributes: dict[str, Any],
) -> str:
    labels = []

    definitions = (
        ("user", "usuario", "usuarios"),
        ("project", "proyecto", "proyectos"),
        ("document", "documento", "documentos"),
        ("page", "página", "páginas"),
    )

    for singular, label_one, label_many in definitions:
        count = _shared_count(
            attributes,
            singular,
        )

        if count <= 0:
            continue

        label = (
            label_one
            if count == 1
            else label_many
        )

        labels.append(
            f"{count} {label}"
        )

    return " · ".join(labels)


def _relation_label(
    attributes: dict[str, Any],
    graph_name: str,
) -> tuple[str, str]:
    relation_type = str(
        attributes.get(
            "relation_type",
            ""
        )
    ).strip()

    if relation_type:
        full_label = RELATION_LABELS.get(
            relation_type,
            relation_type,
        )

        # WORKS_ON se repite muchas veces alrededor
        # del usuario y genera ruido visual.
        # Se conserva en el panel de información,
        # pero no se imprime permanentemente.
        visible_label = (
            ""
            if relation_type == "WORKS_ON"
            else full_label
        )

        return (
            full_label,
            visible_label,
        )

    full_label = (
        _projection_relation_label(
            attributes
        )
    )

    # Las proyecciones pueden tener muchas aristas.
    # El detalle queda disponible al seleccionar
    # la relación, pero no se llena el grafo de texto.
    if graph_name != "structural":
        return (
            full_label,
            "",
        )

    return (
        full_label,
        full_label,
    )


def _edge_weight(
    attributes: dict[str, Any],
) -> float:
    for key in (
        "weight",
        "strength",
        "score",
    ):
        value = attributes.get(
            key
        )

        if isinstance(
            value,
            (int, float),
        ):
            value = float(value)

            if (
                math.isfinite(value)
                and value > 0
            ):
                return value

    total = 0

    for singular in (
        "user",
        "project",
        "document",
        "page",
    ):
        total += _shared_count(
            attributes,
            singular,
        )

    return float(
        max(
            total,
            1,
        )
    )


def build_sigma_graph(
    payload: dict[str, Any],
    graph_name: str,
) -> nx.Graph:
    if graph_name == "structural":
        graph: nx.Graph = nx.DiGraph()
    else:
        graph = nx.Graph()

    for raw_node in payload.get(
        "nodes",
        [],
    ):
        node_id = str(
            raw_node.get(
                "id",
                "",
            )
        )

        if not node_id:
            continue

        attributes = {
            key: _json_safe(value)
            for key, value
            in raw_node.items()
            if key != "id"
        }

        kind = _node_type(
            node_id,
            attributes,
        )

        attributes["node_type"] = kind

        attributes["label"] = str(
            attributes.get("label")
            or node_id
        )

        graph.add_node(
            node_id,
            **attributes,
        )

    for raw_edge in payload.get(
        "edges",
        [],
    ):
        source = str(
            raw_edge.get(
                "source",
                "",
            )
        )

        target = str(
            raw_edge.get(
                "target",
                "",
            )
        )

        if (
            not source
            or not target
            or source not in graph
            or target not in graph
        ):
            continue

        attributes = {
            key: _json_safe(value)
            for key, value
            in raw_edge.items()
            if key not in {
                "source",
                "target",
                "key",
            }
        }

        (
            full_label,
            visible_label,
        ) = _relation_label(
            attributes,
            graph_name,
        )

        weight = _edge_weight(
            attributes
        )

        attributes[
            "relation_label"
        ] = full_label

        attributes[
            "display_label"
        ] = visible_label

        attributes[
            "sigma_weight"
        ] = weight

        if graph_name == "structural":
            edge_size = 1.1
        else:
            edge_size = min(
                4.0,
                0.8
                + math.log1p(
                    weight
                ),
            )

        attributes[
            "sigma_size"
        ] = edge_size

        graph.add_edge(
            source,
            target,
            **attributes,
        )

    if graph.number_of_nodes() == 0:
        return graph

    centrality = (
        nx.degree_centrality(
            graph
        )
    )

    for node_id, attributes in graph.nodes(
        data=True
    ):
        kind = str(
            attributes.get(
                "node_type",
                "unknown",
            )
        )

        degree = int(
            graph.degree(
                node_id
            )
        )

        degree_centrality = float(
            centrality.get(
                node_id,
                0.0,
            )
        )

        base_size = NODE_BASE_SIZE.get(
            kind,
            NODE_BASE_SIZE["unknown"],
        )

        sigma_size = min(
            30.0,
            base_size
            + 10.0
            * math.sqrt(
                max(
                    degree_centrality,
                    0.0,
                )
            ),
        )

        base_label_size = (
            NODE_LABEL_SIZE.get(
                kind,
                NODE_LABEL_SIZE[
                    "unknown"
                ],
            )
        )

        sigma_label_size = min(
            16.0,
            base_label_size
            + 2.0
            * degree_centrality,
        )

        attributes[
            "degree"
        ] = degree

        attributes[
            "degree_centrality"
        ] = round(
            degree_centrality,
            6,
        )

        attributes[
            "sigma_size"
        ] = round(
            sigma_size,
            2,
        )

        attributes[
            "sigma_label_size"
        ] = round(
            sigma_label_size,
            2,
        )

        attributes[
            "sigma_zindex"
        ] = degree

    return graph


def write_sigma_html(
    payload: dict[str, Any],
    output_path: Path,
    *,
    graph_name: str,
) -> Path:
    graph = build_sigma_graph(
        payload,
        graph_name,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    layout_settings = (
        LAYOUT_SETTINGS.get(
            graph_name,
            LAYOUT_SETTINGS[
                "structural"
            ],
        )
    )

    start_layout = (
        START_LAYOUT_SECONDS.get(
            graph_name,
            6,
        )
    )

    Sigma.write_html(
        graph,
        output_path,
        fullscreen=True,

        background_color="white",

        # -------------------------
        # ForceAtlas2
        # -------------------------
        start_layout=start_layout,
        layout_settings=(
            layout_settings
        ),

        # -------------------------
        # Interacción
        # -------------------------
        clickable_edges=True,
        hide_info_panel=False,
        hide_search=False,
        hide_edges_on_move=False,

        # -------------------------
        # Nodos
        # -------------------------
        node_label="label",

        node_color="node_type",
        node_color_palette=(
            NODE_COLOR_PALETTE
        ),

        raw_node_size=(
            "sigma_size"
        ),

        raw_node_label_size=(
            "sigma_label_size"
        ),

        node_zindex=(
            "sigma_zindex"
        ),

        default_node_label_color=(
            "#111827"
        ),

        # -------------------------
        # Etiquetas
        # -------------------------
        label_font="sans-serif",

        label_density=1,

        label_grid_cell_size=260,

        label_rendered_size_threshold=8,

        show_all_labels=False,

        # -------------------------
        # Aristas
        # -------------------------
        edge_label="display_label",

        raw_edge_size="sigma_size",

        edge_weight="sigma_weight",

        default_edge_color=(
            "#cbd5e1"
        ),

        default_edge_type=(
            "arrow"
            if graph.is_directed()
            else "curve"
        ),

        default_edge_curveness=0.18,
    )

    return output_path
