from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from memory_core.domain.episode import ResearchEpisode
from memory_core.domain.episode_edge import ResearchEpisodeEdge
from memory_core.domain.episode_item import ResearchEpisodeItem
from memory_core.domain.research_activity import ResearchActivity
from memory_core.domain.research_annotation import ResearchAnnotation
from memory_core.domain.research_search import ResearchSearch
from memory_core.domain.research_search_result import ResearchSearchResult
from memory_core.episode_builder.models import EpisodeDraft, SearchBranch
from memory_core.episode_builder.rules import build_branch_relations


GROUPING_VERSION = "episodic_v1"


class _UnionFind:
    def __init__(self, values: list[str]):
        self.parent = {value: value for value in values}

    def find(self, value: str) -> str:
        parent = self.parent[value]

        if parent != value:
            self.parent[value] = self.find(parent)

        return self.parent[value]

    def union(self, left: str, right: str) -> None:
        root_left = self.find(left)
        root_right = self.find(right)

        if root_left != root_right:
            self.parent[root_right] = root_left


def _episode_id(project_id: str, anchor_search_id: str) -> str:
    return str(
        uuid5(
            NAMESPACE_URL,
            (
                f"memory-core:episode:{GROUPING_VERSION}:"
                f"{project_id}:{anchor_search_id}"
            ),
        )
    )


def _item_id(episode_id: str, source_type: str, source_id: str) -> str:
    return str(
        uuid5(
            NAMESPACE_URL,
            f"memory-core:item:{episode_id}:{source_type}:{source_id}",
        )
    )


def _edge_id(
    episode_id: str,
    source_item_id: str,
    target_item_id: str,
    relation_type: str,
) -> str:
    return str(
        uuid5(
            NAMESPACE_URL,
            (
                f"memory-core:edge:{episode_id}:{source_item_id}:"
                f"{target_item_id}:{relation_type}"
            ),
        )
    )


def _sort_search(search: ResearchSearch):
    return (
        search.created_at or datetime.min.replace(tzinfo=timezone.utc),
        search.search_id,
    )


class DeterministicEpisodeBuilder:
    def build(
        self,
        *,
        project_id: str,
        searches: list[ResearchSearch],
        search_results: list[ResearchSearchResult],
        annotations: list[ResearchAnnotation],
        activities: list[ResearchActivity],
    ) -> list[EpisodeDraft]:
        project_searches = [
            item for item in searches if item.project_id == project_id
        ]

        if not project_searches:
            return []

        results_by_trace = defaultdict(list)
        annotations_by_trace = defaultdict(list)
        activities_by_trace = defaultdict(list)

        for item in search_results:
            if item.project_id == project_id and item.trace_id:
                results_by_trace[item.trace_id].append(item)

        for item in annotations:
            if item.project_id == project_id and item.trace_id:
                annotations_by_trace[item.trace_id].append(item)

        for item in activities:
            if item.project_id == project_id and item.trace_id:
                activities_by_trace[item.trace_id].append(item)

        branches: list[SearchBranch] = []

        for search in project_searches:
            trace_id = search.trace_id
            branches.append(
                SearchBranch(
                    search=search,
                    results=(
                        list(results_by_trace.get(trace_id, []))
                        if trace_id
                        else []
                    ),
                    annotations=(
                        list(annotations_by_trace.get(trace_id, []))
                        if trace_id
                        else []
                    ),
                    activities=(
                        list(activities_by_trace.get(trace_id, []))
                        if trace_id
                        else []
                    ),
                )
            )

        relations = build_branch_relations(branches)

        search_ids = [branch.search.search_id for branch in branches]
        union = _UnionFind(search_ids)

        for relation in relations:
            if relation.merge_episode:
                union.union(
                    relation.source_search_id,
                    relation.target_search_id,
                )

        branches_by_component = defaultdict(list)

        for branch in branches:
            root = union.find(branch.search.search_id)
            branches_by_component[root].append(branch)

        relations_by_component = defaultdict(list)

        for relation in relations:
            left_root = union.find(relation.source_search_id)
            right_root = union.find(relation.target_search_id)

            if left_root == right_root:
                relations_by_component[left_root].append(relation)

        drafts: list[EpisodeDraft] = []

        for root, component_branches in branches_by_component.items():
            component_branches.sort(key=lambda branch: _sort_search(branch.search))
            anchor = component_branches[0].search
            episode_id = _episode_id(project_id, anchor.search_id)

            times: list[datetime] = []
            actors = {
                branch.search.created_by
                for branch in component_branches
                if branch.search.created_by
            }

            episode_items: dict[tuple[str, str], ResearchEpisodeItem] = {}
            search_item_ids: dict[str, str] = {}

            for branch in component_branches:
                search = branch.search

                if search.created_at:
                    times.append(search.created_at)

                item_id = _item_id(episode_id, "search", search.search_id)
                search_item_ids[search.search_id] = item_id
                episode_items[("search", search.search_id)] = ResearchEpisodeItem(
                    item_id=item_id,
                    episode_id=episode_id,
                    source_type="search",
                    source_id=search.search_id,
                    role="exploration",
                    occurred_at=search.created_at,
                    membership_method="deterministic",
                    membership_reason="search_branch",
                    membership_score=1.0,
                )

            extra_edges: list[ResearchEpisodeEdge] = []

            for branch in component_branches:
                search = branch.search
                search_item_id = search_item_ids[search.search_id]

                for annotation in branch.annotations:
                    if annotation.created_at:
                        times.append(annotation.created_at)

                    item_id = _item_id(
                        episode_id,
                        "annotation",
                        annotation.annotation_id,
                    )
                    key = ("annotation", annotation.annotation_id)

                    if key not in episode_items:
                        role = (
                            "finding"
                            if annotation.annotation_type == "finding"
                            else "analysis"
                        )
                        episode_items[key] = ResearchEpisodeItem(
                            item_id=item_id,
                            episode_id=episode_id,
                            source_type="annotation",
                            source_id=annotation.annotation_id,
                            role=role,
                            occurred_at=annotation.created_at,
                            membership_method="deterministic",
                            membership_reason="same_trace",
                            membership_score=1.0,
                        )

                    extra_edges.append(
                        ResearchEpisodeEdge(
                            edge_id=_edge_id(
                                episode_id,
                                search_item_id,
                                item_id,
                                "annotation_from_search",
                            ),
                            episode_id=episode_id,
                            source_item_id=search_item_id,
                            target_item_id=item_id,
                            relation_type="annotation_from_search",
                            relation_score=1.0,
                            rule_version=GROUPING_VERSION,
                            evidence={"trace_id": search.trace_id},
                        )
                    )

                for activity in branch.activities:
                    if activity.created_at:
                        times.append(activity.created_at)

                    item_id = _item_id(episode_id, "activity", activity.id)
                    key = ("activity", activity.id)

                    if key not in episode_items:
                        episode_items[key] = ResearchEpisodeItem(
                            item_id=item_id,
                            episode_id=episode_id,
                            source_type="activity",
                            source_id=activity.id,
                            role="activity",
                            occurred_at=activity.created_at,
                            membership_method="deterministic",
                            membership_reason="same_trace",
                            membership_score=1.0,
                        )

                    extra_edges.append(
                        ResearchEpisodeEdge(
                            edge_id=_edge_id(
                                episode_id,
                                search_item_id,
                                item_id,
                                "same_trace",
                            ),
                            episode_id=episode_id,
                            source_item_id=search_item_id,
                            target_item_id=item_id,
                            relation_type="same_trace",
                            relation_score=1.0,
                            rule_version=GROUPING_VERSION,
                            evidence={
                                "trace_id": search.trace_id,
                                "activity_type": activity.activity_type,
                            },
                        )
                    )

            relation_edges: list[ResearchEpisodeEdge] = []

            for relation in relations_by_component[root]:
                source_item_id = search_item_ids[relation.source_search_id]
                target_item_id = search_item_ids[relation.target_search_id]
                relation_edges.append(
                    ResearchEpisodeEdge(
                        edge_id=_edge_id(
                            episode_id,
                            source_item_id,
                            target_item_id,
                            relation.relation_type,
                        ),
                        episode_id=episode_id,
                        source_item_id=source_item_id,
                        target_item_id=target_item_id,
                        relation_type=relation.relation_type,
                        relation_score=relation.score,
                        rule_version=GROUPING_VERSION,
                        evidence=relation.evidence,
                    )
                )

            started_at = min(times) if times else anchor.created_at
            ended_at = max(times) if times else anchor.created_at

            episode = ResearchEpisode(
                episode_id=episode_id,
                scope_type="project",
                scope_id=project_id,
                actor_id=next(iter(actors)) if len(actors) == 1 else None,
                started_at=started_at,
                ended_at=ended_at,
                status="provisional",
                grouping_version=GROUPING_VERSION,
                metadata={
                    "builder": "deterministic",
                    "search_count": len(component_branches),
                },
            )

            drafts.append(
                EpisodeDraft(
                    episode=episode,
                    items=list(episode_items.values()),
                    edges=relation_edges + extra_edges,
                    search_ids=[
                        branch.search.search_id for branch in component_branches
                    ],
                )
            )

        drafts.sort(key=lambda draft: draft.episode.started_at)
        return drafts
