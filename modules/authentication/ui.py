from __future__ import annotations

from shiny import ui


def authentication_login_ui():
    """
    Interfaz institucional de acceso a appmemoria.

    Esta capa solamente presenta la interfaz.
    No conoce Supabase ni implementa autenticación.
    """

    return ui.div(
        ui.div(
            class_="auth-background-overlay",
        ),

        ui.div(
            ui.div(
                ui.tags.img(
                    src="jep_icon.png",
                    alt="JEP-IA",
                    class_="auth-logo",
                ),

                ui.div(
                    "JEP-IA",
                    class_="auth-brand",
                ),

                ui.h1(
                    "appmemoria",
                    class_="auth-title",
                ),

                ui.p(
                    "Memoria y panorama de investigación",
                    class_="auth-subtitle",
                ),

                class_="auth-heading",
            ),

            ui.div(
                ui.input_text(
                    "auth_email",
                    "Correo institucional",
                    placeholder="usuario@jep.gov.co",
                ),

                ui.input_password(
                    "auth_password",
                    "Contraseña",
                ),

                ui.output_ui(
                    "auth_message",
                ),

                ui.input_action_button(
                    "auth_login",
                    "Ingresar",
                ),

                class_="auth-form",
            ),

            ui.div(
                "Acceso institucional",
                class_="auth-help-text",
            ),

            ui.div(
                ui.div(
                    "JURISDICCIÓN ESPECIAL PARA LA PAZ",
                    class_="auth-footer-title",
                ),
                ui.div(
                    "República de Colombia",
                    class_="auth-footer-subtitle",
                ),
                class_="auth-footer",
            ),

            class_="auth-card",
        ),

        class_="auth-page",
    )


def authentication_actor_ui():
    """
    Información compacta del usuario autenticado
    para la barra principal de navegación.
    """

    return ui.div(
        ui.output_ui(
            "auth_actor_summary",
        ),
        class_="auth-nav-control",
    )
