from __future__ import annotations

import os
from collections.abc import Mapping

from supabase import create_client

from memory_core.adapters.supabase.episode_repository import (
    SupabaseEpisodeRepository,
)
from memory_core.adapters.supabase.research_activity_source import (
    SupabaseResearchActivitySource,
)
from memory_core.bootstrap.runtime import MemoryRuntime


class MemoryRuntimeConfigurationError(RuntimeError):
    """Invalid or incomplete memory runtime configuration."""


class UnsupportedMemoryProviderError(
    MemoryRuntimeConfigurationError
):
    """Requested memory provider is not supported."""


def build_memory_runtime_from_env(
    environ: Mapping[str, str] | None = None,
) -> MemoryRuntime:
    env = os.environ if environ is None else environ

    provider = env.get(
        "MEMORY_RELATIONAL_PROVIDER",
        "",
    ).strip().lower()

    if not provider:
        raise MemoryRuntimeConfigurationError(
            "MEMORY_RELATIONAL_PROVIDER is not configured."
        )

    if provider != "supabase":
        raise UnsupportedMemoryProviderError(
            f"Unsupported relational memory provider: {provider}"
        )

    supabase_url = env.get(
        "SUPABASE_URL",
        "",
    ).strip()

    supabase_key = env.get(
        "SUPABASE_KEY",
        "",
    ).strip()

    if not supabase_url:
        raise MemoryRuntimeConfigurationError(
            "SUPABASE_URL is not configured."
        )

    if not supabase_key:
        raise MemoryRuntimeConfigurationError(
            "SUPABASE_KEY is not configured."
        )

    client = create_client(
        supabase_url,
        supabase_key,
    )

    return MemoryRuntime(
        episode_repository=(
            SupabaseEpisodeRepository(client)
        ),
        research_activity_source=(
            SupabaseResearchActivitySource(client)
        ),
    )
