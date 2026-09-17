from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


def _optional_text(
    value: str | None,
) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()
    return normalized or None


@dataclass(frozen=True, slots=True)
class ResearchProject:
    project_id: str
    owner_user_id: str
    name: str
    description: str | None = None
    tags: tuple[str, ...] = ()
    status: str = "active"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        project_id = str(
            self.project_id or ""
        ).strip()

        owner_user_id = str(
            self.owner_user_id or ""
        ).strip()

        name = str(
            self.name or ""
        ).strip()

        status = str(
            self.status or "active"
        ).strip().lower()

        if not project_id:
            raise ValueError(
                "project_id es obligatorio."
            )

        if not owner_user_id:
            raise ValueError(
                "owner_user_id es obligatorio."
            )

        if not name:
            raise ValueError(
                "name es obligatorio."
            )

        normalized_tags = tuple(
            str(tag).strip()
            for tag in self.tags
            if str(tag).strip()
        )

        object.__setattr__(
            self,
            "project_id",
            project_id,
        )

        object.__setattr__(
            self,
            "owner_user_id",
            owner_user_id,
        )

        object.__setattr__(
            self,
            "name",
            name,
        )

        object.__setattr__(
            self,
            "description",
            _optional_text(
                self.description
            ),
        )

        object.__setattr__(
            self,
            "tags",
            normalized_tags,
        )

        object.__setattr__(
            self,
            "status",
            status,
        )
