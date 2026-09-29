from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


def _require_identifier(
    value: str,
    field_name: str,
) -> None:
    if not str(value or "").strip():
        raise ValueError(
            f"{field_name} cannot be blank"
        )


@dataclass(frozen=True, slots=True)
class NexusSourceUser:
    user_id: str
    email: str | None = None
    full_name: str | None = None
    functional_role: str | None = None
    status: str | None = None

    def __post_init__(self) -> None:
        _require_identifier(
            self.user_id,
            "user_id",
        )


@dataclass(frozen=True, slots=True)
class NexusSourceUnit:
    unit_id: str
    name: str
    unit_type: str
    status: str = "active"

    def __post_init__(self) -> None:
        _require_identifier(
            self.unit_id,
            "unit_id",
        )


@dataclass(frozen=True, slots=True)
class NexusSourceUserUnitMembership:
    user_id: str
    unit_id: str
    status: str = "active"
    is_primary: bool = False
    valid_from: date | None = None
    valid_to: date | None = None

    def __post_init__(self) -> None:
        _require_identifier(
            self.user_id,
            "user_id",
        )
        _require_identifier(
            self.unit_id,
            "unit_id",
        )


@dataclass(frozen=True, slots=True)
class NexusSourceProject:
    project_id: str
    owner_user_id: str
    name: str
    status: str = "active"
    description: str | None = None
    deleted_at: datetime | None = None

    def __post_init__(self) -> None:
        _require_identifier(
            self.project_id,
            "project_id",
        )
        _require_identifier(
            self.owner_user_id,
            "owner_user_id",
        )


@dataclass(frozen=True, slots=True)
class NexusSourceProjectMembership:
    project_id: str
    user_id: str
    role: str

    def __post_init__(self) -> None:
        _require_identifier(
            self.project_id,
            "project_id",
        )
        _require_identifier(
            self.user_id,
            "user_id",
        )


@dataclass(frozen=True, slots=True)
class NexusSourceAnnotatedPage:
    project_id: str
    doc_id: str
    page_idx: int
    page_num: int | None = None
    document_label: str | None = None
    annotation_count: int = 1

    def __post_init__(self) -> None:
        _require_identifier(
            self.project_id,
            "project_id",
        )
        _require_identifier(
            self.doc_id,
            "doc_id",
        )

        if self.page_idx < 0:
            raise ValueError(
                "page_idx cannot be negative"
            )

        if self.annotation_count < 1:
            raise ValueError(
                "annotation_count must be at least 1"
            )


@dataclass(frozen=True, slots=True)
class NexusBackfillSnapshot:
    users: tuple[NexusSourceUser, ...] = ()
    units: tuple[NexusSourceUnit, ...] = ()

    user_unit_memberships: tuple[
        NexusSourceUserUnitMembership,
        ...,
    ] = ()

    projects: tuple[NexusSourceProject, ...] = ()

    project_memberships: tuple[
        NexusSourceProjectMembership,
        ...,
    ] = ()

    annotated_pages: tuple[
        NexusSourceAnnotatedPage,
        ...,
    ] = ()
