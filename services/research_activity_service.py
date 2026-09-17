from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from core.dependencies import AppDependencies


@dataclass(frozen=True, slots=True)
class ResearchActivityEvent:
    user_id: str
    project_id: str
    event_type: str
    subtype: str | None
    content: str
    document_id: str | None
    page_num: int | None
    occurred_at: datetime | None
    source_id: str


class ResearchActivityService:
    """Normaliza búsquedas, anotaciones y actividades de un proyecto."""

    def __init__(
        self,
        dependencies: AppDependencies,
    ) -> None:
        self._dependencies = dependencies

    @property
    def available(self) -> bool:
        return (
            self._dependencies.research_activity_source
            is not None
        )

    def list_events(
        self,
        *,
        user_id: str,
        project_id: str,
        limit_per_source: int = 5000,
    ) -> list[ResearchActivityEvent]:

        source = self._dependencies.research_activity_source

        if source is None:
            return []

        user_id = str(user_id or "").strip()
        project_id = str(project_id or "").strip()

        if not user_id or not project_id:
            return []

        events: list[ResearchActivityEvent] = []

        for search in source.list_searches(
            project_id=project_id,
            limit=limit_per_source,
        ):
            events.append(
                ResearchActivityEvent(
                    user_id=user_id,
                    project_id=project_id,
                    event_type="search",
                    subtype=self._text(
                        getattr(search, "search_type", None)
                    ),
                    content=(
                        self._text(
                            getattr(search, "original_query", None)
                        )
                        or self._text(
                            getattr(search, "query", None)
                        )
                        or ""
                    ),
                    document_id=self._document_id(search),
                    page_num=self._page_num(search),
                    occurred_at=self._occurred_at(search),
                    source_id=(
                        self._text(
                            getattr(search, "search_id", None)
                        )
                        or ""
                    ),
                )
            )

        for annotation in source.list_annotations(
            project_id=project_id,
            limit=limit_per_source,
        ):
            events.append(
                ResearchActivityEvent(
                    user_id=user_id,
                    project_id=project_id,
                    event_type="annotation",
                    subtype=self._text(
                        getattr(
                            annotation,
                            "annotation_type",
                            None,
                        )
                    ),
                    content=(
                        self._text(
                            getattr(annotation, "body", None)
                        )
                        or self._text(
                            getattr(
                                annotation,
                                "selected_text",
                                None,
                            )
                        )
                        or ""
                    ),
                    document_id=self._document_id(annotation),
                    page_num=self._page_num(annotation),
                    occurred_at=self._occurred_at(annotation),
                    source_id=(
                        self._text(
                            getattr(
                                annotation,
                                "annotation_id",
                                None,
                            )
                        )
                        or ""
                    ),
                )
            )

        for activity in source.list_activities(
            project_id=project_id,
            limit=limit_per_source,
        ):
            events.append(
                ResearchActivityEvent(
                    user_id=user_id,
                    project_id=project_id,
                    event_type="activity",
                    subtype=self._text(
                        getattr(
                            activity,
                            "activity_type",
                            None,
                        )
                    ),
                    content=(
                        self._text(
                            getattr(
                                activity,
                                "description",
                                None,
                            )
                        )
                        or self._text(
                            getattr(
                                activity,
                                "activity_type",
                                None,
                            )
                        )
                        or ""
                    ),
                    document_id=self._document_id(activity),
                    page_num=self._page_num(activity),
                    occurred_at=self._occurred_at(activity),
                    source_id=(
                        self._text(
                            getattr(
                                activity,
                                "activity_id",
                                None,
                            )
                        )
                        or self._text(
                            getattr(activity, "id", None)
                        )
                        or ""
                    ),
                )
            )

        events.sort(
            key=lambda event: (
                event.occurred_at is None,
                (
                    event.occurred_at.isoformat()
                    if event.occurred_at
                    else ""
                ),
            )
        )

        return events

    @staticmethod
    def _text(value: Any) -> str | None:
        if value is None:
            return None

        value = str(value).strip()
        return value or None

    def _document_id(
        self,
        source: Any,
    ) -> str | None:
        return (
            self._text(
                getattr(source, "document_id", None)
            )
            or self._text(
                getattr(source, "doc_id", None)
            )
        )

    @staticmethod
    def _page_num(
        source: Any,
    ) -> int | None:

        value = getattr(
            source,
            "page_num",
            None,
        )

        if value is None:
            value = getattr(
                source,
                "page_number",
                None,
            )

        if value is None:
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _occurred_at(
        source: Any,
    ) -> datetime | None:

        for field in (
            "occurred_at",
            "created_at",
            "started_at",
            "updated_at",
        ):
            value = getattr(
                source,
                field,
                None,
            )

            if isinstance(value, datetime):
                return value

            if isinstance(value, str):
                text = value.strip()

                if not text:
                    continue

                if text.endswith("Z"):
                    text = text[:-1] + "+00:00"

                try:
                    return datetime.fromisoformat(text)
                except ValueError:
                    continue

        return None


__all__ = [
    "ResearchActivityEvent",
    "ResearchActivityService",
]
