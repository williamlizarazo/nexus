from __future__ import annotations

from datetime import datetime

from supabase import Client

from memory_core.domain.research_activity import ResearchActivity
from memory_core.domain.research_annotation import ResearchAnnotation
from memory_core.domain.research_chunk import ResearchChunk
from memory_core.domain.research_document import ResearchDocument
from memory_core.domain.research_page import ResearchPage
from memory_core.domain.research_search import ResearchSearch
from memory_core.domain.research_search_result import ResearchSearchResult


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None

    return datetime.fromisoformat(
        value.replace("Z", "+00:00")
    )


def _resolve_created_at(
    row: dict,
    *,
    json_field: str,
) -> datetime | None:
    payload = row.get(json_field) or {}

    if isinstance(payload, dict):
        original_created_at = payload.get(
            "created_at"
        )

        if original_created_at:
            return _parse_datetime(
                original_created_at
            )

    return _parse_datetime(
        row.get("created_at")
    )


class SupabaseResearchActivitySource:

    def __init__(self, client: Client):
        self.client = client

    # ============================================================
    # SEARCHES
    # ============================================================

    def get_search(
        self,
        search_id: str,
    ) -> ResearchSearch | None:

        response = (
            self.client
            .table("analysis_project_searches")
            .select("*")
            .eq("id", search_id)
            .limit(1)
            .execute()
        )

        if not response.data:
            return None

        return self._map_search(response.data[0])

    def list_searches(
        self,
        project_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 500,
    ) -> list[ResearchSearch]:

        query = (
            self.client
            .table("analysis_project_searches")
            .select("*")
        )

        if project_id:
            query = query.eq("project_id", project_id)

        if trace_id:
            query = query.eq("trace_id", trace_id)

        response = (
            query
            .order("created_at")
            .limit(limit)
            .execute()
        )

        return [
            self._map_search(row)
            for row in response.data
        ]

    # ============================================================
    # ANNOTATIONS
    # ============================================================

    def list_annotations(
        self,
        project_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 500,
    ) -> list[ResearchAnnotation]:

        query = (
            self.client
            .table("analysis_project_annotations")
            .select("*")
        )

        if project_id:
            query = query.eq("project_id", project_id)

        if trace_id:
            query = query.eq("trace_id", trace_id)

        response = (
            query
            .order("created_at")
            .limit(limit)
            .execute()
        )

        return [
            self._map_annotation(row)
            for row in response.data
        ]

    # ============================================================
    # MAPPERS
    # ============================================================

    @staticmethod
    def _map_search(row: dict) -> ResearchSearch:

        return ResearchSearch(
            search_id=str(row["id"]),
            project_id=str(row["project_id"]),
            created_by=(
                str(row["created_by"])
                if row.get("created_by")
                else None
            ),
            trace_id=row.get("trace_id"),
            search_type=row["search_type"],
            original_query=row["original_query"],
            executed_query=row.get("executed_query"),
            query_source=row.get("query_source"),
            status=row.get("status"),
            result_count=row.get("result_count"),
            elapsed_ms=row.get("elapsed_ms"),
            payload=row.get("payload_json") or {},
            created_at=_resolve_created_at(
                row,
                json_field="payload_json",
            ),
            updated_at=_parse_datetime(
                row.get("updated_at")
            ),
        )

    @staticmethod
    def _map_annotation(row: dict) -> ResearchAnnotation:

        return ResearchAnnotation(
            annotation_id=str(row["id"]),
            project_id=str(row["project_id"]),
            created_by=(
                str(row["created_by"])
                if row.get("created_by")
                else None
            ),
            trace_id=row.get("trace_id"),
            annotation_type=row["annotation_type"],
            body=row.get("body"),
            selected_text=row.get("selected_text"),
            doc_id=(
                str(row["doc_id"])
                if row.get("doc_id")
                else None
            ),
            page_idx=row.get("page_idx"),
            page_num=row.get("page_num"),
            chunk_id=(
                str(row["chunk_id"])
                if row.get("chunk_id")
                else None
            ),
            tags=row.get("tags") or [],
            status=row.get("status"),
            metadata=row.get("metadata_json") or {},
            created_at=_resolve_created_at(
                row,
                json_field="metadata_json",
            ),
            updated_at=_parse_datetime(
                row.get("updated_at")
            ),
            deleted_at=_parse_datetime(
                row.get("deleted_at")
            ),
        )

    # ============================================================
    # ACTIVITIES
    # ============================================================

    def list_activities(
        self,
        project_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 500,
    ) -> list[ResearchActivity]:

        query = (
            self.client
            .table("analysis_project_activities")
            .select("*")
        )

        if project_id:
            query = query.eq("project_id", project_id)

        if trace_id:
            query = query.eq("trace_id", trace_id)

        response = (
            query
            .order("created_at")
            .limit(limit)
            .execute()
        )

        return [
            ResearchActivity(
                id=str(row["id"]),
                project_id=str(row["project_id"]),
                activity_id=str(row["activity_id"]),
                activity_type=row["activity_type"],
                created_by=(
                    str(row["created_by"])
                    if row.get("created_by")
                    else None
                ),
                description=row.get("description"),
                trace_id=row.get("trace_id"),
                document_id=(
                    str(row["document_id"])
                    if row.get("document_id")
                    else None
                ),
                page_key=row.get("page_key"),
                payload=row.get("payload_json") or {},
                created_at=_resolve_created_at(
                    row,
                    json_field="payload_json",
                ),
            )
            for row in response.data
        ]

    # ============================================================
    # SEARCH RESULTS
    # ============================================================

    def list_search_results(
        self,
        project_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 1000,
    ) -> list[ResearchSearchResult]:

        query = (
            self.client
            .table("analysis_project_search_results")
            .select("*")
        )

        if project_id:
            query = query.eq("project_id", project_id)

        if trace_id:
            query = query.eq("trace_id", trace_id)

        response = (
            query
            .order("created_at")
            .limit(limit)
            .execute()
        )

        return [
            ResearchSearchResult(
                result_id=str(row["id"]),
                project_id=str(row["project_id"]),
                trace_id=row["trace_id"],
                result_key=row.get("result_key"),
                doc_id=(
                    str(row["doc_id"])
                    if row.get("doc_id")
                    else None
                ),
                chunk_id=(
                    str(row["chunk_id"])
                    if row.get("chunk_id")
                    else None
                ),
                rank_position=row.get("rank_position"),
                score=row.get("score"),
                page_idx_start=row.get("page_idx_start"),
                page_idx_end=row.get("page_idx_end"),
                page_num_start=row.get("page_num_start"),
                page_num_end=row.get("page_num_end"),
                role=row.get("role"),
                source_number=row.get("source_number"),
                version_number=row.get("version_number"),
                window_role=row.get("window_role"),
                payload=row.get("payload_json") or {},
                created_at=_parse_datetime(
                    row.get("created_at")
                ),
                updated_at=_parse_datetime(
                    row.get("updated_at")
                ),
            )
            for row in response.data
        ]

    # ============================================================
    # DOCUMENTS
    # ============================================================

    def list_documents(
        self,
        project_id: str | None = None,
        limit: int = 1000,
    ) -> list[ResearchDocument]:

        query = (
            self.client
            .table("analysis_project_documents")
            .select("*")
        )

        if project_id:
            query = query.eq("project_id", project_id)

        response = (
            query
            .order("created_at")
            .limit(limit)
            .execute()
        )

        return [
            ResearchDocument(
                document_row_id=str(row["id"]),
                project_id=str(row["project_id"]),
                doc_id=str(row["doc_id"]),
                source_blob=row.get("source_blob"),
                display_name=row.get("display_name"),
                metadata=row.get("metadata_json") or {},
                created_at=_parse_datetime(row.get("created_at")),
                updated_at=_parse_datetime(row.get("updated_at")),
            )
            for row in response.data
        ]

    # ============================================================
    # PAGES
    # ============================================================

    def list_pages(
        self,
        project_id: str | None = None,
        doc_id: str | None = None,
        limit: int = 2000,
    ) -> list[ResearchPage]:

        query = (
            self.client
            .table("analysis_project_pages")
            .select("*")
        )

        if project_id:
            query = query.eq("project_id", project_id)

        if doc_id:
            query = query.eq("doc_id", doc_id)

        response = (
            query
            .order("page_idx")
            .limit(limit)
            .execute()
        )

        return [
            ResearchPage(
                page_id=str(row["id"]),
                project_id=str(row["project_id"]),
                doc_id=str(row["doc_id"]),
                page_idx=row["page_idx"],
                page_num=row.get("page_num"),
                page_text=row.get("page_text"),
                total_block_count=row.get("total_block_count"),
                searchable_block_count=row.get("searchable_block_count"),
                has_searchable_text=row.get("has_searchable_text"),
                metadata=row.get("metadata_json") or {},
                created_at=_parse_datetime(row.get("created_at")),
                updated_at=_parse_datetime(row.get("updated_at")),
            )
            for row in response.data
        ]

    # ============================================================
    # CHUNKS
    # ============================================================

    def list_chunks(
        self,
        project_id: str | None = None,
        doc_id: str | None = None,
        limit: int = 5000,
    ) -> list[ResearchChunk]:

        query = (
            self.client
            .table("analysis_project_chunks")
            .select("*")
        )

        if project_id:
            query = query.eq("project_id", project_id)

        if doc_id:
            query = query.eq("doc_id", doc_id)

        response = (
            query
            .order("created_at")
            .limit(limit)
            .execute()
        )

        return [
            ResearchChunk(
                chunk_row_id=str(row["id"]),
                project_id=str(row["project_id"]),
                chunk_id=str(row["chunk_id"]),
                doc_id=str(row["doc_id"]),
                chunk_text=row.get("chunk_text"),
                page_idx_start=row.get("page_idx_start"),
                page_idx_end=row.get("page_idx_end"),
                page_num_start=row.get("page_num_start"),
                page_num_end=row.get("page_num_end"),
                metadata=row.get("metadata_json") or {},
                created_at=_parse_datetime(row.get("created_at")),
                updated_at=_parse_datetime(row.get("updated_at")),
            )
            for row in response.data
        ]
