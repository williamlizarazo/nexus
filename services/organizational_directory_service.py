from __future__ import annotations

from memory_core.domain.organization_directory_entry import (
    OrganizationDirectoryEntry,
    OrganizationUnitOption,
)

from core.dependencies import AppDependencies
from core.organizational_directory_catalog import (
    FUNCTIONAL_ROLE_CHOICES,
    USER_STATUS_CHOICES,
)


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

    def list_organizational_units(
        self,
    ) -> tuple[OrganizationUnitOption, ...]:
        if self._repository is None:
            return ()

        return tuple(
            self._repository
            .list_organizational_units()
        )

    def create_organizational_unit(
        self,
        *,
        name: str,
        unit_type: str,
    ) -> OrganizationUnitOption:
        if self._repository is None:
            raise RuntimeError(
                "Directorio organizacional no disponible."
            )

        normalized_name = " ".join(
            (name or "").split()
        )
        normalized_type = (
            unit_type or ""
        ).strip().lower()

        if not normalized_name:
            raise ValueError(
                "El nombre de la Magistratura/Dirección "
                "es obligatorio."
            )

        if normalized_type not in {
            "magistratura",
            "direccion",
        }:
            raise ValueError(
                "El tipo debe ser Magistratura o Dirección."
            )

        for unit in self.list_organizational_units():
            if (
                unit.unit_type.strip().lower()
                == normalized_type
                and unit.name.strip().casefold()
                == normalized_name.casefold()
            ):
                return unit

        return self._repository.create_organizational_unit(
            name=normalized_name,
            unit_type=normalized_type,
        )

    def update_user(
        self,
        *,
        user_id: str,
        full_name: str,
        functional_role: str,
        status: str,
        unit_ids: tuple[str, ...],
    ) -> None:
        full_name = full_name.strip()
        unit_ids = tuple(dict.fromkeys(unit_ids))

        if not full_name:
            raise ValueError(
                "El nombre no puede estar vacío."
            )

        if functional_role not in FUNCTIONAL_ROLE_CHOICES:
            raise ValueError(
                "Rol funcional no válido."
            )

        if status not in USER_STATUS_CHOICES:
            raise ValueError("Estado no válido.")

        if self._repository is None:
            raise RuntimeError(
                "Directorio organizacional no disponible."
            )

        valid_unit_ids = {
            unit.unit_id
            for unit in (
                self._repository
                .list_organizational_units()
            )
        }

        if set(unit_ids) - valid_unit_ids:
            raise ValueError(
                "Existe una Magistratura/Dirección no válida."
            )

        self._repository.update_directory_user(
            user_id=user_id,
            full_name=full_name,
            functional_role=functional_role,
            status=status,
            unit_ids=unit_ids,
        )
