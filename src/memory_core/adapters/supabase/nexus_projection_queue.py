from __future__ import annotations

from datetime import datetime
from typing import Any

from supabase import Client

from memory_core.domain.nexus_projection_event import (
    NexusProjectionEvent,
)


class SupabaseNexusProjectionQueueRepository:
    """
    Adaptador Supabase para la cola incremental NEXUS.

    La lógica de concurrencia, leases y reintentos permanece
    en PostgreSQL. Este adaptador únicamente invoca los RPC
    y transforma las filas en objetos de dominio.
    """

    def __init__(
        self,
        client: Client,
    ) -> None:
        self._client = client

    # ============================================================
    # CLAIM
    # ============================================================

    def claim(
        self,
        *,
        worker_id: str,
        limit: int = 50,
        lease_seconds: int = 120,
    ) -> list[NexusProjectionEvent]:

        response = (
            self._client
            .rpc(
                "nexus_claim_projection_events",
                {
                    "p_worker_id": worker_id,
                    "p_limit": limit,
                    "p_lease_seconds": lease_seconds,
                },
            )
            .execute()
        )

        rows = list(
            response.data or []
        )

        return [
            self._event_from_row(row)
            for row in rows
        ]

    # ============================================================
    # COMPLETE
    # ============================================================

    def complete(
        self,
        *,
        event_id: str,
        worker_id: str,
    ) -> NexusProjectionEvent:

        response = (
            self._client
            .rpc(
                "nexus_complete_projection_event",
                {
                    "p_event_id": event_id,
                    "p_worker_id": worker_id,
                },
            )
            .execute()
        )

        return self._event_from_row(
            self._single_row(
                response.data
            )
        )

    # ============================================================
    # RETRY
    # ============================================================

    def retry(
        self,
        *,
        event_id: str,
        worker_id: str,
        error: str,
        delay_seconds: int = 30,
    ) -> NexusProjectionEvent:

        response = (
            self._client
            .rpc(
                "nexus_retry_projection_event",
                {
                    "p_event_id": event_id,
                    "p_worker_id": worker_id,
                    "p_error": error,
                    "p_delay_seconds": delay_seconds,
                },
            )
            .execute()
        )

        return self._event_from_row(
            self._single_row(
                response.data
            )
        )

    # ============================================================
    # FAIL
    # ============================================================

    def fail(
        self,
        *,
        event_id: str,
        worker_id: str,
        error: str,
    ) -> NexusProjectionEvent:

        response = (
            self._client
            .rpc(
                "nexus_fail_projection_event",
                {
                    "p_event_id": event_id,
                    "p_worker_id": worker_id,
                    "p_error": error,
                },
            )
            .execute()
        )

        return self._event_from_row(
            self._single_row(
                response.data
            )
        )

    # ============================================================
    # ROW MAPPING
    # ============================================================

    @staticmethod
    def _event_from_row(
        row: dict[str, Any],
    ) -> NexusProjectionEvent:

        return NexusProjectionEvent(
            event_id=str(
                row["event_id"]
            ),
            event_type=str(
                row["event_type"]
            ),
            source_table=str(
                row["source_table"]
            ),
            source_operation=str(
                row["source_operation"]
            ),
            source_record_key=str(
                row["source_record_key"]
            ),
            project_id=(
                str(row["project_id"])
                if row.get("project_id") is not None
                else None
            ),
            user_id=(
                str(row["user_id"])
                if row.get("user_id") is not None
                else None
            ),
            unit_id=(
                str(row["unit_id"])
                if row.get("unit_id") is not None
                else None
            ),
            doc_id=(
                str(row["doc_id"])
                if row.get("doc_id") is not None
                else None
            ),
            page_idx=(
                int(row["page_idx"])
                if row.get("page_idx") is not None
                else None
            ),
            old_values=(
                dict(row["old_values"])
                if row.get("old_values") is not None
                else None
            ),
            new_values=(
                dict(row["new_values"])
                if row.get("new_values") is not None
                else None
            ),
            status=str(
                row["status"]
            ),
            priority=int(
                row["priority"]
            ),
            attempts=int(
                row["attempts"]
            ),
            max_attempts=int(
                row["max_attempts"]
            ),
            available_at=(
                SupabaseNexusProjectionQueueRepository
                ._parse_datetime(
                    row["available_at"]
                )
            ),
            claimed_by=(
                str(row["claimed_by"])
                if row.get("claimed_by") is not None
                else None
            ),
            claimed_at=(
                SupabaseNexusProjectionQueueRepository
                ._parse_optional_datetime(
                    row.get("claimed_at")
                )
            ),
            lease_until=(
                SupabaseNexusProjectionQueueRepository
                ._parse_optional_datetime(
                    row.get("lease_until")
                )
            ),
            processed_at=(
                SupabaseNexusProjectionQueueRepository
                ._parse_optional_datetime(
                    row.get("processed_at")
                )
            ),
            last_error=(
                str(row["last_error"])
                if row.get("last_error") is not None
                else None
            ),
            created_at=(
                SupabaseNexusProjectionQueueRepository
                ._parse_datetime(
                    row["created_at"]
                )
            ),
            updated_at=(
                SupabaseNexusProjectionQueueRepository
                ._parse_datetime(
                    row["updated_at"]
                )
            ),
        )

    @staticmethod
    def _single_row(
        data: Any,
    ) -> dict[str, Any]:

        if isinstance(data, dict):
            return data

        if isinstance(data, list):
            if len(data) != 1:
                raise RuntimeError(
                    "Expected exactly one queue event row"
                )

            return data[0]

        raise RuntimeError(
            "Supabase RPC returned an unexpected response"
        )

    @staticmethod
    def _parse_datetime(
        value: Any,
    ) -> datetime:

        if isinstance(value, datetime):
            return value

        if not isinstance(value, str):
            raise TypeError(
                "Expected datetime or ISO-8601 string"
            )

        return datetime.fromisoformat(
            value.replace(
                "Z",
                "+00:00",
            )
        )

    @staticmethod
    def _parse_optional_datetime(
        value: Any,
    ) -> datetime | None:

        if value is None:
            return None

        return (
            SupabaseNexusProjectionQueueRepository
            ._parse_datetime(value)
        )
