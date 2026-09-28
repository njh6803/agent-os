"""연결이 남은 SSE 스트림이 있을 때 uvicorn 0.53.0 이 멈추는 순서를 잰다."""

from __future__ import annotations

import asyncio
import socket
import sys
import time
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI
from fastapi.sse import EventSourceResponse

T0 = time.monotonic()
GRACE = None if sys.argv[1] == "none" else int(sys.argv[1])


def log(msg: str) -> None:
    print(f"{time.monotonic() - T0:6.2f}s {msg}", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    log("lifespan startup")
    yield
    log("lifespan shutdown 시작 (여기서 앱 소유 실행을 취소할 자리)")


app = FastAPI(lifespan=lifespan)


@app.get("/slow", response_class=EventSourceResponse)
async def slow() -> AsyncIterator[dict[str, int]]:
    for i in range(4):
        yield {"i": i}
        log(f"route: 이벤트 {i} 보냄, 1.5초 뒤 다음")
        await asyncio.sleep(1.5)
    log("route: 결말까지 보냄")


async def main() -> None:
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()
    config = uvicorn.Config(
        app, host="127.0.0.1", port=port, log_level="warning", timeout_graceful_shutdown=GRACE
    )
    server = uvicorn.Server(config)
    serving = asyncio.create_task(server.serve())
    while not server.started:
        await asyncio.sleep(0.05)
    async with httpx.AsyncClient(timeout=None) as client:
        try:
            async with client.stream("GET", f"http://127.0.0.1:{port}/slow") as resp:
                async for chunk in resp.aiter_text():
                    log(f"client: 받음 {chunk.strip()!r}")
                    if '"i": 0' in chunk or '"i":0' in chunk:
                        log("멈춤 요청 (SIGINT 와 같은 should_exit=True)")
                        server.should_exit = True
            log("client: 스트림 정상 종료")
        except Exception as error:
            log(f"client: 끊김 {type(error).__name__}")
    await serving
    log("server.serve() 반환")


asyncio.run(main())
