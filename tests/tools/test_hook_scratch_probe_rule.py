"""tools/hook_scratch_probe_rule.py 의 판정과 표지. main 은 stdin 과 임시 폴더를 바꿔 끼워 표지
길을 보고, 래퍼를 거친 실제 실행은 tools/run_hooks.py 의 표가 본다.

경로는 이 훅을 만든 세션(2026-10-17, 데스크톱 앱)의 스크래치패드 꼴이다.
"""

from __future__ import annotations

import io
import json
import sys
import tempfile
from pathlib import Path

import pytest
from tools.hook_scratch_probe_rule import (
    LEAD,
    TOOLS,
    HookPayload,
    claim_first,
    context_for,
    is_scratch_script,
    main,
    marker_name,
)
from tools.run_hooks import registered_matchers

SCRATCH = (
    "C:\\Users\\User\\AppData\\Local\\Temp\\claude\\C--project-agent"
    "\\627ad275-7ef2-4b63-96e0-b8dabac0ed18\\scratchpad"
)


def _write(file_path: str) -> HookPayload:
    return {"tool_name": "Write", "tool_input": {"file_path": file_path}}


def test_스크래치패드의_파이썬_스크립트를_쓰면_알린다() -> None:
    context = context_for(_write(SCRATCH + "\\measure.py"))
    assert context is not None
    assert context.startswith(LEAD)
    assert ".claude/rules/probes.md" in context


def test_하위_폴더와_슬래시_꼴과_다른_실행_확장자도_알린다() -> None:
    assert is_scratch_script(SCRATCH + "\\probe\\run.sh")
    assert is_scratch_script(SCRATCH.replace("\\", "/") + "/probe/hash_match.mjs")
    for suffix in (".py", ".sh", ".bash", ".ps1", ".js", ".mjs", ".cjs", ".ts"):
        assert is_scratch_script(SCRATCH + "\\x" + suffix), suffix


def test_대소문자가_다른_폴더_이름도_스크래치패드다() -> None:
    assert is_scratch_script(SCRATCH.replace("\\claude\\", "\\Claude\\") + "\\m.py")


def test_Edit_도_알린다() -> None:
    payload: HookPayload = {"tool_name": "Edit", "tool_input": {"file_path": SCRATCH + "\\m.py"}}
    assert context_for(payload) is not None


def test_실행_스크립트가_아닌_스크래치_파일은_지나간다() -> None:
    for name in ("notes.md", "result.json", "brief.txt", "data.toml", "Makefile"):
        assert not is_scratch_script(SCRATCH + "\\" + name), name


def test_저장소_안의_프로브는_지나간다() -> None:
    # 저장소의 `.scratch/**/probes/**` 는 rules 의 paths 가 이미 싣는다.
    assert not is_scratch_script("C:\\project\\agent\\.scratch\\harness\\probes\\x\\run.py")


def test_scratchpad_이름만_같은_다른_폴더는_지나간다() -> None:
    # `claude` 다음 두 토막(프로젝트, 세션) 뒤의 scratchpad 만 세션 스크래치패드다.
    assert not is_scratch_script("C:\\work\\scratchpad\\m.py")
    assert not is_scratch_script("C:\\Temp\\claude\\scratchpad\\m.py")
    assert not is_scratch_script("C:\\Temp\\claude\\a\\b\\c\\scratchpad\\m.py")
    assert not is_scratch_script("C:\\Temp\\claudeX\\a\\b\\scratchpad\\m.py")


def test_다른_도구와_경로_없는_입력은_지나간다() -> None:
    read: HookPayload = {"tool_name": "Read", "tool_input": {"file_path": SCRATCH + "\\m.py"}}
    assert context_for(read) is None
    assert context_for({"tool_name": "Write", "tool_input": {}}) is None
    assert context_for({"tool_name": "Write"}) is None


def test_못_보는_것_Bash_heredoc_으로_쓴_스크래치_파일은_지나간다() -> None:
    # Bash 의 실제 입력은 명령 칸뿐이다. 이 훅의 등록 매처에도 Bash 가 없다. HookPayload 에 없는
    # 칸(command)을 실으려고 main 처럼 JSON 에서 풀어 넘긴다.
    command = f"cat > '{SCRATCH}\\m.py' <<'EOF'\nprint(1)\nEOF"
    heredoc = {"tool_name": "Bash", "tool_input": {"command": command}}
    assert context_for(json.loads(json.dumps(heredoc))) is None


def test_못_보는_것_데스크톱_앱_밖의_스크래치패드_꼴은_지나간다() -> None:
    # 리눅스 CLI 의 꼴로 짐작한 경로다. 실제 자리는 보지 않았다.
    assert not is_scratch_script("/tmp/claude-1000/-home-u-agent/abc/scratchpad/m.py")


def test_못_보는_것_서브에이전트에도_같은_문장을_낸다() -> None:
    payload = _write(SCRATCH + "\\m.py")
    payload["agent_id"] = "agent-a"
    assert context_for(payload) == context_for(_write(SCRATCH + "\\m.py"))


def test_표지는_세션과_에이전트마다_한_번이다(tmp_path: Path) -> None:
    main_key = marker_name("s1", "")
    assert claim_first(main_key, tmp_path)
    assert not claim_first(main_key, tmp_path)
    assert claim_first(marker_name("s1", "agent-a"), tmp_path)
    assert claim_first(marker_name("s2", ""), tmp_path)


def test_표지를_쓰지_못하면_알린다(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("", encoding="utf-8")
    # 디렉터리 자리에 파일이 있어 표지 폴더를 만들지 못한다.
    assert claim_first(marker_name("s1", ""), blocker / "state")
    # 표지 폴더 자리 자체가 파일이면 makedirs 가 FileExistsError 를 낸다. 이미 알린 것으로 읽지
    # 않는다.
    assert claim_first(marker_name("s1", ""), blocker)


def _run_main(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], payload: HookPayload
) -> str:
    """main 을 한 번 돌려 알린 문장을, 알리지 않았으면 빈 문자열을 돌려준다."""
    stdin = io.TextIOWrapper(io.BytesIO(json.dumps(payload).encode("utf-8")), encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", stdin)
    assert main() == 0
    out = capsys.readouterr().out
    if not out:
        return ""
    context = json.loads(out)["hookSpecificOutput"]["additionalContext"]
    assert isinstance(context, str)
    return context


def _session_write(file_path: str, agent_id: str = "") -> HookPayload:
    payload = _write(file_path)
    payload["session_id"] = "session-1"
    if agent_id:
        payload["agent_id"] = agent_id
    return payload


def test_main_은_세션과_에이전트마다_한_번_알린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    assert LEAD in _run_main(monkeypatch, capsys, _session_write(SCRATCH + "\\a.py"))
    assert _run_main(monkeypatch, capsys, _session_write(SCRATCH + "\\a.py")) == ""
    assert LEAD in _run_main(monkeypatch, capsys, _session_write(SCRATCH + "\\a.py", "agent-a"))


def test_못_보는_것_한_번_알린_뒤의_측정_스크립트는_지나간다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # 측정이 아닌 도우미를 먼저 써서 알림을 넘기면, 같은 세션의 뒤 측정 스크립트는 알림을 받지
    # 못한다.
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    assert LEAD in _run_main(monkeypatch, capsys, _session_write(SCRATCH + "\\helper.py"))
    assert _run_main(monkeypatch, capsys, _session_write(SCRATCH + "\\measure.py")) == ""


def test_main_은_임시_폴더가_없으면_호출마다_알린다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def no_temp() -> str:
        raise FileNotFoundError("쓸 수 있는 임시 폴더가 없다")

    monkeypatch.setattr(tempfile, "gettempdir", no_temp)
    assert LEAD in _run_main(monkeypatch, capsys, _session_write(SCRATCH + "\\a.py"))
    assert LEAD in _run_main(monkeypatch, capsys, _session_write(SCRATCH + "\\a.py"))


def test_등록의_매처가_훅이_아는_도구와_같다() -> None:
    assert registered_matchers("hook_scratch_probe_rule.py", "PostToolUse") == ["|".join(TOOLS)]
