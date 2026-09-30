from __future__ import annotations

from typing import Any

from supabase import Client

from memory_core.adapters.supabase.nexus_backfill_source import (
    SupabaseNexusBackfillSource,
)
from memory_core.domain.nexus_backfill import NexusBackfillSnapshot
from memory_core.domain.nexus_incremental import NexusAffectedScope


class SupabaseNexusIncrementalSource:
    """
    Carga solamente el contexto necesario para reproyectar
    una parte afectada del grafo NEXUS.

    Reutiliza los modelos y constructores del backfill histórico.
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

    def load_scope(
        self,
        *,
        scope: NexusAffectedScope,
    ) -> NexusBackfillSnapshot:

        if (
            not scope.project_ids
            and not scope.user_ids
            and not scope.unit_ids
        ):
            return self._empty_snapshot()

        project_ids = set(scope.project_ids)
        user_ids = set(scope.user_ids)
        unit_ids = set(scope.unit_ids)

        # --------------------------------------------------------
        # 1. Usuarios pertenecientes a unidades explícitas
        # --------------------------------------------------------

        explicit_unit_memberships: list[
            dict[str, Any]
        ] = []

        if unit_ids:
            explicit_unit_memberships = (
                self._fetch_filtered(
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
                    filters=(
                        (
                            "in",
                            "unit_id",
                            tuple(sorted(unit_ids)),
                        ),
                    ),
                )
            )

            user_ids.update(
                str(row["user_id"])
                for row in explicit_unit_memberships
                if row.get("user_id") is not None
            )

        # --------------------------------------------------------
        # 2. Proyectos relacionados directamente con usuarios
        # --------------------------------------------------------

        user_project_memberships: list[
            dict[str, Any]
        ] = []

        if user_ids:
            user_project_memberships = (
                self._fetch_filtered(
                    "analysis_project_members",
                    "project_id,user_id,role",
                    order_by=(
                        "project_id",
                        "user_id",
                    ),
                    filters=(
                        (
                            "in",
                            "user_id",
                            tuple(sorted(user_ids)),
                        ),
                    ),
                )
            )

            project_ids.update(
                str(row["project_id"])
                for row in user_project_memberships
                if row.get("project_id") is not None
            )

        # --------------------------------------------------------
        # 3. Cargar proyectos completos del alcance
        # --------------------------------------------------------

        project_rows: list[
            dict[str, Any]
        ] = []

        project_member_rows: list[
            dict[str, Any]
        ] = []

        document_rows: list[
            dict[str, Any]
        ] = []

        page_rows: list[
            dict[str, Any]
        ] = []

        annotation_rows: list[
            dict[str, Any]
        ] = []

        if project_ids:
            project_filter = tuple(
                sorted(project_ids)
            )

            project_rows = self._fetch_filtered(
                "analysis_projects",
                (
                    "id,owner_user_id,name,"
                    "description,status,deleted_at"
                ),
                order_by=("id",),
                filters=(
                    (
                        "in",
                        "id",
                        project_filter,
                    ),
                ),
            )

            project_member_rows = (
                self._fetch_filtered(
                    "analysis_project_members",
                    "project_id,user_id,role",
                    order_by=(
                        "project_id",
                        "user_id",
                    ),
                    filters=(
                        (
                            "in",
                            "project_id",
                            project_filter,
                        ),
                    ),
                )
            )

            document_rows = self._fetch_filtered(
                "analysis_project_documents",
                "project_id,doc_id,display_name",
                order_by=(
                    "project_id",
                    "doc_id",
                ),
                filters=(
                    (
                        "in",
                        "project_id",
                        project_filter,
                    ),
                ),
            )

            page_rows = self._fetch_filtered(
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
                filters=(
                    (
                        "in",
                        "project_id",
                        project_filter,
                    ),
                ),
            )

            annotation_rows = self._fetch_filtered(
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
                        "in",
                        "project_id",
                        project_filter,
                    ),
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

        # --------------------------------------------------------
        # 4. Todos los usuarios requeridos por esos proyectos
        # --------------------------------------------------------

        for row in project_rows:
            owner_user_id = row.get(
                "owner_user_id"
            )

            if owner_user_id is not None:
                user_ids.add(
                    str(owner_user_id)
                )

        for row in project_member_rows:
            user_id = row.get(
                "user_id"
            )

            if user_id is not None:
                user_ids.add(
                    str(user_id)
                )

        # --------------------------------------------------------
        # 5. Perfiles de usuario
        # --------------------------------------------------------

        memory_user_rows: list[
            dict[str, Any]
        ] = []

        if user_ids:
            memory_user_rows = self._fetch_filtered(
                "memory_users",
                (
                    "user_id,email,full_name,"
                    "functional_role,status"
                ),
                order_by=("user_id",),
                filters=(
                    (
                        "in",
                        "user_id",
                        tuple(sorted(user_ids)),
                    ),
                ),
            )

        # --------------------------------------------------------
        # 6. Membresías organizacionales de usuarios afectados
        # --------------------------------------------------------

        user_unit_rows: list[
            dict[str, Any]
        ] = list(
            explicit_unit_memberships
        )

        if user_ids:
            rows = self._fetch_filtered(
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
                filters=(
                    (
                        "in",
                        "user_id",
                        tuple(sorted(user_ids)),
                    ),
                ),
            )

            user_unit_rows.extend(
                rows
            )

        user_unit_rows = self._deduplicate_rows(
            user_unit_rows,
            key_fields=(
                "user_id",
                "unit_id",
                "valid_from",
                "valid_to",
            ),
        )

        unit_ids.update(
            str(row["unit_id"])
            for row in user_unit_rows
            if row.get("unit_id") is not None
        )

        # --------------------------------------------------------
        # 7. Unidades organizacionales
        # --------------------------------------------------------

        unit_rows: list[
            dict[str, Any]
        ] = []

        if unit_ids:
            unit_rows = self._fetch_filtered(
                "memory_organizational_units",
                "unit_id,name,unit_type,status",
                order_by=("unit_id",),
                filters=(
                    (
                        "in",
                        "unit_id",
                        tuple(sorted(unit_ids)),
                    ),
                ),
            )

        # --------------------------------------------------------
        # 8. Reutilizar las transformaciones del backfill
        # --------------------------------------------------------

        return NexusBackfillSnapshot(
            users=(
                SupabaseNexusBackfillSource
                ._build_users(
                    memory_user_rows=memory_user_rows,
                    project_rows=project_rows,
                    project_member_rows=(
                        project_member_rows
                    ),
                )
            ),
            units=(
                SupabaseNexusBackfillSource
                ._build_units(
                    unit_rows
                )
            ),
            user_unit_memberships=(
                SupabaseNexusBackfillSource
                ._build_user_unit_memberships(
                    user_unit_rows
                )
            ),
            projects=(
                SupabaseNexusBackfillSource
                ._build_projects(
                    project_rows
                )
            ),
            project_memberships=(
                SupabaseNexusBackfillSource
                ._build_project_memberships(
                    project_member_rows
                )
            ),
            annotated_pages=(
                SupabaseNexusBackfillSource
                ._build_annotated_pages(
                    annotation_rows=(
                        annotation_rows
                    ),
                    document_rows=(
                        document_rows
                    ),
                    page_rows=page_rows,
                )
            ),
        )

    # ============================================================
    # DATABASE
    # ============================================================

    def _fetch_filtered(
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

                elif operator == "in":
                    query = query.in_(
                        column,
                        list(value),
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
    # HELPERS
    # ============================================================

    @staticmethod
    def _deduplicate_rows(
        rows: list[dict[str, Any]],
        *,
        key_fields: tuple[str, ...],
    ) -> list[dict[str, Any]]:

        indexed: dict[
            tuple[Any, ...],
            dict[str, Any],
        ] = {}

        for row in rows:
            key = tuple(
                row.get(field)
                for field in key_fields
            )

            indexed[key] = row

        return [
            indexed[key]
            for key in sorted(
                indexed,
                key=lambda value: tuple(
                    ""
                    if item is None
                    else str(item)
                    for item in value
                ),
            )
        ]

    @staticmethod
    def _empty_snapshot(
    ) -> NexusBackfillSnapshot:

        return NexusBackfillSnapshot(
            users=(),
            units=(),
            user_unit_memberships=(),
            projects=(),
            project_memberships=(),
            annotated_pages=(),
        )
