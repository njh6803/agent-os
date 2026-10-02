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
    NoticeResult,
    Registration,
    coverage_gaps,
    create_fixtures,
    expected_notice,
    hook_environment,
    launch_argv,
    load_cases,
    notice_outcome,
    outcome_of,
    registered_hooks,
    registration_command,
    run_case,
    run_notices,
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


# 등록 모양의 글자는 test_러너가_띄우는_인자는_… 가 인자 목록으로 고정한다. 여기서는 그 원천을 쓴다.
_REGISTERED_X = registration_command("hook_x.py")


def test_등록은_이벤트와_시간_제한이고_시간_제한이_없으면_Claude_Code_기본값이다(
    tmp_path: Path,
) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(
        _settings({"PreToolUse": [{"command": _REGISTERED_X, "timeout": 20}]}), encoding="utf-8"
    )
    assert registered_hooks(settings) == {"hook_x.py": Registration("PreToolUse", 20)}

    settings.write_text(_settings({"PostToolUse": [{"command": _REGISTERED_X}]}), encoding="utf-8")
    assert registered_hooks(settings) == {"hook_x.py": Registration("PostToolUse", 60)}


def test_훅_하나가_이벤트_둘에_등록되면_거절한다(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    entry: dict[str, JsonValue] = {"command": _REGISTERED_X}
    settings.write_text(
        _settings({"PreToolUse": [entry], "PostToolUse": [entry]}), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="둘에 등록"):
        registered_hooks(settings)


def test_래퍼를_거치지_않거나_모양이_다른_등록은_거절한다(tmp_path: Path) -> None:
    """옛 모양은 훅 파일이 없으면 2로 끝나 PreToolUse 면 그 매처의 모든 호출을 막았다(대기열 91).

    `--project` 가 빠지면 저장소 밖에서 시스템 파이썬으로 돈다(KICKOFF.md 하네스 런타임).
    """
    settings = tmp_path / "settings.json"
    commands = [
        'uv run --project "${CLAUDE_PROJECT_DIR}" --no-sync python'
        ' "${CLAUDE_PROJECT_DIR}/tools/hook_x.py"',
        'uv run --no-sync python "${CLAUDE_PROJECT_DIR}/tools/launch_hook.py" hook_x.py',
        _REGISTERED_X.replace("hook_x.py", "tools/hook_x.py"),
        _REGISTERED_X + " --flag",
    ]
    for command in commands:
        settings.write_text(_settings({"PreToolUse": [{"command": command}]}), encoding="utf-8")

        with pytest.raises(ValueError, match="등록 모양"):
            registered_hooks(settings)


def test_러너가_띄우는_인자는_등록_명령에서_루트만_바꾼_것이다() -> None:
    root = Path("/r o/agent")

    assert launch_argv("hook_x.py", root) == [
        "uv",
        "run",
        "--project",
        "/r o/agent",
        "--no-sync",
        "python",
        "/r o/agent/tools/launch_hook.py",
        "hook_x.py",
    ]


def test_루트의_따옴표는_인자를_가르지_않고_경로에_남는다() -> None:
    """셸의 `"${CLAUDE_PROJECT_DIR}"` 전개는 경로 속 따옴표를 글자로 남긴다(PR #121 CodeRabbit)."""
    argv = launch_argv("hook_x.py", Path('/r"o/agent'))

    assert argv[3] == '/r"o/agent'
    assert argv[6] == '/r"o/agent/tools/launch_hook.py'
    assert len(argv) == 8


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


def test_러너도_등록처럼_래퍼로_띄워_없는_훅은_알림이다(tmp_path: Path) -> None:
    """훅을 바로 띄우면 파이썬이 2로 끝나 block 으로 읽힌다. 세션이 띄우는 모양과 같아야 한다."""
    replacements = create_fixtures(tmp_path)
    case = Case(
        hook="hook_없다.py",
        expect="context",
        payload={"hook_event_name": "PreToolUse", "tool_name": "Bash"},
    )

    result = run_case(case, replacements, Registration("PreToolUse", 20))

    assert result.outcome == "context"


def test_사용자에게만_가는_systemMessage_는_notice_다() -> None:
    """래퍼가 Stop 처럼 additionalContext 를 내지 않는 이벤트에서 지나갈 때의 출력이다(대기열
    93)."""
    assert outcome_of(0, json.dumps({"systemMessage": "x"}), "Stop") == "notice"
    both = json.dumps(
        {
            "systemMessage": "x",
            "hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": "x"},
        }
    )
    assert outcome_of(0, both, "PreToolUse") == "context"
    assert outcome_of(0, json.dumps({"systemMessage": ""}), "Stop") == "output"


def test_등록된_이벤트마다_래퍼가_없는_훅을_지나갈_때의_알림을_받아들이는_모양으로_낸다() -> None:
    """세션이 띄우는 모양(uv run 래퍼)과 등록된 이벤트 이름 그대로 잰다. 래퍼의 사본 테스트는 이벤트
    이름을 손으로 고른다."""
    registrations = registered_hooks()

    results = run_notices(registrations)

    assert {result.event for result in results} == {r.event for r in registrations.values()}
    assert [result for result in results if not result.ok] == []


def test_래퍼의_알림은_모델에게_닿는_이벤트에서_context_이고_Stop_계열에서_notice_다() -> None:
    """Stop·SubagentStop 의 additionalContext 는 대화를 잇는다. 나머지 이벤트에서 notice 만 나오면
    모델에게 가는 알림이 빠진 것이다 — 러너가 둘 다 받으면 그것을 0으로 지나간다(PR #122
    CodeRabbit)."""
    for event in ("PreToolUse", "PostToolUse", "UserPromptSubmit"):
        assert expected_notice(event) == "context"
        assert not NoticeResult(event, "notice", "").ok
    for event in ("Stop", "SubagentStop"):
        assert expected_notice(event) == "notice"
        assert not NoticeResult(event, "context", "").ok


def test_래퍼의_알림은_사용자에게_가는_systemMessage_가_없으면_context_여도_어긋남이다() -> None:
    """outcome_of 는 additionalContext 만 있어도 context 다. 표의 훅은 systemMessage 를 내지 않으니
    그 판정은 그대로 두고, 래퍼의 알림만 사용자 몫을 따로 본다(PR #122 CodeRabbit 2회차)."""
    specific = {"hookEventName": "PreToolUse", "additionalContext": "x"}
    model_only = json.dumps({"hookSpecificOutput": specific})
    both = json.dumps({"systemMessage": "x", "hookSpecificOutput": specific})

    assert notice_outcome(0, model_only, "PreToolUse") != "context"
    assert notice_outcome(0, both, "PreToolUse") == "context"
    assert notice_outcome(0, json.dumps({"systemMessage": "x"}), "Stop") == "notice"
    assert notice_outcome(2, "", "PreToolUse") == "block"


@pytest.mark.parametrize("outcome", ["silent", "block", "output", "event Stop", "timeout"])
def test_래퍼의_알림이_기대한_판정이_아니면_어긋남이다(outcome: str) -> None:
    assert not NoticeResult("PreToolUse", outcome, "").ok
    assert NoticeResult("PreToolUse", "context", "").ok
    assert NoticeResult("Stop", "notice", "").ok


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
