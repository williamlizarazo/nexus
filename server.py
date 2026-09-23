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
from modules.organizational_directory.server import (
    organizational_directory_server,
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
    actor = state.actor

    return app_root_ui(
        is_authenticated=state.is_authenticated,
        is_admin=bool(
            actor and actor.is_admin
        ),
    )


def organizational_directory_is_active(
    state: AuthSessionState,
    selected_nav: Callable[
        [],
        str | None,
    ],
) -> bool:
    actor = state.actor

    if (
        not state.is_authenticated
        or actor is None
        or not actor.is_admin
    ):
        return False

    return (
        selected_nav()
        == "organizational_directory"
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

        def _is_admin() -> bool:
            actor = auth_state.get().actor

            return bool(
                actor
                and actor.is_admin
            )

        def _organizational_directory_is_active(
        ) -> bool:
            return organizational_directory_is_active(
                auth_state.get(),
                input.main_nav,
            )

        organizational_directory_server(
            "organizational_directory",
            dependencies,
            is_authenticated=(
                _is_authenticated
            ),
            is_admin=_is_admin,
            is_active=(
                _organizational_directory_is_active
            ),
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
