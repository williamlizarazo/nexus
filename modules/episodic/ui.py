from shiny import module, ui


@module.ui
def episodic_ui():
    return ui.div(
        ui.h2("Memoria episódica"),
        ui.p(
            (
                "Exploración, auditoría y "
                "análisis de trayectorias "
                "investigativas."
            ),
            class_="text-muted",
        ),

        ui.card(
            ui.card_header(
                "Estado del módulo"
            ),
            ui.output_text(
                "module_status"
            ),
        ),

        ui.card(
            ui.card_header(
                "Episodio"
            ),
            ui.input_select(
                "episode_id",
                "Seleccionar episodio",
                choices={
                    "":
                    "Selecciona un proyecto..."
                },
                selected="",
            ),
        ),

        ui.output_ui(
            "episode_summary"
        ),

        ui.card(
            ui.card_header(
                "Actividad investigativa"
            ),
            ui.output_ui(
                "items_table"
            ),
        ),

        ui.card(
            ui.card_header(
                "Relaciones del episodio"
            ),
            ui.output_ui(
                "edges_table"
            ),
        ),

        ui.card(
            ui.card_header(
                "Timeline"
            ),
            ui.output_ui(
                "timeline"
            ),
        ),

        class_="memory-page",
    )
