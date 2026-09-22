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
        ui.card(
            ui.card_header("Usuarios"),
            ui.p(
                (
                    "La consulta del directorio organizacional "
                    "se integrará en este módulo."
                ),
                class_="text-muted p-3",
            ),
        ),
        class_="p-3",
    )
