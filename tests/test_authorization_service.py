from auth.models import AuthIdentity
from authorization.service import AuthorizationService


def test_admin_role_has_priority():
    service = AuthorizationService(
        admin_emails=("ADMIN@EXAMPLE.ORG",),
        viewer_emails=("admin@example.org",),
    )

    actor = service.authorize(AuthIdentity("user-001", "admin@example.org"))

    assert actor is not None and actor.role == "admin" and actor.is_admin


def test_viewer_is_authorized():
    service = AuthorizationService(viewer_emails=("viewer@example.org",))

    actor = service.authorize(AuthIdentity("user-002", "VIEWER@example.org"))

    assert actor is not None and actor.role == "viewer" and not actor.is_admin


def test_unknown_email_is_denied():
    service = AuthorizationService(admin_emails=("admin@example.org",))

    assert service.authorize(AuthIdentity("user-003", "other@example.org")) is None
