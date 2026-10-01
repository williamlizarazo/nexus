from pathlib import Path

from ipysigma import Sigma

from modules.nexus.sigma_renderer import (
    build_sigma_graph,
    write_sigma_html,
)


STRUCTURAL_PAYLOAD = {
    "nodes": [
        {
            "id": "user:u1",
            "label": "Usuario Uno",
            "node_type": "user",
        },
        {
            "id": "project:p1",
            "label": "Proyecto Uno",
            "node_type": "project",
        },
        {
            "id": "document:d1",
            "label": "Documento 1",
            "node_type": "document",
        },
        {
            "id": "page:d1:0",
            "label": "Página 1",
            "node_type": "page",
        },
    ],
    "edges": [
        {
            "source": "user:u1",
            "target": "project:p1",
            "relation_type": "WORKS_ON",
        },
        {
            "source": "project:p1",
            "target": "document:d1",
            "relation_type": "USES",
        },
        {
            "source": "document:d1",
            "target": "page:d1:0",
            "relation_type": "CONTAINS",
        },
    ],
}


PROJECT_PAYLOAD = {
    "nodes": [
        {
            "id": "project:p1",
            "label": "Proyecto 1",
            "node_type": "project",
        },
        {
            "id": "project:p2",
            "label": "Proyecto 2",
            "node_type": "project",
        },
    ],
    "edges": [
        {
            "source": "project:p1",
            "target": "project:p2",
            "shared_user_count": 1,
            "shared_document_count": 2,
            "shared_page_count": 3,
        },
    ],
}


def test_structural_sigma_graph_is_directed():
    graph = build_sigma_graph(
        STRUCTURAL_PAYLOAD,
        "structural",
    )

    assert graph.is_directed()

    assert graph.number_of_nodes() == 4
    assert graph.number_of_edges() == 3

    assert (
        graph.nodes[
            "user:u1"
        ]["node_type"]
        == "user"
    )

    assert (
        graph.nodes[
            "user:u1"
        ]["sigma_size"]
        > 0
    )


def test_structural_relation_labels_are_human_readable():
    graph = build_sigma_graph(
        STRUCTURAL_PAYLOAD,
        "structural",
    )

    works_on = graph.edges[
        "user:u1",
        "project:p1",
    ]

    assert (
        works_on[
            "relation_label"
        ]
        == "trabaja en"
    )

    # Se oculta visualmente para evitar
    # decenas de textos repetidos.
    assert (
        works_on[
            "display_label"
        ]
        == ""
    )

    uses = graph.edges[
        "project:p1",
        "document:d1",
    ]

    assert (
        uses[
            "display_label"
        ]
        == "usa"
    )


def test_project_projection_is_undirected():
    graph = build_sigma_graph(
        PROJECT_PAYLOAD,
        "projects",
    )

    assert not graph.is_directed()

    assert graph.number_of_nodes() == 2
    assert graph.number_of_edges() == 1


def test_projection_keeps_shared_evidence_label():
    graph = build_sigma_graph(
        PROJECT_PAYLOAD,
        "projects",
    )

    edge = graph.edges[
        "project:p1",
        "project:p2",
    ]

    label = edge[
        "relation_label"
    ]

    assert "1 usuario" in label
    assert "2 documentos" in label
    assert "3 páginas" in label

    # No llenar una red densa de etiquetas.
    assert (
        edge[
            "display_label"
        ]
        == ""
    )


def test_sigma_html_configuration(
    monkeypatch,
    tmp_path,
):
    captured = {}

    def fake_write_html(
        graph,
        path,
        **kwargs,
    ):
        captured[
            "graph"
        ] = graph

        captured[
            "path"
        ] = path

        captured[
            "kwargs"
        ] = kwargs

        Path(path).write_text(
            "<html></html>",
            encoding="utf-8",
        )

    monkeypatch.setattr(
        Sigma,
        "write_html",
        fake_write_html,
    )

    output = (
        tmp_path
        / "nexus.html"
    )

    result = write_sigma_html(
        STRUCTURAL_PAYLOAD,
        output,
        graph_name="structural",
    )

    assert result == output
    assert output.exists()

    kwargs = captured[
        "kwargs"
    ]

    assert (
        kwargs[
            "show_all_labels"
        ]
        is False
    )

    assert (
        kwargs[
            "clickable_edges"
        ]
        is True
    )

    assert (
        kwargs[
            "hide_search"
        ]
        is False
    )

    assert (
        kwargs[
            "hide_info_panel"
        ]
        is False
    )

    assert (
        kwargs[
            "default_edge_type"
        ]
        == "arrow"
    )

    assert (
        kwargs[
            "layout_settings"
        ][
            "adjustSizes"
        ]
        is True
    )
