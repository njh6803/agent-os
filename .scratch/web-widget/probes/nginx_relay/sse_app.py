"""nginx 중계 측정의 상류. 저장소가 잠근 fastapi 의 `EventSourceResponse` 로 SSE 를 낸다.

measure.py 가 띄운다. 손으로 띄우려면 저장소 루트에서

    uv run python .scratch/web-widget/probes/nginx_relay/sse_app.py <포트> <기록 파일>

경로. 메서드는 GET·POST 둘 다 받는다. 채널의 실행 시작이 POST 라 measure.py 는 POST 로
부른다.

- `/chat/stream?count=10&interval_ms=500` 프레임
  `data: {"seq": n, "sent_ms": 보낸 시각}` 을 간격마다 하나씩 count 개 내고 닫는다.
  시각은 epoch 밀리초라 같은 기계의 클라이언트가 도착 시각과 뺀다.
- `/chat/quiet?silence_s=90` 프레임 하나, silence_s 초 침묵, 프레임 하나. 침묵 동안
  fastapi 가 15초마다 `: ping` 주석을 넣는다(fastapi/routing.py 의 `_PING_INTERVAL`).
  모델 호출이 조용한 동안의 흉내다.
- `/chat/quiet-raw?silence_s=90` 같은 모양이되 keepalive 가 없는 대조군.
  `EventSourceResponse` 가 아닌 `StreamingResponse` 로 같은 헤더
  (`Cache-Control: no-cache`, `X-Accel-Buffering: no`)를 낸다.
- `/chat/broken?after=2` 프레임 after 개를 0.2초 간격으로 내고 생성기가 예외를 던진다.
  fastapi 는 생성기를 작업 그룹의 생산자 태스크에서 돌려, 예외가 나도 응답은 마지막
  청크로 닫히고 예외는 그 뒤에 올라온다(기록의 done 이 finished: true).
- `/chat/broken-raw?after=2` 같은 모양을 `StreamingResponse` 로. 응답이 시작된 뒤의 예외에
  uvicorn 은 연결을 그냥 닫는다(h11_impl.py 의 run_asgi). 상류 프로세스가 응답 도중
  죽는 흉내다.
- 그 밖 전부 `{"upstream": "python", "path": ..., "raw_path": ...}` 를 200 으로.
  허용 목록 측정에서 요청이 파이썬에 닿았는지와 파이썬이 본 경로를 가르는 표지다.
  `/openapi.json` 도 여기로 온다(openapi_url=None).

기록 파일에는 JSON 한 줄씩 남긴다. `request`(받은 요청), `disconnect`(앱이
`http.disconnect` 를 받은 시각과 그때까지 응답을 다 보냈는지·보낸 프레임과 ping 수),
`done`(앱이 응답을 끝낸 시각). uvicorn 은 ASGI spec 2.3 을 알리므로 starlette 의
`StreamingResponse` 가 `receive()` 로 끊김을 기다린다. `disconnect` 는 상류 TCP 연결이
닫힌 것을 uvicorn 이 알아챈 시각이다.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.sse import EventSourceResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

ALL_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]


def now_ms() -> int:
    return int(time.time() * 1000)


def frame(seq: int) -> bytes:
    payload = json.dumps({"seq": seq, "sent_ms": now_ms()})
    return f"data: {payload}\n\n".encode()


app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)


@app.api_route("/chat/stream", methods=["GET", "POST"], response_class=EventSourceResponse)
async def stream(count: int = 10, interval_ms: int = 500) -> AsyncIterator[dict[str, int]]:
    for seq in range(1, count + 1):
        if seq > 1:
            await asyncio.sleep(interval_ms / 1000)
        yield {"seq": seq, "sent_ms": now_ms()}


@app.api_route("/chat/quiet", methods=["GET", "POST"], response_class=EventSourceResponse)
async def quiet(silence_s: float = 90) -> AsyncIterator[dict[str, int]]:
    yield {"seq": 1, "sent_ms": now_ms()}
    await asyncio.sleep(silence_s)
    yield {"seq": 2, "sent_ms": now_ms()}


@app.api_route("/chat/quiet-raw", methods=["GET", "POST"])
async def quiet_raw(silence_s: float = 90) -> StreamingResponse:
    async def body() -> AsyncIterator[bytes]:
        yield frame(1)
        await asyncio.sleep(silence_s)
        yield frame(2)

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(body(), media_type="text/event-stream", headers=headers)


@app.api_route("/chat/broken", methods=["GET", "POST"], response_class=EventSourceResponse)
async def broken(after: int = 2) -> AsyncIterator[dict[str, int]]:
    for seq in range(1, after + 1):
        yield {"seq": seq, "sent_ms": now_ms()}
        await asyncio.sleep(0.2)
    raise RuntimeError("probe: 상류가 응답 도중 죽는다")


@app.api_route("/chat/broken-raw", methods=["GET", "POST"])
async def broken_raw(after: int = 2) -> StreamingResponse:
    async def body() -> AsyncIterator[bytes]:
        for seq in range(1, after + 1):
            yield frame(seq)
            await asyncio.sleep(0.2)
        raise RuntimeError("probe: 상류가 응답 도중 죽는다")

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(body(), media_type="text/event-stream", headers=headers)


@app.api_route("/{rest:path}", methods=ALL_METHODS)
async def reached(request: Request) -> JSONResponse:
    raw_path: bytes = request.scope["raw_path"]
    return JSONResponse(
        {
            "upstream": "python",
            "path": request.scope["path"],
            "raw_path": raw_path.decode("latin-1"),
        }
    )


@dataclass
class ResponseState:
    finished: bool = False
    frames: int = 0
    pings: int = 0
    disconnect_seen: bool = False


class Recorder:
    """받은 요청, 연결 끊김, 응답 끝을 기록 파일에 JSON 한 줄씩 남기는 ASGI 감싸개."""

    def __init__(self, inner: ASGIApp, log_path: Path) -> None:
        self.inner = inner
        self.log = log_path.open("a", encoding="utf-8")

    def write(self, record: dict[str, object]) -> None:
        self.log.write(json.dumps(record, ensure_ascii=False) + "\n")
        self.log.flush()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.inner(scope, receive, send)
            return
        raw_path: bytes = scope["raw_path"]
        query: bytes = scope["query_string"]
        base: dict[str, object] = {
            "method": scope["method"],
            "path": scope["path"],
            "raw_path": raw_path.decode("latin-1"),
            "query": query.decode("latin-1"),
            "http_version": scope["http_version"],
        }
        self.write({"event": "request", "t": now_ms(), **base})
        state = ResponseState()

        def progress() -> dict[str, object]:
            return {"finished": state.finished, "frames": state.frames, "pings": state.pings}

        async def watched_receive() -> Message:
            message = await receive()
            if message["type"] == "http.disconnect" and not state.disconnect_seen:
                state.disconnect_seen = True
                self.write({"event": "disconnect", "t": now_ms(), **progress(), **base})
            return message

        async def counted_send(message: Message) -> None:
            if message["type"] == "http.response.body":
                body: bytes = message.get("body", b"")
                state.frames += body.count(b"data: ")
                state.pings += body.count(b": ping")
                if not message.get("more_body", False):
                    state.finished = True
            await send(message)

        try:
            await self.inner(scope, watched_receive, counted_send)
        finally:
            self.write({"event": "done", "t": now_ms(), **progress(), **base})


def main() -> None:
    port = int(sys.argv[1])
    log_path = Path(sys.argv[2])
    uvicorn.run(Recorder(app, log_path), host="127.0.0.1", port=port, log_level="warning")


if __name__ == "__main__":
    main()
