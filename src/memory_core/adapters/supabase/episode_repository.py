from __future__ import annotations

from datetime import datetime

from supabase import Client

from memory_core.domain.episode import ResearchEpisode
from memory_core.domain.episode_analysis import ResearchEpisodeAnalysis
from memory_core.domain.episode_edge import ResearchEpisodeEdge
from memory_core.domain.episode_item import ResearchEpisodeItem


def _datetime_to_str(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _str_to_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


class SupabaseEpisodeRepository:
    def __init__(self, client: Client):
        self.client = client

    # ============================================================
    # EPISODES
    # ============================================================

    def save_episode(
        self,
        episode: ResearchEpisode,
    ) -> ResearchEpisode:

        payload = {
            "episode_id": episode.episode_id,
            "scope_type": episode.scope_type,
            "scope_id": episode.scope_id,
            "actor_id": episode.actor_id,
            "started_at": _datetime_to_str(episode.started_at),
            "ended_at": _datetime_to_str(episode.ended_at),
            "status": episode.status,
            "grouping_version": episode.grouping_version,
            "schema_version": episode.schema_version,
            "metadata_json": episode.metadata,
            "created_at": _datetime_to_str(episode.created_at),
            "updated_at": _datetime_to_str(episode.updated_at),
        }

        (
            self.client
            .table("research_episodes")
            .upsert(payload)
            .execute()
        )

        return episode

    def get_episode(
        self,
        episode_id: str,
    ) -> ResearchEpisode | None:

        response = (
            self.client
            .table("research_episodes")
            .select("*")
            .eq("episode_id", episode_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        row = response.data[0]

        return ResearchEpisode(
            episode_id=row["episode_id"],
            scope_type=row["scope_type"],
            scope_id=row["scope_id"],
            actor_id=row.get("actor_id"),
            started_at=_str_to_datetime(row["started_at"]),
            ended_at=_str_to_datetime(row.get("ended_at")),
            status=row["status"],
            grouping_version=row["grouping_version"],
            schema_version=row["schema_version"],
            metadata=row.get("metadata_json") or {},
            created_at=_str_to_datetime(row["created_at"]),
            updated_at=_str_to_datetime(row["updated_at"]),
        )

    def list_episodes(
        self,
        scope_type: str | None = None,
        scope_id: str | None = None,
        actor_id: str | None = None,
        status: str | None = None,
        limit: int = 500,
    ) -> list[ResearchEpisode]:

        query = (
            self.client
            .table("research_episodes")
            .select("*")
        )

        if scope_type:
            query = query.eq("scope_type", scope_type)

        if scope_id:
            query = query.eq("scope_id", scope_id)

        if actor_id:
            query = query.eq("actor_id", actor_id)

        if status:
            query = query.eq("status", status)

        response = (
            query
            .order("started_at", desc=True)
            .limit(limit)
            .execute()
        )

        return [
            ResearchEpisode(
                episode_id=row["episode_id"],
                scope_type=row["scope_type"],
                scope_id=row["scope_id"],
                actor_id=row.get("actor_id"),
                started_at=_str_to_datetime(
                    row["started_at"]
                ),
                ended_at=_str_to_datetime(
                    row.get("ended_at")
                ),
                status=row["status"],
                grouping_version=row["grouping_version"],
                schema_version=row["schema_version"],
                metadata=row.get("metadata_json") or {},
                created_at=_str_to_datetime(
                    row["created_at"]
                ),
                updated_at=_str_to_datetime(
                    row["updated_at"]
                ),
            )
            for row in response.data
        ]

    # ============================================================
    # ITEMS
    # ============================================================

    def add_item(
        self,
        item: ResearchEpisodeItem,
    ) -> ResearchEpisodeItem:

        payload = {
            "item_id": item.item_id,
            "episode_id": item.episode_id,
            "source_type": item.source_type,
            "source_id": item.source_id,
            "role": item.role,
            "occurred_at": _datetime_to_str(item.occurred_at),
            "membership_method": item.membership_method,
            "membership_reason": item.membership_reason,
            "membership_score": item.membership_score,
            "schema_version": item.schema_version,
            "metadata_json": item.metadata,
            "created_at": _datetime_to_str(item.created_at),
        }

        (
            self.client
            .table("research_episode_items")
            .upsert(
                payload,
                on_conflict="episode_id,source_type,source_id",
            )
            .execute()
        )

        return item

    def list_items(
        self,
        episode_id: str,
    ) -> list[ResearchEpisodeItem]:

        response = (
            self.client
            .table("research_episode_items")
            .select("*")
            .eq("episode_id", episode_id)
            .order("occurred_at")
            .execute()
        )

        return [
            ResearchEpisodeItem(
                item_id=row["item_id"],
                episode_id=row["episode_id"],
                source_type=row["source_type"],
                source_id=row["source_id"],
                role=row.get("role"),
                occurred_at=_str_to_datetime(
                    row.get("occurred_at")
                ),
                membership_method=row["membership_method"],
                membership_reason=row.get("membership_reason"),
                membership_score=row.get("membership_score"),
                schema_version=row["schema_version"],
                metadata=row.get("metadata_json") or {},
                created_at=_str_to_datetime(
                    row["created_at"]
                ),
            )
            for row in response.data
        ]

    # ============================================================
    # EDGES
    # ============================================================

    def add_edge(
        self,
        edge: ResearchEpisodeEdge,
    ) -> ResearchEpisodeEdge:

        payload = {
            "edge_id": edge.edge_id,
            "episode_id": edge.episode_id,
            "source_item_id": edge.source_item_id,
            "target_item_id": edge.target_item_id,
            "relation_type": edge.relation_type,
            "relation_score": edge.relation_score,
            "evidence_json": edge.evidence,
            "rule_version": edge.rule_version,
            "schema_version": edge.schema_version,
            "metadata_json": edge.metadata,
            "created_at": _datetime_to_str(edge.created_at),
        }

        (
            self.client
            .table("research_episode_edges")
            .upsert(payload)
            .execute()
        )

        return edge

    def list_edges(
        self,
        episode_id: str,
    ) -> list[ResearchEpisodeEdge]:

        response = (
            self.client
            .table("research_episode_edges")
            .select("*")
            .eq("episode_id", episode_id)
            .execute()
        )

        return [
            ResearchEpisodeEdge(
                edge_id=row["edge_id"],
                episode_id=row["episode_id"],
                source_item_id=row["source_item_id"],
                target_item_id=row["target_item_id"],
                relation_type=row["relation_type"],
                relation_score=row.get("relation_score"),
                evidence=row.get("evidence_json") or {},
                rule_version=row["rule_version"],
                schema_version=row["schema_version"],
                metadata=row.get("metadata_json") or {},
                created_at=_str_to_datetime(
                    row["created_at"]
                ),
            )
            for row in response.data
        ]

    # ============================================================
    # ANALYSES
    # ============================================================

    def save_analysis(
        self,
        analysis: ResearchEpisodeAnalysis,
    ) -> ResearchEpisodeAnalysis:

        payload = {
            "analysis_id": analysis.analysis_id,
            "episode_id": analysis.episode_id,
            "version": analysis.version,
            "summary": analysis.summary,
            "entities_json": analysis.entities,
            "relations_json": analysis.relations,
            "topics_json": analysis.topics,
            "open_questions_json": analysis.open_questions,
            "contradictions_json": analysis.contradictions,
            "structure_json": analysis.structure,
            "source_fingerprint": analysis.source_fingerprint,
            "provider": analysis.provider,
            "model": analysis.model,
            "prompt_version": analysis.prompt_version,
            "schema_version": analysis.schema_version,
            "metadata_json": analysis.metadata,
            "created_at": _datetime_to_str(
                analysis.created_at
            ),
        }

        (
            self.client
            .table("research_episode_analyses")
            .upsert(
                payload,
                on_conflict="episode_id,version",
            )
            .execute()
        )

        return analysis

    def list_analyses(
        self,
        episode_id: str,
    ) -> list[ResearchEpisodeAnalysis]:

        response = (
            self.client
            .table("research_episode_analyses")
            .select("*")
            .eq("episode_id", episode_id)
            .order("version")
            .execute()
        )

        return [
            ResearchEpisodeAnalysis(
                analysis_id=row["analysis_id"],
                episode_id=row["episode_id"],
                version=row["version"],
                summary=row.get("summary"),
                entities=row.get("entities_json") or [],
                relations=row.get("relations_json") or [],
                topics=row.get("topics_json") or [],
                open_questions=row.get(
                    "open_questions_json"
                ) or [],
                contradictions=row.get(
                    "contradictions_json"
                ) or [],
                structure=row.get("structure_json") or {},
                source_fingerprint=row.get(
                    "source_fingerprint"
                ),
                provider=row.get("provider"),
                model=row.get("model"),
                prompt_version=row.get("prompt_version"),
                schema_version=row["schema_version"],
                metadata=row.get("metadata_json") or {},
                created_at=_str_to_datetime(
                    row["created_at"]
                ),
            )
            for row in response.data
        ]
