from __future__ import annotations

from shiny import (
    Inputs,
    Outputs,
    Session,
    reactive,
    render,
    ui,
)

from core.dependencies import AppDependencies
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


def create_server(
    dependencies: AppDependencies,
):
    def server(
        input: Inputs,
        output: Outputs,
        session: Session,
    ) -> None:
        episodic_service = EpisodicService(
            dependencies
        )

        @reactive.effect
        def _load_episodic_projects() -> None:
            projects = (
                episodic_service.list_projects()
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

        @render.text
        def global_memory_status() -> str:
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
        )

        episodic_server(
            "episodic",
            dependencies,
            project_id=lambda: (
                input.project_id()
            ),
        )

        diagnostics_server(
            "diagnostics",
            dependencies,
        )

    return server
