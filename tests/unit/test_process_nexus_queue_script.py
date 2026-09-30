from datetime import date

from memory_core.scripts.process_nexus_queue import (
    build_processor,
    parse_reference_date,
)


def test_parse_reference_date():
    assert parse_reference_date(
        "2026-09-30"
    ) == date(
        2026,
        9,
        30,
    )


def test_build_processor_wires_nexus_components():
    class FakeClient:
        pass

    processor = build_processor(
        client=FakeClient(),
        reference_date=date(
            2026,
            9,
            30,
        ),
    )

    assert processor is not None
