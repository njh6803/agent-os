"""Ctrl-C 시험이 부하에서 왜 빨개지는지 가른다(대기열 306, ADR 0035).

대상은 `tests/tools/test_mutate.py` 의
`test_실제_러너는_기다리는_동안_Ctrl_C_가_나도_손자_프로세스까지_끝낸다` 다. 그 시험은 실제 러너
(`tools.mutate.run_command`)가 손자를 띄운 자식을 기다리는 동안 Ctrl-C(`KeyboardInterrupt`)를 넣고,
러너가 돌아온 뒤 손자의 기록 파일을 본다. 고치기 전 판(`88fed982`)은 돌아온 직후 0.5초 동안 자라는지
(`_뛰는지`)를 한 번 봤고, pre-commit 의 pytest 에서 다섯 번 빨갰다. 일지 2026-10-15-15 의 8항,
2026-10-16-35, 2026-10-16-60 은 pytest 를 한 프로세스로 돌던 때이고, 2026-10-17-10, 2026-10-17-12 는
xdist 로 나눠 돈 때다(ADR 0035). 남은 모양은 2026-10-15-15 의 "심장 박동 파일이 끊은 뒤에도 뛰었다"
와 2026-10-17-10 의 `_뛰는지(심장)` 가 참이었다는 것뿐이다. 고친 판은 기한 안에 1초 동안 자라지
않는지 (`_멈추는지`)를 거듭 견준다.

시험 함수를 그대로 N 번 부른다. 시험 모듈을 경로로 불러 함수만 부르므로 pytest 의 수집은 빠지고,
`tmp_path` 는 회차마다 새 임시 폴더, `monkeypatch` 는 `pytest.MonkeyPatch.context()` 다.
`--test-file` 을 여러 번 주면 그 파일들을 회차마다 번갈아 불러 같은 부하를 받게 한다. 고치기 전 판은
`git show <커밋>:tests/tools/test_mutate.py` 를 저장소 밖의 `.py` 파일로 옮겨 준다.

계측은 시험과 같은 프로세스에서 `time.perf_counter` 한 축으로 한다.

- 러너(시험 모듈의 `run_command`)를 감싸 손자의 기록 파일 경로를 받고, 지키는 스레드를 띄운다. 그
  스레드는 손자가 남기는 pid 파일을 읽어 그 프로세스의 핸들(`SYNCHRONIZE`)을 열고, 10ms 마다 기록
  파일의 크기와 핸들이 신호를 받았는지(프로세스가 끝났는지, `WaitForSingleObject(handle, 0)`)를
  남긴다. pid 가 다시 쓰여도 연 핸들은 그 프로세스를 가리킨다.
- 시험이 Ctrl-C 를 넣는 조건(`_첫_기다림을_끊는다` 의 `준비됐다`)에, 지키는 스레드가 살아 있고 기록
  파일이 비지 않은 손자를 한 번 봤다는 것을 더한다. 부하에서 그 스레드가 첫 표본을 뜨기 전에 Ctrl-C
  가 나 측정이 아닌 회차가 60번 가운데 12번이었다(첫 판, `before_b16_first.json`). Ctrl-C 가 그만큼
  늦게 날 뿐 판정하는 부분은 그대로다.
- `subprocess.run` 을 감싸 `taskkill` 호출마다 시작·끝, 종료 코드, 출력(OEM 코드 페이지)을 남긴다.
  출력에서 손자 pid 의 줄을 따로 꺼낸다(`grandchild_kill`, 이 PC 에서 본 한국어와 영어 출력
  모양에 기댄다. pytest 부하 두 벌을 건 판에서 영어 출력이 섞여, 한국어만 읽던 판이 그 회차를
  `(없음)` 으로 셌다).
  첫 판에서 종료 코드는 0 말고도 128·255 가 섞였고, 오류 줄은 손자가 아니라 이미 끝난 런처와 자식의
  것(`실행 중인 작업 인스턴스가 없습니다`, `시도한 작업은 지원하지 않습니다`)이었다. venv 의
  `python.exe` 가 런처라 트리는 자식 런처, 자식, 손자 런처, 손자의 네 층이다.
- 러너가 Ctrl-C(`KeyboardInterrupt`)를 올린 시각과, 시험의 판정 함수(`JUDGES` 의 이름 가운데 있는
  것)가 불린 시각, 걸린 시간, 결과를 남긴다.
- 러너를 부른 시각과 첫 기다림을 끊은 시각(위 조건이 처음 참이 된 때)을 남긴다. 부른 때부터
  끊기까지(`startup_ms`)는 자식과 손자를 띄우는 시간에 위에서 더한 조건의 몫이 얹힌 것이고, 부른
  때부터 러너가 예외를 올리기까지(`call_to_raise_ms`)는 거기에 끝내기를 더한 것이다. 같은 자식과
  손자를 쓰는 시간 제한 시험(`test_실제_러너는_시간_제한을_넘기면_…`)의 걸린 시간은 이 값에 끝낸 뒤
  남은 출력을 읽고 자식을 기다리는 몫을 더한 것이라(그 몫은 재지 않았다), 그 시험이 고치기 전에 둔
  상한(`OLD_BOUND_SECONDS`)을 이 값이 넘은 회차를 센다. 그 시험은 pytest 세 벌을 건
  `open_session_pattern_timed.py` 의 부하 pytest 에서 13.6초로 한 번 빨갰다.
- 시험이 끝난 뒤에도 러너가 돌아온 때(`taskkill` 이 더 늦게 돌아왔으면 그때)부터 `AFTER_SECONDS` 가
  지날 때까지 더 지킨다. 그때도 손자가 살아 있으면 지키는 스레드가 연 핸들을 쥔 채(쥔 동안 그 pid 는
  다시 쓰이지 않는다) 그 pid 의 명령줄을 읽고, 이 회차의 기록 파일 경로가 있을 때만 그 핸들로 끝낸다
  (`.claude/rules/probes.md` 의 프로세스를 끄는 탐침). 명령줄은 감싸기 전의 `subprocess.run` 으로
  PowerShell 의 `Get-CimInstance Win32_Process` 를 불러 읽어 기록에 들지 않는다. 끄지 않았으면 그
  까닭을 회차 행의 `cleanup` 에 남긴다.

갈래. 시험이 보는 것은 러너가 돌아온 뒤라 그 시각을 기준으로 한다. 손자가 `taskkill` 이 돌아온
뒤에도 살아 있었는지(`alive_after_kill`)는 따로 적는다. 손자가 쓰는 동안 기록 파일이 가장 오래
자라지 않은 틈(`max_growth_gap_ms`)과 0.5초를 넘은 틈의 수(`long_growth_gaps`)도 적는다. 고친 판정은
1초 동안 자라지 않으면 끝났다고 읽으므로, 이 틈이 1초에 닿으면 살아 있는 손자를 끝났다고 읽는다(거짓
초록). `late-write` 의 덧쓰기는 손자가 끝난 뒤의 자람이라 그 대조의 틈은 이 뜻이 아니다.
`max_growth_gap_ms` 는 러너를 부른 때부터 지키기를 마칠 때까지를 모두 세므로, 판정이 도는 동안의
틈은 따로 낸다. 판정 `_멈추는지` 가 도는 동안 기록 파일이 가장 오래 자라지 않은
구간(`judge_quiet_ms`, 판정의 시작과 끝도 구간의 끝으로 센다)과, 같은 동안 지키는 스레드가 표본을
뜨지 못한 가장 긴 구간(`judge_sample_gap_ms`)이다. 앞의 것만 길면 손자가 실제로 쓰지 않은 것이고,
둘이 함께 길면 지키는 스레드가 굶어 자람을 보지 못한 것이다. 앞의 것이 1초를 넘은 회차 수는
`judge_quiet_over_window`, 지키는 내내의 표본 간격의 최댓값은 `max_sample_gap_ms` 다.

- A. 끝내기가 늦다: 러너가 돌아온 뒤에도 핸들이 신호를 받지 않은 표본이 있고, 지키는 동안 끝났다.
- B. 끝내지 못했다: 지키는 동안 끝까지 핸들이 신호를 받지 않았다.
- C. 끝난 뒤에 자랐다: 러너가 돌아온 뒤의 표본에서 손자가 모두 끝나 있는데 기록 파일이 자랐다.
- ok: 셋 다 아니다(돌아왔을 때 이미 끝났고, 그 뒤 자라지 않았다).

크기를 읽지 못한 표본(-1)은 자람과 틈의 셈에서 뺀다.

고친 길을 지났다는 표지는 둘이다. A 는 손자가 돌아온 뒤에도 살았다는 것뿐이라 돌아온 뒤 자라지 않은
A 회차는 옛 판정도 통과한다. 그래서 판마다 러너가 돌아온 뒤 기록 파일이 자랐는데 통과한 회차
(`passed_with_growth_after_return`)와, 판정 `_멈추는지` 가 `PAST_FIRST_WINDOW_SECONDS` 넘게 걸려
첫 1초 창에서 자람을 보고 다음 창으로 간 뒤 통과한 회차(`passed_past_first_window`)를 센다.

양성 대조는 `--control` 셋이다. `no-tree` 는 `taskkill` 에서 `/T` 를 빼 손자를 남기므로 B 가 나와야
하고, 고친 판이 통과하면 거짓 초록이다. `late-kill` 은 `taskkill` 을 `LATE_SECONDS` 뒤에 따로 도는
스레드에 맡기고 곧바로 성공을 돌려주며, 그동안 루트가 먼저 끝나 트리를 잃지 않게 `Popen.kill` 을
막는다. 손자는 러너가 돌아온 뒤에 끝나므로 A 가 나와야 한다. `late-write` 는 러너가 Ctrl-C 를 올리고
`LATE_SECONDS` 뒤에 프로브가 기록 파일에 한 바이트를 덧쓴다. 손자가 이미 끝났으면 C 가 나와야 한다.
뒤의 둘은 돌아온 뒤 기록 파일을 자라게 하므로, 고치기 전 판은 빨갛고 고친 판은 다음 창으로 가서
통과해야 한다.

표지(회차가 측정인지): 부하 프로세스가 회차가 끝날 때까지 살아 있었다, 러너가 Ctrl-C 를
올렸다(시험이 러너를 끊은 길을 지났다), `taskkill` 이 한 번 돌아왔다, 그 호출이 시작되기 전에 손자가
살아 있고 기록 파일이 비지 않은 표본이 있다. 표지가 없는 회차는 측정이 아니라 까닭과 함께 따로 세고,
하나라도 있으면 종료 코드가 1 이다. `--pytest-loads` 는 회차 수를 부하 pytest 가 끝날 때보다 길게
주면 (`mutate_ctrl_c_all.sh` 의 200) 부하가 끝난 회차가 하나 있어 1 로 끝난다.

부하는 앞선 `filesystem_read_retry.py` 와 같다. `--burners K` 는 쉬지 않고 도는 파이썬 프로세스 K
개, `--pytest-loads P` 는 이 저장소의 전체 pytest 를 xdist 8개로 도는 것 P 벌이다. 이 PC 는 논리 CPU
16개다. `--out` 을 주면 pytest 부하 i 의 출력을 `<out 의 이름>_pytest<i>.txt` 에 남기고, 그 부하가
돈 이 저장소의 시험 가운데 실패한 것을 요약의 `pytest_load_failed` 에 싣는다.

돌리는 법: 저장소 루트에서 `uv run python <이 파일> N [--burners K] [--pytest-loads P]
[--control no-tree|late-kill|late-write] [--test-file <경로>]… --out <JSON>`. 이 파일은
`.scratch/harness/probes/precommit_xdist/mutate_ctrl_c.py` 다. 표준 출력에는 회차별 행을 뺀 요약 한
줄을 낸다. 윈도에서만 돈다(핸들과 `taskkill`).

못 보는 것: pytest 와 xdist 가 얹는 것, 실제 pre-commit 부하의 모양, 다른 기계, POSIX 의
`killpg` 길. 핸들이 신호를 받은 시각은 표본 간격(부하에서는 더 길다)만큼 늦게 보인다.
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
import importlib.util
import json
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))  # 시험 모듈이 `tools.mutate` 를 부른다

TEST_FILE = ROOT / "tests" / "tools" / "test_mutate.py"
TEST_NAME = "test_실제_러너는_기다리는_동안_Ctrl_C_가_나도_손자_프로세스까지_끝낸다"
# 판마다 판정 함수의 이름이 다를 수 있다. 있는 것만 감싼다.
JUDGES = ("_뛰는지", "_멈추는지", "_자라는지")
SAMPLE_SECONDS = 0.01
AFTER_SECONDS = 5.0
LATE_SECONDS = 0.3
# `_멈추는지` 는 첫 1초 창에서 멈췄으면 약 1초에, 자람을 봐 다음 창으로 가면 약 2초 넘어 돌아온다
PAST_FIRST_WINDOW_SECONDS = 1.5
LONG_GAP_SECONDS = 0.5
OLD_BOUND_SECONDS = 8  # 시간 제한 시험이 고치기 전에 러너 호출 전체에 둔 상한
BURNER = "while True:\n    pass\n"
LOAD_WAIT_SECONDS = 900  # 출력을 남기는 pytest 부하가 끝나기를 기다리는 상한
SYNCHRONIZE = 0x00100000
PROCESS_TERMINATE = 0x0001
WAIT_TIMEOUT = 0x102
# 회차 안에서 감싸기 전의 것. 뒷정리와 부하의 `taskkill` 이 기록에 들지 않게 한다.
RUN = subprocess.run


def _kernel() -> ctypes.WinDLL:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    handle = ctypes.c_void_p
    dword = ctypes.c_uint32
    kernel.OpenProcess.restype = handle
    kernel.OpenProcess.argtypes = [dword, ctypes.c_int, dword]
    kernel.WaitForSingleObject.restype = dword
    kernel.WaitForSingleObject.argtypes = [handle, dword]
    kernel.TerminateProcess.restype = ctypes.c_int
    kernel.TerminateProcess.argtypes = [handle, ctypes.c_uint]
    kernel.CloseHandle.argtypes = [handle]
    return kernel


KERNEL = _kernel()


@dataclass
class Trace:
    """한 회차의 기록. 표본은 (시각, 기록 파일 크기, 손자가 살아 있나)다."""

    heartbeat: Path | None = None
    pid: int | None = None
    handle: int | None = None  # 지키는 스레드가 연 손자의 핸들. `_finish` 가 닫는다
    open_failed: bool = False
    cleanup: str | None = None
    samples: list[tuple[float, int, bool]] = field(default_factory=list)
    kills: list[dict[str, object]] = field(default_factory=list)
    called_at: float | None = None
    cut_at: float | None = None
    raised_at: float | None = None
    judges: list[tuple[str, float, float, bool]] = field(default_factory=list)
    stop: threading.Event = field(default_factory=threading.Event)
    ready: threading.Event = field(default_factory=threading.Event)
    threads: list[threading.Thread] = field(default_factory=list)


def _read_pid(path: Path) -> int | None:
    try:
        return int(path.read_text())
    except (OSError, ValueError):  # 아직 없거나 쓰는 중이다
        return None


def _open_grandchild(trace: Trace, heartbeat: Path) -> int | None:
    """pid 파일이 생기기를 기다려 그 프로세스의 핸들을 연다."""
    while not trace.stop.is_set():
        pid = _read_pid(heartbeat.with_suffix(".pid"))
        if pid is None:
            time.sleep(0.005)
            continue
        trace.pid = pid
        handle = KERNEL.OpenProcess(SYNCHRONIZE | PROCESS_TERMINATE, 0, pid)
        if not handle:
            trace.open_failed = True
            return None
        trace.handle = int(handle)
        return trace.handle
    return None


def _size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return -1


def _watch(trace: Trace, heartbeat: Path) -> None:
    handle = _open_grandchild(trace, heartbeat)
    if handle is None:
        return
    # 핸들은 닫지 않는다. `_finish` 가 쥔 채 남은 손자를 끝내고 닫는다
    while not trace.stop.is_set():
        now = time.perf_counter()
        alive = KERNEL.WaitForSingleObject(handle, 0) == WAIT_TIMEOUT
        size = _size(heartbeat)
        trace.samples.append((now, size, alive))
        if alive and size > 0:
            trace.ready.set()
        time.sleep(SAMPLE_SECONDS)


def _oem(data: object) -> str:
    if isinstance(data, bytes):
        return data.decode("oem", "replace")
    return str(data)


def _record_kill(trace: Trace, started: float, result: subprocess.CompletedProcess[bytes]) -> None:
    trace.kills.append(
        {
            "started": started,
            "ended": time.perf_counter(),
            "code": result.returncode,
            "output": (_oem(result.stdout) + _oem(result.stderr)).strip()[-600:],
        }
    )


def _patch_kill(patch: pytest.MonkeyPatch, trace: Trace, control: str) -> None:
    """`taskkill` 을 감싼다. `control` 이 양성 대조를 고른다(모듈 독스트링)."""
    original = RUN

    def traced(args: Sequence[str], *rest: object, **options: object) -> object:
        if not (isinstance(args, list) and args and args[0] == "taskkill"):
            return original(args, *rest, **options)
        argv = [arg for arg in args if not (control == "no-tree" and arg == "/T")]
        if control == "late-kill":

            def later() -> None:
                time.sleep(LATE_SECONDS)
                started = time.perf_counter()
                _record_kill(trace, started, original(argv, capture_output=True, check=False))

            thread = threading.Thread(target=later)
            thread.start()
            trace.threads.append(thread)
            return subprocess.CompletedProcess(argv, 0, b"", b"")
        started = time.perf_counter()
        result = original(argv, *rest, **options)
        _record_kill(trace, started, result)
        return result

    patch.setattr(subprocess, "run", traced)
    if control == "late-kill":
        patch.setattr(subprocess.Popen, "kill", lambda self: None)


def _write_late(heartbeat: Path) -> None:
    """`late-write` 대조. 러너가 돌아온 뒤 기록 파일에 한 바이트를 덧쓴다."""
    time.sleep(LATE_SECONDS)
    with heartbeat.open("ab") as f:
        f.write(b"+")


def _patch_runner(
    patch: pytest.MonkeyPatch, module: ModuleType, trace: Trace, control: str
) -> None:
    original: Callable[..., object] = module.run_command

    def wrapped(argv: Sequence[str], cwd: Path, timeout: int) -> object:
        heartbeat = Path(argv[4])
        trace.heartbeat = heartbeat
        watcher = threading.Thread(target=_watch, args=(trace, heartbeat), daemon=True)
        watcher.start()
        trace.threads.append(watcher)
        trace.called_at = time.perf_counter()
        try:
            return original(argv, cwd, timeout)
        except KeyboardInterrupt:
            trace.raised_at = time.perf_counter()
            if control == "late-write":
                writer = threading.Thread(target=_write_late, args=(heartbeat,))
                writer.start()
                trace.threads.append(writer)
            raise

    patch.setattr(module, "run_command", wrapped)


def _patch_ready(patch: pytest.MonkeyPatch, module: ModuleType, trace: Trace) -> None:
    """시험이 Ctrl-C 를 넣는 조건에, 지키는 스레드가 살아 있는 손자를 한 번 봤다는 것을 더한다."""
    original: Callable[..., None] = module._첫_기다림을_끊는다

    def wrapped(
        mp: pytest.MonkeyPatch,
        cut: Callable[..., BaseException],
        ready: Callable[[object], bool] = lambda _: True,
    ) -> None:
        def ready_now(process: object) -> bool:
            if not (ready(process) and trace.ready.is_set()):
                return False
            if trace.cut_at is None:  # 참을 돌려준 곧바로 끊는다
                trace.cut_at = time.perf_counter()
            return True

        original(mp, cut, ready_now)

    patch.setattr(module, "_첫_기다림을_끊는다", wrapped)


def grandchild_line(output: str, pid: int | None) -> str:
    """`taskkill` 출력에서 손자 pid 의 줄(오류면 다음의 원인 줄까지)을 꺼낸다. 이 PC 에서 본 두
    모양에 기댄다. 한국어 `성공: PID <손자>인 프로세스(PID <부모>인 자식 프로세스)…` 와, 같은 PC
    에서도 섞여 나온 영어 `SUCCESS: The process with PID <손자> (child process of PID <부모>)…`
    다."""
    if pid is None:
        return "(없음)"
    heads = (f"PID {pid}인 프로세스", f"The process with PID {pid}")
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    for index, line in enumerate(lines):
        if line.split("(")[0].rstrip().endswith(heads):
            after = lines[index + 1] if index + 1 < len(lines) else ""
            return line + (" " + after if after.startswith(("원인", "Reason")) else "")
    return "(없음)"


def _patch_judges(patch: pytest.MonkeyPatch, module: ModuleType, trace: Trace) -> None:
    for name in JUDGES:
        original: Callable[..., bool] | None = getattr(module, name, None)
        if original is None:
            continue

        def wrapped(
            *args: object,
            _original: Callable[..., bool] = original,
            _name: str = name,
            **kw: object,
        ) -> bool:
            started = time.perf_counter()
            got = _original(*args, **kw)
            trace.judges.append((_name, started, time.perf_counter(), got))
            return got

        patch.setattr(module, name, wrapped)


def _command_line(pid: int) -> str:
    """그 pid 의 명령줄. 읽지 못하면 빈 문자열이다."""
    query = f"(Get-CimInstance Win32_Process -Filter 'ProcessId={pid}').CommandLine"
    try:
        result = RUN(
            ["powershell", "-NoProfile", "-Command", query],
            capture_output=True,
            check=False,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return _oem(result.stdout)


def _end_if_ours(trace: Trace, handle: int) -> None:
    """쥔 핸들의 손자가 아직 살아 있으면, 그 pid 의 명령줄에 이 회차의 기록 파일 경로가 있을 때만
    그 핸들로 끝낸다. 핸들을 쥔 동안 그 pid 는 다시 쓰이지 않는다."""
    if KERNEL.WaitForSingleObject(handle, 0) != WAIT_TIMEOUT:
        return
    if trace.pid is None or trace.heartbeat is None:
        trace.cleanup = "pid 나 기록 파일 경로를 몰라 끄지 않았다"
        return
    if str(trace.heartbeat) not in _command_line(trace.pid):
        trace.cleanup = "명령줄에 이 회차의 기록 파일 경로가 없어 끄지 않았다"
        return
    if not KERNEL.TerminateProcess(handle, 1):
        trace.cleanup = f"끄지 못했다(오류 {ctypes.get_last_error()})"
        return
    trace.cleanup = "남은 손자를 끝냈다"


def _finish(trace: Trace) -> None:
    """러너가 돌아온 뒤(`taskkill` 이 더 늦으면 그 뒤) `AFTER_SECONDS` 까지 더 지키고, 남은 손자를
    끝낸다."""
    for thread in trace.threads:
        if not thread.daemon:  # 대조(late-kill, late-write)가 띄운 스레드
            thread.join(timeout=60)
    marks = [float(str(kill["ended"])) for kill in trace.kills]
    marks += [] if trace.raised_at is None else [trace.raised_at]
    until = (max(marks) if marks else time.perf_counter()) + AFTER_SECONDS
    while time.perf_counter() < until:
        time.sleep(0.05)
    trace.stop.set()
    for thread in trace.threads:
        thread.join(timeout=10)
    if trace.handle is None:
        return
    try:
        _end_if_ours(trace, trace.handle)
    finally:
        KERNEL.CloseHandle(trace.handle)


def classify(trace: Trace, raised: float) -> dict[str, object]:
    """갈래와 그 근거의 시간(ms, 러너가 돌아온 때가 0)을 낸다."""
    kill_end = float(str(trace.kills[0]["ended"]))
    after = [(t, alive) for t, _, alive in trace.samples if t > raised]
    alive_after = [t for t, alive in after if alive]
    dead_after = [t for t, alive in after if not alive]
    sized = [(t, size) for t, size, _ in trace.samples if size >= 0]  # -1 은 읽지 못한 표본
    growth = [t for (_, before), (t, size) in zip(sized, sized[1:], strict=False) if size > before]
    growth_after = [t for t in growth if t > raised]
    gaps = [b - a for a, b in zip(growth, growth[1:], strict=False)]
    times = [t for t, _, _ in trace.samples]
    sample_gaps = [b - a for a, b in zip(times, times[1:], strict=False)]
    # 판정 `_멈추는지` 가 도는 동안 손자가 쓰지 않은 가장 긴 구간과, 그 동안 지키는 스레드가 표본을
    # 뜨지 못한 가장 긴 구간. 앞의 것만 1초를 넘으면 손자가 실제로 멈춘 것이고, 둘이 함께 길면
    # 지키는 스레드가 굶어 자람을 보지 못한 것이다
    stop_calls = [(start, end) for name, start, end, _ in trace.judges if name == "_멈추는지"]
    judge_quiet: list[float] = []
    judge_sample_gaps: list[float] = []
    for start, end in stop_calls:
        edges = [start, *(t for t in growth if start < t < end), end]
        judge_quiet.extend(b - a for a, b in zip(edges, edges[1:], strict=False))
        inside = [start, *(t for t in times if start < t < end), end]
        judge_sample_gaps.extend(b - a for a, b in zip(inside, inside[1:], strict=False))
    if not dead_after:
        branch = "B"
    elif alive_after:
        branch = "A"
    elif growth_after:
        branch = "C"
    else:
        branch = "ok"

    def ms(t: float | None) -> float | None:
        return None if t is None else round((t - raised) * 1000, 1)

    return {
        "branch": branch,
        "kill_end_ms": ms(kill_end),
        "alive_after_kill": any(alive for t, _, alive in trace.samples if t > kill_end),
        "last_alive_ms": ms(max(alive_after) if alive_after else None),
        "first_dead_ms": ms(min(dead_after) if dead_after else None),
        "last_growth_ms": ms(max(growth) if growth else None),
        "samples_after": len(after),
        # 손자가 쓰는 동안 파일이 가장 오래 자라지 않은 틈. 판정이 "그만큼 조용하면 끝났다" 로 읽는
        # 문턱이 이 틈보다 짧으면, 살아 있는 손자를 끝났다고 읽는다(고친 판의 거짓 초록)
        "max_growth_gap_ms": round(max(gaps, default=0) * 1000, 1),
        # 문턱(1초)에 얼마나 다가가는지 보려고 그 절반을 넘은 틈을 센다
        "long_growth_gaps": sum(1 for gap in gaps if gap > LONG_GAP_SECONDS),
        "max_sample_gap_ms": round(max(sample_gaps, default=0) * 1000, 1),
        "judge_quiet_ms": round(max(judge_quiet) * 1000, 1) if judge_quiet else None,
        "judge_sample_gap_ms": (
            round(max(judge_sample_gaps) * 1000, 1) if judge_sample_gaps else None
        ),
    }


def judged(row: dict[str, object]) -> list[tuple[str, bool]]:
    """회차 행에 남긴 판정 함수의 이름과 결과."""
    value = row.get("judges")
    if not isinstance(value, list):
        return []
    pairs: list[object] = list(value)
    return [
        (str(pair[0]), bool(pair[1]))
        for pair in pairs
        if isinstance(pair, tuple | list) and len(pair) == 2
    ]


def grew_after_return(row: dict[str, object]) -> bool:
    """러너가 돌아온 뒤 기록 파일이 자랐는지. 옛 판정이 빨개질 수 있었던 회차다."""
    value = row.get("last_growth_ms")
    return value is not None and float(str(value)) > 0


def past_first_window(row: dict[str, object]) -> bool:
    """판정 `_멈추는지` 가 첫 1초 창에서 자람을 보고 다음 창으로 갔는지(걸린 시간으로 가늠한다)."""
    value = row.get("judge_ms")
    if not isinstance(value, list):
        return False
    calls: list[object] = list(value)
    return any(
        isinstance(call, tuple | list)
        and len(call) == 2
        and call[0] == "_멈추는지"
        and float(str(call[1])) > PAST_FIRST_WINDOW_SECONDS * 1000
        for call in calls
    )


def unmeasured_reason(trace: Trace, *, alive: bool) -> str | None:
    if not alive:
        return "부하가 회차 중에 끝났다"
    if trace.raised_at is None:
        return "러너가 Ctrl-C 를 올리지 않았다"
    if len(trace.kills) != 1:
        return f"taskkill 이 {len(trace.kills)}번 돌아왔다"
    started = float(str(trace.kills[0]["started"]))
    if not any(t < started and alive and size > 0 for t, size, alive in trace.samples):
        return "taskkill 전에 살아 있는 손자를 보지 못했다" + (
            " (핸들을 열지 못했다)" * trace.open_failed
        )
    return None


def kill_tree(proc: subprocess.Popen[bytes]) -> None:
    """부하 프로세스와 그 자식을 끝낸다. `pytest -n` 의 일꾼은 자식이라 `kill` 만으로는 남는다."""
    if proc.poll() is not None:
        return
    RUN(
        ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    proc.wait(timeout=30)


@contextlib.contextmanager
def burners(
    count: int, pytest_loads: int, logs: Sequence[Path] = ()
) -> Iterator[list[subprocess.Popen[bytes]]]:
    """부하 프로세스를 띄운다. `logs` 가 있으면 pytest 부하 i 의 출력을 `logs[i]` 에 남긴다(그
    부하도 대상 시험을 한 번 돈다. `-rf` 로 실패한 시험의 이름이 끝에 남는다). 없으면 버린다."""
    with contextlib.ExitStack() as stack:
        sinks = [stack.enter_context(path.open("wb")) for path in logs[:pytest_loads]]
        procs = [
            subprocess.Popen([sys.executable, "-c", BURNER], stdout=subprocess.DEVNULL)
            for _ in range(count)
        ]
        procs += [
            subprocess.Popen(
                [sys.executable, "-m", "pytest", "-q", "-rf", "-n", "8", "-p", "no:cacheprovider"],
                cwd=ROOT,
                stdout=sinks[index] if index < len(sinks) else subprocess.DEVNULL,
                stderr=subprocess.STDOUT if index < len(sinks) else subprocess.DEVNULL,
            )
            for index in range(pytest_loads)
        ]
        try:
            # pytest 는 수집과 일꾼을 띄우는 데 시간이 든다. 그 전의 회차는 부하가 덜하다(어림).
            time.sleep(20.0 if pytest_loads else 1.0 if count else 0.0)
            yield procs
        finally:
            # 출력을 남기는 pytest 부하는 끝까지 기다린다. 실패 줄은 pytest 가 끝날 때 찍는다.
            for proc in procs[count : count + len(sinks)]:
                with contextlib.suppress(subprocess.TimeoutExpired):
                    proc.wait(timeout=LOAD_WAIT_SECONDS)
            for proc in procs:
                kill_tree(proc)


def failed_in(log: Path) -> list[str]:
    """pytest 부하의 출력에서 `-rf` 가 남긴 실패 줄을 꺼낸다."""
    try:
        text = log.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ["(출력을 읽지 못했다)"]
    return [line.strip()[:300] for line in text.splitlines() if line.startswith("FAILED ")]


def load_test_module(test_file: Path, index: int) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"probe_test_mutate_{index}", test_file)
    if spec is None or spec.loader is None:
        raise SystemExit(f"시험 모듈을 불러오지 못했다: {test_file}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_once(module: ModuleType, control: str) -> tuple[str, str, Trace]:
    trace = Trace()
    test: Callable[[Path, pytest.MonkeyPatch], None] = getattr(module, TEST_NAME)
    outcome, detail = "passed", ""
    with (
        tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory,
        pytest.MonkeyPatch.context() as patch,
    ):
        _patch_kill(patch, trace, control)
        _patch_runner(patch, module, trace, control)
        _patch_ready(patch, module, trace)
        _patch_judges(patch, module, trace)
        try:
            test(Path(directory), patch)
        except Exception as error:  # 실패의 모양을 센다
            outcome = type(error).__name__
            detail = (str(error).splitlines() or ["(메시지 없음)"])[-1][:200]
        _finish(trace)
    return outcome, detail, trace


def between_ms(start: float | None, end: float | None) -> float | None:
    return None if start is None or end is None else round((end - start) * 1000, 1)


def numbers(rows: list[dict[str, object]], key: str) -> list[float]:
    return [float(str(row[key])) for row in rows if row.get(key) is not None]


def tail(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    ordered = sorted(values)
    return {
        "n": len(ordered),
        "median": round(statistics.median(ordered), 1),
        "max": ordered[-1],
    }


def run(
    runs: int,
    burner_count: int,
    pytest_loads: int,
    control: str,
    test_files: list[Path],
    logs: Sequence[Path] = (),
) -> dict[str, object]:
    modules = [load_test_module(path, index) for index, path in enumerate(test_files)]
    rows: list[dict[str, object]] = []
    unmeasured: list[str] = []
    with burners(burner_count, pytest_loads, logs) as procs:
        began = time.monotonic()
        for index in range(runs):
            which = index % len(modules)
            outcome, detail, trace = run_once(modules[which], control)
            reason = unmeasured_reason(trace, alive=all(proc.poll() is None for proc in procs))
            row: dict[str, object] = {
                "run": index,
                "file": which,
                "outcome": outcome,
                "pid": trace.pid,
            }
            if detail:
                row["detail"] = detail
            if trace.cleanup is not None:
                row["cleanup"] = trace.cleanup
            row["judges"] = [(name, ok) for name, _, _, ok in trace.judges]
            row["judge_ms"] = [
                (name, round((ended - started) * 1000, 1))
                for name, started, ended, _ in trace.judges
            ]
            if reason is not None or trace.raised_at is None:
                reason = reason or "러너가 Ctrl-C 를 올리지 않았다"
                unmeasured.append(reason)
                rows.append({**row, "measured": False, "reason": reason})
            else:
                kill = trace.kills[0]
                kill_ms = (float(str(kill["ended"])) - float(str(kill["started"]))) * 1000
                rows.append(
                    {
                        **row,
                        "measured": True,
                        "kill_ms": round(kill_ms, 1),
                        "kill_code": kill["code"],
                        "kill_output": kill["output"],
                        "grandchild_kill": grandchild_line(str(kill["output"]), trace.pid),
                        "startup_ms": between_ms(trace.called_at, trace.cut_at),
                        "call_to_raise_ms": between_ms(trace.called_at, trace.raised_at),
                        **classify(trace, trace.raised_at),
                    }
                )
            if pytest_loads and not all(proc.poll() is None for proc in procs):
                break
        seconds = round(time.monotonic() - began, 1)
    by_file: list[dict[str, object]] = []
    for which, path in enumerate(test_files):
        mine = [row for row in rows if row["file"] == which]
        measured = [row for row in mine if row["measured"]]
        red = [row for row in measured if row["outcome"] != "passed"]
        passed = [row for row in measured if row["outcome"] == "passed"]
        by_file.append(
            {
                "test_file": str(path),
                "outcomes": {
                    name: sum(1 for row in measured if row["outcome"] == name)
                    for name in sorted({str(row["outcome"]) for row in measured})
                },
                "branches": {
                    name: sum(1 for row in measured if row["branch"] == name)
                    for name in ("ok", "A", "B", "C")
                },
                "red_branches": {
                    name: sum(1 for row in red if row["branch"] == name)
                    for name in ("ok", "A", "B", "C")
                },
                "kill_codes": sorted({str(row["kill_code"]) for row in measured}),
                "grandchild_kill": {
                    head: sum(
                        1 for row in measured if str(row["grandchild_kill"]).split(":")[0] == head
                    )
                    for head in sorted(
                        {str(row["grandchild_kill"]).split(":")[0] for row in measured}
                    )
                },
                "kill_ms": tail([float(str(row["kill_ms"])) for row in measured]),
                "startup_ms": tail(numbers(measured, "startup_ms")),
                "call_to_raise_ms": tail(numbers(measured, "call_to_raise_ms")),
                f"call_to_raise_at_least_{OLD_BOUND_SECONDS}s": sum(
                    1
                    for value in numbers(measured, "call_to_raise_ms")
                    if value >= OLD_BOUND_SECONDS * 1000
                ),
                "alive_after_kill": sum(1 for row in measured if row["alive_after_kill"]),
                "grew_after_return": sum(1 for row in measured if grew_after_return(row)),
                "passed_with_growth_after_return": sum(
                    1 for row in passed if grew_after_return(row)
                ),
                "passed_past_first_window": sum(1 for row in passed if past_first_window(row)),
                "cleanup": {
                    text: sum(1 for row in mine if row.get("cleanup") == text)
                    for text in sorted({str(row["cleanup"]) for row in mine if "cleanup" in row})
                },
                "first_dead_ms": tail(
                    [
                        float(str(row["first_dead_ms"]))
                        for row in measured
                        if row["first_dead_ms"] is not None
                    ]
                ),
                "max_growth_gap_ms": tail(
                    [float(str(row["max_growth_gap_ms"])) for row in measured]
                ),
                "long_growth_gaps": sum(int(str(row["long_growth_gaps"])) for row in measured),
                "max_sample_gap_ms": tail(numbers(measured, "max_sample_gap_ms")),
                "judge_quiet_ms": tail(numbers(measured, "judge_quiet_ms")),
                "judge_sample_gap_ms": tail(numbers(measured, "judge_sample_gap_ms")),
                # 판정의 창(1초)보다 오래 손자가 쓰지 않은 구간이 판정 도중에 있었던 회차
                "judge_quiet_over_window": sum(
                    1 for value in numbers(measured, "judge_quiet_ms") if value > 1000
                ),
                "judges": {
                    f"{name}={ok}": sum(1 for row in measured if (name, ok) in judged(row))
                    for name, ok in sorted({(n, o) for row in measured for n, o in judged(row)})
                },
                "red_details": [str(row.get("detail", "")) for row in red][:10],
            }
        )
    return {
        "runs": runs,
        "burners": burner_count,
        "pytest_loads": pytest_loads,
        "control": control,
        "unmeasured": len(unmeasured),
        "unmeasured_reasons": sorted(set(unmeasured)),
        "seconds": seconds,
        "by_file": by_file,
        "pytest_load_failed": {path.name: failed_in(path) for path in logs[:pytest_loads]},
        "rows": rows,
    }


def main() -> int:
    if sys.platform != "win32":
        raise SystemExit("윈도에서만 돈다")
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", type=int)
    parser.add_argument("--burners", type=int, default=0)
    parser.add_argument("--pytest-loads", type=int, default=0)
    parser.add_argument(
        "--control", choices=("none", "no-tree", "late-kill", "late-write"), default="none"
    )
    parser.add_argument("--test-file", action="append", help="번갈아 부를 시험 파일")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    files = [Path(name) for name in args.test_file or [str(TEST_FILE)]]
    out = Path(args.out) if args.out else None
    logs = (
        [out.with_name(f"{out.stem}_pytest{index}.txt") for index in range(args.pytest_loads)]
        if out
        else []
    )
    summary = run(args.runs, args.burners, args.pytest_loads, args.control, files, logs)
    if args.out:
        Path(args.out).write_text(json.dumps(summary, ensure_ascii=False) + "\n", encoding="utf-8")
    brief = {key: value for key, value in summary.items() if key != "rows"}
    print(json.dumps(brief, ensure_ascii=False), flush=True)
    return 1 if summary["unmeasured"] else 0


if __name__ == "__main__":
    sys.exit(main())
