from __future__ import annotations

from dataclasses import dataclass

from memory_core.contracts.nexus_projection_queue import (
    NexusProjectionQueueRepository,
)
from memory_core.services.nexus_event_scope_resolver import (
    NexusEventScopeResolver,
)
from memory_core.services.nexus_incremental_reconciler import (
    NexusIncrementalReconciler,
)


@dataclass(frozen=True, slots=True)
class NexusQueueBatchResult:
    claimed: int
    completed: int
    retried: int
    failed: int


class NexusQueueProcessor:
    """
    Procesa un lote de eventos NEXUS ya persistidos en la cola.

    Coordina:
    claim -> scope -> reconcile -> complete/retry/fail.
    """

    def __init__(
        self,
        *,
        queue: NexusProjectionQueueRepository,
        reconciler: NexusIncrementalReconciler,
    ) -> None:
        self._queue = queue
        self._reconciler = reconciler

    def process_batch(
        self,
        *,
        worker_id: str,
        limit: int = 50,
        lease_seconds: int = 120,
        retry_delay_seconds: int = 30,
    ) -> NexusQueueBatchResult:

        events = self._queue.claim(
            worker_id=worker_id,
            limit=limit,
            lease_seconds=lease_seconds,
        )

        completed = 0
        retried = 0
        failed = 0

        for event in events:
            try:
                scope = NexusEventScopeResolver.resolve(
                    event
                )

                self._reconciler.reconcile(
                    scope=scope
                )

                self._queue.complete(
                    event_id=event.event_id,
                    worker_id=worker_id,
                )

                completed += 1

            except Exception as exc:
                error = (
                    f"{type(exc).__name__}: {exc}"
                )

                if (
                    event.attempts
                    >= event.max_attempts
                ):
                    self._queue.fail(
                        event_id=event.event_id,
                        worker_id=worker_id,
                        error=error,
                    )

                    failed += 1

                else:
                    self._queue.retry(
                        event_id=event.event_id,
                        worker_id=worker_id,
                        error=error,
                        delay_seconds=(
                            retry_delay_seconds
                        ),
                    )

                    retried += 1

        return NexusQueueBatchResult(
            claimed=len(events),
            completed=completed,
            retried=retried,
            failed=failed,
        )
