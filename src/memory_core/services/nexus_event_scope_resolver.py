from __future__ import annotations

from typing import Any

from memory_core.domain.nexus_incremental import NexusAffectedScope
from memory_core.domain.nexus_projection_event import NexusProjectionEvent


class NexusEventScopeResolver:
    """
    Traduce un evento durable de la cola NEXUS al alcance
    que debe reconciliarse.

    Para cambios de identidad considera tanto old_values
    como new_values, evitando dejar topología obsoleta.
    """

    _PROJECT_EVENTS = {
        "PROJECT_CHANGED",
        "PROJECT_MEMBERSHIP_CHANGED",
        "ANNOTATION_CHANGED",
        "DOCUMENT_CHANGED",
        "PAGE_CHANGED",
    }

    _USER_EVENTS = {
        "USER_CHANGED",
        "PROJECT_MEMBERSHIP_CHANGED",
        "USER_UNIT_MEMBERSHIP_CHANGED",
    }

    _UNIT_EVENTS = {
        "ORGANIZATIONAL_UNIT_CHANGED",
        "USER_UNIT_MEMBERSHIP_CHANGED",
    }

    _SUPPORTED_EVENTS = (
        _PROJECT_EVENTS
        | _USER_EVENTS
        | _UNIT_EVENTS
    )

    @classmethod
    def resolve(
        cls,
        event: NexusProjectionEvent,
    ) -> NexusAffectedScope:

        if event.event_type not in cls._SUPPORTED_EVENTS:
            raise ValueError(
                "Unsupported NEXUS projection event type: "
                f"{event.event_type}"
            )

        project_ids: set[str] = set()
        user_ids: set[str] = set()
        unit_ids: set[str] = set()

        if event.event_type in cls._PROJECT_EVENTS:
            cls._add(
                project_ids,
                event.project_id,
            )

            cls._add_payload_value(
                project_ids,
                event.old_values,
                "project_id",
            )

            cls._add_payload_value(
                project_ids,
                event.new_values,
                "project_id",
            )

            # PROJECT_CHANGED stores the project PK as "id".
            if event.event_type == "PROJECT_CHANGED":
                cls._add_payload_value(
                    project_ids,
                    event.old_values,
                    "id",
                )

                cls._add_payload_value(
                    project_ids,
                    event.new_values,
                    "id",
                )

        if event.event_type in cls._USER_EVENTS:
            cls._add(
                user_ids,
                event.user_id,
            )

            cls._add_payload_value(
                user_ids,
                event.old_values,
                "user_id",
            )

            cls._add_payload_value(
                user_ids,
                event.new_values,
                "user_id",
            )

        if event.event_type in cls._UNIT_EVENTS:
            cls._add(
                unit_ids,
                event.unit_id,
            )

            cls._add_payload_value(
                unit_ids,
                event.old_values,
                "unit_id",
            )

            cls._add_payload_value(
                unit_ids,
                event.new_values,
                "unit_id",
            )

        return NexusAffectedScope(
            project_ids=tuple(project_ids),
            user_ids=tuple(user_ids),
            unit_ids=tuple(unit_ids),
        )

    @staticmethod
    def _add(
        target: set[str],
        value: Any,
    ) -> None:

        if value is None:
            return

        normalized = str(value).strip()

        if normalized:
            target.add(normalized)

    @classmethod
    def _add_payload_value(
        cls,
        target: set[str],
        payload: dict[str, Any] | None,
        field_name: str,
    ) -> None:

        if not payload:
            return

        cls._add(
            target,
            payload.get(field_name),
        )
