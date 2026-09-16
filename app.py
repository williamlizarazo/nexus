from shiny import App

from core.config import load_config
from core.dependencies import build_dependencies
from server import create_server
from ui import app_ui


config = load_config()
dependencies = build_dependencies(config)
server = create_server(dependencies)

app = App(app_ui, server)

# .\.venv\Scripts\Activate.ps1
# shiny run app.py
