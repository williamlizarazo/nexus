from types import SimpleNamespace

from memory_core.organization import MemoryUser
from memory_core.organization.adapters.supabase import (
    SupabaseOrganizationDirectoryRepository,
)


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows
        self.filters = {}
        self.upsert_payload = None

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, field, value):
        self.filters[field] = value
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def upsert(self, payload, on_conflict=None):
        self.upsert_payload = dict(payload)

        existing = next(
            (
                row for row in self.rows
                if row["user_id"] == payload["user_id"]
            ),
            None,
        )

        if existing is None:
            existing = {
                **payload,
                "created_at": "2026-09-17T14:00:00+00:00",
                "updated_at": "2026-09-17T14:00:00+00:00",
            }
            self.rows.append(existing)
        else:
            existing.update(payload)

        return self

    def execute(self):
        result = list(self.rows)

        for field, value in self.filters.items():
            result = [
                row for row in result
                if str(row.get(field)) == str(value)
            ]

        return SimpleNamespace(data=result)


class FakeSupabaseClient:
    def __init__(self):
        self.rows = []

    def table(self, _name):
        return FakeQuery(self.rows)


def test_repository_upserts_and_gets_user():
    client = FakeSupabaseClient()
    repository = SupabaseOrganizationDirectoryRepository(client)

    user = MemoryUser(
        user_id="5ed03a08-700b-4140-af06-a458860e15cd",
        email="usuario@jep.gov.co",
    )

    stored = repository.upsert_user(user)
    recovered = repository.get_user(user.user_id)

    assert stored.user_id == user.user_id
    assert recovered is not None
    assert recovered.email == "usuario@jep.gov.co"


def test_repository_finds_user_by_email():
    client = FakeSupabaseClient()
    repository = SupabaseOrganizationDirectoryRepository(client)

    repository.upsert_user(
        MemoryUser(
            user_id="5ed03a08-700b-4140-af06-a458860e15cd",
            email="usuario@jep.gov.co",
        )
    )

    recovered = repository.get_user_by_email(
        "USUARIO@JEP.GOV.CO"
    )

    assert recovered is not None
    assert recovered.user_id == (
        "5ed03a08-700b-4140-af06-a458860e15cd"
    )
