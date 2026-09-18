from __future__ import annotations

from types import SimpleNamespace

import core.dependencies as dependencies_module
from auth.adapters.supabase import AuthProviderConfigurationError
from core.config import AppConfig
from memory_core.bootstrap import MemoryRuntimeConfigurationError


class FakeEpisodeRepository:
    pass


class FakeResearchActivitySource:
    pass


def test_build_dependencies_uses_memory_runtime(
    monkeypatch,
):
    episode_repository = FakeEpisodeRepository()
    research_activity_source = FakeResearchActivitySource()
    research_project_source = object()

    runtime = SimpleNamespace(
        episode_repository=episode_repository,
        research_activity_source=research_activity_source,
        research_project_source=research_project_source,
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

    assert (
        dependencies.research_project_source
        is research_project_source
    )


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


def test_auth_survives_memory_runtime_failure(monkeypatch):
    auth_provider = object()
    monkeypatch.setattr(
        dependencies_module,
        "build_supabase_auth_provider_from_env",
        lambda: auth_provider,
    )
    monkeypatch.setattr(
        dependencies_module,
        "build_memory_runtime_from_env",
        lambda: (_ for _ in ()).throw(
            MemoryRuntimeConfigurationError("memory unavailable")
        ),
    )

    dependencies = dependencies_module.build_dependencies(
        AppConfig("appmemoria", "test", True)
    )

    assert dependencies.auth_provider is auth_provider
    assert dependencies.authorization_service is not None
    assert dependencies.memory_runtime_error == "memory unavailable"


def test_memory_survives_auth_provider_failure(monkeypatch):
    runtime = SimpleNamespace(
        episode_repository=object(),
        research_activity_source=object(),
    )
    monkeypatch.setattr(
        dependencies_module,
        "build_supabase_auth_provider_from_env",
        lambda: (_ for _ in ()).throw(
            AuthProviderConfigurationError("auth unavailable")
        ),
    )
    monkeypatch.setattr(
        dependencies_module,
        "build_memory_runtime_from_env",
        lambda: runtime,
    )

    dependencies = dependencies_module.build_dependencies(
        AppConfig("appmemoria", "test", True)
    )

    assert dependencies.episode_repository is runtime.episode_repository
    assert dependencies.auth_provider is None
    assert dependencies.auth_runtime_error == "auth unavailable"
