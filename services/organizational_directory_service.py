from __future__ import annotations

from memory_core.domain.organization_directory_entry import (
    OrganizationDirectoryEntry,
)

from core.dependencies import AppDependencies


class OrganizationalDirectoryService:
    def __init__(
        self,
        dependencies: AppDependencies,
    ):
        self._repository = (
            dependencies
            .organization_directory_repository
        )

    def list_entries(
        self,
    ) -> tuple[
        OrganizationDirectoryEntry,
        ...,
    ]:
        if self._repository is None:
            return ()

        return tuple(
            self._repository
            .list_directory_entries()
        )
