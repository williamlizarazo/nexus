from __future__ import annotations

import argparse
import os
from collections import Counter
from dataclasses import dataclass
from datetime import date

from supabase import Client, create_client

from memory_core.adapters.supabase.nexus_backfill_source import (
    SupabaseNexusBackfillSource,
)
from memory_core.adapters.supabase.nexus_graph_projection import (
    SupabaseGraphProjectionRepository,
)
from memory_core.contracts.nexus_backfill_source import (
    NexusBackfillSource,
)
from memory_core.contracts.nexus_graph_projection import (
    GraphProjectionRepository,
)
from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
)
from memory_core.services.nexus_backfill_service import (
    NexusBackfillService,
)
from memory_core.services.nexus_projector import (
    NexusProjector,
)


ADMIN_KEY_ENV_NAMES = (
    "NEXUS_SUPABASE_ADMIN_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "SUPABASE_SECRET_KEY",
    "SUPABASE_KEY",
)


@dataclass(frozen=True, slots=True)
class BackfillReport:
    reference_date: date
    written: bool

    source_users: int
    source_units: int
    source_user_unit_memberships: int
    source_projects: int
    source_project_memberships: int
    source_annotated_pages: int

    projected_nodes: int
    projected_edges: int

    node_types: tuple[
        tuple[str, int],
        ...,
    ]

    relation_types: tuple[
        tuple[str, int],
        ...,
    ]

    persisted_nodes: int | None = None
    persisted_edges: int | None = None


class _StaticBackfillSource:
    """
    Fuente interna que evita volver a consultar Supabase durante
    la escritura después de construir el preview.
    """

    def __init__(
        self,
        snapshot: NexusBackfillSnapshot,
    ) -> None:
        self._snapshot = snapshot

    def load_snapshot(
        self,
    ) -> NexusBackfillSnapshot:
        return self._snapshot


def parse_reference_date(
    value: str,
) -> date:
    try:
        return date.fromisoformat(
            value
        )
    except ValueError as exc:
        raise ValueError(
            "Invalid reference date. "
            "Expected YYYY-MM-DD."
        ) from exc


def _counter_items(
    values,
) -> tuple[
    tuple[str, int],
    ...,
]:
    return tuple(
        sorted(
            Counter(values).items()
        )
    )


def execute_backfill(
    *,
    source: NexusBackfillSource,
    projector: NexusProjector,
    repository: (
        GraphProjectionRepository
        | None
    ),
    reference_date: date,
    write: bool,
) -> BackfillReport:

    if write and repository is None:
        raise ValueError(
            "repository is required "
            "when write=True"
        )

    snapshot = (
        source.load_snapshot()
    )

    graph = projector.project(
        snapshot
    )

    persisted_nodes = None
    persisted_edges = None

    if write:
        assert repository is not None

        service = NexusBackfillService(
            source=_StaticBackfillSource(
                snapshot
            ),
            projector=projector,
            repository=repository,
        )

        persisted_graph = (
            service.run()
        )

        if persisted_graph != graph:
            raise RuntimeError(
                "NEXUS projection changed "
                "between preview and write."
            )

        persisted_nodes = len(
            repository.list_nodes(
                active_only=False
            )
        )

        persisted_edges = len(
            repository.list_edges(
                active_only=False
            )
        )

    return BackfillReport(
        reference_date=reference_date,
        written=write,
        source_users=len(
            snapshot.users
        ),
        source_units=len(
            snapshot.units
        ),
        source_user_unit_memberships=len(
            snapshot.user_unit_memberships
        ),
        source_projects=len(
            snapshot.projects
        ),
        source_project_memberships=len(
            snapshot.project_memberships
        ),
        source_annotated_pages=len(
            snapshot.annotated_pages
        ),
        projected_nodes=len(
            graph.nodes
        ),
        projected_edges=len(
            graph.edges
        ),
        node_types=_counter_items(
            node.node_type
            for node in graph.nodes
        ),
        relation_types=_counter_items(
            edge.relation_type
            for edge in graph.edges
        ),
        persisted_nodes=(
            persisted_nodes
        ),
        persisted_edges=(
            persisted_edges
        ),
    )


def _read_admin_key() -> str:
    for variable_name in (
        ADMIN_KEY_ENV_NAMES
    ):
        value = (
            os.getenv(
                variable_name,
                ""
            )
            .strip()
        )

        if not value:
            continue

        if value.startswith(
            "sb_publishable_"
        ):
            raise RuntimeError(
                f"{variable_name} contains a "
                "publishable Supabase key, but "
                "the NEXUS backfill requires a "
                "privileged backend key."
            )

        return value

    raise RuntimeError(
        "Missing privileged Supabase key. "
        "Set NEXUS_SUPABASE_ADMIN_KEY, "
        "SUPABASE_SERVICE_ROLE_KEY, "
        "SUPABASE_SECRET_KEY, or "
        "SUPABASE_KEY."
    )


def build_supabase_client_from_env(
) -> Client:

    url = (
        os.getenv(
            "SUPABASE_URL",
            ""
        )
        .strip()
    )

    if not url:
        raise RuntimeError(
            "Missing SUPABASE_URL."
        )

    key = _read_admin_key()

    return create_client(
        url,
        key,
    )


def _print_report(
    report: BackfillReport,
) -> None:

    mode = (
        "WRITE"
        if report.written
        else "DRY-RUN"
    )

    print(
        "NEXUS historical backfill"
    )
    print(
        f"Mode: {mode}"
    )
    print(
        "Reference date: "
        f"{report.reference_date.isoformat()}"
    )

    print()
    print("Source snapshot")
    print(
        f"  Users:                    "
        f"{report.source_users}"
    )
    print(
        f"  Units:                    "
        f"{report.source_units}"
    )
    print(
        f"  User-unit memberships:    "
        f"{report.source_user_unit_memberships}"
    )
    print(
        f"  Projects:                 "
        f"{report.source_projects}"
    )
    print(
        f"  Project memberships:      "
        f"{report.source_project_memberships}"
    )
    print(
        f"  Annotated pages:          "
        f"{report.source_annotated_pages}"
    )

    print()
    print("Projection")
    print(
        f"  Nodes:                    "
        f"{report.projected_nodes}"
    )

    for (
        node_type,
        count,
    ) in report.node_types:
        print(
            f"    {node_type}: {count}"
        )

    print(
        f"  Edges:                    "
        f"{report.projected_edges}"
    )

    for (
        relation_type,
        count,
    ) in report.relation_types:
        print(
            f"    {relation_type}: {count}"
        )

    if report.written:
        print()
        print("Persisted projection")
        print(
            f"  nexus_nodes:              "
            f"{report.persisted_nodes}"
        )
        print(
            f"  nexus_edges:              "
            f"{report.persisted_edges}"
        )


def _build_parser(
) -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Build the historical "
            "NEXUS graph projection."
        )
    )

    parser.add_argument(
        "--reference-date",
        required=True,
        help=(
            "Organizational reference "
            "date in YYYY-MM-DD format."
        ),
    )

    parser.add_argument(
        "--write",
        action="store_true",
        help=(
            "Persist the projection. "
            "Without this flag the command "
            "runs in dry-run mode."
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
        )

        client = (
            build_supabase_client_from_env()
        )

        source = (
            SupabaseNexusBackfillSource(
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

        report = execute_backfill(
            source=source,
            projector=projector,
            repository=repository,
            reference_date=reference_date,
            write=bool(
                args.write
            ),
        )

        _print_report(
            report
        )

        return 0

    except Exception as exc:
        print(
            "NEXUS backfill failed: "
            f"{exc}"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
