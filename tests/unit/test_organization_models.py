import pytest

from memory_core.organization.models import MemoryUser


def test_memory_user_accepts_minimal_identity():
    user = MemoryUser(
        user_id="5ed03a08-700b-4140-af06-a458860e15cd",
        email="usuario@jep.gov.co",
    )

    assert user.user_id == "5ed03a08-700b-4140-af06-a458860e15cd"
    assert user.email == "usuario@jep.gov.co"
    assert user.full_name is None
    assert user.functional_role is None
    assert user.status == "active"


def test_memory_user_can_be_enriched_later():
    user = MemoryUser(
        user_id="5ed03a08-700b-4140-af06-a458860e15cd",
        email="usuario@jep.gov.co",
        full_name="Usuario Ejemplo",
        functional_role="Investigador",
    )

    assert user.full_name == "Usuario Ejemplo"
    assert user.functional_role == "Investigador"


def test_memory_user_normalizes_email():
    user = MemoryUser(
        user_id="abc",
        email="  Usuario@JEP.GOV.CO  ",
    )

    assert user.email == "usuario@jep.gov.co"


def test_memory_user_requires_identity():
    with pytest.raises(ValueError):
        MemoryUser(
            user_id="",
            email="usuario@jep.gov.co",
        )


def test_memory_user_requires_email():
    with pytest.raises(ValueError):
        MemoryUser(
            user_id="abc",
            email="",
        )


def test_memory_user_rejects_unknown_status():
    with pytest.raises(ValueError):
        MemoryUser(
            user_id="abc",
            email="usuario@jep.gov.co",
            status="deleted",
        )
