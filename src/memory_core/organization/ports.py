from __future__ import annotations

from typing import Protocol

from .models import MemoryUser


class OrganizationDirectoryRepository(Protocol):
    """Contrato de persistencia del directorio organizacional."""

    def get_user(
        self,
        user_id: str,
    ) -> MemoryUser | None:
        ...

    def get_user_by_email(
        self,
        email: str,
    ) -> MemoryUser | None:
        ...

    def list_users(
        self,
        *,
        status: str | None = None,
        limit: int = 500,
    ) -> list[MemoryUser]:
        ...

    def upsert_user(
        self,
        user: MemoryUser,
    ) -> MemoryUser:
        ...
