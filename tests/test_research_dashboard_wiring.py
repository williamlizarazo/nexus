import server as app_server
from ui import app_ui


def test_research_dashboard_is_wired_into_app():
    html = app_ui.render()["html"]

    assert "Panorama de investigación" in html
    assert "Memoria episódica" in html
    assert "research_dashboard" in html

    assert callable(app_server.create_server)


def test_research_dashboard_server_is_wired_into_app(monkeypatch):
    calls = []
    dependencies = object()
    input_ = object()
    output = object()
    session = object()

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
        app_server,
        "research_dashboard_server",
        lambda *args: calls.append(args),
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

    app_server.create_server(dependencies)(
        input_,
        output,
        session,
    )

    assert calls == [
        (
            input_,
            output,
            session,
            dependencies,
        )
    ]
