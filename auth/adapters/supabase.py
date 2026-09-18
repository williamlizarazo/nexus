from __future__ import annotations

import base64
import binascii
import json
import os

from auth.models import AuthIdentity


class AuthProviderConfigurationError(RuntimeError):
    pass


def _is_privileged_api_key(api_key: str) -> bool:
    if api_key.startswith("sb_secret_"):
        return True

    parts = api_key.split(".")
    if len(parts) != 3:
        return False

    try:
        payload_part = parts[1]
        padding = "=" * (-len(payload_part) % 4)
        payload = json.loads(
            base64.urlsafe_b64decode(payload_part + padding).decode("utf-8")
        )
    except (binascii.Error, UnicodeDecodeError, ValueError, json.JSONDecodeError):
        return True

    if not isinstance(payload, dict):
        return True

    role = payload.get("role")
    if not isinstance(role, str):
        return True

    return role in {"service_role", "supabase_admin"}


class SupabaseAuthProvider:
    def __init__(self, *, url: str, api_key: str) -> None:
        if _is_privileged_api_key(api_key):
            raise AuthProviderConfigurationError(
                "La autenticación requiere una clave pública de Supabase."
            )

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

    if _is_privileged_api_key(api_key):
        raise AuthProviderConfigurationError(
            "La autenticación requiere una clave pública de Supabase."
        )

    return SupabaseAuthProvider(url=url, api_key=api_key)
