from __future__ import annotations

from datetime import datetime
from typing import Any

from ..models import MemoryUser


USER_COLUMNS = (
    "user_id,email,full_name,functional_role,"
    "status,created_at,updated_at"
)


def _parse_datetime(value: Any) -> datetime | None:
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        return value

    text = str(value).strip()

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _memory_user_from_row(
    row: dict[str, Any],
) -> MemoryUser:
    return MemoryUser(
        user_id=str(row.get("user_id") or ""),
        email=str(row.get("email") or ""),
        full_name=row.get("full_name"),
        functional_role=row.get("functional_role"),
        status=str(row.get("status") or "active"),
        created_at=_parse_datetime(row.get("created_at")),
        updated_at=_parse_datetime(row.get("updated_at")),
    )


class SupabaseOrganizationDirectoryRepository:
    """
    Implementación Supabase del directorio organizacional.

    El cliente Supabase se inyecta desde fuera.
    Este adapter no crea conexiones ni lee variables de entorno.
    """

    def __init__(
        self,
        client: Any,
        *,
        users_table: str = "memory_users",
    ) -> None:
        self._client = client
        self._users_table = users_table

    def get_user(
        self,
        user_id: str,
    ) -> MemoryUser | None:
        response = (
            self._client
            .table(self._users_table)
            .select(USER_COLUMNS)
            .eq("user_id", str(user_id).strip())
            .limit(1)
            .execute()
        )

        rows = list(response.data or [])

        if not rows:
            return None

        return _memory_user_from_row(rows[0])

    def get_user_by_email(
        self,
        email: str,
    ) -> MemoryUser | None:
        normalized_email = str(email or "").strip().lower()

        response = (
            self._client
            .table(self._users_table)
            .select(USER_COLUMNS)
            .eq("email", normalized_email)
            .limit(1)
            .execute()
        )

        rows = list(response.data or [])

        if not rows:
            return None

        return _memory_user_from_row(rows[0])

    def list_users(
        self,
        *,
        status: str | None = None,
        limit: int = 500,
    ) -> list[MemoryUser]:
        query = (
            self._client
            .table(self._users_table)
            .select(USER_COLUMNS)
        )

        if status:
            query = query.eq(
                "status",
                str(status).strip().lower(),
            )

        response = (
            query
            .order("email")
            .limit(int(limit))
            .execute()
        )

        return [
            _memory_user_from_row(row)
            for row in (response.data or [])
        ]

    def upsert_user(
        self,
        user: MemoryUser,
    ) -> MemoryUser:
        payload = {
            "user_id": user.user_id,
            "email": user.email,
            "full_name": user.full_name,
            "functional_role": user.functional_role,
            "status": user.status,
        }

        response = (
            self._client
            .table(self._users_table)
            .upsert(
                payload,
                on_conflict="user_id",
            )
            .execute()
        )

        rows = list(response.data or [])

        if rows:
            return _memory_user_from_row(rows[0])

        stored = self.get_user(user.user_id)

        if stored is None:
            raise RuntimeError(
                "El usuario no pudo recuperarse después del upsert."
            )

        return stored


__all__ = [
    "SupabaseOrganizationDirectoryRepository",
]
