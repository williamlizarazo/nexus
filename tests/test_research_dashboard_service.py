from datetime import datetime, timezone
from types import SimpleNamespace

from services.research_dashboard_service import (
    AnalysisContext,
    ResearchDashboardService,
)


NOW = datetime(
    2026,
    9,
    7,
    12,
    0,
    tzinfo=timezone.utc,
)


class FakeUsers:

    def list_users(self):
        return [
            SimpleNamespace(
                user_id="user-a",
                email="a@example.org",
                full_name="Usuario A",
            ),
            SimpleNamespace(
                user_id="user-b",
                email="b@example.org",
                full_name="Usuario B",
            ),
        ]


class FakeProjects:

    PROJECTS = [
        SimpleNamespace(
            project_id="project-a",
            owner_user_id="user-a",
            name="Proyecto A",
        ),
        SimpleNamespace(
            project_id="project-b",
            owner_user_id="user-b",
            name="Proyecto B",
        ),
    ]

    def list_projects(
        self,
        owner_user_id=None,
        limit=500,
    ):
        if owner_user_id is None:
            return self.PROJECTS

        return [
            project
            for project in self.PROJECTS
            if project.owner_user_id
            == owner_user_id
        ]


class FakeActivitySource:

    def list_searches(
        self,
        project_id=None,
        trace_id=None,
        limit=500,
    ):
        values = {
            "project-a": [
                SimpleNamespace(
                    search_id="search-a",
                    project_id="project-a",
                    created_by="user-a",
                    trace_id="trace-a",
                    search_type="semantic",
                    original_query=(
                        "Pregunta diferente A"
                    ),
                    created_at=NOW,
                )
            ],
            "project-b": [
                SimpleNamespace(
                    search_id="search-b",
                    project_id="project-b",
                    created_by="user-b",
                    trace_id="trace-b",
                    search_type="bm25",
                    original_query=(
                        "Pregunta diferente B"
                    ),
                    created_at=NOW,
                )
            ],
        }

        return values.get(project_id, [])

    def list_annotations(
        self,
        project_id=None,
        trace_id=None,
        limit=500,
    ):
        return []

    def list_activities(
        self,
        project_id=None,
        trace_id=None,
        limit=500,
    ):
        return []

    def list_search_results(
        self,
        project_id=None,
        trace_id=None,
        limit=1000,
    ):
        values = {
            "project-a": [
                SimpleNamespace(
                    trace_id="trace-a",
                    doc_id="doc-shared",
                    chunk_id="chunk-a",
                    page_num_start=None,
                    page_idx_start=None,
                )
            ],
            "project-b": [
                SimpleNamespace(
                    trace_id="trace-b",
                    doc_id="doc-shared",
                    chunk_id="chunk-b",
                    page_num_start=None,
                    page_idx_start=None,
                )
            ],
        }

        return values.get(project_id, [])

    def list_chunks(
        self,
        project_id=None,
        doc_id=None,
        limit=5000,
    ):
        values = {
            "project-a": [
                SimpleNamespace(
                    chunk_id="chunk-a",
                    doc_id="doc-shared",
                    page_num_start=218,
                    page_idx_start=217,
                )
            ],
            "project-b": [
                SimpleNamespace(
                    chunk_id="chunk-b",
                    doc_id="doc-shared",
                    page_num_start=218,
                    page_idx_start=217,
                )
            ],
        }

        return values.get(project_id, [])

    def list_documents(
        self,
        project_id=None,
        limit=1000,
    ):
        return [
            SimpleNamespace(
                doc_id="doc-shared",
                display_name="Documento compartido",
            )
        ]


def test_dashboard_reconstructs_shared_evidence_paths():

    dependencies = SimpleNamespace(
        organization_directory_repository=(
            FakeUsers()
        ),
        research_project_source=FakeProjects(),
        research_activity_source=(
            FakeActivitySource()
        ),
    )

    service = ResearchDashboardService(
        dependencies
    )

    snapshot = service.build_snapshot(
        AnalysisContext()
    )

    assert snapshot.kpis.users == 2
    assert snapshot.kpis.projects == 2
    assert snapshot.kpis.questions == 2

    assert len(
        snapshot.evidence_paths
    ) == 2

    first, second = snapshot.evidence_paths

    assert (
        first.document_id
        == second.document_id
        == "doc-shared"
    )

    assert (
        first.page_num
        == second.page_num
        == 218
    )

    assert {
        first.user_id,
        second.user_id,
    } == {
        "user-a",
        "user-b",
    }
