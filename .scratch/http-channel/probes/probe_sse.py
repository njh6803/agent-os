"""FastAPI 0.141 yield 라우트의 두 성질을 잰다.

1. 첫 항목 전에 예외가 나면 상태 코드는 무엇인가.
2. 클라이언트가 끊으면 제너레이터에 무엇이 들어가나.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse

app = FastAPI()
seen: list[str] = []


@app.post("/boom", response_class=EventSourceResponse)
async def boom() -> AsyncIterator[dict[str, str]]:
    raise LookupError("실행 전 실패")
    yield {"never": "x"}


@app.post("/slow", response_class=EventSourceResponse)
async def slow() -> AsyncIterator[dict[str, int]]:
    try:
        for i in range(50):
            yield {"i": i}
            await asyncio.sleep(0.1)
        seen.append("finished")
    except BaseException as error:  # 무엇이 들어오는지 본다
        seen.append(type(error).__name__)
        raise


async def raw_call(path: str, disconnect_after: float | None) -> list[dict[str, object]]:
    sent: list[dict[str, object]] = []
    body_sent = False

    async def receive() -> dict[str, object]:
        nonlocal body_sent
        if not body_sent:
            body_sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        if disconnect_after is None:
            await asyncio.sleep(3600)
        else:
            await asyncio.sleep(disconnect_after)
        return {"type": "http.disconnect"}

    async def send(message: dict[str, object]) -> None:
        sent.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 1),
        "server": ("127.0.0.1", 80),
        "scheme": "http",
        "root_path": "",
    }
    try:
        await app(scope, receive, send)
    except Exception as error:
        sent.append({"type": "app-raised", "error": repr(error)})
    return sent


async def main() -> None:
    boom_sent = await raw_call("/boom", disconnect_after=None)
    print("boom:", [(m["type"], m.get("status")) for m in boom_sent])
    slow_sent = await raw_call("/slow", disconnect_after=0.35)
    chunks = [m for m in slow_sent if m["type"] == "http.response.body"]
    print("slow: start", [m.get("status") for m in slow_sent if m["type"] == "http.response.start"])
    print("slow: body chunks", len(chunks))
    await asyncio.sleep(0.5)
    print("generator saw:", seen)

    pass


asyncio.run(main())
