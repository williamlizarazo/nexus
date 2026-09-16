from __future__ import annotations

from core.dependencies import AppDependencies


class EpisodicService:
    def __init__(self, dependencies: AppDependencies) -> None:
        self._dependencies = dependencies

    @property
    def repository_available(self) -> bool:
        return self._dependencies.episode_repository is not None

    def status_message(self) -> str:
        if self.repository_available:
            return "Repositorio episódico disponible."
        return "Módulo episódico activo. Repositorio todavía no conectado."
