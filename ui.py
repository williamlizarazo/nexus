from pathlib import Path

from shiny import ui

from modules.authentication.ui import (
    authentication_actor_ui,
    authentication_login_ui,
)
from modules.diagnostics.ui import diagnostics_ui
from modules.episodic.ui import episodic_ui
from modules.research_dashboard.ui import (
    research_dashboard_ui,
)


APP_DIR = Path(__file__).resolve().parent


def episodic_sidebar_ui():
    return ui.sidebar(
        ui.h5("Contexto de memoria"),
        ui.input_select(
            "project_id",
            "Proyecto",
            choices={
                "": "Cargando proyectos..."
            },
            selected="",
        ),
        ui.input_select(
            "actor_id",
            "Actor",
            choices={
                "": "Todos",
            },
            selected="",
        ),
        ui.hr(),
        ui.h6("Sistema de memoria"),
        ui.output_text(
            "global_memory_status"
        ),
        open="desktop",
        width=300,
        resizable=True,
    )


def app_shell_ui():
    """
    Shell principal mostrado después
    de autenticar al usuario.
    """

    return ui.page_navbar(
        ui.nav_panel(
            "Panorama de investigación",
            research_dashboard_ui(),
            value="research_dashboard",
        ),

        ui.nav_panel(
            "Memoria episódica",
            ui.layout_sidebar(
                episodic_sidebar_ui(),
                episodic_ui("episodic"),
            ),
            value="episodic",
        ),

        ui.nav_spacer(),

        ui.nav_panel(
            "Diagnóstico",
            diagnostics_ui(
                "diagnostics"
            ),
            value="diagnostics",
        ),

        ui.nav_control(
            authentication_actor_ui()
        ),

        title="appmemoria",
        id="main_nav",
        selected="research_dashboard",
        fillable=True,
    )


def app_root_ui(
    *,
    is_authenticated: bool,
):
    if not is_authenticated:
        return authentication_login_ui()

    return app_shell_ui()


app_ui = ui.div(
    ui.include_css(
        APP_DIR
        / "www"
        / "css"
        / "app.css"
    ),

    ui.output_ui(
        "app_root"
    ),
    id="app-root-host",
)
