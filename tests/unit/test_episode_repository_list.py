from __future__ import annotations

from types import SimpleNamespace

from memory_core.adapters.supabase.episode_repository import (
    SupabaseEpisodeRepository,
)


class FakeQuery:
    def __init__(self, rows: list[dict]):
        self.rows = rows
        self.filters: list[tuple[str, object]] = []
        self.order_field: str | None = None
        self.order_desc = False
        self.limit_value: int | None = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, field: str, value: object):
        self.filters.append((field, value))
        return self

    def order(
        self,
        field: str,
        desc: bool = False,
    ):
        self.order_field = field
        self.order_desc = desc
        return self

    def limit(self, value: int):
        self.limit_value = value
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


class FakeClient:
    def __init__(self, rows: list[dict]):
        self.query = FakeQuery(rows)
        self.table_name: str | None = None

    def table(self, name: str):
        self.table_name = name
        return self.query


def test_list_episodes_filters_by_scope_and_status():
    rows = [
        {
            "episode_id": "episode-001",
            "scope_type": "project",
            "scope_id": "project-001",
            "actor_id": "actor-001",
            "started_at": "2026-09-15T10:00:00+00:00",
            "ended_at": "2026-09-15T11:00:00+00:00",
            "status": "provisional",
            "grouping_version": "v1",
            "schema_version": "1",
            "metadata_json": {},
            "created_at": "2026-09-15T10:00:00+00:00",
            "updated_at": "2026-09-15T11:00:00+00:00",
        }
    ]

    client = FakeClient(rows)
    repository = SupabaseEpisodeRepository(client)

    episodes = repository.list_episodes(
        scope_type="project",
        scope_id="project-001",
        status="provisional",
        limit=50,
    )

    assert len(episodes) == 1

    episode = episodes[0]

    assert episode.episode_id == "episode-001"
    assert episode.scope_type == "project"
    assert episode.scope_id == "project-001"
    assert episode.status == "provisional"

    assert client.table_name == "research_episodes"

    assert client.query.filters == [
        ("scope_type", "project"),
        ("scope_id", "project-001"),
        ("status", "provisional"),
    ]

    assert client.query.limit_value == 50
