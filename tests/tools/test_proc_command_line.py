"""tools/proc_command_line.py: pid 하나의 명령 줄을 낱말로 읽는다.

살아 있는 하위 프로세스를 띄워 실제로 읽는다. 리눅스 CI 에서는 `/proc`, 이 PC 에서는 PEB 를 읽는다.
"""

from __future__ import annotations

import ast
import subprocess
import sys
import time
import uuid
from pathlib import Path

from tools.proc_command_line import argv_from_cmdline, command_line

ROOT = Path(__file__).resolve().parents[2]


def test_살아_있는_프로세스의_명령_줄을_낱말로_읽는다() -> None:
    marker = f"표지 {uuid.uuid4()}"  # 공백이 든 낱말도 한 낱말로 돌아온다
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)", marker, ""],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        argv = command_line(process.pid)
    finally:
        process.kill()
        process.wait(timeout=60)

    assert argv is not None
    assert marker in argv
    assert argv[-2:] == (marker, "")


def test_끝났지만_거두지_않은_자식은_빈_값이다() -> None:
    process = subprocess.Popen(
        [sys.executable, "-c", "pass"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        # 거두면 pid 가 다른 프로세스에 갈 수 있어 poll 도 부르지 않고 끝나기를 기다린다
        deadline = time.monotonic() + 60
        argv = command_line(process.pid)
        while argv is not None and time.monotonic() < deadline:
            time.sleep(0.1)
            argv = command_line(process.pid)
    finally:
        process.wait(timeout=60)

    assert argv is None


def test_없는_pid_와_0_이하의_pid_는_빈_값이다() -> None:
    assert command_line(0) is None
    assert command_line(-5) is None
    assert command_line(2**31 - 1) is None  # 리눅스의 pid 상한과 윈도의 pid 보다 크다


def test_proc_의_명령_줄은_끝의_NUL_하나만_떼고_빈_낱말을_지킨다() -> None:
    assert argv_from_cmdline(b"claude\0-p\0\0--resume\0s-1\0") == (
        "claude",
        "-p",
        "",
        "--resume",
        "s-1",
    )
    assert argv_from_cmdline(b"") == ()  # 거두지 않은 좀비의 cmdline 은 비었다


def _윗자리_정의(path: Path) -> dict[str, ast.stmt]:
    """모듈 맨 위와 그 바로 아래 `if`(플랫폼 갈래) 안의 함수·클래스·이름 하나에 대는 대입을
    이름마다. 함수와 클래스는 독스트링을 뗀다. 독스트링의 띄어쓰기는 두 사본이 다르게 써 왔다."""
    statements: list[ast.stmt] = []
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        statements.extend([*node.body, *node.orelse] if isinstance(node, ast.If) else [node])
    found: dict[str, ast.stmt] = {}
    for node in statements:
        if isinstance(node, ast.FunctionDef | ast.ClassDef):
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                if isinstance(first.value.value, str):
                    node.body = node.body[1:]
            found[node.name] = node
        elif isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                found[target.id] = node
    return found


def test_훅에서_옮긴_명령_줄_읽기가_훅의_것과_같다() -> None:
    # 훅은 단독 실행이라 이 모듈을 import 하지 않고 옮겨 적었다(모듈 독스트링). 윈도 갈래는
    # `sys.platform` 아래에서만 정의되어 import 로는 리눅스 CI 에서 볼 수 없으므로 소스를 풀어 댄다
    copy = _윗자리_정의(ROOT / "tools" / "proc_command_line.py")
    hook = _윗자리_정의(ROOT / "tools" / "hook_edit_during_commit.py")
    shared = set(copy) & set(hook)

    assert shared == {
        "argv_from_cmdline",
        "_QUERY_LIMITED",
        "_VM_READ",
        "_INHERIT_HANDLE",
        "_PEB_PARAMS",
        "_PARAMS_COMMAND_LINE",
        "_BasicInformation",
        "_windows_api",
        "_read_memory",
        "_unicode_string",
        "_parameters",
        "_split_command_line",
    }
    for name in sorted(shared - {"_windows_api"}):
        assert ast.dump(copy[name]) == ast.dump(hook[name]), name
    # API 원형은 이 모듈이 쓰는 것만 적는다. 훅은 Toolhelp 와 실행 파일 경로를 더 쓴다
    copied, original = copy["_windows_api"], hook["_windows_api"]
    assert isinstance(copied, ast.FunctionDef)
    assert isinstance(original, ast.FunctionDef)
    original_lines = {ast.dump(statement) for statement in original.body}
    missing = [ast.dump(s) for s in copied.body if ast.dump(s) not in original_lines]
    assert missing == [], "훅의 API 원형에 없는 문장"
