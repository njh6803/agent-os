"""가짜 모델 서버. 실제 모델 서버 없이 Chat Completions를 흉내 내는 시험 픽스처다.

`with FakeModelServer(응답, 응답, ...) as server:`로 쓴다. 서버는 시험 프로세스 안의 스레드로
루프백(127.0.0.1)의 빈 포트에 뜨고, 띄운 쪽이 쥔 핸들(`stop()`이나 `with`를 나가는 것)로만 끈다.
끄면 듣는 소켓만 닫혀 새 연결은 거부되지만, 클라이언트가 쥐고 있는 쉬는 연결은 그 클라이언트가
닫을 때까지 계속 답한다. 그래서 연결을 쥔 클라이언트가 있는 채로 서버가 죽는 사례는 이 픽스처로
재현되지 않는다. 같은 프로세스의 시험도, 시험이 자식 프로세스로 띄운 CLI도 `server.base_url`로
붙는다. 한 시험에서 서버 둘 이상을 함께 띄울 수 있고, 받은 요청과 연결의 셈은 서버마다 따로다.

- 받은 요청은 메서드, 경로, 헤더, 본문을 받은 차례로 `requests`에 적는다. 요청은 응답을 짓기 전에
  적히므로, 응답 함수가 돌 때 `requests`에는 그 요청이 이미 들어 있다.
- 응답은 시험이 차례로 정한다. 엔트리는 `Reply`(상태 코드와 본문. 본문은 JSON이거나 JSON이 아닌 날
  글자)이거나 받은 요청을 보고 `Reply`를 짓는 함수다. 함수는 요청을 받은 그 자리에서 돈다(서버
  스레드). `Reply.delay_seconds`는 답하기 전에 기다릴 시간이다. 정한 응답이 바닥난 뒤의 요청에는
  404와 오류 본문으로 답하고 그 요청도 적는다.
- 서버는 HTTP/1.1로 답하고 연결을 닫을지는 클라이언트가 정한다. 서버가 응답마다 연결을 닫으면 연결의
  셈이 어느 클라이언트에서나 "모두 닫혔다"가 되어 수명 사례가 퇴행을 가르지 못한다. 그래서 서버는
  쉬는 연결을 스스로 닫지 않는다.
- `opened_connections`는 서버가 받은 연결이고 `closed_connections`는 처리를 마친 연결이다. 뒤의 것은
  클라이언트가 연결을 닫아 서버가 다음 요청 줄을 읽다 끝(EOF)을 만나면 하나 는다. 답하기 전에 기다릴
  시간을 준 응답의 연결은 클라이언트가 그 전에 끊어도 그 시간이 끝난 뒤에야 처리를 마친 것으로
  세어진다. 서버가 그 시간 동안 그 요청을 처리하고 있기 때문이다. 그래서 기한에 끊기는 사례는 연결의
  셈을 단언하기 전에 그 시간보다 더 기다려야 한다. 셈은 `connections_settled(within)`로 기한까지
  거듭 견준다.

흉내 내는 것은 Chat Completions 하나이고 스트리밍(SSE)은 하지 않는다. 로깅 모듈을 쓰지 않아 어댑터
시험이 모으는 로그 레코드에 서버의 줄이 섞이지 않는다.
"""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import TracebackType
from typing import Self, TypeGuard

CHAT_PATH = "/v1/chat/completions"


def _is_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


@dataclass(frozen=True)
class Received:
    """서버가 받은 요청 하나. `target`은 요청 줄의 글자 그대로이고 `path`는 쿼리를 뺀 것이다."""

    method: str
    target: str
    headers: tuple[tuple[str, str], ...]
    body: bytes

    @property
    def path(self) -> str:
        return self.target.split("?", 1)[0]

    def header(self, name: str) -> list[str]:
        """그 이름(대소문자 무시)으로 받은 헤더 값 전부."""
        return [value for key, value in self.headers if key.lower() == name.lower()]

    def json(self) -> dict[str, object] | None:
        """본문이 JSON 객체이면 그것, 아니면 None."""
        try:
            parsed: object = json.loads(self.body)
        except ValueError:
            return None
        return parsed if _is_object(parsed) else None


@dataclass(frozen=True)
class Reply:
    """서버가 돌려줄 응답 하나. `delay_seconds`는 답하기 전에 기다릴 시간이다."""

    status: int
    body: bytes
    content_type: str = "application/json"
    delay_seconds: float = 0.0

    @classmethod
    def json(cls, status: int, payload: object, *, delay_seconds: float = 0.0) -> Reply:
        return cls(status, json.dumps(payload).encode(), delay_seconds=delay_seconds)

    @classmethod
    def text(
        cls,
        status: int,
        text: str,
        *,
        content_type: str = "text/plain; charset=utf-8",
        delay_seconds: float = 0.0,
    ) -> Reply:
        """JSON이 아닌 날 글자 본문."""
        return cls(status, text.encode(), content_type=content_type, delay_seconds=delay_seconds)


type Responder = Callable[[Received], Reply]


def completion(
    *,
    content: str | None = "pong",
    tool_calls: Sequence[Mapping[str, object]] | None = None,
    model: str | None = "served-model-name",
    usage: Mapping[str, object] | None = None,
    finish_reason: str = "stop",
    delay_seconds: float = 0.0,
) -> Reply:
    """Chat Completions의 정상 응답. `model`이나 `usage`를 None으로 두면 그 칸이 응답에서 빠진다."""
    message: dict[str, object] = {"role": "assistant", "content": content}
    if tool_calls is not None:
        message["tool_calls"] = list(tool_calls)
    payload: dict[str, object] = {
        "id": "chatcmpl-fake",
        "object": "chat.completion",
        "created": 1,
        "choices": [{"index": 0, "message": message, "finish_reason": finish_reason}],
    }
    if model is not None:
        payload["model"] = model
    if usage is not None:
        payload["usage"] = dict(usage)
    return Reply.json(200, payload, delay_seconds=delay_seconds)


def tool_call(name: str, arguments: str, call_id: str = "call_1") -> dict[str, object]:
    """`completion(tool_calls=[...])`에 넣는 도구 호출. `arguments`는 JSON 글자 그대로이고 깨진
    글자도 된다."""
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": arguments}}


def error_reply(status: int, message: str, *, delay_seconds: float = 0.0) -> Reply:
    """OpenAI 꼴의 오류 본문(`{"error": {"message": ...}}`)."""
    body = {"error": {"message": message, "type": "fake_error", "param": None, "code": None}}
    return Reply.json(status, body, delay_seconds=delay_seconds)


class FakeModelServer:
    """뜬 가짜 모델 서버 하나. `with`로 쓰거나 `start()`와 `stop()`을 직접 부른다."""

    def __init__(self, *script: Reply | Responder) -> None:
        self._script = list(script)
        self._requests: list[Received] = []
        self._opened = 0
        self._closed = 0
        self._lock = threading.Lock()
        self._httpd: ThreadingHTTPServer | None = None

    @property
    def requests(self) -> list[Received]:
        """받은 요청을 받은 차례로(그 시점의 사본)."""
        with self._lock:
            return list(self._requests)

    @property
    def opened_connections(self) -> int:
        with self._lock:
            return self._opened

    @property
    def closed_connections(self) -> int:
        with self._lock:
            return self._closed

    def connections_settled(self, within: float) -> bool:
        """받은 연결이 하나 이상이고 모두 처리를 마칠 때까지 기한(초)까지 거듭 견준다. 마쳤으면
        True."""
        end = time.monotonic() + within
        while True:
            with self._lock:
                if self._opened > 0 and self._opened == self._closed:
                    return True
            if time.monotonic() >= end:
                return False
            time.sleep(0.02)

    @property
    def port(self) -> int:
        if self._httpd is None:
            raise RuntimeError("서버가 아직 뜨지 않았다")
        return self._httpd.server_address[1]

    @property
    def base_url(self) -> str:
        """모델 파일의 `base_url`로 쓰는 주소(경로 `/v1`까지)."""
        return f"http://127.0.0.1:{self.port}/v1"

    def _connection_opened(self) -> None:
        with self._lock:
            self._opened += 1

    def _connection_closed(self) -> None:
        with self._lock:
            self._closed += 1

    def _take(self, request: Received) -> Reply:
        with self._lock:
            self._requests.append(request)
            entry = self._script.pop(0) if self._script else None
        if entry is None:
            return error_reply(404, f"시험이 정한 응답이 없다: {request.method} {request.target}")
        # 함수는 잠금 밖에서 돈다. 함수가 requests를 읽어도 막히지 않는다.
        return entry if isinstance(entry, Reply) else entry(request)

    def start(self) -> Self:
        if self._httpd is not None:
            raise RuntimeError("서버가 이미 떠 있다")
        owner = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def _serve(self) -> None:
                length = int(self.headers.get("Content-Length") or 0)
                request = Received(
                    method=self.command,
                    target=self.path,
                    headers=tuple(self.headers.items()),
                    body=self.rfile.read(length) if length else b"",
                )
                reply = owner._take(request)
                if reply.delay_seconds > 0:
                    time.sleep(reply.delay_seconds)
                try:
                    self._send(reply)
                except OSError:  # 클라이언트가 답을 기다리지 않고 먼저 끊었다
                    self.close_connection = True

            def _send(self, reply: Reply) -> None:
                self.send_response(reply.status)
                self.send_header("Content-Type", reply.content_type)
                self.send_header("Content-Length", str(len(reply.body)))
                self.end_headers()
                self.wfile.write(reply.body)

            do_GET = _serve
            do_POST = _serve

            def setup(self) -> None:
                super().setup()
                owner._connection_opened()

            def handle(self) -> None:
                try:
                    super().handle()
                except OSError:  # 클라이언트가 연결을 끊어 읽기가 실패했다. 처리를 마친 연결이다
                    pass

            def finish(self) -> None:
                try:
                    super().finish()
                except OSError:  # 끊긴 소켓에 남은 쓰기를 비우다 실패했다
                    pass
                finally:
                    owner._connection_closed()

            def log_message(self, format: str, *args: object) -> None:
                """서버의 접근 로그를 stderr에 찍지 않는다."""

        httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        httpd.daemon_threads = True
        # 끌 때 `shutdown()`이 폴링 간격만큼 기다리므로 기본 0.5초보다 짧게 둔다
        threading.Thread(
            target=httpd.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True
        ).start()
        self._httpd = httpd
        return self

    def stop(self) -> None:
        """듣는 소켓을 닫는다. 이미 껐으면 아무것도 하지 않는다. 끈 뒤에는 그 포트가 닫힌다."""
        httpd, self._httpd = self._httpd, None
        if httpd is not None:
            httpd.shutdown()
            httpd.server_close()

    def __enter__(self) -> Self:
        return self.start()

    def __exit__(
        self,
        kind: type[BaseException] | None,
        value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.stop()
