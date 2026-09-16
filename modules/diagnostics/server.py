from shiny import Inputs, Outputs, Session, module, render

from core.dependencies import AppDependencies
from services.diagnostics_service import DiagnosticsService


@module.server
def diagnostics_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    dependencies: AppDependencies,
):
    service = DiagnosticsService(dependencies)

    @render.code
    def dependency_status() -> str:
        status = service.get_dependency_status()
        return "\n".join(
            (
                "Estado inicial de dependencias",
                "",
                f"EpisodeRepository: {status.episode_repository}",
                f"ResearchActivitySource: {status.research_activity_source}",
                f"VectorStore: {status.vector_store}",
                f"LLMProvider: {status.llm_provider}",
                f"EmbeddingProvider: {status.embedding_provider}",
            )
        )
