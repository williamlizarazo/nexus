from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
import json
import logging
from typing import Any

from memory_core.domain.organization_directory_entry import (
    OrganizationUnitOption,
)
from shiny import (
    module,
    reactive,
    render,
    ui,
)

from core.dependencies import AppDependencies
from core.organizational_directory_catalog import (
    FUNCTIONAL_ROLE_CHOICES,
    USER_STATUS_CHOICES,
)
from presenters.organizational_directory_presenter import (
    OrganizationalDirectoryPresenter,
)
from services.organizational_directory_service import (
    OrganizationalDirectoryService,
)


LOGGER = logging.getLogger(__name__)

DIRECTORY_UNAVAILABLE_MESSAGE = (
    "Directorio organizacional no disponible."
)

VISIBLE_FIELDS = (
    "Nombre",
    "Correo",
    "Rol funcional",
    "Magistratura / Dirección",
    "Estado",
)


@dataclass(
    frozen=True,
    slots=True,
)
class DirectoryViewState:
    rows: tuple[dict[str, Any], ...] = ()
    error_message: str | None = None


def load_directory_state(
    service: OrganizationalDirectoryService,
    *,
    is_authenticated: bool,
    is_admin: bool,
    is_active: bool,
) -> DirectoryViewState:
    if (
        not is_authenticated
        or not is_admin
        or not is_active
    ):
        return DirectoryViewState()

    try:
        entries = service.list_entries()
        rows = (
            OrganizationalDirectoryPresenter
            .rows(entries)
        )
    except Exception:
        LOGGER.exception(
            "Unable to load organizational directory"
        )
        return DirectoryViewState(
            error_message=(
                DIRECTORY_UNAVAILABLE_MESSAGE
            )
        )

    return DirectoryViewState(
        rows=tuple(rows)
    )


def filter_directory_rows(
    rows: tuple[dict[str, Any], ...],
    query: str | None,
) -> tuple[dict[str, Any], ...]:
    normalized_query = (
        query or ""
    ).strip().casefold()

    if not normalized_query:
        return rows

    return tuple(
        row
        for row in rows
        if any(
            normalized_query
            in str(row.get(field, "")).casefold()
            for field in VISIBLE_FIELDS
        )
    )


def organizational_unit_choices(
    units: Iterable[OrganizationUnitOption],
) -> dict[str, str]:
    unit_type_labels = {
        "magistratura": "Magistratura",
        "direccion": "Dirección",
    }

    return {
        unit.unit_id: (
            f"{unit_type_labels.get(unit.unit_type, unit.unit_type)}"
            f" · {unit.name}"
        )
        for unit in units
    }


def _selected_values(
    value: Any,
) -> tuple[str, ...]:
    if value is None:
        return ()

    if isinstance(value, str):
        return (value,) if value else ()

    return tuple(
        str(item)
        for item in value
        if item
    )


def _selection_with_unit(
    value: Any,
    unit_id: str,
) -> list[str]:
    return list(
        dict.fromkeys(
            [
                *_selected_values(value),
                unit_id,
            ]
        )
    )


def _pending_new_unit_name(
    show_form: bool,
    value: str | None,
) -> str:
    if not show_form:
        return ""

    return (value or "").strip()


def create_unit_selection(
    service: OrganizationalDirectoryService,
    *,
    name: str,
    unit_type: str,
    current_value: Any,
) -> tuple[
    OrganizationUnitOption,
    dict[str, str],
    list[str],
]:
    unit = service.create_organizational_unit(
        name=name,
        unit_type=unit_type,
    )
    choices = organizational_unit_choices(
        service.list_organizational_units()
    )
    selected = _selection_with_unit(
        current_value,
        unit.unit_id,
    )

    return unit, choices, selected


def directory_table_ui(
    rows: tuple[dict[str, Any], ...],
    *,
    edit_input_id: str,
):
    if not rows:
        return ui.p(
            "No se encontraron usuarios.",
            class_="text-muted p-3",
        )

    body_rows = []

    for row in rows:
        user_id = str(row["user_id"])
        onclick = (
            "Shiny.setInputValue("
            f"{json.dumps(edit_input_id)}, "
            f"{json.dumps(user_id)}, "
            "{priority: 'event'}"
            ")"
        )

        body_rows.append(
            ui.tags.tr(
                *(
                    ui.tags.td(row[field])
                    for field in VISIBLE_FIELDS
                ),
                ui.tags.td(
                    ui.tags.button(
                        "Editar",
                        type="button",
                        class_=(
                            "btn btn-sm "
                            "btn-outline-primary"
                        ),
                        onclick=onclick,
                    )
                ),
            )
        )

    return ui.tags.div(
        ui.tags.table(
            ui.tags.thead(
                ui.tags.tr(
                    *(
                        ui.tags.th(field)
                        for field in VISIBLE_FIELDS
                    ),
                    ui.tags.th("Acción"),
                )
            ),
            ui.tags.tbody(*body_rows),
            class_=(
                "table table-hover "
                "align-middle mb-0"
            ),
        ),
        class_="table-responsive",
    )


def new_unit_form_ui(
    *,
    ns: Callable[[str], str],
):
    return ui.div(
        ui.hr(),
        ui.h6(
            "Nueva Magistratura / Dirección"
        ),
        ui.input_radio_buttons(
            ns("new_unit_type"),
            "Tipo",
            choices={
                "magistratura": "Magistratura",
                "direccion": "Dirección",
            },
            selected="magistratura",
            inline=True,
        ),
        ui.input_text(
            ns("new_unit_name"),
            "Nombre",
            placeholder="Ej. Magistrado Vidal",
        ),
        ui.div(
            ui.input_action_button(
                ns("cancel_new_unit"),
                "Cancelar",
                class_=(
                    "btn btn-sm "
                    "btn-outline-secondary"
                ),
            ),
            ui.input_action_button(
                ns("create_new_unit"),
                "Crear unidad",
                class_=(
                    "btn btn-sm "
                    "btn-primary ms-2"
                ),
            ),
            class_="mb-3",
        ),
        class_=(
            "border rounded "
            "p-3 mb-3 bg-light"
        ),
    )


def user_editor_modal(
    selected: dict[str, Any],
    units: Iterable[OrganizationUnitOption],
    *,
    ns: Callable[[str], str],
):
    email_id = ns("edit_email")

    return ui.modal(
        ui.input_text(
            ns("edit_full_name"),
            "Nombre",
            value=selected["Nombre"],
        ),
        ui.div(
            ui.tags.label(
                "Correo",
                for_=email_id,
                class_="control-label",
            ),
            ui.tags.input(
                id=email_id,
                type="text",
                value=selected["Correo"],
                readonly=True,
                class_="form-control",
            ),
            class_="form-group shiny-input-container",
        ),
        ui.input_select(
            ns("edit_functional_role"),
            "Rol funcional",
            choices=FUNCTIONAL_ROLE_CHOICES,
            selected=(
                selected["_functional_role"]
                or None
            ),
        ),
        ui.input_selectize(
            ns("edit_unit_ids"),
            "Magistratura / Dirección",
            choices=organizational_unit_choices(units),
            selected=list(selected["_unit_ids"]),
            multiple=True,
            remove_button=True,
            options={
                "create": False,
                "placeholder": (
                    "Seleccione una o varias "
                    "Magistraturas/Direcciones"
                ),
            },
        ),
        ui.input_action_button(
            ns("show_new_unit"),
            "+ Agregar Magistratura / Dirección",
            class_=(
                "btn btn-sm "
                "btn-outline-secondary mb-2"
            ),
        ),
        ui.output_ui(
            ns("new_unit_form")
        ),
        ui.input_select(
            ns("edit_status"),
            "Estado",
            choices=USER_STATUS_CHOICES,
            selected=selected["_status"],
        ),
        title="Editar usuario",
        easy_close=False,
        footer=ui.div(
            ui.modal_button("Cancelar"),
            ui.input_action_button(
                ns("save_user"),
                "Guardar",
                class_="btn-primary",
            ),
            class_=(
                "d-flex gap-2 "
                "justify-content-end"
            ),
        ),
    )


@module.server
def organizational_directory_server(
    input,
    output,
    session,
    dependencies: AppDependencies,
    *,
    is_authenticated: Callable[[], bool],
    is_admin: Callable[[], bool],
    is_active: Callable[[], bool],
):
    service = OrganizationalDirectoryService(
        dependencies
    )
    refresh_token = reactive.Value(0)
    editing_user_id = reactive.Value(None)
    show_new_unit_form = reactive.Value(False)

    @reactive.calc
    def directory_state():
        refresh_token.get()

        return load_directory_state(
            service,
            is_authenticated=is_authenticated(),
            is_admin=is_admin(),
            is_active=is_active(),
        )

    @reactive.calc
    def filtered_rows():
        return filter_directory_rows(
            directory_state().rows,
            input.directory_search(),
        )

    @output
    @render.text
    def directory_status():
        if (
            not is_authenticated()
            or not is_admin()
            or not is_active()
        ):
            return ""

        state = directory_state()

        if state.error_message:
            return state.error_message

        count = len(filtered_rows())

        if count == 0:
            return "No hay usuarios para mostrar."

        if count == 1:
            return "1 usuario registrado"

        return f"{count} usuarios registrados"

    @output
    @render.ui
    def directory_table():
        return directory_table_ui(
            filtered_rows(),
            edit_input_id=session.ns(
                "edit_user_id"
            ),
        )

    @reactive.effect
    @reactive.event(input.edit_user_id)
    def open_user_editor():
        user_id = input.edit_user_id()

        if not user_id:
            return

        selected = next(
            (
                row
                for row in directory_state().rows
                if row["user_id"] == user_id
            ),
            None,
        )

        if selected is None:
            return

        try:
            units = service.list_organizational_units()
        except Exception:
            LOGGER.exception(
                "Unable to load organizational units"
            )
            ui.notification_show(
                DIRECTORY_UNAVAILABLE_MESSAGE,
                type="error",
                duration=5,
            )
            return

        editing_user_id.set(user_id)
        show_new_unit_form.set(False)
        ui.modal_show(
            user_editor_modal(
                selected,
                units,
                ns=session.ns,
            )
        )

    @reactive.effect
    @reactive.event(input.show_new_unit)
    def show_new_unit():
        show_new_unit_form.set(True)

    @output
    @render.ui
    def new_unit_form():
        if not show_new_unit_form.get():
            return None

        return new_unit_form_ui(
            ns=session.ns
        )

    @reactive.effect
    @reactive.event(input.cancel_new_unit)
    def cancel_new_unit():
        show_new_unit_form.set(False)

    @reactive.effect
    @reactive.event(input.create_new_unit)
    def create_new_unit():
        if (
            not is_authenticated()
            or not is_admin()
            or not is_active()
        ):
            return

        try:
            unit, choices, selected = (
                create_unit_selection(
                    service,
                    name=(
                        input.new_unit_name()
                        or ""
                    ),
                    unit_type=(
                        input.new_unit_type()
                        or ""
                    ),
                    current_value=(
                        input.edit_unit_ids()
                    ),
                )
            )
        except ValueError as exc:
            ui.notification_show(
                str(exc),
                type="warning",
                duration=5,
            )
            return
        except Exception:
            LOGGER.exception(
                "Unable to create organizational unit"
            )
            ui.notification_show(
                (
                    "No fue posible crear la "
                    "Magistratura/Dirección."
                ),
                type="error",
                duration=5,
            )
            return

        ui.update_selectize(
            "edit_unit_ids",
            choices=choices,
            selected=selected,
            session=session,
        )
        show_new_unit_form.set(False)
        ui.notification_show(
            (
                f"{unit.name} quedó disponible "
                "y seleccionado."
            ),
            type="message",
            duration=3,
        )

    @reactive.effect
    @reactive.event(input.save_user)
    def save_user():
        if (
            not is_authenticated()
            or not is_admin()
            or not is_active()
        ):
            return

        user_id = editing_user_id.get()

        if not user_id:
            return

        pending_name = _pending_new_unit_name(
            show_new_unit_form.get(),
            input.new_unit_name(),
        )

        if pending_name:
            ui.notification_show(
                (
                    "Primero pulsa 'Crear unidad' "
                    "para registrar la nueva "
                    "Magistratura/Dirección."
                ),
                type="warning",
                duration=5,
            )
            return

        selected_unit_ids = _selected_values(
            input.edit_unit_ids()
        )

        try:
            service.update_user(
                user_id=user_id,
                full_name=(
                    input.edit_full_name() or ""
                ),
                functional_role=(
                    input.edit_functional_role()
                    or ""
                ),
                status=(
                    input.edit_status()
                    or "active"
                ),
                unit_ids=selected_unit_ids,
            )
        except ValueError as exc:
            ui.notification_show(
                str(exc),
                type="error",
                duration=5,
            )
            return
        except Exception:
            LOGGER.exception(
                "Unable to update directory user"
            )
            ui.notification_show(
                "No fue posible guardar los cambios.",
                type="error",
                duration=5,
            )
            return

        ui.modal_remove()
        editing_user_id.set(None)
        refresh_token.set(
            refresh_token.get() + 1
        )
        ui.notification_show(
            "Usuario actualizado.",
            type="message",
            duration=3,
        )
