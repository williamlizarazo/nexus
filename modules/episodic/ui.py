from shiny import module, ui


@module.ui
def episodic_ui():
    return ui.div(
        ui.h2("Memoria episódica"),
        ui.p(
            "Exploración, auditoría y análisis de trayectorias investigativas.",
            class_="text-muted",
        ),
        ui.card(
            ui.card_header("Estado del módulo"),
            ui.output_text("module_status"),
        ),
        ui.card(
            ui.card_header("Próxima integración"),
            ui.p(
                "En la siguiente etapa este módulo consultará episodios, items "
                "y edges a través de los contratos de memory_core."
            ),
        ),
        class_="memory-page",
    )
