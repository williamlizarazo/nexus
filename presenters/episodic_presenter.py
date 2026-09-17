from __future__ import annotations

from datetime import datetime
from typing import Any


def format_datetime(
    value: datetime | None,
) -> str:
    if value is None:
        return "—"

    return value.strftime(
        "%d/%m/%Y %H:%M"
    )


def format_score(
    value: float | None,
) -> str:
    if value is None:
        return "—"

    return f"{value:.2f}"


def project_choices(
    projects: list[Any],
) -> dict[str, str]:
    choices = {
        "": "Selecciona un proyecto..."
    }

    for project in projects:
        count = project.episode_count

        noun = (
            "episodio"
            if count == 1
            else "episodios"
        )

        choices[project.project_id] = (
            f"{project.project_id} · "
            f"{count} {noun}"
        )

    return choices


def episode_choices(
    episodes: list[Any],
) -> dict[str, str]:
    choices = {
        "": "Selecciona un episodio..."
    }

    for episode in episodes:
        started = format_datetime(
            episode.started_at
        )

        choices[episode.episode_id] = (
            f"{started} · "
            f"{episode.status} · "
            f"{episode.item_count} items"
        )

    return choices
