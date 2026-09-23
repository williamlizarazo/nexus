from __future__ import annotations

from datetime import date, datetime
from typing import Any

from memory_core.domain.organization_directory_entry import (
    OrganizationDirectoryEntry,
    OrganizationUnitOption,
)

from ..models import MemoryUser


USER_COLUMNS = (
    "user_id,email,full_name,functional_role,"
    "status,created_at,updated_at"
)

DIRECTORY_COLUMNS = (
    "user_id,email,full_name,functional_role,user_status,"
    "membership_id,is_primary,valid_from,valid_to,"
    "membership_status,unit_id,unit_name,unit_type,unit_status"
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


def _parse_date(
    value: Any,
) -> date | None:
    if value is None or value == "":
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    return date.fromisoformat(
        str(value).strip()
    )


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


def _directory_entry_from_row(
    row: dict[str, Any],
) -> OrganizationDirectoryEntry:
    return OrganizationDirectoryEntry(
        user_id=str(row["user_id"]),
        email=str(row["email"]),
        full_name=row.get("full_name"),
        functional_role=row.get(
            "functional_role"
        ),
        user_status=str(
            row.get("user_status")
            or "active"
        ),
        membership_id=(
            str(row["membership_id"])
            if row.get("membership_id")
            else None
        ),
        unit_id=(
            str(row["unit_id"])
            if row.get("unit_id")
            else None
        ),
        unit_name=row.get("unit_name"),
        unit_type=row.get("unit_type"),
        unit_status=row.get("unit_status"),
        is_primary=bool(
            row.get("is_primary", False)
        ),
        valid_from=_parse_date(
            row.get("valid_from")
        ),
        valid_to=_parse_date(
            row.get("valid_to")
        ),
        membership_status=row.get(
            "membership_status"
        ),
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

    def list_directory_entries(
        self,
    ) -> list[OrganizationDirectoryEntry]:
        response = (
            self._client
            .table(
                "memory_organizational_directory_v"
            )
            .select(DIRECTORY_COLUMNS)
            .order("full_name")
            .execute()
        )

        return [
            _directory_entry_from_row(row)
            for row in (response.data or [])
        ]

    def list_organizational_units(
        self,
    ) -> list[OrganizationUnitOption]:
        response = (
            self._client
            .table("memory_organizational_units")
            .select("unit_id,name,unit_type,status")
            .eq("status", "active")
            .order("unit_type")
            .order("name")
            .execute()
        )

        return [
            OrganizationUnitOption(
                unit_id=str(row["unit_id"]),
                name=str(row["name"]),
                unit_type=str(row["unit_type"]),
            )
            for row in (response.data or [])
        ]

    def create_organizational_unit(
        self,
        *,
        name: str,
        unit_type: str,
    ) -> OrganizationUnitOption:
        response = (
            self._client
            .table("memory_organizational_units")
            .insert(
                {
                    "name": name,
                    "unit_type": unit_type,
                    "status": "active",
                }
            )
            .execute()
        )

        rows = response.data or []

        if not rows:
            raise RuntimeError(
                "No fue posible crear la unidad organizacional."
            )

        row = rows[0]

        return OrganizationUnitOption(
            unit_id=str(row["unit_id"]),
            name=str(row["name"]),
            unit_type=str(row["unit_type"]),
        )

    def update_directory_user(
        self,
        *,
        user_id: str,
        full_name: str,
        functional_role: str,
        status: str,
        unit_ids: tuple[str, ...],
    ) -> None:
        (
            self._client
            .rpc(
                "memory_update_directory_user",
                {
                    "p_user_id": user_id,
                    "p_full_name": full_name,
                    "p_functional_role": functional_role,
                    "p_status": status,
                    "p_unit_ids": list(unit_ids),
                },
            )
            .execute()
        )

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
