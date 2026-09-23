from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterable
from typing import Any

from memory_core.domain.organization_directory_entry import (
    OrganizationDirectoryEntry,
)


class OrganizationalDirectoryPresenter:
    _UNIT_TYPES = {
        "magistratura": (
            0,
            "Magistratura",
        ),
        "direccion": (
            1,
            "Dirección",
        ),
    }

    _STATUS = {
        "active": "Activo",
        "inactive": "Inactivo",
    }

    @staticmethod
    def _readable(
        value: str,
    ) -> str:
        return (
            value
            .replace("_", " ")
            .strip()
            .title()
        )

    @classmethod
    def rows(
        cls,
        entries: Iterable[
            OrganizationDirectoryEntry
        ],
    ) -> list[dict[str, Any]]:
        users: OrderedDict[
            str,
            dict[str, Any],
        ] = OrderedDict()

        for entry in entries:
            user = users.setdefault(
                entry.user_id,
                {
                    "name": (
                        entry.full_name
                        or ""
                    ),
                    "email": entry.email,
                    "role": (
                        entry.functional_role
                        or ""
                    ),
                    "status": (
                        entry.user_status
                        or ""
                    ),
                    "units": {},
                },
            )

            if (
                not user["name"]
                and entry.full_name
            ):
                user["name"] = (
                    entry.full_name
                )

            if (
                not user["role"]
                and entry.functional_role
            ):
                user["role"] = (
                    entry.functional_role
                )

            if not entry.unit_name:
                continue

            normalized_type = (
                entry.unit_type
                or ""
            ).strip().lower()

            order, type_label = (
                cls._UNIT_TYPES.get(
                    normalized_type,
                    (
                        2,
                        (
                            cls._readable(
                                normalized_type
                            )
                            if normalized_type
                            else ""
                        ),
                    ),
                )
            )

            key = (
                normalized_type,
                (
                    entry.unit_id
                    or entry.unit_name.casefold()
                ),
            )

            user["units"][key] = (
                order,
                type_label.casefold(),
                entry.unit_name.casefold(),
                entry.unit_name,
                entry.unit_id,
            )

        result: list[
            dict[str, Any]
        ] = []

        for user_id, user in users.items():
            units = sorted(
                user["units"].values()
            )
            status = user["status"]
            unit_ids = tuple(
                unit[4]
                for unit in units
                if unit[4]
            )

            result.append(
                {
                    "user_id": user_id,
                    "Nombre": (
                        user["name"]
                        or user["email"]
                    ),
                    "Correo": user["email"],
                    "Rol funcional": (
                        user["role"]
                        or "—"
                    ),
                    "Magistratura / Dirección": (
                        " · ".join(
                            unit[3]
                            for unit in units
                        )
                        if units
                        else "—"
                    ),
                    "Estado": (
                        cls._STATUS.get(
                            status,
                            cls._readable(
                                status
                            ),
                        )
                    ),
                    "_unit_ids": unit_ids,
                    "_functional_role": user["role"],
                    "_status": status,
                }
            )

        return sorted(
            result,
            key=lambda row: (
                row["Nombre"].casefold(),
                row["Correo"].casefold(),
            ),
        )
