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

from tools.proc_command_line import argv_from_cmdline, command_line, pids_named

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


def test_실행_파일_이름으로_살아_있는_프로세스의_pid_를_훑는다() -> None:
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        found = pids_named(sys.executable)
        # 이름만 견주므로 폴더와 대소문자가 달라도 같다(윈도). 리눅스는 대소문자를 가린다
        other = pids_named(str(Path("다른곳") / Path(sys.executable).name))
        missing = pids_named(f"없는-이름-{uuid.uuid4().hex[:6]}")
    finally:
        process.kill()
        process.wait(timeout=60)

    assert found is not None and process.pid in found
    assert other is not None and process.pid in other
    assert missing == []


def _잠든_자식(argv: list[str]) -> subprocess.Popen[bytes]:
    return subprocess.Popen(
        argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )


def test_리눅스는_링크로_띄운_이름과_스스로_바꾼_이름을_놓치고_앞_15바이트가_같은_이름을_함께_든다(
    tmp_path: Path,
) -> None:
    """`pids_named`의 못 보는 것 셋. 셋 다 리눅스의 comm 에서만 나므로 리눅스에서만 단언하고, 이
    PC(윈도)에서는 이 시험이 재는 것이 없다. 리눅스 CI 가 잰다."""
    if sys.platform != "linux":
        return
    link = tmp_path / "aliasprobe12345"  # comm 의 상한인 15바이트
    link.symlink_to(sys.executable)
    sleep = "import time; time.sleep(120)"
    rename = "open('/proc/self/comm', 'w').write('renamedprobe'); import time; time.sleep(120)"
    linked = _잠든_자식([str(link), "-c", sleep])
    renamed = _잠든_자식([sys.executable, "-c", rename])
    observed = False
    try:
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            seen = pids_named("renamedprobe")
            if seen is not None and renamed.pid in seen:
                observed = True
                break
            time.sleep(0.1)
        by_python = pids_named(sys.executable)
        by_longer = pids_named("aliasprobe12345-그-뒤가-다르다")
    finally:
        for process in (linked, renamed):
            process.kill()
            process.wait(timeout=60)

    assert observed, "이름을 바꾼 자식을 기한 안에 보지 못했다"
    assert by_python is not None
    assert linked.pid not in by_python and renamed.pid not in by_python
    assert by_longer is not None and linked.pid in by_longer


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
        "_SNAPSHOT_PROCESSES",
        "_INVALID_HANDLE",
        "_ProcessEntry",
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
    # API 원형은 이 모듈이 쓰는 것만 적는다. 훅은 실행 파일 경로를 더 쓴다
    copied, original = copy["_windows_api"], hook["_windows_api"]
    assert isinstance(copied, ast.FunctionDef)
    assert isinstance(original, ast.FunctionDef)
    original_lines = {ast.dump(statement) for statement in original.body}
    missing = [ast.dump(s) for s in copied.body if ast.dump(s) not in original_lines]
    assert missing == [], "훅의 API 원형에 없는 문장"
