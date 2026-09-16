from pathlib import Path

from shiny import ui

from modules.diagnostics.ui import diagnostics_ui
from modules.episodic.ui import episodic_ui
from modules.overview.ui import overview_ui


APP_DIR = Path(__file__).resolve().parent


global_sidebar = ui.sidebar(
    ui.h5("Contexto global"),
    ui.input_select(
        "project_id",
        "Proyecto",
        choices={"": "Sin conectar"},
        selected="",
    ),
    ui.input_select(
        "actor_id",
        "Actor",
        choices={"": "Todos"},
        selected="",
    ),
    ui.hr(),
    ui.h6("Sistema de memoria"),
    ui.p("Fase 5 · appmemoria", class_="text-muted"),
    ui.p("Infraestructura todavía no conectada.", class_="small text-muted"),
    open="desktop",
    width=300,
    resizable=True,
)


app_ui = ui.page_navbar(
    ui.nav_panel(
        "Visión general",
        overview_ui("overview"),
        value="overview",
    ),
    ui.nav_panel(
        "Memoria episódica",
        episodic_ui("episodic"),
        value="episodic",
    ),
    ui.nav_spacer(),
    ui.nav_panel(
        "Diagnóstico",
        diagnostics_ui("diagnostics"),
        value="diagnostics",
    ),
    title="appmemoria",
    id="main_nav",
    sidebar=global_sidebar,
    fillable=True,
    header=ui.include_css(APP_DIR / "www" / "css" / "app.css"),
)
