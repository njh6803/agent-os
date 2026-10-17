"""PostToolUse 훅(Write|Edit|NotebookEdit). 고친 파일이 든 체크아웃에 `git commit` 이 도는 중이면 이
편집이 그 커밋의 검사와 겹친다고 알린다.

왜. pre-commit 의 검사는 작업 트리를 읽는다. 커밋이 도는 동안 파일을 고치자 pytest 가 줄을 감다 만
순간의 파일을 읽었고, pre-commit 은 훅이 도는 사이 바뀐 파일을 그 훅이 고친 것으로 세어 커밋이
실패했다(대기열 293. 일지 2026-10-06-09 와 2026-10-16-21). 이 저장소의 커밋은 pre-commit 이 길어
백그라운드로 돌기 쉽고, 그동안 다음 편집을 시작하기 쉽다. 커밋 전에 스테이지하지 않은 변경이
있었으면 더 나쁘다. pre-commit 은 그 변경을 치우고(`git checkout -- .`) 훅을 돈 뒤 패치를
되돌리는데, 되돌리기가 충돌하면 작업 트리를 다시 치우고 패치만 얹어 그 사이의 편집이
지워진다(pre-commit 4.6.2 의 `staged_files_only.py` 를 읽었다). 실패가 시끄러운 쪽(커밋이 빨갛다)이
있어 막지 않고 알린다(`.claude/rules/tools.md` 의 계기·막는 훅 가름). 알린 뒤에도 어겨지면
PreToolUse 의 막는 훅으로 올린다. PostToolUse 라 알림은 편집이 끝난 뒤에 온다.

왜 프로세스인가. 대기열 293 의 행은 그 체크아웃의 git 디렉터리에 `index.lock` 이 있는지로 보자고
했다. 탐침으로 재니(`.scratch/harness/probes/commit_lock/probe.py`, git 2.32) `git add` 뒤의 보통
커밋은 pre-commit·commit-msg 훅이 도는 동안 `index.lock` 이 없었다. 잠금은 `-a` 와 경로를 준
커밋에만 있었다. 이 저장소의 커밋은 앞의 꼴이라 잠금으로는 거의 못 본다. 그래서 도는 `git commit`
프로세스를 찾는다.

판정. 편집한 파일(`file_path`, NotebookEdit 은 `notebook_path`)의 폴더에서 위로 올라가 처음
`.git`(디렉터리나 워크트리의 파일)이 있는 폴더를 그 체크아웃으로 본다. 프로세스 가운데 이름이
git 인 것의 명령 줄에서 전역 옵션(`-C <경로>`, `-c <설정>` 등)을 건너뛴 첫 낱말이 `commit` 이면,
그 작업 디렉터리에서 같은 방법으로 체크아웃을 찾는다. 둘이 같으면 알린다. 주 체크아웃 안의
워크트리(`.claude/worktrees/<이름>`)는 자기 `.git` 파일이 있어 다른 체크아웃이다. 실제 git 은
하위 폴더에서 쳤든 밖에서 `-C`(상대 경로 포함)·`--git-dir`·`--work-tree` 로 쳤든 작업 디렉터리를 그
작업 트리 안으로 옮겼다(tests/tools 의 실제 프로세스 시험, git 2.32). 다만 윈도 git 의
런처(`cmd\\git.exe`)는 띄운 폴더를 작업 디렉터리로 쥔 채 같은 명령 줄로 살아 있다. 이 PC 에서 세션의
PowerShell 도구는 `git` 을 이 런처로 먼저 풀었고, 런처로 친 `git -C <A> commit` 은 띄운 폴더 B 를
작업 디렉터리로 쥔 런처와 A 의 실제 git 둘로 보였다(손으로 봤다, 2026-10-16). 작업 디렉터리만 본 첫
판은 그 커밋을 B 의 커밋으로도 읽었다(셀프 리뷰 명세 축이 재현했다). 그래서 자식 git 을 띄운
git(런처)은 세지 않는다(`running_commits`). 런처의 작업 디렉터리에 `-C` 를 얹던 둘째 판은 실제 git
에도 얹어, 이미 옮겨 간 자리에 상대 경로 `-C ../../repo` 를 한 번 더 얹어 놓쳤다(PR 직전
`bug-perf-review` 가 실제 프로세스로 재현했다). 커밋이 도는 동안의 편집마다 같은 알림을 낸다.
편집마다 겹치기 때문이다. 경로는 `os.path.realpath` 로 펴서 대고,
윈도에서는 대소문자를 가리지 않는다. 윈도는 Toolhelp 스냅숏으로 프로세스 이름을 훑고 git 만 열어
PEB 의 작업 디렉터리와 명령 줄을 읽는다. PEB 를 읽는 자리는 `tools/tidy_checkouts.py` 와 같고, 훅은
단독 실행 스크립트라 그 모듈을 import 하지 않고 옮겨 적었다(`.claude/rules/tools.md`). 리눅스는
`/proc/<pid>/` 의 `comm`·`stat`(부모 pid)·`cmdline`·`cwd` 를 읽는다. 읽다 실패하면 알리지
않는다(fail-open).

못 보는 것.
- 커밋이 아닌 검사(`uv run pre-commit run`, `uv run pytest`)가 도는 동안의 편집. git 의 `commit`
  만 센다. git 을 감싸는 실행 파일(`hub commit`)은 세지 않고 그 아래에서 도는 git 이 센다.
- git 별칭으로 친 커밋(`git ci`). 명령 줄의 하위 명령이 `commit` 이 아니라 세지 않는다.
- `.git` 이 없는 작업 트리(바깥 저장소를 `--git-dir` 로 쓰는 꼴). 그 커밋도 그 안의 편집도
  체크아웃을 찾지 못한다.
- Bash 로 고친 파일(`sed -i`, `>`). 이 훅은 편집 도구 셋에만 붙고 그 입력에는 경로 칸이 없다.
- 윈도와 리눅스 밖의 OS, 32비트 파이썬. 프로세스를 읽지 않아 알리지 않는다(PEB 는 x64 의 자리만
  안다). 32비트 git 은 64비트 PEB 의 사본을 읽어, 32비트 코드가 옮긴 작업 디렉터리를 따라가지 않을
  수 있다(`tools/tidy_checkouts.py` 의 못 보는 것과 같다. 재지 않았다).
"""

from __future__ import annotations

import ctypes
import json
import os
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import NamedTuple, TypedDict

# git 전역 옵션 가운데 다음 낱말을 값으로 먹는 것(`git -C <경로> commit`).
_GIT_VALUE_OPTIONS = frozenset(
    {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env", "--super-prefix"}
)


class Process(NamedTuple):
    """프로세스 하나. `argv` 는 명령 줄을 나눈 낱말, `cwd` 는 작업 디렉터리, `parent` 는 부모
    pid(모르면 0)다."""

    pid: int
    image: str
    argv: tuple[str, ...]
    cwd: str
    parent: int = 0


class RunningCommit(NamedTuple):
    """도는 `git commit` 하나와 그 체크아웃(`checkout_of` 의 값)."""

    pid: int
    checkout: str


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분."""

    tool_input: dict[str, object]
    cwd: str


def git_subcommand(argv: Sequence[str]) -> str | None:
    """git 명령 줄에서 전역 옵션을 건너뛴 첫 낱말. 없으면 None."""
    index = 1
    while index < len(argv):
        word = argv[index]
        if not word.startswith("-"):
            return word
        index += 2 if word in _GIT_VALUE_OPTIONS else 1
    return None


def is_git(image: str) -> bool:
    name = image.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return name.removesuffix(".exe") == "git"


def _without_long_prefix(path: str) -> str:
    """`\\\\?\\UNC\\` 와 `\\\\?\\` 머리를 뗀다. PEB 의 작업 디렉터리에 붙어 올 수 있다."""
    if path.startswith("\\\\?\\UNC\\"):
        return "\\\\" + path[len("\\\\?\\UNC\\") :]
    return path.removeprefix("\\\\?\\")


def checkout_of(directory: str) -> str | None:
    """`directory` 에서 위로 올라가 처음 `.git`(디렉터리나 워크트리의 파일)이 있는 폴더. 없으면
    None."""
    try:
        current = Path(os.path.realpath(_without_long_prefix(directory)))
    except (OSError, ValueError):
        return None
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return str(candidate)
    return None


def _same(left: str, right: str) -> bool:
    return os.path.normcase(left) == os.path.normcase(right)


def running_commits(processes: Iterable[Process]) -> list[RunningCommit]:
    """프로세스 가운데 도는 `git commit` 과 그 체크아웃. 자식 git 을 띄운 git(런처)과 체크아웃을
    찾지 못한 것은 뺀다. 런처의 일은 그 자식인 실제 git 이 센다."""
    gits = [process for process in processes if is_git(process.image)]
    launchers = {process.parent for process in gits} & {process.pid for process in gits}
    found: list[RunningCommit] = []
    for process in gits:
        if process.pid in launchers or git_subcommand(process.argv) != "commit":
            continue
        checkout = checkout_of(process.cwd)
        if checkout is not None:
            found.append(RunningCommit(process.pid, checkout))
    return found


def edited_file(tool_input: Mapping[str, object]) -> str | None:
    """편집 도구의 입력에서 고친 파일 경로. Write·Edit 은 `file_path`, NotebookEdit 은
    `notebook_path` 다."""
    for key in ("file_path", "notebook_path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def context_for(file_path: str, commits: Sequence[RunningCommit]) -> str | None:
    """고친 파일의 체크아웃에서 도는 커밋이 있으면 알릴 문장, 없으면 None."""
    checkout = checkout_of(os.path.dirname(os.path.abspath(file_path)))
    if checkout is None:
        return None
    pids = sorted({commit.pid for commit in commits if _same(commit.checkout, checkout)})
    if not pids:
        return None
    return (
        f"방금 고친 `{file_path}` 이 든 체크아웃 `{checkout}` 에서 `git commit`(pid "
        f"{', '.join(map(str, pids))})이 돌고 있다. 그 커밋의 pre-commit 검사는 작업 트리를 "
        "읽어, 도는 동안 바뀐 파일을 쓰다 만 채로 읽거나 그 훅이 고친 것으로 세어 커밋이 실패할 "
        "수 있다(대기열 293). 이 편집은 이미 적용됐다. 커밋이 끝날 때까지 이 체크아웃의 파일을 더 "
        "고치지 않는다. 커밋 전에 스테이지하지 않은 변경이 있었으면 pre-commit 이 그것을 치웠다가 "
        "끝에 되돌리므로, 이 편집은 치운 판 위에 적용됐거나 되돌릴 때 지워졌을 수 있다. 커밋이 "
        "끝나면 이 파일을 다시 읽어 편집이 남았는지 보고, 지워졌으면 다시 적용한다. 이 편집보다 "
        "먼저 시작한 커밋에는 이 편집이 들지 않는다(커밋은 시작할 때 스테이지한 것으로 만든다). "
        "이 세션이 띄운 커밋이면, 실패했을 때 이 편집까지 스테이지해 다시 커밋한다. 이 세션이 "
        "띄운 커밋이 아니면 같은 체크아웃을 쓰는 다른 세션의 것이니 그 커밋을 다시 치지 않는다."
    )


def _is_64bit() -> bool:
    """이 파이썬이 64비트인가. 윈도의 PEB 는 x64 의 자리만 안다."""
    return ctypes.sizeof(ctypes.c_void_p) == 8


def argv_from_cmdline(raw: bytes) -> tuple[str, ...]:
    """`/proc/<pid>/cmdline` 의 낱말. 낱말마다 NUL 로 끝나므로 끝의 NUL 하나만 떼고 빈 낱말은
    지킨다. 빈 낱말을 버리면 `git -C "" commit` 의 `-C` 가 `commit` 을 값으로 먹는다(PR 직전
    `bug-perf-review`)."""
    parts = raw.split(b"\0")
    if parts and parts[-1] == b"":
        parts.pop()
    return tuple(part.decode("utf-8", "replace") for part in parts)


def parent_from_stat(stat: str) -> int:
    """`/proc/<pid>/stat` 의 부모 pid. 이름 칸이 괄호 안에 공백을 품을 수 있어 마지막 `)` 뒤에서
    센다(상태, 부모 pid 차례). 읽지 못하면 0."""
    fields = stat.rpartition(")")[2].split()
    return int(fields[1]) if len(fields) > 1 and fields[1].isdigit() else 0


def _linux_processes() -> list[Process]:
    """`/proc/<pid>/` 에서 이름이 git 인 프로세스의 명령 줄, 작업 디렉터리, 부모 pid. 읽을 수
    없는 프로세스(다른 사용자의 것, 그새 끝난 것)는 건너뛴다."""
    found: list[Process] = []
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        base = f"/proc/{entry}"
        try:
            if Path(f"{base}/comm").read_text(encoding="utf-8", errors="replace").strip() != "git":
                continue
            stat = Path(f"{base}/stat").read_text(encoding="utf-8", errors="replace")
            raw = Path(f"{base}/cmdline").read_bytes()
            cwd = os.readlink(f"{base}/cwd")
        except OSError:
            continue
        parent = parent_from_stat(stat)
        found.append(Process(int(entry), "git", argv_from_cmdline(raw), cwd, parent))
    return found


if sys.platform == "win32":
    _SNAPSHOT_PROCESSES = 0x2  # TH32CS_SNAPPROCESS
    _QUERY_LIMITED = 0x1000  # PROCESS_QUERY_LIMITED_INFORMATION
    _VM_READ = 0x0010  # PROCESS_VM_READ
    _INHERIT_HANDLE = False  # bInheritHandle. 자식 프로세스에 핸들을 물려주지 않는다
    # x64 의 자리: PEB.ProcessParameters, 그 안의 CurrentDirectory.DosPath 와 CommandLine(둘 다
    # UNICODE_STRING)
    _PEB_PARAMS = 0x20
    _PARAMS_CWD = 0x38
    _PARAMS_COMMAND_LINE = 0x70
    _INVALID_HANDLE = ctypes.c_void_p(-1).value

    class _ProcessEntry(ctypes.Structure):
        """PROCESSENTRY32W."""

        _fields_ = [
            ("size", ctypes.c_ulong),
            ("usage", ctypes.c_ulong),
            ("pid", ctypes.c_ulong),
            ("heap", ctypes.c_size_t),
            ("module", ctypes.c_ulong),
            ("threads", ctypes.c_ulong),
            ("parent", ctypes.c_ulong),
            ("priority", ctypes.c_long),
            ("flags", ctypes.c_ulong),
            ("exe", ctypes.c_wchar * 260),
        ]

    class _BasicInformation(ctypes.Structure):
        """PROCESS_BASIC_INFORMATION. `peb` 가 그 프로세스 안의 PEB 주소다."""

        _fields_ = [
            ("exit_status", ctypes.c_void_p),
            ("peb", ctypes.c_void_p),
            ("affinity", ctypes.c_void_p),
            ("priority", ctypes.c_void_p),
            ("pid", ctypes.c_void_p),
            ("parent", ctypes.c_void_p),
        ]

    def _windows_api() -> tuple[ctypes.WinDLL, ctypes.WinDLL, ctypes.WinDLL]:
        """핸들과 포인터가 64비트에서 잘리지 않게 원형을 적은 kernel32, ntdll, shell32."""
        kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        ntdll = ctypes.WinDLL("ntdll")
        shell = ctypes.WinDLL("shell32")
        dword, handle, pointer = ctypes.c_ulong, ctypes.c_void_p, ctypes.c_void_p
        kernel.CreateToolhelp32Snapshot.restype = handle
        kernel.CreateToolhelp32Snapshot.argtypes = [dword, dword]
        kernel.Process32FirstW.argtypes = [handle, ctypes.POINTER(_ProcessEntry)]
        kernel.Process32NextW.argtypes = [handle, ctypes.POINTER(_ProcessEntry)]
        kernel.OpenProcess.restype = handle
        kernel.OpenProcess.argtypes = [dword, ctypes.c_int, dword]
        kernel.CloseHandle.argtypes = [handle]
        kernel.ReadProcessMemory.argtypes = [
            handle,
            pointer,
            pointer,
            ctypes.c_size_t,
            ctypes.POINTER(ctypes.c_size_t),
        ]
        kernel.LocalFree.argtypes = [pointer]
        ntdll.NtQueryInformationProcess.argtypes = [handle, ctypes.c_int, pointer, dword, pointer]
        shell.CommandLineToArgvW.restype = ctypes.POINTER(ctypes.c_wchar_p)
        shell.CommandLineToArgvW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)]
        return kernel, ntdll, shell

    def _git_pids(kernel: ctypes.WinDLL) -> list[tuple[int, int]]:
        """Toolhelp 스냅숏에서 실행 파일 이름이 git 인 프로세스의 (pid, 부모 pid)."""
        snapshot = kernel.CreateToolhelp32Snapshot(_SNAPSHOT_PROCESSES, 0)
        if snapshot is None or snapshot == _INVALID_HANDLE:
            return []
        pids: list[tuple[int, int]] = []
        try:
            entry = _ProcessEntry()
            entry.size = ctypes.sizeof(entry)
            more = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
            while more:
                if is_git(entry.exe):
                    pids.append((int(entry.pid), int(entry.parent)))
                more = kernel.Process32NextW(snapshot, ctypes.byref(entry))
        finally:
            kernel.CloseHandle(snapshot)
        return pids

    def _read_memory(kernel: ctypes.WinDLL, handle: int, address: int, size: int) -> bytes | None:
        buffer = ctypes.create_string_buffer(size)
        got = ctypes.c_size_t()
        if not kernel.ReadProcessMemory(handle, address, buffer, size, ctypes.byref(got)):
            return None
        return buffer.raw if got.value == size else None

    def _unicode_string(kernel: ctypes.WinDLL, handle: int, address: int) -> str | None:
        """그 프로세스의 `address` 에 있는 UNICODE_STRING 의 글."""
        raw = _read_memory(kernel, handle, address, 16)
        if raw is None:
            return None
        length = int.from_bytes(raw[0:2], "little")
        buffer = int.from_bytes(raw[8:16], "little")
        if length == 0 or buffer == 0:
            return None
        text = _read_memory(kernel, handle, buffer, length)
        return text.decode("utf-16-le", errors="replace") if text is not None else None

    def _parameters(kernel: ctypes.WinDLL, ntdll: ctypes.WinDLL, handle: int) -> int | None:
        """그 프로세스의 RTL_USER_PROCESS_PARAMETERS 주소."""
        info = _BasicInformation()
        size = ctypes.sizeof(info)
        status = ntdll.NtQueryInformationProcess(handle, 0, ctypes.byref(info), size, None)
        peb = info.peb
        if status != 0 or not isinstance(peb, int):
            return None
        raw = _read_memory(kernel, handle, peb + _PEB_PARAMS, 8)
        return int.from_bytes(raw, "little") if raw is not None else None

    def _split_command_line(kernel: ctypes.WinDLL, shell: ctypes.WinDLL, line: str) -> list[str]:
        """윈도 명령 줄을 낱말로 나눈다(CommandLineToArgvW)."""
        count = ctypes.c_int()
        array = shell.CommandLineToArgvW(line, ctypes.byref(count))
        if not array:
            return []
        try:
            words = [array[index] for index in range(count.value)]
        finally:
            kernel.LocalFree(array)
        return [word for word in words if isinstance(word, str)]

    def _windows_processes() -> list[Process] | None:
        """이름이 git 인 프로세스마다 PEB 의 작업 디렉터리와 명령 줄. 열지 못하는 프로세스는
        건너뛴다. x64 의 자리만 안다. 32비트 파이썬이면 None 이다."""
        if not _is_64bit():
            return None
        kernel, ntdll, shell = _windows_api()
        found: list[Process] = []
        for pid, parent in _git_pids(kernel):
            handle = kernel.OpenProcess(_QUERY_LIMITED | _VM_READ, _INHERIT_HANDLE, pid)
            if not handle:
                continue
            try:
                parameters = _parameters(kernel, ntdll, handle)
                if parameters is None:
                    continue
                cwd = _unicode_string(kernel, handle, parameters + _PARAMS_CWD)
                line = _unicode_string(kernel, handle, parameters + _PARAMS_COMMAND_LINE)
            finally:
                kernel.CloseHandle(handle)
            if cwd is not None and line is not None:
                argv = tuple(_split_command_line(kernel, shell, line))
                found.append(Process(pid, "git.exe", argv, cwd, parent))
        return found


def scan_processes() -> list[Process] | None:
    """이름이 git 인 프로세스들. 이 OS 에서 볼 수 없거나 읽다 실패하면 None."""
    try:
        if sys.platform == "win32":
            return _windows_processes()
        if sys.platform == "linux":
            return _linux_processes()
    except (OSError, AttributeError, ValueError, ctypes.ArgumentError):
        # DLL 이나 함수를 싣지 못했거나(OSError, AttributeError) 인자를 바꾸지 못했다
        return None
    return None


def main() -> int:
    # stdin 은 바이트로. 이유는 .claude/rules/tools.md(대기열 25).
    payload: HookPayload = json.load(sys.stdin.buffer)
    file_path = edited_file(payload.get("tool_input") or {})
    if file_path is None:
        return 0
    if not os.path.isabs(file_path):
        file_path = os.path.join(payload.get("cwd") or os.getcwd(), file_path)
    # 체크아웃 밖의 파일(스크래치, 메모리)이면 프로세스를 훑지 않는다
    if checkout_of(os.path.dirname(os.path.abspath(file_path))) is None:
        return 0
    processes = scan_processes()
    if not processes:
        return 0
    context = context_for(file_path, running_commits(processes))
    if context is None:
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": context,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
