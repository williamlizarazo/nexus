from types import SimpleNamespace

from memory_core.domain.organization_directory_entry import (
    OrganizationDirectoryEntry,
)

from modules.organizational_directory.server import (
    DIRECTORY_UNAVAILABLE_MESSAGE,
    load_directory_state,
)
from services.organizational_directory_service import (
    OrganizationalDirectoryService,
)


class CountingRepository:
    def __init__(
        self,
        *,
        entries=(),
        error=None,
    ):
        self.calls = 0
        self.entries = entries
        self.error = error

    def list_directory_entries(self):
        self.calls += 1

        if self.error:
            raise self.error

        return list(self.entries)


def service(repository):
    return OrganizationalDirectoryService(
        SimpleNamespace(
            organization_directory_repository=(
                repository
            )
        )
    )


def test_viewer_does_not_read_repository():
    repository = CountingRepository()

    state = load_directory_state(
        service(repository),
        is_authenticated=True,
        is_admin=False,
        is_active=True,
    )

    assert state.rows == ()
    assert repository.calls == 0


def test_logged_out_does_not_read_repository():
    repository = CountingRepository()

    state = load_directory_state(
        service(repository),
        is_authenticated=False,
        is_admin=True,
        is_active=True,
    )

    assert state.rows == ()
    assert repository.calls == 0


def test_inactive_tab_does_not_read_repository():
    repository = CountingRepository()

    state = load_directory_state(
        service(repository),
        is_authenticated=True,
        is_admin=True,
        is_active=False,
    )

    assert state.rows == ()
    assert repository.calls == 0


def test_active_admin_reads_and_presents_repository():
    repository = CountingRepository(
        entries=(
            OrganizationDirectoryEntry(
                user_id="user-1",
                email="persona@jep.gov.co",
                full_name="Persona Uno",
                functional_role="Investigador",
                user_status="active",
            ),
        )
    )

    state = load_directory_state(
        service(repository),
        is_authenticated=True,
        is_admin=True,
        is_active=True,
    )

    assert repository.calls == 1
    assert state.error_message is None
    assert state.rows == (
        {
            "Nombre": "Persona Uno",
            "Correo": "persona@jep.gov.co",
            "Rol funcional": "Investigador",
            "Magistratura / Dirección": "—",
            "Principal": "—",
            "Estado": "Activo",
        },
    )


def test_backend_error_is_not_exposed():
    repository = CountingRepository(
        error=RuntimeError(
            "secret backend error"
        )
    )

    state = load_directory_state(
        service(repository),
        is_authenticated=True,
        is_admin=True,
        is_active=True,
    )

    assert state.rows == ()
    assert (
        state.error_message
        == DIRECTORY_UNAVAILABLE_MESSAGE
    )
    assert (
        "secret backend error"
        not in state.error_message
    )
    assert repository.calls == 1
