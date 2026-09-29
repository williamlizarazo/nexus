from __future__ import annotations

from types import SimpleNamespace

from memory_core.adapters.supabase.nexus_graph_projection import (
    SupabaseGraphProjectionRepository,
)
from memory_core.contracts.nexus_graph_projection import (
    GraphProjectionRepository,
)
from memory_core.domain.nexus_graph import (
    GraphEdge,
    GraphNode,
)


class FakeQuery:

    def __init__(
        self,
        client,
        table_name,
    ):
        self._client = client
        self._table_name = table_name
        self._filters = []
        self._orders = []
        self._start = 0
        self._end = None

    def select(
        self,
        columns,
    ):
        return self

    def eq(
        self,
        column,
        value,
    ):
        self._filters.append(
            (column, value)
        )
        return self

    def order(
        self,
        column,
    ):
        self._orders.append(
            column
        )
        return self

    def range(
        self,
        start,
        end,
    ):
        self._start = start
        self._end = end
        return self

    def upsert(
        self,
        rows,
        *,
        on_conflict=None,
    ):
        self._client.upserts.append(
            {
                "table": self._table_name,
                "rows": [
                    dict(row)
                    for row in rows
                ],
                "on_conflict": on_conflict,
            }
        )
        return self

    def execute(self):
        rows = [
            dict(row)
            for row
            in self._client.tables.get(
                self._table_name,
                [],
            )
        ]

        for column, value in self._filters:
            rows = [
                row
                for row in rows
                if row.get(column) == value
            ]

        for column in reversed(
            self._orders
        ):
            rows.sort(
                key=lambda row: row.get(
                    column
                )
            )

        if self._end is not None:
            rows = rows[
                self._start:
                self._end + 1
            ]

        return SimpleNamespace(
            data=rows
        )


class FakeClient:

    def __init__(
        self,
        tables=None,
    ):
        self.tables = tables or {
            "nexus_nodes": [],
            "nexus_edges": [],
        }
        self.upserts = []

    def table(
        self,
        table_name,
    ):
        return FakeQuery(
            self,
            table_name,
        )


def test_repository_implements_projection_contract():
    repository = (
        SupabaseGraphProjectionRepository(
            FakeClient()
        )
    )

    assert isinstance(
        repository,
        GraphProjectionRepository,
    )


def test_upsert_nodes_maps_graph_nodes_to_nexus_nodes():
    client = FakeClient()

    repository = (
        SupabaseGraphProjectionRepository(
            client
        )
    )

    repository.upsert_nodes(
        [
            GraphNode(
                node_key="user:user-1",
                node_type="user",
                entity_id="user-1",
                label="Usuario Uno",
                metadata={
                    "email": "uno@jep.gov.co",
                },
                active=True,
            ),
            GraphNode(
                node_key="project:project-1",
                node_type="project",
                entity_id="project-1",
                label="Proyecto Uno",
                metadata={
                    "status": "active",
                },
                active=True,
            ),
        ]
    )

    assert len(client.upserts) == 1

    operation = client.upserts[0]

    assert operation["table"] == "nexus_nodes"

    assert (
        operation["on_conflict"]
        == "node_key"
    )

    assert operation["rows"] == [
        {
            "node_key": "project:project-1",
            "node_type": "project",
            "entity_id": "project-1",
            "label": "Proyecto Uno",
            "metadata": {
                "status": "active",
            },
            "active": True,
        },
        {
            "node_key": "user:user-1",
            "node_type": "user",
            "entity_id": "user-1",
            "label": "Usuario Uno",
            "metadata": {
                "email": "uno@jep.gov.co",
            },
            "active": True,
        },
    ]


def test_upsert_edges_uses_structural_unique_key():
    client = FakeClient()

    repository = (
        SupabaseGraphProjectionRepository(
            client
        )
    )

    repository.upsert_edges(
        [
            GraphEdge(
                source_key="user:user-1",
                relation_type="WORKS_ON",
                target_key="project:project-1",
                metadata={
                    "role": "owner",
                },
                active=True,
            )
        ]
    )

    assert len(client.upserts) == 1

    operation = client.upserts[0]

    assert operation["table"] == "nexus_edges"

    assert operation["on_conflict"] == (
        "source_key,"
        "relation_type,"
        "target_key"
    )

    assert operation["rows"] == [
        {
            "source_key": "user:user-1",
            "relation_type": "WORKS_ON",
            "target_key": "project:project-1",
            "metadata": {
                "role": "owner",
            },
            "active": True,
        }
    ]


def test_list_nodes_maps_rows_and_filters_active():
    client = FakeClient(
        {
            "nexus_nodes": [
                {
                    "node_key": "user:user-2",
                    "node_type": "user",
                    "entity_id": "user-2",
                    "label": "Usuario Dos",
                    "metadata": {},
                    "active": False,
                },
                {
                    "node_key": "user:user-1",
                    "node_type": "user",
                    "entity_id": "user-1",
                    "label": "Usuario Uno",
                    "metadata": {
                        "email": "uno@jep.gov.co",
                    },
                    "active": True,
                },
            ],
            "nexus_edges": [],
        }
    )

    repository = (
        SupabaseGraphProjectionRepository(
            client
        )
    )

    nodes = repository.list_nodes()

    assert len(nodes) == 1

    assert nodes[0] == GraphNode(
        node_key="user:user-1",
        node_type="user",
        entity_id="user-1",
        label="Usuario Uno",
        metadata={
            "email": "uno@jep.gov.co",
        },
        active=True,
    )


def test_list_nodes_can_include_inactive_nodes():
    client = FakeClient(
        {
            "nexus_nodes": [
                {
                    "node_key": "user:user-1",
                    "node_type": "user",
                    "entity_id": "user-1",
                    "label": "Usuario Uno",
                    "metadata": {},
                    "active": False,
                },
            ],
            "nexus_edges": [],
        }
    )

    repository = (
        SupabaseGraphProjectionRepository(
            client
        )
    )

    nodes = repository.list_nodes(
        active_only=False,
    )

    assert len(nodes) == 1
    assert nodes[0].active is False


def test_list_edges_maps_rows_and_filters_active():
    client = FakeClient(
        {
            "nexus_nodes": [],
            "nexus_edges": [
                {
                    "source_key": "user:user-1",
                    "relation_type": "WORKS_ON",
                    "target_key": "project:project-1",
                    "metadata": {
                        "role": "owner",
                    },
                    "active": True,
                },
                {
                    "source_key": "user:user-2",
                    "relation_type": "WORKS_ON",
                    "target_key": "project:project-2",
                    "metadata": {},
                    "active": False,
                },
            ],
        }
    )

    repository = (
        SupabaseGraphProjectionRepository(
            client
        )
    )

    edges = repository.list_edges()

    assert edges == [
        GraphEdge(
            source_key="user:user-1",
            relation_type="WORKS_ON",
            target_key="project:project-1",
            metadata={
                "role": "owner",
            },
            active=True,
        )
    ]


def test_upsert_is_batched():
    client = FakeClient()

    repository = (
        SupabaseGraphProjectionRepository(
            client,
            write_batch_size=2,
        )
    )

    nodes = [
        GraphNode(
            node_key=f"user:user-{index}",
            node_type="user",
            entity_id=f"user-{index}",
            label=f"Usuario {index}",
        )
        for index in range(5)
    ]

    repository.upsert_nodes(
        nodes
    )

    assert [
        len(operation["rows"])
        for operation in client.upserts
    ] == [
        2,
        2,
        1,
    ]


def test_list_nodes_paginates_all_rows():
    client = FakeClient(
        {
            "nexus_nodes": [
                {
                    "node_key": f"user:user-{index}",
                    "node_type": "user",
                    "entity_id": f"user-{index}",
                    "label": f"Usuario {index}",
                    "metadata": {},
                    "active": True,
                }
                for index in range(5)
            ],
            "nexus_edges": [],
        }
    )

    repository = (
        SupabaseGraphProjectionRepository(
            client,
            read_page_size=2,
        )
    )

    nodes = repository.list_nodes()

    assert len(nodes) == 5

    assert [
        node.node_key
        for node in nodes
    ] == [
        "user:user-0",
        "user:user-1",
        "user:user-2",
        "user:user-3",
        "user:user-4",
    ]
