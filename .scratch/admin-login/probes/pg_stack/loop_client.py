"""`loop_app.py` 를 자식 프로세스로 띄워 조합마다 요청 하나를 보내고 `RESULT <json>` 줄을 낸다.

윈도 호스트와 리눅스 컨테이너 안에서 같은 파일을 쓴다. 표준 라이브러리만 쓴다. 서버는 `/shutdown`
으로 스스로 끝나게 하고, 8초 안에 끝나지 않으면 이 파일이 쥔 `Popen` 핸들로 끈다(pid 로 찾아 끄지
않는다). DSN 은 환경 변수로 자식에게 넘어가고 출력에 싣지 않는다. 측정의 셈은 `run.py` 가 한다.
"""

from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = (
    "psycopg-sync",
    "sqlalchemy-core-sync+psycopg",
    "psycopg-async",
    "psycopg-async+pool",
    "asyncpg",
    "sqlalchemy-core-async+psycopg",
    "sqlalchemy-core-async+asyncpg",
)


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
        return port


def fetch(port: int, path: str, *, post: bool = False, timeout: float = 60) -> str:
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}", method="POST" if post else "GET"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body: bytes = response.read()
            return body.decode("utf-8")
    except urllib.error.HTTPError as error:
        return json.dumps({"http_error": error.code, "body": error.read().decode("utf-8")[:300]})
    except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
        return json.dumps({"client_error": f"{type(error).__name__}: {error}"})


def wait_ready(port: int, server: subprocess.Popen[bytes], seconds: float) -> bool:
    begin = time.monotonic()
    while time.monotonic() - begin < seconds:
        if server.poll() is not None:
            return False
        if '"loop"' in fetch(port, "/loop", timeout=2):
            return True
        time.sleep(0.2)
    return False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", default="")
    args = parser.parse_args()
    loop_option: str = args.loop
    port = free_port()
    argv = [sys.executable, str(HERE / "loop_app.py"), "--port", str(port)]
    if loop_option:
        argv += ["--loop", loop_option]
    server = subprocess.Popen(argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        if not wait_ready(port, server, 40):
            print(f"RESULT {json.dumps({'kind': 'server', 'ready': False})}", flush=True)
            return 1
        print(f"RESULT {json.dumps({'kind': 'loop', **json.loads(fetch(port, '/loop'))})}")
        for label in LABELS:
            reply = fetch(port, f"/exercise?label={urllib.parse.quote(label, safe='')}")
            print(f"RESULT {json.dumps({'kind': 'exercise', 'label': label, **json.loads(reply)})}")
        child = json.loads(fetch(port, "/subprocess"))
        print(f"RESULT {json.dumps({'kind': 'subprocess', **child})}", flush=True)
        opened = json.loads(fetch(port, "/mcp"))
        print(f"RESULT {json.dumps({'kind': 'mcp', **opened})}", flush=True)
        fetch(port, "/shutdown", post=True, timeout=5)
        try:
            code = server.wait(timeout=8)
        except subprocess.TimeoutExpired:
            code = None
        print(f"RESULT {json.dumps({'kind': 'shutdown', 'exit_code': code})}", flush=True)
    finally:
        if server.poll() is None:
            server.kill()
            server.wait(timeout=10)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
