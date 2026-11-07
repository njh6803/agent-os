"""tools/hook_scratch_probe_reread.py 의 판정. 대화 기록은 임시 파일로 짓고, 래퍼를 거친 실제
실행은 tools/run_hooks.py 의 표가 본다.

기록 줄의 모양은 실제 Claude Code 기록 한 개에서 손으로 본 것이다(assistant 줄의
`message.content` 에 `tool_use` 블록이 있고 `input.file_path` 가 든다).
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path
from typing import TypedDict

import pytest
from tools.hook_scratch_probe_reread import (
    DENY_LIMIT,
    LEAD,
    HookPayload,
    count_history,
    is_probes_rule,
    is_scratch_script,
    main,
    reason_for,
)
from tools.run_hooks import registered_matchers

from tools import hook_scratch_probe_rule

SCRATCH = (
    "C:\\Users\\User\\AppData\\Local\\Temp\\claude\\C--project-agent"
    "\\627ad275-7ef2-4b63-96e0-b8dabac0ed18\\scratchpad"
)
PROBES_RULE = "C:\\project\\agent\\.claude\\rules\\probes.md"
ISSUE_TRACKER = "C:\\project\\agent\\docs\\agents\\issue-tracker.md"


def _line(name: str, file_path: str, tool_id: str, *, sidechain: bool = False) -> bytes:
    record = {
        "type": "assistant",
        "isSidechain": sidechain,
        "message": {
            "content": [
                {"type": "tool_use", "id": tool_id, "name": name, "input": {"file_path": file_path}}
            ]
        },
    }
    return json.dumps(record, ensure_ascii=False).encode("utf-8")


def _write_line(tool_id: str, *, name: str = "Write", sidechain: bool = False) -> bytes:
    return _line(name, SCRATCH + "\\" + tool_id + ".py", tool_id, sidechain=sidechain)


_TOOL_USE_ID = re.compile(rb'"id": "([^"]+)"')


def _result_line(tool_id: str, *, error: bool = False) -> bytes:
    """user 줄의 `tool_result` 블록. 키 순서는 실제 기록 한 개에서 본 대로다(type, tool_use_id,
    content)."""
    block: dict[str, object] = {"type": "tool_result", "tool_use_id": tool_id, "content": "ok"}
    if error:
        block["is_error"] = True
    record = {"type": "user", "message": {"role": "user", "content": [block]}}
    return json.dumps(record, ensure_ascii=False).encode("utf-8")


def _transcript(tmp_path: Path, *lines: bytes, pending: tuple[str, ...] = ()) -> str:
    """줄마다 그 줄의 `tool_use` 에 도구 결과 줄을 끝에 붙인다. `pending` 의 id 는 결과가 아직 없는
    호출(같은 메시지의 병렬 형제)이다."""
    results = [
        _result_line(found.decode("ascii"))
        for line in lines
        for found in _TOOL_USE_ID.findall(line)
        if found.decode("ascii") not in pending
    ]
    path = tmp_path / "session.jsonl"
    path.write_bytes(b"\n".join([*lines, *results]) + b"\n")
    return str(path)


def _payload(
    transcript: str | None,
    *,
    file_path: str = SCRATCH + "\\current.py",
    tool: str = "Write",
    tool_use_id: str | None = "toolu_current",
    agent_id: str = "",
) -> HookPayload:
    payload: HookPayload = {"tool_name": tool, "tool_input": {"file_path": file_path}}
    if transcript is not None:
        payload["transcript_path"] = transcript
    if tool_use_id is not None:
        payload["tool_use_id"] = tool_use_id
    if agent_id:
        payload["agent_id"] = agent_id
    return payload


def test_첫_시도는_지나간다(tmp_path: Path) -> None:
    transcript = _transcript(tmp_path, _line("Read", ISSUE_TRACKER, "toolu_r"))
    assert reason_for(_payload(transcript)) is None


def test_스크래치_스크립트를_이미_쓴_세션이_probes_md_를_열지_않았으면_거부한다(
    tmp_path: Path,
) -> None:
    transcript = _transcript(tmp_path, _write_line("toolu_a"))
    reason = reason_for(_payload(transcript))
    assert reason is not None
    assert reason.startswith(LEAD)
    assert ".claude/rules/probes.md" in reason


def test_거부는_두_번까지고_그_뒤_시도는_지나간다(tmp_path: Path) -> None:
    assert DENY_LIMIT == 2
    # 거부된 시도도 기록에 tool_use 로 남고 뒤에 도구 결과가 붙어 앞선 시도의 수를 키운다(기록
    # 한 개에서 손으로 본 것이고 독스트링에 적었다).
    for earlier, denied in ((1, True), (2, True), (3, False), (4, False)):
        lines = [_write_line(f"toolu_{index}") for index in range(earlier)]
        reason = reason_for(_payload(_transcript(tmp_path, *lines)))
        assert (reason is not None) is denied, earlier


def test_같은_메시지의_병렬_형제는_서로를_앞선_시도로_세지_않는다(tmp_path: Path) -> None:
    # 도구 결과가 아직 없는 호출은 센 수에 들지 않아, 첫 배치의 호출은 모두 지나간다.
    siblings = (_write_line("toolu_a"), _write_line("toolu_b"), _write_line("toolu_c"))
    transcript = _transcript(tmp_path, *siblings, pending=("toolu_a", "toolu_b", "toolu_c"))
    assert reason_for(_payload(transcript)) is None


def test_병렬_형제가_있어도_결과가_온_앞선_시도는_센다(tmp_path: Path) -> None:
    transcript = _transcript(
        tmp_path,
        _write_line("toolu_done"),
        _write_line("toolu_b"),
        _write_line("toolu_c"),
        pending=("toolu_b", "toolu_c"),
    )
    assert reason_for(_payload(transcript)) is not None


def test_실패한_시도도_도구_결과가_있으면_센다(tmp_path: Path) -> None:
    failed = _write_line("toolu_a", name="Edit")
    path = tmp_path / "session.jsonl"
    path.write_bytes(b"\n".join([failed, _result_line("toolu_a", error=True)]) + b"\n")
    assert reason_for(_payload(str(path))) is not None


@pytest.mark.parametrize(
    "rule_path",
    [
        PROBES_RULE,
        "C:/project/agent/.claude/rules/probes.md",
        "C:\\project\\agent\\.claude\\worktrees\\side\\.claude\\rules\\probes.md",
        "C:\\PROJECT\\AGENT\\.Claude\\Rules\\Probes.MD",
    ],
)
def test_probes_md_를_Read_로_열었으면_지나간다(tmp_path: Path, rule_path: str) -> None:
    transcript = _transcript(tmp_path, _write_line("toolu_a"), _line("Read", rule_path, "toolu_r"))
    assert reason_for(_payload(transcript)) is None


def test_probes_md_가_아닌_파일을_연_것은_읽음이_아니다(tmp_path: Path) -> None:
    # 대기열 426 의 사건: 알림을 받은 세션이 probes.md 대신 issue-tracker.md 를 열었다.
    transcript = _transcript(
        tmp_path, _write_line("toolu_a"), _line("Read", ISSUE_TRACKER, "toolu_r")
    )
    assert reason_for(_payload(transcript)) is not None
    other = "C:\\project\\agent\\.claude\\rules\\tools.md"
    assert (
        reason_for(
            _payload(_transcript(tmp_path, _write_line("toolu_a"), _line("Read", other, "r")))
        )
        is not None
    )
    lookalike = "C:\\project\\agent\\.claude\\rules\\old-probes.md"
    transcript = _transcript(tmp_path, _write_line("toolu_a"), _line("Read", lookalike, "toolu_r"))
    assert reason_for(_payload(transcript)) is not None


def test_Read_가_아닌_도구가_probes_md_를_가리킨_것은_읽음이_아니다(tmp_path: Path) -> None:
    edit = _line("Edit", PROBES_RULE, "toolu_e")
    grep_text = json.dumps(
        {
            "type": "user",
            "message": {"content": [{"type": "tool_result", "content": "rules/probes.md 를 열라"}]},
        }
    ).encode("utf-8")
    transcript = _transcript(tmp_path, _write_line("toolu_a"), edit, grep_text)
    assert reason_for(_payload(transcript)) is not None


def test_이_호출의_기록은_앞선_시도로_세지_않는다(tmp_path: Path) -> None:
    # PreToolUse 시점에 자기 기록이 이미 있을 수 있다.
    transcript = _transcript(tmp_path, _write_line("toolu_current"))
    assert reason_for(_payload(transcript)) is None


def test_서브에이전트_쪽_기록은_세지_않는다(tmp_path: Path) -> None:
    transcript = _transcript(tmp_path, _write_line("toolu_side", sidechain=True))
    assert reason_for(_payload(transcript)) is None
    # 서브에이전트가 연 probes.md 도 이 세션의 읽음이 아니다.
    side_read = _line("Read", PROBES_RULE, "toolu_side_read", sidechain=True)
    transcript = _transcript(tmp_path, _write_line("toolu_a"), side_read)
    assert reason_for(_payload(transcript)) is not None


def test_스크래치패드가_아닌_쓰기는_앞선_시도로_세지_않는다(tmp_path: Path) -> None:
    repo_write = _line("Write", "C:\\project\\agent\\tools\\x.py", "toolu_repo")
    note = _line("Write", SCRATCH + "\\notes.md", "toolu_note")
    assert reason_for(_payload(_transcript(tmp_path, repo_write, note))) is None


def test_Edit_도_앞선_시도로_센다(tmp_path: Path) -> None:
    transcript = _transcript(tmp_path, _write_line("toolu_a", name="Edit"))
    assert reason_for(_payload(transcript, tool="Edit")) is not None


def test_깨진_줄은_건너뛴다(tmp_path: Path) -> None:
    transcript = _transcript(tmp_path, b'{"scratchpad": ', b"[1, 2]", _write_line("toolu_a"))
    assert reason_for(_payload(transcript)) is not None


def test_같은_호출이_두_줄에_나뉘어_기록돼도_한_번으로_센다(tmp_path: Path) -> None:
    line = _write_line("toolu_a")
    assert (
        reason_for(_payload(_transcript(tmp_path, line, line, _write_line("toolu_b")))) is not None
    )
    assert count_history([line, line, _result_line("toolu_a")], own_id="x").earlier == 1


def test_스크래치패드가_아닌_경로와_다른_도구는_지나간다(tmp_path: Path) -> None:
    transcript = _transcript(tmp_path, _write_line("toolu_a"))
    assert reason_for(_payload(transcript, file_path="C:\\project\\agent\\tools\\x.py")) is None
    assert reason_for(_payload(transcript, file_path=SCRATCH + "\\notes.md")) is None
    assert reason_for(_payload(transcript, tool="Read")) is None
    assert reason_for(_payload(transcript, tool="Bash")) is None


@pytest.mark.parametrize("tool_input", ["x", {"file_path": 1}, {"file_path": None}, {}])
def test_꼴이_어긋난_입력은_예외_없이_지나간다(tmp_path: Path, tool_input: object) -> None:
    transcript = _transcript(tmp_path, _write_line("toolu_a"))
    payload = json.loads(
        json.dumps(
            {
                "tool_name": "Write",
                "tool_input": tool_input,
                "transcript_path": transcript,
                "tool_use_id": "toolu_current",
            }
        )
    )
    assert reason_for(payload) is None


def test_못_보는_것_서브에이전트의_호출은_막지_않는다(tmp_path: Path) -> None:
    transcript = _transcript(tmp_path, _write_line("toolu_a"))
    assert reason_for(_payload(transcript, agent_id="agent-a")) is None


def test_못_보는_것_기록을_알_수_없으면_막지_않는다(tmp_path: Path) -> None:
    transcript = _transcript(tmp_path, _write_line("toolu_a"))
    assert reason_for(_payload(None)) is None
    assert reason_for(_payload(str(tmp_path / "없는-기록.jsonl"))) is None
    assert reason_for(_payload(str(tmp_path))) is None
    # 자기 기록을 가를 수 없으면 첫 시도를 막을 수 있어 막지 않는다.
    assert reason_for(_payload(transcript, tool_use_id=None)) is None


def test_못_보는_것_Bash_로_쓴_스크래치_스크립트는_센_수에_들지_않는다(tmp_path: Path) -> None:
    heredoc = json.dumps(
        {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_b",
                        "name": "Bash",
                        "input": {"command": f"cat > '{SCRATCH}\\m.py' <<'EOF'\nprint(1)\nEOF"},
                    }
                ]
            },
        }
    ).encode("utf-8")
    assert reason_for(_payload(_transcript(tmp_path, heredoc))) is None


def test_못_보는_것_측정이_아닌_도우미_스크립트도_둘째_시도부터_막는다(tmp_path: Path) -> None:
    # 훅은 측정인지 가르지 못한다. 이유가 측정이 아니면 같은 호출을 다시 부르라고 적는다.
    helper = _line("Write", SCRATCH + "\\list_files.py", "toolu_h")
    reason = reason_for(_payload(_transcript(tmp_path, helper), file_path=SCRATCH + "\\next.py"))
    assert reason is not None
    assert "측정이 아니면 같은 호출을 다시 부른다" in reason


def test_못_보는_것_스크래치패드의_설계_문서는_센_수에_들지_않는다(tmp_path: Path) -> None:
    # 사전 등록 문서는 이 훅이 보지 않는다. 막는 것은 둘째 스크립트부터다.
    design = _line("Write", SCRATCH + "\\design.md", "toolu_d")
    assert reason_for(_payload(_transcript(tmp_path, design))) is None


def test_거부_이유는_읽지_않고_다시_부르면_한_번_더_막힌다고_알린다(tmp_path: Path) -> None:
    reason = reason_for(_payload(_transcript(tmp_path, _write_line("toolu_a"))))
    assert reason is not None
    assert "읽지 않고 다시 부르면 이 훅이 한 번 더 막고" in reason
    assert "세션마다 두 번까지만 막은 뒤 지나간다" in reason


def test_못_보는_것_저장소_프로브를_열어_자동으로_실린_규칙은_읽음이_아니다(tmp_path: Path) -> None:
    probe_read = _line("Read", "C:\\project\\agent\\.scratch\\harness\\probes\\x.py", "toolu_p")
    assert (
        reason_for(_payload(_transcript(tmp_path, _write_line("toolu_a"), probe_read))) is not None
    )


def test_못_보는_것_읽음이_기록에_아직_없으면_거부한다(tmp_path: Path) -> None:
    # 같은 메시지의 병렬 호출에서 Read 가 Write 보다 늦게 기록되면 읽은 세션도 한 번 막힌다.
    # 기록에 읽음 줄이 없는 입력은 읽지 않은 세션과 같아 구분되지 않는다(재지 않았다).
    transcript = _transcript(tmp_path, _write_line("toolu_a"))
    assert reason_for(_payload(transcript)) is not None


def test_못_보는_것_압축_뒤에도_읽음은_기록에_남아_거부하지_않는다(tmp_path: Path) -> None:
    lines = [
        _write_line("toolu_a"),
        _line("Read", PROBES_RULE, "toolu_r"),
        _write_line("toolu_b"),
        _write_line("toolu_c"),
    ]
    assert reason_for(_payload(_transcript(tmp_path, *lines))) is None


def test_못_보는_것_상한을_넘게_쌓인_기록은_읽지_않았어도_지나간다(tmp_path: Path) -> None:
    # 긴 세션이나 앞 세션의 기록을 이은 재개. 거부는 첫 알림 직후의 두 번뿐이다.
    lines = [_write_line(f"toolu_{index}") for index in range(DENY_LIMIT + 1)]
    assert reason_for(_payload(_transcript(tmp_path, *lines))) is None


def test_못_보는_것_결과_줄의_모양이_바뀌면_조용히_지나간다(tmp_path: Path) -> None:
    # 센 수가 0 이 된다.
    block = {"type": "tool_result", "toolUseId": "toolu_a", "content": "ok"}
    changed = json.dumps({"type": "user", "message": {"content": [block]}}).encode("utf-8")
    path = tmp_path / "session.jsonl"
    path.write_bytes(b"\n".join([_write_line("toolu_a"), changed]) + b"\n")
    assert reason_for(_payload(str(path))) is None


def test_스크래치_스크립트_판정은_알림_훅과_같다() -> None:
    # 훅끼리 import 하지 않으므로 복사본이다. 두 사본이 어긋나면 이 시험이 빨개진다.
    paths = (
        SCRATCH + "\\measure.py",
        SCRATCH.replace("\\claude\\", "\\Claude\\") + "\\m.sh",
        SCRATCH + "\\notes.md",
        SCRATCH + "\\sub\\deep.ts",
        "C:\\Temp\\claude\\scratchpad\\m.py",
        "C:\\project\\agent\\.scratch\\harness\\probes\\x.py",
        "",
    )
    for path in paths:
        assert is_scratch_script(path) == hook_scratch_probe_rule.is_scratch_script(path), path
    assert is_scratch_script(paths[0])
    assert not is_scratch_script(paths[2])


def test_probes_md_판정은_규칙_파일_이름으로_끝날_때만_참이다() -> None:
    assert is_probes_rule(PROBES_RULE)
    assert not is_probes_rule("C:\\project\\agent\\docs\\probes.md")
    assert not is_probes_rule("probes.md")
    assert not is_probes_rule("")


class _Specific(TypedDict):
    hookEventName: str
    permissionDecision: str
    permissionDecisionReason: str


class _Output(TypedDict):
    hookSpecificOutput: _Specific


def _run_main(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], payload: HookPayload
) -> _Output | None:
    stdin = io.TextIOWrapper(io.BytesIO(json.dumps(payload).encode("utf-8")), encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", stdin)
    assert main() == 0
    out = capsys.readouterr().out
    if not out:
        return None
    result: _Output = json.loads(out)
    return result


def test_main_은_거부를_PreToolUse_형식으로_낸다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    transcript = _transcript(tmp_path, _write_line("toolu_a"))
    output = _run_main(monkeypatch, capsys, _payload(transcript))
    assert output is not None
    specific = output["hookSpecificOutput"]
    assert specific["hookEventName"] == "PreToolUse"
    assert specific["permissionDecision"] == "deny"
    assert specific["permissionDecisionReason"].startswith(LEAD)


def test_main_은_지나가는_호출에_아무것도_내지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        _run_main(
            monkeypatch, capsys, _payload(_transcript(tmp_path, _line("Read", ISSUE_TRACKER, "r")))
        )
        is None
    )


def test_등록의_매처가_훅이_아는_도구와_같다() -> None:
    assert registered_matchers("hook_scratch_probe_reread.py", "PreToolUse") == ["Write|Edit"]
