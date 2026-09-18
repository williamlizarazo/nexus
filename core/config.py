from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


APP_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True, slots=True)
class AppConfig:
    app_name: str
    environment: str
    debug: bool
    admin_emails: tuple[str, ...] = ()
    viewer_emails: tuple[str, ...] = ()


def _env_bool(
    name: str,
    default: bool = False,
) -> bool:
    value = os.getenv(name)

    if value is None:
        return default

    return value.strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _env_csv(name: str) -> tuple[str, ...]:
    return tuple(
        value.strip().lower()
        for value in os.getenv(name, "").split(",")
        if value.strip()
    )


def load_local_env(
    dotenv_path: str | Path | None = None,
) -> bool:
    """
    Load appmemoria local configuration from .env.

    Existing process/environment variables always
    take precedence over values stored in .env.
    """

    path = (
        Path(dotenv_path)
        if dotenv_path is not None
        else APP_DIR / ".env"
    )

    if not path.exists():
        return False

    return bool(
        load_dotenv(
            dotenv_path=path,
            override=False,
        )
    )


def load_config() -> AppConfig:
    # Local development configuration is loaded
    # before the application dependencies are built.
    load_local_env()

    return AppConfig(
        app_name="appmemoria",
        environment=os.getenv(
            "APPMEMORIA_ENV",
            "local",
        ),
        debug=_env_bool(
            "APPMEMORIA_DEBUG",
            default=True,
        ),
        admin_emails=_env_csv(
            "APPMEMORIA_ADMIN_EMAILS",
        ),
        viewer_emails=_env_csv(
            "APPMEMORIA_VIEWER_EMAILS",
        ),
    )
