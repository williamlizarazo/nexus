from __future__ import annotations

from shiny import (
    Inputs,
    Outputs,
    Session,
    reactive,
    render,
    req,
    ui,
)

from auth.session import (
    AuthSessionState,
)
from core.dependencies import (
    AppDependencies,
)
from modules.authentication.server import (
    authentication_server,
)
from modules.diagnostics.server import (
    diagnostics_server,
)
from modules.episodic.server import (
    episodic_server,
)
from modules.research_dashboard.server import (
    research_dashboard_server,
)
from presenters.episodic_presenter import (
    project_choices,
)
from services.episodic_service import (
    EpisodicService,
)
from ui import app_root_ui


def root_ui_for_auth_state(
    state: AuthSessionState,
):
    return app_root_ui(
        is_authenticated=(
            state.is_authenticated
        )
    )


def create_server(
    dependencies: AppDependencies,
):
    def server(
        input: Inputs,
        output: Outputs,
        session: Session,
    ) -> None:

        auth_state = authentication_server(
            input,
            output,
            session,
            dependencies=dependencies,
        )

        def _is_authenticated() -> bool:
            return (
                auth_state.get()
                .is_authenticated
            )

        @output
        @render.ui
        def app_root():
            return root_ui_for_auth_state(
                auth_state.get()
            )

        episodic_service = EpisodicService(
            dependencies
        )

        @reactive.effect
        def _load_episodic_projects():
            req(
                _is_authenticated()
            )

            projects = (
                episodic_service
                .list_projects()
            )

            choices = project_choices(
                projects
            )

            selected = (
                projects[0].project_id
                if projects
                else ""
            )

            ui.update_select(
                "project_id",
                choices=choices,
                selected=selected,
                session=session,
            )

        @output
        @render.text
        def global_memory_status() -> str:
            req(
                _is_authenticated()
            )

            error = (
                dependencies
                .memory_runtime_error
            )

            if error:
                return (
                    "Memoria no disponible: "
                    f"{error}"
                )

            if not (
                dependencies
                .episode_repository
            ):
                return (
                    "Repositorio episódico "
                    "no disponible."
                )

            return "Memoria conectada."

        research_dashboard_server(
            input,
            output,
            session,
            dependencies,
            is_authenticated=(
                _is_authenticated
            ),
        )

        episodic_server(
            "episodic",
            dependencies,
            project_id=lambda: (
                input.project_id()
            ),
            is_authenticated=(
                _is_authenticated
            ),
        )

        diagnostics_server(
            "diagnostics",
            dependencies,
            is_authenticated=(
                _is_authenticated
            ),
        )

    return server
