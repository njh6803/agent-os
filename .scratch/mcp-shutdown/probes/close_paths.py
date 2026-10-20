"""MCP stdio 서버를 닫는 길마다 서버와 그 자식이 내려가는지, 닫는 데 얼마가 드는지 잰다.

mcp의 `stdio_client`와 `ClientSession`을 직접 쓴다. 어댑터(`McpTools`)는 그 둘을 감쌀 뿐이고 닫기는
`stdio_client`가 한다(지금의 langchain-mcp-adapters 0.3.2도 서버마다 그 둘을 연다. 코드를 읽었다).
그래서 같은 스크립트를 mcp 1.30.0(지금, 대조군)과 2.3.0(ADR 0034가 고른 판)의 환경에서 돌려 견준다.
실행 타임아웃처럼 취소 범위가 연결 전체를 감싼다(`core/run.py`의 진입점이 기한 범위로 몸통을 감싸는
모양). 이 프로브는 그 범위를 처음 쓸 때의 core 처럼 `fail_after`로 연다. #325 뒤의 core 는
`move_on_after`이고, 둘은 범위가 끝날 때 예외를 내는지만 다르다.

사례(가짜 프로세스는 `fakes.py`):
- `cancel`: 감싸는 프로세스 → 입력이 닫혀도 끝나지 않는 서버. `slow(30)` 도중에 기한(1초)이 온다.
- `stay_normal`: 같은 서버를 `slow(0.1)` 뒤 정상으로 닫는다.
- `exit_child_normal`: 입력이 닫히면 스스로 끝나며 자식을 남기는 서버를 정상으로 닫는다.
- `raise_inside`: `cancel`의 서버에서 `slow(0.1)` 뒤 세션 안에서 예외를 던진다(연결 안의 예외).
- `close_fails`: `cancel`의 서버를 한 태스크에서 열어 `slow(0.1)`을 부르고, 다른 태스크에서 닫는다.
  anyio 의 취소 범위는 연 태스크에서 닫혀야 해서 닫기 자체가 예외로 끝난다(타임아웃이 아닌 닫기
  실패. pytest-asyncio 픽스처의 setup 과 teardown 이 이 모양이었다, ADR 0007 이력).
- `sigterm_ignored_cancel`(POSIX만): `cancel`과 같되 서버가 SIGTERM을 무시한다.
- `missing_command`: 없는 명령을 서버로 띄운다. 어느 예외가 어디서 오는지 본다.
- `cli_ctrl_c`: CLI처럼 `asyncio.run`으로 도는 자식 프로세스가 `slow(30)` 도중에 SIGINT를 받는다
  (`asyncio.run`이 주 태스크를 네이티브로 취소한다). 자식이 끝난 뒤 서버가 남는지 본다.
- `cli_ctrl_c_twice`: `cli_ctrl_c`에 0.5초 뒤 SIGINT 하나를 더한다. 둘째는 닫기의 유예(2초) 안에
  온다. 그 뒤 10초가 지나도 자식이 끝나지 않았으면 셋째를 보낸다(사람이 멈춘 CLI 에서 한 번 더
  누르는 것). 셋째가 나갔는지(`third_sigint_to_exit_seconds`)가 둘째 뒤에 멈췄는지를 가른다.

`--cli-handler force`를 주면 두 CLI 사례의 자식이 `asyncio.run`의 처리기 대신 명세가 정한 처리기의
시제품(`_run_with_force_exit`. 첫 SIGINT 는 주 태스크를 취소하고 둘째는 곧바로 끝낸다)으로 돈다.
끝나는 꼴은 처리하지 않은 KeyboardInterrupt 로 끝나는 파이썬과 같다(POSIX 는 SIGINT 로 죽고 윈도우는
STATUS_CONTROL_C_EXIT). 자식의 종료 코드(`child_exit`)를 기록에 남긴다.

선택: `--launcher none|kill|watch`(POSIX만. `launcher.py`를 서버 앞에 끼운다. watch는
`--watch-parent`), `--python base|venv`(가짜 프로세스를 띄울 파이썬. base는 `sys._base_executable`,
venv는 이 환경의 `sys.executable`이다. 윈도우의 venv 파이썬은 진짜 파이썬을 자식으로 띄우는 런처다).

표지: 연결을 연 사례는 역할마다 하트비트가 닫기 전에 생겼고(`_marked`), 취소 사례는 `slow`가
시작했다는 표시 파일이 기한보다 먼저 생겼고, 정상 사례는 `slow`가 "done"을 돌려줬으며,
`raise_inside`는 던진 예외가 호출자에게 온 것 안에 있고, `close_fails`는 닫기가 다른 태스크라는
anyio 의 예외로 끝났고, 없는 명령은 그 까닭(명령을 찾지 못했다)이 예외나 런처의 한 줄에 있고,
`cli_ctrl_c`는 SIGINT를 보내기 전에 `slow`가 시작했고 자식이 `slow`가 돌아오기 전에
KeyboardInterrupt로 끝났다 (돌아온 뒤에 끝났으면 취소가 아니라 정상 닫기를 잰 것이다). 표지가 없는
사례는 측정이 아니라고 따로 세고 종료 코드를 1로 둔다. 남은 프로세스는 멈춤 파일로 끝내고, 끝나지
않으면 그것도 종료 코드 1이다.

돌리는 명령은 같은 폴더의 `README.md`에 있다.
"""

from __future__ import annotations

import argparse
import asyncio
import faulthandler
import importlib.metadata
import json
import os
import platform
import signal
import subprocess
import sys
import sysconfig
import tempfile
import threading
import time
from collections.abc import Callable, Coroutine
from contextlib import AsyncExitStack
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters, stdio_client

HERE = Path(__file__).resolve().parent
FAKES = HERE / "fakes.py"
LAUNCHER = HERE / "launcher.py"
SITE = sysconfig.get_paths()["purelib"]
MISSING = "definitely-not-a-command-agent-os"
DEADLINE_SECONDS = 1.0
WINDOW_SECONDS = 0.6
CASES = (
    "cancel",
    "stay_normal",
    "exit_child_normal",
    "raise_inside",
    "close_fails",
    "sigterm_ignored_cancel",
    "missing_command",
    "cli_ctrl_c",
    "cli_ctrl_c_twice",
)
POSIX_ONLY = {"sigterm_ignored_cancel"}
CANCELLED = {"cancel", "sigterm_ignored_cancel"}
CLI = {"cli_ctrl_c", "cli_ctrl_c_twice"}
SECOND_SIGINT_SECONDS = 0.5
THIRD_SIGINT_SECONDS = 10.0
STATUS_CONTROL_C_EXIT = 0xC000013A
# anyio 가 취소 범위를 연 태스크가 아닌 태스크에서 닫을 때 내는 예외의 글(`close_fails`의 표지). 첫
# 회차의 원본 출력에서 골랐다.
OTHER_TASK = "different task"


class ProbeError(RuntimeError):
    """`raise_inside`가 세션 안에서 던지는 예외."""


def _python(choice: str) -> str:
    return sys._base_executable if choice == "base" else sys.executable


def _roles(case: str) -> list[str]:
    if case == "missing_command":
        return []
    if case == "exit_child_normal":
        return ["server", "child"]
    return ["wrapper", "server"]


def _command(case: str, work: Path, launcher: str, python: str) -> tuple[str, list[str]]:
    """사례의 서버 명령. 런처를 고르면 그 앞에 런처를 끼운다."""
    stop = str(work / "stop")
    if case == "missing_command":
        command, args = MISSING, []
    elif case == "exit_child_normal":
        server = [str(work / "server.hb"), stop, SITE, "exit", str(work / "child.hb"), "keep"]
        command, args = python, [str(FAKES), "server", *server]
    else:
        sigterm = "ignore" if case == "sigterm_ignored_cancel" else "keep"
        server = [str(work / "server.hb"), stop, SITE, "stay", "-", sigterm]
        command = python
        args = [str(FAKES), "wrapper", str(work / "wrapper.hb"), stop, *server]
    if launcher == "none":
        return command, args
    watch = ["--watch-parent"] if launcher == "watch" else []
    return sys.executable, ["-I", str(LAUNCHER), *watch, command, *args]


def _describe(error: BaseException) -> dict[str, object]:
    described: dict[str, object] = {
        "type": f"{type(error).__module__}.{type(error).__qualname__}",
        "str": str(error)[:200],
    }
    if isinstance(error, BaseExceptionGroup):
        described["inner"] = [_describe(inner) for inner in error.exceptions]
    return described


def _contains(error: BaseException, target: type[BaseException]) -> bool:
    if isinstance(error, target):
        return True
    if isinstance(error, BaseExceptionGroup):
        return any(_contains(inner, target) for inner in error.exceptions)
    return False


def _size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return None


def _beating(work: Path, roles: list[str]) -> dict[str, bool | None]:
    """역할마다 하트비트가 창(0.6초) 동안 자랐는지. 파일이 없으면 없음이다."""
    before = {role: _size(work / f"{role}.hb") for role in roles}
    time.sleep(WINDOW_SECONDS)
    return {
        role: None if before[role] is None else _size(work / f"{role}.hb") != before[role]
        for role in roles
    }


async def _wait_for(path: Path, seconds: float = 20.0) -> bool:
    end = anyio.current_time() + seconds
    while not path.exists():
        if anyio.current_time() > end:
            return False
        await anyio.sleep(0.05)
    return True


async def _connected(case: str, work: Path, params: StdioServerParameters) -> dict[str, object]:
    """연결을 열고 사례대로 움직인 뒤 닫는다. 기록과 표지를 돌려준다."""
    record: dict[str, object] = {}
    marker = work / "server.hb.slow"
    started_close: float | None = None
    deadline: float | None = None
    deadline_wall: float | None = None
    with (work / "errlog.txt").open("w", encoding="utf-8") as errlog:

        async def drive() -> None:
            """새는 예외를 보려고 연결 전체를 감싼다. 아래 `try` 가 이 호출 하나를 받는다."""
            nonlocal started_close, deadline, deadline_wall
            with anyio.fail_after(60) as scope:
                async with stdio_client(params, errlog=errlog) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        for role in _roles(case):
                            record[f"{role}_started"] = await _wait_for(work / f"{role}.hb")
                        if case in CANCELLED:
                            scope.deadline = anyio.current_time() + DEADLINE_SECONDS
                            deadline = scope.deadline
                            deadline_wall = time.time() + DEADLINE_SECONDS
                            await session.call_tool("slow", {"seconds": 30})
                            record["unexpected"] = "slow(30) 이 기한 안에 돌아왔다"
                        else:
                            result = await session.call_tool("slow", {"seconds": 0.1})
                            record["slow_done"] = any(
                                getattr(block, "text", None) == "done" for block in result.content
                            )
                            started_close = anyio.current_time()
                            if case == "raise_inside":
                                raise ProbeError("세션 안에서 던진 예외")
            if started_close is not None:
                record["close_seconds"] = round(anyio.current_time() - started_close, 3)

        try:
            await drive()
        except Exception as error:
            now = anyio.current_time()
            record["exception"] = _describe(error)
            if deadline is not None:
                record["deadline_to_exception_seconds"] = round(now - deadline, 3)
                record["timeout_error"] = type(error) is TimeoutError
            if started_close is not None:
                record["close_seconds"] = round(now - started_close, 3)
                record["raised_reached_caller"] = _contains(error, ProbeError)
    if deadline_wall is not None:
        record["slow_started_before_deadline"] = (
            marker.exists() and marker.stat().st_mtime <= deadline_wall
        )
    record["errlog"] = (work / "errlog.txt").read_text(encoding="utf-8", errors="replace")[-400:]
    return record


async def _close_elsewhere(
    case: str, work: Path, params: StdioServerParameters
) -> dict[str, object]:
    """`close_fails`. 한 태스크에서 연결을 열어 도구를 부르고, 이 태스크에서 닫는다."""
    record: dict[str, object] = {}
    stack = AsyncExitStack()
    with (work / "errlog.txt").open("w", encoding="utf-8") as errlog:

        async def open_it() -> None:
            read, write = await stack.enter_async_context(stdio_client(params, errlog=errlog))
            session = await stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            for role in _roles(case):
                record[f"{role}_started"] = await _wait_for(work / f"{role}.hb")
            result = await session.call_tool("slow", {"seconds": 0.1})
            record["slow_done"] = any(
                getattr(block, "text", None) == "done" for block in result.content
            )

        await asyncio.create_task(open_it())
        started_close = anyio.current_time()
        try:
            with anyio.fail_after(30):
                await stack.aclose()
            record["close_raised"] = False
        except Exception as error:
            record["close_raised"] = True
            record["exception"] = _describe(error)
        record["close_seconds"] = round(anyio.current_time() - started_close, 3)
    record["errlog"] = (work / "errlog.txt").read_text(encoding="utf-8", errors="replace")[-400:]
    return record


def _marked(case: str, record: dict[str, object]) -> bool:
    """사례가 재려는 상황이 그 회차에 실제로 났는가.

    닫기 전에 역할마다 하트비트가 생겼어야 한다(`<역할>_started`. CLI 사례는 자식이 따로 돌아 그
    기록이 없어, 닫은 뒤 하트비트 파일이 있었는지로 본다). 하트비트가 없으면 "자랐는가"가 없음이라
    "내려갔다"로 읽힐 수 있다. 없는 명령은 실패의 까닭(명령을 찾지 못했다)까지 본다(셀프 리뷰가
    짚어 더했다).
    """
    if case == "missing_command":
        exception = record.get("exception")
        errlog = str(record.get("errlog", ""))
        return "FileNotFoundError" in json.dumps(exception) or "띄우지 못했다" in errlog
    if case in CLI:
        twice = case != "cli_ctrl_c_twice" or "second_sigint_to_exit_seconds" in record
        right_after = record.get("beating_right_after")
        existed = isinstance(right_after, dict) and None not in right_after.values()
        return (
            record.get("slow_started_before_sigint") is True
            and record.get("keyboard_interrupt") is True
            and "slow_returned_before_exit" not in record
            and "child_timeout" not in record
            and twice
            and existed
        )
    started = all(record.get(f"{role}_started") is True for role in _roles(case))
    if case in CANCELLED:
        return started and record.get("slow_started_before_deadline") is True
    if case == "raise_inside":
        return (
            started
            and record.get("slow_done") is True
            and record.get("raised_reached_caller") is True
        )
    if case == "close_fails":
        return (
            started
            and record.get("slow_done") is True
            and record.get("close_raised") is True
            and OTHER_TASK in json.dumps(record.get("exception"))
        )
    return started and record.get("slow_done") is True


def _cli_child(config: dict[str, str | list[str]]) -> None:
    """`cli_ctrl_c`의 자식. CLI처럼 `asyncio.run`으로 돌고 `slow(30)` 도중에 SIGINT를 받는다."""
    work = Path(str(config["work"]))
    marker = work / "server.hb.slow"
    params = StdioServerParameters(command=str(config["command"]), args=list(config["args"]))

    def interrupt() -> None:
        """터미널의 Ctrl+C 처럼 주 스레드가 SIGINT 를 받게 한다.

        POSIX 에서 이 스레드가 `raise_signal` 로 올리면 신호가 이 스레드에 닿아 주 스레드의 epoll
        대기가 깨지지 않고, 처리기는 `slow(30)` 이 돌아온 뒤에야 돈다(첫 판이 그렇게 30초를 쟀다).
        그래서 이 스레드는 SIGINT 를 막고 프로세스에 보내 주 스레드가 받게 한다. 윈도우는 C 처리기가
        올린 스레드에서 돌고 이벤트 루프를 깨우므로 그대로 올린다.
        """
        end = time.monotonic() + 30
        while not marker.exists() and time.monotonic() < end:
            time.sleep(0.05)
        print(json.dumps({"sigint": time.time(), "slow": marker.exists()}), flush=True)
        if os.name == "posix":
            signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
        _send()
        if config.get("twice") == "yes":
            time.sleep(SECOND_SIGINT_SECONDS)
            print(json.dumps({"second_sigint": time.time()}), flush=True)
            _send()
            # 둘째 뒤 이 프로세스가 끝나지 않고 멈추면(윈도우 첫 회차) 사람은 한 번 더 누른다. 이
            # 스레드는 daemon 이라 프로세스가 끝나면 여기까지 오지 않는다.
            time.sleep(THIRD_SIGINT_SECONDS)
            print(json.dumps({"third_sigint": time.time()}), flush=True)
            _send()

    def _send() -> None:
        if os.name == "posix":
            os.kill(os.getpid(), signal.SIGINT)
        else:
            signal.raise_signal(signal.SIGINT)

    async def main() -> None:
        with anyio.fail_after(600):
            with (work / "errlog.txt").open("w", encoding="utf-8") as errlog:
                async with stdio_client(params, errlog=errlog) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        threading.Thread(target=interrupt, daemon=True).start()
                        await session.call_tool("slow", {"seconds": 30})
                        print(json.dumps({"slow_returned": time.time()}), flush=True)

    # 20초 넘게 끝나지 않으면 모든 스레드의 스택을 표준 에러(`cli_stderr.txt`)에 남긴다. 둘째 Ctrl+C
    # 뒤 윈도우에서 자식이 끝나지 않은 첫 회차의 자리를 보려고 더했다.
    faulthandler.dump_traceback_later(20)
    if config.get("handler") == "force":
        _run_with_force_exit(main)
        return
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(json.dumps({"keyboard_interrupt": time.time()}), flush=True)
        raise


def _die_interrupted() -> None:
    """처리하지 않은 KeyboardInterrupt 로 끝나는 파이썬과 같은 꼴로 곧바로 끝난다."""
    if os.name != "posix":
        os._exit(STATUS_CONTROL_C_EXIT - 2**32)  # os._exit 는 C int 를 받는다
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    os.kill(os.getpid(), signal.SIGINT)
    os._exit(128 + signal.SIGINT)


def _run_with_force_exit(main: Callable[[], Coroutine[object, object, None]]) -> None:
    """명세가 정한 CLI 처리기의 시제품. 첫 SIGINT 는 `asyncio.run`처럼 주 태스크를 한 번 취소하고,
    둘째는 곧바로 프로세스를 끝낸다(`_die_interrupted`). 저장소 사본에 얹는 판은
    `prototype/src/agent_os/channel/cli/interrupt.py`다.

    처리기를 `asyncio.run` 앞에 달면 그 러너는 자기 처리기를 달지 않는다(SIGINT 처리기가 기본값일
    때만 단다, Python 3.12 `asyncio/runners.py`를 읽었다). 주 태스크가 취소로 끝나면
    `CancelledError`가 올라오고, 그것을 받아 끝낸다.
    """
    held: dict[str, asyncio.Task[None] | asyncio.AbstractEventLoop] = {}
    pressed: list[float] = []

    def on_sigint(signum: int, frame: object) -> None:
        task, loop = held.get("task"), held.get("loop")
        if not pressed and isinstance(task, asyncio.Task) and not task.done():
            pressed.append(time.time())
            task.cancel()
            if isinstance(loop, asyncio.AbstractEventLoop):
                loop.call_soon_threadsafe(lambda: None)
            return
        print(json.dumps({"force_exit": time.time()}), flush=True)
        _die_interrupted()

    async def wrapped() -> None:
        task = asyncio.current_task()
        if task is not None:
            held["task"] = task
        held["loop"] = asyncio.get_running_loop()
        await main()

    signal.signal(signal.SIGINT, on_sigint)
    try:
        asyncio.run(wrapped())
    except asyncio.CancelledError:
        print(json.dumps({"cancelled": time.time()}), flush=True)
        _die_interrupted()


def _cli_case(
    work: Path, command: str, args: list[str], *, twice: bool, handler: str
) -> dict[str, object]:
    config = {
        "work": str(work),
        "command": command,
        "args": args,
        "twice": "yes" if twice else "no",
        "handler": handler,
    }
    stderr_path = work / "cli_stderr.txt"
    with stderr_path.open("w", encoding="utf-8") as stderr:
        child = subprocess.Popen(
            [sys.executable, __file__, "--cli-child", json.dumps(config)],
            stdout=subprocess.PIPE,
            stderr=stderr,
            text=True,
        )
        try:
            out, _ = child.communicate(timeout=60)
            timed_out = False
        except subprocess.TimeoutExpired:
            child.kill()
            out, _ = child.communicate()
            timed_out = True
    exited = time.time()
    record: dict[str, object] = {"child_exit": child.returncode}
    record["cli_stderr_tail"] = stderr_path.read_text(encoding="utf-8", errors="replace")[-3000:]
    if timed_out:
        record["child_timeout"] = True
    for line in out.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "sigint" in event:
            record["slow_started_before_sigint"] = event["slow"]
            record["sigint_to_exit_seconds"] = round(exited - float(event["sigint"]), 3)
        if "keyboard_interrupt" in event or "cancelled" in event or "force_exit" in event:
            record["keyboard_interrupt"] = True  # 처리기마다 끝나는 표지가 다르다
        if "force_exit" in event:
            record["force_exit"] = True
        if "slow_returned" in event:
            record["slow_returned_before_exit"] = True
        if "second_sigint" in event:
            record["second_sigint_to_exit_seconds"] = round(
                exited - float(event["second_sigint"]), 3
            )
        if "third_sigint" in event:
            record["third_sigint_to_exit_seconds"] = round(exited - float(event["third_sigint"]), 3)
    return record


def run_case(case: str, launcher: str, python: str, handler: str) -> dict[str, object]:
    work = Path(tempfile.mkdtemp(prefix=f"mcp-close-{case}-"))
    roles = _roles(case)
    command, args = _command(case, work, launcher, _python(python))
    if case in CLI:
        twice = case == "cli_ctrl_c_twice"
        record = _cli_case(work, command, args, twice=twice, handler=handler)
    elif case == "close_fails":
        params = StdioServerParameters(command=command, args=args)
        record = anyio.run(_close_elsewhere, case, work, params)
    else:
        params = StdioServerParameters(command=command, args=args)
        record = anyio.run(_connected, case, work, params)
    record["beating_right_after"] = _beating(work, roles)
    time.sleep(3)
    record["beating_3s_later"] = _beating(work, roles)
    (work / "stop").touch()
    time.sleep(0.5)
    record["beating_after_stop_file"] = _beating(work, roles)
    record["marked"] = _marked(case, record)
    record["work"] = str(work)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--launcher", choices=("none", "kill", "watch"), default="none")
    parser.add_argument("--python", choices=("base", "venv"), default="base")
    parser.add_argument("--cli-handler", choices=("asyncio", "force"), default="asyncio")
    parser.add_argument("--cli-child")
    parser.add_argument("cases", nargs="*")
    options = parser.parse_args()
    if options.cli_child is not None:
        _cli_child(json.loads(options.cli_child))
        return 0
    if options.launcher != "none" and os.name != "posix":
        print("런처는 POSIX에서만 고른다", file=sys.stderr)
        return 2
    cases = options.cases or [c for c in CASES if os.name == "posix" or c not in POSIX_ONLY]
    header = {
        "mcp": importlib.metadata.version("mcp"),
        "anyio": importlib.metadata.version("anyio"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "launcher": options.launcher,
        "fake_python": options.python,
        "cli_handler": options.cli_handler,
    }
    print(json.dumps(header, ensure_ascii=False))
    unmarked: list[str] = []
    unstopped: list[str] = []
    for case in cases:
        record = run_case(case, options.launcher, options.python, options.cli_handler)
        print(json.dumps({"case": case, **record}, ensure_ascii=False))
        if not record["marked"]:
            unmarked.append(case)
        after_stop = record["beating_after_stop_file"]
        if isinstance(after_stop, dict) and any(after_stop.values()):
            unstopped.append(case)
    print(json.dumps({"unmarked": unmarked, "unstopped": unstopped}, ensure_ascii=False))
    return 1 if unmarked or unstopped else 0


if __name__ == "__main__":
    sys.exit(main())
