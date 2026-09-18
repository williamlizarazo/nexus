from __future__ import annotations

from auth.models import AuthIdentity
from auth.ports import AuthProvider


class AuthenticationError(RuntimeError):
    pass


class AuthService:
    def __init__(
        self,
        provider: AuthProvider,
    ) -> None:
        self._provider = provider

    def login(
        self,
        email: str,
        password: str,
    ) -> AuthIdentity:
        normalized_email = email.strip().lower()

        if not normalized_email or not password:
            raise AuthenticationError(
                "Correo y contraseña son obligatorios."
            )

        try:
            identity = self._provider.authenticate(
                normalized_email,
                password,
            )
        except Exception as exc:
            raise AuthenticationError(
                "No fue posible autenticar las credenciales."
            ) from exc

        return AuthIdentity(
            user_id=identity.user_id,
            email=identity.email,
        )
