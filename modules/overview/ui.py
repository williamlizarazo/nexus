from shiny import module, ui


@module.ui
def overview_ui():
    return ui.div(
        ui.h2("Visión general"),
        ui.p(
            "Estado general del sistema de memoria investigativa.",
            class_="text-muted",
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Sistema de memoria"),
                ui.p("Punto de entrada para observar las memorias del proyecto."),
            ),
            ui.card(
                ui.card_header("Memorias"),
                ui.p("La memoria episódica será el primer módulo conectado."),
            ),
            ui.card(
                ui.card_header("Estado"),
                ui.output_text("runtime_state"),
            ),
            col_widths=(4, 4, 4),
        ),
        class_="memory-page",
    )
