import pytest

from memory_core.domain.research_project import ResearchProject


def test_research_project_normalizes_project_data():
    project = ResearchProject(
        project_id=" project-1 ",
        owner_user_id=" user-1 ",
        name=" Proyecto uno ",
        description=" Descripción ",
        tags=(" justicia ", "", " memoria "),
        status=" ACTIVE ",
    )

    assert project.project_id == "project-1"
    assert project.owner_user_id == "user-1"
    assert project.name == "Proyecto uno"
    assert project.description == "Descripción"
    assert project.tags == ("justicia", "memoria")
    assert project.status == "active"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("project_id", ""),
        ("owner_user_id", ""),
        ("name", ""),
    ],
)
def test_research_project_requires_identity_and_name(field, value):
    values = {
        "project_id": "project-1",
        "owner_user_id": "user-1",
        "name": "Proyecto uno",
    }
    values[field] = value

    with pytest.raises(ValueError):
        ResearchProject(**values)
