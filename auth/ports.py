from __future__ import annotations

from typing import Protocol

from auth.models import AuthIdentity


class AuthProvider(Protocol):
    def authenticate(
        self,
        email: str,
        password: str,
    ) -> AuthIdentity:
        ...
