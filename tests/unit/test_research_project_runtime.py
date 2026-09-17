from memory_core.adapters.supabase.research_project_source import (
    SupabaseResearchProjectSource,
)
from memory_core.bootstrap import factory
from memory_core.bootstrap.runtime import MemoryRuntime


def test_memory_runtime_exposes_research_project_source():
    research_project_source = object()

    runtime = MemoryRuntime(
        episode_repository=object(),
        research_activity_source=object(),
        research_project_source=research_project_source,
    )

    assert runtime.research_project_source is research_project_source


def test_factory_builds_research_project_source(monkeypatch):
    fake_client = object()

    monkeypatch.setattr(
        factory,
        "create_client",
        lambda _url, _key: fake_client,
    )

    runtime = factory.build_memory_runtime_from_env(
        {
            "MEMORY_RELATIONAL_PROVIDER": "supabase",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_KEY": "test-key",
        }
    )

    assert isinstance(
        runtime.research_project_source,
        SupabaseResearchProjectSource,
    )
    assert runtime.research_project_source._client is fake_client
