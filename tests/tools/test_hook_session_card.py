"""tools/hook_session_card.py 의 순수 함수. stdin 을 읽는 main 은 실제 입력 표로 확인한다."""

from __future__ import annotations

import json

from tools.hook_session_card import output_for
from tools.run_hooks import registered_matchers


def _payload(tool_input: object) -> bytes:
    return json.dumps(
        {"tool_name": "mcp__ccd_session__start_session", "tool_input": tool_input},
        ensure_ascii=False,
    ).encode("utf-8")


def _deny_reason(output: str | None) -> str:
    assert output is not None
    parsed = json.loads(output)
    specific = parsed["hookSpecificOutput"]
    assert specific["hookEventName"] == "PreToolUse"
    assert specific["permissionDecision"] == "deny"
    reason = specific["permissionDecisionReason"]
    assert isinstance(reason, str)
    return reason


def test_스스로_낸_카드는_막고_까닭을_준다() -> None:
    raw = _payload(
        {
            "initiation": "own_initiative",
            "context": "fresh",
            "title": "후속 일",
            "prompt": "한다",
        }
    )

    reason = _deny_reason(output_for(raw))

    assert '일지의 "다음"' in reason
    assert "대기열" in reason
    assert "user_asked" in reason
    assert "offer" in reason
    assert "ADR 0037" in reason


def test_막는_출력은_ASCII라_훅_환경의_인코딩에_기대지_않는다() -> None:
    """훅 환경에 `PYTHONUTF8` 이 없으면 표준 출력은 cp949 이고 까닭 글의 `—` 를 쓰지 못해 예외로
    끝난다. PreToolUse 의 예외는 막지 않고 지나간다(.claude/rules/tools.md)."""
    output = output_for(_payload({"initiation": "own_initiative"}))

    assert output is not None
    assert output.isascii()


def test_사용자가_시킨_카드는_지나간다() -> None:
    assert output_for(_payload({"initiation": "user_asked", "prompt": "한다"})) is None


def test_사용자에게_묻는_카드는_지나간다() -> None:
    assert output_for(_payload({"initiation": "offer", "prompt": "한다"})) is None


def test_이미_뜬_카드의_시작은_지나간다() -> None:
    assert output_for(_payload({"proposal_id": "task_ab12cd34"})) is None


def test_JSON이_아니면_지나간다() -> None:
    assert output_for(b"not json {") is None


def test_tool_input이_객체가_아니면_지나간다() -> None:
    assert output_for(_payload(["own_initiative"])) is None
    assert output_for(_payload("own_initiative")) is None


def test_최상위가_객체가_아니면_지나간다() -> None:
    assert output_for(b'["own_initiative"]') is None


def test_다른_세션_도구와_이름이_바뀐_도구는_보지_않는다() -> None:
    """거짓 음성이다. `output_for` 는 `tool_name` 을 보지 않고, settings.json 이 이 훅을 이 도구
    이름 하나의 매처에만 건다. 그래서 `hand_off_to_session` 이나 이름이 바뀐 도구는 불리지
    않는다."""
    assert registered_matchers("hook_session_card.py", "PreToolUse") == [
        "mcp__ccd_session__start_session"
    ]
