"""이벤트는 디스크에 남는 형식이다. JSON 왕복과 판별을 확인한다."""

from datetime import UTC, datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from agent_os.sdk import Event, RunStarted


def test_event_round_trips_through_json() -> None:
    event = RunStarted(run_id="r1", ts=datetime.now(UTC), agent="echo", request="hi")
    adapter = TypeAdapter[Event](Event)
    restored = adapter.validate_json(adapter.dump_json(event))
    assert restored == event


def test_unknown_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TypeAdapter[Event](Event).validate_python(
            {"type": "nope", "run_id": "r1", "ts": "2026-09-19T00:00:00Z"}
        )


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RunStarted(run_id="r1", ts=datetime(2026, 9, 19), agent="echo", request="hi")  # noqa: DTZ001
