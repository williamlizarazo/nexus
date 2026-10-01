from modules.nexus.ui import (
    nexus_ui,
)
from ui import app_shell_ui


def test_nexus_module_exposes_controls():
    html = str(
        nexus_ui("nexus")
    )

    assert "NEXUS" in html
    assert "Actualizar análisis" in html
    assert "Estructural" in html
    assert "Usuarios" in html
    assert "Proyectos" in html
    assert "Unidades" in html
    assert "Centralidad" in html


def test_authenticated_shell_exposes_nexus():
    html = str(
        app_shell_ui(
            is_admin=False
        )
    )

    assert "NEXUS" in html
    assert "nexus" in html
