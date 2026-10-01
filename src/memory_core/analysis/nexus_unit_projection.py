from __future__ import annotations

from datetime import date
from itertools import combinations

import networkx as nx

from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
    NexusSourceUserUnitMembership,
)


class NexusUnitProjectionBuilder:
    """
    Construye una proyección analítica
    Unidad organizacional <-> Unidad organizacional.

    La relación se deriva de evidencia compartida por
    los usuarios con membresía vigente en cada unidad.
    """

    @staticmethod
    def build(
        snapshot: NexusBackfillSnapshot,
        *,
        reference_date: date,
    ) -> nx.Graph:

        graph = nx.Graph()

        # --------------------------------------------------------
        # UNITS
        # --------------------------------------------------------

        for unit in snapshot.units:
            graph.add_node(
                f"organizational_unit:{unit.unit_id}",
                unit_id=unit.unit_id,
                label=unit.name,
                unit_type=unit.unit_type,
                status=unit.status,
            )

        # --------------------------------------------------------
        # UNIT -> USERS
        # --------------------------------------------------------

        unit_users: dict[str, set[str]] = {
            unit.unit_id: set()
            for unit in snapshot.units
        }

        for membership in snapshot.user_unit_memberships:
            if not NexusUnitProjectionBuilder._membership_is_current(
                membership,
                reference_date=reference_date,
            ):
                continue

            unit_users.setdefault(
                membership.unit_id,
                set(),
            ).add(
                membership.user_id
            )

        # --------------------------------------------------------
        # USER -> PROJECTS
        # --------------------------------------------------------

        user_projects: dict[str, set[str]] = {}

        for membership in snapshot.project_memberships:
            user_projects.setdefault(
                membership.user_id,
                set(),
            ).add(
                membership.project_id
            )

        # --------------------------------------------------------
        # PROJECT -> DOCUMENTS / PAGES
        # --------------------------------------------------------

        project_documents: dict[
            str,
            set[str],
        ] = {}

        project_pages: dict[
            str,
            set[tuple[str, int]],
        ] = {}

        for page in snapshot.annotated_pages:
            project_documents.setdefault(
                page.project_id,
                set(),
            ).add(
                page.doc_id
            )

            project_pages.setdefault(
                page.project_id,
                set(),
            ).add(
                (
                    page.doc_id,
                    page.page_idx,
                )
            )

        # --------------------------------------------------------
        # UNIT -> PROJECTS / DOCUMENTS / PAGES
        # --------------------------------------------------------

        unit_projects: dict[
            str,
            set[str],
        ] = {}

        unit_documents: dict[
            str,
            set[str],
        ] = {}

        unit_pages: dict[
            str,
            set[tuple[str, int]],
        ] = {}

        for (
            unit_id,
            users,
        ) in unit_users.items():

            projects: set[str] = set()

            for user_id in users:
                projects.update(
                    user_projects.get(
                        user_id,
                        set(),
                    )
                )

            documents: set[str] = set()
            pages: set[
                tuple[str, int]
            ] = set()

            for project_id in projects:
                documents.update(
                    project_documents.get(
                        project_id,
                        set(),
                    )
                )

                pages.update(
                    project_pages.get(
                        project_id,
                        set(),
                    )
                )

            unit_projects[unit_id] = projects
            unit_documents[unit_id] = documents
            unit_pages[unit_id] = pages

        # --------------------------------------------------------
        # PAIRWISE PROJECTION
        # --------------------------------------------------------

        unit_ids = sorted(
            unit.unit_id
            for unit in snapshot.units
        )

        for (
            left_unit,
            right_unit,
        ) in combinations(
            unit_ids,
            2,
        ):

            shared_users = sorted(
                unit_users.get(
                    left_unit,
                    set(),
                )
                & unit_users.get(
                    right_unit,
                    set(),
                )
            )

            shared_projects = sorted(
                unit_projects.get(
                    left_unit,
                    set(),
                )
                & unit_projects.get(
                    right_unit,
                    set(),
                )
            )

            shared_documents = sorted(
                unit_documents.get(
                    left_unit,
                    set(),
                )
                & unit_documents.get(
                    right_unit,
                    set(),
                )
            )

            shared_pages = sorted(
                unit_pages.get(
                    left_unit,
                    set(),
                )
                & unit_pages.get(
                    right_unit,
                    set(),
                )
            )

            if not (
                shared_users
                or shared_projects
                or shared_documents
                or shared_pages
            ):
                continue

            graph.add_edge(
                f"organizational_unit:{left_unit}",
                f"organizational_unit:{right_unit}",
                shared_user_count=len(
                    shared_users
                ),
                shared_project_count=len(
                    shared_projects
                ),
                shared_document_count=len(
                    shared_documents
                ),
                shared_page_count=len(
                    shared_pages
                ),
                shared_users=tuple(
                    shared_users
                ),
                shared_projects=tuple(
                    shared_projects
                ),
                shared_documents=tuple(
                    shared_documents
                ),
                shared_pages=tuple(
                    shared_pages
                ),
            )

        return graph

    @staticmethod
    def _membership_is_current(
        membership: NexusSourceUserUnitMembership,
        *,
        reference_date: date,
    ) -> bool:

        if (
            membership.status is not None
            and membership.status.strip().lower()
            != "active"
        ):
            return False

        if (
            membership.valid_from is not None
            and membership.valid_from
            > reference_date
        ):
            return False

        if (
            membership.valid_to is not None
            and membership.valid_to
            < reference_date
        ):
            return False

        return True
