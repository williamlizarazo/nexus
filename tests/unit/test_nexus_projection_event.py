from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from memory_core.domain.nexus_projection_event import NexusProjectionEvent


def _event() -> NexusProjectionEvent:
    now = datetime(2026, 9, 30, 15, 0, tzinfo=timezone.utc)

    return NexusProjectionEvent(
        event_id="event-1",
        event_type="ANNOTATION_CHANGED",
        source_table="analysis_project_annotations",
        source_operation="UPDATE",
        source_record_key="annotation-1",
        project_id="project-1",
        user_id=None,
        unit_id=None,
        doc_id="doc-1",
        page_idx=4,
        old_values={"status": "active", "page_idx": 3},
        new_values={"status": "active", "page_idx": 4},
        status="processing",
        priority=100,
        attempts=1,
        max_attempts=5,
        available_at=now,
        claimed_by="ubuntu-nexus-worker",
        claimed_at=now,
        lease_until=now,
        processed_at=None,
        last_error=None,
        created_at=now,
        updated_at=now,
    )


def test_projection_event_models_claimed_queue_event():
    event = _event()

    assert event.event_id == "event-1"
    assert event.event_type == "ANNOTATION_CHANGED"
    assert event.project_id == "project-1"
    assert event.doc_id == "doc-1"
    assert event.page_idx == 4
    assert event.attempts == 1
    assert event.claimed_by == "ubuntu-nexus-worker"


def test_projection_event_is_immutable():
    event = _event()

    with pytest.raises(FrozenInstanceError):
        event.status = "done"
