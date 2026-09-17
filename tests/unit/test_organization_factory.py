from memory_core.bootstrap import factory
from memory_core.organization.adapters.supabase import (
    SupabaseOrganizationDirectoryRepository,
)


def test_factory_builds_organization_directory_repository(monkeypatch):
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
        runtime.organization_directory_repository,
        SupabaseOrganizationDirectoryRepository,
    )
    assert (
        runtime.organization_directory_repository._client
        is fake_client
    )
