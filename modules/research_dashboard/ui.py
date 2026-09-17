from datetime import date, timedelta

from shiny import ui


def default_analysis_period(
    today: date | None = None,
) -> tuple[date, date]:
    """Return the first day of the previous month through today."""

    end = today or date.today()
    first_current_month = end.replace(day=1)
    last_previous_month = first_current_month - timedelta(days=1)
    start = last_previous_month.replace(day=1)

    return start, end


def _metric_card(
    title: str,
    output_id: str,
):
    return ui.card(
        ui.div(
            title,
            class_="rd-metric-title",
        ),
        ui.div(
            ui.output_text(output_id),
            class_="rd-metric-value",
        ),
        class_="rd-metric",
    )


def research_dashboard_ui():
    period_start, period_end = default_analysis_period()

    return ui.div(
        ui.tags.style(
            """
            .rd-dashboard {
                padding: 8px;
            }

            .rd-title {
                margin-bottom: 4px;
            }

            .rd-subtitle {
                color: #667085;
                margin-bottom: 18px;
            }

            .rd-metric {
                min-height: 105px;
            }

            .rd-metric-title {
                font-size: 0.82rem;
                color: #667085;
                text-transform: uppercase;
                letter-spacing: .04em;
            }

            .rd-metric-value {
                font-size: 1.9rem;
                font-weight: 700;
                margin-top: 7px;
            }

            .rd-card-title {
                font-weight: 650;
            }

            .rd-filter-help {
                color: #667085;
                font-size: 0.82rem;
                margin-bottom: 12px;
            }

            .rd-apply-button {
                width: 100%;
                margin-top: 8px;
            }
            """
        ),
        ui.div(
            ui.h2(
                "Panorama de investigación",
                class_="rd-title",
            ),
            ui.p(
                "Actividad investigativa observable "
                "por usuario, proyecto y evidencia.",
                class_="rd-subtitle",
            ),
            ui.layout_sidebar(
                ui.sidebar(
                    ui.h5("Contexto de análisis"),
                    ui.p(
                        "Configura el contexto y pulsa Aplicar filtros.",
                        class_="rd-filter-help",
                    ),
                    ui.input_selectize(
                        "rd_users",
                        "Usuarios",
                        choices={},
                        multiple=True,
                        options={
                            "placeholder": "Todos los usuarios",
                        },
                    ),
                    ui.input_selectize(
                        "rd_projects",
                        "Proyectos",
                        choices={},
                        multiple=True,
                        options={
                            "placeholder": "Todos los proyectos",
                        },
                    ),
                    ui.input_date_range(
                        "rd_period",
                        "Periodo",
                        start=period_start,
                        end=period_end,
                    ),
                    ui.input_selectize(
                        "rd_activity_types",
                        "Actividad",
                        choices={
                            "search": "Preguntas / búsquedas",
                            "annotation": "Anotaciones",
                            "activity": "Actividades",
                        },
                        selected=[
                            "search",
                            "annotation",
                            "activity",
                        ],
                        multiple=True,
                    ),
                    ui.input_action_button(
                        "rd_apply_filters",
                        "Aplicar filtros",
                        class_="btn-primary rd-apply-button",
                    ),
                    width=300,
                ),
                ui.div(
                    ui.layout_columns(
                        _metric_card("Usuarios", "rd_kpi_users"),
                        _metric_card("Proyectos", "rd_kpi_projects"),
                        _metric_card("Preguntas", "rd_kpi_questions"),
                        _metric_card("Anotaciones", "rd_kpi_annotations"),
                        _metric_card("Actividades", "rd_kpi_activities"),
                        _metric_card("Eventos", "rd_kpi_events"),
                        col_widths=(2, 2, 2, 2, 2, 2),
                    ),
                    ui.card(
                        ui.card_header("Actividad en el tiempo"),
                        ui.output_data_frame("rd_timeline"),
                    ),
                    ui.layout_columns(
                        ui.card(
                            ui.card_header("Comparación por usuario"),
                            ui.output_data_frame("rd_users_comparison"),
                        ),
                        ui.card(
                            ui.card_header("Comparación por proyecto"),
                            ui.output_data_frame("rd_projects_comparison"),
                        ),
                        col_widths=(6, 6),
                    ),
                    ui.card(
                        ui.card_header("Preguntas y búsquedas"),
                        ui.output_data_frame("rd_questions"),
                    ),
                    ui.card(
                        ui.card_header("Anotaciones"),
                        ui.output_data_frame("rd_annotations"),
                    ),
                    ui.card(
                        ui.card_header(
                            ui.div(
                                ui.div(
                                    "Recorrido investigativo",
                                    class_="rd-card-title",
                                ),
                                ui.div(
                                    "Usuario → Proyecto → Pregunta → "
                                    "Documento → Página",
                                ),
                            )
                        ),
                        ui.output_data_frame("rd_evidence_paths"),
                    ),
                ),
            ),
            class_="rd-dashboard",
        ),
    )
