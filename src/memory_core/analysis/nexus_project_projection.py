from __future__ import annotations

from itertools import combinations

import networkx as nx

from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
)


class NexusProjectProjectionBuilder:
    """
    Construye una proyección analítica Proyecto <-> Proyecto.

    La relación se deriva de evidencia compartida:
    usuarios, documentos y páginas.
    """

    @staticmethod
    def build(
        snapshot: NexusBackfillSnapshot,
    ) -> nx.Graph:

        graph = nx.Graph()

        # --------------------------------------------------------
        # PROJECTS
        # --------------------------------------------------------

        for project in snapshot.projects:
            graph.add_node(
                f"project:{project.project_id}",
                project_id=project.project_id,
                label=project.name,
                description=project.description,
                status=project.status,
                active=(
                    project.deleted_at is None
                    and (
                        project.status is None
                        or project.status.strip().lower()
                        == "active"
                    )
                ),
            )

        # --------------------------------------------------------
        # PROJECT -> USERS
        # --------------------------------------------------------

        project_users: dict[
            str,
            set[str],
        ] = {
            project.project_id: set()
            for project in snapshot.projects
        }

        for membership in snapshot.project_memberships:
            project_users.setdefault(
                membership.project_id,
                set(),
            ).add(
                membership.user_id
            )

        # --------------------------------------------------------
        # PROJECT -> DOCUMENTS / PAGES
        # --------------------------------------------------------

        project_documents: dict[
            str,
            set[str],
        ] = {
            project.project_id: set()
            for project in snapshot.projects
        }

        project_pages: dict[
            str,
            set[tuple[str, int]],
        ] = {
            project.project_id: set()
            for project in snapshot.projects
        }

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
        # PAIRWISE PROJECTION
        # --------------------------------------------------------

        project_ids = sorted(
            project.project_id
            for project in snapshot.projects
        )

        for (
            left_project,
            right_project,
        ) in combinations(
            project_ids,
            2,
        ):

            shared_users = sorted(
                project_users.get(
                    left_project,
                    set(),
                )
                & project_users.get(
                    right_project,
                    set(),
                )
            )

            shared_documents = sorted(
                project_documents.get(
                    left_project,
                    set(),
                )
                & project_documents.get(
                    right_project,
                    set(),
                )
            )

            shared_pages = sorted(
                project_pages.get(
                    left_project,
                    set(),
                )
                & project_pages.get(
                    right_project,
                    set(),
                )
            )

            if not (
                shared_users
                or shared_documents
                or shared_pages
            ):
                continue

            graph.add_edge(
                f"project:{left_project}",
                f"project:{right_project}",
                shared_user_count=len(
                    shared_users
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
                shared_documents=tuple(
                    shared_documents
                ),
                shared_pages=tuple(
                    shared_pages
                ),
            )

        return graph
