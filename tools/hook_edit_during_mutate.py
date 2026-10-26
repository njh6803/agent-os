"""PostToolUse 훅(Write|Edit|NotebookEdit). 고친 파일이 든 체크아웃에서 `tools/mutate.py` 가 도는
중이면 이 편집이 변이와 겹친다고 알린다.

왜. 변이 도구는 그 도구가 든 체크아웃의 소스를 고쳐 놓고 시험을 돈다. 백그라운드로 띄운 표 묶음을
`TaskStop` 으로 멈춘 뒤에도 윈도우에서 묶음을 돌리던 셸 스크립트(`bash.exe`)와 그 아래
`uv.exe`·`python.exe` 가 남아 다음 표를 이어 돌았고, 그 약 17분 동안 변이가 든 체크아웃에서
`tools/mutate.py` 와 `tests/tools/test_mutate.py` 를 고쳤다(대기열 358, 일지 2026-10-19-13. 같은
꼴이 일지 2026-10-15-13·2026-10-16-07 에도 있었다). 변이가 든 동안의 편집은 변이된 소스 위에
얹히고, 변이한 파일을 고쳤으면 되돌림이 그 파일을 덮지 않고 3으로 멈춘다. 도구의 독스트링에 처방을
두 번 적었지만 세 번째가 났다. 실패가 시끄러운 쪽(되돌림이 3으로 멈춘다)이 있고 그 편집이 일부러
한 것일 수도 있어 막지 않고 알린다(`.claude/rules/tools.md` 의 계기·막는 훅 가름).

왜 따로인가. 같은 편집 도구에 붙는 `hook_edit_during_commit`(지금은 PreToolUse 에서 막는다, 대기열
412)에 얹지 않는다. 그 훅은 git 프로세스의 명령 줄을
훑고 이 훅은 표지 파일과 pid 하나만 보며, 처방(커밋을 다시 친다, 남은 묶음을 끝낸다)도 다르다.
하나에 얹으면 독스트링의 왜·못 보는 것과 페이로드 표의 사례가 두 판정으로
섞인다(`hook_scratch_probe_rule` 의 같은 판단). 값은 편집마다 래퍼를 거친 파이썬 한 번이다.

판정. 편집한 파일의 폴더에서 위로 올라가 처음 `.git` 이 있는 폴더를 그 체크아웃으로 보고(그 꼴은
`tools/hook_edit_during_commit.py` 와 같다), 그 git 디렉터리(`.git` 디렉터리, 또는 워크트리의
`.git` 파일이 `gitdir:` 로 가리키는 곳)에서 `mutate-running-<pid>.json` 을 찾는다. 변이 도구가 잴
때 두고 끝나면 지우는 표지이고 pid 와 표의 경로와 그 프로세스의 시작 시각(`started`)을 든다. 그
pid 가 살아 있고 지금 그 pid 의 시작 시각이 표지의 것과 같은 표지만 센다. 강제로 끝나 지우지 못한
표지는 pid 가 죽어 세지 않고, 그 pid 를 다른 프로세스가 받았으면 시작 시각이 달라 세지 않는다.
pid 만 보던 때 강제로 끝낸 실행 둘의 표지가 남았고, 그 pid 를 잠깐 받은 다른 프로세스 때문에 변이
도구가 돈다고 거짓으로 알려 확인에 도구 호출 아홉 번을 썼다(대기열 449). 살았는지는 윈도에서
`OpenProcess` 와 `GetExitCodeProcess`(`STILL_ACTIVE`), POSIX 에서 `os.kill(pid, 0)` 으로 본다.
시작 시각은 윈도에서 `GetProcessTimes` 의 만든 시각(100ns 단위), 리눅스에서 `/proc/<pid>/stat` 의
`starttime`(부팅 뒤 클록 틱)이다. 변이 도구가 같은 이름의 사본으로 자기 시작 시각을 적는다
(tests/tools/test_mutate.py 가 두 값을 대조한다). 시작 시각 칸이 있는데 정수가 아닌 표지는 꼴이
다른 표지처럼 세지 않는다. 읽다 실패하면 알리지 않는다(fail-open).

못 보는 것.
- 시작 시각이 없는 옛 표지(이 고침 전의 도구가 남긴 것)는 pid 만으로 본다. 그 pid 를 다른
  프로세스가 받으면 산 것으로 읽어 알린다(거짓 양성). 알림의 처방이 그 pid 를 명령 줄로 확인하게
  한다.
- 시작 시각을 읽지 못하는 자리(윈도·리눅스가 아닌 OS, 열 권한이 없는 프로세스)에서는 시작 시각을
  든 표지를 세지 않아, 실제로 도는 변이 도구도 놓친다(거짓 음성). 막지 않는 계기라 거짓 알림보다
  침묵 쪽으로 기운다. 도구도 그 OS 에서는 시작 시각을 적지 않아 위의 옛 표지처럼 pid 만으로 본다.
- 윈도에서 종료 코드 259 로 끝난 프로세스. 그 값이 `STILL_ACTIVE` 와 같아, 누가 핸들을 쥔 동안
  산 것으로 읽고 시작 시각도 맞아 알린다(거짓 양성). 변이 도구는 0·1·2 로만 끝나고 `taskkill /F`
  는 1 을 내므로, 그 값으로 직접 끝낸 때만 난다.
- 표지를 두기 전과 지운 뒤의 틈. 표를 읽고 고르고 시작 줄의 알림을 내는 동안(아무 파일도 쓰지
  않는다. 원문 확인은 표지를 둔 뒤다)과 마지막 되돌림이 끝난 뒤다.
- 다른 체크아웃의 도구로 이 체크아웃을 고치는 실행. 변이 도구는 자기가 든 체크아웃만 고치므로
  표지도 그 체크아웃에 둔다.
- Bash 로 고친 파일(`sed -i`, `>`). 이 훅은 편집 도구 셋에만 붙는다.
"""

from __future__ import annotations

import ctypes
import json
import os
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import NamedTuple, TypedDict, TypeGuard

# `tools/mutate.py` 의 같은 이름과 같아야 한다(tests/tools/test_mutate.py 가 대조한다). 훅은 단독
# 실행 스크립트라 그 모듈을 import 하지 않는다(`.claude/rules/tools.md`)
MARKER_PREFIX = "mutate-running-"
_STILL_ACTIVE = 259
_QUERY_LIMITED = 0x1000  # PROCESS_QUERY_LIMITED_INFORMATION
_ACCESS_DENIED = 5  # ERROR_ACCESS_DENIED. 프로세스는 있는데 열 권한이 없다
_INHERIT_HANDLE = False  # bInheritHandle. 자식 프로세스에 핸들을 물려주지 않는다


class RunningMutation(NamedTuple):
    """도는 변이 도구 하나의 pid 와 표의 경로."""

    pid: int
    table: str


class _Marker(NamedTuple):
    """표지 파일 하나. `started` 는 그 프로세스의 시작 시각이고 옛 표지에는 없다."""

    pid: int
    table: str
    started: int | None


class _MarkerFile(TypedDict, total=False):
    """표지 파일의 JSON. 값의 형은 읽은 뒤에 본다."""

    pid: object
    table: object
    started: object


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분."""

    tool_input: dict[str, object]
    cwd: str


def checkout_of(directory: str) -> str | None:
    """`directory` 에서 위로 올라가 처음 `.git`(디렉터리나 워크트리의 파일)이 있는 폴더. 없으면
    None."""
    try:
        current = Path(os.path.realpath(directory))
    except (OSError, ValueError):
        return None
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return str(candidate)
    return None


def git_dir_of(checkout: str) -> str | None:
    """그 체크아웃의 git 디렉터리. `.git` 이 디렉터리면 그것, 파일이면 `gitdir:` 줄이 가리키는 곳
    (상대 경로는 그 체크아웃에서 푼다). 읽지 못하면 None."""
    dot_git = Path(checkout) / ".git"
    try:
        if dot_git.is_dir():
            return str(dot_git.resolve())
        line = dot_git.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None
    if not line.startswith("gitdir:"):
        return None
    target = line.removeprefix("gitdir:").strip()
    if not target:
        return None
    return str((Path(checkout) / target).resolve())


def is_alive(pid: int) -> bool:
    """그 pid 의 프로세스가 살아 있나. 이 OS 에서 볼 수 없으면 거짓이다."""
    if pid <= 0:
        return False
    if sys.platform == "win32":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(_QUERY_LIMITED, _INHERIT_HANDLE, pid)
        if not handle:
            return ctypes.get_last_error() == _ACCESS_DENIED
        try:
            code = ctypes.c_ulong()
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return code.value == _STILL_ACTIVE
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def process_started(pid: int) -> int | None:
    """그 pid 프로세스의 시작 시각. 윈도는 `GetProcessTimes` 의 만든 시각(100ns 단위), 리눅스는
    `/proc/<pid>/stat` 의 `starttime`(부팅 뒤 클록 틱)이다. 프로세스가 없거나 끝났거나 읽지
    못하거나 다른 OS 면 None. 윈도는 끝난 프로세스도 누가 핸들을 쥐고 있으면 열리고 만든 시각을
    내므로 끝났는지(`STILL_ACTIVE`)를 함께 본다. `tools/mutate.py` 의 같은 이름과 같은 값을 내야
    한다."""
    if pid <= 0:
        return None
    if sys.platform == "win32":
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
        kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
        times = ctypes.POINTER(ctypes.c_ulonglong)
        kernel.GetProcessTimes.argtypes = [ctypes.c_void_p, times, times, times, times]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(_QUERY_LIMITED, _INHERIT_HANDLE, pid)
        if not handle:
            return None
        try:
            code = ctypes.c_ulong()
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
                return None
            if code.value != _STILL_ACTIVE:
                return None
            created, ended, kernel_time, user_time = (ctypes.c_ulonglong() for _ in range(4))
            if not kernel.GetProcessTimes(
                handle,
                ctypes.byref(created),
                ctypes.byref(ended),
                ctypes.byref(kernel_time),
                ctypes.byref(user_time),
            ):
                return None
            return created.value
        finally:
            kernel.CloseHandle(handle)
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    # 둘째 칸(실행 파일 이름)은 괄호에 싸여 공백을 들 수 있어 마지막 `)` 뒤에서 센다. 그 뒤 첫 칸이
    # 셋째 칸(state)이고 starttime 은 스물두째 칸이다(proc(5))
    fields = stat.rsplit(")", 1)[-1].split()
    return int(fields[19]) if len(fields) > 19 and fields[19].isdigit() else None


_NO_START = object()  # 시작 시각 칸이 없는 옛 표지


def _is_int(value: object) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _marker(path: Path) -> _Marker | None:
    """표지 하나. 읽지 못하거나 꼴이 다르면 None."""
    try:
        data: _MarkerFile = json.loads(path.read_text(encoding="utf-8"))
        pid, table = data.get("pid"), data.get("table")
        started = data.get("started", _NO_START)
    except (OSError, ValueError, AttributeError):  # 읽지 못했거나 JSON 객체가 아니다
        return None
    if not _is_int(pid) or not isinstance(table, str):
        return None
    if started is _NO_START:
        return _Marker(pid, table, None)
    return _Marker(pid, table, started) if _is_int(started) else None


def _running(marker: _Marker) -> bool:
    """표지의 프로세스가 아직 도나. 시작 시각을 든 표지는 지금 그 pid 의 시작 시각과도 맞아야
    한다."""
    if not is_alive(marker.pid):
        return False
    return marker.started is None or process_started(marker.pid) == marker.started


def running_mutations(git_dir: str) -> list[RunningMutation]:
    """그 git 디렉터리의 표지 가운데 그 프로세스가 아직 도는 것, pid 차례로."""
    try:
        paths = sorted(Path(git_dir).glob(f"{MARKER_PREFIX}*.json"))
    except OSError:
        return []
    found = [marker for marker in map(_marker, paths) if marker is not None]
    alive = [RunningMutation(m.pid, m.table) for m in found if _running(m)]
    return sorted(alive, key=lambda run: run.pid)


def edited_file(tool_input: Mapping[str, object]) -> str | None:
    """편집 도구의 입력에서 고친 파일 경로. Write·Edit 은 `file_path`, NotebookEdit 은
    `notebook_path` 다."""
    for key in ("file_path", "notebook_path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _file_name(path: str) -> str:
    """경로의 마지막 토막. 윈도 경로든 POSIX 경로든 이 OS 와 상관없이 뗀다."""
    return path.replace("\\", "/").rsplit("/", 1)[-1]


def context_for(file_path: str, checkout: str, running: Sequence[RunningMutation]) -> str:
    """알릴 문장."""
    runs = ", ".join(f"pid {run.pid}, 표 `{run.table}`" for run in running)
    names = ", ".join(f"`{_file_name(run.table)}`" for run in running)
    return (
        f"방금 고친 `{file_path}` 이 든 체크아웃 `{checkout}` 에서 `tools/mutate.py`({runs})가 "
        "돌고 있다. 그 도구는 이 체크아웃의 소스에 변이를 넣어 놓고 시험을 돌므로, "
        "이 편집은 변이가 든 소스 위에 얹혔을 수 있고, 변이한 파일을 고쳤으면 "
        "되돌림이 그 파일을 덮지 않고 3으로 멈춘다(대기열 358). 이 편집은 이미 "
        "적용됐다. 도구가 끝날 때까지 이 체크아웃의 파일을 더 고치지 않는다. 표 "
        "묶음을 `TaskStop` 으로 멈췄는데도 돌고 있으면 묶음을 돌리던 셸 스크립트가 "
        "남은 것이다. 위의 pid 는 변이 도구를 돌리는 `python.exe` 의 것이고 그 위에 "
        "가상 환경의 런처 `python.exe`, `uv.exe`, 묶음을 돌리던 `bash.exe` 가 차례로 "
        "있다. 명령 줄에 표 파일 이름 "
        f"{names} 이나 묶음 스크립트가 든 `bash.exe`·`uv.exe`·`python.exe` 를 찾는다"
        "(명령 줄의 경로는 상대 경로일 수 있어 위의 절대 경로로는 찾지 않는다). 그 "
        "가운데 가장 위의 것을 `taskkill /T /F /PID <pid>` 로 끝낸다. "
        "끝난 뒤 `git diff` 로 변이가 남았는지 보고 변이만 걷어 낸 다음, 이 편집이 "
        "남았는지 다시 읽는다. pid 를 다른 프로세스가 받았을 수도 있으니 끝내기 전에 "
        "그 명령 줄이 이 도구인지 본다."
    )


def main() -> int:
    # stdin 은 바이트로. 이유는 .claude/rules/tools.md(대기열 25).
    payload: HookPayload = json.load(sys.stdin.buffer)
    file_path = edited_file(payload.get("tool_input") or {})
    if file_path is None:
        return 0
    if not os.path.isabs(file_path):
        file_path = os.path.join(payload.get("cwd") or os.getcwd(), file_path)
    checkout = checkout_of(os.path.dirname(os.path.abspath(file_path)))
    if checkout is None:
        return 0
    git_dir = git_dir_of(checkout)
    if git_dir is None:
        return 0
    try:
        running = running_mutations(git_dir)
    except (OSError, AttributeError, ValueError, ctypes.ArgumentError):
        return 0  # 프로세스를 볼 DLL 이나 함수를 싣지 못했다
    if not running:
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": context_for(file_path, checkout, running),
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
