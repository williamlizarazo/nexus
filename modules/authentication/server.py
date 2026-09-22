from __future__ import annotations

from typing import Any

from shiny import reactive, render, ui

from auth.service import (
    AuthenticationError,
    AuthService,
)
from auth.session import AuthSessionState


def authentication_server(
    input: Any,
    output: Any,
    session: Any,
    *,
    dependencies: Any,
):
    """
    Autenticación y autorización de una sesión PyShiny.

    El estado reactivo se crea dentro de esta función,
    por lo que no se comparte entre usuarios.
    """

    _ = session

    auth_state = reactive.Value(
        AuthSessionState()
    )

    auth_service = None

    if dependencies.auth_provider is not None:
        auth_service = AuthService(
            dependencies.auth_provider
        )

    @reactive.effect
    @reactive.event(input.auth_login)
    def _login():
        email = (
            input.auth_email()
            or ""
        ).strip()

        password = (
            input.auth_password()
            or ""
        )

        if auth_service is None:
            auth_state.set(
                AuthSessionState.failed(
                    dependencies.auth_runtime_error
                    or (
                        "El servicio de autenticación "
                        "no está disponible."
                    )
                )
            )
            return

        try:
            identity = auth_service.login(
                email,
                password,
            )

        except AuthenticationError:
            auth_state.set(
                AuthSessionState.failed(
                    "Correo o contraseña incorrectos."
                )
            )
            return

        authorization_service = (
            dependencies.authorization_service
        )

        if authorization_service is None:
            auth_state.set(
                AuthSessionState.failed(
                    (
                        "El servicio de autorización "
                        "no está disponible."
                    )
                )
            )
            return

        actor = authorization_service.authorize(
            identity
        )

        if actor is None:
            auth_state.set(
                AuthSessionState.failed(
                    (
                        "El usuario está autenticado, "
                        "pero no tiene autorización "
                        "para acceder a appmemoria."
                    )
                )
            )
            return

        auth_state.set(
            AuthSessionState.authenticated(
                actor
            )
        )

    @reactive.effect
    @reactive.event(input.auth_logout)
    def _logout():
        auth_state.set(
            AuthSessionState()
        )

    @output
    @render.ui
    def auth_message():
        state = auth_state.get()

        if not state.error_message:
            return None

        return ui.div(
            state.error_message,
            class_="alert alert-danger py-2",
        )

    @output
    @render.ui
    def auth_actor_summary():
        state = auth_state.get()

        if state.actor is None:
            return None

        actor = state.actor

        role_label = (
            "Administrador"
            if actor.is_admin
            else "Visor"
        )

        return ui.div(
            ui.div(
                ui.strong(
                    actor.email
                ),
                ui.div(
                    role_label,
                    class_="auth-role-label",
                ),
            ),
            ui.input_action_button(
                "auth_logout",
                "Cerrar sesión",
                class_=(
                    "btn-sm "
                    "btn-outline-secondary"
                ),
            ),
            class_="auth-actor-summary",
        )

    return auth_state
