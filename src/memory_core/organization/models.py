from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


VALID_USER_STATUSES = frozenset({"active", "inactive"})


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()
    return normalized or None


@dataclass(frozen=True, slots=True)
class MemoryUser:
    """
    Identidad organizacional de una persona cuya actividad puede
    participar en el sistema de memoria.

    user_id:
        Identidad técnica estable proveniente actualmente de Supabase Auth.

    email:
        Identificación visible mínima. Se considera estable e inmutable.

    full_name / functional_role:
        Atributos opcionales que pueden enriquecerse posteriormente.
    """

    user_id: str
    email: str
    full_name: str | None = None
    functional_role: str | None = None
    status: str = "active"
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def __post_init__(self) -> None:
        user_id = str(self.user_id or "").strip()
        email = str(self.email or "").strip().lower()
        status = str(self.status or "").strip().lower()

        if not user_id:
            raise ValueError("user_id es obligatorio.")

        if not email:
            raise ValueError("email es obligatorio.")

        if status not in VALID_USER_STATUSES:
            raise ValueError(
                f"status inválido: {status!r}. "
                f"Valores permitidos: {sorted(VALID_USER_STATUSES)}"
            )

        object.__setattr__(self, "user_id", user_id)
        object.__setattr__(self, "email", email)
        object.__setattr__(
            self,
            "full_name",
            _optional_text(self.full_name),
        )
        object.__setattr__(
            self,
            "functional_role",
            _optional_text(self.functional_role),
        )
        object.__setattr__(self, "status", status)
