# Organizational Directory Admin Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a read-only organizational directory backed by Supabase and visible only to authenticated `admin` actors in `appmemoria`.

**Architecture:** Extend the existing `memory_core` organizational repository with a canonical row model and a view-backed read method. Consume that method through an `appmemoria` service and presenter, then expose the grouped rows through a namespaced PyShiny module guarded independently by authentication and administrator authorization.

**Tech Stack:** Python 3.11, dataclasses, Protocol, Supabase Python client, PyShiny 1.8, pandas, pytest.

**Spec:** `docs/superpowers/specs/2026-09-22-organizational-directory-admin-design.md`

## Global Constraints

- Work spans the sibling repositories `memory_core` and `appmemoria`; keep their commits separate.
- Do not create or modify SQL, tables, views, RLS policies, Panorama, or Memoria episódica.
- Preserve `OrganizationDirectoryRepository.list_users()` and every existing repository method.
- Read only from `memory_organizational_directory_v`; add no directory write operation.
- Show and load the directory only for an authenticated actor whose `is_admin` property is true.
- Never expose a raw Supabase exception in the UI.
- Use the existing `AppDependencies.organization_directory_repository`; do not create a second dependency path.
- Use the pre-implementation tags `checkpoint/antes-directorio-organizacional-admin-2026-09-22` in `memory_core` and `checkpoint/antes-implementacion-sustancial-2026-09-22` in `appmemoria` for recovery.

## Review Focus

- A `viewer` or logged-out session must not call the repository even if the server module is registered; Task 4 tests the guard through the real load function.
- `response.data` may be `None`; Task 2 requires it to produce an empty list.
- A malformed membership date must not be silently changed; Task 2 requires `ValueError`, which Task 4 converts into the safe UI error state.
- Duplicate memberships and multiple primary flags must produce deterministic output; Task 3 tests deduplication, stable ordering, and the first sorted primary.
- Role changes and logout must affect both navigation and data access; Task 5 tests admin/viewer shell rendering and uses the same actor state for the server callback.

---

### Task 1: Add the canonical directory entry model

**Files:**
- Create: `../memory_core/src/memory_core/domain/organization_directory_entry.py`
- Create: `../memory_core/tests/unit/test_organization_directory_entry.py`

**Interfaces:**
- Consumes: standard-library `date` and `dataclass`.
- Produces: `OrganizationDirectoryEntry` with user, membership, unit, status, primary, and validity fields.

- [ ] **Step 1: Write the failing model tests**

```python
from datetime import date

from memory_core.domain.organization_directory_entry import (
    OrganizationDirectoryEntry,
)


def test_directory_entry_supports_user_without_unit():
    entry = OrganizationDirectoryEntry(
        user_id="user-1",
        email="persona@jep.gov.co",
        full_name="Persona Uno",
        functional_role="Investigador",
        user_status="active",
    )

    assert entry.membership_id is None
    assert entry.unit_id is None
    assert entry.unit_name is None
    assert entry.unit_type is None
    assert entry.unit_status is None
    assert entry.is_primary is False
    assert entry.valid_from is None
    assert entry.valid_to is None
    assert entry.membership_status is None


def test_directory_entry_preserves_membership_metadata():
    entry = OrganizationDirectoryEntry(
        user_id="user-1",
        email="persona@jep.gov.co",
        full_name="Persona Uno",
        functional_role="Investigador",
        user_status="active",
        membership_id="membership-1",
        unit_id="unit-1",
        unit_name="Magistratura A",
        unit_type="magistratura",
        unit_status="active",
        is_primary=True,
        valid_from=date(2026, 1, 1),
        valid_to=date(2026, 12, 31),
        membership_status="active",
    )

    assert entry.membership_id == "membership-1"
    assert entry.unit_name == "Magistratura A"
    assert entry.unit_type == "magistratura"
    assert entry.unit_status == "active"
    assert entry.is_primary is True
    assert entry.valid_from == date(2026, 1, 1)
    assert entry.valid_to == date(2026, 12, 31)
    assert entry.membership_status == "active"
```

- [ ] **Step 2: Run the tests and verify RED**

Run from `memory_core`:

```powershell
python -m pytest tests/unit/test_organization_directory_entry.py -q
```

Expected: collection fails with `ModuleNotFoundError` for `memory_core.domain.organization_directory_entry`.

- [ ] **Step 3: Implement the immutable model**

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True, slots=True)
class OrganizationDirectoryEntry:
    """Canonical row from the organizational directory."""

    user_id: str
    email: str
    full_name: str | None
    functional_role: str | None
    user_status: str
    membership_id: str | None = None
    unit_id: str | None = None
    unit_name: str | None = None
    unit_type: str | None = None
    unit_status: str | None = None
    is_primary: bool = False
    valid_from: date | None = None
    valid_to: date | None = None
    membership_status: str | None = None
```

- [ ] **Step 4: Run the focused and complete unit suites**

```powershell
python -m pytest tests/unit/test_organization_directory_entry.py -q
python -m pytest tests/unit -q
```

Expected: both commands exit 0.

- [ ] **Step 5: Commit the model in `memory_core`**

```powershell
git add src/memory_core/domain/organization_directory_entry.py tests/unit/test_organization_directory_entry.py
git commit -m "feat: add organizational directory entry model"
```

### Task 2: Extend the repository contract and Supabase adapter

**Files:**
- Modify: `../memory_core/src/memory_core/organization/ports.py:1-35`
- Modify: `../memory_core/src/memory_core/organization/adapters/supabase.py:1-174`
- Modify: `../memory_core/tests/unit/test_organization_supabase_adapter.py:1-105`

**Interfaces:**
- Consumes: `OrganizationDirectoryEntry` from Task 1 and the injected Supabase client.
- Produces: `OrganizationDirectoryRepository.list_directory_entries() -> list[OrganizationDirectoryEntry]` and its Supabase implementation.

- [ ] **Step 1: Make the fake client record the real boundary contract**

Extend the existing fakes without replacing their row storage:

```python
class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.filters = {}
        self.upsert_payload = None
        self.selected_columns = None
        self.order_field = None

    def select(self, columns, *_args, **_kwargs):
        self.selected_columns = columns
        return self

    def order(self, field, *_args, **_kwargs):
        self.order_field = field
        return self


class FakeSupabaseClient:
    def __init__(self):
        self.rows = []
        self.table_name = None
        self.last_query = None

    def table(self, name):
        self.table_name = name
        self.last_query = FakeQuery(self.rows)
        return self.last_query
```

Keep the current `eq`, `limit`, `upsert`, and `execute` behavior in `FakeQuery` unchanged.

- [ ] **Step 2: Write failing adapter tests**

```python
from datetime import date


def test_repository_lists_directory_entries_from_view():
    client = FakeSupabaseClient()
    client.rows = [
        {
            "user_id": "user-1",
            "email": "persona@jep.gov.co",
            "full_name": "Persona Uno",
            "functional_role": "Investigador",
            "user_status": "active",
            "membership_id": "membership-1",
            "is_primary": True,
            "valid_from": "2026-01-01",
            "valid_to": "2026-12-31",
            "membership_status": "active",
            "unit_id": "unit-1",
            "unit_name": "Magistratura A",
            "unit_type": "magistratura",
            "unit_status": "active",
        },
        {
            "user_id": "user-2",
            "email": "sinunidad@jep.gov.co",
            "full_name": None,
            "functional_role": None,
            "user_status": None,
            "membership_id": None,
            "is_primary": None,
            "valid_from": None,
            "valid_to": None,
            "membership_status": None,
            "unit_id": None,
            "unit_name": None,
            "unit_type": None,
            "unit_status": None,
        },
    ]
    repository = SupabaseOrganizationDirectoryRepository(client)

    entries = repository.list_directory_entries()

    assert client.table_name == "memory_organizational_directory_v"
    assert client.last_query.selected_columns == (
        "user_id,email,full_name,functional_role,user_status,"
        "membership_id,is_primary,valid_from,valid_to,"
        "membership_status,unit_id,unit_name,unit_type,unit_status"
    )
    assert client.last_query.order_field == "full_name"
    assert len(entries) == 2
    assert entries[0].membership_id == "membership-1"
    assert entries[0].valid_from == date(2026, 1, 1)
    assert entries[0].valid_to == date(2026, 12, 31)
    assert entries[1].user_status == "active"
    assert entries[1].unit_id is None
    assert entries[1].is_primary is False


def test_repository_handles_empty_directory_response():
    client = FakeSupabaseClient()
    client.rows = None
    repository = SupabaseOrganizationDirectoryRepository(client)

    assert repository.list_directory_entries() == []


def test_repository_rejects_malformed_membership_date():
    client = FakeSupabaseClient()
    client.rows = [
        {
            "user_id": "user-1",
            "email": "persona@jep.gov.co",
            "valid_from": "not-a-date",
        }
    ]
    repository = SupabaseOrganizationDirectoryRepository(client)

    with pytest.raises(ValueError):
        repository.list_directory_entries()
```

Add `import pytest` to the test file. Adjust `FakeQuery.execute()` to use `list(self.rows or [])`, preserving all existing filtering behavior.

- [ ] **Step 3: Run the adapter tests and verify RED**

```powershell
python -m pytest tests/unit/test_organization_supabase_adapter.py -q
```

Expected: the new tests fail because `list_directory_entries` does not exist.

- [ ] **Step 4: Extend the Protocol without removing existing methods**

In `organization/ports.py` import the model, retain all four existing methods,
and add this fifth method inside `OrganizationDirectoryRepository`:

```python
from memory_core.domain.organization_directory_entry import (
    OrganizationDirectoryEntry,
)
def list_directory_entries(
    self,
) -> list[OrganizationDirectoryEntry]:
    ...
```

- [ ] **Step 5: Implement date parsing and row mapping in the adapter**

Add beside `USER_COLUMNS`:

```python
from datetime import date, datetime

from memory_core.domain.organization_directory_entry import (
    OrganizationDirectoryEntry,
)


DIRECTORY_COLUMNS = (
    "user_id,email,full_name,functional_role,user_status,"
    "membership_id,is_primary,valid_from,valid_to,"
    "membership_status,unit_id,unit_name,unit_type,unit_status"
)


def _parse_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).strip())


def _directory_entry_from_row(
    row: dict[str, Any],
) -> OrganizationDirectoryEntry:
    return OrganizationDirectoryEntry(
        user_id=str(row["user_id"]),
        email=str(row["email"]),
        full_name=row.get("full_name"),
        functional_role=row.get("functional_role"),
        user_status=str(row.get("user_status") or "active"),
        membership_id=(
            str(row["membership_id"])
            if row.get("membership_id")
            else None
        ),
        unit_id=(
            str(row["unit_id"])
            if row.get("unit_id")
            else None
        ),
        unit_name=row.get("unit_name"),
        unit_type=row.get("unit_type"),
        unit_status=row.get("unit_status"),
        is_primary=bool(row.get("is_primary", False)),
        valid_from=_parse_date(row.get("valid_from")),
        valid_to=_parse_date(row.get("valid_to")),
        membership_status=row.get("membership_status"),
    )
```

Add to `SupabaseOrganizationDirectoryRepository` using the existing private client name:

```python
def list_directory_entries(
    self,
) -> list[OrganizationDirectoryEntry]:
    response = (
        self._client
        .table("memory_organizational_directory_v")
        .select(DIRECTORY_COLUMNS)
        .order("full_name")
        .execute()
    )
    return [
        _directory_entry_from_row(row)
        for row in (response.data or [])
    ]
```

- [ ] **Step 6: Run adapter and complete `memory_core` tests**

```powershell
python -m pytest tests/unit/test_organization_supabase_adapter.py -q
python -m pytest tests/unit -q
python -m compileall src/memory_core
git diff --check
```

Expected: all commands exit 0.

- [ ] **Step 7: Commit the contract and adapter in `memory_core`**

```powershell
git add src/memory_core/organization/ports.py src/memory_core/organization/adapters/supabase.py tests/unit/test_organization_supabase_adapter.py
git commit -m "feat: read organizational directory view"
```

### Task 3: Add the application service and grouped presenter

**Files:**
- Create: `services/organizational_directory_service.py`
- Create: `presenters/organizational_directory_presenter.py`
- Create: `tests/test_organizational_directory.py`

**Interfaces:**
- Consumes: `AppDependencies.organization_directory_repository` and `OrganizationDirectoryEntry` rows.
- Produces: `OrganizationalDirectoryService.list_entries()` and `OrganizationalDirectoryPresenter.rows()` with the six UI columns.

- [ ] **Step 1: Write failing service and presenter tests**

Create a complete literal fixture and tests:

```python
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


DIRECTORY_ENTRIES = [
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
        return list(DIRECTORY_ENTRIES)


def test_service_returns_repository_entries_as_tuple():
    service = OrganizationalDirectoryService(
        SimpleNamespace(
            organization_directory_repository=FakeRepository(),
        )
    )

    assert service.list_entries() == tuple(DIRECTORY_ENTRIES)


def test_service_returns_empty_tuple_without_repository():
    service = OrganizationalDirectoryService(
        SimpleNamespace(organization_directory_repository=None)
    )

    assert service.list_entries() == ()


def test_presenter_groups_and_orders_memberships_by_user():
    rows = OrganizationalDirectoryPresenter.rows(DIRECTORY_ENTRIES)

    assert rows == [
        {
            "Nombre": "Usuario Dos",
            "Correo": "usuario2@jep.gov.co",
            "Rol funcional": "—",
            "Magistratura / Dirección": "—",
            "Principal": "—",
            "Estado": "Inactivo",
        },
        {
            "Nombre": "Usuario Uno",
            "Correo": "usuario@jep.gov.co",
            "Rol funcional": "Investigador",
            "Magistratura / Dirección": (
                "Magistratura: Magistratura A · "
                "Dirección: Dirección B"
            ),
            "Principal": "Magistratura A",
            "Estado": "Activo",
        },
    ]


def test_presenter_keeps_unknown_unit_and_status_visible():
    entry = OrganizationDirectoryEntry(
        user_id="user-3",
        email="usuario3@jep.gov.co",
        full_name=None,
        functional_role=None,
        user_status="on_leave",
        unit_name="Equipo C",
        unit_type="secretaria_tecnica",
        is_primary=True,
    )

    assert OrganizationalDirectoryPresenter.rows([entry]) == [
        {
            "Nombre": "usuario3@jep.gov.co",
            "Correo": "usuario3@jep.gov.co",
            "Rol funcional": "—",
            "Magistratura / Dirección": "Secretaria Tecnica: Equipo C",
            "Principal": "Equipo C",
            "Estado": "On Leave",
        }
    ]
```

- [ ] **Step 2: Run the focused tests and verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_organizational_directory.py -q
```

Expected: collection fails because the service and presenter modules do not exist.

- [ ] **Step 3: Implement the service**

```python
from __future__ import annotations

from memory_core.domain.organization_directory_entry import (
    OrganizationDirectoryEntry,
)

from core.dependencies import AppDependencies


class OrganizationalDirectoryService:
    def __init__(self, dependencies: AppDependencies):
        self._repository = dependencies.organization_directory_repository

    def list_entries(
        self,
    ) -> tuple[OrganizationDirectoryEntry, ...]:
        if self._repository is None:
            return ()
        return tuple(self._repository.list_directory_entries())
```

- [ ] **Step 4: Implement deterministic presentation**

Implement `OrganizationalDirectoryPresenter.rows()` with these concrete rules:

```python
from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable
from typing import Any

from memory_core.domain.organization_directory_entry import (
    OrganizationDirectoryEntry,
)


class OrganizationalDirectoryPresenter:
    _UNIT_TYPES = {
        "magistratura": (0, "Magistratura"),
        "direccion": (1, "Dirección"),
    }
    _STATUS = {"active": "Activo", "inactive": "Inactivo"}

    @staticmethod
    def _readable(value: str) -> str:
        return value.replace("_", " ").strip().title()

    @classmethod
    def rows(
        cls,
        entries: Iterable[OrganizationDirectoryEntry],
    ) -> list[dict[str, str]]:
        users: OrderedDict[str, dict[str, Any]] = OrderedDict()

        for entry in entries:
            user = users.setdefault(
                entry.user_id,
                {
                    "name": entry.full_name or "",
                    "email": entry.email,
                    "role": entry.functional_role or "",
                    "status": entry.user_status or "",
                    "units": {},
                },
            )
            if not user["name"] and entry.full_name:
                user["name"] = entry.full_name
            if not user["role"] and entry.functional_role:
                user["role"] = entry.functional_role
            if not user["status"] and entry.user_status:
                user["status"] = entry.user_status
            if not entry.unit_name:
                continue

            normalized_type = (entry.unit_type or "").strip().lower()
            order, type_label = cls._UNIT_TYPES.get(
                normalized_type,
                (2, cls._readable(normalized_type) if normalized_type else ""),
            )
            label = (
                f"{type_label}: {entry.unit_name}"
                if type_label
                else entry.unit_name
            )
            key = (
                normalized_type,
                entry.unit_id or entry.unit_name.casefold(),
            )
            existing = user["units"].get(key)
            user["units"][key] = (
                order,
                type_label.casefold(),
                entry.unit_name.casefold(),
                label,
                entry.unit_name,
                bool(entry.is_primary or (existing and existing[5])),
            )

        result = []
        for user in users.values():
            units = sorted(user["units"].values())
            primary = next((unit[4] for unit in units if unit[5]), "—")
            status = user["status"]
            result.append(
                {
                    "Nombre": user["name"] or user["email"],
                    "Correo": user["email"],
                    "Rol funcional": user["role"] or "—",
                    "Magistratura / Dirección": (
                        " · ".join(unit[3] for unit in units) if units else "—"
                    ),
                    "Principal": primary,
                    "Estado": cls._STATUS.get(status, cls._readable(status)),
                }
            )

        return sorted(
            result,
            key=lambda row: (row["Nombre"].casefold(), row["Correo"].casefold()),
        )
```

- [ ] **Step 5: Run focused and complete `appmemoria` tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_organizational_directory.py -q
.\.venv\Scripts\python.exe -m pytest tests -q
```

Expected: both commands exit 0.

- [ ] **Step 6: Commit service and presenter in `appmemoria`**

```powershell
git add services/organizational_directory_service.py presenters/organizational_directory_presenter.py tests/test_organizational_directory.py
git commit -m "feat: present organizational directory entries"
```

### Task 4: Build the guarded PyShiny module

**Files:**
- Create: `modules/organizational_directory/__init__.py`
- Create: `modules/organizational_directory/ui.py`
- Create: `modules/organizational_directory/server.py`
- Create: `tests/test_organizational_directory_module.py`

**Interfaces:**
- Consumes: `OrganizationalDirectoryService`, `OrganizationalDirectoryPresenter`, `is_authenticated()`, and `is_admin()`.
- Produces: namespaced UI/server functions and a testable `load_directory_state()` security boundary.

- [ ] **Step 1: Write failing module and guard tests**

```python
from types import SimpleNamespace

from modules.organizational_directory.server import (
    DIRECTORY_UNAVAILABLE_MESSAGE,
    load_directory_state,
)
from modules.organizational_directory.ui import organizational_directory_ui
from services.organizational_directory_service import OrganizationalDirectoryService


class CountingRepository:
    def __init__(self, *, error=None):
        self.calls = 0
        self.error = error

    def list_directory_entries(self):
        self.calls += 1
        if self.error is not None:
            raise self.error
        return []


def _service(repository):
    return OrganizationalDirectoryService(
        SimpleNamespace(organization_directory_repository=repository)
    )


def test_module_ui_is_namespaced():
    html = str(organizational_directory_ui("organizational_directory"))

    assert "Directorio organizacional" in html
    assert "organizational_directory-directory_table" in html


def test_viewer_does_not_read_repository():
    repository = CountingRepository()

    state = load_directory_state(
        _service(repository),
        is_authenticated=True,
        is_admin=False,
    )

    assert state.rows == ()
    assert state.error_message is None
    assert repository.calls == 0


def test_logged_out_session_does_not_read_repository():
    repository = CountingRepository()

    state = load_directory_state(
        _service(repository),
        is_authenticated=False,
        is_admin=True,
    )

    assert state.rows == ()
    assert repository.calls == 0


def test_admin_receives_safe_state_when_repository_fails():
    repository = CountingRepository(error=RuntimeError("secret detail"))

    state = load_directory_state(
        _service(repository),
        is_authenticated=True,
        is_admin=True,
    )

    assert state.rows == ()
    assert state.error_message == DIRECTORY_UNAVAILABLE_MESSAGE
    assert "secret detail" not in state.error_message
    assert repository.calls == 1
```

- [ ] **Step 2: Run the module tests and verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_organizational_directory_module.py -q
```

Expected: collection fails because the module does not exist.

- [ ] **Step 3: Implement namespaced UI**

```python
from __future__ import annotations

from shiny import module, ui


@module.ui
def organizational_directory_ui():
    return ui.div(
        ui.h2("Directorio organizacional", class_="mb-1"),
        ui.p(
            "Usuarios, roles funcionales y pertenencias organizacionales.",
            class_="text-muted mb-3",
        ),
        ui.output_text("directory_status"),
        ui.output_data_frame("directory_table"),
        class_="p-3",
    )
```

- [ ] **Step 4: Implement the guarded load boundary and server**

```python
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import logging

import pandas as pd
from shiny import module, reactive, render

from core.dependencies import AppDependencies
from presenters.organizational_directory_presenter import OrganizationalDirectoryPresenter
from services.organizational_directory_service import OrganizationalDirectoryService


LOGGER = logging.getLogger(__name__)
DIRECTORY_UNAVAILABLE_MESSAGE = "Directorio organizacional no disponible."
DIRECTORY_COLUMNS = [
    "Nombre",
    "Correo",
    "Rol funcional",
    "Magistratura / Dirección",
    "Principal",
    "Estado",
]


@dataclass(frozen=True, slots=True)
class DirectoryViewState:
    rows: tuple[dict[str, str], ...] = ()
    error_message: str | None = None


def load_directory_state(
    service: OrganizationalDirectoryService,
    *,
    is_authenticated: bool,
    is_admin: bool,
) -> DirectoryViewState:
    if not is_authenticated or not is_admin:
        return DirectoryViewState()
    try:
        rows = OrganizationalDirectoryPresenter.rows(service.list_entries())
    except Exception:
        LOGGER.exception("Unable to load organizational directory")
        return DirectoryViewState(error_message=DIRECTORY_UNAVAILABLE_MESSAGE)
    return DirectoryViewState(rows=tuple(rows))


@module.server
def organizational_directory_server(
    input,
    output,
    session,
    dependencies: AppDependencies,
    *,
    is_authenticated: Callable[[], bool],
    is_admin: Callable[[], bool],
):
    service = OrganizationalDirectoryService(dependencies)

    @reactive.calc
    def directory_state():
        return load_directory_state(
            service,
            is_authenticated=is_authenticated(),
            is_admin=is_admin(),
        )

    @output
    @render.text
    def directory_status():
        state = directory_state()
        if state.error_message:
            return state.error_message
        if not is_authenticated() or not is_admin():
            return ""
        count = len(state.rows)
        if count == 0:
            return "No hay usuarios registrados en el directorio."
        return f"{count} usuarios registrados"

    @output
    @render.data_frame
    def directory_table():
        frame = pd.DataFrame(directory_state().rows, columns=DIRECTORY_COLUMNS)
        return render.DataGrid(frame, filters=True, width="100%", height="560px")
```

Export `organizational_directory_ui` and `organizational_directory_server` from the package `__init__.py`.

- [ ] **Step 5: Run module and complete tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_organizational_directory_module.py -q
.\.venv\Scripts\python.exe -m pytest tests -q
```

Expected: both commands exit 0 and the failure-path test may emit only the expected captured log record.

- [ ] **Step 6: Commit the PyShiny module**

```powershell
git add modules/organizational_directory tests/test_organizational_directory_module.py
git commit -m "feat: add guarded organizational directory module"
```

### Task 5: Integrate admin-only navigation and server wiring

**Files:**
- Modify: `ui.py:1-107`
- Modify: `server.py:1-169`
- Modify: `tests/test_authenticated_shell.py:1-35`
- Modify: `tests/test_server_auth_gate.py:1-31`

**Interfaces:**
- Consumes: `AuthSessionState.actor.is_admin` and the module from Task 4.
- Produces: admin-only navbar content plus `is_admin()` server callback sourced from the same session state.

- [ ] **Step 1: Write failing admin/viewer shell tests**

Update shell tests to make the role explicit:

```python
def test_admin_shell_exposes_organizational_directory():
    html = str(app_shell_ui(is_admin=True))

    assert "Directorio organizacional" in html
    assert "organizational_directory" in html


def test_viewer_shell_hides_organizational_directory():
    html = str(app_shell_ui(is_admin=False))

    assert "Directorio organizacional" not in html
    assert "organizational_directory" not in html
```

Add to `test_server_auth_gate.py`:

```python
def test_root_ui_exposes_directory_for_admin_only():
    admin = AuthSessionState.authenticated(
        AppActor("admin-1", "admin@example.org", "admin")
    )
    viewer = AuthSessionState.authenticated(
        AppActor("viewer-1", "viewer@example.org", "viewer")
    )

    assert "organizational_directory" in str(root_ui_for_auth_state(admin))
    assert "organizational_directory" not in str(root_ui_for_auth_state(viewer))
```

- [ ] **Step 2: Run the shell tests and verify RED**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_authenticated_shell.py tests/test_server_auth_gate.py -q
```

Expected: tests fail because `app_shell_ui` does not accept or apply `is_admin` and the directory panel does not exist.

- [ ] **Step 3: Make UI construction role-aware**

Import the module UI. Change signatures to:

```python
def app_shell_ui(*, is_admin: bool = False):
    directory_panel = (
        (
            ui.nav_panel(
                "Directorio organizacional",
                organizational_directory_ui("organizational_directory"),
                value="organizational_directory",
            ),
        )
        if is_admin
        else ()
    )

    return ui.page_navbar(
        ui.nav_panel(
            "Panorama de investigación",
            research_dashboard_ui(),
            value="research_dashboard",
        ),
        ui.nav_panel(
            "Memoria episódica",
            ui.layout_sidebar(
                episodic_sidebar_ui(),
                episodic_ui("episodic"),
            ),
            value="episodic",
        ),
        *directory_panel,
        ui.nav_spacer(),
        ui.nav_panel(
            "Diagnóstico",
            diagnostics_ui("diagnostics"),
            value="diagnostics",
        ),
        ui.nav_control(authentication_actor_ui()),
        title="appmemoria",
        id="main_nav",
        selected="research_dashboard",
        fillable=True,
    )


def app_root_ui(*, is_authenticated: bool, is_admin: bool = False):
    if not is_authenticated:
        return authentication_login_ui()
    return app_shell_ui(is_admin=is_admin)
```

This retains the existing Panorama, Memoria episódica, Diagnóstico, nav spacer,
actor control, title, IDs, selection, and layout arguments while inserting the
directory between Memoria episódica and the spacer.

- [ ] **Step 4: Derive UI and server authorization from `AuthSessionState`**

Update `root_ui_for_auth_state`:

```python
def root_ui_for_auth_state(state: AuthSessionState):
    actor = state.actor
    return app_root_ui(
        is_authenticated=state.is_authenticated,
        is_admin=bool(actor and actor.is_admin),
    )
```

Inside `create_server.server`, beside `_is_authenticated`, add:

```python
def _is_admin() -> bool:
    actor = auth_state.get().actor
    return bool(actor and actor.is_admin)
```

Register the module after the authentication callbacks are defined:

```python
organizational_directory_server(
    "organizational_directory",
    dependencies,
    is_authenticated=_is_authenticated,
    is_admin=_is_admin,
)
```

- [ ] **Step 5: Run authorization, module, and full application tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_authenticated_shell.py tests/test_server_auth_gate.py tests/test_organizational_directory_module.py -q
.\.venv\Scripts\python.exe -m pytest tests -q
```

Expected: all tests exit 0; the baseline was 62 tests and the final count must be reported from actual output.

- [ ] **Step 6: Commit shell and server integration**

```powershell
git add ui.py server.py tests/test_authenticated_shell.py tests/test_server_auth_gate.py
git commit -m "feat: expose organizational directory to admins"
```

### Task 6: Verify both repositories and the real read path

**Files:**
- Verify only; do not create SQL or persistence artifacts.

**Interfaces:**
- Consumes: the complete implementation from Tasks 1-5 and local environment configuration.
- Produces: objective unit, integration, compilation, formatting, read-only Supabase, and visual evidence.

- [ ] **Step 1: Run fresh complete suites in both repositories**

From `memory_core`:

```powershell
python -m pytest tests/unit -q
python -m compileall src/memory_core
git diff --check
git status --short --branch
```

From `appmemoria`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m compileall modules/organizational_directory services/organizational_directory_service.py presenters/organizational_directory_presenter.py ui.py server.py
git diff --check
git status --short --branch
```

Expected: both test suites and both compile commands exit 0; both diff checks are silent.

- [ ] **Step 2: Perform a read-only live Supabase probe when configured**

Run from `appmemoria` so `.env` is available:

```powershell
@'
from dotenv import load_dotenv

load_dotenv()

from memory_core.bootstrap import build_memory_runtime_from_env

runtime = build_memory_runtime_from_env()
repository = runtime.organization_directory_repository
entries = repository.list_directory_entries()
print(f"entries={len(entries)}")
for entry in entries[:5]:
    print(entry)
'@ | .\.venv\Scripts\python.exe -
```

Expected when configured: the command prints a nonnegative count and up to five `OrganizationDirectoryEntry` values without writing data. If configuration is absent, record the configuration error explicitly and continue with automated verification; do not weaken tests.

- [ ] **Step 3: Start PyShiny and validate admin rendering**

```powershell
.\.venv\Scripts\shiny.exe run app.py
```

Verify in the browser with an authorized admin account:

- navbar order is Panorama, Memoria episódica, Directorio organizacional, Diagnóstico;
- the directory heading, subtitle, count, filters, and six columns render;
- multiple memberships are grouped into one user row;
- no raw backend error is shown.

Then verify with a `viewer` account that the directory tab is absent. Stop the development server after inspection.

- [ ] **Step 4: Review the final commit and change boundaries**

```powershell
git -C ..\memory_core log --oneline --decorate -4
git -C ..\memory_core status --short --branch
git log --oneline --decorate -6
git status --short --branch
```

Confirm that neither repository contains SQL changes and that no Panorama or Memoria episódica behavior changed.
