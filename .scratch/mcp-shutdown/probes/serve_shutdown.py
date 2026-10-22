"""serve 를 멈출 때 실행이 띄운 MCP 서버가 내려가는지, 멈추는 데 얼마가 드는지 잰다.

자식 프로세스가 `main.py`의 `serve`와 같은 설정으로 uvicorn 을
띄운다(`timeout_graceful_shutdown=5`). 앱의 수명은 `channel/http/runs.py`의 `Runs.lifespan`과 같은
모양이다 — anyio 태스크 그룹을 열고, 닫힐 때 그 범위를 취소한다. `POST /start`가 그 그룹에 실행
하나를 띄운다. 실행은 core 처럼 기한 범위 안에서 감싸는 프로세스 → 입력이 닫혀도 끝나지 않는
서버(`fakes.py`)에 붙어 `slow(600)`을 부른다. 그 범위는 이 프로브를 처음 쓸 때의 core 처럼
`fail_after`다. #325 뒤의 core 는 `move_on_after`이고, 둘은 범위가 끝날 때 예외를 내는지만 다르다.
`GET /stream`은 끝나지 않는 응답이고, 실행의 스트림이 열려 있는 것을 흉내 낸다.

사례:
- `graceful`: 신호 하나(POSIX SIGINT, 윈도우 CTRL_BREAK). uvicorn 이 연결을 5초 기다린 뒤 수명을
  닫는다.
- `force`(POSIX만): SIGINT 둘(1초 사이). 둘째가 uvicorn 의 강제 종료라 수명 닫기를 건너뛰고,
  asyncio 가 남은 태스크를 취소한 뒤 끝나기를 기다린다.
- `force_then_interrupt`(POSIX만): `force`에 SIGINT 하나를 더한다. 셋째는 수명의 닫기가 시작된 0.3초
  뒤, 곧 asyncio 가 남은 태스크를 기다리는 동안 온다(그때는 uvicorn 의 신호 처리기가 풀려 있다).
- `sigkill`: serve 자식을 SIGKILL(윈도우는 TerminateProcess)로 끈다.

표지: 신호 전에 `slow`가 시작했고 스트림이 열려 첫 조각을 받았으며 serve 자식이 끝났다.
`force_then_interrupt`는 셋째 신호를 보낼 때 수명의 닫기가 시작했고 실행의 닫기가 아직 끝나지
않았어야 한다. 없는 사례는 측정이 아니라고 세고 종료 코드를 1로 둔다. 남은 프로세스는 멈춤 파일로
끝낸다.

선택은 `close_paths.py`와 같은 `--launcher`(POSIX만)다. 돌리는 명령은 `README.md`에 있다.
"""

from __future__ import annotations

import argparse
import http.client
import importlib.metadata
import json
import os
import platform
import signal
import socket
import subprocess
import sys
import sysconfig
import tempfile
import threading
import time
import urllib.request
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

import anyio
from anyio.abc import TaskGroup

HERE = Path(__file__).resolve().parent
FAKES = HERE / "fakes.py"
LAUNCHER = HERE / "launcher.py"
SITE = sysconfig.get_paths()["purelib"]
GRACE_SECONDS = 5
WINDOW_SECONDS = 0.6
# 사례마다 보낼 신호. (기준, 초, 종류)이고 기준은 첫 신호(start)나 수명의 닫기 시작(closing)이다.
SIGNALS: dict[str, tuple[tuple[str, float, str], ...]] = {
    "graceful": (("start", 0.0, "int"),),
    "force": (("start", 0.0, "int"), ("start", 1.0, "int")),
    "force_then_interrupt": (
        ("start", 0.0, "int"),
        ("start", 1.0, "int"),
        ("closing", 0.3, "int"),
    ),
    "sigkill": (("start", 0.0, "kill"),),
}
POSIX_ONLY = {"force", "force_then_interrupt"}


def _params(work: Path, launcher: str) -> tuple[str, list[str]]:
    stop = str(work / "stop")
    server = [str(work / "server.hb"), stop, SITE, "stay", "-", "keep"]
    command = sys._base_executable
    args = [str(FAKES), "wrapper", str(work / "wrapper.hb"), stop, *server]
    if launcher == "none":
        return command, args
    watch = ["--watch-parent"] if launcher == "watch" else []
    return sys.executable, ["-I", str(LAUNCHER), *watch, command, *args]


def _serve(work: Path, port: int, launcher: str) -> None:
    """serve 자식. uvicorn 이 끝나면 돌아온다."""
    import uvicorn
    from mcp import ClientSession, StdioServerParameters, stdio_client
    from starlette.applications import Starlette
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response, StreamingResponse
    from starlette.routing import Route

    command, args = _params(work, launcher)
    params = StdioServerParameters(command=command, args=args)
    groups: list[TaskGroup] = []

    async def run_one() -> None:
        try:
            with anyio.fail_after(600):
                with (work / "errlog.txt").open("w", encoding="utf-8") as errlog:
                    async with stdio_client(params, errlog=errlog) as (read, write):
                        async with ClientSession(read, write) as session:
                            await session.initialize()
                            await session.call_tool("slow", {"seconds": 600})
        finally:
            (work / "run_ended").write_text(str(time.time()))

    @asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with anyio.create_task_group() as group:
            groups.append(group)
            try:
                yield
            finally:
                (work / "lifespan_closing").write_text(str(time.time()))
                group.cancel_scope.cancel()

    async def start(request: Request) -> Response:
        groups[0].start_soon(run_one)
        return JSONResponse({"started": True})

    async def stream(request: Request) -> Response:
        async def chunks() -> AsyncIterator[bytes]:
            while True:
                yield b"."
                await anyio.sleep(0.5)

        return StreamingResponse(chunks())

    app = Starlette(
        routes=[Route("/start", start, methods=["POST"]), Route("/stream", stream)],
        lifespan=lifespan,
    )
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=port,
        timeout_graceful_shutdown=GRACE_SECONDS,
        log_level="warning",
    )


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for(check: object, seconds: float) -> bool:
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if callable(check) and check():
            return True
        time.sleep(0.05)
    return False


def _listening(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.2):
            return True
    except OSError:
        return False


def _beating(work: Path) -> dict[str, bool | None]:
    roles = ("wrapper", "server")
    before = {role: _size(work / f"{role}.hb") for role in roles}
    time.sleep(WINDOW_SECONDS)
    return {
        role: None if before[role] is None else _size(work / f"{role}.hb") != before[role]
        for role in roles
    }


def _size(path: Path) -> int | None:
    try:
        return path.stat().st_size
    except FileNotFoundError:
        return None


def _read_time(path: Path) -> float | None:
    try:
        return float(path.read_text())
    except (FileNotFoundError, ValueError):
        return None


def run_case(case: str, launcher: str) -> dict[str, object]:
    work = Path(tempfile.mkdtemp(prefix=f"mcp-serve-{case}-"))
    port = _free_port()
    flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
    child = subprocess.Popen(
        [sys.executable, __file__, "--serve", str(work), str(port), launcher],
        creationflags=flags,
        stdout=subprocess.DEVNULL,
        stderr=(work / "serve_stderr.txt").open("w", encoding="utf-8"),
    )
    record: dict[str, object] = {"listening": _wait_for(lambda: _listening(port), 30)}
    base = f"http://127.0.0.1:{port}"
    urllib.request.urlopen(urllib.request.Request(f"{base}/start", method="POST"), timeout=10)
    marker = work / "server.hb.slow"
    record["slow_started"] = _wait_for(marker.exists, 30)
    stream: dict[str, float | int] = {"chunks": 0}

    def read_stream() -> None:
        try:
            with urllib.request.urlopen(f"{base}/stream", timeout=120) as response:
                while response.read(1):
                    stream["chunks"] = int(stream["chunks"]) + 1
        except (OSError, http.client.HTTPException):
            pass  # 서버가 응답 중간에 연결을 끊으면 청크가 덜 와 IncompleteRead 다
        stream["closed"] = time.time()

    threading.Thread(target=read_stream, daemon=True).start()
    record["stream_open"] = _wait_for(lambda: int(stream["chunks"]) > 0, 10)
    first = time.time()
    closing = work / "lifespan_closing"
    for basis, offset, kind in SIGNALS[case]:
        if basis == "closing":
            record["closing_before_signal"] = _wait_for(closing.exists, 30)
            at = (_read_time(closing) or time.time()) + offset
        else:
            at = first + offset
        _wait_for(lambda at=at: time.time() >= at, offset + 1)
        if basis == "closing":
            record["run_closing_at_signal"] = not (work / "run_ended").exists()
        if kind == "kill":
            child.kill()
        else:
            child.send_signal(signal.CTRL_BREAK_EVENT if os.name == "nt" else signal.SIGINT)
    try:
        child.wait(timeout=60)
        exited = time.time()
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait()
        exited = None
    record["exit_code"] = child.returncode
    if exited is not None:
        record["signal_to_exit_seconds"] = round(exited - first, 3)
    for name in ("lifespan_closing", "run_ended"):
        at = _read_time(work / name)
        record[f"signal_to_{name}_seconds"] = None if at is None else round(at - first, 3)
    closed = stream.get("closed")
    record["signal_to_stream_closed_seconds"] = (
        None if closed is None else round(float(closed) - first, 3)
    )
    record["beating_right_after"] = _beating(work)
    time.sleep(3)
    record["beating_3s_later"] = _beating(work)
    (work / "stop").touch()
    time.sleep(0.5)
    record["beating_after_stop_file"] = _beating(work)
    record["marked"] = bool(
        record["slow_started"]
        and record["stream_open"]
        and exited is not None
        and record.get("closing_before_signal", True)
        and record.get("run_closing_at_signal", True)
    )
    record["serve_stderr_tail"] = (work / "serve_stderr.txt").read_text(
        encoding="utf-8", errors="replace"
    )[-300:]
    record["work"] = str(work)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--launcher", choices=("none", "kill", "watch"), default="none")
    parser.add_argument("--serve", nargs=3)
    parser.add_argument("cases", nargs="*")
    options = parser.parse_args()
    if options.serve is not None:
        work, port, launcher = options.serve
        _serve(Path(work), int(port), launcher)
        return 0
    if options.launcher != "none" and os.name != "posix":
        print("런처는 POSIX에서만 고른다", file=sys.stderr)
        return 2
    cases = options.cases or [c for c in SIGNALS if os.name == "posix" or c not in POSIX_ONLY]
    header = {
        name: importlib.metadata.version(name) for name in ("mcp", "anyio", "uvicorn", "starlette")
    }
    header |= {"python": platform.python_version(), "platform": platform.platform()}
    header |= {"launcher": options.launcher}
    print(json.dumps(header, ensure_ascii=False))
    unmarked: list[str] = []
    unstopped: list[str] = []
    for case in cases:
        record = run_case(case, options.launcher)
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
