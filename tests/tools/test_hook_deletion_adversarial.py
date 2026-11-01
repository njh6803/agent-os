"""tools/hook_deletion_adversarial.py 의 판정과 표지. main 은 stdin 과 임시 폴더를 바꿔 끼워 표지
길을 보고, 래퍼를 거친 실제 실행은 tools/run_hooks.py 의 표가 본다.
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from pathlib import Path

import pytest
from tools.hook_deletion_adversarial import (
    LEAD,
    TOOLS,
    HookPayload,
    added_lines,
    claim_first,
    context_for,
    deleting_lines,
    is_tool_code,
    main,
    marker_name,
)
from tools.run_hooks import registered_matchers

ROOT = "C:\\project\\agent\\.claude\\worktrees\\deletion-hook"
PY = ROOT + "\\tools\\tidy_checkouts.py"
TS = ROOT + "\\web\\tools\\judge-trees.ts"


def _write(file_path: str, content: str) -> HookPayload:
    return {"tool_name": "Write", "tool_input": {"file_path": file_path, "content": content}}


def _edit(file_path: str, old: str, new: str, original: str | None = None) -> HookPayload:
    payload: HookPayload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path, "old_string": old, "new_string": new},
    }
    if original is not None:
        payload["tool_response"] = {"originalFile": original}
    return payload


def test_지우는_호출을_더하면_다섯_입력을_짚는다() -> None:
    context = context_for(_write(PY, "import shutil\nshutil.rmtree(path)\n"))
    assert context is not None
    assert context.startswith(LEAD)
    assert "shutil.rmtree(path)" in context
    assert ".claude/rules/tools.md" in context
    # 다섯 입력: 사람이 지은 같은 꼴 폴더, 경로 정규화, 링크, MAX_PATH, 다른 자리.
    for needle in ("커밋하지 않은 파일", "경로 정규화", "junction", "MAX_PATH", "다른 자리"):
        assert needle in context, needle


@pytest.mark.parametrize(
    "line",
    [
        "shutil.rmtree(path, ignore_errors=True)",
        "rmtree(path)",
        "os.remove(path)",
        "os.unlink(path)",
        "path.unlink(missing_ok=True)",
        "folder.rmdir()",
        "os.rmdir(folder)",
        "os.removedirs(folder)",
        "rmSync(target, { recursive: true })",
        "fs.rmSync(target, { recursive: true, force: true })",
        "rmdirSync(target)",
        "unlinkSync(target)",
        "await rm(target, { recursive: true })",
        "await fsp.rm(target, { recursive: true })",
        "await fs.promises.rm(target)",
        "rimraf(target)",
        "git worktree remove --force path",
        'run(["git", "worktree", "remove", str(path)])',
        'git("worktree", "remove", path)',
        "git clean -fd",
        'git("clean", "-fdx")',
        "git branch -D old",
        'git("branch", "-D", name)',
        "Remove-Item -Recurse -Force $path",
        "rm -rf build",
    ],
)
def test_지우는_호출의_꼴마다_알린다(line: str) -> None:
    assert deleting_lines([line]) == [line], line


@pytest.mark.parametrize(
    "line",
    [
        "items.remove(item)",
        "seen.discard(name)",
        "result = perform(x)",
        "confirm(message)",
        "platform(x)",
        "storm(x)",
        "git worktree list",
        'git("worktree", "add", path)',
        'git("branch", "--show-current")',
        "git status --porcelain",
        "removed = len(paths)",
        "rm_count = 0",
    ],
)
def test_지우지_않는_호출은_지나간다(line: str) -> None:
    assert deleting_lines([line]) == [], line


def test_주석_줄은_지나간다() -> None:
    lines = ["# shutil.rmtree(path) 로 지운다", "// fs.rmSync(path) 로 지운다"]
    assert deleting_lines(lines) == []


def test_tools_와_web_tools_아래_코드만_본다() -> None:
    assert is_tool_code(PY)
    assert is_tool_code(TS)
    assert is_tool_code(PY.replace("\\", "/"))
    assert is_tool_code(PY.replace("\\tools\\", "\\Tools\\"))
    assert is_tool_code("tools/canary.py")
    assert is_tool_code(ROOT + "\\tools\\sub\\deep.py")
    for suffix in (".py", ".ts", ".tsx", ".mts", ".cts", ".js", ".mjs", ".cjs", ".ps1", ".sh"):
        assert is_tool_code(ROOT + "\\tools\\x" + suffix), suffix


def test_시험_파일과_tools_밖은_지나간다() -> None:
    for path in (
        ROOT + "\\tests\\tools\\test_tidy_checkouts.py",
        ROOT + "\\tests\\tools\\fixtures\\helper.py",
        ROOT + "\\tools\\test_x.py",
        ROOT + "\\tools\\x_test.py",
        ROOT + "\\tools\\conftest.py",
        ROOT + "\\web\\tools\\judge-trees.test.ts",
        ROOT + "\\web\\tools\\types.test-d.ts",
        ROOT + "\\web\\tools\\a.spec.ts",
        ROOT + "\\src\\agent_os\\core\\loader.py",
        ROOT + "\\.claude\\skills\\x\\run.py",
        ROOT + "\\tools\\README.md",
        ROOT + "\\tools\\data.toml",
        ROOT + "\\tools",
        "tools",
    ):
        assert not is_tool_code(path), path


def test_폴더_이름이_tools_인_것만_tools_다() -> None:
    assert not is_tool_code(ROOT + "\\mytools\\x.py")
    assert not is_tool_code(ROOT + "\\tools2\\x.py")
    assert not is_tool_code(ROOT + "\\tools.py")


def test_시험_파일에_지우는_호출을_더해도_지나간다() -> None:
    payload = _write(ROOT + "\\tests\\tools\\test_x.py", "shutil.rmtree(tmp_path)\n")
    assert context_for(payload) is None


def test_코드_밖_확장자에_더해도_지나간다() -> None:
    assert context_for(_write(ROOT + "\\tools\\NOTES.md", "shutil.rmtree(path)\n")) is None


def test_Edit_이_더한_줄만_본다() -> None:
    original = "shutil.rmtree(path)\nx = 1\n"
    assert context_for(_edit(PY, "x = 1", "x = 2", original)) is None
    context = context_for(_edit(PY, "x = 1", "x = 1\nos.remove(other)", original))
    assert context is not None
    assert "os.remove(other)" in context
    assert "shutil.rmtree(path)" not in context


def test_Write_는_원래_파일에_없던_줄만_본다() -> None:
    payload: HookPayload = {
        "tool_name": "Write",
        "tool_input": {"file_path": PY, "content": "shutil.rmtree(a)\nos.remove(b)\n"},
        "tool_response": {"type": "update", "originalFile": "shutil.rmtree(a)\n"},
    }
    context = context_for(payload)
    assert context is not None
    assert "os.remove(b)" in context
    assert "shutil.rmtree(a)" not in context


def test_새_파일의_Write_는_모든_줄을_본다() -> None:
    payload = _write(PY, "shutil.rmtree(a)\n")
    assert context_for(payload) is not None
    created = json.loads(json.dumps({**payload, "tool_response": {"originalFile": None}}))
    assert context_for(created) is not None


def test_Edit_조각이_줄의_일부여도_그_줄을_본다() -> None:
    original = "    path = target\n"
    new = "path = target; shutil.rmtree(path)"
    context = context_for(_edit(PY, "path = target", new, original))
    assert context is not None
    assert "path = target; shutil.rmtree(path)" in context


def test_replace_all_은_모든_자리를_바꾼다() -> None:
    original = "a = 1\nb = 1\n"
    payload: HookPayload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": PY, "old_string": "= 1", "new_string": "= f(); rmtree(x)"},
        "tool_response": {"originalFile": original},
    }
    once = context_for(payload)
    payload["tool_input"]["replace_all"] = True
    every = context_for(payload)
    assert once is not None
    assert every is not None
    assert "걸린 줄(1개)" in once
    assert "걸린 줄(2개)" in every


def test_걸린_줄은_셋까지_잘라_보인다() -> None:
    lines = [f"rmtree(p{index}) " + "가" * 300 for index in range(5)]
    context = context_for(_write(PY, "\n".join(lines)))
    assert context is not None
    assert "걸린 줄(5개)" in context
    assert "rmtree(p0)" in context
    assert "rmtree(p3)" not in context
    assert "가" * 200 not in context


def test_더한_줄은_원래_글에_없던_줄이다() -> None:
    assert added_lines("a\nb\n", "a\nc\nb\n") == ["c"]
    assert added_lines("", "x\n\ny") == ["x", "y"]


def test_다른_도구와_꼴이_어긋난_입력은_지나간다() -> None:
    read = json.loads(json.dumps({"tool_name": "Read", "tool_input": {"file_path": PY}}))
    assert context_for(read) is None
    for tool_input in ("x", {"file_path": 1}, {"file_path": PY, "new_string": 1}, {}):
        payload = json.loads(json.dumps({"tool_name": "Edit", "tool_input": tool_input}))
        assert context_for(payload) is None, tool_input
    assert context_for(json.loads(json.dumps({"tool_name": "Write"}))) is None
    write = {"tool_name": "Write", "tool_input": {"file_path": PY, "content": "rmtree(x)\n"}}
    write["tool_response"] = "x"
    assert context_for(json.loads(json.dumps(write))) is not None


def test_못_보는_것_도우미를_거친_지우기는_지나간다() -> None:
    # 지우는 호출이 도우미 함수 뒤에 있으면 그 호출 줄이 아니다. 도우미를 부르는 줄은 알리지 않는다.
    assert context_for(_write(PY, "delete_path(folder)\n")) is None


def test_못_보는_것_이미_있는_지우기_둘레의_판정을_고쳐도_지나간다() -> None:
    original = "if is_safe(path):\n    shutil.rmtree(path)\n"
    edit = _edit(PY, "is_safe(path)", "is_safe(path) and not linked(path)", original)
    assert context_for(edit) is None


def test_못_보는_것_덮어쓰는_호출은_지나간다() -> None:
    content = 'path.write_text("x")\nos.replace(a, b)\nshutil.move(a, b)\nopen(path, "w")\n'
    assert context_for(_write(PY, content)) is None


def test_못_보는_것_독스트링에_든_호출_낱말도_알린다() -> None:
    # 주석 줄만 걸러 내므로, 독스트링 안의 줄은 코드와 가르지 못한다.
    assert context_for(_write(PY, '"""\n지울 때 shutil.rmtree(path) 를 쓴다.\n"""\n')) is not None


def test_못_보는_것_Bash_로_쓴_파일은_지나간다() -> None:
    command = f"cat >> '{PY}' <<'EOF'\nshutil.rmtree(path)\nEOF"
    payload = json.loads(json.dumps({"tool_name": "Bash", "tool_input": {"command": command}}))
    assert context_for(payload) is None


def test_못_보는_것_저장소_밖의_tools_폴더도_본다() -> None:
    assert is_tool_code("C:\\Users\\User\\tools\\clean.py")


def test_못_보는_것_tools_토막이_든_다른_자리도_본다() -> None:
    for path in (
        "web/apps/admin/tools/x.ts",
        "plugins/x/tools/a.py",
        "node_modules/pkg/tools/a.js",
    ):
        assert is_tool_code(path), path


def test_못_보는_것_같은_글자의_줄을_또_더하면_지나간다() -> None:
    original = "def a():\n    shutil.rmtree(path)\n"
    payload: HookPayload = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": PY,
            "content": original + "def b():\n    shutil.rmtree(path)\n",
        },
        "tool_response": {"originalFile": original},
    }
    assert context_for(payload) is None


def test_못_보는_것_보호문을_둘러_들여쓰기가_바뀐_지우기는_알린다() -> None:
    original = "shutil.rmtree(path)\n"
    edit = _edit(PY, "shutil.rmtree(path)", "if safe(path):\n    shutil.rmtree(path)", original)
    context = context_for(edit)
    assert context is not None
    assert "shutil.rmtree(path)" in context


@pytest.mark.parametrize(
    "line",
    [
        '["rm", "-rf", path]',
        'os.system("rm -rf x")',
        "rm -R dir",
        "rm --recursive dir",
        'rm "$f"',
        "rimraf.sync(path)",
        "dir.Delete(true)",
        "rmdir /s /q dir",
        "git branch --delete topic",
    ],
)
def test_못_보는_것_호출_목록_밖의_지우기는_지나간다(line: str) -> None:
    assert deleting_lines([line]) == [], line


def test_못_보는_것_확장자가_코드_목록_밖이면_지나간다() -> None:
    for suffix in (".bat", ".cmd", ".psm1"):
        assert context_for(_write(ROOT + "\\tools\\x" + suffix, "rm -rf dir\n")) is None, suffix


@pytest.mark.parametrize(
    "line",
    [
        "x = 1  # shutil.rmtree(p)",
        "/* rmSync(x) */",
        " * rmSync(x)",
        "def rmtree(a):",
        "def unlink(self):",
        "git clean -n",
    ],
)
def test_못_보는_것_지우지_않는_줄도_알린다(line: str) -> None:
    assert deleting_lines([line]) == [line], line


def test_못_보는_것_시험_파일_꼴_이름의_도구_파일은_지나간다() -> None:
    for name in ("test_runner.py", "latest_test.py"):
        payload = _write(ROOT + "\\tools\\" + name, "shutil.rmtree(path)\n")
        assert context_for(payload) is None, name


def test_Edit_은_원래_글이_없으면_조각_둘을_쓰기_전과_뒤로_본다() -> None:
    # 결과에 originalFile 이 없다.
    context = context_for(_edit(PY, "x = 1", "x = 1\nrmtree(p)"))
    assert context is not None
    assert "rmtree(p)" in context
    # originalFile 은 있으나 old_string 이 그 안에 없다.
    context = context_for(_edit(PY, "rmtree(p)", "rmtree(p)\nrmtree(q)", "other\n"))
    assert context is not None
    assert "rmtree(q)" in context
    assert "rmtree(p)" not in context


def test_표지는_세션과_에이전트마다_한_번이다(tmp_path: Path) -> None:
    main_key = marker_name("s1", "")
    assert claim_first(main_key, tmp_path)
    assert not claim_first(main_key, tmp_path)
    assert claim_first(marker_name("s1", "agent-a"), tmp_path)
    assert claim_first(marker_name("s2", ""), tmp_path)


def test_표지를_쓰지_못하면_알린다(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("", encoding="utf-8")
    assert claim_first(marker_name("s1", ""), blocker / "state")
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


def _session_write(content: str, agent_id: str = "") -> HookPayload:
    payload = _write(PY, content)
    payload["session_id"] = "session-1"
    if agent_id:
        payload["agent_id"] = agent_id
    return payload


def test_main_은_세션과_에이전트마다_한_번_알린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    assert LEAD in _run_main(monkeypatch, capsys, _session_write("rmtree(a)\n"))
    assert _run_main(monkeypatch, capsys, _session_write("rmtree(b)\n")) == ""
    assert LEAD in _run_main(monkeypatch, capsys, _session_write("rmtree(c)\n", "agent-a"))


def test_main_은_걸리지_않은_편집으로_표지를_쓰지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    assert _run_main(monkeypatch, capsys, _session_write("x = 1\n")) == ""
    assert LEAD in _run_main(monkeypatch, capsys, _session_write("rmtree(a)\n"))


def test_main_은_세션을_모르면_호출마다_알린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))
    payload = _write(PY, "rmtree(a)\n")
    assert LEAD in _run_main(monkeypatch, capsys, payload)
    assert LEAD in _run_main(monkeypatch, capsys, payload)
    # 빈 세션 ID 도 모르는 세션이다. 하나의 표지 이름으로 묶으면 서로 다른 세션이 알림을 가린다.
    blank = _write(PY, "rmtree(a)\n")
    blank["session_id"] = ""
    assert LEAD in _run_main(monkeypatch, capsys, blank)
    assert LEAD in _run_main(monkeypatch, capsys, blank)


def test_main_은_임시_폴더가_없으면_호출마다_알린다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def no_temp() -> str:
        raise FileNotFoundError("쓸 수 있는 임시 폴더가 없다")

    monkeypatch.setattr(tempfile, "gettempdir", no_temp)
    assert LEAD in _run_main(monkeypatch, capsys, _session_write("rmtree(a)\n"))
    assert LEAD in _run_main(monkeypatch, capsys, _session_write("rmtree(a)\n"))


def test_등록의_매처가_훅이_아는_도구와_같다() -> None:
    assert registered_matchers("hook_deletion_adversarial.py", "PostToolUse") == ["|".join(TOOLS)]
