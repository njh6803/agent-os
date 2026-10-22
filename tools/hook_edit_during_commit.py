"""PreToolUse 훅(Write|Edit|NotebookEdit). 고칠 파일이 든 체크아웃에 `git commit` 이 도는 중이면 그
편집을 막는다. 막는 대상은 커밋이 도는 줄 모르고 내는 편집(실수)이다. 일부러 돌아가는 길은 막지
않는다(못 보는 것의 셸 편집).

왜. pre-commit 의 검사는 작업 트리를 읽는다. 커밋이 도는 동안 파일을 고치자 pytest 가 줄을 감다 만
순간의 파일을 읽었고, pre-commit 은 훅이 도는 사이 바뀐 파일을 그 훅이 고친 것으로 세어 커밋이
실패했다(대기열 293. 일지 2026-10-06-09 와 2026-10-16-21). 이 저장소의 커밋은 pre-commit 이 길어
백그라운드로 돌기 쉽고, 그동안 다음 편집을 시작하기 쉽다. 커밋 전에 스테이지하지 않은 변경이
있었으면 더 나쁘다. pre-commit 은 그 변경을 치우고(`git checkout -- .`) 훅을 돈 뒤 패치를
되돌리는데, 되돌리기가 충돌하면 작업 트리를 다시 치우고 패치만 얹어 그 사이의 편집이
지워진다(pre-commit 4.6.2 의 `staged_files_only.py` 를 읽었다). 첫 판은 실패가 시끄러운 쪽(커밋이
빨갛다)이 있어 막지 않고 PostToolUse 에서 알렸다. 알림은 편집이 끝난 뒤에 와서, 그 편집으로 커밋이
"files were modified by this hook" 으로 실패한 일이 다시 났다(대기열 412, 293 의 4회차. 일지
2026-10-21-14). 그래서 편집 전에 막는다(`.claude/rules/tools.md` 의 계기·막는 훅 가름).

왜 프로세스인가. 대기열 293 의 행은 그 체크아웃의 git 디렉터리에 `index.lock` 이 있는지로 보자고
했다. 탐침으로 재니(`.scratch/harness/probes/commit_lock/probe.py`, git 2.32) `git add` 뒤의 보통
커밋은 pre-commit·commit-msg 훅이 도는 동안 `index.lock` 이 없었다. 잠금은 `-a` 와 경로를 준
커밋에만 있었다. 이 저장소의 커밋은 앞의 꼴이라 잠금으로는 거의 못 본다. 그래서 도는 `git commit`
프로세스를 찾는다.

판정. 고칠 파일(`file_path`, NotebookEdit 은 `notebook_path`)의 폴더에서 위로 올라가 처음
`.git`(디렉터리나 워크트리의 파일)이 있는 폴더를 그 체크아웃으로 본다. 프로세스 가운데 이름이
git 인 것의 명령 줄에서 전역 옵션(`-C <경로>`, `-c <설정>` 등)을 건너뛴 첫 낱말이 `commit` 이면,
그 커밋이 도는 작업 트리 안의 폴더(`commit_directory`)에서 같은 방법으로 체크아웃을 찾는다. 둘이
같으면 막는다. 주 체크아웃 안의 워크트리(`.claude/worktrees/<이름>`)는 자기 `.git` 파일이 있어 다른
체크아웃이다. 커밋이 도는 동안의 편집마다 막는다.

작업 트리 안의 폴더는 작업 디렉터리만으로 정하지 않는다. 실제 git 은 하위 폴더에서 쳤든 밖에서
`-C`(상대 경로 포함)·`--git-dir`·`--work-tree` 로 쳤든 작업 디렉터리를 그 작업 트리 안으로
옮긴다(tests/tools 의 실제 프로세스 시험, git 2.32). 다만 옮기기 전에는 띄운 폴더에 있고, 윈도 git
의 런처(`cmd\\git.exe`, `bin\\git.exe`)는 띄운 폴더를 작업 디렉터리로 쥔 채 같은 명령 줄로 살아
실제 git 을 자식으로 띄운다. 작업 디렉터리만 본 판은 다른 저장소에 친 `git -C <임시> commit` 을
띄운 폴더의 커밋으로 셌다. 부하 pytest 가 임시 저장소에 친 커밋을 이 체크아웃의 커밋으로 두 번
알렸고(대기열 368), 탐침(`.scratch/harness/probes/edit_during_commit_launcher.py`)으로 재니 런처로
친 회차는 모두, 실제 git 을 바로 띄운 회차도 10회차 가운데 부하 없이 절대 경로 5·상대 경로 3, 부하
아래 9·9에서 그 순간이 훑혔다. 그래서
전역 옵션의 `-C` 를 차례로 풀고 마지막 `--work-tree` 를 그 위에 푼다. 절대 경로면 그 자리로
바꾼다. 옮기기 전과 뒤가 같은 자리를 가리킨다. 상대 경로는 런처면 띄운 폴더에서 풀고, 실제 git
이면 앞선 절대 경로가 자리를 정했을 때만 얹는다. 이미 옮긴 작업 디렉터리에 상대 경로를 한 번 더
얹으면 놓친다(PR 직전 `bug-perf-review` 가 실제 프로세스로 재현했다). 런처는 실행 파일의 자리로
알아본다(`is_launcher`). `cmd`·`bin` 의 `git.exe` 가운데 곁의 `mingw64`(`mingw32`, `clangarm64`)
아래 실제 git 이 있는 것이다. 자식 git 을 띄운 git 은 세지 않는다(`running_commits`). 그 일은
자식이 세고, 런처가 띄운 자식의 상대 경로는 런처의 작업 디렉터리에서 푼다. 자식은 거기서 시작해
같은 명령 줄을 받으므로 옮겼든 옮기기 전이든 같은 자리다. 고친 판으로 같은 탐침을 30회차씩 다시
재니 절대 경로의 180회차는 거짓 알림이 0 이었고, 런처로 친 상대 경로의 120회차는 둘이었다. 둘 다
자식이 끝난 뒤의 런처였고 원인은 가르지 않았다(그 탐침의 README 행). 경로는
`os.path.realpath` 로 펴서 대고, 윈도에서는 대소문자를 가리지 않는다. 윈도는 Toolhelp 스냅숏으로
프로세스 이름을 훑고 git 만 열어 실행 파일의 전체 경로와 PEB 의 작업 디렉터리와 명령 줄을 읽는다.
PEB 를 읽는 자리는 `tools/tidy_checkouts.py` 와 같고, 훅은 단독 실행 스크립트라 그 모듈을 import
하지 않고 옮겨 적었다(`.claude/rules/tools.md`). 리눅스는 `/proc/<pid>/` 의 `comm`·`stat`(부모
pid)·`cmdline`·`cwd` 를 읽는다. 읽다 실패하면 막지 않는다(fail-open).

못 보는 것.
- 커밋이 아닌 검사(`uv run pre-commit run`, `uv run pytest`)가 도는 동안의 편집. git 의 `commit`
  만 센다. git 을 감싸는 실행 파일(`hub commit`)은 세지 않고 그 아래에서 도는 git 이 센다.
- git 별칭으로 친 커밋(`git ci`). 명령 줄의 하위 명령이 `commit` 이 아니라 세지 않는다.
- `.git` 이 없는 작업 트리(바깥 저장소를 `--git-dir` 로 쓰는 꼴). 그 커밋도 그 안의 편집도
  체크아웃을 찾지 못한다.
- 셸로 고친 파일(`sed -i`, `>`). 이 훅은 편집 도구 셋에만 붙고 그 입력에는 경로 칸이 없다.
  일부러 돌아가는 대표 길이다.
- 상대 경로 `-C`·`--work-tree` 로 바로 띄운 실제 git(Git Bash 의 `git` 이 이 꼴이다)이 작업
  디렉터리를 옮기기 전의 순간. 이미 옮겼는지 알 수 없어 작업 디렉터리를 믿고, 띄운 폴더의 편집을
  막는다(거짓 양성. 고친 판의 탐침 30회차에서 부하 없이 17, 부하 아래 30. 그 앞 판의 60회차에서는
  35·57). 실행 파일의 자리를 읽지 못한 런처와 그 자식도 실제 git 으로 보아 같다. 런처로 친 상대
  경로도 고친 판의 120회차 가운데 둘(자식이 끝난 뒤의 런처)에서 막았고 원인은 가르지 않았다. 그
  순간은 git 이 뜬 직후라 짧다고 보아(어림. 창의 길이는 재지 않았다), 막는 이유는 커밋을 띄우지 않은
  세션에 같은 편집을 한 번 다시 하라고 한다. 환경 변수(`GIT_WORK_TREE`)로 준 작업 트리는 읽지
  않는다.
- 윈도와 리눅스 밖의 OS, 32비트 파이썬. 프로세스를 읽지 않아 막지 않는다(PEB 는 x64 의 자리만
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

# Git for Windows 에서 실제 git 이 든 폴더. 런처(`cmd`, `bin`)의 곁에 있다.
_MINGW_FOLDERS = ("mingw64", "mingw32", "clangarm64")


class Process(NamedTuple):
    """프로세스 하나. `image` 는 실행 파일(윈도는 읽었으면 전체 경로), `argv` 는 명령 줄을 나눈
    낱말, `cwd` 는 작업 디렉터리, `parent` 는 부모 pid(모르면 0)다."""

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


def global_options(argv: Sequence[str]) -> list[tuple[str, str]]:
    """git 명령 줄의 하위 명령 앞에서 값을 먹는 전역 옵션의 (옵션, 값). 따로 쓴 꼴(`-C <경로>`)과
    붙여 쓴 꼴(`--work-tree=<경로>`)을 모두 푼다."""
    found: list[tuple[str, str]] = []
    index = 1
    while index < len(argv):
        word = argv[index]
        if not word.startswith("-"):
            break
        if word in _GIT_VALUE_OPTIONS:
            if index + 1 < len(argv):
                found.append((word, argv[index + 1]))
            index += 2
            continue
        name, equals, value = word.partition("=")
        if equals and name in _GIT_VALUE_OPTIONS:
            found.append((name, value))
        index += 1
    return found


def is_git(image: str) -> bool:
    name = image.replace("\\", "/").rsplit("/", 1)[-1].lower()
    return name.removesuffix(".exe") == "git"


def is_launcher(image: str) -> bool:
    """윈도 git 의 런처인가. `cmd`·`bin` 폴더의 `git.exe` 가운데 곁의 `mingw64`(`mingw32`,
    `clangarm64`) 아래 실제 git 이 있는 것이다. 이름만 읽은 실행 파일(`git.exe`, 리눅스의 `git`)은
    자리를 몰라 런처로 보지 않는다."""
    folder, _, name = image.replace("\\", "/").rpartition("/")
    install, _, leaf = folder.rpartition("/")
    if name.lower() != "git.exe" or leaf.lower() not in ("cmd", "bin") or not install:
        return False
    return any(
        os.path.isfile(os.path.join(install, mingw, "bin", "git.exe")) for mingw in _MINGW_FOLDERS
    )


def commit_directory(process: Process) -> str:
    """그 커밋이 도는 작업 트리 안의 폴더. 전역 옵션의 `-C` 를 차례로 풀고 마지막 `--work-tree` 를
    그 위에 푼다. 절대 경로면 그 자리로 바꾸고, 상대 경로는 런처면 띄운 폴더에서 풀고 실제 git 이면
    앞선 절대 경로가 자리를 정했을 때만 얹는다(이미 옮긴 작업 디렉터리에 다시 얹지 않게)."""
    directory = process.cwd
    anchored = is_launcher(process.image)
    options = global_options(process.argv)
    moves = [value for option, value in options if option == "-C"]
    trees = [value for option, value in options if option == "--work-tree"]
    for value in [*moves, *trees[-1:]]:
        if not value:
            continue
        if os.path.isabs(value):
            directory, anchored = value, True
        elif anchored:
            directory = os.path.join(directory, value)
    return directory


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
    찾지 못한 것은 뺀다. 런처의 일은 그 자식인 실제 git 이 센다. 자식을 띄우기 전과 자식이 끝난 뒤의
    런처는 `commit_directory` 가 띄운 폴더 대신 명령 줄의 자리로 센다. 런처가 띄운 자식은 런처의
    작업 디렉터리에서 시작해 같은 명령 줄을 받으므로, 옮겼든 옮기기 전이든 런처의 작업 디렉터리에서
    푼다."""
    gits = [process for process in processes if is_git(process.image)]
    by_pid = {process.pid: process for process in gits}
    launchers = {process.parent for process in gits} & set(by_pid)
    found: list[RunningCommit] = []
    for process in gits:
        if process.pid in launchers or git_subcommand(process.argv) != "commit":
            continue
        anchor = by_pid.get(process.parent)
        resolved = process
        if anchor is not None and is_launcher(anchor.image):
            resolved = process._replace(image=anchor.image, cwd=anchor.cwd)
        checkout = checkout_of(commit_directory(resolved))
        if checkout is not None:
            found.append(RunningCommit(process.pid, checkout))
    return found


def edited_file(tool_input: Mapping[str, object]) -> str | None:
    """편집 도구의 입력에서 고칠 파일 경로. Write·Edit 은 `file_path`, NotebookEdit 은
    `notebook_path` 다."""
    for key in ("file_path", "notebook_path"):
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def deny_reason(file_path: str, commits: Sequence[RunningCommit]) -> str | None:
    """고칠 파일의 체크아웃에서 도는 커밋이 있으면 막는 이유, 없으면 None."""
    checkout = checkout_of(os.path.dirname(os.path.abspath(file_path)))
    if checkout is None:
        return None
    pids = sorted({commit.pid for commit in commits if _same(commit.checkout, checkout)})
    if not pids:
        return None
    return (
        f"`{file_path}` 이 든 체크아웃 `{checkout}` 에서 `git commit`(pid "
        f"{', '.join(map(str, pids))})이 돌고 있어 이 편집을 막았다. 그 커밋의 pre-commit "
        "검사는 작업 트리를 읽어, 도는 동안 바뀐 파일을 쓰다 만 채로 읽거나 그 훅이 고친 것으로 "
        "세어 커밋이 실패한다(대기열 293·412). 커밋이 끝난 뒤 같은 편집을 다시 한다. 이 세션이 "
        "백그라운드로 띄운 커밋이면 그 끝 알림을 기다린다. 이 세션이 띄운 커밋이 없으면 같은 "
        "편집을 한 번 다시 한다. 다른 프로세스의 git 이 작업 폴더를 옮기기 전의 순간을 훑었을 수 "
        "있다(이 훅의 못 보는 것). 다시 막히면 다른 세션의 커밋이 이 체크아웃에서 도는 것이라 "
        "끝나기를 기다린다. 기다리는 동안 이 체크아웃 밖(세션 스크래치패드)의 파일은 고칠 수 "
        "있다. 셸로 파일을 고쳐 이 막음을 돌아가지 않는다."
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
    _IMAGE_PATH_CHARS = 32768  # 윈도 긴 경로의 상한(글자)
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
        kernel.QueryFullProcessImageNameW.argtypes = [
            handle,
            dword,
            ctypes.c_wchar_p,
            ctypes.POINTER(dword),
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

    def _image_path(kernel: ctypes.WinDLL, handle: int) -> str | None:
        """그 프로세스의 실행 파일 전체 경로. 런처를 알아보는 데 쓴다(`is_launcher`)."""
        size = ctypes.c_ulong(_IMAGE_PATH_CHARS)
        buffer = ctypes.create_unicode_buffer(_IMAGE_PATH_CHARS)
        if not kernel.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size)):
            return None
        return buffer.value or None

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
        """이름이 git 인 프로세스마다 실행 파일의 전체 경로(읽지 못하면 `git.exe`)와 PEB 의 작업
        디렉터리와 명령 줄. 열지 못하는 프로세스는 건너뛴다. x64 의 자리만 안다. 32비트 파이썬이면
        None 이다."""
        if not _is_64bit():
            return None
        kernel, ntdll, shell = _windows_api()
        found: list[Process] = []
        for pid, parent in _git_pids(kernel):
            handle = kernel.OpenProcess(_QUERY_LIMITED | _VM_READ, _INHERIT_HANDLE, pid)
            if not handle:
                continue
            try:
                image = _image_path(kernel, handle) or "git.exe"
                parameters = _parameters(kernel, ntdll, handle)
                if parameters is None:
                    continue
                cwd = _unicode_string(kernel, handle, parameters + _PARAMS_CWD)
                line = _unicode_string(kernel, handle, parameters + _PARAMS_COMMAND_LINE)
            finally:
                kernel.CloseHandle(handle)
            if cwd is not None and line is not None:
                argv = tuple(_split_command_line(kernel, shell, line))
                found.append(Process(pid, image, argv, cwd, parent))
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
    reason = deny_reason(file_path, running_commits(processes))
    if reason is None:
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
