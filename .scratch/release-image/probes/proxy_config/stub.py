"""뒷단 컨테이너를 대신하는 작은 HTTP 서버. `0.0.0.0` 에만 묶는다(IPv6 에는 묶지 않는다).

    python stub.py <이름> <포트>

`bridge_edge/stub.py` 를 옮겨 셋을 더했다. 실제 이미지(serve, 위젯, 위젯 미리보기 페이지)가 아니다.
어느 요청이든 200 과 JSON 본문으로 답하고, 본문에 이 서버의 이름과 인스턴스 표지, 받은 요청 줄의
경로, 받은 헤더 몇 개, 본문 크기, TCP 상대 주소를 싣는다. 응답 헤더 `X-Stub` 에 이름을,
`X-Stub-Instance` 에 인스턴스 표지를 싣는다.

더한 것
- 인스턴스 표지: 뜰 때마다 새로 뽑는 무작위 글자. 같은 이름으로 다시 만든 컨테이너를 옛 것과 가른다.
- 접근 기록의 rid: 받은 `X-Probe-Rid` 헤더를 표준 출력의 접근 기록 줄에 싣는다. 요청 줄에 질의를
  붙이지 않은 요청도 이 기록에서 찾으려는 것이다(경로를 글자 그대로 보내야 하는 측정이 있다).
- 첫 줄: 뜬 직후 `stub <이름> <인스턴스> listening on 0.0.0.0:<포트>` 를 낸다.

경로가 `/sse` 로 끝나면 `text/event-stream` 으로 이벤트를 띄엄띄엄 낸다. 질의 `n`(이벤트 수),
`gap`(간격 초), `accel`(1 이면 `X-Accel-Buffering: no` 를 붙인다)을 받는다.
"""

from __future__ import annotations

import json
import secrets
import socket
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

INSTANCE = secrets.token_hex(4)


def first(query: dict[str, list[str]], key: str, default: str) -> str:
    values = query.get(key)
    return values[0] if values else default


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    name = "stub"

    def log_message(self, format: str, *args: object) -> None:
        rid = self.headers.get("X-Probe-Rid", "-") if hasattr(self, "headers") else "-"
        line = f"stub {self.name} {INSTANCE} rid={rid} {self.address_string()} {format % args}"
        sys.stdout.write(line + "\n")
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
            "instance": INSTANCE,
            "hostname": socket.gethostname(),
            "method": self.command,
            "path": self.path,
            "peer": self.client_address[0],
            "host": self.headers.get("Host"),
            "xff": self.headers.get("X-Forwarded-For"),
            "xfp": self.headers.get("X-Forwarded-Proto"),
            "rid": self.headers.get("X-Probe-Rid"),
            "http_version": self.request_version,
            "body_bytes": received,
        }
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Stub", self.name)
        self.send_header("X-Stub-Instance", INSTANCE)
        self.end_headers()
        self.wfile.write(body)

    def stream(self, query: dict[str, list[str]]) -> None:
        count = int(first(query, "n", "4"))
        gap = float(first(query, "gap", "0.5"))
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("X-Stub", self.name)
        self.send_header("X-Stub-Instance", INSTANCE)
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


def main() -> int:
    Handler.name = sys.argv[1]
    server = ThreadingHTTPServer(("0.0.0.0", int(sys.argv[2])), Handler)
    print(f"stub {Handler.name} {INSTANCE} listening on 0.0.0.0:{sys.argv[2]}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
