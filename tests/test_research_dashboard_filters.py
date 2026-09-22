from datetime import date

import modules.research_dashboard.server as dashboard_server
import modules.research_dashboard.ui as dashboard_ui
from shiny.testserver import test_server
from services.research_dashboard_service import (
    DashboardProject,
    DashboardUser,
    ResearchDashboardService,
)


def test_default_analysis_period_uses_previous_month():
    default_analysis_period = getattr(
        dashboard_ui,
        "default_analysis_period",
        None,
    )

    assert default_analysis_period is not None

    start, end = default_analysis_period(
        date(2026, 9, 17)
    )

    assert start == date(2026, 8, 1)
    assert end == date(2026, 9, 17)


def test_default_analysis_period_crosses_year_boundary():
    start, end = dashboard_ui.default_analysis_period(
        date(2026, 1, 15)
    )

    assert start == date(2025, 12, 1)
    assert end == date(2026, 1, 15)


def test_dashboard_has_explicit_apply_filters_button():
    html = dashboard_ui.research_dashboard_ui().render()[
        "html"
    ]

    assert "rd_apply_filters" in html
    assert "Aplicar filtros" in html


def test_snapshot_uses_only_the_applied_filter_context(monkeypatch):
    effects = {}
    calculations = {}

    class FakeValue:
        def __init__(self, value):
            self.value = value

        def get(self):
            return self.value

        def set(self, value):
            self.value = value

    class Inputs:
        users = ("user-a",)
        projects = ("project-a",)
        period = (date(2026, 8, 1), date(2026, 9, 17))
        activity_types = ("search", "annotation", "activity")

        def rd_users(self):
            return self.users

        def rd_projects(self):
            return self.projects

        def rd_period(self):
            return self.period

        def rd_activity_types(self):
            return self.activity_types

        def rd_apply_filters(self):
            return 0

    class Service:
        def __init__(self):
            self.contexts = []

        def list_projects(self, user_ids):
            project_id = {
                ("user-a",): "project-a",
                ("user-b",): "project-b",
            }.get(user_ids)

            if project_id is None:
                return []

            return [
                type(
                    "Project",
                    (),
                    {"project_id": project_id},
                )()
            ]

        def build_snapshot(self, context):
            self.contexts.append(context)
            return object()

        def _empty_snapshot(self):
            return object()

    def capture_effect(function):
        effects[function.__name__] = function
        return function

    def capture_calc(function):
        calculations[function.__name__] = function
        return function

    service = Service()
    inputs = Inputs()

    monkeypatch.setattr(
        dashboard_server.reactive,
        "value",
        FakeValue,
    )
    monkeypatch.setattr(
        dashboard_server.reactive,
        "effect",
        capture_effect,
    )
    monkeypatch.setattr(
        dashboard_server.reactive,
        "event",
        lambda *args, **kwargs: lambda function: function,
    )
    monkeypatch.setattr(
        dashboard_server.reactive,
        "calc",
        capture_calc,
    )
    monkeypatch.setattr(
        dashboard_server.render,
        "text",
        lambda function: function,
    )
    monkeypatch.setattr(
        dashboard_server.render,
        "data_frame",
        lambda function: function,
    )
    monkeypatch.setattr(
        dashboard_server,
        "ResearchDashboardService",
        lambda dependencies: service,
    )

    dashboard_server.research_dashboard_server(
        inputs,
        object(),
        object(),
        object(),
        is_authenticated=lambda: True,
    )

    assert "_initialize_context" in effects
    assert "_apply_filters" in effects

    effects["_initialize_context"]()
    calculations["snapshot"]()

    assert service.contexts[-1].project_ids == ("project-a",)

    inputs.projects = ("project-b",)
    calculations["snapshot"]()

    assert service.contexts[-1].project_ids == ("project-a",)

    inputs.users = ("user-b",)
    inputs.projects = ("project-a",)
    effects["_apply_filters"]()
    calculations["snapshot"]()

    assert service.contexts[-1].user_ids == ("user-b",)
    assert service.contexts[-1].project_ids == ()

    inputs.projects = ("project-b",)
    effects["_apply_filters"]()
    calculations["snapshot"]()

    assert service.contexts[-1].project_ids == ("project-b",)


def test_selectors_rebuild_only_when_filters_are_applied(monkeypatch):
    empty_snapshot = ResearchDashboardService._empty_snapshot()

    class Service:
        def __init__(self):
            self.contexts = []

        def list_users(self):
            return [
                DashboardUser(
                    user_id="user-a",
                    label="Usuario A",
                    email="a@example.org",
                ),
                DashboardUser(
                    user_id="user-b",
                    label="Usuario B",
                    email="b@example.org",
                ),
            ]

        def list_projects(self, user_ids=()):
            if tuple(user_ids) == ("user-b",):
                return [
                    DashboardProject(
                        project_id="project-c",
                        owner_user_id="user-b",
                        name="Proyecto C",
                    )
                ]

            return [
                DashboardProject(
                    project_id="project-a",
                    owner_user_id="user-a",
                    name="Proyecto A",
                ),
                DashboardProject(
                    project_id="project-b",
                    owner_user_id="user-a",
                    name="Proyecto B",
                ),
            ]

        def build_snapshot(self, context):
            self.contexts.append(context)
            return empty_snapshot

        def _empty_snapshot(self):
            return empty_snapshot

    service = Service()
    monkeypatch.setattr(
        dashboard_server,
        "ResearchDashboardService",
        lambda dependencies: service,
    )
    monkeypatch.setattr(
        dashboard_server.render,
        "data_frame",
        lambda function: function,
    )
    monkeypatch.setattr(
        dashboard_server.ui,
        "update_selectize",
        lambda *args, **kwargs: None,
    )

    def server(input, output, session):
        dashboard_server.research_dashboard_server(
            input,
            output,
            session,
            object(),
            is_authenticated=lambda: True,
        )

    with test_server(server, timeout_secs=20) as session:
        session.set_inputs(
            rd_users=["user-a"],
            rd_projects=["project-a"],
            rd_period=["2026-08-01", "2026-09-17"],
            rd_activity_types=[
                "search",
                "annotation",
                "activity",
            ],
            rd_apply_filters=0,
        )
        session.get_output("rd_kpi_events")

        assert len(service.contexts) == 1
        assert service.contexts[-1].project_ids == ("project-a",)

        session.set_inputs(rd_projects=["project-b"])
        session.get_output("rd_kpi_events")

        assert len(service.contexts) == 1
        assert service.contexts[-1].project_ids == ("project-a",)

        session.set_inputs(rd_apply_filters=1)
        session.get_output("rd_kpi_events")

        assert len(service.contexts) == 2
        assert service.contexts[-1].project_ids == ("project-b",)

        session.set_inputs(
            rd_users=["user-b"],
            rd_projects=["project-a"],
            rd_apply_filters=2,
        )
        session.get_output("rd_kpi_events")

        assert len(service.contexts) == 3
        assert service.contexts[-1].user_ids == ("user-b",)
        assert service.contexts[-1].project_ids == ()
