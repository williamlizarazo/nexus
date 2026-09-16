from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MemoryModuleDefinition:
    key: str
    label: str
    enabled: bool
    description: str


MEMORY_REGISTRY: tuple[MemoryModuleDefinition, ...] = (
    MemoryModuleDefinition(
        key="episodic",
        label="Memoria episódica",
        enabled=True,
        description=(
            "Trayectorias investigativas construidas a partir de búsquedas, "
            "actividades, anotaciones y relaciones."
        ),
    ),
)


def list_memory_modules() -> tuple[MemoryModuleDefinition, ...]:
    return MEMORY_REGISTRY
