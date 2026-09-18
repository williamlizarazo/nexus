from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


AccessRole = Literal[
    "admin",
    "viewer",
]


@dataclass(frozen=True, slots=True)
class AuthIdentity:
    user_id: str
    email: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "user_id",
            self.user_id.strip(),
        )
        object.__setattr__(
            self,
            "email",
            self.email.strip().lower(),
        )


@dataclass(frozen=True, slots=True)
class AppActor:
    user_id: str
    email: str
    role: AccessRole

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"
