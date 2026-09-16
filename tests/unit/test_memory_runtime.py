from __future__ import annotations

from memory_core.bootstrap.runtime import MemoryRuntime


class FakeEpisodeRepository:
    pass


class FakeResearchActivitySource:
    pass


def test_memory_runtime_exposes_core_capabilities():
    episode_repository = FakeEpisodeRepository()
    research_activity_source = FakeResearchActivitySource()

    runtime = MemoryRuntime(
        episode_repository=episode_repository,
        research_activity_source=research_activity_source,
    )

    assert runtime.episode_repository is episode_repository
    assert (
        runtime.research_activity_source
        is research_activity_source
    )
