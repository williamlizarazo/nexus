from auth.models import AppActor
from auth.session import AuthSessionState
from server import (
    organizational_directory_is_active,
    root_ui_for_auth_state,
)


def test_root_ui_for_empty_session_returns_login():
    component = root_ui_for_auth_state(
        AuthSessionState()
    )

    html = str(component)

    assert "auth_login" in html
    assert "research_dashboard" not in html


def test_root_ui_for_authenticated_session_returns_app():
    actor = AppActor(
        user_id="user-001",
        email="admin@example.org",
        role="admin",
    )

    component = root_ui_for_auth_state(
        AuthSessionState.authenticated(actor)
    )

    html = str(component)

    assert "research_dashboard" in html
    assert "episodic" in html
    assert "auth_actor_summary" in html


def test_root_ui_exposes_directory_for_admin_only():
    admin_state = AuthSessionState.authenticated(
        AppActor(
            user_id="admin-001",
            email="admin@example.org",
            role="admin",
        )
    )
    viewer_state = AuthSessionState.authenticated(
        AppActor(
            user_id="viewer-001",
            email="viewer@example.org",
            role="viewer",
        )
    )

    admin_html = str(
        root_ui_for_auth_state(
            admin_state
        )
    )
    viewer_html = str(
        root_ui_for_auth_state(
            viewer_state
        )
    )

    assert "organizational_directory" in admin_html
    assert "organizational_directory" not in viewer_html


def test_directory_is_active_only_for_admin_on_its_tab():
    nav_reads = []

    def selected_directory():
        nav_reads.append("directory")
        return "organizational_directory"

    def selected_dashboard():
        nav_reads.append("dashboard")
        return "research_dashboard"

    def forbidden_nav_read():
        raise AssertionError(
            "La navegación no debe leerse sin autorización."
        )

    admin_state = AuthSessionState.authenticated(
        AppActor(
            user_id="admin-001",
            email="admin@example.org",
            role="admin",
        )
    )
    viewer_state = AuthSessionState.authenticated(
        AppActor(
            user_id="viewer-001",
            email="viewer@example.org",
            role="viewer",
        )
    )

    assert organizational_directory_is_active(
        admin_state,
        selected_directory,
    ) is True
    assert organizational_directory_is_active(
        admin_state,
        selected_dashboard,
    ) is False
    assert organizational_directory_is_active(
        viewer_state,
        forbidden_nav_read,
    ) is False
    assert organizational_directory_is_active(
        AuthSessionState(),
        forbidden_nav_read,
    ) is False
    assert nav_reads == [
        "directory",
        "dashboard",
    ]
