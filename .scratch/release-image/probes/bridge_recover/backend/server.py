"""뒷단 넷(serve, 관리 화면, 위젯, 위젯 미리보기 페이지)을 흉내 내는 작은 HTTP 서버.

실제 이미지가 아니다. 컨테이너 안의 모든 주소(BACKEND_BIND, 기본 0.0.0.0)에 묶여, 요청마다 자기
이름(BACKEND_NAME)과 컨테이너 호스트 이름과 이미지에 구운 판(IMAGE_VERSION)을 본문 한 줄로 답하고
표준 출력에 접근 기록 한 줄을 남긴다. 프로브는 본문의 host 로 "새 컨테이너가 답했다"를, 접근 기록의
rid 로 "요청이 이 컨테이너에 실제로 도착했다"를 본다.

START_DELAY(초)를 주면 그동안 포트를 열지 않는다. 뜰 때 빌드하느라 한동안 답하지 않는 위젯
컨테이너를 흉내 낸다(컨테이너는 돌고 있어 이름은 풀리지만 연결은 거부된다).
"""

from __future__ import annotations

import http.server
import os
import socket
import sys
import time

NAME = os.environ.get("BACKEND_NAME", "?")
PORT = int(os.environ.get("BACKEND_PORT", "8000"))
BIND = os.environ.get("BACKEND_BIND", "0.0.0.0")
DELAY = float(os.environ.get("START_DELAY", "0"))
VERSION = os.environ.get("IMAGE_VERSION", "?")
HOST = socket.gethostname()


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        body = f"name={NAME} host={HOST} version={VERSION} path={self.path}\n".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        peer = self.client_address[0]
        line = f"backend-access name={NAME} host={HOST} peer={peer} path={self.path}"
        print(line, flush=True)


class Server(http.server.ThreadingHTTPServer):
    address_family = socket.AF_INET6 if ":" in BIND else socket.AF_INET


def main() -> int:
    print(f"backend-boot name={NAME} host={HOST} version={VERSION} delay={DELAY}", flush=True)
    if DELAY > 0:
        time.sleep(DELAY)
    server = Server((BIND, PORT), Handler)
    print(f"backend-listen name={NAME} host={HOST} bind={BIND} port={PORT}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
