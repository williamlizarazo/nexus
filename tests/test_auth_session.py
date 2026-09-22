from auth.models import AppActor
from auth.session import AuthSessionState


def test_new_session_is_not_authenticated():
    state = AuthSessionState()

    assert state.is_authenticated is False
    assert state.actor is None
    assert state.error_message is None


def test_authenticated_session_contains_actor():
    actor = AppActor(
        user_id="user-001",
        email="admin@example.org",
        role="admin",
    )

    state = AuthSessionState.authenticated(actor)

    assert state.is_authenticated is True
    assert state.actor == actor
    assert state.error_message is None


def test_failed_session_contains_safe_message():
    state = AuthSessionState.failed(
        "Acceso no autorizado."
    )

    assert state.is_authenticated is False
    assert state.actor is None
    assert state.error_message == "Acceso no autorizado."


def test_logout_returns_clean_state():
    actor = AppActor(
        user_id="user-001",
        email="admin@example.org",
        role="admin",
    )

    state = (
        AuthSessionState
        .authenticated(actor)
        .logout()
    )

    assert state == AuthSessionState()
