from types import SimpleNamespace

import core.dependencies as dependencies


def test_build_dependencies_exposes_organization_directory_repository(
    monkeypatch,
):
    organization_directory_repository = object()

    fake_runtime = SimpleNamespace(
        episode_repository=object(),
        research_activity_source=object(),
        organization_directory_repository=(
            organization_directory_repository
        ),
    )

    monkeypatch.setattr(
        dependencies,
        "build_memory_runtime_from_env",
        lambda: fake_runtime,
    )

    result = dependencies.build_dependencies(
        config=object(),
    )

    assert (
        result.organization_directory_repository
        is organization_directory_repository
    )
