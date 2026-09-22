import server as app_server
from auth.models import AppActor
from auth.session import AuthSessionState
from ui import app_shell_ui


def test_research_dashboard_is_wired_into_app():
    html = app_shell_ui().render()["html"]

    assert "Panorama de investigación" in html
    assert "Memoria episódica" in html
    assert "research_dashboard" in html

    assert callable(app_server.create_server)


def test_research_dashboard_server_is_wired_into_app(
    monkeypatch,
):
    calls = []

    dependencies = object()
    input_ = object()
    output = lambda function: function
    session = object()

    actor = AppActor(
        user_id="user-001",
        email="admin@example.org",
        role="admin",
    )

    state = AuthSessionState.authenticated(
        actor
    )

    class FakeAuthState:
        def get(self):
            return state

    class FakeEpisodicService:
        def __init__(self, dependencies):
            self.dependencies = dependencies

        def list_projects(self):
            return []

    monkeypatch.setattr(
        app_server,
        "authentication_server",
        lambda *args, **kwargs: FakeAuthState(),
    )

    monkeypatch.setattr(
        app_server,
        "EpisodicService",
        FakeEpisodicService,
    )

    monkeypatch.setattr(
        app_server.reactive,
        "effect",
        lambda function: function,
    )

    monkeypatch.setattr(
        app_server.render,
        "text",
        lambda function: function,
    )

    monkeypatch.setattr(
        app_server.render,
        "ui",
        lambda function: function,
    )

    monkeypatch.setattr(
        app_server,
        "research_dashboard_server",
        lambda *args, **kwargs: calls.append(
            (args, kwargs)
        ),
    )

    monkeypatch.setattr(
        app_server,
        "episodic_server",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        app_server,
        "diagnostics_server",
        lambda *args, **kwargs: None,
    )

    app_server.create_server(
        dependencies
    )(
        input_,
        output,
        session,
    )

    assert len(calls) == 1

    args, kwargs = calls[0]

    assert args == (
        input_,
        output,
        session,
        dependencies,
    )

    assert "is_authenticated" in kwargs
    assert callable(
        kwargs["is_authenticated"]
    )

    assert (
        kwargs["is_authenticated"]()
        is True
    )
