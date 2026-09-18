from types import SimpleNamespace

import pytest
import supabase

from auth.adapters.supabase import (
    AuthProviderConfigurationError,
    SupabaseAuthProvider,
    build_supabase_auth_provider_from_env,
)


def test_builder_prefers_publishable_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "publishable-key")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "legacy-key")

    assert build_supabase_auth_provider_from_env()._api_key == "publishable-key"


def test_builder_rejects_missing_public_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)

    with pytest.raises(AuthProviderConfigurationError):
        build_supabase_auth_provider_from_env()


def test_builder_rejects_missing_url(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "publishable-key")

    with pytest.raises(AuthProviderConfigurationError, match="SUPABASE_URL"):
        build_supabase_auth_provider_from_env()


def test_builder_uses_legacy_anon_key_as_fallback(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.delenv("SUPABASE_PUBLISHABLE_KEY", raising=False)
    monkeypatch.setenv("SUPABASE_ANON_KEY", "legacy-key")

    assert build_supabase_auth_provider_from_env()._api_key == "legacy-key"


def test_builder_rejects_secret_key(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", "sb_secret_forbidden")

    with pytest.raises(AuthProviderConfigurationError, match="clave pública"):
        build_supabase_auth_provider_from_env()


def test_builder_rejects_legacy_service_role_key(monkeypatch):
    service_role_key = (
        "eyJhbGciOiJIUzI1NiJ9."
        "eyJyb2xlIjoic2VydmljZV9yb2xlIn0."
        "signature"
    )
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_PUBLISHABLE_KEY", service_role_key)

    with pytest.raises(AuthProviderConfigurationError, match="clave pública"):
        build_supabase_auth_provider_from_env()


def test_provider_constructor_rejects_secret_key():
    with pytest.raises(AuthProviderConfigurationError, match="clave pública"):
        SupabaseAuthProvider(
            url="https://example.supabase.co",
            api_key="sb_secret_forbidden",
        )


@pytest.mark.parametrize(
    "payload",
    [
        "W10",
        "eyJyb2xlIjpbXX0",
    ],
)
def test_builder_rejects_malformed_legacy_key(monkeypatch, payload):
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv(
        "SUPABASE_PUBLISHABLE_KEY",
        f"eyJhbGciOiJIUzI1NiJ9.{payload}.signature",
    )

    with pytest.raises(AuthProviderConfigurationError, match="clave pública"):
        build_supabase_auth_provider_from_env()


def test_authenticate_creates_a_fresh_client_per_attempt(monkeypatch):
    clients = []

    def create_client(url, key):
        client = SimpleNamespace(
            auth=SimpleNamespace(
                sign_in_with_password=lambda credentials: SimpleNamespace(
                    user=SimpleNamespace(
                        id=f"user-{len(clients)}",
                        email=credentials["email"],
                    )
                )
            )
        )
        clients.append(client)
        return client

    monkeypatch.setattr(supabase, "create_client", create_client)
    provider = SupabaseAuthProvider(
        url="https://example.supabase.co",
        api_key="publishable-key",
    )

    provider.authenticate("one@example.org", "secret")
    provider.authenticate("two@example.org", "secret")

    assert len(clients) == 2 and clients[0] is not clients[1]


def test_authenticate_rejects_response_without_user(monkeypatch):
    client = SimpleNamespace(
        auth=SimpleNamespace(
            sign_in_with_password=lambda credentials: SimpleNamespace(user=None)
        )
    )
    monkeypatch.setattr(supabase, "create_client", lambda url, key: client)
    provider = SupabaseAuthProvider(
        url="https://example.supabase.co",
        api_key="publishable-key",
    )

    with pytest.raises(RuntimeError, match="no devolvió usuario"):
        provider.authenticate("user@example.org", "secret")


def test_authenticate_rejects_response_without_user_id(monkeypatch):
    client = SimpleNamespace(
        auth=SimpleNamespace(
            sign_in_with_password=lambda credentials: SimpleNamespace(
                user=SimpleNamespace(id="", email=credentials["email"])
            )
        )
    )
    monkeypatch.setattr(supabase, "create_client", lambda url, key: client)
    provider = SupabaseAuthProvider(
        url="https://example.supabase.co",
        api_key="publishable-key",
    )

    with pytest.raises(RuntimeError, match="user_id"):
        provider.authenticate("user@example.org", "secret")
