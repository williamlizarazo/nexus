from types import SimpleNamespace

import core.dependencies as dependencies_module
from core.dependencies import (
    AppDependencies,
    build_dependencies,
)


def test_app_dependencies_exposes_optional_nexus_source():
    dependencies = AppDependencies()

    assert dependencies.nexus_backfill_source is None


def test_build_dependencies_exposes_nexus_source(
    monkeypatch,
):
    nexus_source = object()

    runtime = SimpleNamespace(
        episode_repository=object(),
        research_activity_source=object(),
        research_project_source=object(),
        organization_directory_repository=object(),
        nexus_backfill_source=nexus_source,
    )

    monkeypatch.setattr(
        dependencies_module,
        "build_memory_runtime_from_env",
        lambda: runtime,
    )

    monkeypatch.setattr(
        dependencies_module,
        "build_supabase_auth_provider_from_env",
        lambda: None,
    )

    config = SimpleNamespace(
        admin_emails=(),
        viewer_emails=(),
    )

    dependencies = build_dependencies(
        config
    )

    assert (
        dependencies.nexus_backfill_source
        is nexus_source
    )
