from memory_core.adapters.supabase.research_activity_source import (
    _resolve_created_at,
)


def test_resolve_created_at_prefers_original_json_timestamp():
    row = {
        "created_at": "2026-08-05T22:35:49+00:00",
        "payload_json": {
            "created_at": "2026-07-31T22:11:29+00:00",
        },
    }

    value = _resolve_created_at(
        row,
        json_field="payload_json",
    )

    assert value.isoformat() == (
        "2026-07-31T22:11:29+00:00"
    )


def test_resolve_created_at_falls_back_to_row_timestamp():
    row = {
        "created_at": "2026-08-05T22:35:49+00:00",
        "payload_json": {},
    }

    value = _resolve_created_at(
        row,
        json_field="payload_json",
    )

    assert value.isoformat() == (
        "2026-08-05T22:35:49+00:00"
    )
