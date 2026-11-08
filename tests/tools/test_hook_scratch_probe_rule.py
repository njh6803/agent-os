"""tools/hook_scratch_probe_rule.py 의 판정과 표지. main 은 stdin 과 임시 폴더를 바꿔 끼워 표지
길을 보고, 래퍼를 거친 실제 실행은 tools/run_hooks.py 의 표가 본다.

경로는 이 훅을 만든 세션(2026-10-17, 데스크톱 앱)의 스크래치패드 꼴이다.
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
from tools.hook_scratch_probe_rule import (
    LEAD,
    ROUNDS_LEAD,
    TOOLS,
    HookPayload,
    claim_first,
    context_for,
    is_repo_probe,
    is_scratch_script,
    main,
    marker_name,
    rounds_context_for,
)
from tools.probe_kit import Rounds, Slot
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


@pytest.mark.parametrize("tool_input", ["x", {"file_path": 1}, {"file_path": None}])
def test_꼴이_어긋난_입력은_예외_없이_지나간다(tool_input: object) -> None:
    # HookPayload 에 맞지 않는 꼴이라 main 처럼 JSON 에서 풀어 넘긴다.
    payload = json.loads(json.dumps({"tool_name": "Write", "tool_input": tool_input}))
    assert context_for(payload) is None


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


def test_표지_파일을_만들지_못하면_알린다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def denied(*_args: object) -> int:
        raise PermissionError

    monkeypatch.setattr(os, "open", denied)
    assert claim_first(marker_name("s1", ""), tmp_path)
    assert claim_first(marker_name("s1", ""), tmp_path)


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


def test_표지_이름은_이유마다_갈린다() -> None:
    assert marker_name("s1", "") == marker_name("s1", "", "")
    assert marker_name("s1", "", "rounds") != marker_name("s1", "")
    assert marker_name("s1", "agent-a", "rounds") != marker_name("s1", "", "rounds")


# --- 저장소 프로브의 Rounds (대기열 430) ---


def _probe_path(tmp_path: Path, name: str = "measure.py", folder: str = "harness") -> Path:
    return tmp_path / ".scratch" / folder / "probes" / name


def _repo_write(path: Path, content: str) -> HookPayload:
    return {"tool_name": "Write", "tool_input": {"file_path": str(path), "content": content}}


WITH_ROUNDS = "from tools.probe_kit import Rounds\nrounds = Rounds()\n"


def test_Rounds_가_없는_저장소_프로브를_쓰면_알린다(tmp_path: Path) -> None:
    context = rounds_context_for(_repo_write(_probe_path(tmp_path), "print(1)\n"))
    assert context is not None
    assert context.startswith(ROUNDS_LEAD)
    assert ".claude/rules/probes.md" in context
    assert "tools/probe_kit.py" in context
    assert "Rounds" in context


def test_알림이_가리키는_이름이_probe_kit_에_있다() -> None:
    context = rounds_context_for(_repo_write(Path(".scratch/x/probes/m.py"), "print(1)\n"))
    assert context is not None
    for name in ("round", "mark", "exit_code"):
        assert f"`{name}`" in context, name
    assert hasattr(Rounds, "round")
    assert hasattr(Rounds, "exit_code")
    assert hasattr(Slot, "mark")


def test_알림이_가리키는_첫_항목_문장이_규칙_파일에_있다() -> None:
    rule = Path(__file__).resolve().parents[2] / ".claude" / "rules" / "probes.md"
    items = [
        line for line in rule.read_text(encoding="utf-8").splitlines() if line.startswith("- ")
    ]
    assert items, "규칙 파일에서 첫 항목을 찾지 못했다"
    first = items[0]
    for sentence in (
        "재려는 상황이 그 회차에 실제로 났다는 표지",
        "표지가 없는 회차",
        "종료 코드를 0으로 두지 않는다",
        "`Rounds`",
        "`round`",
        "`mark`",
        "`exit_code`",
    ):
        assert sentence in first, sentence


def test_못_보는_것_측정이_아닌_저장소_프로브에도_알린다(tmp_path: Path) -> None:
    # 변이 표를 읽는 도우미도 Rounds 가 없으면 알린다. 세션마다 한 번이라 값이 작다(거짓 양성).
    helper = "import json\nprint(json.dumps({}))\n"
    payload = _repo_write(_probe_path(tmp_path, "read_table.py"), helper)
    assert rounds_context_for(payload) is not None


def test_Rounds_를_가져오면_지나간다(tmp_path: Path) -> None:
    assert rounds_context_for(_repo_write(_probe_path(tmp_path), WITH_ROUNDS)) is None


def test_probe_kit_만_가져오고_Rounds_는_쓰지_않으면_알린다(tmp_path: Path) -> None:
    content = "from tools.probe_kit import LineReader\n"
    assert rounds_context_for(_repo_write(_probe_path(tmp_path), content)) is not None


def test_Rounds_가_다른_이름의_일부이면_알린다(tmp_path: Path) -> None:
    content = "from tools.probe_kit import LineReader\nMyRounds = 1\nRoundsList = 2\n"
    assert rounds_context_for(_repo_write(_probe_path(tmp_path), content)) is not None


def test_Rounds_낱말만_있고_probe_kit_이_없으면_알린다(tmp_path: Path) -> None:
    payload = _repo_write(_probe_path(tmp_path), "# Rounds 는 나중에\n")
    assert rounds_context_for(payload) is not None


def test_Edit_는_고쳐진_디스크의_파일을_읽는다(tmp_path: Path) -> None:
    path = _probe_path(tmp_path)
    path.parent.mkdir(parents=True)
    edit: HookPayload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(path), "new_string": "x = 1"},
    }
    path.write_text(WITH_ROUNDS + "x = 1\n", encoding="utf-8")
    assert rounds_context_for(edit) is None
    path.write_text("x = 1\n", encoding="utf-8")
    assert rounds_context_for(edit) is not None


def test_Edit_의_파일을_읽지_못하면_알린다(tmp_path: Path) -> None:
    edit: HookPayload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(_probe_path(tmp_path)), "new_string": "x"},
    }
    assert rounds_context_for(edit) is not None


def test_하위_폴더의_프로브도_센다(tmp_path: Path) -> None:
    path = tmp_path / ".scratch" / "harness" / "probes" / "precommit_xdist" / "run.py"
    assert is_repo_probe(str(path))
    assert rounds_context_for(_repo_write(path, "print(1)\n")) is not None


def test_파이썬_프로브만_센다(tmp_path: Path) -> None:
    for name in ("run.sh", "probe.mjs", "README.md", "cases.toml", "data.json"):
        assert not is_repo_probe(str(_probe_path(tmp_path, name))), name


def test_프로브_폴더_밖의_파이썬은_지나간다(tmp_path: Path) -> None:
    assert not is_repo_probe(str(tmp_path / ".scratch" / "harness" / "tools" / "m.py"))
    assert not is_repo_probe(str(tmp_path / "tools" / "probes" / "m.py"))
    assert not is_repo_probe(str(tmp_path / ".scratch" / "harness" / "m.py"))
    assert not is_repo_probe(str(tmp_path / "probes" / ".scratch" / "m.py"))


def test_스크래치패드의_스크립트에는_Rounds_알림이_없다() -> None:
    payload = _write(SCRATCH + "\\measure.py")
    assert rounds_context_for(payload) is None
    assert context_for(payload) is not None


def test_저장소_프로브에는_스크래치패드_알림이_없다(tmp_path: Path) -> None:
    assert context_for(_repo_write(_probe_path(tmp_path), "print(1)\n")) is None


def test_다른_도구와_꼴이_어긋난_입력은_지나간다(tmp_path: Path) -> None:
    path = str(_probe_path(tmp_path))
    assert rounds_context_for({"tool_name": "Read", "tool_input": {"file_path": path}}) is None
    for tool_input in ("x", {"file_path": 1}, {}):
        payload = json.loads(json.dumps({"tool_name": "Write", "tool_input": tool_input}))
        assert rounds_context_for(payload) is None


def test_Write_의_content_가_문자열이_아니면_알린다(tmp_path: Path) -> None:
    payload = json.loads(
        json.dumps(
            {
                "tool_name": "Write",
                "tool_input": {"file_path": str(_probe_path(tmp_path)), "content": 1},
            }
        )
    )
    assert rounds_context_for(payload) is not None


def test_못_보는_것_Rounds_를_주석에만_적은_프로브는_지나간다(tmp_path: Path) -> None:
    content = "# from tools.probe_kit import Rounds 로 바꿀 것\nprint(1)\n"
    assert rounds_context_for(_repo_write(_probe_path(tmp_path), content)) is None


def test_main_은_스크래치패드_알림과_Rounds_알림을_따로_한_번씩_낸다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    state = tmp_path / "state"
    state.mkdir()
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(state))
    probe = _repo_write(_probe_path(tmp_path), "print(1)\n")
    probe["session_id"] = "session-1"
    assert ROUNDS_LEAD in _run_main(monkeypatch, capsys, probe)
    assert _run_main(monkeypatch, capsys, probe) == ""
    # 스크래치패드 알림의 표지는 따로다.
    assert LEAD in _run_main(monkeypatch, capsys, _session_write(SCRATCH + "\\a.py"))
    assert _run_main(monkeypatch, capsys, _session_write(SCRATCH + "\\a.py")) == ""
    # 에이전트마다 따로 센다.
    other = probe.copy()
    other["agent_id"] = "agent-a"
    assert ROUNDS_LEAD in _run_main(monkeypatch, capsys, other)


def test_main_은_Rounds_가_있는_프로브에_아무것도_내지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path / "state"))
    payload = _repo_write(_probe_path(tmp_path), WITH_ROUNDS)
    payload["session_id"] = "session-1"
    assert _run_main(monkeypatch, capsys, payload) == ""
