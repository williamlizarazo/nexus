from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from auth.adapters.supabase import (
    AuthProviderConfigurationError,
    build_supabase_auth_provider_from_env,
)
from authorization.service import AuthorizationService
from memory_core.bootstrap import (
    MemoryRuntimeConfigurationError,
    build_memory_runtime_from_env,
)

from core.config import AppConfig


@dataclass(slots=True)
class AppDependencies:
    """External capabilities available to appmemoria."""

    episode_repository: Any | None = None
    research_activity_source: Any | None = None
    research_project_source: Any | None = None
    organization_directory_repository: Any | None = None
    nexus_backfill_source: Any | None = None
    vector_store: Any | None = None
    llm_provider: Any | None = None
    embedding_provider: Any | None = None
    auth_provider: Any | None = None
    authorization_service: Any | None = None
    auth_runtime_error: str | None = None
    memory_runtime_error: str | None = None


def build_dependencies(
    config: AppConfig,
) -> AppDependencies:
    """Build dependencies available to appmemoria."""

    authorization_service = AuthorizationService(
        admin_emails=getattr(
            config,
            "admin_emails",
            (),
        ),
        viewer_emails=getattr(
            config,
            "viewer_emails",
            (),
        ),
    )

    auth_provider = None
    auth_runtime_error = None

    try:
        auth_provider = (
            build_supabase_auth_provider_from_env()
        )

    except AuthProviderConfigurationError as exc:
        auth_runtime_error = str(exc)

    runtime = None
    memory_runtime_error = None

    try:
        runtime = (
            build_memory_runtime_from_env()
        )

    except MemoryRuntimeConfigurationError as exc:
        memory_runtime_error = str(exc)

    return AppDependencies(
        episode_repository=(
            getattr(
                runtime,
                "episode_repository",
                None,
            )
            if runtime
            else None
        ),
        research_activity_source=(
            getattr(
                runtime,
                "research_activity_source",
                None,
            )
            if runtime
            else None
        ),
        research_project_source=(
            getattr(
                runtime,
                "research_project_source",
                None,
            )
            if runtime
            else None
        ),
        organization_directory_repository=(
            getattr(
                runtime,
                "organization_directory_repository",
                None,
            )
            if runtime
            else None
        ),
        nexus_backfill_source=(
            getattr(
                runtime,
                "nexus_backfill_source",
                None,
            )
            if runtime
            else None
        ),
        auth_provider=auth_provider,
        authorization_service=(
            authorization_service
        ),
        auth_runtime_error=auth_runtime_error,
        memory_runtime_error=memory_runtime_error,
    )
