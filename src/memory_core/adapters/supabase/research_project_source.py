from __future__ import annotations

from datetime import datetime
from typing import Any

from memory_core.domain.research_project import (
    ResearchProject,
)


PROJECT_COLUMNS = (
    "id,"
    "owner_user_id,"
    "name,"
    "description,"
    "tags,"
    "status,"
    "created_at,"
    "updated_at"
)


def _parse_datetime(
    value: Any,
) -> datetime | None:
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        return value

    text = str(value).strip()

    if text.endswith("Z"):
        text = (
            text[:-1]
            + "+00:00"
        )

    try:
        return datetime.fromisoformat(
            text
        )
    except ValueError:
        return None


def _normalize_tags(
    value: Any,
) -> tuple[str, ...]:
    if value is None:
        return ()

    if isinstance(
        value,
        (list, tuple),
    ):
        return tuple(
            str(item).strip()
            for item in value
            if str(item).strip()
        )

    return ()


def _project_from_row(
    row: dict[str, Any],
) -> ResearchProject:
    return ResearchProject(
        project_id=str(
            row.get("id") or ""
        ),
        owner_user_id=str(
            row.get(
                "owner_user_id"
            )
            or ""
        ),
        name=str(
            row.get("name") or ""
        ),
        description=(
            row.get("description")
        ),
        tags=_normalize_tags(
            row.get("tags")
        ),
        status=str(
            row.get("status")
            or "active"
        ),
        created_at=_parse_datetime(
            row.get("created_at")
        ),
        updated_at=_parse_datetime(
            row.get("updated_at")
        ),
    )


class SupabaseResearchProjectSource:
    """
    Fuente Supabase de proyectos.

    El cliente se recibe por inyección.
    Este adaptador no crea conexiones.
    """

    def __init__(
        self,
        client: Any,
        *,
        projects_table: str = (
            "analysis_projects"
        ),
    ) -> None:
        self._client = client
        self._projects_table = (
            projects_table
        )

    def get_project(
        self,
        project_id: str,
    ) -> ResearchProject | None:
        response = (
            self._client
            .table(
                self._projects_table
            )
            .select(
                PROJECT_COLUMNS
            )
            .eq(
                "id",
                str(
                    project_id
                ).strip(),
            )
            .neq(
                "status",
                "archived",
            )
            .is_(
                "deleted_at",
                "null",
            )
            .limit(1)
            .execute()
        )

        rows = list(
            response.data or []
        )

        if not rows:
            return None

        return _project_from_row(
            rows[0]
        )

    def list_projects(
        self,
        owner_user_id: (
            str | None
        ) = None,
        limit: int = 500,
    ) -> list[ResearchProject]:
        query = (
            self._client
            .table(
                self._projects_table
            )
            .select(
                PROJECT_COLUMNS
            )
            .neq(
                "status",
                "archived",
            )
            .is_(
                "deleted_at",
                "null",
            )
        )

        normalized_owner = str(
            owner_user_id or ""
        ).strip()

        if normalized_owner:
            query = query.eq(
                "owner_user_id",
                normalized_owner,
            )

        response = (
            query
            .order(
                "updated_at",
                desc=True,
            )
            .limit(
                int(limit)
            )
            .execute()
        )

        return [
            _project_from_row(row)
            for row in (
                response.data or []
            )
        ]


__all__ = [
    "SupabaseResearchProjectSource",
]
