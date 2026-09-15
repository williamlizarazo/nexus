from datetime import datetime, timezone

from memory_core.domain.research_activity import ResearchActivity
from memory_core.domain.research_annotation import ResearchAnnotation
from memory_core.domain.research_search import ResearchSearch
from memory_core.domain.research_search_result import ResearchSearchResult
from memory_core.episode_builder.builder import DeterministicEpisodeBuilder


NOW = datetime(2026, 9, 15, 12, 0, tzinfo=timezone.utc)


def search(search_id, trace_id, query):
    return ResearchSearch(
        search_id=search_id,
        project_id="project-1",
        search_type="bm25",
        original_query=query,
        trace_id=trace_id,
        created_at=NOW,
    )


def result(result_id, trace_id, doc_id, chunk_id, page_idx):
    return ResearchSearchResult(
        result_id=result_id,
        project_id="project-1",
        trace_id=trace_id,
        doc_id=doc_id,
        chunk_id=chunk_id,
        page_idx_start=page_idx,
        page_idx_end=page_idx,
    )


def test_deterministic_episode_builder():
    searches = [
        search("s1", "t1", "FARC"),
        search("s2", "t2", "FARC ELN"),
        search("s3", "t3", "Casanare"),
    ]

    results = [
        result("r1", "t1", "d1", "c1", 10),
        result("r2", "t2", "d1", "c1", 10),
        # Solo comparte documento con s1/s2; no debe bastar para fusionar.
        result("r3", "t3", "d1", "c9", 30),
    ]

    annotations = [
        ResearchAnnotation(
            annotation_id="a1",
            project_id="project-1",
            annotation_type="finding",
            trace_id="t1",
            created_at=NOW,
        )
    ]

    activities = [
        ResearchActivity(
            id="act1",
            project_id="project-1",
            activity_id="activity-1",
            activity_type="analyst_comment",
            trace_id="t2",
            created_at=NOW,
        )
    ]

    builder = DeterministicEpisodeBuilder()
    drafts = builder.build(
        project_id="project-1",
        searches=searches,
        search_results=results,
        annotations=annotations,
        activities=activities,
    )

    assert len(drafts) == 2

    large_episode = max(drafts, key=lambda item: len(item.search_ids))
    assert set(large_episode.search_ids) == {"s1", "s2"}
    assert len(large_episode.items) == 4

    relation_types = {edge.relation_type for edge in large_episode.edges}
    assert "shared_chunk" in relation_types
    assert "annotation_from_search" in relation_types
    assert "same_trace" in relation_types

    second_run = builder.build(
        project_id="project-1",
        searches=searches,
        search_results=results,
        annotations=annotations,
        activities=activities,
    )

    assert [item.episode.episode_id for item in drafts] == [
        item.episode.episode_id for item in second_run
    ]
