"""테스트용 streamable HTTP MCP 서버. 어댑터 시험과 core 시험과 실제 모델 시험이 함께 쓴다.

`sys.executable 이 파일 <포트> <기록 파일> [선택 인자]`로 띄우고 `tests/mcp_http.py` 의
`serving` 이 그 일을 맡는다. stdio 픽스처(`tests/adapters/mcp_fixture_server.py`)와 같은
`MCPServer` 에 add, 잠드는 slow, 받은 비밀의 길이를 돌려주는 keep 을 두고 앞에 기록 미들웨어를
끼운다. keep 이 비밀 값 자체를 돌려주지 않는 까닭은 돌려주면 서버의 응답이 라이브러리 로그에
실려 로그 시험이 값이 어디서 새는지 가르지 못하기 때문이다. 요청마다 메서드·경로·쿼리 문자열·요청
헤더 전부를 기록 파일에 JSON 한 줄로 남긴다. 헤더 이름은 소문자다.

선택 인자(`.scratch/mcp-http/probes/http_fixture_server.py` 가 같은 모양의 선례다).

- `--expect-authorization <값>`: 그 값과 다른 `Authorization` 의 요청을 401 로 막는다.
- `--echo <메서드>`: JSON-RPC 의 그 메서드(`initialize`, `tools/call`)에 401 과, 받은
  `Authorization` 값을 글에 담은 JSON-RPC 오류 본문을 돌려준다. 값을 되울리는 서버의 모양이다.
- `--redirect`: 경로 끝에 `/` 가 없는 요청을 `/` 를 붙인 같은 출처의 경로로 307 로 돌려보낸다. 끝에
  `/` 가 붙은 요청은 `/` 를 떼고 앱에 넘긴다.
- `--list-error`: 도구 목록 요청(`tools/list`)에 HTTP 200 과 JSON-RPC 오류 본문으로 답한다.
- `--delete-sleep <초>`: 세션 종료 요청(DELETE)에 답하지 않고 그 초만큼 잠든다.
- `--delete-drop`: DELETE 에 상태줄과 헤더만 보내고 본문 없이 연결을 끊는다. 클라이언트에는 응답이
  끝까지 오지 않은 채 연결이 끊긴 것으로 보인다.
- `--delete-redirect <주소>`: DELETE 만 그 주소로 307 로 돌려보낸다. 다른 출처(다른 포트의 두 번째
  서버)를 주면 그 서버의 기록 파일로 요청이 닿았는지 본다.
- `--stateless`: 세션을 두지 않는 서버로 띄운다. 응답에 `mcp-session-id` 헤더가 없다.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import time
from collections.abc import Awaitable, Callable, MutableMapping
from pathlib import Path
from typing import TypeGuard

import uvicorn
from mcp.server.mcpserver import MCPServer

Scope = MutableMapping[str, object]
Message = MutableMapping[str, object]
Receive = Callable[[], Awaitable[Message]]
Send = Callable[[Message], Awaitable[None]]
App = Callable[[Scope, Receive, Send], Awaitable[None]]

server = MCPServer("http-fixture")
_options = argparse.Namespace(
    record="",
    expect_authorization=None,
    echo=None,
    redirect=False,
    list_error=False,
    delete_sleep=0.0,
    delete_drop=False,
    delete_redirect=None,
    stateless=False,
)


@server.tool()
def add(a: int, b: int) -> int:
    return a + b


@server.tool()
async def slow(seconds: float) -> str:
    """표지(`<기록 파일>.slow`)를 만든 뒤 잠든다. 기한이 도구 호출 도중에 왔다는 표지다."""
    Path(f"{_options.record}.slow").touch()
    await asyncio.sleep(seconds)
    return "done"


@server.tool()
def keep(secret: str) -> str:
    """받은 비밀을 돌려주지 않고 길이만 돌려준다."""
    return str(len(secret))


class Recording:
    def __init__(self, app: App) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != "http":
            await self._app(scope, receive, send)
            return
        headers = _headers(scope)
        method = str(scope.get("method"))
        path = str(scope.get("path"))
        query = scope.get("query_string")
        line = {
            "t": time.time(),
            "method": method,
            "path": path,
            "query": query.decode("utf-8", "replace") if isinstance(query, bytes) else "",
            "headers": headers,
        }
        with Path(_options.record).open("a", encoding="utf-8") as record:
            record.write(json.dumps(line, ensure_ascii=False) + "\n")
        body = await _body(receive) if method == "POST" else b""
        rpc = _rpc(body)
        rpc_method = rpc.get("method")
        rpc_id = rpc.get("id")
        authorization = headers.get("authorization")
        expected = _options.expect_authorization
        if expected is not None and authorization != expected:
            await _text(send, 401, "unauthorized")
            return
        if method == "DELETE" and await self._answer_delete(send, path):
            return
        if _options.echo is not None and rpc_method == _options.echo:
            echoed = f"bad credentials: {authorization} token={_last_word(authorization)}"
            await _json(send, 401, _rpc_error(rpc_id, echoed))
            return
        if _options.list_error and rpc_method == "tools/list":
            await _json(send, 200, _rpc_error(rpc_id, "tool list refused"))
            return
        if _options.redirect:
            if not path.endswith("/"):
                await _redirect(send, f"{path}/")
                return
            scope["path"] = path.rstrip("/")
            scope["raw_path"] = path.rstrip("/").encode("utf-8")
        await self._app(scope, _replay(body, receive), send)

    @staticmethod
    async def _answer_delete(send: Send, path: str) -> bool:
        """DELETE 만 받는 선택 인자 셋을 처리한다. 앱에 넘기지 않고 끝냈으면 참이다."""
        if _options.delete_redirect is not None:
            await _redirect(send, _options.delete_redirect)
            return True
        if _options.delete_drop:
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [(b"content-length", b"10")],
                }
            )
            raise ConnectionAbortedError(f"DELETE {path} 의 연결을 끊는다")
        if _options.delete_sleep > 0:
            await asyncio.sleep(_options.delete_sleep)
        return False


def _headers(scope: Scope) -> dict[str, str]:
    raw = scope.get("headers")
    if not _is_list(raw):
        return {}
    pairs: dict[str, str] = {}
    for item in raw:
        if _is_pair(item):
            name, value = item
            if isinstance(name, bytes) and isinstance(value, bytes):
                pairs[name.decode("latin-1").lower()] = value.decode("latin-1")
    return pairs


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _is_pair(value: object) -> TypeGuard[tuple[object, object]]:
    # ASGI 의 헤더는 (이름, 값) 쌍이다.
    return isinstance(value, tuple)


def _is_dict(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


async def _body(receive: Receive) -> bytes:
    chunks: list[bytes] = []
    while True:
        message = await receive()
        chunk = message.get("body")
        if isinstance(chunk, bytes):
            chunks.append(chunk)
        if not message.get("more_body"):
            return b"".join(chunks)


def _replay(body: bytes, receive: Receive) -> Receive:
    """읽어 버린 본문을 앱에 한 번 다시 준다. 그 뒤의 요청 메시지(연결 끊김 등)는 원래 것이다."""
    pending = [body]

    async def replay() -> Message:
        if pending:
            return {"type": "http.request", "body": pending.pop(), "more_body": False}
        return await receive()

    return replay


def _rpc(body: bytes) -> dict[str, object]:
    try:
        parsed = json.loads(body) if body else None
    except ValueError:
        return {}
    return parsed if _is_dict(parsed) else {}


def _rpc_error(rpc_id: object, text: str) -> dict[str, object]:
    return {"jsonrpc": "2.0", "id": rpc_id, "error": {"code": -32001, "message": text}}


def _last_word(value: str | None) -> str:
    return "" if value is None else value.split(" ")[-1]


async def _text(send: Send, status: int, body: str) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"text/plain; charset=utf-8")],
        }
    )
    await send({"type": "http.response.body", "body": body.encode("utf-8")})


async def _json(send: Send, status: int, body: dict[str, object]) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": status,
            "headers": [(b"content-type", b"application/json")],
        }
    )
    await send({"type": "http.response.body", "body": json.dumps(body).encode("utf-8")})


async def _redirect(send: Send, location: str) -> None:
    await send(
        {
            "type": "http.response.start",
            "status": 307,
            "headers": [(b"location", location.encode("utf-8")), (b"content-length", b"0")],
        }
    )
    await send({"type": "http.response.body", "body": b""})


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("port", type=int)
    parser.add_argument("record")
    parser.add_argument("--expect-authorization")
    parser.add_argument("--echo")
    parser.add_argument("--redirect", action="store_true")
    parser.add_argument("--list-error", action="store_true")
    parser.add_argument("--delete-sleep", type=float, default=0.0)
    parser.add_argument("--delete-drop", action="store_true")
    parser.add_argument("--delete-redirect")
    parser.add_argument("--stateless", action="store_true")
    parser.parse_args(namespace=_options)
    uvicorn.run(
        Recording(server.streamable_http_app(stateless_http=_options.stateless)),
        host="127.0.0.1",
        port=_options.port,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
