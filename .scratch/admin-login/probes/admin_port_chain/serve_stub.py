"""admin_port_chain 프로브에서 `serve` 자리에 서는 대역. 실제 serve 가 아니다.

    python -I serve_stub.py serve
    python -I serve_stub.py client <호스트> <포트> <태그>

`serve` 는 두 포트를 듣는다.

- 8000(재는 길). compose 네트워크의 이름 `serve` 로, 관리 화면 이미지의 Next 중계가
  `http://serve:8000` 으로 넘긴 요청을 받는다. 어느 요청이든 받은 머리(이름의 대소문자와 차례
  그대로, 같은 이름이 여럿이면 여럿), TCP 상대 주소, 질의의 `tag`, 이 응답에 실은 `Set-Cookie` 줄을
  기록에 쌓는다. 경로가 고르는 것은 넷이다.
  - `/page`: 작은 HTML 문서. 브라우저가 그 출처의 페이지를 열 자리다.
  - `/set`: 쿠키 둘을 심는다. `__Host-aos_at=<값>; HttpOnly; Secure; SameSite=Strict; Path=/` 와
    `__Host-aos_rt=<값>; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=1800`. 값은 부를 때마다
    새로 짓는 무작위 글이고 비밀이 아니다.
  - `/clear`: 같은 두 이름을 같은 속성에 `Max-Age=0` 과 1970년의 `Expires` 로 지운다.
  - 그 밖: 받은 머리를 JSON 으로 돌려준다.
- 8001(기록의 길). 측정 스크립트가 호스트의 `127.0.0.1` 에서만 읽는다(compose 가 그 주소에만
  발행한다). `/health` 는 파이썬 판을, `/log?since=<번호>` 는 그 번호부터의 기록을 낸다.

`client` 는 같은 이미지로 compose 네트워크 안에서 프록시에 TLS 요청 하나를 건다(측정 스크립트가
`docker compose exec serve` 로 부른다). 프록시가 보는 접속 주소가 TCP 상대의 주소라는 것을, 주소
변환이 끼지 않는 길에서 보이는 양성 대조다. 인증서는 확인하지 않는다(프로브의 자체 서명 인증서).

표준 라이브러리만 쓴다(이미지에 아무것도 깔지 않는다). 회차와 표지는 측정 스크립트 `probe.mjs` 가
센다. 이 파일은 측정하지 않으므로 `tools/probe_kit.py` 의 `Rounds` 를 쓰지 않는다.
"""

from __future__ import annotations

import html
import json
import secrets
import ssl
import sys
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

ATTRIBUTES = "HttpOnly; Secure; SameSite=Strict; Path=/"
REFRESH_MAX_AGE = 1800
COOKIE_NAMES = ("__Host-aos_at", "__Host-aos_rt")
EPOCH = "Thu, 01 Jan 1970 00:00:00 GMT"


class Journal:
    """재는 길이 받은 요청의 기록. 번호는 쌓인 차례다."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._entries: list[dict[str, object]] = []

    def add(self, entry: dict[str, object]) -> None:
        with self._lock:
            entry["seq"] = len(self._entries)
            self._entries.append(entry)

    def since(self, seq: int) -> list[dict[str, object]]:
        with self._lock:
            return list(self._entries[seq:])


JOURNAL = Journal()


def set_lines() -> list[str]:
    access = f"at-{secrets.token_hex(6)}"
    refresh = f"rt-{secrets.token_hex(6)}"
    return [
        f"{COOKIE_NAMES[0]}={access}; {ATTRIBUTES}",
        f"{COOKIE_NAMES[1]}={refresh}; {ATTRIBUTES}; Max-Age={REFRESH_MAX_AGE}",
    ]


def clear_lines() -> list[str]:
    return [f"{name}=; {ATTRIBUTES}; Max-Age=0; Expires={EPOCH}" for name in COOKIE_NAMES]


class Measured(BaseHTTPRequestHandler):
    """재는 길(8000)."""

    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        self.answer()

    def do_POST(self) -> None:
        self.answer()

    def do_OPTIONS(self) -> None:
        self.answer()

    def answer(self) -> None:
        length = int(self.headers.get("Content-Length") or "0")
        body = self.rfile.read(length) if length else b""
        split = urlsplit(self.path)
        tag = (parse_qs(split.query).get("tag") or [""])[0]
        headers = [[name, value] for name, value in self.headers.items()]
        lines: list[str] = []
        if split.path == "/page":
            content_type = "text/html; charset=utf-8"
            title = html.escape(tag)
            payload = (
                f"<!doctype html><html><head><title>{title}</title></head>"
                f"<body>{title}</body></html>"
            ).encode()
        else:
            if split.path == "/set":
                lines = set_lines()
            elif split.path == "/clear":
                lines = clear_lines()
            content_type = "application/json"
            payload = json.dumps({"tag": tag, "headers": headers}).encode()
        JOURNAL.add(
            {
                "method": self.command,
                "path": split.path,
                "tag": tag,
                "headers": headers,
                "peer": self.client_address[0],
                "set_cookie": lines,
                "body_length": len(body),
            }
        )
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        for line in lines:
            self.send_header("Set-Cookie", line)
        self.end_headers()
        self.wfile.write(payload)


class Control(BaseHTTPRequestHandler):
    """기록의 길(8001)."""

    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: object) -> None:
        return

    def do_GET(self) -> None:
        split = urlsplit(self.path)
        if split.path == "/health":
            payload = json.dumps({"python": sys.version}).encode()
        elif split.path == "/log":
            since = int((parse_qs(split.query).get("since") or ["0"])[0])
            payload = json.dumps(JOURNAL.since(since)).encode()
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def serve() -> int:
    measured = ThreadingHTTPServer(("0.0.0.0", 8000), Measured)
    control = ThreadingHTTPServer(("0.0.0.0", 8001), Control)
    measured.daemon_threads = True
    control.daemon_threads = True
    threading.Thread(target=control.serve_forever, daemon=True).start()
    measured.serve_forever()
    return 0


def client(host: str, port: str, tag: str) -> int:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    request = urllib.request.Request(
        f"https://{host}:{port}/api/echo?tag={tag}", headers={"Host": f"admin.test:{port}"}
    )
    with urllib.request.urlopen(request, context=context, timeout=20) as response:
        print(json.dumps({"status": response.status, "tag": tag}))
    return 0


def main(argv: list[str]) -> int:
    if argv[:1] == ["serve"]:
        return serve()
    if argv[:1] == ["client"] and len(argv) == 4:
        return client(argv[1], argv[2], argv[3])
    print(
        "사용: serve_stub.py serve | serve_stub.py client <호스트> <포트> <태그>", file=sys.stderr
    )
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
