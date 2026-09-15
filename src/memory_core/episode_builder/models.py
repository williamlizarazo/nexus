from __future__ import annotations

from dataclasses import dataclass, field

from memory_core.domain.episode import ResearchEpisode
from memory_core.domain.episode_edge import ResearchEpisodeEdge
from memory_core.domain.episode_item import ResearchEpisodeItem
from memory_core.domain.research_activity import ResearchActivity
from memory_core.domain.research_annotation import ResearchAnnotation
from memory_core.domain.research_search import ResearchSearch
from memory_core.domain.research_search_result import ResearchSearchResult


@dataclass(slots=True)
class SearchBranch:
    search: ResearchSearch

    results: list[ResearchSearchResult] = field(default_factory=list)
    annotations: list[ResearchAnnotation] = field(default_factory=list)
    activities: list[ResearchActivity] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class BranchRelation:
    source_search_id: str
    target_search_id: str

    relation_type: str
    merge_episode: bool
    score: float

    evidence: dict = field(default_factory=dict)


@dataclass(slots=True)
class EpisodeDraft:
    episode: ResearchEpisode
    items: list[ResearchEpisodeItem] = field(default_factory=list)
    edges: list[ResearchEpisodeEdge] = field(default_factory=list)
    search_ids: list[str] = field(default_factory=list)
