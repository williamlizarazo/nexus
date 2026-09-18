from __future__ import annotations

import os

from auth.models import AuthIdentity


class AuthProviderConfigurationError(RuntimeError):
    pass


class SupabaseAuthProvider:
    def __init__(self, *, url: str, api_key: str) -> None:
        self._url = url
        self._api_key = api_key

    def authenticate(self, email: str, password: str) -> AuthIdentity:
        from supabase import create_client

        client = create_client(self._url, self._api_key)
        response = client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        user = getattr(response, "user", None)

        if user is None:
            raise RuntimeError("Supabase no devolvió usuario.")

        user_id = str(getattr(user, "id", "")).strip()
        if not user_id:
            raise RuntimeError("Supabase no devolvió user_id.")

        user_email = str(getattr(user, "email", "") or email)
        return AuthIdentity(user_id, user_email)


def build_supabase_auth_provider_from_env() -> SupabaseAuthProvider:
    url = os.getenv("SUPABASE_URL", "").strip()
    api_key = (
        os.getenv("SUPABASE_PUBLISHABLE_KEY", "").strip()
        or os.getenv("SUPABASE_ANON_KEY", "").strip()
    )

    if not url:
        raise AuthProviderConfigurationError("Falta SUPABASE_URL.")

    if not api_key:
        raise AuthProviderConfigurationError(
            "Falta SUPABASE_PUBLISHABLE_KEY o SUPABASE_ANON_KEY."
        )

    if api_key.startswith("sb_secret_"):
        raise AuthProviderConfigurationError(
            "La autenticación requiere una clave pública de Supabase."
        )

    return SupabaseAuthProvider(url=url, api_key=api_key)
