from types import SimpleNamespace

from memory_core.domain.organization_directory_entry import (
    OrganizationDirectoryEntry,
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
    def list_directory_entries(self):
        return list(ENTRIES)


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
            "Magistratura: Magistratura A"
            " · Dirección: Dirección B"
        )
    )
    assert (
        user["Principal"]
        == "Magistratura A"
    )
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
    assert user["Principal"] == "—"
    assert user["Estado"] == "Inactivo"
    assert user["Rol funcional"] == "—"
