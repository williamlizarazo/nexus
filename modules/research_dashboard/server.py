from __future__ import annotations

from collections.abc import Callable
from datetime import date

import pandas as pd
from shiny import reactive, render, ui

from core.dependencies import AppDependencies
from presenters.research_dashboard_presenter import (
    ResearchDashboardPresenter,
)
from services.research_dashboard_service import (
    AnalysisContext,
    ResearchDashboardService,
)


def _tuple_value(value) -> tuple[str, ...]:
    if value is None:
        return ()

    if isinstance(value, str):
        return (value,) if value else ()

    return tuple(
        str(item)
        for item in value
        if item
    )


def _date_value(value) -> date | None:
    if value is None:
        return None

    if isinstance(value, date):
        return value

    if isinstance(value, str) and value:
        return date.fromisoformat(value)

    return None


def _grid(rows):
    return render.DataGrid(
        pd.DataFrame(rows),
        filters=True,
        width="100%",
        height="360px",
    )


def research_dashboard_server(
    input,
    output,
    session,
    dependencies: AppDependencies,
    *,
    is_authenticated: Callable[
        [],
        bool,
    ],
):
    service = ResearchDashboardService(
        dependencies
    )
    presenter = ResearchDashboardPresenter()

    applied_context = reactive.value(
        None
    )
    initialized = reactive.value(
        False
    )

    def _read_draft_context() -> AnalysisContext:
        period = input.rd_period()

        date_from = None
        date_to = None

        user_ids = _tuple_value(
            input.rd_users()
        )

        selected_project_ids = (
            _tuple_value(
                input.rd_projects()
            )
        )

        if period:
            if len(period) > 0:
                date_from = _date_value(
                    period[0]
                )

            if len(period) > 1:
                date_to = _date_value(
                    period[1]
                )

        available_project_ids = {
            project.project_id
            for project in (
                service.list_projects(
                    user_ids
                )
            )
        }

        project_ids = tuple(
            project_id
            for project_id
            in selected_project_ids
            if project_id
            in available_project_ids
        )

        return AnalysisContext(
            user_ids=user_ids,
            project_ids=project_ids,
            date_from=date_from,
            date_to=date_to,
            event_types=_tuple_value(
                input.rd_activity_types()
            ),
        )

    @reactive.effect
    def _reset_when_logged_out():
        if is_authenticated():
            return

        applied_context.set(None)
        initialized.set(False)

    @reactive.effect
    def _load_users():
        if not is_authenticated():
            return

        users = service.list_users()

        choices = {
            user.user_id: user.label
            for user in users
        }

        selected = (
            [users[0].user_id]
            if users
            else []
        )

        ui.update_selectize(
            "rd_users",
            choices=choices,
            selected=selected,
            session=session,
        )

    @reactive.effect
    def _load_projects():
        if not is_authenticated():
            return

        user_ids = _tuple_value(
            input.rd_users()
        )

        projects = service.list_projects(
            user_ids
        )

        choices = {
            project.project_id:
            project.name
            for project in projects
        }

        with reactive.isolate():
            current = set(
                _tuple_value(
                    input.rd_projects()
                )
            )

        selected = [
            project_id
            for project_id in current
            if project_id in choices
        ]

        ui.update_selectize(
            "rd_projects",
            choices=choices,
            selected=selected,
            session=session,
        )

    @reactive.effect
    def _initialize_context():
        if not is_authenticated():
            return

        if initialized.get():
            return

        if not _tuple_value(
            input.rd_users()
        ):
            return

        applied_context.set(
            _read_draft_context()
        )

        initialized.set(True)

    @reactive.effect
    @reactive.event(
        input.rd_apply_filters
    )
    def _apply_filters():
        if not is_authenticated():
            return

        applied_context.set(
            _read_draft_context()
        )

    @reactive.calc
    def snapshot():
        if not is_authenticated():
            return service._empty_snapshot()

        context = applied_context.get()

        if context is None:
            return service._empty_snapshot()

        return service.build_snapshot(
            context
        )

    @render.text
    def rd_kpi_users():
        return str(
            snapshot().kpis.users
        )

    @render.text
    def rd_kpi_projects():
        return str(
            snapshot().kpis.projects
        )

    @render.text
    def rd_kpi_questions():
        return str(
            snapshot().kpis.questions
        )

    @render.text
    def rd_kpi_annotations():
        return str(
            snapshot().kpis.annotations
        )

    @render.text
    def rd_kpi_activities():
        return str(
            snapshot().kpis.activities
        )

    @render.text
    def rd_kpi_events():
        return str(
            snapshot().kpis.events
        )

    @render.data_frame
    def rd_timeline():
        return _grid(
            presenter.timeline(
                snapshot()
            )
        )

    @render.data_frame
    def rd_questions():
        return _grid(
            presenter.questions(
                snapshot()
            )
        )

    @render.data_frame
    def rd_annotations():
        return _grid(
            presenter.annotations(
                snapshot()
            )
        )

    @render.data_frame
    def rd_evidence_paths():
        return _grid(
            presenter.evidence_paths(
                snapshot()
            )
        )

    @render.data_frame
    def rd_users_comparison():
        return _grid(
            presenter.users_comparison(
                snapshot()
            )
        )

    @render.data_frame
    def rd_projects_comparison():
        return _grid(
            presenter.projects_comparison(
                snapshot()
            )
        )
