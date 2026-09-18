from __future__ import annotations

from auth.models import AppActor, AuthIdentity


def _normalize_emails(values: tuple[str, ...]) -> frozenset[str]:
    return frozenset(value.strip().lower() for value in values if value.strip())


class AuthorizationService:
    def __init__(
        self,
        *,
        admin_emails: tuple[str, ...] = (),
        viewer_emails: tuple[str, ...] = (),
    ) -> None:
        self._admins = _normalize_emails(admin_emails)
        self._viewers = _normalize_emails(viewer_emails)

    def authorize(self, identity: AuthIdentity) -> AppActor | None:
        email = identity.email.strip().lower()

        if email in self._admins:
            return AppActor(identity.user_id, email, "admin")

        if email in self._viewers:
            return AppActor(identity.user_id, email, "viewer")

        return None
