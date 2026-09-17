from memory_core.bootstrap.runtime import MemoryRuntime


def test_memory_runtime_exposes_organization_directory_repository():
    episode_repository = object()
    research_activity_source = object()
    organization_directory_repository = object()

    runtime = MemoryRuntime(
        episode_repository=episode_repository,
        research_activity_source=research_activity_source,
        organization_directory_repository=organization_directory_repository,
    )

    assert (
        runtime.organization_directory_repository
        is organization_directory_repository
    )
