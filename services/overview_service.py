from __future__ import annotations

from dataclasses import dataclass

from core.dependencies import AppDependencies


@dataclass(frozen=True, slots=True)
class OverviewStatus:
    ready: bool
    message: str


class OverviewService:
    def __init__(self, dependencies: AppDependencies) -> None:
        self._dependencies = dependencies

    def get_status(self) -> OverviewStatus:
        return OverviewStatus(
            ready=True,
            message=(
                "Shell de appmemoria activo. "
                "Los proveedores todavía no están conectados."
            ),
        )
