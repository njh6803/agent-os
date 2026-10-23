"""pid 하나의 명령 줄을 낱말로 읽는다. 다시 풀기 러너가 세션을 끄기 직전에 그 pid 가 자기가 띄운
그 호출인지(명령 줄에 그 호출의 세션 id 가 있는지) 보는 데 쓴다(`tools/rerun_session.py`의 `_ours`,
명세 `.scratch/model-rerun/spec.md` "상한과 끄기").

리눅스는 `/proc/<pid>/cmdline`을, 윈도는 그 프로세스의 PEB 에 든 `CommandLine`을 읽어
`CommandLineToArgvW`로 나눈다. 둘 다 `tools/hook_edit_during_commit.py`의 읽기를 옮긴 사본이다. 훅은
단독 실행 스크립트라 서로와 이 모듈을 import 하지 않는다(`.claude/rules/tools.md`). 두 사본이
같은지는 `tests/tools/test_proc_command_line.py`가 두 파일의 소스를 풀어 댄다. 그 훅이 이름이 git 인
프로세스를 모두 훑는 것과 달리 여기서는 pid 하나만 연다.

러너가 띄운 자식은 거두기 전까지 그 pid 가 다른 프로세스에 가지 않는다. POSIX 는 끝난 자식을 좀비로
남기고, 윈도는 `Popen`이 프로세스 핸들을 쥔다. 그래서 읽은 명령 줄과 끄는 프로세스가 갈리지 않는다.

못 보는 것: 32비트 파이썬의 윈도(PEB 의 x64 자리만 안다), 리눅스와 윈도 밖의 OS, 윈도에서 다른
사용자의 프로세스(열지 못한다), 끝났지만 거두지 않은 좀비(리눅스는 명령 줄이 비었다). 모두 None
이다. 리눅스의 `/proc/<pid>/cmdline`은 `hidepid`로 숨기지 않았으면 다른 사용자의 것도 읽힌다.
러너는 자기가 띄운 자식만 읽으므로 이 갈래를 쓰지 않는다.
"""

from __future__ import annotations

import ctypes
import sys
from collections.abc import Callable
from pathlib import Path

CommandLineReader = Callable[[int], tuple[str, ...] | None]


def argv_from_cmdline(raw: bytes) -> tuple[str, ...]:
    """`/proc/<pid>/cmdline`의 낱말. 낱말마다 NUL 로 끝나므로 끝의 NUL 하나만 떼고, 명령 줄을
    그대로 옮기려고 빈 낱말(`""`로 넘긴 인자)도 지킨다."""
    parts = raw.split(b"\0")
    if parts and parts[-1] == b"":
        parts.pop()
    return tuple(part.decode("utf-8", "replace") for part in parts)


def _linux_command_line(pid: int) -> tuple[str, ...] | None:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:  # 없는 pid, 다른 사용자의 프로세스
        return None
    return argv_from_cmdline(raw) or None


if sys.platform == "win32":
    _QUERY_LIMITED = 0x1000  # PROCESS_QUERY_LIMITED_INFORMATION
    _VM_READ = 0x0010  # PROCESS_VM_READ
    _INHERIT_HANDLE = False  # bInheritHandle. 자식 프로세스에 핸들을 물려주지 않는다
    # x64 의 자리: PEB.ProcessParameters, 그 안의 CommandLine(UNICODE_STRING)
    _PEB_PARAMS = 0x20
    _PARAMS_COMMAND_LINE = 0x70

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

    def _read_memory(kernel: ctypes.WinDLL, handle: int, address: int, size: int) -> bytes | None:
        buffer = ctypes.create_string_buffer(size)
        got = ctypes.c_size_t()
        if not kernel.ReadProcessMemory(handle, address, buffer, size, ctypes.byref(got)):
            return None
        return buffer.raw if got.value == size else None

    def _unicode_string(kernel: ctypes.WinDLL, handle: int, address: int) -> str | None:
        """그 프로세스의 `address`에 있는 UNICODE_STRING 의 글."""
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

    def _windows_command_line(pid: int) -> tuple[str, ...] | None:
        """x64 의 자리만 안다. 32비트 파이썬이면 None 이다."""
        if ctypes.sizeof(ctypes.c_void_p) != 8:
            return None
        kernel, ntdll, shell = _windows_api()
        handle = kernel.OpenProcess(_QUERY_LIMITED | _VM_READ, _INHERIT_HANDLE, pid)
        if not handle:
            return None
        try:
            parameters = _parameters(kernel, ntdll, handle)
            if parameters is None:
                return None
            line = _unicode_string(kernel, handle, parameters + _PARAMS_COMMAND_LINE)
        finally:
            kernel.CloseHandle(handle)
        if line is None:
            return None
        return tuple(_split_command_line(kernel, shell, line)) or None


def command_line(pid: int) -> tuple[str, ...] | None:
    """그 pid 의 명령 줄 낱말. 0 이하의 pid, 없는 pid, 읽지 못한 것(모듈 독스트링의 못 보는 것)은
    None 이다."""
    if pid <= 0:
        return None
    try:
        if sys.platform == "win32":
            return _windows_command_line(pid)
        if sys.platform == "linux":
            return _linux_command_line(pid)
    except (OSError, AttributeError, ValueError, OverflowError, ctypes.ArgumentError):
        # DLL 이나 함수를 싣지 못했거나(OSError, AttributeError) 인자를 바꾸지 못했다
        return None
    return None
