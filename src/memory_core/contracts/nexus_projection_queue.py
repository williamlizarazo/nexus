from __future__ import annotations

from typing import Protocol, runtime_checkable

from memory_core.domain.nexus_projection_event import NexusProjectionEvent


@runtime_checkable
class NexusProjectionQueueRepository(Protocol):

    def claim(
        self,
        *,
        worker_id: str,
        limit: int = 50,
        lease_seconds: int = 120,
    ) -> list[NexusProjectionEvent]:
        ...

    def complete(
        self,
        *,
        event_id: str,
        worker_id: str,
    ) -> NexusProjectionEvent:
        ...

    def retry(
        self,
        *,
        event_id: str,
        worker_id: str,
        error: str,
        delay_seconds: int = 30,
    ) -> NexusProjectionEvent:
        ...

    def fail(
        self,
        *,
        event_id: str,
        worker_id: str,
        error: str,
    ) -> NexusProjectionEvent:
        ...
