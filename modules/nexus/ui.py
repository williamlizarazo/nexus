from __future__ import annotations

from shiny import module, ui


@module.ui
def nexus_ui():
    return ui.div(
        ui.div(
            ui.h2(
                "NEXUS",
                class_="mb-1",
            ),
            ui.p(
                (
                    "Red analítica de usuarios, proyectos, "
                    "documentos, páginas y unidades "
                    "organizacionales."
                ),
                class_="text-muted mb-0",
            ),
            class_="nexus-heading",
        ),

        ui.div(
            ui.div(
                ui.div(
                    "Nodos",
                    class_="nexus-kpi-label",
                ),
                ui.output_text(
                    "kpi_nodes"
                ),
                class_="nexus-kpi-card",
            ),
            ui.div(
                ui.div(
                    "Relaciones",
                    class_="nexus-kpi-label",
                ),
                ui.output_text(
                    "kpi_edges"
                ),
                class_="nexus-kpi-card",
            ),
            ui.div(
                ui.div(
                    "Componentes",
                    class_="nexus-kpi-label",
                ),
                ui.output_text(
                    "kpi_components"
                ),
                class_="nexus-kpi-card",
            ),
            ui.div(
                ui.div(
                    "Aislados",
                    class_="nexus-kpi-label",
                ),
                ui.output_text(
                    "kpi_isolates"
                ),
                class_="nexus-kpi-card",
            ),
            class_="nexus-kpi-grid",
        ),

        ui.card(
            ui.card_header(
                ui.div(
                    ui.div(
                        ui.input_select(
                            "network",
                            "Red",
                            choices={
                                "structural":
                                    "Estructural",
                                "users":
                                    "Usuarios",
                                "projects":
                                    "Proyectos",
                                "units":
                                    "Unidades",
                            },
                            selected="structural",
                        ),
                        class_="nexus-network-select",
                    ),
                    ui.div(
                        ui.input_action_button(
                            "refresh",
                            "Actualizar análisis",
                            class_=(
                                "btn-primary "
                                "nexus-refresh-button"
                            ),
                        ),
                        class_="nexus-refresh-wrap",
                    ),
                    class_="nexus-toolbar",
                )
            ),

            ui.div(
                ui.output_text(
                    "status"
                ),
                class_="nexus-status",
            ),

            ui.output_ui(
                "graph"
            ),

            full_screen=True,
            class_="nexus-graph-card",
        ),

        ui.card(
            ui.card_header(
                "Centralidad"
            ),
            ui.p(
                (
                    "Indicadores estructurales de los "
                    "nodos de la red seleccionada."
                ),
                class_="text-muted",
            ),
            ui.output_data_frame(
                "centrality"
            ),
            class_="nexus-centrality-card",
        ),

        class_="nexus-shell",
    )
