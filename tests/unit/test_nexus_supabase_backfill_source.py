from __future__ import annotations

from types import SimpleNamespace

from memory_core.adapters.supabase.nexus_backfill_source import (
    SupabaseNexusBackfillSource,
)
from memory_core.contracts.nexus_backfill_source import (
    NexusBackfillSource,
)


class FakeQuery:

    def __init__(
        self,
        rows,
    ):
        self._rows = [
            dict(row)
            for row in rows
        ]
        self._columns = "*"
        self._filters = []
        self._orders = []
        self._start = 0
        self._end = None

    def select(
        self,
        columns,
    ):
        self._columns = columns
        return self

    def eq(
        self,
        column,
        value,
    ):
        self._filters.append(
            (
                "eq",
                column,
                value,
            )
        )
        return self

    def is_(
        self,
        column,
        value,
    ):
        self._filters.append(
            (
                "is",
                column,
                value,
            )
        )
        return self

    def order(
        self,
        column,
    ):
        self._orders.append(
            column
        )
        return self

    def range(
        self,
        start,
        end,
    ):
        self._start = start
        self._end = end
        return self

    def execute(self):
        rows = [
            dict(row)
            for row in self._rows
        ]

        for operator, column, value in self._filters:

            if operator == "eq":
                rows = [
                    row
                    for row in rows
                    if row.get(column) == value
                ]

            elif operator == "is":
                if value in (None, "null"):
                    rows = [
                        row
                        for row in rows
                        if row.get(column) is None
                    ]

        for column in reversed(
            self._orders
        ):
            rows.sort(
                key=lambda row: (
                    row.get(column) is None,
                    row.get(column),
                )
            )

        if self._end is not None:
            rows = rows[
                self._start:
                self._end + 1
            ]

        if self._columns != "*":
            columns = [
                column.strip()
                for column
                in self._columns.split(",")
            ]

            rows = [
                {
                    column: row.get(column)
                    for column in columns
                }
                for row in rows
            ]

        return SimpleNamespace(
            data=rows
        )


class FakeClient:

    def __init__(
        self,
        tables,
    ):
        self._tables = tables
        self.requested_tables = []

    def table(
        self,
        name,
    ):
        if name not in self._tables:
            raise AssertionError(
                f"Unexpected table requested: {name}"
            )

        self.requested_tables.append(
            name
        )

        return FakeQuery(
            self._tables[name]
        )


def _empty_tables():
    return {
        "memory_users": [],
        "memory_organizational_units": [],
        "memory_user_unit_memberships": [],
        "analysis_projects": [],
        "analysis_project_members": [],
        "analysis_project_documents": [],
        "analysis_project_pages": [],
        "analysis_project_annotations": [],
    }


def test_supabase_source_builds_canonical_backfill_snapshot():
    tables = _empty_tables()

    tables["memory_users"] = [
        {
            "user_id": "user-1",
            "email": "uno@jep.gov.co",
            "full_name": "Usuario Uno",
            "functional_role": "Analista",
            "status": "active",
        },
        {
            "user_id": "user-directory",
            "email": "directorio@jep.gov.co",
            "full_name": "Usuario Directorio",
            "functional_role": "Investigador",
            "status": "active",
        },
    ]

    tables["memory_organizational_units"] = [
        {
            "unit_id": "unit-1",
            "name": "Magistratura X",
            "unit_type": "magistratura",
            "status": "active",
        },
    ]

    tables["memory_user_unit_memberships"] = [
        {
            "user_id": "user-1",
            "unit_id": "unit-1",
            "status": "active",
            "is_primary": True,
            "valid_from": "2026-01-01",
            "valid_to": None,
        },
    ]

    tables["analysis_projects"] = [
        {
            "id": "project-1",
            "owner_user_id": "user-2",
            "name": "Proyecto Uno",
            "description": "Descripción uno",
            "status": "active",
            "deleted_at": None,
        },
        {
            "id": "project-2",
            "owner_user_id": "user-1",
            "name": "Proyecto Dos",
            "description": "",
            "status": "active",
            "deleted_at": None,
        },
    ]

    tables["analysis_project_members"] = [
        {
            "project_id": "project-1",
            "user_id": "user-2",
            "role": "owner",
        },
        {
            "project_id": "project-2",
            "user_id": "user-1",
            "role": "owner",
        },
    ]

    tables["analysis_project_documents"] = [
        {
            "project_id": "project-1",
            "doc_id": "doc-1",
            "display_name": "Documento Uno.pdf",
        },
        {
            "project_id": "project-2",
            "doc_id": "doc-2",
            "display_name": "Documento Dos.pdf",
        },
    ]

    tables["analysis_project_pages"] = [
        {
            "project_id": "project-1",
            "doc_id": "doc-1",
            "page_idx": 4,
            "page_num": 5,
        },
        {
            "project_id": "project-2",
            "doc_id": "doc-2",
            "page_idx": 8,
            "page_num": 9,
        },
    ]

    tables["analysis_project_annotations"] = [
        {
            "project_id": "project-1",
            "doc_id": "doc-1",
            "page_idx": 4,
            "status": "active",
            "deleted_at": None,
        },
        {
            "project_id": "project-1",
            "doc_id": "doc-1",
            "page_idx": 4,
            "status": "active",
            "deleted_at": None,
        },
        {
            "project_id": "project-2",
            "doc_id": "doc-2",
            "page_idx": 8,
            "status": "inactive",
            "deleted_at": None,
        },
        {
            "project_id": "project-2",
            "doc_id": "doc-2",
            "page_idx": 8,
            "status": "active",
            "deleted_at": "2026-09-01T12:00:00+00:00",
        },
    ]

    client = FakeClient(
        tables
    )

    source = SupabaseNexusBackfillSource(
        client,
        page_size=2,
    )

    assert isinstance(
        source,
        NexusBackfillSource,
    )

    snapshot = source.load_snapshot()

    users = {
        user.user_id: user
        for user in snapshot.users
    }

    assert set(users) == {
        "user-1",
        "user-2",
        "user-directory",
    }

    assert (
        users["user-1"].email
        == "uno@jep.gov.co"
    )

    assert (
        users["user-1"].full_name
        == "Usuario Uno"
    )

    # user-2 existe estructuralmente en proyectos,
    # aunque todavía no tenga perfil memory_users.
    assert users["user-2"].email is None
    assert users["user-2"].full_name is None
    assert users["user-2"].status is None

    assert len(snapshot.units) == 1

    assert (
        snapshot.units[0].unit_id
        == "unit-1"
    )

    assert (
        len(
            snapshot.user_unit_memberships
        )
        == 1
    )

    assert len(snapshot.projects) == 2
    assert len(snapshot.project_memberships) == 2

    assert len(snapshot.annotated_pages) == 1

    annotated_page = (
        snapshot.annotated_pages[0]
    )

    assert (
        annotated_page.project_id
        == "project-1"
    )

    assert (
        annotated_page.doc_id
        == "doc-1"
    )

    assert annotated_page.page_idx == 4
    assert annotated_page.page_num == 5

    assert (
        annotated_page.document_label
        == "Documento Uno.pdf"
    )

    assert (
        annotated_page.annotation_count
        == 2
    )

    # El adaptador no debe requerir acceso privilegiado
    # directo al esquema auth.
    assert (
        "auth.users"
        not in client.requested_tables
    )


def test_supabase_source_paginates_complete_tables():
    tables = _empty_tables()

    tables["memory_users"] = [
        {
            "user_id": "user-1",
            "email": "uno@jep.gov.co",
            "full_name": "Usuario Uno",
            "functional_role": None,
            "status": "active",
        },
        {
            "user_id": "user-2",
            "email": "dos@jep.gov.co",
            "full_name": "Usuario Dos",
            "functional_role": None,
            "status": "active",
        },
        {
            "user_id": "user-3",
            "email": "tres@jep.gov.co",
            "full_name": "Usuario Tres",
            "functional_role": None,
            "status": "active",
        },
    ]

    source = SupabaseNexusBackfillSource(
        FakeClient(tables),
        page_size=2,
    )

    snapshot = source.load_snapshot()

    assert [
        user.user_id
        for user in snapshot.users
    ] == [
        "user-1",
        "user-2",
        "user-3",
    ]
