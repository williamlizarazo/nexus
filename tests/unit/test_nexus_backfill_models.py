from datetime import date, datetime, timezone

import pytest

from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
    NexusSourceAnnotatedPage,
    NexusSourceProject,
    NexusSourceProjectMembership,
    NexusSourceUnit,
    NexusSourceUser,
    NexusSourceUserUnitMembership,
)


def test_source_user_supports_auth_identity_without_directory_profile():
    user = NexusSourceUser(
        user_id="user-1",
        email="persona@jep.gov.co",
    )

    assert user.user_id == "user-1"
    assert user.email == "persona@jep.gov.co"
    assert user.full_name is None
    assert user.functional_role is None
    assert user.status is None


def test_source_user_supports_directory_enrichment():
    user = NexusSourceUser(
        user_id="user-1",
        email="persona@jep.gov.co",
        full_name="Persona Uno",
        functional_role="Analista",
        status="active",
    )

    assert user.full_name == "Persona Uno"
    assert user.functional_role == "Analista"
    assert user.status == "active"


def test_source_unit_preserves_organizational_data():
    unit = NexusSourceUnit(
        unit_id="unit-1",
        name="Magistratura X",
        unit_type="magistratura",
        status="active",
    )

    assert unit.unit_id == "unit-1"
    assert unit.name == "Magistratura X"
    assert unit.unit_type == "magistratura"
    assert unit.status == "active"


def test_source_user_unit_membership_preserves_validity():
    membership = NexusSourceUserUnitMembership(
        user_id="user-1",
        unit_id="unit-1",
        status="active",
        is_primary=True,
        valid_from=date(2026, 1, 1),
    )

    assert membership.user_id == "user-1"
    assert membership.unit_id == "unit-1"
    assert membership.is_primary is True
    assert membership.valid_from == date(2026, 1, 1)
    assert membership.valid_to is None


def test_source_project_preserves_owner_and_project_state():
    project = NexusSourceProject(
        project_id="project-1",
        owner_user_id="user-1",
        name="Proyecto Uno",
        description="Descripción",
        status="active",
    )

    assert project.project_id == "project-1"
    assert project.owner_user_id == "user-1"
    assert project.name == "Proyecto Uno"
    assert project.status == "active"
    assert project.deleted_at is None


def test_source_project_membership_preserves_role():
    membership = NexusSourceProjectMembership(
        project_id="project-1",
        user_id="user-1",
        role="owner",
    )

    assert membership.project_id == "project-1"
    assert membership.user_id == "user-1"
    assert membership.role == "owner"


def test_source_annotated_page_represents_effective_document_work():
    page = NexusSourceAnnotatedPage(
        project_id="project-1",
        doc_id="document-1",
        document_label="Documento Uno.pdf",
        page_idx=12,
        page_num=13,
        annotation_count=2,
    )

    assert page.project_id == "project-1"
    assert page.doc_id == "document-1"
    assert page.document_label == "Documento Uno.pdf"
    assert page.page_idx == 12
    assert page.page_num == 13
    assert page.annotation_count == 2


def test_backfill_snapshot_contains_source_facts():
    user = NexusSourceUser(
        user_id="user-1",
        email="persona@jep.gov.co",
    )

    project = NexusSourceProject(
        project_id="project-1",
        owner_user_id="user-1",
        name="Proyecto Uno",
        status="active",
    )

    page = NexusSourceAnnotatedPage(
        project_id="project-1",
        doc_id="document-1",
        document_label="Documento Uno.pdf",
        page_idx=0,
        page_num=1,
    )

    snapshot = NexusBackfillSnapshot(
        users=(user,),
        projects=(project,),
        annotated_pages=(page,),
    )

    assert snapshot.users == (user,)
    assert snapshot.projects == (project,)
    assert snapshot.annotated_pages == (page,)
    assert snapshot.units == ()
    assert snapshot.user_unit_memberships == ()
    assert snapshot.project_memberships == ()


@pytest.mark.parametrize(
    ("factory", "expected_message"),
    [
        (
            lambda: NexusSourceUser(
                user_id="",
                email="persona@jep.gov.co",
            ),
            "user_id",
        ),
        (
            lambda: NexusSourceUnit(
                unit_id=" ",
                name="Unidad",
                unit_type="magistratura",
            ),
            "unit_id",
        ),
        (
            lambda: NexusSourceProject(
                project_id="",
                owner_user_id="user-1",
                name="Proyecto",
            ),
            "project_id",
        ),
        (
            lambda: NexusSourceProjectMembership(
                project_id="project-1",
                user_id="",
                role="owner",
            ),
            "user_id",
        ),
        (
            lambda: NexusSourceAnnotatedPage(
                project_id="project-1",
                doc_id="",
                page_idx=0,
            ),
            "doc_id",
        ),
    ],
)
def test_source_models_reject_blank_identifiers(
    factory,
    expected_message,
):
    with pytest.raises(ValueError, match=expected_message):
        factory()


def test_annotated_page_rejects_negative_page_index():
    with pytest.raises(ValueError, match="page_idx"):
        NexusSourceAnnotatedPage(
            project_id="project-1",
            doc_id="document-1",
            page_idx=-1,
        )


def test_annotated_page_requires_at_least_one_annotation():
    with pytest.raises(ValueError, match="annotation_count"):
        NexusSourceAnnotatedPage(
            project_id="project-1",
            doc_id="document-1",
            page_idx=0,
            annotation_count=0,
        )


def test_project_supports_deleted_at_from_source():
    deleted_at = datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    )

    project = NexusSourceProject(
        project_id="project-1",
        owner_user_id="user-1",
        name="Proyecto Uno",
        status="deleted",
        deleted_at=deleted_at,
    )

    assert project.deleted_at == deleted_at
