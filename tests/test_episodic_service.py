from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from core.dependencies import AppDependencies
from services.episodic_service import EpisodicService


def dt(hour: int):
    return datetime(
        2026,
        9,
        15,
        hour,
        0,
        tzinfo=timezone.utc,
    )


class FakeEpisodeRepository:
    def __init__(self):
        self.episodes = [
            SimpleNamespace(
                episode_id="episode-001",
                scope_type="project",
                scope_id="project-001",
                actor_id="actor-001",
                started_at=dt(10),
                ended_at=dt(11),
                status="provisional",
            ),
            SimpleNamespace(
                episode_id="episode-002",
                scope_type="project",
                scope_id="project-001",
                actor_id="actor-001",
                started_at=dt(12),
                ended_at=dt(13),
                status="provisional",
            ),
            SimpleNamespace(
                episode_id="episode-003",
                scope_type="project",
                scope_id="project-002",
                actor_id="actor-002",
                started_at=dt(14),
                ended_at=dt(15),
                status="provisional",
            ),
        ]

        self.items = {
            "episode-001": [
                SimpleNamespace(
                    item_id="item-search",
                    episode_id="episode-001",
                    source_type="search",
                    source_id="search-001",
                    role="exploration",
                    occurred_at=dt(10),
                    membership_method="seed",
                    membership_reason="search_seed",
                    membership_score=1.0,
                    metadata={},
                ),
                SimpleNamespace(
                    item_id="item-annotation",
                    episode_id="episode-001",
                    source_type="annotation",
                    source_id="annotation-001",
                    role="finding",
                    occurred_at=dt(11),
                    membership_method="same_trace",
                    membership_reason="same trace",
                    membership_score=1.0,
                    metadata={},
                ),
            ],
            "episode-002": [],
            "episode-003": [],
        }

        self.edges = {
            "episode-001": [
                SimpleNamespace(
                    edge_id="edge-001",
                    episode_id="episode-001",
                    source_item_id="item-search",
                    target_item_id="item-annotation",
                    relation_type="same_trace",
                    relation_score=1.0,
                    evidence={"trace_id": "trace-001"},
                    rule_version="v1",
                    metadata={},
                )
            ],
            "episode-002": [],
            "episode-003": [],
        }

    def list_episodes(
        self,
        scope_type=None,
        scope_id=None,
        actor_id=None,
        status=None,
        limit=500,
    ):
        result = self.episodes

        if scope_type:
            result = [
                item
                for item in result
                if item.scope_type == scope_type
            ]

        if scope_id:
            result = [
                item
                for item in result
                if item.scope_id == scope_id
            ]

        return result[:limit]

    def get_episode(self, episode_id):
        return next(
            (
                item
                for item in self.episodes
                if item.episode_id == episode_id
            ),
            None,
        )

    def list_items(self, episode_id):
        return self.items.get(episode_id, [])

    def list_edges(self, episode_id):
        return self.edges.get(episode_id, [])


class FakeResearchActivitySource:
    def list_searches(
        self,
        project_id=None,
        trace_id=None,
        limit=500,
    ):
        return [
            SimpleNamespace(
                search_id="search-001",
                original_query="FARC AND CASANARE",
                search_type="bm25",
                trace_id="trace-001",
            )
        ]

    def list_annotations(
        self,
        project_id=None,
        trace_id=None,
        limit=500,
    ):
        return [
            SimpleNamespace(
                annotation_id="annotation-001",
                annotation_type="finding",
                body="Hallazgo relevante",
                selected_text="Fragmento documental",
                trace_id="trace-001",
            )
        ]

    def list_activities(
        self,
        project_id=None,
        trace_id=None,
        limit=500,
    ):
        return []


def make_service():
    return EpisodicService(
        AppDependencies(
            episode_repository=FakeEpisodeRepository(),
            research_activity_source=(
                FakeResearchActivitySource()
            ),
        )
    )


def test_list_projects_is_derived_from_episodes():
    service = make_service()

    projects = service.list_projects()

    assert len(projects) == 2

    assert projects[0].project_id == "project-001"
    assert projects[0].episode_count == 2

    assert projects[1].project_id == "project-002"
    assert projects[1].episode_count == 1


def test_list_episodes_returns_counts():
    service = make_service()

    episodes = service.list_episodes(
        "project-001"
    )

    assert len(episodes) == 2

    first = episodes[0]

    assert first.episode_id == "episode-001"
    assert first.item_count == 2
    assert first.edge_count == 1
    assert first.search_count == 1


def test_get_episode_detail_enriches_sources():
    service = make_service()

    detail = service.get_episode_detail(
        "episode-001"
    )

    assert detail is not None

    assert len(detail.items) == 2
    assert len(detail.edges) == 1

    search_item = detail.items[0]

    assert search_item.source_type == "search"
    assert search_item.source_label == (
        "FARC AND CASANARE"
    )

    annotation_item = detail.items[1]

    assert annotation_item.source_type == "annotation"
    assert annotation_item.source_label == (
        "Hallazgo relevante"
    )

    assert (
        detail.edges[0].relation_type
        == "same_trace"
    )
