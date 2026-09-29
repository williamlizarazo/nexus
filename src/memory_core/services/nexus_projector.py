from __future__ import annotations

from datetime import date

from memory_core.domain.nexus_backfill import (
    NexusBackfillSnapshot,
    NexusSourceAnnotatedPage,
    NexusSourceUserUnitMembership,
)
from memory_core.domain.nexus_graph import (
    GraphEdge,
    GraphNode,
    NexusGraphSnapshot,
)


class NexusProjector:
    """
    Proyector puro y determinista de hechos fuente NEXUS a topología.

    No conoce Supabase, PostgreSQL, NetworkX ni tablas físicas.
    """

    def __init__(
        self,
        *,
        reference_date: date,
    ) -> None:
        self._reference_date = reference_date

    def project(
        self,
        snapshot: NexusBackfillSnapshot,
    ) -> NexusGraphSnapshot:
        self._validate_references(snapshot)

        nodes: dict[str, GraphNode] = {}
        edges: dict[
            tuple[str, str, str],
            GraphEdge,
        ] = {}

        self._project_users(
            snapshot,
            nodes,
        )

        self._project_units(
            snapshot,
            nodes,
        )

        self._project_projects(
            snapshot,
            nodes,
        )

        self._project_user_unit_memberships(
            snapshot,
            edges,
        )

        self._project_project_memberships(
            snapshot,
            edges,
        )

        self._project_annotated_pages(
            snapshot,
            nodes,
            edges,
        )

        return NexusGraphSnapshot(
            nodes=tuple(
                nodes[key]
                for key in sorted(nodes)
            ),
            edges=tuple(
                edges[key]
                for key in sorted(edges)
            ),
        )

    # ============================================================
    # VALIDATION
    # ============================================================

    def _validate_references(
        self,
        snapshot: NexusBackfillSnapshot,
    ) -> None:
        user_ids = {
            user.user_id
            for user in snapshot.users
        }

        unit_ids = {
            unit.unit_id
            for unit in snapshot.units
        }

        project_ids = {
            project.project_id
            for project in snapshot.projects
        }

        for project in snapshot.projects:
            if project.owner_user_id not in user_ids:
                raise ValueError(
                    "Unknown NEXUS user referenced by project "
                    f"{project.project_id}: "
                    f"{project.owner_user_id}"
                )

        for membership in snapshot.user_unit_memberships:
            if membership.user_id not in user_ids:
                raise ValueError(
                    "Unknown NEXUS user referenced by "
                    "organizational membership: "
                    f"{membership.user_id}"
                )

            if membership.unit_id not in unit_ids:
                raise ValueError(
                    "Unknown NEXUS organizational unit: "
                    f"{membership.unit_id}"
                )

        for membership in snapshot.project_memberships:
            if membership.user_id not in user_ids:
                raise ValueError(
                    "Unknown NEXUS user referenced by "
                    "project membership: "
                    f"{membership.user_id}"
                )

            if membership.project_id not in project_ids:
                raise ValueError(
                    "Unknown NEXUS project referenced by "
                    "project membership: "
                    f"{membership.project_id}"
                )

        for page in snapshot.annotated_pages:
            if page.project_id not in project_ids:
                raise ValueError(
                    "Unknown NEXUS project referenced by "
                    "annotated page: "
                    f"{page.project_id}"
                )

    # ============================================================
    # NODE PROJECTION
    # ============================================================

    @staticmethod
    def _project_users(
        snapshot: NexusBackfillSnapshot,
        nodes: dict[str, GraphNode],
    ) -> None:
        for user in snapshot.users:
            node_key = NexusProjector._user_key(
                user.user_id
            )

            nodes[node_key] = GraphNode(
                node_key=node_key,
                node_type="user",
                entity_id=user.user_id,
                label=(
                    user.full_name
                    or user.email
                    or user.user_id
                ),
                metadata={
                    "email": user.email,
                    "functional_role": (
                        user.functional_role
                    ),
                    "status": user.status,
                },
                active=(
                    NexusProjector._status_is_active(
                        user.status
                    )
                ),
            )

    @staticmethod
    def _project_units(
        snapshot: NexusBackfillSnapshot,
        nodes: dict[str, GraphNode],
    ) -> None:
        for unit in snapshot.units:
            node_key = NexusProjector._unit_key(
                unit.unit_id
            )

            nodes[node_key] = GraphNode(
                node_key=node_key,
                node_type="organizational_unit",
                entity_id=unit.unit_id,
                label=unit.name,
                metadata={
                    "unit_type": unit.unit_type,
                    "status": unit.status,
                },
                active=(
                    NexusProjector._status_is_active(
                        unit.status
                    )
                ),
            )

    @staticmethod
    def _project_projects(
        snapshot: NexusBackfillSnapshot,
        nodes: dict[str, GraphNode],
    ) -> None:
        for project in snapshot.projects:
            node_key = NexusProjector._project_key(
                project.project_id
            )

            nodes[node_key] = GraphNode(
                node_key=node_key,
                node_type="project",
                entity_id=project.project_id,
                label=project.name,
                metadata={
                    "owner_user_id": (
                        project.owner_user_id
                    ),
                    "description": (
                        project.description
                    ),
                    "status": project.status,
                    "deleted_at": (
                        project.deleted_at.isoformat()
                        if project.deleted_at
                        else None
                    ),
                },
                active=(
                    project.deleted_at is None
                    and NexusProjector._status_is_active(
                        project.status
                    )
                ),
            )

    # ============================================================
    # STRUCTURAL RELATIONS
    # ============================================================

    def _project_user_unit_memberships(
        self,
        snapshot: NexusBackfillSnapshot,
        edges: dict[
            tuple[str, str, str],
            GraphEdge,
        ],
    ) -> None:
        for membership in snapshot.user_unit_memberships:
            if not self._membership_is_current(
                membership
            ):
                continue

            edge = GraphEdge(
                source_key=self._user_key(
                    membership.user_id
                ),
                relation_type="BELONGS_TO",
                target_key=self._unit_key(
                    membership.unit_id
                ),
                metadata={
                    "is_primary": membership.is_primary,
                },
            )

            self._store_edge(
                edges,
                edge,
            )

    @staticmethod
    def _project_project_memberships(
        snapshot: NexusBackfillSnapshot,
        edges: dict[
            tuple[str, str, str],
            GraphEdge,
        ],
    ) -> None:
        for membership in snapshot.project_memberships:
            edge = GraphEdge(
                source_key=NexusProjector._user_key(
                    membership.user_id
                ),
                relation_type="WORKS_ON",
                target_key=NexusProjector._project_key(
                    membership.project_id
                ),
                metadata={
                    "role": membership.role,
                },
            )

            NexusProjector._store_edge(
                edges,
                edge,
            )

    # ============================================================
    # ANNOTATED DOCUMENTS / PAGES
    # ============================================================

    @staticmethod
    def _project_annotated_pages(
        snapshot: NexusBackfillSnapshot,
        nodes: dict[str, GraphNode],
        edges: dict[
            tuple[str, str, str],
            GraphEdge,
        ],
    ) -> None:
        document_labels = (
            NexusProjector._document_labels(
                snapshot.annotated_pages
            )
        )

        page_numbers = (
            NexusProjector._page_numbers(
                snapshot.annotated_pages
            )
        )

        for page in snapshot.annotated_pages:
            document_key = (
                NexusProjector._document_key(
                    page.doc_id
                )
            )

            page_key = NexusProjector._page_key(
                page.doc_id,
                page.page_idx,
            )

            if document_key not in nodes:
                nodes[document_key] = GraphNode(
                    node_key=document_key,
                    node_type="document",
                    entity_id=page.doc_id,
                    label=document_labels[
                        page.doc_id
                    ],
                )

            if page_key not in nodes:
                resolved_page_num = page_numbers[
                    (
                        page.doc_id,
                        page.page_idx,
                    )
                ]

                nodes[page_key] = GraphNode(
                    node_key=page_key,
                    node_type="page",
                    entity_id=(
                        f"{page.doc_id}:"
                        f"{page.page_idx}"
                    ),
                    label=(
                        f"Página {resolved_page_num}"
                        if resolved_page_num is not None
                        else (
                            "Página índice "
                            f"{page.page_idx}"
                        )
                    ),
                    metadata={
                        "doc_id": page.doc_id,
                        "page_idx": page.page_idx,
                        "page_num": (
                            resolved_page_num
                        ),
                    },
                )

            uses_edge = GraphEdge(
                source_key=(
                    NexusProjector._project_key(
                        page.project_id
                    )
                ),
                relation_type="USES",
                target_key=document_key,
            )

            contains_edge = GraphEdge(
                source_key=document_key,
                relation_type="CONTAINS",
                target_key=page_key,
            )

            NexusProjector._store_edge(
                edges,
                uses_edge,
            )

            NexusProjector._store_edge(
                edges,
                contains_edge,
            )

    # ============================================================
    # DETERMINISTIC RESOLUTION
    # ============================================================

    @staticmethod
    def _document_labels(
        pages: tuple[
            NexusSourceAnnotatedPage,
            ...,
        ],
    ) -> dict[str, str]:
        labels: dict[str, set[str]] = {}

        for page in pages:
            if not page.document_label:
                labels.setdefault(
                    page.doc_id,
                    set(),
                )
                continue

            normalized = page.document_label.strip()

            if normalized:
                labels.setdefault(
                    page.doc_id,
                    set(),
                ).add(normalized)

        doc_ids = {
            page.doc_id
            for page in pages
        }

        result: dict[str, str] = {}

        for doc_id in doc_ids:
            candidates = labels.get(
                doc_id,
                set(),
            )

            if not candidates:
                result[doc_id] = doc_id
                continue

            result[doc_id] = sorted(
                candidates,
                key=lambda value: (
                    value.casefold(),
                    value,
                ),
            )[0]

        return result

    @staticmethod
    def _page_numbers(
        pages: tuple[
            NexusSourceAnnotatedPage,
            ...,
        ],
    ) -> dict[
        tuple[str, int],
        int | None,
    ]:
        values: dict[
            tuple[str, int],
            set[int],
        ] = {}

        page_keys = {
            (
                page.doc_id,
                page.page_idx,
            )
            for page in pages
        }

        for page in pages:
            key = (
                page.doc_id,
                page.page_idx,
            )

            if page.page_num is not None:
                values.setdefault(
                    key,
                    set(),
                ).add(page.page_num)

        result: dict[
            tuple[str, int],
            int | None,
        ] = {}

        for key in page_keys:
            candidates = values.get(
                key,
                set(),
            )

            if len(candidates) == 1:
                result[key] = next(
                    iter(candidates)
                )
            else:
                result[key] = None

        return result

    # ============================================================
    # HELPERS
    # ============================================================

    def _membership_is_current(
        self,
        membership: NexusSourceUserUnitMembership,
    ) -> bool:
        if not self._status_is_active(
            membership.status
        ):
            return False

        if (
            membership.valid_from is not None
            and membership.valid_from
            > self._reference_date
        ):
            return False

        if (
            membership.valid_to is not None
            and membership.valid_to
            < self._reference_date
        ):
            return False

        return True

    @staticmethod
    def _status_is_active(
        status: str | None,
    ) -> bool:
        if status is None:
            return True

        return (
            status.strip().lower()
            == "active"
        )

    @staticmethod
    def _store_edge(
        edges: dict[
            tuple[str, str, str],
            GraphEdge,
        ],
        edge: GraphEdge,
    ) -> None:
        key = (
            edge.source_key,
            edge.relation_type,
            edge.target_key,
        )

        edges.setdefault(
            key,
            edge,
        )

    @staticmethod
    def _user_key(
        user_id: str,
    ) -> str:
        return f"user:{user_id}"

    @staticmethod
    def _unit_key(
        unit_id: str,
    ) -> str:
        return (
            "organizational_unit:"
            f"{unit_id}"
        )

    @staticmethod
    def _project_key(
        project_id: str,
    ) -> str:
        return f"project:{project_id}"

    @staticmethod
    def _document_key(
        doc_id: str,
    ) -> str:
        return f"document:{doc_id}"

    @staticmethod
    def _page_key(
        doc_id: str,
        page_idx: int,
    ) -> str:
        return (
            f"page:{doc_id}:{page_idx}"
        )
