from __future__ import annotations

import os

import core.config as config_module


def test_load_local_env_reads_dotenv_without_overriding_process_env(
    tmp_path,
    monkeypatch,
):
    env_file = tmp_path / ".env"

    env_file.write_text(
        "\n".join(
            [
                "MEMORY_RELATIONAL_PROVIDER=supabase",
                "SUPABASE_URL=https://example.supabase.co",
                "SUPABASE_KEY=file-key",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.delenv(
        "MEMORY_RELATIONAL_PROVIDER",
        raising=False,
    )
    monkeypatch.delenv(
        "SUPABASE_URL",
        raising=False,
    )

    monkeypatch.setenv(
        "SUPABASE_KEY",
        "process-key",
    )

    loaded = config_module.load_local_env(
        env_file
    )

    assert loaded is True

    assert (
        os.environ["MEMORY_RELATIONAL_PROVIDER"]
        == "supabase"
    )

    assert (
        os.environ["SUPABASE_URL"]
        == "https://example.supabase.co"
    )

    # La variable ya presente en el proceso
    # debe tener prioridad sobre .env.
    assert (
        os.environ["SUPABASE_KEY"]
        == "process-key"
    )


def test_load_config_loads_local_environment(
    monkeypatch,
):
    calls = []

    monkeypatch.setattr(
        config_module,
        "load_local_env",
        lambda: calls.append(True),
    )

    config_module.load_config()

    assert calls == [True]


def test_load_config_reads_normalized_authorized_emails(monkeypatch):
    monkeypatch.setattr(config_module, "load_local_env", lambda: True)
    monkeypatch.setenv(
        "APPMEMORIA_ADMIN_EMAILS",
        " ADMIN@example.org, second@example.org ",
    )
    monkeypatch.setenv("APPMEMORIA_VIEWER_EMAILS", " viewer@example.org, ")

    config = config_module.load_config()

    assert config.admin_emails == ("admin@example.org", "second@example.org")
    assert config.viewer_emails == ("viewer@example.org",)
