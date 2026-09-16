from shiny import module, ui


@module.ui
def diagnostics_ui():
    return ui.div(
        ui.h2("Diagnóstico"),
        ui.p(
            "Estado técnico de los componentes del sistema de memoria.",
            class_="text-muted",
        ),
        ui.card(
            ui.card_header("Dependencias"),
            ui.output_code("dependency_status"),
        ),
        class_="memory-page",
    )
