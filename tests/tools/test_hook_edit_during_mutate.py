"""tools/hook_edit_during_mutate.py 의 판정. 도는 표지는 `tools/mutate.py` 가 그 체크아웃의 git
디렉터리에 두는 `mutate-running-<pid>.json` 이고, pid 가 살았는지는 실제 프로세스로 본다.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from tools.hook_edit_during_mutate import (
    MARKER_PREFIX,
    RunningMutation,
    context_for,
    git_dir_of,
    is_alive,
    running_mutations,
)
from tools.run_hooks import registered_matchers

HOOK = Path(__file__).parents[2] / "tools" / "hook_edit_during_mutate.py"


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
    )


def _저장소(root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    (root / "m.py").write_text("x = 1\n", encoding="utf-8")
    _git(root, "init", "-q", "-b", "main")
    _git(root, "add", ".")
    _git(root, "commit", "-q", "-m", "처음")
    return root


def _끝난_pid() -> int:
    """끝난 프로세스의 pid. 그새 다른 프로세스가 같은 번호를 받으면 산 것으로 읽힌다(못 보는 것)."""
    process = subprocess.Popen([sys.executable, "-c", "pass"])
    process.wait(timeout=60)
    return process.pid


def _표지를_둔다(git_dir: Path, pid: int, table: str = "probes/x_mutations.toml") -> Path:
    path = git_dir / f"{MARKER_PREFIX}{pid}.json"
    path.write_text(json.dumps({"pid": pid, "table": table}), encoding="utf-8")
    return path


def test_주_체크아웃의_git_디렉터리는_그_폴더다(tmp_path: Path) -> None:
    root = _저장소(tmp_path / "repo")

    assert git_dir_of(str(root)) == str((root / ".git").resolve())


def test_워크트리의_git_디렉터리는_git_파일이_가리키는_곳이다(tmp_path: Path) -> None:
    root = _저장소(tmp_path / "repo")
    옆 = tmp_path / "side"
    _git(root, "worktree", "add", "-q", "-b", "side", str(옆))

    assert git_dir_of(str(옆)) == str((root / ".git" / "worktrees" / "side").resolve())


def test_git_파일의_상대_경로는_그_체크아웃에서_푼다(tmp_path: Path) -> None:
    (tmp_path / "real").mkdir()
    (tmp_path / "co").mkdir()
    (tmp_path / "co" / ".git").write_text("gitdir: ../real\n", encoding="utf-8")

    assert git_dir_of(str(tmp_path / "co")) == str((tmp_path / "real").resolve())


@pytest.mark.parametrize("내용", ["", "not a gitdir line\n"], ids=["빈_파일", "모르는_꼴"])
def test_읽지_못하는_git_파일이면_git_디렉터리가_없다(tmp_path: Path, 내용: str) -> None:
    (tmp_path / ".git").write_text(내용, encoding="utf-8")

    assert git_dir_of(str(tmp_path)) is None


def test_이_프로세스는_살았고_끝난_프로세스는_죽었다() -> None:
    assert is_alive(os.getpid())
    assert not is_alive(_끝난_pid())


def test_산_pid_의_표지만_센다(tmp_path: Path) -> None:
    """강제로 끝나 지우지 못한 표지(pid 가 죽었다)는 세지 않는다."""
    _표지를_둔다(tmp_path, os.getpid(), "a_mutations.toml")
    _표지를_둔다(tmp_path, _끝난_pid(), "b_mutations.toml")
    (tmp_path / f"{MARKER_PREFIX}9.json").write_text("{깨졌다", encoding="utf-8")
    (tmp_path / f"{MARKER_PREFIX}8.json").write_text('{"pid": "8"}', encoding="utf-8")

    assert running_mutations(str(tmp_path)) == [RunningMutation(os.getpid(), "a_mutations.toml")]


def test_알림은_pid_와_표와_남은_묶음을_찾는_법을_든다() -> None:
    표 = "C:\\r\\.scratch\\p\\x_mutations.toml"  # 도구는 절대 경로를 적는다
    context = context_for("C:/r/tools/m.py", "C:/r", [RunningMutation(41, 표)])

    for 문구 in ("pid 41", 표, "bash.exe", "uv.exe", "taskkill /T /F", "git diff"):
        assert 문구 in context, 문구


def test_남은_묶음은_절대_경로가_아니라_표_파일_이름으로_찾게_한다() -> None:
    """놓친 프로세스의 명령 줄은 상대 경로였고, 표지의 pid 는 python 의 것이라 묶음을 돌리던
    `bash.exe` 의 명령 줄에 없다(일지 2026-10-19-13, 셀프 리뷰 표준 축)."""
    for 표 in ("C:\\r\\.scratch\\p\\x_mutations.toml", "/r/.scratch/p/x_mutations.toml"):
        context = context_for("C:/r/tools/m.py", "C:/r", [RunningMutation(41, 표)])
        assert "표 파일 이름 `x_mutations.toml`" in context, context


def _run_hook(payload: dict[str, object]) -> str:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
        timeout=60,
        check=True,
    )
    return result.stdout.decode("utf-8")


def _편집(path: Path) -> dict[str, object]:
    return {
        "hook_event_name": "PostToolUse",
        "tool_name": "Edit",
        "tool_input": {"file_path": str(path), "old_string": "x", "new_string": "y"},
        "cwd": str(path.parent),
    }


def test_훅은_변이가_도는_체크아웃의_편집에만_계기를_낸다(tmp_path: Path) -> None:
    """stdin 의 바이트 페이로드부터 출력까지. 표지의 pid 는 이 시험 프로세스라 살아 있다."""
    도는 = _저장소(tmp_path / "running")
    남은_표지 = _저장소(tmp_path / "stale")
    _표지를_둔다(도는 / ".git", os.getpid())
    _표지를_둔다(남은_표지 / ".git", _끝난_pid())

    firing = _run_hook(_편집(도는 / "m.py"))
    stale = _run_hook(_편집(남은_표지 / "m.py"))
    outside = _run_hook(_편집(tmp_path / "loose.py"))

    output = json.loads(firing)["hookSpecificOutput"]
    assert output["hookEventName"] == "PostToolUse"
    assert "tools/mutate.py" in output["additionalContext"]
    assert (stale, outside) == ("", "")


def test_settings의_매처는_편집_도구_셋이다() -> None:
    """알림은 편집이 끝난 뒤에 온다(PostToolUse). 그 편집 하나는 이미 변이와 겹쳤다."""
    assert registered_matchers("hook_edit_during_mutate.py", "PostToolUse") == [
        "Write|Edit|NotebookEdit"
    ]
