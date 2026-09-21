"""시스템 Clock. UTC 시각과 실행마다 다른 식별자."""

from datetime import UTC
from uuid import UUID

from agent_os.adapters.clock import SystemClock
from agent_os.core.ports import Clock


def test_시각은_UTC_aware다() -> None:
    clock: Clock = SystemClock()

    assert clock.now().tzinfo is UTC


def test_실행_식별자는_실행마다_다르고_uuid다() -> None:
    clock: Clock = SystemClock()

    first, second = clock.new_run_id(), clock.new_run_id()

    assert first != second
    assert UUID(first).version == 4
