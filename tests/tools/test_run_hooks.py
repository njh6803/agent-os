"""tools/run_hooks.py — 판정·표 읽기·빈자리 셈은 순수 함수로, 배관은 실제 훅 하나로 잰다.

표의 빈자리(등록과 표가 한쪽에만 있는 훅, 발동·침묵 한쪽이 없는 훅)는 러너가 스스로 센다. 여기서는
이 저장소가 지금 빈자리 0인 것과 빈자리를 만들면 잡히는 것을 한 쌍으로 둔다(tests.md). 등록 쪽을
빼는 변이와 표 쪽을 빼는 변이가 각각 하나다.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from pydantic import JsonValue
from tools.run_hooks import (
    PAYLOADS,
    Case,
    Registration,
    coverage_gaps,
    create_fixtures,
    hook_environment,
    load_cases,
    outcome_of,
    registered_hooks,
    run_case,
    substitute,
)


def _specific(**fields: str) -> str:
    return json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", **fields}})


def test_종료_코드와_출력을_기대_넷으로_읽는다() -> None:
    deny = _specific(permissionDecision="deny", permissionDecisionReason="x")
    context = _specific(additionalContext="retro")
    assert outcome_of(0, deny, "PreToolUse") == "deny"
    assert outcome_of(0, context, "PreToolUse") == "context"
    block = json.dumps({"decision": "block", "reason": "x"})
    assert outcome_of(0, block, "UserPromptSubmit") == "block"
    assert outcome_of(2, "이유", "PreToolUse") == "block"
    assert outcome_of(0, "", "PreToolUse") == "silent"
    assert outcome_of(0, "   \n", "PreToolUse") == "silent"


def test_기대_밖의_결과는_그대로_설명한다() -> None:
    """트레이스백(종료 1, stderr 만)과 JSON 아닌 출력은 기대와 어긋나는 것으로 보인다."""
    assert outcome_of(1, "", "PreToolUse") == "exit 1"
    assert outcome_of(0, "not json", "PreToolUse") == "output"
    assert outcome_of(0, "[1, 2]", "PreToolUse") == "output"
    assert outcome_of(0, _specific(), "PreToolUse") == "output"


def test_hookEventName_이_없거나_등록된_이벤트와_다르면_어긋남이다() -> None:
    """hookEventName 이 없거나 다른 hookSpecificOutput 은 Claude Code 가 받지 않는다."""
    without_event = json.dumps({"hookSpecificOutput": {"permissionDecision": "deny"}})
    assert outcome_of(0, without_event, "PreToolUse") == "output"
    assert outcome_of(0, _specific(permissionDecision="deny"), "PostToolUse") == "event PreToolUse"


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


def _settings(hooks: dict[str, list[dict[str, JsonValue]]]) -> str:
    groups = {event: [{"hooks": entries}] for event, entries in hooks.items()}
    return json.dumps({"hooks": groups})


def test_등록은_이벤트와_시간_제한이고_시간_제한이_없으면_Claude_Code_기본값이다(
    tmp_path: Path,
) -> None:
    settings = tmp_path / "settings.json"
    command = 'uv run python "${CLAUDE_PROJECT_DIR}/tools/hook_x.py"'
    settings.write_text(
        _settings({"PreToolUse": [{"command": command, "timeout": 20}]}), encoding="utf-8"
    )
    assert registered_hooks(settings) == {"hook_x.py": Registration("PreToolUse", 20)}

    settings.write_text(_settings({"PostToolUse": [{"command": command}]}), encoding="utf-8")
    assert registered_hooks(settings) == {"hook_x.py": Registration("PostToolUse", 60)}


def test_훅_하나가_이벤트_둘에_등록되면_거절한다(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    entry: dict[str, JsonValue] = {"command": 'python "${CLAUDE_PROJECT_DIR}/tools/hook_x.py"'}
    settings.write_text(
        _settings({"PreToolUse": [entry], "PostToolUse": [entry]}), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="둘에 등록"):
        registered_hooks(settings)


def _case(hook: str, expect: str) -> Case:
    return Case.model_validate({"hook": hook, "expect": expect, "payload": {}})


def test_등록과_표의_빈자리를_센다() -> None:
    """표에 없는 훅, 등록되지 않은 훅, 침묵만 있는 훅, 발동만 있는 훅이 각각 한 줄이다."""
    cases = [
        _case("hook_env_read.py", "deny"),
        _case("hook_env_read.py", "silent"),
        _case("hook_bash_heredoc.py", "silent"),
        _case("hook_bash_gate_pipe.py", "context"),
        _case("hook_prompt_directive.py", "context"),
        _case("hook_prompt_directive.py", "silent"),
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
        "hook_prompt_directive.py: 표에 있는데 등록되지 않았다",
    ]


def test_이_저장소의_표는_등록된_훅마다_발동과_침묵이_있다() -> None:
    registered = registered_hooks()

    assert registered
    assert coverage_gaps(load_cases(PAYLOADS), registered) == []


def test_등록된_훅을_표에서_빼면_빈자리를_잡는다() -> None:
    cases = [case for case in load_cases(PAYLOADS) if case.hook != "hook_env_read.py"]

    assert coverage_gaps(cases, registered_hooks()) == ["hook_env_read.py: 등록됐는데 표에 없다"]


def test_표의_훅을_등록에서_빼면_빈자리를_잡는다() -> None:
    """settings.json 에서 등록만 지우고 파일과 사례를 남기면 실제 세션에는 그 훅이 없다."""
    registered = {hook for hook in registered_hooks() if hook != "hook_env_read.py"}

    assert coverage_gaps(load_cases(PAYLOADS), registered) == [
        "hook_env_read.py: 표에 있는데 등록되지 않았다"
    ]


def test_자식_환경은_러너를_띄운_세션의_entrypoint_를_물려주지_않는다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Stop 훅(hook_stop_korean)은 SDK 세션에서 침묵한다. 러너가 SDK 세션 안에서 돌면 그 값을
    물려받아 발동 사례가 침묵으로 어긋난다. 판정이 러너를 띄운 자리에 기대지 않게 한다.
    """
    monkeypatch.setenv("CLAUDE_CODE_ENTRYPOINT", "sdk-py")

    # 키만 본다. 환경 전체를 단언하면 실패 출력에 값(토큰일 수 있다)이 찍힌다.
    assert "CLAUDE_CODE_ENTRYPOINT" not in hook_environment().keys()


def test_실제_훅_하나를_페이로드로_돌려_판정한다(tmp_path: Path) -> None:
    """배관(uv run 자식, 바이트 stdin, PYTHONUTF8 없는 환경)을 한 번은 실제로 본다."""
    replacements = create_fixtures(tmp_path)
    registration = Registration("PreToolUse", 20)
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

    assert run_case(deny, replacements, registration).ok
    assert run_case(silent, replacements, registration).ok
    assert (tmp_path / "on-main" / ".git").is_dir()
    assert (tmp_path / "transcript-used.jsonl").is_file()


def test_푸시하지_않은_커밋이_있는_저장소를_만든다(tmp_path: Path) -> None:
    """`${UNPUSHED_REPO}` 는 upstream 이 HEAD 의 조상이고 HEAD 와 다르다.

    hook_pr_head_sync 의 발동 사례가 기대는 모양이다.
    """
    repo = create_fixtures(tmp_path)["UNPUSHED_REPO"]

    def rev(name: str) -> str:
        result = subprocess.run(
            ["git", "-C", repo, "rev-parse", name], check=True, capture_output=True, text=True
        )
        return result.stdout.strip()

    ancestor = subprocess.run(
        ["git", "-C", repo, "merge-base", "--is-ancestor", "@{u}", "HEAD"], check=False
    )

    assert rev("HEAD") != rev("@{u}")
    assert ancestor.returncode == 0


def test_등록된_이벤트와_다른_훅은_실제로_돌려도_어긋남이다(tmp_path: Path) -> None:
    replacements = create_fixtures(tmp_path)
    deny = Case(
        hook="hook_env_read.py",
        expect="deny",
        payload={"tool_name": "Bash", "tool_input": {"command": "cat .env"}},
    )

    result = run_case(deny, replacements, Registration("PostToolUse", 20))

    assert result.outcome == "event PreToolUse"
    assert not result.ok


def test_시간_제한을_넘긴_자식은_timeout_으로_판정한다(tmp_path: Path) -> None:
    """제한 0초 — uv 자식이 뜨기도 전에 끝나므로 어떤 훅이든 넘긴다."""
    replacements = create_fixtures(tmp_path)
    case = Case(hook="hook_env_read.py", expect="silent", payload={"tool_name": "Bash"})

    result = run_case(case, replacements, Registration("PreToolUse", 0))

    assert result.outcome == "timeout"
    assert not result.ok
    assert "0초" in result.output
