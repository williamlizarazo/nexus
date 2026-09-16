from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AppConfig:
    app_name: str
    environment: str
    debug: bool


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_config() -> AppConfig:
    return AppConfig(
        app_name="appmemoria",
        environment=os.getenv("APPMEMORIA_ENV", "local"),
        debug=_env_bool("APPMEMORIA_DEBUG", default=True),
    )
