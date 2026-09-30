from __future__ import annotations

from typing import Any

from memory_core.adapters.supabase.nexus_projection_queue import (
    SupabaseNexusProjectionQueueRepository,
)


EVENT_ROW = {
    "event_id": "11111111-1111-1111-1111-111111111111",
    "event_type": "ANNOTATION_CHANGED",
    "source_table": "analysis_project_annotations",
    "source_operation": "UPDATE",
    "source_record_key": "annotation-1",
    "project_id": "22222222-2222-2222-2222-222222222222",
    "user_id": None,
    "unit_id": None,
    "doc_id": "doc-1",
    "page_idx": 4,
    "old_values": {
        "status": "active",
        "page_idx": 3,
    },
    "new_values": {
        "status": "active",
        "page_idx": 4,
    },
    "status": "processing",
    "priority": 100,
    "attempts": 1,
    "max_attempts": 5,
    "available_at": "2026-09-30T15:00:00+00:00",
    "claimed_by": "ubuntu-nexus-worker",
    "claimed_at": "2026-09-30T15:01:00+00:00",
    "lease_until": "2026-09-30T15:03:00+00:00",
    "processed_at": None,
    "last_error": None,
    "created_at": "2026-09-30T14:59:00+00:00",
    "updated_at": "2026-09-30T15:01:00+00:00",
}


class FakeResponse:
    def __init__(self, data: Any) -> None:
        self.data = data


class FakeRpcCall:
    def __init__(
        self,
        client: "FakeClient",
        function_name: str,
        params: dict[str, Any],
    ) -> None:
        self.client = client
        self.function_name = function_name
        self.params = params

    def execute(self) -> FakeResponse:
        self.client.calls.append(
            (
                self.function_name,
                self.params,
            )
        )

        return FakeResponse(
            self.client.responses[
                self.function_name
            ]
        )


class FakeClient:
    def __init__(
        self,
        responses: dict[str, Any],
    ) -> None:
        self.responses = responses
        self.calls: list[
            tuple[str, dict[str, Any]]
        ] = []

    def rpc(
        self,
        function_name: str,
        params: dict[str, Any],
    ) -> FakeRpcCall:
        return FakeRpcCall(
            self,
            function_name,
            params,
        )


def test_claim_maps_supabase_rows_to_projection_events():
    client = FakeClient(
        {
            "nexus_claim_projection_events": [
                EVENT_ROW
            ]
        }
    )

    repository = SupabaseNexusProjectionQueueRepository(
        client
    )

    events = repository.claim(
        worker_id="ubuntu-nexus-worker",
        limit=10,
        lease_seconds=120,
    )

    assert len(events) == 1

    event = events[0]

    assert event.event_id == EVENT_ROW["event_id"]
    assert event.event_type == "ANNOTATION_CHANGED"
    assert event.doc_id == "doc-1"
    assert event.page_idx == 4
    assert event.status == "processing"
    assert event.attempts == 1
    assert event.claimed_by == "ubuntu-nexus-worker"

    assert event.claimed_at is not None
    assert event.claimed_at.tzinfo is not None

    assert client.calls == [
        (
            "nexus_claim_projection_events",
            {
                "p_worker_id": "ubuntu-nexus-worker",
                "p_limit": 10,
                "p_lease_seconds": 120,
            },
        )
    ]


def test_complete_calls_supabase_rpc():
    row = {
        **EVENT_ROW,
        "status": "done",
        "processed_at": "2026-09-30T15:02:00+00:00",
        "lease_until": None,
    }

    client = FakeClient(
        {
            "nexus_complete_projection_event": row
        }
    )

    repository = SupabaseNexusProjectionQueueRepository(
        client
    )

    event = repository.complete(
        event_id=EVENT_ROW["event_id"],
        worker_id="ubuntu-nexus-worker",
    )

    assert event.status == "done"

    assert client.calls == [
        (
            "nexus_complete_projection_event",
            {
                "p_event_id": EVENT_ROW["event_id"],
                "p_worker_id": "ubuntu-nexus-worker",
            },
        )
    ]


def test_retry_calls_supabase_rpc():
    row = {
        **EVENT_ROW,
        "status": "pending",
        "claimed_by": None,
        "claimed_at": None,
        "lease_until": None,
        "last_error": "temporary error",
    }

    client = FakeClient(
        {
            "nexus_retry_projection_event": row
        }
    )

    repository = SupabaseNexusProjectionQueueRepository(
        client
    )

    event = repository.retry(
        event_id=EVENT_ROW["event_id"],
        worker_id="ubuntu-nexus-worker",
        error="temporary error",
        delay_seconds=30,
    )

    assert event.status == "pending"
    assert event.last_error == "temporary error"

    assert client.calls == [
        (
            "nexus_retry_projection_event",
            {
                "p_event_id": EVENT_ROW["event_id"],
                "p_worker_id": "ubuntu-nexus-worker",
                "p_error": "temporary error",
                "p_delay_seconds": 30,
            },
        )
    ]


def test_fail_calls_supabase_rpc():
    row = {
        **EVENT_ROW,
        "status": "failed",
        "claimed_by": None,
        "claimed_at": None,
        "lease_until": None,
        "processed_at": "2026-09-30T15:02:00+00:00",
        "last_error": "terminal error",
    }

    client = FakeClient(
        {
            "nexus_fail_projection_event": row
        }
    )

    repository = SupabaseNexusProjectionQueueRepository(
        client
    )

    event = repository.fail(
        event_id=EVENT_ROW["event_id"],
        worker_id="ubuntu-nexus-worker",
        error="terminal error",
    )

    assert event.status == "failed"
    assert event.last_error == "terminal error"

    assert client.calls == [
        (
            "nexus_fail_projection_event",
            {
                "p_event_id": EVENT_ROW["event_id"],
                "p_worker_id": "ubuntu-nexus-worker",
                "p_error": "terminal error",
            },
        )
    ]
