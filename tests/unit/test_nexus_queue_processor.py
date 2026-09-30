from datetime import datetime, timezone

from memory_core.domain.nexus_projection_event import NexusProjectionEvent
from memory_core.services.nexus_queue_processor import (
    NexusQueueProcessor,
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
    attempts=1,
    max_attempts=5,
):
    return NexusProjectionEvent(
        event_id="event-1",
        event_type="PROJECT_CHANGED",
        source_table="analysis_projects",
        source_operation="UPDATE",
        source_record_key="project-1",
        project_id="project-1",
        user_id=None,
        unit_id=None,
        doc_id=None,
        page_idx=None,
        old_values={"id": "project-1"},
        new_values={"id": "project-1"},
        status="processing",
        priority=100,
        attempts=attempts,
        max_attempts=max_attempts,
        available_at=NOW,
        claimed_by="worker-1",
        claimed_at=NOW,
        lease_until=NOW,
        processed_at=None,
        last_error=None,
        created_at=NOW,
        updated_at=NOW,
    )


class FakeQueue:
    def __init__(self, events):
        self.events = events
        self.completed = []
        self.retried = []
        self.failed = []

    def claim(
        self,
        *,
        worker_id,
        limit=50,
        lease_seconds=120,
    ):
        return list(self.events)

    def complete(
        self,
        *,
        event_id,
        worker_id,
    ):
        self.completed.append(
            (event_id, worker_id)
        )
        return _event()

    def retry(
        self,
        *,
        event_id,
        worker_id,
        error,
        delay_seconds=30,
    ):
        self.retried.append(
            (
                event_id,
                worker_id,
                error,
                delay_seconds,
            )
        )
        return _event()

    def fail(
        self,
        *,
        event_id,
        worker_id,
        error,
    ):
        self.failed.append(
            (
                event_id,
                worker_id,
                error,
            )
        )
        return _event()


class FakeReconciler:
    def __init__(self, error=None):
        self.error = error
        self.scopes = []

    def reconcile(self, *, scope):
        self.scopes.append(scope)

        if self.error is not None:
            raise self.error


def test_successful_event_is_completed():
    queue = FakeQueue([_event()])
    reconciler = FakeReconciler()

    processor = NexusQueueProcessor(
        queue=queue,
        reconciler=reconciler,
    )

    result = processor.process_batch(
        worker_id="worker-1",
    )

    assert result.claimed == 1
    assert result.completed == 1
    assert result.retried == 0
    assert result.failed == 0

    assert queue.completed == [
        ("event-1", "worker-1")
    ]

    assert reconciler.scopes[0].project_ids == (
        "project-1",
    )


def test_transient_failure_is_retried():
    queue = FakeQueue(
        [
            _event(
                attempts=1,
                max_attempts=5,
            )
        ]
    )

    reconciler = FakeReconciler(
        RuntimeError("temporary failure")
    )

    processor = NexusQueueProcessor(
        queue=queue,
        reconciler=reconciler,
    )

    result = processor.process_batch(
        worker_id="worker-1",
        retry_delay_seconds=45,
    )

    assert result.retried == 1
    assert result.failed == 0

    assert queue.retried[0][0] == "event-1"
    assert queue.retried[0][1] == "worker-1"
    assert "temporary failure" in queue.retried[0][2]
    assert queue.retried[0][3] == 45


def test_failure_at_max_attempts_is_terminal():
    queue = FakeQueue(
        [
            _event(
                attempts=5,
                max_attempts=5,
            )
        ]
    )

    reconciler = FakeReconciler(
        RuntimeError("persistent failure")
    )

    processor = NexusQueueProcessor(
        queue=queue,
        reconciler=reconciler,
    )

    result = processor.process_batch(
        worker_id="worker-1",
    )

    assert result.failed == 1
    assert result.retried == 0

    assert queue.failed[0][0] == "event-1"
    assert "persistent failure" in queue.failed[0][2]


def test_empty_queue_returns_zero_counts():
    processor = NexusQueueProcessor(
        queue=FakeQueue([]),
        reconciler=FakeReconciler(),
    )

    result = processor.process_batch(
        worker_id="worker-1",
    )

    assert result.claimed == 0
    assert result.completed == 0
    assert result.retried == 0
    assert result.failed == 0
