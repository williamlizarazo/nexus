from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from shiny import (
    Inputs,
    Outputs,
    Session,
    module,
    reactive,
    render,
    ui,
)

from core.dependencies import (
    AppDependencies,
)
from presenters.episodic_presenter import (
    episode_choices,
    format_datetime,
    format_score,
)
from services.episodic_service import (
    EpisodicService,
)


def _empty_state(
    message: str,
):
    return ui.p(
        message,
        class_="text-muted mb-0",
    )


def _table(
    headers: list[str],
    rows: list[list[Any]],
):
    if not rows:
        return _empty_state(
            "No hay información disponible."
        )

    return ui.div(
        ui.tags.table(
            ui.tags.thead(
                ui.tags.tr(
                    *[
                        ui.tags.th(header)
                        for header in headers
                    ]
                )
            ),
            ui.tags.tbody(
                *[
                    ui.tags.tr(
                        *[
                            ui.tags.td(
                                str(cell)
                            )
                            for cell in row
                        ]
                    )
                    for row in rows
                ]
            ),
            class_=(
                "table table-sm "
                "table-hover "
                "memory-table"
            ),
        ),
        class_="table-responsive",
    )


@module.server
def episodic_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    dependencies: AppDependencies,
    project_id: Callable[[], str],
):
    service = EpisodicService(
        dependencies
    )

    @reactive.calc
    def selected_project_id() -> str:
        return (
            project_id() or ""
        ).strip()

    @reactive.calc
    def episodes():
        value = selected_project_id()

        if not value:
            return []

        return service.list_episodes(
            value
        )

    @reactive.effect
    def _sync_episode_selector():
        available = episodes()

        choices = episode_choices(
            available
        )

        selected = (
            available[0].episode_id
            if available
            else ""
        )

        ui.update_select(
            "episode_id",
            choices=choices,
            selected=selected,
            session=session,
        )

    @reactive.calc
    def detail():
        episode_id = (
            input.episode_id()
            or ""
        ).strip()

        if not episode_id:
            return None

        return service.get_episode_detail(
            episode_id
        )

    @render.text
    def module_status() -> str:
        if not service.repository_available:
            return service.status_message()

        project = selected_project_id()

        if not project:
            return (
                "Repositorio disponible. "
                "Selecciona un proyecto."
            )

        return (
            "Repositorio disponible · "
            f"Proyecto {project}"
        )

    @render.ui
    def episode_summary():
        value = detail()

        if value is None:
            return ui.card(
                _empty_state(
                    "Selecciona un episodio."
                )
            )

        summary = value.summary

        return ui.layout_columns(
            ui.value_box(
                "Búsquedas",
                str(
                    summary.search_count
                ),
            ),
            ui.value_box(
                "Items",
                str(
                    summary.item_count
                ),
            ),
            ui.value_box(
                "Relaciones",
                str(
                    summary.edge_count
                ),
            ),
            ui.value_box(
                "Estado",
                summary.status,
            ),
            col_widths=[
                3,
                3,
                3,
                3,
            ],
        )

    @render.ui
    def items_table():
        value = detail()

        if value is None:
            return _empty_state(
                "No hay episodio seleccionado."
            )

        ordered = sorted(
            value.items,
            key=lambda item: (
                item.occurred_at.timestamp()
                if item.occurred_at
                else float("inf")
            ),
        )

        rows = [
            [
                format_datetime(
                    item.occurred_at
                ),
                item.source_type,
                item.source_label,
                item.role or "—",
                item.membership_method,
                format_score(
                    item.membership_score
                ),
            ]
            for item in ordered
        ]

        return _table(
            [
                "Fecha",
                "Tipo",
                "Contenido",
                "Rol",
                "Método",
                "Score",
            ],
            rows,
        )

    @render.ui
    def edges_table():
        value = detail()

        if value is None:
            return _empty_state(
                "No hay episodio seleccionado."
            )

        labels = {
            item.item_id:
            item.source_label
            for item in value.items
        }

        rows = []

        for edge in value.edges:
            evidence = json.dumps(
                edge.evidence or {},
                ensure_ascii=False,
            )

            rows.append(
                [
                    edge.relation_type,
                    format_score(
                        edge.relation_score
                    ),
                    labels.get(
                        edge.source_item_id,
                        edge.source_item_id,
                    ),
                    labels.get(
                        edge.target_item_id,
                        edge.target_item_id,
                    ),
                    evidence,
                ]
            )

        return _table(
            [
                "Relación",
                "Score",
                "Origen",
                "Destino",
                "Evidencia",
            ],
            rows,
        )

    @render.ui
    def timeline():
        value = detail()

        if value is None:
            return _empty_state(
                "No hay episodio seleccionado."
            )

        ordered = sorted(
            value.items,
            key=lambda item: (
                item.occurred_at.timestamp()
                if item.occurred_at
                else float("inf")
            ),
        )

        if not ordered:
            return _empty_state(
                "El episodio no contiene items."
            )

        entries = []

        for item in ordered:
            entries.append(
                ui.tags.li(
                    ui.div(
                        ui.tags.strong(
                            format_datetime(
                                item.occurred_at
                            )
                        ),
                        ui.tags.span(
                            item.source_type,
                            class_=(
                                "memory-type-badge"
                            ),
                        ),
                        class_=(
                            "memory-timeline-head"
                        ),
                    ),
                    ui.div(
                        item.source_label,
                        class_=(
                            "memory-timeline-label"
                        ),
                    ),
                    ui.div(
                        (
                            "Pertenencia: "
                            f"{item.membership_method}"
                        ),
                        class_="text-muted small",
                    ),
                    class_=(
                        "memory-timeline-item"
                    ),
                )
            )

        return ui.tags.ul(
            *entries,
            class_="memory-timeline",
        )
