from __future__ import annotations

from dataclasses import dataclass


def _normalize_ids(
    values: tuple[str, ...],
) -> tuple[str, ...]:
    normalized = {
        value.strip()
        for value in values
        if value is not None
        and value.strip()
    }

    return tuple(
        sorted(normalized)
    )


@dataclass(frozen=True, slots=True)
class NexusAffectedScope:
    project_ids: tuple[str, ...] = ()
    user_ids: tuple[str, ...] = ()
    unit_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "project_ids",
            _normalize_ids(
                self.project_ids
            ),
        )

        object.__setattr__(
            self,
            "user_ids",
            _normalize_ids(
                self.user_ids
            ),
        )

        object.__setattr__(
            self,
            "unit_ids",
            _normalize_ids(
                self.unit_ids
            ),
        )
