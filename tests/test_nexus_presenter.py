from datetime import date

from core.dependencies import AppDependencies
from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
    NexusSourceAnnotatedPage,
    NexusSourceProject,
    NexusSourceProjectMembership,
    NexusSourceUser,
)
from presenters.nexus_presenter import (
    NexusPresenter,
)
from services.nexus_service import (
    NexusService,
)


REFERENCE_DATE = date(2026, 10, 1)


class FakeNexusSource:
    def load_snapshot(self):
        return NexusBackfillSnapshot(
            users=(
                NexusSourceUser(
                    user_id="user-1",
                    email="uno@example.org",
                    full_name="Usuario Uno",
                    functional_role="Investigador",
                    status="active",
                ),
                NexusSourceUser(
                    user_id="user-2",
                    email="dos@example.org",
                    full_name="Usuario Dos",
                    functional_role="Analista",
                    status="active",
                ),
            ),
            units=(),
            user_unit_memberships=(),
            projects=(
                NexusSourceProject(
                    project_id="project-1",
                    owner_user_id="user-1",
                    name="Proyecto 1",
                    description=None,
                    status="active",
                    deleted_at=None,
                ),
                NexusSourceProject(
                    project_id="project-2",
                    owner_user_id="user-2",
                    name="Proyecto 2",
                    description=None,
                    status="active",
                    deleted_at=None,
                ),
            ),
            project_memberships=(
                NexusSourceProjectMembership(
                    project_id="project-1",
                    user_id="user-1",
                    role="owner",
                ),
                NexusSourceProjectMembership(
                    project_id="project-2",
                    user_id="user-2",
                    role="owner",
                ),
            ),
            annotated_pages=(
                NexusSourceAnnotatedPage(
                    project_id="project-1",
                    doc_id="doc-A",
                    document_label="Documento A",
                    page_idx=3,
                    page_num=4,
                    annotation_count=1,
                ),
                NexusSourceAnnotatedPage(
                    project_id="project-2",
                    doc_id="doc-A",
                    document_label="Documento A",
                    page_idx=3,
                    page_num=4,
                    annotation_count=1,
                ),
            ),
        )


def _analysis():
    service = NexusService(
        AppDependencies(
            nexus_backfill_source=FakeNexusSource()
        )
    )

    return service.build_analysis(
        reference_date=REFERENCE_DATE,
    )


def test_presenter_builds_kpis():
    result = _analysis()

    presenter = NexusPresenter(
        result
    )

    kpis = presenter.kpis()

    assert kpis["structural_nodes"] == 6
    assert kpis["structural_edges"] == 5
    assert kpis["users"] == 2
    assert kpis["projects"] == 2


def test_presenter_builds_user_graph_payload():
    presenter = NexusPresenter(
        _analysis()
    )

    payload = presenter.graph_payload(
        "users"
    )

    assert len(payload["nodes"]) == 2
    assert len(payload["edges"]) == 1

    edge = payload["edges"][0]

    assert edge["shared_document_count"] == 1
    assert edge["shared_page_count"] == 1


def test_presenter_builds_project_graph_payload():
    presenter = NexusPresenter(
        _analysis()
    )

    payload = presenter.graph_payload(
        "projects"
    )

    assert len(payload["nodes"]) == 2
    assert len(payload["edges"]) == 1


def test_presenter_builds_centrality_rows():
    presenter = NexusPresenter(
        _analysis()
    )

    rows = presenter.centrality_rows(
        "users"
    )

    assert len(rows) == 2

    assert {
        "node",
        "label",
        "degree_centrality",
        "betweenness_centrality",
    } <= set(rows[0])


def test_presenter_rejects_unknown_graph():
    presenter = NexusPresenter(
        _analysis()
    )

    try:
        presenter.graph_payload(
            "unknown"
        )
    except ValueError as exc:
        assert "unknown graph" in str(exc).lower()
    else:
        raise AssertionError(
            "ValueError was expected"
        )

def test_presenter_builds_network_kpis():
    presenter = NexusPresenter(
        _analysis()
    )

    kpis = presenter.network_kpis(
        "users"
    )

    assert kpis["nodes"] == 2
    assert kpis["edges"] == 1
    assert kpis["components"] == 1
    assert kpis["isolates"] == 0
