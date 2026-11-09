"""streamable HTTP 로 붙은 MCP 서버를 닫는 길마다 종료 요청이 서버에 닿는지와 걸리는 시간, 그리고
접속 실패의 문구와 로그에 주소의 쿼리 문자열이 실리는지를 잰다.

mcp 2.3.0 의 `streamable_http_client`와 `ClientSession`을 직접 쓴다(어댑터는 아직 http 모양을
모른다). 서버는 같은 폴더의 `http_fixture_server.py`를 사례마다 새 프로세스로 띄우고 기록 파일로
본다. 실행 타임아웃처럼 취소 범위가 연결 전체를 감싸고(`core/run.py`의 `move_on_after`), 기한을
받았는지는 core 처럼 `cancelled_caught`로 본다.

사례:
- `normal`: 헤더를 환경 변수에서 읽어 실은 클라이언트로 열고 add 를 부른 뒤 정상으로 닫는다. 닫는
  시간, 서버가 받은 Authorization 값, DELETE 가 그 세션 번호로 닿았는지를 본다.
- `normal_own_delete`: `normal`과 같되 `deadline_shield_finally`의 닫는
  길(`terminate_on_close=False`, 스택 닫기를 `try`에, 보호와 프로브의 DELETE 를 `finally`에)로
  닫는다. 기한이 없다. 명세가 고른 길을 정상 종료가 지날 때의 닫는 시간을 `normal`과 같은 실행에서
  견준다(ADR 0049 Consequences 의 "정상 종료는 늦지 않는다"를 어림에서 측정으로).
- `deadline_plain`: slow(30) 도중에 기한(1초)이 온다. 닫기를 보호하지 않는다(대조군).
- `deadline_shield_exit`: 같되 `streamable_http_client`의 닫기(라이브러리가 DELETE 를 보낸다)와
  클라이언트 닫기를 바깥에서 `CancelScope(shield=True)`와 2초 유예로 감싼다(ADR 0049 의 첫째 안).
- `deadline_shield_delete`: 같되 `terminate_on_close=False`로 열고, 스택을 닫은 뒤 세션 번호로
  DELETE 를 프로브가 직접 보낸다. 보호는 `deadline_shield_exit`처럼 스택 닫기까지 감싼다. 앞 사례와
  함께 실패하면 원인이 라이브러리의 DELETE 가 아니라 보호의 자리라는 갈래다.
- `deadline_shield_exit_hang`: `deadline_shield_exit`인데 서버가 DELETE 에 30초 동안 답하지 않는다.
  2초 유예가 닫기를 끊는지 본다.
- `deadline_shield_after`: `terminate_on_close=False`로 열고, 스택은 보호 없이 먼저 닫은 뒤 다음
  문장에서 `CancelScope(shield=True)`와 2초 유예 안에 DELETE 와 클라이언트 닫기를 둔다. 취소된
  범위에서는 스택 닫기의 `await`가 끝나며 취소가 다시 올라가 그 뒤 문장이 돌지 않는다는 것을 보이는
  갈래다(`grace_expired`가 기록되지 않고 DELETE 가 닿지 않는다).
- `deadline_shield_finally`: 같되 스택 닫기를 `try`에 두고 보호 범위를 `finally`에 둔다. 취소가
  올라가는 중에도 `finally`는 돌고, 보호 범위는 그때 가장 안쪽이라 중첩을 지킨다(ADR 0049 의 대안.
  보호의 자리가 라이브러리 바깥이다).
- `deadline_shield_finally_hang`: `deadline_shield_finally`인데 서버가 DELETE 에 30초 동안 답하지
  않는다. 2초 유예가 닫기를 끊고 기한 결말이 그대로인지 본다.
- `closed_port`: 아무도 듣지 않는 포트에, 쿼리 문자열이 든 주소로 연다. 예외의 종류와 글, 글과
  로그에 쿼리 문자열이 실리는지, 거부까지 걸린 시간을 본다.
- `unauthorized`: 서버가 Authorization 을 요구하는데 헤더 없이 연다. 예외의 종류와 글, 로그의 쿼리
  문자열, 그리고 클라이언트의 응답 훅이 401 응답을 받는지를 본다.
- `query_url_normal`: 사는 서버에 쿼리 문자열이 든 주소로 열어 add 를 부른다. 쿼리가 서버에 닿는지와
  로그(`mcp.client.streamable_http`와 `httpx2`, DEBUG)에 실리는지를 본다.

모든 사례에서 헤더 값(토큰)이 예외 글과 세 로거(`mcp`, `httpx2`, `httpcore2`)의 DEBUG 줄에
실리는지도 본다(`token_in_exception`, `token_in_log`). 서버 기록의 `authorization_seen`이 값이
서버에 닿았다는 양성 대조다. `unauthorized`는 헤더 없이 열고 `closed_port`는 서버에 닿지 않아 그
둘에는 양성 대조가 없다.

표지: 연결을 연 사례는 `initialize`가 끝났고 add 가 3 을 돌려줬다. 기한 사례는 서버의 slow 표지
파일이 기한보다 먼저 생겼고 slow 가 돌아오지 않았다. `closed_port`는 예외의 잎 가운데 httpx2 의 전송
오류 (`TransportError`)가 있다. `unauthorized`는 서버 기록에 헤더 없는 POST 가 있고 예외가 났으며
응답 훅이 401 응답을 받았다(401 아닌 까닭의 예외는 측정이 아니다). 표지가 없는 회차는 측정이
아니라고 따로 세고 종료 코드를 1 로 둔다(`tools/probe_kit.py`의 `Rounds`).

서버 프로세스는 프로브가 쥔 `Popen` 핸들로만 끈다. 번호를 보고 끄지 않는다.

돌리는 명령은 같은 폴더의 `README.md`에 있다.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import logging
import os
import platform
import socket
import subprocess
import sys
import tempfile
import time
from contextlib import AsyncExitStack
from functools import partial
from pathlib import Path

import anyio
import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.probe_kit import Rounds  # noqa: E402

SERVER = HERE / "http_fixture_server.py"
TOKEN_VARIABLE = "PROBE_MCP_TOKEN"
TOKEN_VALUE = "fixture-token-7c1e"
QUERY_SECRET = "query-secret-4b9d"
DEADLINE_SECONDS = 1.0
GRACE_SECONDS = 2.0
READY_WITHIN_SECONDS = 30.0
CASES = (
    "normal",
    "normal_own_delete",
    "deadline_plain",
    "deadline_shield_exit",
    "deadline_shield_delete",
    "deadline_shield_exit_hang",
    "deadline_shield_after",
    "deadline_shield_finally",
    "deadline_shield_finally_hang",
    "closed_port",
    "unauthorized",
    "query_url_normal",
)
DEADLINE = {c for c in CASES if c.startswith("deadline_")}
# 라이브러리의 종료 요청을 끄고 프로브가 DELETE 를 직접 보내는 사례.
OWN_DELETE = {
    "normal_own_delete",
    "deadline_shield_delete",
    "deadline_shield_after",
    "deadline_shield_finally",
    "deadline_shield_finally_hang",
}
# 스택을 먼저 닫고 보호를 `finally`에 두는 사례.
SHIELD_FINALLY = {"normal_own_delete", "deadline_shield_finally", "deadline_shield_finally_hang"}
# 자식 로거(`mcp.client.streamable_http`)의 기록은 부모 `mcp`로 전파되므로 부모에만 단다. 둘 다 달면
# 같은 줄이 두 번 모인다(첫 실행에서 봤다). httpx2 의 전송 층은 httpcore2 라 그 로거도 단다.
LOGGERS = ("mcp", "httpx2", "httpcore2")


class LogCapture(logging.Handler):
    """고른 로거의 기록을 (이름, 수준, 글)로 모은다."""

    def __init__(self) -> None:
        super().__init__(logging.DEBUG)
        self.lines: list[tuple[str, str, str]] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append((record.name, record.levelname, record.getMessage()))

    def attach(self) -> None:
        for name in LOGGERS:
            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)
            logger.addHandler(self)

    def detach(self) -> None:
        for name in LOGGERS:
            logging.getLogger(name).removeHandler(self)

    def mentioning(self, text: str) -> list[str]:
        return [f"{name}:{level}" for name, level, message in self.lines if text in message]


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _listening(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


class Server:
    """사례 하나의 서버 프로세스. 기록 파일과 slow 표지의 경로를 안다."""

    def __init__(self, work: Path, *extra: str) -> None:
        self.port = _free_port()
        self.record = work / "record.jsonl"
        self.slow_marker = Path(f"{self.record}.slow")
        self.stderr = (work / "server_stderr.txt").open("w", encoding="utf-8")
        self.process = subprocess.Popen(
            [sys.executable, str(SERVER), str(self.port), str(self.record), *extra],
            stdout=subprocess.DEVNULL,
            stderr=self.stderr,
        )

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/mcp"

    def wait_ready(self) -> bool:
        end = time.monotonic() + READY_WITHIN_SECONDS
        while time.monotonic() < end:
            if self.process.poll() is not None:
                return False
            if _listening(self.port):
                return True
            time.sleep(0.05)
        return False

    def lines(self) -> list[dict[str, object]]:
        if not self.record.exists():
            return []
        out: list[dict[str, object]] = []
        for raw in self.record.read_text(encoding="utf-8").splitlines():
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                out.append(parsed)
        return out

    def stop(self) -> None:
        """프로브가 띄운 자식을 그 핸들로 끈다."""
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=10)
        self.stderr.close()


def _describe(error: BaseException) -> dict[str, object]:
    text = str(error)
    described: dict[str, object] = {
        "type": f"{type(error).__module__}.{type(error).__qualname__}",
        "str": text[:300],
        # 비밀값 검사는 자르기 전의 전체 글에서 한다(자른 글만 보면 300자 뒤의 값을 놓친다)
        "has_query": QUERY_SECRET in text,
        "has_token": TOKEN_VALUE in text,
    }
    if isinstance(error, BaseExceptionGroup):
        described["inner"] = [_describe(inner) for inner in error.exceptions]
    return described


def _flagged(described: object, key: str) -> bool:
    """`_describe`가 적은 예외 글(예외 그룹은 안쪽까지)에 `key`의 표지가 서 있는가."""
    if not isinstance(described, dict):
        return False
    inner = described.get("inner")
    return described.get(key) is True or (
        isinstance(inner, list) and any(_flagged(item, key) for item in inner)
    )


def _leaves(error: BaseException) -> list[BaseException]:
    if isinstance(error, BaseExceptionGroup):
        return [leaf for inner in error.exceptions for leaf in _leaves(inner)]
    return [error]


def _client(
    *, with_token: bool, seen_sessions: list[str], seen_statuses: list[str]
) -> httpx2.AsyncClient:
    """어댑터가 만들 모양의 클라이언트. 헤더 값은 환경 변수에서 접속 직전에 읽는다. 응답 훅으로
    세션 번호를 잡아 둔다(`streamable_http_client`는 세션 번호를 내주지 않는다). 같은 훅이 응답마다
    메서드와 상태 코드를 적어, 라이브러리가 상태 코드 없이 "Server returned an error response"로
    바꾸는 오류 응답(401 등)을 어댑터가 문구에 실을 수 있는지 본다."""

    async def remember(response: httpx2.Response) -> None:
        seen_statuses.append(
            f"{response.request.method} {response.status_code} {response.reason_phrase}"
        )
        session = response.headers.get("mcp-session-id")
        if session and session not in seen_sessions:
            seen_sessions.append(session)

    headers = {"Authorization": f"Bearer {os.environ[TOKEN_VARIABLE]}"} if with_token else {}
    return httpx2.AsyncClient(
        headers=headers,
        timeout=httpx2.Timeout(30, read=300),
        event_hooks={"response": [remember]},
    )


async def _connected(
    case: str, url: str, server: Server | None, *, with_token: bool
) -> dict[str, object]:
    """연결을 열고 사례대로 움직인 뒤 닫는다. 기록과 표지의 재료를 돌려준다."""
    record: dict[str, object] = {}
    sessions: list[str] = []
    statuses: list[str] = []
    client = _client(with_token=with_token, seen_sessions=sessions, seen_statuses=statuses)
    terminate_on_close = case not in OWN_DELETE
    deadline_wall: float | None = None
    close_started: float | None = None
    protocol_version: str | None = None

    async def body(stack: AsyncExitStack, scope: anyio.CancelScope) -> None:
        nonlocal deadline_wall, protocol_version
        read, write = await stack.enter_async_context(
            streamable_http_client(url, http_client=client, terminate_on_close=terminate_on_close)
        )
        session = await stack.enter_async_context(ClientSession(read, write))
        initialized = await session.initialize()
        protocol_version = initialized.protocol_version
        record["initialized"] = True
        if case in DEADLINE:
            scope.deadline = anyio.current_time() + DEADLINE_SECONDS
            deadline_wall = time.time() + DEADLINE_SECONDS
            try:
                await session.call_tool("slow", {"seconds": 30})
            except anyio.get_cancelled_exc_class():
                record["slow_cancelled"] = True  # 기한이 slow 를 기다리는 중에 취소했다
                raise
            record["unexpected"] = "slow(30) 이 기한 안에 돌아왔다"
            return
        result = await session.call_tool("add", {"a": 1, "b": 2})
        record["add"] = [getattr(block, "text", None) for block in result.content]

    async def close(stack: AsyncExitStack) -> None:
        nonlocal close_started
        close_started = anyio.current_time()
        if case in {"deadline_plain", "normal", "closed_port", "unauthorized", "query_url_normal"}:
            await stack.aclose()
            await client.aclose()
            return
        if case == "deadline_shield_after":
            await stack.aclose()
            with anyio.CancelScope(shield=True):
                await _delete_then_close()
            return
        if case in SHIELD_FINALLY:
            try:
                await stack.aclose()
            finally:
                with anyio.CancelScope(shield=True):
                    await _delete_then_close()
            return
        with anyio.CancelScope(shield=True), anyio.move_on_after(GRACE_SECONDS) as grace:
            await stack.aclose()
            if case in OWN_DELETE:
                await own_delete()
            await client.aclose()
        record["grace_expired"] = grace.cancelled_caught

    async def _delete_then_close() -> None:
        """종료 요청만 2초 유예 안에 두고, 클라이언트 닫기는 유예가 지났어도 이어서 한다.
        유예 안에 둘을 함께 두면 종료 요청이 걸렸을 때 닫기가 건너뛰어진다."""
        with anyio.move_on_after(GRACE_SECONDS) as grace:
            await own_delete()
        record["grace_expired"] = grace.cancelled_caught
        closing = anyio.current_time()
        await client.aclose()
        record["client_closed"] = True
        record["client_close_seconds"] = round(anyio.current_time() - closing, 3)

    async def own_delete() -> None:
        """라이브러리 대신 프로브가 세션 번호로 종료 요청을 보낸다. 세션 번호가 없으면 보내지
        않는다."""
        if not sessions:
            return
        headers = {
            "accept": "application/json, text/event-stream",
            "content-type": "application/json",
            "mcp-session-id": sessions[0],
        }
        if protocol_version:
            headers["mcp-protocol-version"] = protocol_version
        try:
            response = await client.delete(url, headers=headers)
        except httpx2.HTTPError as error:
            record["delete_error"] = type(error).__name__  # 명세대로 삼킨다. 닫기는 이어진다
            return
        record["delete_status"] = response.status_code

    async def drive() -> None:
        with anyio.move_on_after(60) as scope:
            stack = AsyncExitStack()
            try:
                await body(stack, scope)
            finally:
                await close(stack)
        record["cancelled_caught"] = scope.cancelled_caught
        if deadline_wall is not None:
            record["deadline_to_return_seconds"] = round(time.time() - deadline_wall, 3)

    started = time.time()
    try:
        await drive()
    except Exception as error:
        record["exception"] = _describe(error)
        record["leaf_types"] = [
            f"{type(leaf).__module__}.{type(leaf).__qualname__}" for leaf in _leaves(error)
        ]
        record["open_to_exception_seconds"] = round(time.time() - started, 3)
    if close_started is not None:
        record["close_seconds"] = round(anyio.current_time() - close_started, 3)
    record["sessions"] = sessions
    record["statuses"] = statuses
    if server is not None:
        _server_facts(record, server, sessions, deadline_wall)
    return record


def _server_facts(
    record: dict[str, object], server: Server, sessions: list[str], deadline_wall: float | None
) -> None:
    lines = server.lines()
    record["requests"] = [
        f"{line.get('method')} {line.get('path')}?{line.get('query')}" for line in lines
    ]
    record["authorization_seen"] = sorted({str(line.get("authorization")) for line in lines})
    deletes = [line for line in lines if line.get("method") == "DELETE"]
    record["delete_reached"] = bool(deletes)
    record["delete_session_matches"] = any(line.get("session") in sessions for line in deletes)
    if deadline_wall is not None:
        marker = server.slow_marker
        record["slow_started_before_deadline"] = (
            marker.exists() and marker.stat().st_mtime <= deadline_wall
        )


def _query_facts(record: dict[str, object], capture: LogCapture) -> None:
    exception = record.get("exception")
    record["query_in_exception"] = _flagged(exception, "has_query")
    record["query_in_log"] = capture.mentioning(QUERY_SECRET)
    record["token_in_exception"] = _flagged(exception, "has_token")
    record["token_in_log"] = capture.mentioning(TOKEN_VALUE)
    record["log_lines"] = len(capture.lines)
    record["log_sample"] = [
        f"{name}:{level}: {message[:160]}"
        for name, level, message in capture.lines
        if QUERY_SECRET in message
    ][:4]


def _marked(case: str, record: dict[str, object]) -> bool:
    """사례가 재려는 상황이 그 회차에 실제로 났는가."""
    if case == "closed_port":
        return any(
            leaf.startswith("httpx2.") and leaf.endswith(("ConnectError", "TransportError"))
            for leaf in _as_list(record.get("leaf_types"))
        )
    if case == "unauthorized":
        return (
            "exception" in record
            and "None" in _as_list(record.get("authorization_seen"))
            and any(" 401 " in status for status in _as_list(record.get("statuses")))
        )
    if case in DEADLINE:
        return (
            record.get("initialized") is True
            and record.get("slow_started_before_deadline") is True
            and record.get("slow_cancelled") is True
            and "unexpected" not in record
            and (case not in SHIELD_FINALLY or record.get("client_closed") is True)
        )
    return record.get("initialized") is True and record.get("add") == ["3"]


def _as_list(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _verdict(case: str, record: dict[str, object]) -> str:
    """측정인 회차의 결과 갈래. 수는 기록에 두고 여기에는 갈래만 적는다."""
    if case == "closed_port":
        return (
            f"leaf={record.get('leaf_types')} query_in_exception={record.get('query_in_exception')}"
            f" query_in_log={bool(record.get('query_in_log'))}"
        )
    if case == "unauthorized":
        hook_saw_401 = any(" 401 " in status for status in _as_list(record.get("statuses")))
        return (
            f"leaf={record.get('leaf_types')} hook_saw_401={hook_saw_401}"
            f" query_in_log={bool(record.get('query_in_log'))}"
        )
    if case in DEADLINE:
        return (
            f"caught={record.get('cancelled_caught')} delete={record.get('delete_reached')}"
            f" match={record.get('delete_session_matches')} escaped={'exception' in record}"
            f" grace_expired={record.get('grace_expired')}"
        )
    return (
        f"delete={record.get('delete_reached')}"
        f" session_match={record.get('delete_session_matches')}"
        f" auth_seen={TOKEN_VALUE in json.dumps(record.get('authorization_seen'))}"
        f" query_in_log={bool(record.get('query_in_log'))}"
        f" token_in_log={bool(record.get('token_in_log'))}"
        f" grace_expired={record.get('grace_expired')}"
    )


def run_case(case: str) -> dict[str, object]:
    work = Path(tempfile.mkdtemp(prefix=f"mcp-http-{case}-"))
    capture = LogCapture()
    capture.attach()
    server: Server | None = None
    try:
        if case == "closed_port":
            url = f"http://127.0.0.1:{_free_port()}/mcp?token={QUERY_SECRET}"
            record = anyio.run(partial(_connected, case, url, None, with_token=True))
        else:
            extra: list[str] = []
            if case == "unauthorized":
                extra = ["--expect-authorization", f"Bearer {TOKEN_VALUE}"]
            if case.endswith("_hang"):
                extra = ["--delete-hang", "30"]
            server = Server(work, *extra)
            record: dict[str, object] = {"server_ready": server.wait_ready()}
            if record["server_ready"]:
                url = server.url
                if case in {"query_url_normal", "unauthorized"}:
                    url = f"{url}?token={QUERY_SECRET}"
                with_token = case != "unauthorized"
                connected = partial(_connected, case, url, server, with_token=with_token)
                record.update(anyio.run(connected))
    finally:
        capture.detach()
        if server is not None:
            server.stop()
    _query_facts(record, capture)
    record["work"] = str(work)
    return record


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("cases", nargs="*")
    options = parser.parse_args()
    unknown = [case for case in options.cases if case not in CASES]
    if unknown:
        # 모르는 이름이 기본 갈래로 돌아 측정으로 세어진 적이 있다(PR 직전 리뷰 뒤의 양성 대조).
        parser.error(f"모르는 사례 {unknown}. 고를 수 있는 것: {list(CASES)}")
    os.environ[TOKEN_VARIABLE] = TOKEN_VALUE
    cases = options.cases or list(CASES)
    header = {
        "mcp": importlib.metadata.version("mcp"),
        "httpx2": importlib.metadata.version("httpx2"),
        "anyio": importlib.metadata.version("anyio"),
        "uvicorn": importlib.metadata.version("uvicorn"),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "repeat": options.repeat,
    }
    print(json.dumps(header, ensure_ascii=False), flush=True)
    rounds = Rounds()
    for case in cases:
        for index in range(options.repeat):
            label = f"{case}#{index + 1}"
            with rounds.round(label) as current:
                record = run_case(case)
                marked = _marked(case, record)
                print(json.dumps({"case": label, **record}, ensure_ascii=False), flush=True)
                current.mark(measured=marked, result=_verdict(case, record))
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    sys.exit(main())
