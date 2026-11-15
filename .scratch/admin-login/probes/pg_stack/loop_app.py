"""서버가 쓰는 이벤트 루프 안에서 조합을 돌리는 작은 FastAPI 앱.

`src/agent_os/main.py` 의 `_serve` 가 부르는 모양 그대로 띄운다. 곧
`uvicorn.run(app, host=, port=, timeout_graceful_shutdown=)` 이고 `loop` 인자를 주지 않는다.
`--loop` 를 주면 그 값만 `uvicorn.run` 의 `loop` 로 넘긴다(가르는 갈래, 예
`asyncio:SelectorEventLoop`).

경로. `/loop` 는 도는 루프의 클래스 이름, `/exercise?label=` 은 조합 하나(동기 조합은 서버가 하듯
작업 스레드에서 돈다), `/subprocess` 는 anyio 로 자식 프로세스 하나를 띄운다, `/mcp` 는 stdio MCP
서버 하나를 저장소의 MCP 어댑터와 같은 호출(`stdio_client` 와 `ClientSession`)로 열어 도구 목록을
받는다, `/shutdown` 은 자기에게 SIGINT 를 보내 uvicorn 이 스스로 끝나게 한다. 측정의 셈은 `run.py`
가, 요청은 `loop_client.py` 가 한다. 이 파일은 도우미다.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import signal
import sys
from dataclasses import asdict
from pathlib import Path

import anyio
import anyio.to_thread
import uvicorn
from exercise import DSN_ENV, SYNC_LABELS, run_async_stack, run_sync_stack
from fastapi import FastAPI
from mcp import ClientSession, StdioServerParameters, stdio_client

SHUTDOWN_GRACE_SECONDS = 5
MCP_SERVER = Path(__file__).resolve().parent / "mcp_probe_server.py"

app = FastAPI()

type Reply = dict[str, str | int | bool | list[bool]]


def loop_name() -> str:
    return type(asyncio.get_running_loop()).__name__


@app.get("/loop")
async def loop() -> Reply:
    return {"loop": loop_name(), "platform": sys.platform}


@app.get("/exercise")
async def exercise(label: str) -> Reply:
    dsn = os.environ[DSN_ENV]
    if label in SYNC_LABELS:
        outcome = await anyio.to_thread.run_sync(run_sync_stack, label, dsn, loop_name())
    else:
        outcome = await run_async_stack(label, dsn)
    fields = asdict(outcome)
    return {**fields, "deleted": list(outcome.deleted)}


@app.get("/subprocess")
async def subprocess() -> Reply:
    try:
        done = await anyio.run_process([sys.executable, "-c", "print('child-ok')"])
    except NotImplementedError as error:
        return {"ok": False, "loop": loop_name(), "error": f"NotImplementedError: {error}"}
    return {"ok": True, "loop": loop_name(), "stdout": done.stdout.decode().strip()}


@app.get("/mcp")
async def mcp_stdio() -> Reply:
    """stdio MCP 서버 하나를 `src/agent_os/adapters/mcp.py` 의 `_stdio_session` 과 같은 호출로
    연다."""
    parameters = StdioServerParameters(command=sys.executable, args=[str(MCP_SERVER)])

    async def tool_names() -> list[str]:
        async with stdio_client(parameters) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            return [tool.name for tool in (await session.list_tools()).tools]

    try:
        names = await tool_names()
    except Exception as error:  # 루프가 이 길을 막는지를 결과 한 줄로 남긴다
        return {"ok": False, "loop": loop_name(), "error": f"{type(error).__name__}: {error}"}
    return {"ok": True, "loop": loop_name(), "tools": ",".join(names)}


@app.post("/shutdown")
async def shutdown() -> Reply:
    signal.raise_signal(signal.SIGINT)
    return {"stopping": True}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--loop", default="")
    args = parser.parse_args()
    port: int = args.port
    loop_option: str = args.loop
    if loop_option:
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=port,
            timeout_graceful_shutdown=SHUTDOWN_GRACE_SECONDS,
            loop=loop_option,
        )
    else:
        uvicorn.run(
            app, host="127.0.0.1", port=port, timeout_graceful_shutdown=SHUTDOWN_GRACE_SECONDS
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
