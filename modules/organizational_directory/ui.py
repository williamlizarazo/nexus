from __future__ import annotations

from shiny import module, ui


@module.ui
def organizational_directory_ui():
    return ui.div(
        ui.h2(
            "Directorio organizacional",
            class_="mb-1",
        ),
        ui.p(
            (
                "Administración de usuarios y pertenencias "
                "a Magistraturas y Direcciones."
            ),
            class_="text-muted mb-3",
        ),
        ui.div(
            ui.input_text(
                "directory_search",
                None,
                placeholder=(
                    "Buscar por nombre, correo, rol o "
                    "Magistratura/Dirección..."
                ),
            ),
            class_="mb-3",
        ),
        ui.output_text(
            "directory_status"
        ),
        ui.card(
            ui.card_header("Usuarios"),
            ui.output_ui(
                "directory_table"
            ),
        ),
        class_="p-3",
    )
