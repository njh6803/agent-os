"""BaseHTTPMiddleware 둘 뒤의 SSE: 조각별 전달과 끊김 전파, 그리고 요청 밖 태스크의 생존."""

import asyncio
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request, Response
from fastapi.sse import EventSourceResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

log: list[str] = []
release = asyncio.Event()
background_done = asyncio.Event()


class MW(BaseHTTPMiddleware):
    def __init__(self, app, *, name: str) -> None:
        super().__init__(app)
        self.name = name

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        r = await call_next(request)
        r.headers[f"x-{self.name}"] = "1"
        return r


app = FastAPI()
tasks: set[asyncio.Task[None]] = set()


async def detached() -> None:
    # 요청 밖에서 도는 '실행'의 대역. 끊겨도 끝까지 가는지 본다.
    for i in range(3):
        await asyncio.sleep(0.05)
        log.append(f"detached {i}")
    background_done.set()


@app.post("/runs", response_class=EventSourceResponse)
async def runs() -> AsyncIterator[dict[str, int]]:
    t = asyncio.get_running_loop().create_task(detached())
    tasks.add(t)
    try:
        yield {"n": 1}
        log.append("gen after first yield")
        await release.wait()
        yield {"n": 2}
        log.append("gen after second yield")
    except BaseException as e:
        log.append(f"gen got {type(e).__name__}")
        raise


app.add_middleware(MW, name="inner")
app.add_middleware(MW, name="outer")


async def main() -> None:
    sent: list[dict] = []
    first_body = asyncio.Event()
    disconnect = asyncio.Event()
    req_sent = False

    async def receive():
        nonlocal req_sent
        if not req_sent:
            req_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await disconnect.wait()
        return {"type": "http.disconnect"}

    async def send(msg):
        sent.append(msg)
        if msg["type"] == "http.response.body" and msg.get("body"):
            log.append(f"send body {msg['body']!r}")
            first_body.set()

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/runs",
        "raw_path": b"/runs",
        "query_string": b"",
        "root_path": "",
        "headers": [],
        "client": ("127.0.0.1", 1),
        "server": ("127.0.0.1", 80),
    }
    call = asyncio.create_task(app(scope, receive, send))
    await asyncio.wait_for(first_body.wait(), 2)
    log.append("FIRST CHUNK ARRIVED BEFORE RELEASE (incremental)")
    start = next(m for m in sent if m["type"] == "http.response.start")
    log.append(f"status {start['status']} headers {[k for k, _ in start['headers']]}")
    disconnect.set()
    await asyncio.wait_for(call, 2)
    log.append("app call returned after disconnect")
    await asyncio.wait_for(background_done.wait(), 2)
    log.append("detached task finished")


asyncio.run(main())
print("\n".join(log))
