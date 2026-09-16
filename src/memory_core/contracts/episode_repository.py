from __future__ import annotations

from typing import Protocol

from memory_core.domain.episode import ResearchEpisode
from memory_core.domain.episode_analysis import ResearchEpisodeAnalysis
from memory_core.domain.episode_edge import ResearchEpisodeEdge
from memory_core.domain.episode_item import ResearchEpisodeItem


class EpisodeRepository(Protocol):
    def save_episode(
        self,
        episode: ResearchEpisode,
    ) -> ResearchEpisode:
        ...

    def get_episode(
        self,
        episode_id: str,
    ) -> ResearchEpisode | None:
        ...

    def list_episodes(
        self,
        scope_type: str | None = None,
        scope_id: str | None = None,
        actor_id: str | None = None,
        status: str | None = None,
        limit: int = 500,
    ) -> list[ResearchEpisode]:
        ...

    def add_item(
        self,
        item: ResearchEpisodeItem,
    ) -> ResearchEpisodeItem:
        ...

    def list_items(
        self,
        episode_id: str,
    ) -> list[ResearchEpisodeItem]:
        ...

    def add_edge(
        self,
        edge: ResearchEpisodeEdge,
    ) -> ResearchEpisodeEdge:
        ...

    def list_edges(
        self,
        episode_id: str,
    ) -> list[ResearchEpisodeEdge]:
        ...

    def save_analysis(
        self,
        analysis: ResearchEpisodeAnalysis,
    ) -> ResearchEpisodeAnalysis:
        ...

    def list_analyses(
        self,
        episode_id: str,
    ) -> list[ResearchEpisodeAnalysis]:
        ...
