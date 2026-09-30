from memory_core.contracts.nexus_projection_queue import (
    NexusProjectionQueueRepository,
)
from memory_core.domain.nexus_projection_event import NexusProjectionEvent


class FakeProjectionQueue:
    def claim(
        self,
        *,
        worker_id: str,
        limit: int = 50,
        lease_seconds: int = 120,
    ) -> list[NexusProjectionEvent]:
        return []

    def complete(
        self,
        *,
        event_id: str,
        worker_id: str,
    ) -> NexusProjectionEvent:
        raise NotImplementedError

    def retry(
        self,
        *,
        event_id: str,
        worker_id: str,
        error: str,
        delay_seconds: int = 30,
    ) -> NexusProjectionEvent:
        raise NotImplementedError

    def fail(
        self,
        *,
        event_id: str,
        worker_id: str,
        error: str,
    ) -> NexusProjectionEvent:
        raise NotImplementedError


def test_projection_queue_contract_is_runtime_checkable():
    repository = FakeProjectionQueue()

    assert isinstance(repository, NexusProjectionQueueRepository)
