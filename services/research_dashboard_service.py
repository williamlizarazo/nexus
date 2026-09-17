from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from core.dependencies import AppDependencies


@dataclass(frozen=True, slots=True)
class AnalysisContext:
    user_ids: tuple[str, ...] = ()
    project_ids: tuple[str, ...] = ()
    date_from: date | None = None
    date_to: date | None = None
    event_types: tuple[str, ...] = (
        "search",
        "annotation",
        "activity",
    )


@dataclass(frozen=True, slots=True)
class DashboardUser:
    user_id: str
    label: str
    email: str


@dataclass(frozen=True, slots=True)
class DashboardProject:
    project_id: str
    owner_user_id: str
    name: str


@dataclass(frozen=True, slots=True)
class QuestionRow:
    user_id: str
    user_label: str
    project_id: str
    project_name: str
    search_id: str
    trace_id: str | None
    search_type: str
    query: str
    occurred_at: datetime | None


@dataclass(frozen=True, slots=True)
class AnnotationRow:
    user_id: str
    user_label: str
    project_id: str
    project_name: str
    annotation_id: str
    annotation_type: str
    content: str
    document_id: str | None
    page_num: int | None
    page_idx: int | None
    occurred_at: datetime | None


@dataclass(frozen=True, slots=True)
class ActivityRow:
    user_id: str
    user_label: str
    project_id: str
    project_name: str
    activity_id: str
    activity_type: str
    description: str
    occurred_at: datetime | None


@dataclass(frozen=True, slots=True)
class EvidencePath:
    user_id: str
    user_label: str
    project_id: str
    project_name: str
    search_id: str
    trace_id: str
    query: str
    document_id: str
    document_name: str
    page_num: int | None
    page_idx: int | None
    page_source: str | None
    occurred_at: datetime | None


@dataclass(frozen=True, slots=True)
class TimelinePoint:
    day: date
    searches: int
    annotations: int
    activities: int


@dataclass(frozen=True, slots=True)
class DashboardKpis:
    users: int
    projects: int
    questions: int
    annotations: int
    activities: int
    events: int


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    kpis: DashboardKpis
    questions: tuple[QuestionRow, ...]
    annotations: tuple[AnnotationRow, ...]
    activities: tuple[ActivityRow, ...]
    evidence_paths: tuple[EvidencePath, ...]
    timeline: tuple[TimelinePoint, ...]


def _first_not_none(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _inside_period(
    value: datetime | None,
    context: AnalysisContext,
) -> bool:
    if value is None:
        return True

    event_date = value.date()

    if context.date_from is not None and event_date < context.date_from:
        return False

    if context.date_to is not None and event_date > context.date_to:
        return False

    return True


def _event_enabled(
    event_type: str,
    context: AnalysisContext,
) -> bool:
    if not context.event_types:
        return True

    return event_type in context.event_types


def _latest_first(value: datetime | None) -> tuple[bool, str]:
    return (
        value is not None,
        value.isoformat() if value is not None else "",
    )


class ResearchDashboardService:

    def __init__(
        self,
        dependencies: AppDependencies,
    ) -> None:
        self._dependencies = dependencies

    def list_users(self) -> list[DashboardUser]:
        repository = getattr(
            self._dependencies,
            "organization_directory_repository",
            None,
        )

        if repository is None:
            return []

        result: list[DashboardUser] = []

        for user in repository.list_users():
            email = str(getattr(user, "email", "") or "")
            full_name = str(
                getattr(user, "full_name", "") or ""
            ).strip()
            label = full_name or email or str(user.user_id)

            result.append(
                DashboardUser(
                    user_id=str(user.user_id),
                    label=label,
                    email=email,
                )
            )

        return sorted(result, key=lambda item: item.label.lower())

    def list_projects(
        self,
        user_ids: tuple[str, ...] = (),
    ) -> list[DashboardProject]:
        source = getattr(
            self._dependencies,
            "research_project_source",
            None,
        )

        if source is None:
            return []

        if user_ids:
            raw_projects = []
            for user_id in user_ids:
                raw_projects.extend(
                    source.list_projects(
                        owner_user_id=user_id,
                        limit=5000,
                    )
                )
        else:
            raw_projects = source.list_projects(
                owner_user_id=None,
                limit=5000,
            )

        projects_by_id: dict[str, DashboardProject] = {}

        for project in raw_projects:
            project_id = str(project.project_id)
            projects_by_id[project_id] = DashboardProject(
                project_id=project_id,
                owner_user_id=str(project.owner_user_id),
                name=str(project.name),
            )

        return sorted(
            projects_by_id.values(),
            key=lambda item: item.name.lower(),
        )

    def build_snapshot(
        self,
        context: AnalysisContext,
    ) -> DashboardSnapshot:
        source = getattr(
            self._dependencies,
            "research_activity_source",
            None,
        )

        if source is None:
            return self._empty_snapshot()

        user_labels = {
            user.user_id: user.label
            for user in self.list_users()
        }
        projects = self.list_projects(context.user_ids)

        if context.project_ids:
            selected = set(context.project_ids)
            projects = [
                project
                for project in projects
                if project.project_id in selected
            ]

        questions: list[QuestionRow] = []
        annotations: list[AnnotationRow] = []
        activities: list[ActivityRow] = []
        evidence_paths: list[EvidencePath] = []
        timeline: dict[date, dict[str, int]] = defaultdict(
            lambda: {
                "search": 0,
                "annotation": 0,
                "activity": 0,
            }
        )
        observed_users: set[str] = set()

        for project in projects:
            project_id = project.project_id
            owner_user_id = project.owner_user_id
            searches = source.list_searches(
                project_id=project_id,
                limit=5000,
            )
            raw_annotations = source.list_annotations(
                project_id=project_id,
                limit=5000,
            )
            raw_activities = source.list_activities(
                project_id=project_id,
                limit=5000,
            )
            search_results = source.list_search_results(
                project_id=project_id,
                limit=10000,
            )
            chunks = source.list_chunks(
                project_id=project_id,
                limit=10000,
            )
            documents = source.list_documents(
                project_id=project_id,
                limit=5000,
            )

            results_by_trace: dict[str, list[Any]] = defaultdict(list)
            for result in search_results:
                if result.trace_id:
                    results_by_trace[str(result.trace_id)].append(result)

            chunks_by_id = {
                str(chunk.chunk_id): chunk
                for chunk in chunks
                if chunk.chunk_id
            }
            documents_by_id = {
                str(document.doc_id): document
                for document in documents
                if document.doc_id
            }

            if _event_enabled("search", context):
                for search in searches:
                    if not _inside_period(search.created_at, context):
                        continue

                    actor_id = str(search.created_by or owner_user_id)
                    if context.user_ids and actor_id not in context.user_ids:
                        continue

                    observed_users.add(actor_id)
                    user_label = user_labels.get(actor_id, actor_id)
                    questions.append(
                        QuestionRow(
                            user_id=actor_id,
                            user_label=user_label,
                            project_id=project_id,
                            project_name=project.name,
                            search_id=str(search.search_id),
                            trace_id=(
                                str(search.trace_id)
                                if search.trace_id
                                else None
                            ),
                            search_type=str(search.search_type),
                            query=str(search.original_query),
                            occurred_at=search.created_at,
                        )
                    )

                    if search.created_at:
                        timeline[search.created_at.date()]["search"] += 1

                    if not search.trace_id:
                        continue

                    for result in results_by_trace.get(
                        str(search.trace_id),
                        [],
                    ):
                        if not result.doc_id:
                            continue

                        chunk = (
                            chunks_by_id.get(str(result.chunk_id))
                            if result.chunk_id
                            else None
                        )
                        page_num = _first_not_none(
                            result.page_num_start,
                            getattr(chunk, "page_num_start", None),
                        )
                        page_idx = _first_not_none(
                            result.page_idx_start,
                            getattr(chunk, "page_idx_start", None),
                        )

                        if (
                            result.page_num_start is not None
                            or result.page_idx_start is not None
                        ):
                            page_source = "search_result"
                        elif chunk is not None and (
                            chunk.page_num_start is not None
                            or chunk.page_idx_start is not None
                        ):
                            page_source = "chunk"
                        else:
                            page_source = None

                        document = documents_by_id.get(str(result.doc_id))
                        display_name = (
                            getattr(document, "display_name", None)
                            if document
                            else None
                        )
                        evidence_paths.append(
                            EvidencePath(
                                user_id=actor_id,
                                user_label=user_label,
                                project_id=project_id,
                                project_name=project.name,
                                search_id=str(search.search_id),
                                trace_id=str(search.trace_id),
                                query=str(search.original_query),
                                document_id=str(result.doc_id),
                                document_name=(
                                    str(display_name)
                                    if display_name
                                    else str(result.doc_id)
                                ),
                                page_num=page_num,
                                page_idx=page_idx,
                                page_source=page_source,
                                occurred_at=search.created_at,
                            )
                        )

            if _event_enabled("annotation", context):
                for annotation in raw_annotations:
                    if not _inside_period(annotation.created_at, context):
                        continue

                    actor_id = str(annotation.created_by or owner_user_id)
                    if context.user_ids and actor_id not in context.user_ids:
                        continue

                    observed_users.add(actor_id)
                    user_label = user_labels.get(actor_id, actor_id)
                    chunk = (
                        chunks_by_id.get(str(annotation.chunk_id))
                        if annotation.chunk_id
                        else None
                    )
                    page_num = _first_not_none(
                        annotation.page_num,
                        getattr(chunk, "page_num_start", None),
                    )
                    page_idx = _first_not_none(
                        annotation.page_idx,
                        getattr(chunk, "page_idx_start", None),
                    )
                    content = annotation.body or annotation.selected_text or ""
                    annotations.append(
                        AnnotationRow(
                            user_id=actor_id,
                            user_label=user_label,
                            project_id=project_id,
                            project_name=project.name,
                            annotation_id=str(annotation.annotation_id),
                            annotation_type=str(annotation.annotation_type),
                            content=str(content),
                            document_id=(
                                str(annotation.doc_id)
                                if annotation.doc_id
                                else None
                            ),
                            page_num=page_num,
                            page_idx=page_idx,
                            occurred_at=annotation.created_at,
                        )
                    )

                    if annotation.created_at:
                        timeline[annotation.created_at.date()]["annotation"] += 1

            if _event_enabled("activity", context):
                for activity in raw_activities:
                    if not _inside_period(activity.created_at, context):
                        continue

                    actor_id = str(activity.created_by or owner_user_id)
                    if context.user_ids and actor_id not in context.user_ids:
                        continue

                    observed_users.add(actor_id)
                    user_label = user_labels.get(actor_id, actor_id)
                    activity_id = (
                        getattr(activity, "activity_id", None)
                        or getattr(activity, "id", "")
                    )
                    activities.append(
                        ActivityRow(
                            user_id=actor_id,
                            user_label=user_label,
                            project_id=project_id,
                            project_name=project.name,
                            activity_id=str(activity_id),
                            activity_type=str(activity.activity_type),
                            description=str(activity.description or ""),
                            occurred_at=activity.created_at,
                        )
                    )

                    if activity.created_at:
                        timeline[activity.created_at.date()]["activity"] += 1

        timeline_points = tuple(
            TimelinePoint(
                day=day,
                searches=values["search"],
                annotations=values["annotation"],
                activities=values["activity"],
            )
            for day, values in sorted(timeline.items())
        )
        total_events = len(questions) + len(annotations) + len(activities)

        return DashboardSnapshot(
            kpis=DashboardKpis(
                users=len(observed_users),
                projects=len(projects),
                questions=len(questions),
                annotations=len(annotations),
                activities=len(activities),
                events=total_events,
            ),
            questions=tuple(
                sorted(
                    questions,
                    key=lambda item: _latest_first(item.occurred_at),
                    reverse=True,
                )
            ),
            annotations=tuple(
                sorted(
                    annotations,
                    key=lambda item: _latest_first(item.occurred_at),
                    reverse=True,
                )
            ),
            activities=tuple(
                sorted(
                    activities,
                    key=lambda item: _latest_first(item.occurred_at),
                    reverse=True,
                )
            ),
            evidence_paths=tuple(
                sorted(
                    evidence_paths,
                    key=lambda item: _latest_first(item.occurred_at),
                    reverse=True,
                )
            ),
            timeline=timeline_points,
        )

    @staticmethod
    def _empty_snapshot() -> DashboardSnapshot:
        return DashboardSnapshot(
            kpis=DashboardKpis(
                users=0,
                projects=0,
                questions=0,
                annotations=0,
                activities=0,
                events=0,
            ),
            questions=(),
            annotations=(),
            activities=(),
            evidence_paths=(),
            timeline=(),
        )
