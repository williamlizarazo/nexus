from types import SimpleNamespace

from memory_core.adapters.supabase.research_project_source import (
    SupabaseResearchProjectSource,
)


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.filters = []
        self.requested_limit = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, field, value):
        self.filters.append(("eq", field, value))
        return self

    def neq(self, field, value):
        self.filters.append(("neq", field, value))
        return self

    def is_(self, field, value):
        self.filters.append(("is", field, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, value):
        self.requested_limit = value
        return self

    def execute(self):
        result = list(self.rows)

        for operation, field, value in self.filters:
            if operation == "eq":
                result = [row for row in result if row.get(field) == value]
            elif operation == "neq":
                result = [row for row in result if row.get(field) != value]
            elif operation == "is" and value == "null":
                result = [row for row in result if row.get(field) is None]

        if self.requested_limit is not None:
            result = result[: self.requested_limit]

        return SimpleNamespace(data=result)


class FakeSupabaseClient:
    def __init__(self, rows):
        self.query = FakeQuery(rows)

    def table(self, table_name):
        assert table_name == "analysis_projects"
        return self.query


def test_source_lists_active_projects_for_owner():
    client = FakeSupabaseClient(
        [
            {
                "id": "project-1",
                "owner_user_id": "user-1",
                "name": "Proyecto uno",
                "description": "Descripción",
                "tags": ["justicia", "memoria"],
                "status": "active",
                "created_at": "2026-09-17T14:00:00Z",
                "updated_at": "2026-09-17T15:00:00+00:00",
                "deleted_at": None,
            },
            {
                "id": "project-2",
                "owner_user_id": "user-2",
                "name": "Otro proyecto",
                "status": "active",
                "deleted_at": None,
            },
        ]
    )

    projects = SupabaseResearchProjectSource(client).list_projects(
        owner_user_id=" user-1 ",
        limit=100,
    )

    assert [project.project_id for project in projects] == ["project-1"]
    assert projects[0].owner_user_id == "user-1"
    assert projects[0].tags == ("justicia", "memoria")
    assert projects[0].created_at.isoformat() == "2026-09-17T14:00:00+00:00"
    assert ("neq", "status", "archived") in client.query.filters
    assert ("is", "deleted_at", "null") in client.query.filters


def test_source_returns_none_when_project_does_not_exist():
    source = SupabaseResearchProjectSource(FakeSupabaseClient([]))

    assert source.get_project("missing") is None
