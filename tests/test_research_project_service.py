from types import SimpleNamespace

from memory_core.domain.research_project import ResearchProject

from core.dependencies import AppDependencies
from services.research_project_service import ResearchProjectService


class FakeResearchProjectSource:
    def __init__(self):
        self.calls = []

    def list_projects(self, *, owner_user_id, limit):
        self.calls.append((owner_user_id, limit))
        return [
            ResearchProject(
                project_id="project-1",
                owner_user_id=owner_user_id,
                name="Proyecto uno",
            )
        ]


def test_service_lists_projects_for_normalized_user():
    source = FakeResearchProjectSource()
    dependencies = AppDependencies(
        research_project_source=source,
    )
    service = ResearchProjectService(dependencies)

    projects = service.list_projects_for_user(" user-1 ", limit=25)

    assert service.available is True
    assert [project.project_id for project in projects] == ["project-1"]
    assert source.calls == [("user-1", 25)]


def test_service_returns_empty_without_source_or_user():
    unavailable_service = ResearchProjectService(AppDependencies())
    source = SimpleNamespace(
        list_projects=lambda **_kwargs: (_ for _ in ()).throw(
            AssertionError("source should not be called")
        )
    )
    blank_user_service = ResearchProjectService(
        AppDependencies(research_project_source=source)
    )

    assert unavailable_service.available is False
    assert unavailable_service.list_projects_for_user("user-1") == []
    assert blank_user_service.list_projects_for_user("  ") == []
