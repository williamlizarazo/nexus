from __future__ import annotations

from collections.abc import Callable

from shiny import (
    Inputs,
    Outputs,
    Session,
    module,
    render,
)

from core.dependencies import (
    AppDependencies,
)
from services.diagnostics_service import (
    DiagnosticsService,
)


@module.server
def diagnostics_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    dependencies: AppDependencies,
    is_authenticated: Callable[
        [],
        bool,
    ],
):
    service = DiagnosticsService(
        dependencies
    )

    @render.code
    def dependency_status() -> str:
        if not is_authenticated():
            return (
                "Autenticación requerida."
            )

        status = (
            service
            .get_dependency_status()
        )

        return "\n".join(
            (
                "Estado inicial de dependencias",
                "",
                (
                    "EpisodeRepository: "
                    f"{status.episode_repository}"
                ),
                (
                    "ResearchActivitySource: "
                    f"{status.research_activity_source}"
                ),
                (
                    "VectorStore: "
                    f"{status.vector_store}"
                ),
                (
                    "LLMProvider: "
                    f"{status.llm_provider}"
                ),
                (
                    "EmbeddingProvider: "
                    f"{status.embedding_provider}"
                ),
            )
        )
