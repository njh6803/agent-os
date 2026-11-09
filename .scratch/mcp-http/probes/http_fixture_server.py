"""프로브용 streamable HTTP MCP 서버. `http_close.py`가
`sys.executable 이 파일 <포트> <기록 파일>`로 띄운다.

같은 `MCPServer`를 streamable HTTP 로 루프백 포트에 띄운다(ADR 0049 의 시험 픽스처 모양). 도구는
add 와 slow 둘이다. slow 는 잠들기 전에 표지 파일(`<기록 파일>.slow`)을 만든다 — 프로브가 기한이
slow 의 시작 뒤에 왔다는 표지로 쓴다. 앱 앞에 기록 미들웨어를 끼워 HTTP 요청마다 시각·메서드·경로·
쿼리 문자열·Authorization 헤더·Mcp-Session-Id 헤더를 기록 파일에 JSON 한 줄로 남긴다. 프로브는 그
줄로 종료 요청(DELETE)이 서버에 닿았는지, 헤더 값과 쿼리 문자열이 서버에 닿았는지를 본다.

선택 인자. `--expect-authorization <값>`을 주면 그 값과 다른 Authorization 헤더의 요청을
401(text/plain)로 막는다. `--delete-hang <초>`를 주면 DELETE 를 그 초만큼 잠재운 뒤 앱에 넘긴다(종료
요청에 답하지 않는 서버의 모양). 표준 출력에 `ready <포트>` 한 줄을 찍는 것은 uvicorn 이 아니라 이
파일이 뜬 표지이고, 프로브는 포트가 열렸는지를 TCP 접속으로 따로 본다.

uvicorn 의 기본 로그는 끈다(`log_level="warning"`). 요청 기록은 미들웨어의 파일이다.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from collections.abc import Awaitable, Callable, MutableMapping
from pathlib import Path

import uvicorn
from mcp.server.mcpserver import MCPServer

Scope = MutableMapping[str, object]
Receive = Callable[[], Awaitable[MutableMapping[str, object]]]
Send = Callable[[MutableMapping[str, object]], Awaitable[None]]
App = Callable[[Scope, Receive, Send], Awaitable[None]]

server = MCPServer("fixture")
_options = argparse.Namespace(record="", expect_authorization=None, delete_hang=0.0)


@server.tool()
def add(a: int, b: int) -> int:
    return a + b


@server.tool()
async def slow(seconds: float) -> str:
    """표지를 만든 뒤 잠든다. 프로브는 표지의 시각이 기한보다 앞인지 본다."""
    Path(f"{_options.record}.slow").touch()
    await asyncio.sleep(seconds)
    return "done"


class Recording:
    """요청마다 한 줄을 기록하고, 선택으로 401 과 DELETE 잠재우기를 한다."""

    def __init__(self, app: App) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self._app(scope, receive, send)
            return
        headers = _headers(scope)
        method = str(scope.get("method"))
        query = scope.get("query_string")
        line = {
            "t": time.time(),
            "method": method,
            "path": str(scope.get("path")),
            "query": query.decode("utf-8", "replace") if isinstance(query, bytes) else "",
            "authorization": headers.get("authorization"),
            "session": headers.get("mcp-session-id"),
        }
        with Path(_options.record).open("a", encoding="utf-8") as record:
            record.write(json.dumps(line, ensure_ascii=False) + "\n")
        expected = _options.expect_authorization
        if expected is not None and headers.get("authorization") != expected:
            await _plain(send, 401, "unauthorized")
            return
        if method == "DELETE" and _options.delete_hang > 0:
            await asyncio.sleep(_options.delete_hang)
        await self._app(scope, receive, send)


def _headers(scope: Scope) -> dict[str, str]:
    raw = scope.get("headers")
    if not isinstance(raw, list):
        return {}
    pairs: dict[str, str] = {}
    for item in raw:
        if isinstance(item, tuple) and len(item) == 2:
            name, value = item
            if isinstance(name, bytes) and isinstance(value, bytes):
                pairs[name.decode("latin-1").lower()] = value.decode("latin-1")
    return pairs


async def _plain(send: Send, status: int, body: str) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"text/plain; charset=utf-8")],
        }
    )
    await send({"type": "http.response.body", "body": body.encode("utf-8")})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=int)
    parser.add_argument("record")
    parser.add_argument("--expect-authorization")
    parser.add_argument("--delete-hang", type=float, default=0.0)
    parser.parse_args(namespace=_options)
    app = Recording(server.streamable_http_app())
    print(f"ready {_options.port}", flush=True)
    sys.stdout.flush()
    uvicorn.run(app, host="127.0.0.1", port=_options.port, log_level="warning")


if __name__ == "__main__":
    main()
