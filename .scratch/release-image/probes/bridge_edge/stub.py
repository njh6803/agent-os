"""뒷단 컨테이너를 대신하는 작은 HTTP 서버. `0.0.0.0` 에 묶는다.

    python stub.py <이름> <포트>

실제 이미지(serve, 관리 화면, 위젯, 위젯 미리보기 페이지)가 아니다. 프록시와 포트 발행을 재는 데
필요한 것만 한다. 어느 요청이든 200 과 JSON 본문으로 답하고, 본문에 이 서버의 이름과 받은 요청
줄의 경로, 받은 헤더 몇 개, 본문 크기, TCP 상대 주소를 싣는다. 그래서 요청을 보낸 쪽이 누가
답했는지와 프록시가 무엇을 넘겼는지를 본문에서 읽는다. 응답 헤더 `X-Stub` 에도 이름을 싣는다.

경로가 `/sse` 로 끝나면 `text/event-stream` 으로 이벤트를 띄엄띄엄 낸다. 질의 `n`(이벤트 수),
`gap`(간격 초), `accel`(1 이면 `X-Accel-Buffering: no` 를 붙인다)을 받는다. FastAPI 의 SSE 응답이
붙이는 그 헤더가 있을 때와 없을 때 프록시가 응답을 모으는지를 가르는 데 쓴다.

    python stub.py <이름> <포트> ::

셋째 인자로 `::` 를 주면 `::` 에 IPV6_V6ONLY 를 끄고 묶어 IPv4 와 IPv6 를 함께 받는다(항목 7 의
`compose.ipv6-listen.yml`). 이웃이 컨테이너의 IPv6 주소로 건 요청이 닿았을 때 이 서버가 답하게
하려는 것이다. 이때 IPv4 상대 주소는 `::ffff:` 가 붙은 꼴로 실린다.
"""

from __future__ import annotations

import json
import socket
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit


def first(query: dict[str, list[str]], key: str, default: str) -> str:
    values = query.get(key)
    return values[0] if values else default


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    name = "stub"

    def log_message(self, format: str, *args: object) -> None:
        sys.stdout.write(f"stub {self.name} {self.address_string()} {format % args}\n")
        sys.stdout.flush()

    def answer(self) -> None:
        length = int(self.headers.get("Content-Length") or "0")
        received = len(self.rfile.read(length)) if length else 0
        split = urlsplit(self.path)
        if split.path.endswith("/sse"):
            self.stream(parse_qs(split.query))
            return
        payload = {
            "stub": self.name,
            "method": self.command,
            "path": self.path,
            "peer": self.client_address[0],
            "host": self.headers.get("Host"),
            "xff": self.headers.get("X-Forwarded-For"),
            "xfp": self.headers.get("X-Forwarded-Proto"),
            "http_version": self.request_version,
            "body_bytes": received,
        }
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Stub", self.name)
        self.end_headers()
        self.wfile.write(body)

    def stream(self, query: dict[str, list[str]]) -> None:
        count = int(first(query, "n", "4"))
        gap = float(first(query, "gap", "0.4"))
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("X-Stub", self.name)
        if first(query, "accel", "1") == "1":
            self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        for index in range(count):
            self.wfile.write(f"data: {self.name}-{index}\n\n".encode())
            self.wfile.flush()
            if index < count - 1:
                time.sleep(gap)
        self.close_connection = True

    do_GET = answer
    do_POST = answer
    do_DELETE = answer


class DualStackServer(ThreadingHTTPServer):
    """`::` 에 묶고 IPV6_V6ONLY 를 꺼서 IPv4 와 IPv6 를 함께 받는다."""

    address_family = socket.AF_INET6

    def server_bind(self) -> None:
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        super().server_bind()


def main() -> int:
    Handler.name = sys.argv[1]
    bind = sys.argv[3] if len(sys.argv) > 3 else "0.0.0.0"
    kind = DualStackServer if ":" in bind else ThreadingHTTPServer
    server = kind((bind, int(sys.argv[2])), Handler)
    print(f"stub {Handler.name} listening on {bind}:{sys.argv[2]}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
