from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Any

from supabase import Client

from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
    NexusSourceAnnotatedPage,
    NexusSourceProject,
    NexusSourceProjectMembership,
    NexusSourceUnit,
    NexusSourceUser,
    NexusSourceUserUnitMembership,
)


def _optional_str(
    value: Any,
) -> str | None:
    if value is None:
        return None

    text = str(value).strip()

    return text or None


def _required_str(
    value: Any,
    field_name: str,
) -> str:
    result = _optional_str(
        value
    )

    if result is None:
        raise ValueError(
            f"{field_name} cannot be blank"
        )

    return result


def _optional_int(
    value: Any,
) -> int | None:
    if value is None or value == "":
        return None

    return int(value)


def _required_int(
    value: Any,
    field_name: str,
) -> int:
    result = _optional_int(
        value
    )

    if result is None:
        raise ValueError(
            f"{field_name} cannot be null"
        )

    return result


def _parse_date(
    value: Any,
) -> date | None:
    if value is None or value == "":
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value.date()

    if isinstance(
        value,
        date,
    ):
        return value

    return date.fromisoformat(
        str(value).strip()
    )


def _parse_datetime(
    value: Any,
) -> datetime | None:
    if value is None or value == "":
        return None

    if isinstance(
        value,
        datetime,
    ):
        return value

    return datetime.fromisoformat(
        str(value)
        .strip()
        .replace(
            "Z",
            "+00:00",
        )
    )


class SupabaseNexusBackfillSource:
    """
    Adaptador Supabase para construir el snapshot fuente NEXUS.

    La clase conoce el esquema físico actual, pero devuelve únicamente
    modelos de dominio agnósticos.
    """

    def __init__(
        self,
        client: Client,
        *,
        page_size: int = 1000,
    ) -> None:
        if page_size < 1:
            raise ValueError(
                "page_size must be greater than zero"
            )

        self._client = client
        self._page_size = page_size

    def load_snapshot(
        self,
    ) -> NexusBackfillSnapshot:

        memory_user_rows = self._fetch_all(
            "memory_users",
            (
                "user_id,email,full_name,"
                "functional_role,status"
            ),
            order_by=(
                "user_id",
            ),
        )

        unit_rows = self._fetch_all(
            "memory_organizational_units",
            (
                "unit_id,name,"
                "unit_type,status"
            ),
            order_by=(
                "unit_id",
            ),
        )

        user_unit_rows = self._fetch_all(
            "memory_user_unit_memberships",
            (
                "user_id,unit_id,status,"
                "is_primary,valid_from,valid_to"
            ),
            order_by=(
                "user_id",
                "unit_id",
                "valid_from",
            ),
        )

        project_rows = self._fetch_all(
            "analysis_projects",
            (
                "id,owner_user_id,name,"
                "description,status,deleted_at"
            ),
            order_by=(
                "id",
            ),
        )

        project_member_rows = self._fetch_all(
            "analysis_project_members",
            "project_id,user_id,role",
            order_by=(
                "project_id",
                "user_id",
            ),
        )

        document_rows = self._fetch_all(
            "analysis_project_documents",
            (
                "project_id,doc_id,"
                "display_name"
            ),
            order_by=(
                "project_id",
                "doc_id",
            ),
        )

        page_rows = self._fetch_all(
            "analysis_project_pages",
            (
                "project_id,doc_id,"
                "page_idx,page_num"
            ),
            order_by=(
                "project_id",
                "doc_id",
                "page_idx",
            ),
        )

        annotation_rows = self._fetch_all(
            "analysis_project_annotations",
            (
                "project_id,doc_id,page_idx,"
                "status,deleted_at"
            ),
            order_by=(
                "project_id",
                "doc_id",
                "page_idx",
            ),
            filters=(
                (
                    "eq",
                    "status",
                    "active",
                ),
                (
                    "is",
                    "deleted_at",
                    "null",
                ),
            ),
        )

        users = self._build_users(
            memory_user_rows=memory_user_rows,
            project_rows=project_rows,
            project_member_rows=(
                project_member_rows
            ),
        )

        units = self._build_units(
            unit_rows
        )

        user_unit_memberships = (
            self._build_user_unit_memberships(
                user_unit_rows
            )
        )

        projects = self._build_projects(
            project_rows
        )

        project_memberships = (
            self._build_project_memberships(
                project_member_rows
            )
        )

        annotated_pages = (
            self._build_annotated_pages(
                annotation_rows=annotation_rows,
                document_rows=document_rows,
                page_rows=page_rows,
            )
        )

        return NexusBackfillSnapshot(
            users=users,
            units=units,
            user_unit_memberships=(
                user_unit_memberships
            ),
            projects=projects,
            project_memberships=(
                project_memberships
            ),
            annotated_pages=annotated_pages,
        )

    # ============================================================
    # DATABASE READ
    # ============================================================

    def _fetch_all(
        self,
        table_name: str,
        columns: str,
        *,
        order_by: tuple[str, ...] = (),
        filters: tuple[
            tuple[str, str, Any],
            ...,
        ] = (),
    ) -> list[dict[str, Any]]:

        result: list[
            dict[str, Any]
        ] = []

        start = 0

        while True:
            query = (
                self._client
                .table(table_name)
                .select(columns)
            )

            for (
                operator,
                column,
                value,
            ) in filters:

                if operator == "eq":
                    query = query.eq(
                        column,
                        value,
                    )

                elif operator == "is":
                    query = query.is_(
                        column,
                        value,
                    )

                else:
                    raise ValueError(
                        "Unsupported Supabase "
                        f"filter operator: {operator}"
                    )

            for column in order_by:
                query = query.order(
                    column
                )

            end = (
                start
                + self._page_size
                - 1
            )

            response = (
                query
                .range(
                    start,
                    end,
                )
                .execute()
            )

            batch = list(
                response.data or []
            )

            result.extend(
                batch
            )

            if len(batch) < self._page_size:
                break

            start += self._page_size

        return result

    # ============================================================
    # USERS
    # ============================================================

    @staticmethod
    def _build_users(
        *,
        memory_user_rows: list[
            dict[str, Any]
        ],
        project_rows: list[
            dict[str, Any]
        ],
        project_member_rows: list[
            dict[str, Any]
        ],
    ) -> tuple[
        NexusSourceUser,
        ...,
    ]:

        profiles: dict[
            str,
            dict[str, Any],
        ] = {}

        for row in memory_user_rows:
            user_id = _required_str(
                row.get("user_id"),
                "memory_users.user_id",
            )

            profiles[user_id] = row

        user_ids = set(
            profiles
        )

        for row in project_rows:
            owner_user_id = _required_str(
                row.get("owner_user_id"),
                (
                    "analysis_projects."
                    "owner_user_id"
                ),
            )

            user_ids.add(
                owner_user_id
            )

        for row in project_member_rows:
            user_id = _required_str(
                row.get("user_id"),
                (
                    "analysis_project_members."
                    "user_id"
                ),
            )

            user_ids.add(
                user_id
            )

        users = []

        for user_id in sorted(
            user_ids
        ):
            profile = profiles.get(
                user_id
            )

            users.append(
                NexusSourceUser(
                    user_id=user_id,
                    email=(
                        _optional_str(
                            profile.get("email")
                        )
                        if profile
                        else None
                    ),
                    full_name=(
                        _optional_str(
                            profile.get(
                                "full_name"
                            )
                        )
                        if profile
                        else None
                    ),
                    functional_role=(
                        _optional_str(
                            profile.get(
                                "functional_role"
                            )
                        )
                        if profile
                        else None
                    ),
                    status=(
                        _optional_str(
                            profile.get(
                                "status"
                            )
                        )
                        if profile
                        else None
                    ),
                )
            )

        return tuple(
            users
        )

    # ============================================================
    # ORGANIZATIONAL STRUCTURE
    # ============================================================

    @staticmethod
    def _build_units(
        rows: list[
            dict[str, Any]
        ],
    ) -> tuple[
        NexusSourceUnit,
        ...,
    ]:

        units = [
            NexusSourceUnit(
                unit_id=_required_str(
                    row.get("unit_id"),
                    (
                        "memory_organizational_"
                        "units.unit_id"
                    ),
                ),
                name=_required_str(
                    row.get("name"),
                    (
                        "memory_organizational_"
                        "units.name"
                    ),
                ),
                unit_type=_required_str(
                    row.get("unit_type"),
                    (
                        "memory_organizational_"
                        "units.unit_type"
                    ),
                ),
                status=(
                    _optional_str(
                        row.get("status")
                    )
                    or "active"
                ),
            )
            for row in rows
        ]

        return tuple(
            sorted(
                units,
                key=lambda item: (
                    item.unit_id
                ),
            )
        )

    @staticmethod
    def _build_user_unit_memberships(
        rows: list[
            dict[str, Any]
        ],
    ) -> tuple[
        NexusSourceUserUnitMembership,
        ...,
    ]:

        memberships = [
            NexusSourceUserUnitMembership(
                user_id=_required_str(
                    row.get("user_id"),
                    (
                        "memory_user_unit_"
                        "memberships.user_id"
                    ),
                ),
                unit_id=_required_str(
                    row.get("unit_id"),
                    (
                        "memory_user_unit_"
                        "memberships.unit_id"
                    ),
                ),
                status=(
                    _optional_str(
                        row.get("status")
                    )
                    or "active"
                ),
                is_primary=bool(
                    row.get(
                        "is_primary",
                        False,
                    )
                ),
                valid_from=_parse_date(
                    row.get(
                        "valid_from"
                    )
                ),
                valid_to=_parse_date(
                    row.get(
                        "valid_to"
                    )
                ),
            )
            for row in rows
        ]

        return tuple(
            sorted(
                memberships,
                key=lambda item: (
                    item.user_id,
                    item.unit_id,
                    (
                        item.valid_from
                        or date.min
                    ),
                    (
                        item.valid_to
                        or date.max
                    ),
                ),
            )
        )

    # ============================================================
    # PROJECTS
    # ============================================================

    @staticmethod
    def _build_projects(
        rows: list[
            dict[str, Any]
        ],
    ) -> tuple[
        NexusSourceProject,
        ...,
    ]:

        projects = [
            NexusSourceProject(
                project_id=_required_str(
                    row.get("id"),
                    "analysis_projects.id",
                ),
                owner_user_id=_required_str(
                    row.get(
                        "owner_user_id"
                    ),
                    (
                        "analysis_projects."
                        "owner_user_id"
                    ),
                ),
                name=_required_str(
                    row.get("name"),
                    "analysis_projects.name",
                ),
                description=_optional_str(
                    row.get("description")
                ),
                status=(
                    _optional_str(
                        row.get("status")
                    )
                    or "active"
                ),
                deleted_at=(
                    _parse_datetime(
                        row.get(
                            "deleted_at"
                        )
                    )
                ),
            )
            for row in rows
        ]

        return tuple(
            sorted(
                projects,
                key=lambda item: (
                    item.project_id
                ),
            )
        )

    @staticmethod
    def _build_project_memberships(
        rows: list[
            dict[str, Any]
        ],
    ) -> tuple[
        NexusSourceProjectMembership,
        ...,
    ]:

        memberships = [
            NexusSourceProjectMembership(
                project_id=_required_str(
                    row.get("project_id"),
                    (
                        "analysis_project_"
                        "members.project_id"
                    ),
                ),
                user_id=_required_str(
                    row.get("user_id"),
                    (
                        "analysis_project_"
                        "members.user_id"
                    ),
                ),
                role=_required_str(
                    row.get("role"),
                    (
                        "analysis_project_"
                        "members.role"
                    ),
                ),
            )
            for row in rows
        ]

        return tuple(
            sorted(
                memberships,
                key=lambda item: (
                    item.project_id,
                    item.user_id,
                    item.role,
                ),
            )
        )

    # ============================================================
    # ANNOTATED DOCUMENTS / PAGES
    # ============================================================

    @staticmethod
    def _build_annotated_pages(
        *,
        annotation_rows: list[
            dict[str, Any]
        ],
        document_rows: list[
            dict[str, Any]
        ],
        page_rows: list[
            dict[str, Any]
        ],
    ) -> tuple[
        NexusSourceAnnotatedPage,
        ...,
    ]:

        documents: dict[
            tuple[str, str],
            dict[str, Any],
        ] = {}

        for row in document_rows:
            project_id = _required_str(
                row.get("project_id"),
                (
                    "analysis_project_"
                    "documents.project_id"
                ),
            )

            doc_id = _required_str(
                row.get("doc_id"),
                (
                    "analysis_project_"
                    "documents.doc_id"
                ),
            )

            documents[
                (
                    project_id,
                    doc_id,
                )
            ] = row

        pages: dict[
            tuple[str, str, int],
            dict[str, Any],
        ] = {}

        for row in page_rows:
            project_id = _required_str(
                row.get("project_id"),
                (
                    "analysis_project_pages."
                    "project_id"
                ),
            )

            doc_id = _required_str(
                row.get("doc_id"),
                (
                    "analysis_project_pages."
                    "doc_id"
                ),
            )

            page_idx = _required_int(
                row.get("page_idx"),
                (
                    "analysis_project_pages."
                    "page_idx"
                ),
            )

            pages[
                (
                    project_id,
                    doc_id,
                    page_idx,
                )
            ] = row

        counts: Counter[
            tuple[str, str, int]
        ] = Counter()

        for row in annotation_rows:

            status = (
                _optional_str(
                    row.get("status")
                )
                or ""
            ).lower()

            if status != "active":
                continue

            if row.get("deleted_at") not in (
                None,
                "",
            ):
                continue

            project_id = _optional_str(
                row.get("project_id")
            )

            doc_id = _optional_str(
                row.get("doc_id")
            )

            page_idx = _optional_int(
                row.get("page_idx")
            )

            if (
                project_id is None
                or doc_id is None
                or page_idx is None
            ):
                continue

            counts[
                (
                    project_id,
                    doc_id,
                    page_idx,
                )
            ] += 1

        annotated_pages = []

        for (
            project_id,
            doc_id,
            page_idx,
        ) in sorted(
            counts
        ):

            document_row = documents.get(
                (
                    project_id,
                    doc_id,
                ),
                {},
            )

            page_row = pages.get(
                (
                    project_id,
                    doc_id,
                    page_idx,
                ),
                {},
            )

            annotated_pages.append(
                NexusSourceAnnotatedPage(
                    project_id=project_id,
                    doc_id=doc_id,
                    document_label=(
                        _optional_str(
                            document_row.get(
                                "display_name"
                            )
                        )
                    ),
                    page_idx=page_idx,
                    page_num=(
                        _optional_int(
                            page_row.get(
                                "page_num"
                            )
                        )
                    ),
                    annotation_count=counts[
                        (
                            project_id,
                            doc_id,
                            page_idx,
                        )
                    ],
                )
            )

        return tuple(
            annotated_pages
        )
