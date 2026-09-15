from memory_core.domain.episode import ResearchEpisode
from memory_core.domain.episode_analysis import ResearchEpisodeAnalysis
from memory_core.domain.episode_edge import ResearchEpisodeEdge
from memory_core.domain.episode_item import ResearchEpisodeItem


def test_episode_domain():
    episode = ResearchEpisode(
        scope_type="project",
        scope_id="project-001",
    )

    search = ResearchEpisodeItem(
        episode_id=episode.episode_id,
        source_type="search",
        source_id="search-001",
    )

    annotation = ResearchEpisodeItem(
        episode_id=episode.episode_id,
        source_type="annotation",
        source_id="annotation-001",
    )

    edge = ResearchEpisodeEdge(
        episode_id=episode.episode_id,
        source_item_id=search.item_id,
        target_item_id=annotation.item_id,
        relation_type="same_trace",
    )

    analysis = ResearchEpisodeAnalysis(
        episode_id=episode.episode_id,
        version=1,
        summary="Primer análisis del episodio.",
    )

    assert episode.status == "open"
    assert search.source_type == "search"
    assert annotation.source_type == "annotation"
    assert edge.relation_type == "same_trace"
    assert analysis.version == 1
