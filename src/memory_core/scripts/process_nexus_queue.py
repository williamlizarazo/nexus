from __future__ import annotations

import argparse
import socket
from datetime import date

from supabase import Client

from memory_core.adapters.supabase.nexus_graph_projection import (
    SupabaseGraphProjectionRepository,
)
from memory_core.adapters.supabase.nexus_incremental_source import (
    SupabaseNexusIncrementalSource,
)
from memory_core.adapters.supabase.nexus_projection_queue import (
    SupabaseNexusProjectionQueueRepository,
)
from memory_core.scripts.backfill_nexus import (
    build_supabase_client_from_env,
    parse_reference_date,
)
from memory_core.services.nexus_incremental_reconciler import (
    NexusIncrementalReconciler,
)
from memory_core.services.nexus_projector import (
    NexusProjector,
)
from memory_core.services.nexus_queue_processor import (
    NexusQueueProcessor,
)


def build_processor(
    *,
    client: Client,
    reference_date: date,
) -> NexusQueueProcessor:

    queue = (
        SupabaseNexusProjectionQueueRepository(
            client
        )
    )

    source = (
        SupabaseNexusIncrementalSource(
            client
        )
    )

    projector = NexusProjector(
        reference_date=reference_date
    )

    repository = (
        SupabaseGraphProjectionRepository(
            client
        )
    )

    reconciler = NexusIncrementalReconciler(
        source=source,
        projector=projector,
        repository=repository,
    )

    return NexusQueueProcessor(
        queue=queue,
        reconciler=reconciler,
    )


def _build_parser(
) -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Process pending NEXUS "
            "incremental projection events."
        )
    )

    parser.add_argument(
        "--worker-id",
        default=socket.gethostname(),
        help=(
            "Unique worker identifier. "
            "Defaults to the machine hostname."
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum events to claim.",
    )

    parser.add_argument(
        "--lease-seconds",
        type=int,
        default=120,
        help="Queue claim lease duration.",
    )

    parser.add_argument(
        "--retry-delay-seconds",
        type=int,
        default=30,
        help="Delay before retrying a failed event.",
    )

    parser.add_argument(
        "--reference-date",
        default=None,
        help=(
            "Organizational reference date "
            "in YYYY-MM-DD format. "
            "Defaults to today's date."
        ),
    )

    return parser


def main(
    argv: list[str] | None = None,
) -> int:

    args = (
        _build_parser()
        .parse_args(argv)
    )

    try:
        reference_date = (
            parse_reference_date(
                args.reference_date
            )
            if args.reference_date
            else date.today()
        )

        if args.limit < 1:
            raise ValueError(
                "limit must be greater than zero"
            )

        if args.lease_seconds < 10:
            raise ValueError(
                "lease-seconds must be at least 10"
            )

        if args.retry_delay_seconds < 0:
            raise ValueError(
                "retry-delay-seconds cannot be negative"
            )

        client = (
            build_supabase_client_from_env()
        )

        processor = build_processor(
            client=client,
            reference_date=reference_date,
        )

        result = processor.process_batch(
            worker_id=args.worker_id,
            limit=args.limit,
            lease_seconds=args.lease_seconds,
            retry_delay_seconds=(
                args.retry_delay_seconds
            ),
        )

        print("NEXUS incremental worker")
        print(
            f"Worker:         {args.worker_id}"
        )
        print(
            "Reference date: "
            f"{reference_date.isoformat()}"
        )
        print(
            f"Claimed:        {result.claimed}"
        )
        print(
            f"Completed:      {result.completed}"
        )
        print(
            f"Retried:        {result.retried}"
        )
        print(
            f"Failed:         {result.failed}"
        )

        return 0

    except Exception as exc:
        print(
            "NEXUS incremental worker failed: "
            f"{type(exc).__name__}: {exc}"
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
