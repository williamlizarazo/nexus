from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from presenters.episodic_presenter import (
    episode_choices,
    format_datetime,
    project_choices,
)


def test_project_choices_include_episode_count():
    projects = [
        SimpleNamespace(
            project_id="project-001",
            episode_count=4,
            latest_started_at=datetime(
                2026,
                9,
                15,
                10,
                0,
                tzinfo=timezone.utc,
            ),
        )
    ]

    choices = project_choices(projects)

    assert choices[""] == "Selecciona un proyecto..."
    assert choices["project-001"] == (
        "project-001 · 4 episodios"
    )


def test_episode_choices_include_date_status_and_counts():
    episodes = [
        SimpleNamespace(
            episode_id="episode-001",
            started_at=datetime(
                2026,
                9,
                15,
                10,
                0,
                tzinfo=timezone.utc,
            ),
            status="provisional",
            item_count=8,
            edge_count=5,
        )
    ]

    choices = episode_choices(episodes)

    assert choices[""] == "Selecciona un episodio..."

    assert "15/09/2026 10:00" in choices["episode-001"]
    assert "provisional" in choices["episode-001"]
    assert "8 items" in choices["episode-001"]


def test_format_datetime_handles_none():
    assert format_datetime(None) == "—"
