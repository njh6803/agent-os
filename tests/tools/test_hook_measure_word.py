"""tools/hook_measure_word.py 의 판정. 래퍼를 거친 실제 실행은 tools/run_hooks.py 의 표가 본다."""

from __future__ import annotations

import io
import json
import sys

import pytest
from tools.hook_measure_word import (
    LEAD,
    TOOLS,
    HookPayload,
    added_lines,
    context_for,
    flagged_lines,
    is_evidence_doc,
    main,
)
from tools.run_hooks import registered_matchers

ROOT = "C:\\project\\agent\\.claude\\worktrees\\measure-word-hook"
ADR = ROOT + "\\docs\\adr\\0035-precommit-pytest-is-split-by-xdist-in-the-runner.md"
QUEUE = ROOT + "\\.scratch\\retro-queue.md"
PROBE_README = ROOT + "\\.scratch\\harness\\probes\\README.md"


def _edit(file_path: str, old: str, new: str) -> HookPayload:
    return {
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "old_string": old, "new_string": new},
    }


def _edit_file(original: str, old: str, new: str, *, replace_all: bool = False) -> HookPayload:
    """결과에 고치기 전 파일(`originalFile`)이 실린 실제 Edit 의 꼴."""
    return {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": ADR,
            "old_string": old,
            "new_string": new,
            "replace_all": replace_all,
        },
        "tool_response": {"originalFile": original},
    }


def test_Edit_조각이_줄의_일부여도_그_줄의_probes_경로를_본다() -> None:
    original = "- 한 바퀴가 4초를 쟀다(`.scratch/a/probes/p.py`)\n"
    assert context_for(_edit_file(original, "4초를 쟀다", "5초를 쟀다")) is None
    bare = "- 한 바퀴가 4초였다\n"
    context = context_for(_edit_file(bare, "4초였다", "4초를 쟀다"))
    assert context is not None
    assert "- 한 바퀴가 4초를 쟀다" in context


def test_Edit_의_replace_all_은_모든_자리를_바꾼다() -> None:
    original = "가 4초\n나(`probes/p.py`)\n가 4초\n"
    once = context_for(_edit_file(original, "가 4초", "가 실측 4초"))
    every = context_for(_edit_file(original, "가 4초", "가 실측 4초", replace_all=True))
    assert once is not None
    assert every is not None
    assert "걸린 줄(1개)" in once
    assert "걸린 줄(2개)" in every


def test_originalFile_에_조각이_없으면_조각만_본다() -> None:
    assert context_for(_edit_file("다른 글\n", "4초", "실측 4초")) is not None
    assert context_for(_edit_file("다른 글\n", "4초", "4초")) is None


def test_ADR_에_근거_없는_실측을_더하면_알린다() -> None:
    context = context_for(_edit(ADR, "- 이력\n", "- 이력\n- 한 프로세스가 4초였다(실측)\n"))
    assert context is not None
    assert context.startswith(LEAD)
    assert "docs/agents/issue-tracker.md" in context
    assert "한 프로세스가 4초였다(실측)" in context


def test_세_자리와_세_낱말을_모두_본다() -> None:
    for path in (ADR, QUEUE, PROBE_README, ROOT + "\\.scratch\\x\\probes\\README.md"):
        for word in ("쟀다", "재니", "실측"):
            assert context_for(_edit(path, "", f"시간을 {word}\n")) is not None, (path, word)


def test_슬래시_꼴과_대소문자가_다른_경로도_본다() -> None:
    assert is_evidence_doc(ADR.replace("\\", "/"))
    assert is_evidence_doc(QUEUE.replace("\\scratch\\", "\\Scratch\\"))
    assert is_evidence_doc(PROBE_README.replace("README.md", "readme.md"))


def test_같은_줄에_probes_경로나_손으로가_있으면_지나간다() -> None:
    lines = (
        "4초였다(실측, `.scratch/harness/probes/x.py`)\n",
        "4초였다(손으로 쟀다)\n",
    )
    for line in lines:
        assert context_for(_edit(ADR, "", line)) is None, line


def test_원래_있던_줄은_보지_않는다() -> None:
    old = "옛 줄은 실측이라 적었다\n"
    assert context_for(_edit(ADR, old, old + "새 줄은 낱말이 없다\n")) is None


def test_다른_파일은_지나간다() -> None:
    for path in (
        ROOT + "\\docs\\journal\\2026-10-19-02-x.md",
        ROOT + "\\docs\\PRD.md",
        ROOT + "\\.scratch\\harness\\probes\\run.py",
        ROOT + "\\.scratch\\plan.md",
        ROOT + "\\tools\\adr\\x.md",
        ROOT + "\\docs\\retro-queue.md",
        ROOT + "\\web\\probes\\README.md",
    ):
        assert context_for(_edit(path, "", "실측\n")) is None, path


def test_Write_는_원래_파일에_없던_줄만_본다() -> None:
    old = "# 0035\n옛 실측\n"
    payload: HookPayload = {
        "tool_name": "Write",
        "tool_input": {"file_path": ADR, "content": old + "새로 쟀다\n"},
        "tool_response": {"type": "update", "originalFile": old},
    }
    context = context_for(payload)
    assert context is not None
    assert "새로 쟀다" in context
    assert "옛 실측" not in context


def test_새_파일의_Write_는_모든_줄을_본다() -> None:
    payload: HookPayload = {
        "tool_name": "Write",
        "tool_input": {"file_path": ADR, "content": "# 0099\n\n재니 3초였다\n"},
    }
    assert context_for(payload) is not None
    # 실제 새 파일의 결과는 originalFile 이 null 이다(프로브 README 의 journal_number_hook/ 행).
    created = json.loads(json.dumps({**payload, "tool_response": {"originalFile": None}}))
    assert context_for(created) is not None


def test_더한_줄은_원래_글에_없던_줄이다() -> None:
    assert added_lines("a\nb\n", "a\nc\nb\n") == ["c"]
    assert added_lines("", "x\n\ny") == ["x", "y"]


def test_걸린_줄은_셋까지_잘라_보인다() -> None:
    lines = [f"{index} 실측 " + "가" * 300 for index in range(5)]
    flagged = flagged_lines(lines)
    assert len(flagged) == 5
    context = context_for(_edit(ADR, "", "\n".join(lines)))
    assert context is not None
    assert "0 실측" in context
    assert "3 실측" not in context
    assert "가" * 200 not in context


def test_다른_도구와_꼴이_어긋난_입력은_지나가고_객체가_아닌_결과는_없는_것으로_본다() -> None:
    read = json.loads(json.dumps({"tool_name": "Read", "tool_input": {"file_path": ADR}}))
    assert context_for(read) is None
    for tool_input in ("x", {"file_path": 1}, {"file_path": ADR, "new_string": 1}, {}):
        payload = json.loads(json.dumps({"tool_name": "Edit", "tool_input": tool_input}))
        assert context_for(payload) is None, tool_input
    write = {"tool_name": "Write", "tool_input": {"file_path": ADR, "content": "실측\n"}}
    write["tool_response"] = "x"
    assert context_for(json.loads(json.dumps(write))) is not None


def test_못_보는_것_다른_꼴의_측정_낱말은_지나간다() -> None:
    for line in ("3초를 잰 값이다\n", "재 보니 3초였다\n", "측정했다\n"):
        assert context_for(_edit(ADR, "", line)) is None, line


def test_못_보는_것_낱말을_인용만_한_줄에도_알린다() -> None:
    # 대기열 행이 낱말을 이름으로 들기만 해도 근거 문장과 가르지 못한다.
    assert context_for(_edit(QUEUE, "", "| 9 | `쟀다`·`실측`을 든 줄 | tools/ | 자체 승인 |\n"))


def test_못_보는_것_옛_줄을_고쳐_쓰면_더한_줄이다() -> None:
    # 줄 하나의 다른 자리만 고쳐도 그 줄 전체가 새 줄이라, 옛 낱말이 다시 걸린다.
    old = "| 1 | 4초 실측 | x | 승인 |\n"
    assert context_for(_edit(QUEUE, old, old.replace("| 1 |", "| ~~1~~ |"))) is not None
    context = context_for(_edit_file(old, "| 1 |", "| ~~1~~ |"))
    assert context is not None
    assert "취소선" in context  # 알림이 이 경우는 무시하라고 적는다
    # originalFile 이 없는 Edit 은 조각만 보므로 거꾸로 지나간다.
    assert context_for(_edit(QUEUE, "| 1 |", "| ~~1~~ |")) is None


def test_못_보는_것_근거가_같은_줄_밖이면_알린다() -> None:
    wrapped = "  4초를 쟀다\n  (`.scratch/a/probes/p.py`).\n"
    row = "| `p.py` | 4초를 쟀다 | 근거 | 돌리는 법 |\n"
    assert context_for(_edit(ADR, "", wrapped)) is not None
    context = context_for(_edit(PROBE_README, "", row))
    assert context is not None
    assert "프로브 README" in context  # 알림이 이 경우도 무시하라고 적는다


def test_못_보는_것_표지는_글자만_본다() -> None:
    for line in ("실측했다(`web/probes/없는.py`)\n", "손으로 보지 않고 실측했다\n"):
        assert context_for(_edit(ADR, "", line)) is None, line


def test_못_보는_것_경로를_정규화하지_않는다() -> None:
    assert not is_evidence_doc("docs/./adr/y.md")
    assert is_evidence_doc("C:/docs/adr/proj/src/a.py")


def test_못_보는_것_Bash_로_쓴_파일은_지나간다() -> None:
    command = f"cat >> '{ADR}' <<'EOF'\n실측\nEOF"
    payload = json.loads(json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}))
    assert context_for(payload) is None


def _run_main(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], payload: HookPayload
) -> str:
    stdin = io.TextIOWrapper(io.BytesIO(json.dumps(payload).encode("utf-8")), encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", stdin)
    assert main() == 0
    out = capsys.readouterr().out
    if not out:
        return ""
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert isinstance(context, str)
    return context


def test_main_은_걸릴_때마다_알린다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    payload = _edit(ADR, "", "실측\n")
    assert LEAD in _run_main(monkeypatch, capsys, payload)
    assert LEAD in _run_main(monkeypatch, capsys, payload)
    assert _run_main(monkeypatch, capsys, _edit(ADR, "", "낱말 없음\n")) == ""


def test_등록의_매처가_훅이_아는_도구와_같다() -> None:
    assert registered_matchers("hook_measure_word.py", "PostToolUse") == ["|".join(TOOLS)]
