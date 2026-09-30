from dataclasses import FrozenInstanceError

import pytest

from memory_core.domain.nexus_incremental import NexusAffectedScope


def test_affected_scope_stores_incremental_identifiers():
    scope = NexusAffectedScope(
        project_ids=(
            "project-2",
            "project-1",
        ),
        user_ids=(
            "user-1",
        ),
        unit_ids=(
            "unit-1",
        ),
    )

    assert scope.project_ids == (
        "project-1",
        "project-2",
    )
    assert scope.user_ids == (
        "user-1",
    )
    assert scope.unit_ids == (
        "unit-1",
    )


def test_affected_scope_removes_duplicates_and_blank_values():
    scope = NexusAffectedScope(
        project_ids=(
            "project-1",
            "project-1",
            "",
        ),
        user_ids=(
            "user-1",
            " user-1 ",
            "",
        ),
        unit_ids=(),
    )

    assert scope.project_ids == (
        "project-1",
    )
    assert scope.user_ids == (
        "user-1",
    )
    assert scope.unit_ids == ()


def test_affected_scope_is_immutable():
    scope = NexusAffectedScope(
        project_ids=("project-1",),
    )

    with pytest.raises(FrozenInstanceError):
        scope.project_ids = ()
