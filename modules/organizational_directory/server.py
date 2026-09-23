from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

import pandas as pd
from shiny import (
    module,
    reactive,
    render,
)

from core.dependencies import AppDependencies
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

DIRECTORY_COLUMNS = [
    "Nombre",
    "Correo",
    "Rol funcional",
    "Magistratura / Dirección",
    "Principal",
    "Estado",
]


@dataclass(
    frozen=True,
    slots=True,
)
class DirectoryViewState:
    rows: tuple[
        dict[str, str],
        ...,
    ] = ()
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


@module.server
def organizational_directory_server(
    input,
    output,
    session,
    dependencies: AppDependencies,
    *,
    is_authenticated: Callable[
        [],
        bool,
    ],
    is_admin: Callable[
        [],
        bool,
    ],
    is_active: Callable[
        [],
        bool,
    ],
):
    service = (
        OrganizationalDirectoryService(
            dependencies
        )
    )

    @reactive.calc
    def directory_state():
        return load_directory_state(
            service,
            is_authenticated=(
                is_authenticated()
            ),
            is_admin=is_admin(),
            is_active=is_active(),
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

        count = len(state.rows)

        if count == 0:
            return (
                "No hay usuarios registrados "
                "en el directorio."
            )

        return (
            f"{count} usuarios registrados"
        )

    @output
    @render.data_frame
    def directory_table():
        state = directory_state()
        frame = pd.DataFrame(
            state.rows,
            columns=DIRECTORY_COLUMNS,
        )

        return render.DataGrid(
            frame,
            filters=True,
            width="100%",
            height="560px",
        )
