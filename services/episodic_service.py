from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.dependencies import AppDependencies


@dataclass(frozen=True, slots=True)
class ProjectSummary:
    project_id: str
    episode_count: int
    latest_started_at: datetime | None


@dataclass(frozen=True, slots=True)
class EpisodeSummary:
    episode_id: str
    project_id: str
    actor_id: str | None
    started_at: datetime | None
    ended_at: datetime | None
    status: str
    search_count: int
    item_count: int
    edge_count: int


@dataclass(frozen=True, slots=True)
class EpisodeItemView:
    item_id: str
    source_type: str
    source_id: str
    role: str | None
    occurred_at: datetime | None
    membership_method: str
    membership_reason: str | None
    membership_score: float | None
    source_label: str
    source_detail: str | None


@dataclass(frozen=True, slots=True)
class EpisodeEdgeView:
    edge_id: str
    source_item_id: str
    target_item_id: str
    relation_type: str
    relation_score: float | None
    evidence: dict[str, Any]


@dataclass(frozen=True, slots=True)
class EpisodeDetail:
    summary: EpisodeSummary
    items: tuple[EpisodeItemView, ...]
    edges: tuple[EpisodeEdgeView, ...]


class EpisodicService:
    def __init__(
        self,
        dependencies: AppDependencies,
    ) -> None:
        self._dependencies = dependencies

    @property
    def repository_available(self) -> bool:
        return (
            self._dependencies.episode_repository
            is not None
        )

    @property
    def activity_source_available(self) -> bool:
        return (
            self._dependencies.research_activity_source
            is not None
        )

    def status_message(self) -> str:
        if self.repository_available:
            return (
                "Repositorio episódico disponible."
            )

        return (
            "Módulo episódico activo. "
            "Repositorio todavía no conectado."
        )

    def list_projects(
        self,
    ) -> list[ProjectSummary]:
        repository = (
            self._dependencies.episode_repository
        )

        if repository is None:
            return []

        episodes = repository.list_episodes(
            scope_type="project",
            limit=5000,
        )

        grouped: dict[str, list[Any]] = {}

        for episode in episodes:
            grouped.setdefault(
                episode.scope_id,
                [],
            ).append(episode)

        projects: list[ProjectSummary] = []

        for project_id, project_episodes in (
            grouped.items()
        ):
            started_values = [
                episode.started_at
                for episode in project_episodes
                if episode.started_at is not None
            ]

            latest = (
                max(started_values)
                if started_values
                else None
            )

            projects.append(
                ProjectSummary(
                    project_id=project_id,
                    episode_count=len(
                        project_episodes
                    ),
                    latest_started_at=latest,
                )
            )

        return projects

    def list_episodes(
        self,
        project_id: str,
    ) -> list[EpisodeSummary]:
        repository = (
            self._dependencies.episode_repository
        )

        if repository is None:
            return []

        episodes = repository.list_episodes(
            scope_type="project",
            scope_id=project_id,
            limit=500,
        )

        result: list[EpisodeSummary] = []

        for episode in episodes:
            items = repository.list_items(
                episode.episode_id
            )
            edges = repository.list_edges(
                episode.episode_id
            )

            result.append(
                self._build_summary(
                    episode,
                    items,
                    edges,
                )
            )

        return result

    def get_episode_detail(
        self,
        episode_id: str,
    ) -> EpisodeDetail | None:
        repository = (
            self._dependencies.episode_repository
        )

        if repository is None:
            return None

        episode = repository.get_episode(
            episode_id
        )

        if episode is None:
            return None

        items = repository.list_items(
            episode_id
        )
        edges = repository.list_edges(
            episode_id
        )

        source_indexes = (
            self._load_source_indexes(
                episode.scope_id
            )
        )

        item_views = tuple(
            self._build_item_view(
                item,
                source_indexes,
            )
            for item in items
        )

        edge_views = tuple(
            EpisodeEdgeView(
                edge_id=edge.edge_id,
                source_item_id=(
                    edge.source_item_id
                ),
                target_item_id=(
                    edge.target_item_id
                ),
                relation_type=(
                    edge.relation_type
                ),
                relation_score=(
                    edge.relation_score
                ),
                evidence=edge.evidence,
            )
            for edge in edges
        )

        return EpisodeDetail(
            summary=self._build_summary(
                episode,
                items,
                edges,
            ),
            items=item_views,
            edges=edge_views,
        )

    def _build_summary(
        self,
        episode: Any,
        items: list[Any],
        edges: list[Any],
    ) -> EpisodeSummary:
        return EpisodeSummary(
            episode_id=episode.episode_id,
            project_id=episode.scope_id,
            actor_id=episode.actor_id,
            started_at=episode.started_at,
            ended_at=episode.ended_at,
            status=episode.status,
            search_count=sum(
                1
                for item in items
                if item.source_type == "search"
            ),
            item_count=len(items),
            edge_count=len(edges),
        )

    def _load_source_indexes(
        self,
        project_id: str,
    ) -> dict[str, dict[str, Any]]:
        source = (
            self._dependencies.research_activity_source
        )

        indexes: dict[
            str,
            dict[str, Any],
        ] = {
            "search": {},
            "annotation": {},
            "activity": {},
        }

        if source is None:
            return indexes

        for search in source.list_searches(
            project_id=project_id,
            limit=5000,
        ):
            indexes["search"][
                search.search_id
            ] = search

        for annotation in (
            source.list_annotations(
                project_id=project_id,
                limit=5000,
            )
        ):
            indexes["annotation"][
                annotation.annotation_id
            ] = annotation

        for activity in source.list_activities(
            project_id=project_id,
            limit=5000,
        ):
            activity_id = getattr(
                activity,
                "activity_id",
                None,
            )

            row_id = getattr(
                activity,
                "id",
                None,
            )

            if activity_id:
                indexes["activity"][
                    str(activity_id)
                ] = activity

            if row_id:
                indexes["activity"][
                    str(row_id)
                ] = activity

        return indexes

    def _build_item_view(
        self,
        item: Any,
        indexes: dict[
            str,
            dict[str, Any],
        ],
    ) -> EpisodeItemView:
        source = indexes.get(
            item.source_type,
            {},
        ).get(item.source_id)

        label = item.source_id
        detail: str | None = None

        if (
            item.source_type == "search"
            and source is not None
        ):
            label = (
                source.original_query
                or item.source_id
            )
            detail = getattr(
                source,
                "search_type",
                None,
            )

        elif (
            item.source_type == "annotation"
            and source is not None
        ):
            label = (
                getattr(source, "body", None)
                or getattr(
                    source,
                    "selected_text",
                    None,
                )
                or item.source_id
            )

            detail = getattr(
                source,
                "annotation_type",
                None,
            )

        elif (
            item.source_type == "activity"
            and source is not None
        ):
            label = (
                getattr(
                    source,
                    "description",
                    None,
                )
                or getattr(
                    source,
                    "activity_type",
                    None,
                )
                or item.source_id
            )

            detail = getattr(
                source,
                "activity_type",
                None,
            )

        return EpisodeItemView(
            item_id=item.item_id,
            source_type=item.source_type,
            source_id=item.source_id,
            role=item.role,
            occurred_at=item.occurred_at,
            membership_method=(
                item.membership_method
            ),
            membership_reason=(
                item.membership_reason
            ),
            membership_score=(
                item.membership_score
            ),
            source_label=str(label),
            source_detail=detail,
        )
