from types import SimpleNamespace

import pytest

from memory_core.domain.organization_directory_entry import (
    OrganizationDirectoryEntry,
    OrganizationUnitOption,
)

from presenters.organizational_directory_presenter import (
    OrganizationalDirectoryPresenter,
)
from services.organizational_directory_service import (
    OrganizationalDirectoryService,
)


ENTRIES = [
    OrganizationDirectoryEntry(
        user_id="user-1",
        email="usuario@jep.gov.co",
        full_name="Usuario Uno",
        functional_role="Investigador",
        user_status="active",
        unit_id="unit-2",
        unit_name="Dirección B",
        unit_type="direccion",
    ),
    OrganizationDirectoryEntry(
        user_id="user-1",
        email="usuario@jep.gov.co",
        full_name="Usuario Uno",
        functional_role="Investigador",
        user_status="active",
        unit_id="unit-1",
        unit_name="Magistratura A",
        unit_type="magistratura",
        is_primary=False,
    ),
    OrganizationDirectoryEntry(
        user_id="user-1",
        email="usuario@jep.gov.co",
        full_name="Usuario Uno",
        functional_role="Investigador",
        user_status="active",
        unit_id="unit-1",
        unit_name="Magistratura A",
        unit_type="magistratura",
        is_primary=True,
    ),
    OrganizationDirectoryEntry(
        user_id="user-2",
        email="usuario2@jep.gov.co",
        full_name="Usuario Dos",
        functional_role=None,
        user_status="inactive",
    ),
]


class FakeRepository:
    def __init__(self):
        self.units = [
            OrganizationUnitOption(
                unit_id="unit-1",
                name="Magistratura A",
                unit_type="magistratura",
            ),
            OrganizationUnitOption(
                unit_id="unit-2",
                name="Dirección B",
                unit_type="direccion",
            ),
        ]
        self.updated = None
        self.created = []

    def list_directory_entries(self):
        return list(ENTRIES)

    def list_organizational_units(self):
        return list(self.units)

    def update_directory_user(self, **values):
        self.updated = values

    def create_organizational_unit(
        self,
        *,
        name,
        unit_type,
    ):
        self.created.append((name, unit_type))
        return OrganizationUnitOption(
            unit_id="created-unit",
            name=name,
            unit_type=unit_type,
        )


def test_service_reads_repository():
    service = OrganizationalDirectoryService(
        SimpleNamespace(
            organization_directory_repository=(
                FakeRepository()
            )
        )
    )

    assert service.list_entries() == tuple(
        ENTRIES
    )


def test_service_without_repository_is_empty():
    service = OrganizationalDirectoryService(
        SimpleNamespace(
            organization_directory_repository=None
        )
    )

    assert service.list_entries() == ()
    assert service.list_organizational_units() == ()


def test_service_lists_organizational_units():
    repository = FakeRepository()
    service = OrganizationalDirectoryService(
        SimpleNamespace(
            organization_directory_repository=repository
        )
    )

    assert service.list_organizational_units() == tuple(
        repository.units
    )


def test_service_creates_normalized_organizational_unit():
    repository = FakeRepository()
    repository.units = []
    service = OrganizationalDirectoryService(
        SimpleNamespace(
            organization_directory_repository=repository
        )
    )

    result = service.create_organizational_unit(
        name="  Magistrado   Vidal  ",
        unit_type=" MAGISTRATURA ",
    )

    assert result.unit_id == "created-unit"
    assert repository.created == [
        ("Magistrado Vidal", "magistratura")
    ]


def test_service_reuses_existing_unit_case_insensitively():
    repository = FakeRepository()
    service = OrganizationalDirectoryService(
        SimpleNamespace(
            organization_directory_repository=repository
        )
    )

    result = service.create_organizational_unit(
        name="  magistratura a ",
        unit_type="MAGISTRATURA",
    )

    assert result.unit_id == "unit-1"
    assert repository.created == []


@pytest.mark.parametrize(
    ("name", "unit_type", "message"),
    [
        ("  ", "magistratura", "obligatorio"),
        ("Magistratura A", "equipo", "tipo"),
    ],
)
def test_service_rejects_invalid_organizational_unit(
    name,
    unit_type,
    message,
):
    service = OrganizationalDirectoryService(
        SimpleNamespace(
            organization_directory_repository=FakeRepository()
        )
    )

    with pytest.raises(ValueError, match=message):
        service.create_organizational_unit(
            name=name,
            unit_type=unit_type,
        )


def test_directory_update_rejects_blank_name():
    service = OrganizationalDirectoryService(
        SimpleNamespace(
            organization_directory_repository=FakeRepository()
        )
    )

    with pytest.raises(ValueError, match="nombre"):
        service.update_user(
            user_id="user-1",
            full_name="  ",
            functional_role="Investigador/a",
            status="active",
            unit_ids=(),
        )


def test_directory_update_rejects_unknown_role():
    service = OrganizationalDirectoryService(
        SimpleNamespace(
            organization_directory_repository=FakeRepository()
        )
    )

    with pytest.raises(ValueError, match="Rol funcional"):
        service.update_user(
            user_id="user-1",
            full_name="Persona Uno",
            functional_role="Rol inventado",
            status="active",
            unit_ids=(),
        )


def test_directory_update_rejects_unknown_status():
    service = OrganizationalDirectoryService(
        SimpleNamespace(
            organization_directory_repository=FakeRepository()
        )
    )

    with pytest.raises(ValueError, match="Estado"):
        service.update_user(
            user_id="user-1",
            full_name="Persona Uno",
            functional_role="Investigador/a",
            status="blocked",
            unit_ids=(),
        )


def test_directory_update_rejects_unknown_unit():
    service = OrganizationalDirectoryService(
        SimpleNamespace(
            organization_directory_repository=FakeRepository()
        )
    )

    with pytest.raises(
        ValueError,
        match="Magistratura/Dirección",
    ):
        service.update_user(
            user_id="user-1",
            full_name="Persona Uno",
            functional_role="Investigador/a",
            status="active",
            unit_ids=("unknown-unit",),
        )


def test_directory_update_normalizes_name_and_calls_repository():
    repository = FakeRepository()
    service = OrganizationalDirectoryService(
        SimpleNamespace(
            organization_directory_repository=repository
        )
    )

    service.update_user(
        user_id="user-1",
        full_name="  Persona Uno  ",
        functional_role="Investigador/a",
        status="inactive",
        unit_ids=("unit-2",),
    )

    assert repository.updated == {
        "user_id": "user-1",
        "full_name": "Persona Uno",
        "functional_role": "Investigador/a",
        "status": "inactive",
        "unit_ids": ("unit-2",),
    }


def test_directory_update_deduplicates_unit_ids_in_order():
    repository = FakeRepository()
    service = OrganizationalDirectoryService(
        SimpleNamespace(
            organization_directory_repository=repository
        )
    )

    service.update_user(
        user_id="user-1",
        full_name="Persona Uno",
        functional_role="Investigador/a",
        status="active",
        unit_ids=("unit-2", "unit-1", "unit-2"),
    )

    assert repository.updated["unit_ids"] == (
        "unit-2",
        "unit-1",
    )


def test_presenter_groups_memberships():
    rows = OrganizationalDirectoryPresenter.rows(
        ENTRIES
    )

    assert len(rows) == 2

    user = next(
        row
        for row in rows
        if row["Correo"]
        == "usuario@jep.gov.co"
    )

    assert (
        user["Magistratura / Dirección"]
        ==
        (
            "Magistratura A"
            " · Dirección B"
        )
    )
    assert "Principal" not in user
    assert user["user_id"] == "user-1"
    assert user["_unit_ids"] == (
        "unit-1",
        "unit-2",
    )
    assert user["_functional_role"] == "Investigador"
    assert user["_status"] == "active"
    assert user["Estado"] == "Activo"


def test_presenter_supports_user_without_unit():
    rows = OrganizationalDirectoryPresenter.rows(
        ENTRIES
    )

    user = next(
        row
        for row in rows
        if row["Correo"]
        == "usuario2@jep.gov.co"
    )

    assert (
        user["Magistratura / Dirección"]
        == "—"
    )
    assert "Principal" not in user
    assert user["_unit_ids"] == ()
    assert user["Estado"] == "Inactivo"
    assert user["Rol funcional"] == "—"
