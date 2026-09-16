from shiny import Inputs, Outputs, Session, module, render

from core.dependencies import AppDependencies
from services.episodic_service import EpisodicService


@module.server
def episodic_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    dependencies: AppDependencies,
):
    service = EpisodicService(dependencies)

    @render.text
    def module_status() -> str:
        return service.status_message()
