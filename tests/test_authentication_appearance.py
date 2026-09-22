from modules.authentication.ui import (
    authentication_login_ui,
)
from ui import app_shell_ui


def test_login_contains_institutional_visual_structure():
    html = authentication_login_ui().render()["html"]

    assert "jep_icon.png" in html
    assert "JEP-IA" in html
    assert "appmemoria" in html
    assert "Memoria y panorama de investigación" in html
    assert "Correo institucional" in html
    assert "auth_login" in html
    assert "JURISDICCIÓN ESPECIAL PARA LA PAZ" in html


def test_application_shell_contains_authenticated_actor():
    html = app_shell_ui().render()["html"]

    assert "auth_actor_summary" in html
    assert "auth-nav-control" in html
