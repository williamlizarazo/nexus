from __future__ import annotations

from itertools import combinations

import networkx as nx

from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
)


class NexusUserProjectionBuilder:
    """
    Construye una proyección analítica Usuario <-> Usuario.

    La proyección es derivada y no se persiste como topología NEXUS.
    """

    @staticmethod
    def build(
        snapshot: NexusBackfillSnapshot,
    ) -> nx.Graph:

        graph = nx.Graph()

        # --------------------------------------------------------
        # USERS
        # --------------------------------------------------------

        for user in snapshot.users:
            graph.add_node(
                f"user:{user.user_id}",
                user_id=user.user_id,
                label=(
                    user.full_name
                    or user.email
                    or user.user_id
                ),
                email=user.email,
                functional_role=(
                    user.functional_role
                ),
                status=user.status,
            )

        # --------------------------------------------------------
        # USER -> PROJECT
        # --------------------------------------------------------

        user_projects: dict[
            str,
            set[str],
        ] = {
            user.user_id: set()
            for user in snapshot.users
        }

        project_users: dict[
            str,
            set[str],
        ] = {}

        for membership in snapshot.project_memberships:
            user_projects.setdefault(
                membership.user_id,
                set(),
            ).add(
                membership.project_id
            )

            project_users.setdefault(
                membership.project_id,
                set(),
            ).add(
                membership.user_id
            )

        # --------------------------------------------------------
        # PROJECT -> DOCUMENT / PAGE
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
        # USER -> DOCUMENT / PAGE
        # --------------------------------------------------------

        user_documents: dict[
            str,
            set[str],
        ] = {}

        user_pages: dict[
            str,
            set[tuple[str, int]],
        ] = {}

        for (
            user_id,
            project_ids,
        ) in user_projects.items():

            documents: set[str] = set()
            pages: set[
                tuple[str, int]
            ] = set()

            for project_id in project_ids:
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

            user_documents[user_id] = (
                documents
            )

            user_pages[user_id] = pages

        # --------------------------------------------------------
        # PAIRWISE PROJECTION
        # --------------------------------------------------------

        user_ids = sorted(
            user.user_id
            for user in snapshot.users
        )

        for (
            left_user,
            right_user,
        ) in combinations(
            user_ids,
            2,
        ):

            shared_projects = sorted(
                user_projects.get(
                    left_user,
                    set(),
                )
                & user_projects.get(
                    right_user,
                    set(),
                )
            )

            shared_documents = sorted(
                user_documents.get(
                    left_user,
                    set(),
                )
                & user_documents.get(
                    right_user,
                    set(),
                )
            )

            shared_pages = sorted(
                user_pages.get(
                    left_user,
                    set(),
                )
                & user_pages.get(
                    right_user,
                    set(),
                )
            )

            if not (
                shared_projects
                or shared_documents
                or shared_pages
            ):
                continue

            graph.add_edge(
                f"user:{left_user}",
                f"user:{right_user}",
                shared_project_count=len(
                    shared_projects
                ),
                shared_document_count=len(
                    shared_documents
                ),
                shared_page_count=len(
                    shared_pages
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
