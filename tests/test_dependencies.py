from __future__ import annotations

from types import SimpleNamespace

import core.dependencies as dependencies_module
from core.config import AppConfig


class FakeEpisodeRepository:
    pass


class FakeResearchActivitySource:
    pass


def test_build_dependencies_uses_memory_runtime(
    monkeypatch,
):
    episode_repository = FakeEpisodeRepository()
    research_activity_source = FakeResearchActivitySource()

    runtime = SimpleNamespace(
        episode_repository=episode_repository,
        research_activity_source=research_activity_source,
    )

    monkeypatch.setattr(
        dependencies_module,
        "build_memory_runtime_from_env",
        lambda: runtime,
        raising=False,
    )

    config = AppConfig(
        app_name="appmemoria",
        environment="test",
        debug=True,
    )

    dependencies = dependencies_module.build_dependencies(
        config
    )

    assert (
        dependencies.episode_repository
        is episode_repository
    )

    assert (
        dependencies.research_activity_source
        is research_activity_source
    )


from memory_core.bootstrap import MemoryRuntimeConfigurationError


def test_build_dependencies_degrades_gracefully_when_runtime_is_not_configured(
    monkeypatch,
):
    def fake_build_runtime():
        raise MemoryRuntimeConfigurationError(
            "SUPABASE_URL is not configured."
        )

    monkeypatch.setattr(
        dependencies_module,
        "build_memory_runtime_from_env",
        fake_build_runtime,
    )

    config = AppConfig(
        app_name="appmemoria",
        environment="test",
        debug=True,
    )

    dependencies = dependencies_module.build_dependencies(
        config
    )

    assert dependencies.episode_repository is None
    assert dependencies.research_activity_source is None
    assert (
        dependencies.memory_runtime_error
        == "SUPABASE_URL is not configured."
    )
