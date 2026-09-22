from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class OrganizationDirectoryEntry:
    """
    Fila canónica del directorio organizacional.

    No depende de Supabase ni de nombres físicos de tablas.
    Un usuario puede aparecer en varias filas cuando pertenece
    a varias Magistraturas o Direcciones.
    """

    user_id: str
    email: str
    full_name: str | None
    functional_role: str | None
    user_status: str

    membership_id: str | None = None

    unit_id: str | None = None
    unit_name: str | None = None
    unit_type: str | None = None
    unit_status: str | None = None

    is_primary: bool = False

    valid_from: date | None = None
    valid_to: date | None = None

    membership_status: str | None = None
