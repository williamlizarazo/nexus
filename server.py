from __future__ import annotations

from shiny import Inputs, Outputs, Session

from core.dependencies import AppDependencies
from modules.diagnostics.server import diagnostics_server
from modules.episodic.server import episodic_server
from modules.overview.server import overview_server


def create_server(dependencies: AppDependencies):
    def server(input: Inputs, output: Outputs, session: Session) -> None:
        overview_server("overview", dependencies)
        episodic_server("episodic", dependencies)
        diagnostics_server("diagnostics", dependencies)

    return server
