from __future__ import annotations

from collections import defaultdict
from typing import Any

from services.research_dashboard_service import (
    DashboardSnapshot,
)


def _datetime_text(value) -> str:
    if value is None:
        return ""

    return value.strftime("%Y-%m-%d %H:%M")


def _page_text(
    page_num: int | None,
    page_idx: int | None,
) -> str:
    if page_num is not None:
        return str(page_num)

    if page_idx is not None:
        return f"idx {page_idx}"

    return ""


class ResearchDashboardPresenter:

    @staticmethod
    def questions(
        snapshot: DashboardSnapshot,
    ) -> list[dict[str, Any]]:
        return [
            {
                "Usuario": row.user_label,
                "Proyecto": row.project_name,
                "Fecha": _datetime_text(row.occurred_at),
                "Tipo": row.search_type,
                "Pregunta / búsqueda": row.query,
            }
            for row in snapshot.questions
        ]

    @staticmethod
    def annotations(
        snapshot: DashboardSnapshot,
    ) -> list[dict[str, Any]]:
        return [
            {
                "Usuario": row.user_label,
                "Proyecto": row.project_name,
                "Fecha": _datetime_text(row.occurred_at),
                "Tipo": row.annotation_type,
                "Contenido": row.content,
                "Documento": row.document_id or "",
                "Página": _page_text(row.page_num, row.page_idx),
            }
            for row in snapshot.annotations
        ]

    @staticmethod
    def evidence_paths(
        snapshot: DashboardSnapshot,
    ) -> list[dict[str, Any]]:
        return [
            {
                "Usuario": row.user_label,
                "Proyecto": row.project_name,
                "Pregunta": row.query,
                "Documento": row.document_name,
                "Página": _page_text(row.page_num, row.page_idx),
                "Fuente página": row.page_source or "",
                "Fecha": _datetime_text(row.occurred_at),
            }
            for row in snapshot.evidence_paths
        ]

    @staticmethod
    def timeline(
        snapshot: DashboardSnapshot,
    ) -> list[dict[str, Any]]:
        return [
            {
                "Fecha": point.day.isoformat(),
                "Búsquedas": point.searches,
                "Anotaciones": point.annotations,
                "Actividades": point.activities,
                "Total": (
                    point.searches
                    + point.annotations
                    + point.activities
                ),
            }
            for point in snapshot.timeline
        ]

    @staticmethod
    def users_comparison(
        snapshot: DashboardSnapshot,
    ) -> list[dict[str, Any]]:
        values = defaultdict(
            lambda: {
                "projects": set(),
                "questions": 0,
                "annotations": 0,
                "activities": 0,
                "label": "",
            }
        )

        for row in snapshot.questions:
            item = values[row.user_id]
            item["label"] = row.user_label
            item["projects"].add(row.project_id)
            item["questions"] += 1

        for row in snapshot.annotations:
            item = values[row.user_id]
            item["label"] = row.user_label
            item["projects"].add(row.project_id)
            item["annotations"] += 1

        for row in snapshot.activities:
            item = values[row.user_id]
            item["label"] = row.user_label
            item["projects"].add(row.project_id)
            item["activities"] += 1

        return [
            {
                "Usuario": value["label"],
                "Proyectos": len(value["projects"]),
                "Preguntas": value["questions"],
                "Anotaciones": value["annotations"],
                "Actividades": value["activities"],
            }
            for value in values.values()
        ]

    @staticmethod
    def projects_comparison(
        snapshot: DashboardSnapshot,
    ) -> list[dict[str, Any]]:
        values = defaultdict(
            lambda: {
                "name": "",
                "questions": 0,
                "annotations": 0,
                "activities": 0,
            }
        )

        for row in snapshot.questions:
            item = values[row.project_id]
            item["name"] = row.project_name
            item["questions"] += 1

        for row in snapshot.annotations:
            item = values[row.project_id]
            item["name"] = row.project_name
            item["annotations"] += 1

        for row in snapshot.activities:
            item = values[row.project_id]
            item["name"] = row.project_name
            item["activities"] += 1

        return [
            {
                "Proyecto": value["name"],
                "Preguntas": value["questions"],
                "Anotaciones": value["annotations"],
                "Actividades": value["activities"],
            }
            for value in values.values()
        ]
