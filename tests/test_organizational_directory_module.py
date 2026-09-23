from types import SimpleNamespace

import pytest

from memory_core.domain.organization_directory_entry import (
    OrganizationDirectoryEntry,
    OrganizationUnitOption,
)

from modules.organizational_directory.server import (
    DIRECTORY_UNAVAILABLE_MESSAGE,
    _pending_new_unit_name,
    _selected_values,
    _selection_with_unit,
    create_unit_selection,
    directory_table_ui,
    filter_directory_rows,
    load_directory_state,
    new_unit_form_ui,
    organizational_unit_choices,
    user_editor_modal,
)
from modules.organizational_directory.ui import (
    organizational_directory_ui,
)
from shiny._namespaces import ResolvedId
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


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, ()),
        ("", ()),
        ("unit-1", ("unit-1",)),
        (["unit-1", "unit-2"], ("unit-1", "unit-2")),
    ],
)
def test_selected_values_preserve_ids_without_splitting_strings(
    value,
    expected,
):
    assert _selected_values(value) == expected


def test_selection_with_unit_appends_uuid_once():
    assert _selection_with_unit(
        "unit-1",
        "unit-2",
    ) == ["unit-1", "unit-2"]
    assert _selection_with_unit(
        ["unit-1", "unit-2"],
        "unit-1",
    ) == ["unit-1", "unit-2"]


def test_pending_new_unit_name_only_blocks_visible_form():
    assert _pending_new_unit_name(
        True,
        "  Magistrado Vidal  ",
    ) == "Magistrado Vidal"
    assert _pending_new_unit_name(
        False,
        "Magistrado Vidal",
    ) == ""


def test_create_unit_selection_returns_updated_choices_and_uuids():
    created_unit = OrganizationUnitOption(
        unit_id="unit-created",
        name="Magistrado Vidal",
        unit_type="magistratura",
    )

    class CreatingService:
        def create_organizational_unit(self, **_values):
            return created_unit

        def list_organizational_units(self):
            return (created_unit,)

    unit, choices, selected = create_unit_selection(
        CreatingService(),
        name="Magistrado Vidal",
        unit_type="magistratura",
        current_value="unit-existing",
    )

    assert unit is created_unit
    assert choices == {
        "unit-created": "Magistratura · Magistrado Vidal"
    }
    assert selected == [
        "unit-existing",
        "unit-created",
    ]


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
            "user_id": "user-1",
            "Nombre": "Persona Uno",
            "Correo": "persona@jep.gov.co",
            "Rol funcional": "Investigador",
            "Magistratura / Dirección": "—",
            "Estado": "Activo",
            "_unit_ids": (),
            "_functional_role": "Investigador",
            "_status": "active",
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


def test_filter_directory_rows_searches_only_visible_fields():
    rows = (
        {
            "user_id": "hidden-user-1",
            "Nombre": "Persona Uno",
            "Correo": "persona@jep.gov.co",
            "Rol funcional": "Investigador/a",
            "Magistratura / Dirección": "Magistratura A",
            "Estado": "Activo",
            "_unit_ids": ("hidden-unit-1",),
        },
        {
            "user_id": "hidden-user-2",
            "Nombre": "Persona Dos",
            "Correo": "dos@jep.gov.co",
            "Rol funcional": "Analista",
            "Magistratura / Dirección": "Dirección B",
            "Estado": "Inactivo",
            "_unit_ids": (),
        },
    )

    assert filter_directory_rows(rows, "DIRECCIÓN") == (
        rows[1],
    )
    assert filter_directory_rows(rows, "hidden-unit-1") == ()
    assert filter_directory_rows(rows, "  ") == rows


def test_directory_table_renders_edit_action_without_primary():
    row = {
        "user_id": "user-1",
        "Nombre": "Persona Uno",
        "Correo": "persona@jep.gov.co",
        "Rol funcional": "Investigador/a",
        "Magistratura / Dirección": "Magistratura A",
        "Estado": "Activo",
        "_unit_ids": ("unit-1",),
        "_functional_role": "Investigador/a",
        "_status": "active",
    }

    html = str(
        directory_table_ui(
            (row,),
            edit_input_id="directory-edit_user_id",
        )
    )

    assert "Acción" in html
    assert "Editar" in html
    assert "Principal" not in html
    assert "Shiny.setInputValue" in html
    assert "directory-edit_user_id" in html
    assert "user-1" in html


def test_organizational_unit_choices_include_type_and_name():
    choices = organizational_unit_choices(
        (
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
        )
    )

    assert choices == {
        "unit-1": "Magistratura · Magistratura A",
        "unit-2": "Dirección · Dirección B",
    }


def test_directory_ui_exposes_search_and_html_table_output():
    html = str(
        organizational_directory_ui("directory")
    )

    assert "directory-directory_search" in html
    assert "directory-directory_table" in html
    assert "Buscar por nombre, correo, rol" in html
    assert "shiny-data-frame-output" not in html


def test_user_editor_modal_renders_readonly_email_and_selections():
    selected = {
        "Nombre": "Persona Uno",
        "Correo": "persona@jep.gov.co",
        "_functional_role": "Investigador/a",
        "_unit_ids": ("unit-1",),
        "_status": "active",
    }
    units = (
        OrganizationUnitOption(
            unit_id="unit-1",
            name="Magistratura A",
            unit_type="magistratura",
        ),
    )

    html = str(
        user_editor_modal(
            selected,
            units,
            ns=ResolvedId("directory"),
        )
    )

    assert "Editar usuario" in html
    assert 'id="directory-edit_email"' in html
    assert "readonly" in html
    assert "directory-edit_unit_ids" in html
    assert "multiple" in html
    assert '"create": false' in html
    assert "directory-show_new_unit" in html
    assert "+ Agregar Magistratura / Dirección" in html
    assert "directory-new_unit_form" in html
    assert "Cancelar" in html
    assert "Guardar" in html


def test_new_unit_form_renders_type_name_and_actions():
    html = str(
        new_unit_form_ui(
            ns=ResolvedId("directory")
        )
    )

    assert "Nueva Magistratura / Dirección" in html
    assert "directory-new_unit_type" in html
    assert 'value="magistratura"' in html
    assert 'value="direccion"' in html
    assert "directory-new_unit_name" in html
    assert "directory-cancel_new_unit" in html
    assert "directory-create_new_unit" in html
