from auth.models import AppActor
from auth.session import AuthSessionState
from server import root_ui_for_auth_state


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
