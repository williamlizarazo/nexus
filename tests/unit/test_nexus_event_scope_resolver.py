from datetime import datetime, timezone

from memory_core.domain.nexus_projection_event import NexusProjectionEvent
from memory_core.services.nexus_event_scope_resolver import (
    NexusEventScopeResolver,
)


NOW = datetime(
    2026,
    9,
    30,
    15,
    0,
    tzinfo=timezone.utc,
)


def _event(
    *,
    event_type: str,
    project_id=None,
    user_id=None,
    unit_id=None,
    old_values=None,
    new_values=None,
):
    return NexusProjectionEvent(
        event_id="event-1",
        event_type=event_type,
        source_table="test",
        source_operation="UPDATE",
        source_record_key="record-1",
        project_id=project_id,
        user_id=user_id,
        unit_id=unit_id,
        doc_id=None,
        page_idx=None,
        old_values=old_values,
        new_values=new_values,
        status="processing",
        priority=100,
        attempts=1,
        max_attempts=5,
        available_at=NOW,
        claimed_by="worker-1",
        claimed_at=NOW,
        lease_until=NOW,
        processed_at=None,
        last_error=None,
        created_at=NOW,
        updated_at=NOW,
    )


def test_project_event_resolves_project_scope():
    scope = NexusEventScopeResolver.resolve(
        _event(
            event_type="PROJECT_CHANGED",
            project_id="project-1",
        )
    )

    assert scope.project_ids == (
        "project-1",
    )


def test_membership_change_includes_old_and_new_identity():
    scope = NexusEventScopeResolver.resolve(
        _event(
            event_type="PROJECT_MEMBERSHIP_CHANGED",
            project_id="project-2",
            user_id="user-2",
            old_values={
                "project_id": "project-1",
                "user_id": "user-1",
            },
            new_values={
                "project_id": "project-2",
                "user_id": "user-2",
            },
        )
    )

    assert scope.project_ids == (
        "project-1",
        "project-2",
    )

    assert scope.user_ids == (
        "user-1",
        "user-2",
    )


def test_user_unit_change_includes_old_and_new_scope():
    scope = NexusEventScopeResolver.resolve(
        _event(
            event_type="USER_UNIT_MEMBERSHIP_CHANGED",
            user_id="user-2",
            unit_id="unit-2",
            old_values={
                "user_id": "user-1",
                "unit_id": "unit-1",
            },
            new_values={
                "user_id": "user-2",
                "unit_id": "unit-2",
            },
        )
    )

    assert scope.user_ids == (
        "user-1",
        "user-2",
    )

    assert scope.unit_ids == (
        "unit-1",
        "unit-2",
    )


def test_annotation_identity_change_reconciles_both_projects():
    scope = NexusEventScopeResolver.resolve(
        _event(
            event_type="ANNOTATION_CHANGED",
            project_id="project-2",
            old_values={
                "project_id": "project-1",
            },
            new_values={
                "project_id": "project-2",
            },
        )
    )

    assert scope.project_ids == (
        "project-1",
        "project-2",
    )


def test_user_event_resolves_user_scope():
    scope = NexusEventScopeResolver.resolve(
        _event(
            event_type="USER_CHANGED",
            user_id="user-1",
        )
    )

    assert scope.user_ids == (
        "user-1",
    )


def test_unit_event_resolves_unit_scope():
    scope = NexusEventScopeResolver.resolve(
        _event(
            event_type="ORGANIZATIONAL_UNIT_CHANGED",
            unit_id="unit-1",
        )
    )

    assert scope.unit_ids == (
        "unit-1",
    )
