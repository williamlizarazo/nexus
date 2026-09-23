from memory_core.organization.adapters.supabase import (
    SupabaseOrganizationDirectoryRepository,
)


class FakeResponse:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self):
        self.payload = None

    def insert(self, payload):
        self.payload = payload
        return self

    def execute(self):
        return FakeResponse(
            [
                {
                    "unit_id": "unit-1",
                    "name": self.payload["name"],
                    "unit_type": self.payload["unit_type"],
                    "status": self.payload["status"],
                }
            ]
        )


class FakeClient:
    def __init__(self):
        self.table_name = None
        self.query = FakeQuery()

    def table(self, name):
        self.table_name = name
        return self.query


def test_create_organizational_unit_inserts_active_row():
    client = FakeClient()
    repository = SupabaseOrganizationDirectoryRepository(
        client
    )

    unit = repository.create_organizational_unit(
        name="Magistrado Vidal",
        unit_type="magistratura",
    )

    assert client.table_name == (
        "memory_organizational_units"
    )
    assert client.query.payload == {
        "name": "Magistrado Vidal",
        "unit_type": "magistratura",
        "status": "active",
    }
    assert unit.unit_id == "unit-1"
    assert unit.name == "Magistrado Vidal"
    assert unit.unit_type == "magistratura"


def test_create_organizational_unit_rejects_empty_response():
    client = FakeClient()
    client.query.execute = lambda: FakeResponse([])
    repository = SupabaseOrganizationDirectoryRepository(
        client
    )

    try:
        repository.create_organizational_unit(
            name="Magistrado Vidal",
            unit_type="magistratura",
        )
    except RuntimeError as exc:
        assert "No fue posible crear" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")
