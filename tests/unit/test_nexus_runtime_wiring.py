from memory_core.adapters.supabase.nexus_backfill_source import (
    SupabaseNexusBackfillSource,
)
from memory_core.bootstrap import (
    MemoryRuntime,
    build_memory_runtime_from_env,
)


def test_memory_runtime_exposes_optional_nexus_backfill_source():
    runtime = MemoryRuntime(
        episode_repository=object(),
        research_activity_source=object(),
    )

    assert runtime.nexus_backfill_source is None


def test_factory_builds_nexus_backfill_source(monkeypatch):
    fake_client = object()

    monkeypatch.setattr(
        "memory_core.bootstrap.factory.create_client",
        lambda *_args, **_kwargs: fake_client,
    )

    runtime = build_memory_runtime_from_env(
        {
            "MEMORY_RELATIONAL_PROVIDER": "supabase",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_KEY": "test-key",
        }
    )

    assert isinstance(
        runtime.nexus_backfill_source,
        SupabaseNexusBackfillSource,
    )
