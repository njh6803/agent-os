"""`tests/mcp_http_server.py` 를 별도 프로세스로 띄우는 도우미. 어댑터 시험·core 시험·실제 모델
시험이 함께 쓴다(`from tests.mcp_http import serving`).

서버는 루프백의 빈 포트에 뜨고, 시험은 포트가 열릴 때까지 TCP 접속으로 기다린다. 프로세스는 이
도우미가 쥔 핸들로만 끈다. 번호를 보고 끄지 않는다. 기록 파일의 줄은 서버가 받은 요청이다(그 모듈의
독스트링).
"""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import TypeGuard

SERVER = Path(__file__).with_name("mcp_http_server.py")
# 서버가 포트를 열기까지의 상한. 파이썬을 새로 띄워 mcp 와 uvicorn 을 불러 들인다. 다른 세션의
# 테스트와 겹친 부하에서 어림으로 넉넉히 잡았다(`.claude/rules/tests.md` 의 시간 단언).
READY_WITHIN_SECONDS = 60.0


def free_port() -> int:
    """지금 아무도 듣지 않는 루프백 포트. 닫힌 서버를 흉내 낼 때도 쓴다."""
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _listening(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def _is_row(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


def _is_headers(value: object) -> TypeGuard[dict[str, str]]:
    return isinstance(value, dict)


class HttpFixture:
    """뜬 서버 하나. 주소와 기록 파일을 안다."""

    def __init__(self, folder: Path, *options: str) -> None:
        self.port = free_port()
        self.record = folder / "record.jsonl"
        self.slow_marker = Path(f"{self.record}.slow")
        self._stderr_path = folder / "server_stderr.txt"
        self._stderr = self._stderr_path.open("w", encoding="utf-8")
        self._process = subprocess.Popen(
            [sys.executable, str(SERVER), str(self.port), str(self.record), *options],
            stdout=subprocess.DEVNULL,
            stderr=self._stderr,
        )

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/mcp"

    def wait_ready(self) -> None:
        end = time.monotonic() + READY_WITHIN_SECONDS
        while time.monotonic() < end:
            if self._process.poll() is not None:
                raise RuntimeError(f"서버가 포트를 열기 전에 끝났다: {self._stderr_text()}")
            if _listening(self.port):
                return
            time.sleep(0.05)
        raise RuntimeError(f"{READY_WITHIN_SECONDS}초 안에 포트가 열리지 않았다")

    def _stderr_text(self) -> str:
        self._stderr.flush()
        return self._stderr_path.read_text(encoding="utf-8")

    def requests(self) -> list[dict[str, object]]:
        """서버가 받은 요청을 받은 순서로. 줄마다 method, path, query, headers(소문자 이름)다."""
        if not self.record.exists():
            return []
        rows: list[dict[str, object]] = []
        for raw in self.record.read_text(encoding="utf-8").splitlines():
            parsed = json.loads(raw)
            if _is_row(parsed):
                rows.append(parsed)
        return rows

    def headers_of(self, method: str) -> list[dict[str, str]]:
        """그 메서드의 요청마다 받은 헤더(소문자 이름)."""
        found: list[dict[str, str]] = []
        for row in self.requests():
            headers = row.get("headers")
            if row.get("method") == method and _is_headers(headers):
                found.append(headers)
        return found

    def stop(self) -> None:
        if self._process.poll() is None:
            self._process.terminate()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=10)
        self._stderr.close()


@contextmanager
def serving(folder: Path, *options: str) -> Generator[HttpFixture]:
    """서버를 띄워 포트가 열린 것을 본 뒤 내주고, 나갈 때 끈다. 선택 인자는 서버의 독스트링이다."""
    fixture = HttpFixture(folder, *options)
    try:
        fixture.wait_ready()
        yield fixture
    finally:
        fixture.stop()
