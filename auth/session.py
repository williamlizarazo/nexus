from __future__ import annotations

from dataclasses import dataclass

from auth.models import AppActor


@dataclass(
    frozen=True,
    slots=True,
)
class AuthSessionState:
    """
    Estado lógico de autenticación de una sesión
    de appmemoria.

    No depende de PyShiny ni de Supabase.
    """

    actor: AppActor | None = None
    error_message: str | None = None

    @property
    def is_authenticated(self) -> bool:
        return self.actor is not None

    @classmethod
    def authenticated(
        cls,
        actor: AppActor,
    ) -> "AuthSessionState":
        return cls(
            actor=actor,
            error_message=None,
        )

    @classmethod
    def failed(
        cls,
        message: str,
    ) -> "AuthSessionState":
        return cls(
            actor=None,
            error_message=message,
        )

    def logout(
        self,
    ) -> "AuthSessionState":
        return AuthSessionState()
