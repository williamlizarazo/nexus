from __future__ import annotations

from typing import Protocol

from memory_core.domain.research_activity import ResearchActivity
from memory_core.domain.research_annotation import ResearchAnnotation
from memory_core.domain.research_chunk import ResearchChunk
from memory_core.domain.research_document import ResearchDocument
from memory_core.domain.research_page import ResearchPage
from memory_core.domain.research_search import ResearchSearch
from memory_core.domain.research_search_result import ResearchSearchResult


class ResearchActivitySource(Protocol):

    def get_search(
        self,
        search_id: str,
    ) -> ResearchSearch | None:
        ...

    def list_searches(
        self,
        project_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 500,
    ) -> list[ResearchSearch]:
        ...

    def list_annotations(
        self,
        project_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 500,
    ) -> list[ResearchAnnotation]:
        ...

    def list_activities(
        self,
        project_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 500,
    ) -> list[ResearchActivity]:
        ...

    def list_search_results(
        self,
        project_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 1000,
    ) -> list[ResearchSearchResult]:
        ...

    def list_documents(
        self,
        project_id: str | None = None,
        limit: int = 1000,
    ) -> list[ResearchDocument]:
        ...

    def list_pages(
        self,
        project_id: str | None = None,
        doc_id: str | None = None,
        limit: int = 2000,
    ) -> list[ResearchPage]:
        ...

    def list_chunks(
        self,
        project_id: str | None = None,
        doc_id: str | None = None,
        limit: int = 5000,
    ) -> list[ResearchChunk]:
        ...
