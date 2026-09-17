from datetime import datetime, timezone
from types import SimpleNamespace

from core.dependencies import AppDependencies
from services.research_activity_service import (
    ResearchActivityService,
)


class FakeActivitySource:
    def list_searches(self, project_id=None, trace_id=None, limit=500):
        return [
            SimpleNamespace(
                search_id="search-1",
                search_type="semantic",
                original_query="¿Qué relación tuvieron las FARC con el EPL?",
                created_at=datetime(
                    2026, 9, 17, 10, 0,
                    tzinfo=timezone.utc,
                ),
            )
        ]

    def list_annotations(self, project_id=None, trace_id=None, limit=500):
        return [
            SimpleNamespace(
                annotation_id="annotation-1",
                annotation_type="finding",
                body="Hallazgo relevante",
                selected_text=None,
                document_id="doc-1",
                page_num=12,
                created_at=datetime(
                    2026, 9, 17, 10, 5,
                    tzinfo=timezone.utc,
                ),
            )
        ]

    def list_activities(self, project_id=None, trace_id=None, limit=500):
        return [
            SimpleNamespace(
                activity_id="activity-1",
                activity_type="document_opened",
                description="Documento consultado",
                document_id="doc-1",
                page_num=12,
                created_at=datetime(
                    2026, 9, 17, 10, 10,
                    tzinfo=timezone.utc,
                ),
            )
        ]


def test_list_events_normalizes_project_activity():
    dependencies = AppDependencies(
        research_activity_source=FakeActivitySource(),
    )

    service = ResearchActivityService(
        dependencies
    )

    events = service.list_events(
        user_id="user-1",
        project_id="project-1",
    )

    assert len(events) == 3

    assert [event.event_type for event in events] == [
        "search",
        "annotation",
        "activity",
    ]

    assert events[0].subtype == "semantic"
    assert events[0].content == (
        "¿Qué relación tuvieron las FARC con el EPL?"
    )

    assert events[1].document_id == "doc-1"
    assert events[1].page_num == 12
    assert events[1].content == "Hallazgo relevante"

    assert events[2].source_id == "activity-1"
