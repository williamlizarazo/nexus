import pytest

from auth.models import AuthIdentity
from auth.service import AuthenticationError, AuthService


class FakeAuthProvider:
    def __init__(self):
        self.received = None

    def authenticate(
        self,
        email: str,
        password: str,
    ) -> AuthIdentity:
        self.received = (email, password)
        return AuthIdentity(
            user_id="user-001",
            email=email,
        )


class FailingAuthProvider:
    def authenticate(
        self,
        email: str,
        password: str,
    ) -> AuthIdentity:
        raise RuntimeError("provider failure")


def test_login_normalizes_email():
    provider = FakeAuthProvider()
    identity = AuthService(provider).login(
        "  USER@EXAMPLE.ORG ",
        "secret",
    )

    assert identity == AuthIdentity(
        "user-001",
        "user@example.org",
    )
    assert provider.received == (
        "user@example.org",
        "secret",
    )


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("", "secret"),
        ("user@example.org", ""),
    ],
)
def test_login_rejects_empty_credentials(
    email,
    password,
):
    with pytest.raises(AuthenticationError):
        AuthService(FakeAuthProvider()).login(
            email,
            password,
        )


def test_login_hides_provider_error():
    with pytest.raises(
        AuthenticationError,
        match="No fue posible autenticar",
    ):
        AuthService(FailingAuthProvider()).login(
            "user@example.org",
            "secret",
        )
