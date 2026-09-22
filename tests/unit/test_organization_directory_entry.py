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
