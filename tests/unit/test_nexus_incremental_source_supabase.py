from __future__ import annotations

from typing import Any

from memory_core.adapters.supabase.nexus_incremental_source import (
    SupabaseNexusIncrementalSource,
)
from memory_core.domain.nexus_incremental import NexusAffectedScope


class FakeIncrementalSource(SupabaseNexusIncrementalSource):
    def __init__(
        self,
        rows: dict[str, list[dict[str, Any]]],
    ) -> None:
        self.rows = rows
        self.calls = []

    def _fetch_filtered(
        self,
        table_name: str,
        columns: str,
        *,
        order_by: tuple[str, ...] = (),
        filters: tuple[tuple[str, str, Any], ...] = (),
    ) -> list[dict[str, Any]]:
        self.calls.append((table_name, filters))

        rows = list(self.rows.get(table_name, []))

        for operator, column, value in filters:
            if operator == "eq":
                rows = [
                    row
                    for row in rows
                    if row.get(column) == value
                ]

            elif operator == "in":
                allowed = set(value)
                rows = [
                    row
                    for row in rows
                    if row.get(column) in allowed
                ]

            elif operator == "is" and value == "null":
                rows = [
                    row
                    for row in rows
                    if row.get(column) is None
                ]

        return rows


def test_project_scope_loads_project_context():
    source = FakeIncrementalSource(
        {
            "analysis_projects": [
                {
                    "id": "project-1",
                    "owner_user_id": "user-1",
                    "name": "Proyecto uno",
                    "description": None,
                    "status": "active",
                    "deleted_at": None,
                }
            ],
            "analysis_project_members": [
                {
                    "project_id": "project-1",
                    "user_id": "user-1",
                    "role": "owner",
                }
            ],
            "analysis_project_documents": [],
            "analysis_project_pages": [],
            "analysis_project_annotations": [],
            "memory_users": [
                {
                    "user_id": "user-1",
                    "email": "one@example.com",
                    "full_name": "User One",
                    "functional_role": None,
                    "status": "active",
                }
            ],
            "memory_user_unit_memberships": [
                {
                    "user_id": "user-1",
                    "unit_id": "unit-1",
                    "status": "active",
                    "is_primary": True,
                    "valid_from": "2026-01-01",
                    "valid_to": None,
                }
            ],
            "memory_organizational_units": [
                {
                    "unit_id": "unit-1",
                    "name": "Unidad uno",
                    "unit_type": "office",
                    "status": "active",
                }
            ],
        }
    )

    snapshot = source.load_scope(
        scope=NexusAffectedScope(
            project_ids=("project-1",),
        )
    )

    assert tuple(
        item.project_id
        for item in snapshot.projects
    ) == ("project-1",)

    assert tuple(
        item.user_id
        for item in snapshot.users
    ) == ("user-1",)

    assert tuple(
        item.unit_id
        for item in snapshot.units
    ) == ("unit-1",)


def test_user_scope_loads_user_context():
    source = FakeIncrementalSource(
        {
            "analysis_projects": [],
            "analysis_project_members": [],
            "analysis_project_documents": [],
            "analysis_project_pages": [],
            "analysis_project_annotations": [],
            "memory_users": [
                {
                    "user_id": "user-1",
                    "email": "one@example.com",
                    "full_name": "User One",
                    "functional_role": None,
                    "status": "active",
                }
            ],
            "memory_user_unit_memberships": [],
            "memory_organizational_units": [],
        }
    )

    snapshot = source.load_scope(
        scope=NexusAffectedScope(
            user_ids=("user-1",),
        )
    )

    assert tuple(
        item.user_id
        for item in snapshot.users
    ) == ("user-1",)


def test_empty_scope_does_not_query():
    source = FakeIncrementalSource({})

    snapshot = source.load_scope(
        scope=NexusAffectedScope()
    )

    assert snapshot.users == ()
    assert snapshot.projects == ()
    assert snapshot.units == ()
    assert source.calls == []
