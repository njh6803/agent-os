"""tools/run_hooks.py — 판정·표 읽기·빈자리 셈은 순수 함수로, 배관은 실제 훅 하나로 잰다.

표의 빈자리(등록됐는데 표에 없는 훅)는 러너가 스스로 센다. 여기서는 이 저장소가 지금 빈자리 0인 것과
빈자리를 만들면 잡히는 것을 한 쌍으로 둔다(tests.md).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import JsonValue
from tools.run_hooks import (
    PAYLOADS,
    Case,
    coverage_gaps,
    create_fixtures,
    load_cases,
    outcome_of,
    registered_hooks,
    run_case,
    substitute,
)


def test_종료_코드와_출력을_기대_넷으로_읽는다() -> None:
    deny = json.dumps(
        {"hookSpecificOutput": {"permissionDecision": "deny", "permissionDecisionReason": "x"}}
    )
    context = json.dumps({"hookSpecificOutput": {"additionalContext": "retro"}})
    assert outcome_of(0, deny) == "deny"
    assert outcome_of(0, context) == "context"
    assert outcome_of(0, json.dumps({"decision": "block", "reason": "x"})) == "block"
    assert outcome_of(2, "이유") == "block"
    assert outcome_of(0, "") == "silent"
    assert outcome_of(0, "   \n") == "silent"


def test_기대_밖의_결과는_그대로_설명한다() -> None:
    """트레이스백(종료 1, stderr 만)과 JSON 아닌 출력은 기대와 어긋나는 것으로 보인다."""
    assert outcome_of(1, "") == "exit 1"
    assert outcome_of(0, "not json") == "output"
    assert outcome_of(0, "[1, 2]") == "output"
    assert (
        outcome_of(0, json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse"}}))
        == "output"
    )


def test_자리표시자는_표_안까지_바꾼다() -> None:
    payload: dict[str, JsonValue] = {
        "tool_input": {"command": "cat ${ROOT}/x"},
        "cwd": "${MAIN_REPO}",
        "n": 1,
        "l": ["${ROOT}"],
    }

    assert substitute(payload, {"ROOT": "/r", "MAIN_REPO": "/m"}) == {
        "tool_input": {"command": "cat /r/x"},
        "cwd": "/m",
        "n": 1,
        "l": ["/r"],
    }


def test_표의_기대는_넷_중_하나여야_한다(tmp_path: Path) -> None:
    table = tmp_path / "t.toml"
    table.write_text(
        '[[case]]\nhook = "hook_env_read.py"\nexpect = "warn"\npayload = { tool_name = "Bash" }\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="expect"):
        load_cases(table)


def test_표가_가리키는_훅_파일은_있어야_한다(tmp_path: Path) -> None:
    table = tmp_path / "t.toml"
    table.write_text(
        '[[case]]\nhook = "hook_없다.py"\nexpect = "deny"\npayload = { tool_name = "Bash" }\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="없다"):
        load_cases(table)


def _case(hook: str, expect: str) -> Case:
    return Case.model_validate({"hook": hook, "expect": expect, "payload": {}})


def test_등록된_훅의_빈자리를_센다() -> None:
    """표에 없는 훅, 침묵만 있는 훅, 발동만 있는 훅이 각각 한 줄이다."""
    cases = [
        _case("hook_env_read.py", "deny"),
        _case("hook_env_read.py", "silent"),
        _case("hook_bash_heredoc.py", "silent"),
        _case("hook_bash_gate_pipe.py", "context"),
    ]
    registered = {
        "hook_env_read.py",
        "hook_bash_heredoc.py",
        "hook_bash_gate_pipe.py",
        "hook_journal_retro.py",
    }

    assert coverage_gaps(cases, registered) == [
        "hook_bash_gate_pipe.py: 침묵 사례가 없다",
        "hook_bash_heredoc.py: 발동 사례가 없다",
        "hook_journal_retro.py: 등록됐는데 표에 없다",
    ]


def test_이_저장소의_표는_등록된_훅마다_발동과_침묵이_있다() -> None:
    registered = registered_hooks()

    assert registered
    assert coverage_gaps(load_cases(PAYLOADS), registered) == []


def test_등록된_훅을_표에서_빼면_빈자리를_잡는다() -> None:
    cases = [case for case in load_cases(PAYLOADS) if case.hook != "hook_env_read.py"]

    assert coverage_gaps(cases, registered_hooks()) == ["hook_env_read.py: 등록됐는데 표에 없다"]


def test_실제_훅_하나를_페이로드로_돌려_판정한다(tmp_path: Path) -> None:
    """배관(uv run 자식, 바이트 stdin, PYTHONUTF8 없는 환경)을 한 번은 실제로 본다."""
    replacements = create_fixtures(tmp_path)
    deny = Case(
        hook="hook_env_read.py",
        expect="deny",
        payload={"tool_name": "Bash", "tool_input": {"command": "cat .env"}},
    )
    silent = Case(
        hook="hook_env_read.py",
        expect="silent",
        payload={"tool_name": "Bash", "tool_input": {"command": "ls"}},
    )

    assert run_case(deny, replacements).ok
    assert run_case(silent, replacements).ok
    assert (tmp_path / "on-main" / ".git").is_dir()
    assert (tmp_path / "transcript-used.jsonl").is_file()
