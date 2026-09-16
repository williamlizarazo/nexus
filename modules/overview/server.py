from shiny import Inputs, Outputs, Session, module, render

from core.dependencies import AppDependencies
from services.overview_service import OverviewService


@module.server
def overview_server(
    input: Inputs,
    output: Outputs,
    session: Session,
    dependencies: AppDependencies,
):
    service = OverviewService(dependencies)

    @render.text
    def runtime_state() -> str:
        return service.get_status().message
