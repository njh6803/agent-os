"""루프백(127.0.0.1)의 빈 포트에 뜨는 가짜 모델 서버. 프로브가 가져다 쓴다(측정이 아니다).

표준 라이브러리의 `http.server`만 쓴다. 받은 요청을 줄(메서드와 경로), 헤더 전부, 본문 그대로
기록하고, 사례가 정해 준 응답 함수의 답을 돌려준다. 로깅 모듈을 쓰지 않아 프로브가 모으는 로그
레코드에 서버의 줄이 섞이지 않는다. 스트리밍(SSE)은 하지 않는다. 루프는 `ainvoke`만 부른다.

서버는 프로브 프로세스 안의 daemon 스레드에서 돈다. 따로 띄운 프로세스가 없어 끌 번호가 없다.
"""

from __future__ import annotations

import json
import socket
import threading
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import TracebackType

CHAT_PATH = "/v1/chat/completions"


@dataclass(frozen=True)
class Received:
    """서버가 받은 요청 하나."""

    method: str
    target: str
    headers: tuple[tuple[str, str], ...]
    body: bytes

    def header(self, name: str) -> list[str]:
        return [value for key, value in self.headers if key.lower() == name.lower()]

    def json(self) -> dict[str, object] | None:
        try:
            parsed = json.loads(self.body)
        except ValueError:
            return None
        return parsed if isinstance(parsed, dict) else None

    def mentions(self, needle: str) -> list[str]:
        """이 요청의 어느 자리에 그 글자가 실렸는지. 경로, 헤더(이름과 값), 본문을 본다."""
        places: list[str] = []
        if needle in self.target:
            places.append("target")
        places.extend(f"header:{key}" for key, value in self.headers if needle in f"{key}: {value}")
        if needle.encode() in self.body:
            places.append("body")
        return places


@dataclass(frozen=True)
class Reply:
    status: int
    body: bytes
    content_type: str = "application/json"
    headers: tuple[tuple[str, str], ...] = ()


type Responder = Callable[[Received], Reply]


def completion(
    *,
    content: str | None = "pong",
    tool_calls: Sequence[Mapping[str, object]] | None = None,
    model: str | None = "served-model-name",
    usage: Mapping[str, object] | None = None,
    message_extra: Mapping[str, object] | None = None,
    finish_reason: str = "stop",
) -> Reply:
    """Chat Completions 의 정상 응답. `message_extra`는 메시지에 덧붙일 칸이다(사고 글 등)."""
    message: dict[str, object] = {"role": "assistant", "content": content}
    if tool_calls is not None:
        message["tool_calls"] = list(tool_calls)
    if message_extra is not None:
        message.update(message_extra)
    payload: dict[str, object] = {
        "id": "chatcmpl-probe",
        "object": "chat.completion",
        "created": 1,
        "choices": [{"index": 0, "message": message, "finish_reason": finish_reason}],
    }
    if model is not None:
        payload["model"] = model
    if usage is not None:
        payload["usage"] = dict(usage)
    return Reply(200, json.dumps(payload).encode())


def tool_call(name: str, arguments: str, call_id: str = "call_1") -> dict[str, object]:
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": arguments}}


def error(status: int, message: str) -> Reply:
    """OpenAI 꼴의 오류 본문."""
    body = {"error": {"message": message, "type": "probe_error", "param": None, "code": None}}
    return Reply(status, json.dumps(body).encode())


def default_responder(request: Received) -> Reply:
    """Chat Completions 경로에는 글 응답을, 그 밖의 경로에는 404 를 준다."""
    if request.target.split("?", 1)[0] == CHAT_PATH:
        return completion(usage={"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18})
    return error(404, f"no route: {request.target}")


@dataclass
class FakeServer:
    """`with FakeServer(respond) as server:` 로 쓴다. `server.requests`가 받은 요청의 열이다."""

    respond: Responder = default_responder
    requests: list[Received] = field(default_factory=list[Received])
    # 받은 연결의 수와 처리를 마친 연결의 수. 뒤의 것은 클라이언트가 연결을 닫아 다음 요청 줄이 EOF
    # 로 끝나면 하나 는다. 서버는 쉬는 연결을 스스로 닫지 않는다(keep-alive 제한 시간이 없다).
    opened_connections: int = 0
    closed_connections: int = 0
    _httpd: ThreadingHTTPServer | None = None

    def __enter__(self) -> FakeServer:
        owner = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def _serve(self) -> None:
                length = int(self.headers.get("Content-Length") or 0)
                received = Received(
                    method=self.command,
                    target=self.path,
                    headers=tuple(self.headers.items()),
                    body=self.rfile.read(length) if length else b"",
                )
                owner.requests.append(received)
                reply = owner.respond(received)
                try:
                    self._send(reply)
                except OSError:  # 클라이언트가 답을 기다리지 않고 먼저 끊었다(취소 사례)
                    self.close_connection = True

            def _send(self, reply: Reply) -> None:
                self.send_response(reply.status)
                self.send_header("Content-Type", reply.content_type)
                self.send_header("Content-Length", str(len(reply.body)))
                for key, value in reply.headers:
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(reply.body)

            do_GET = _serve
            do_POST = _serve
            do_DELETE = _serve

            def setup(self) -> None:
                super().setup()
                owner.opened_connections += 1

            def finish(self) -> None:
                super().finish()
                owner.closed_connections += 1

            def log_message(self, format: str, *args: object) -> None:
                """서버의 접근 로그를 stderr 에 찍지 않는다."""

        httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        httpd.daemon_threads = True
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        self._httpd = httpd
        return self

    def __exit__(
        self,
        kind: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()

    @property
    def port(self) -> int:
        if self._httpd is None:
            raise RuntimeError("서버가 아직 뜨지 않았다")
        return self._httpd.server_address[1]

    @property
    def origin(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    @property
    def base_url(self) -> str:
        return f"{self.origin}/v1"

    def chat_requests(self) -> list[Received]:
        return [r for r in self.requests if r.target.split("?", 1)[0] == CHAT_PATH]


def closed_port() -> int:
    """아무도 듣지 않는 포트 하나. 잠깐 묶었다 놓은 포트라 곧바로는 다시 쓰이지 않는다고 본다."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]
