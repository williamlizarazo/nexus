from __future__ import annotations

import pytest

from memory_core.adapters.supabase.episode_repository import (
    SupabaseEpisodeRepository,
)
from memory_core.adapters.supabase.research_activity_source import (
    SupabaseResearchActivitySource,
)
from memory_core.bootstrap import (
    UnsupportedMemoryProviderError,
    build_memory_runtime_from_env,
)


class FakeSupabaseClient:
    pass


def test_build_runtime_from_env_uses_configured_provider(
    monkeypatch,
):
    from memory_core.bootstrap import factory as factory_module

    fake_client = FakeSupabaseClient()

    calls: list[tuple[str, str]] = []

    def fake_create_client(
        url: str,
        key: str,
    ):
        calls.append((url, key))
        return fake_client

    monkeypatch.setattr(
        factory_module,
        "create_client",
        fake_create_client,
    )

    runtime = factory_module.build_memory_runtime_from_env(
        {
            "MEMORY_RELATIONAL_PROVIDER": "supabase",
            "SUPABASE_URL": "https://example.supabase.co",
            "SUPABASE_KEY": "test-key",
        }
    )

    assert calls == [
        (
            "https://example.supabase.co",
            "test-key",
        )
    ]

    assert isinstance(
        runtime.episode_repository,
        SupabaseEpisodeRepository,
    )

    assert isinstance(
        runtime.research_activity_source,
        SupabaseResearchActivitySource,
    )

    assert (
        runtime.episode_repository.client
        is fake_client
    )

    assert (
        runtime.research_activity_source.client
        is fake_client
    )


def test_runtime_rejects_unknown_provider():
    with pytest.raises(
        UnsupportedMemoryProviderError,
        match="Unsupported relational memory provider",
    ):
        build_memory_runtime_from_env(
            {
                "MEMORY_RELATIONAL_PROVIDER": "unknown",
            }
        )
