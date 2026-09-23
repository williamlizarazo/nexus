from ui import (
    app_root_ui,
    app_shell_ui,
)


def test_root_shows_login_when_not_authenticated():
    component = app_root_ui(
        is_authenticated=False
    )

    html = str(component)

    assert "Correo institucional" in html
    assert "auth_login" in html
    assert "research_dashboard" not in html


def test_root_shows_application_when_authenticated():
    component = app_root_ui(
        is_authenticated=True
    )

    html = str(component)

    assert "research_dashboard" in html
    assert "episodic" in html
    assert "diagnostics" in html
    assert "auth_actor_summary" in html


def test_application_shell_can_be_built():
    component = app_shell_ui()

    assert component is not None


def test_admin_shell_exposes_organizational_directory():
    html = str(
        app_shell_ui(
            is_admin=True
        )
    )

    assert "Directorio organizacional" in html
    assert "organizational_directory" in html
    assert (
        "Administración de usuarios y pertenencias "
        "a Magistraturas y Direcciones."
    ) in html
    assert (
        "organizational_directory-directory_status"
        in html
    )
    assert (
        "organizational_directory-directory_table"
        in html
    )


def test_viewer_shell_hides_organizational_directory():
    html = str(
        app_shell_ui(
            is_admin=False
        )
    )

    assert "Directorio organizacional" not in html
    assert "organizational_directory" not in html
