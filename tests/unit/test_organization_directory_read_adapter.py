from datetime import date

import pytest

from memory_core.organization.adapters.supabase import (
    SupabaseOrganizationDirectoryRepository,
)


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.selected_columns = None
        self.order_field = None

    def select(self, columns, *args, **kwargs):
        self.selected_columns = columns
        return self

    def order(self, field, *args, **kwargs):
        self.order_field = field
        return self

    def execute(self):
        return FakeResponse(self.rows)


class FakeClient:
    def __init__(self, rows):
        self.rows = rows
        self.table_name = None
        self.last_query = None

    def table(self, name):
        self.table_name = name
        self.last_query = FakeQuery(self.rows)
        return self.last_query


def test_repository_lists_directory_entries():
    client = FakeClient(
        [
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
            }
        ]
    )
    repository = SupabaseOrganizationDirectoryRepository(
        client
    )

    entries = repository.list_directory_entries()

    assert (
        client.table_name
        == "memory_organizational_directory_v"
    )
    assert client.last_query.selected_columns == (
        "user_id,email,full_name,functional_role,user_status,"
        "membership_id,is_primary,valid_from,valid_to,"
        "membership_status,unit_id,unit_name,unit_type,unit_status"
    )
    assert client.last_query.order_field == "full_name"
    assert len(entries) == 1

    entry = entries[0]

    assert entry.user_id == "user-1"
    assert entry.unit_name == "Magistratura A"
    assert entry.is_primary is True
    assert entry.valid_from == date(2026, 1, 1)
    assert entry.valid_to == date(2026, 12, 31)


def test_repository_handles_none_response():
    repository = (
        SupabaseOrganizationDirectoryRepository(
            FakeClient(None)
        )
    )

    assert (
        repository.list_directory_entries()
        == []
    )


def test_repository_rejects_invalid_date():
    repository = (
        SupabaseOrganizationDirectoryRepository(
            FakeClient(
                [
                    {
                        "user_id": "user-1",
                        "email": "persona@jep.gov.co",
                        "valid_from": "fecha-invalida",
                    }
                ]
            )
        )
    )

    with pytest.raises(ValueError):
        repository.list_directory_entries()
