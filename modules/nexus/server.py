from __future__ import annotations

import logging
import shutil
from collections.abc import Callable
from datetime import date, datetime
from pathlib import Path
from uuid import uuid4

import pandas as pd

from shiny import (
    Inputs,
    Outputs,
    Session,
    module,
    reactive,
    render,
    ui,
)

from modules.nexus.sigma_renderer import (
    write_sigma_html,
)
from core.dependencies import (
    AppDependencies,
)
from presenters.nexus_presenter import (
    NexusPresenter,
)
from services.nexus_service import (
    NexusService,
)


logger = logging.getLogger(__name__)


NETWORK_LABELS = {
    "structural": "Estructural",
    "users": "Usuarios",
    "projects": "Proyectos",
    "units": "Unidades",
}


@module.server
def nexus_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    dependencies: AppDependencies,
    *,
    is_authenticated: Callable[
        [],
        bool,
    ],
):
    service = NexusService(
        dependencies
    )

    sigma_session_id = uuid4().hex

    sigma_output_dir = (
        Path("www")
        / "nexus_runtime"
        / sigma_session_id
    )

    def cleanup_sigma_files() -> None:
        shutil.rmtree(
            sigma_output_dir,
            ignore_errors=True,
        )

    session.on_ended(
        cleanup_sigma_files
    )

    analysis = reactive.value(
        None
    )

    error_message = reactive.value(
        None
    )

    updated_at = reactive.value(
        None
    )

    @reactive.effect
    def _reset_when_logged_out():
        if is_authenticated():
            return

        analysis.set(None)
        error_message.set(None)
        updated_at.set(None)

    @reactive.effect
    @reactive.event(
        input.refresh
    )
    def _refresh_analysis():
        if not is_authenticated():
            return

        if not service.source_available:
            analysis.set(None)
            error_message.set(
                "La fuente NEXUS no está disponible."
            )
            return

        try:
            result = service.build_analysis(
                reference_date=date.today()
            )

        except Exception:
            logger.exception(
                "NEXUS analysis refresh failed."
            )

            analysis.set(None)
            error_message.set(
                (
                    "No fue posible actualizar "
                    "el análisis NEXUS."
                )
            )
            return

        analysis.set(
            result
        )

        error_message.set(
            None
        )

        updated_at.set(
            datetime.now()
        )

    @reactive.calc
    def presenter():
        result = analysis.get()

        if result is None:
            return None

        return NexusPresenter(
            result
        )

    @reactive.calc
    def selected_network() -> str:
        value = (
            input.network()
            or "structural"
        )

        if value not in NETWORK_LABELS:
            return "structural"

        return value

    @reactive.calc
    def current_kpis():
        current = presenter()

        if current is None:
            return {
                "nodes": 0,
                "edges": 0,
                "components": 0,
                "isolates": 0,
                "density": 0.0,
            }

        return current.network_kpis(
            selected_network()
        )

    @render.text
    def kpi_nodes():
        return str(
            current_kpis()["nodes"]
        )

    @render.text
    def kpi_edges():
        return str(
            current_kpis()["edges"]
        )

    @render.text
    def kpi_components():
        return str(
            current_kpis()[
                "components"
            ]
        )

    @render.text
    def kpi_isolates():
        return str(
            current_kpis()[
                "isolates"
            ]
        )

    @render.text
    def status():
        error = error_message.get()

        if error:
            return error

        if analysis.get() is None:
            return (
                "Presione «Actualizar análisis» "
                "para cargar NEXUS."
            )

        timestamp = updated_at.get()

        network_label = (
            NETWORK_LABELS[
                selected_network()
            ]
        )

        if timestamp is None:
            return (
                f"Red: {network_label}"
            )

        return (
            f"Red: {network_label} · "
            "Última actualización: "
            f"{timestamp:%H:%M:%S}"
        )

    @render.ui
    def graph():
        current = presenter()

        if current is None:
            return ui.div(
                ui.p(
                    (
                        "El gráfico aparecerá aquí "
                        "después de actualizar "
                        "el análisis."
                    ),
                    class_="text-muted mb-0",
                ),
                class_="nexus-empty-graph",
            )

        graph_name = (
            selected_network()
        )

        payload = (
            current.graph_payload(
                graph_name
            )
        )

        if not payload.get(
            "nodes"
        ):
            return ui.div(
                ui.p(
                    (
                        "La red seleccionada "
                        "no contiene nodos."
                    ),
                    class_="text-muted mb-0",
                ),
                class_="nexus-empty-graph",
            )

        output_path = (
            sigma_output_dir
            / f"{graph_name}.html"
        )

        write_sigma_html(
            payload,
            output_path,
            graph_name=graph_name,
        )

        timestamp = updated_at()

        revision = (
            int(
                timestamp.timestamp()
            )
            if timestamp is not None
            else 0
        )

        src = (
            "nexus_runtime/"
            f"{sigma_session_id}/"
            f"{graph_name}.html"
            f"?v={revision}"
        )

        return ui.tags.iframe(
            src=src,
            class_="nexus-sigma-frame",
        )

    @render.data_frame
    def centrality():
        current = presenter()

        if current is None:
            frame = pd.DataFrame(
                columns=[
                    "Nodo",
                    "Etiqueta",
                    "Centralidad de grado",
                    "Intermediación",
                ]
            )

        else:
            rows = current.centrality_rows(
                selected_network()
            )

            frame = pd.DataFrame(
                [
                    {
                        "Nodo": row["node"],
                        "Etiqueta": row["label"],
                        "Centralidad de grado": (
                            row[
                                "degree_centrality"
                            ]
                        ),
                        "Intermediación": (
                            row[
                                "betweenness_centrality"
                            ]
                        ),
                    }
                    for row in rows
                ]
            )

        return render.DataGrid(
            frame,
            filters=True,
            width="100%",
            height="360px",
        )
