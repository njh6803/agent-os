"""모델에 붙었는지 묻는 요청을 실제 SDK가 어떻게 보내고, 실패를 어떻게 올리고, 무엇을 로그에 찍는지.

ADR 0067의 결정 "모델을 확인하는 법"과 "결과가 있는 자리"가 대 보지 않고 남긴 것을 루프백에서
잰다. 바깥 네트워크와 실제 키를 쓰지 않는다. 서버는 사례마다 127.0.0.1의 빈 포트에 새로 띄우는 표준
라이브러리 HTTP 서버이고, 키 글자(`probe-key-…`)는 지어낸 것이다. 그래서 여기서 본 것은
`anthropic`과 `openai` SDK가 요청을 어떻게 짓고 응답과 실패를 어떻게 읽는지까지다. 실제 제공사와
실제 모델 서버가 그 요청에 어떻게 답하는지는 `model_requests_live.py`가 보거나 재지 않았다.

회차와 표지:
- `versions`: 깔린 판. 표지는 네 패키지의 판이 모두 읽힌 것이다.
- `anthropic_retrieve`: id 하나를 묻는 요청의 메서드·경로·헤더. 표지는 서버가 요청을 정확히 한 건
  받았고 돌려받은 id가 물은 id인 것이다.
- `anthropic_statuses`, `openai_statuses`: 오류 상태마다 닿는 예외의 종류와, 서버가 본문에 되울린
  글(`probe-echo-…`)과 키가 예외의 글에 실리는지. 표지는 상태마다 예외의 `status_code`가 서버가 준
  상태와 같고 요청이 한 건인 것이다(재시도 0회로 불렀다).
- `anthropic_default_retries`: 재시도 대조. 기본 설정의 클라이언트가 500에 요청을 두 건 이상 보낸
  것이 표지이고, 위 회차의 "요청 한 건"이 `max_retries=0` 때문임을 이것이 가른다.
- `refused`, `timed_out`: 닫힌 포트와 답이 늦는 서버. 닫힌 포트의 표지는 두 SDK의 호출이 모두
  `APIConnectionError`(그 하위인 `APITimeoutError`는 아니다)로 끝난 것이다. 그 포트에는 서버를
  띄우지 않았으므로 받은 요청을 셀 것이 없다. 늦는 서버의 표지는 서버가 요청을 한 건 받았고, 호출이
  서버의 지연보다 먼저 `APITimeoutError`로 끝난 것이다.
- `anthropic_list_pages`: 목록이 여러 쪽일 때. 표지는 첫 쪽 요청에 `limit=1000`이 실린 것과, 끝까지
  돌 때 `after_id`가 든 둘째 요청이 간 것이다.
- `openai_list`: 목록 요청의 메서드·경로·헤더. 표지는 서버가 `/v1/models`를 받은 것이다.
- `anthropic_follows_run`: 실행이 쓰는 `ChatAnthropic`의 공개 칸(`anthropic_api_url`,
  `anthropic_api_key`)으로 만든 클라이언트가 실행과 같은 서버에 같은 키로 묻는지. 표지는 같은
  서버가 실행의 요청(POST)과 확인의 요청(GET)을 둘 다 그 키로 받은 것이다. 인자 없이 만든 SDK
  클라이언트의 주소는 결과로 적을 뿐 표지에 넣지 않는다.
- `log_lines`: 로그 수준 셋(기본인 WARNING, INFO, DEBUG)에서 찍히는 줄. 표지는 INFO에서 `httpx2`
  로거가 요청 경로와 상태가 든 줄을 찍은 것이다(줄을 모으는 길이 선다는 양성 대조).

표지가 없는 회차가 하나라도 있으면 1로 끝난다(`tools/probe_kit.py`의 `Rounds`).

    uv run python .scratch/connection-check/probes/model_requests_loopback.py
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import socket
import sys
import threading
import time
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.metadata import version
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import anthropic
import openai
from langchain_anthropic import ChatAnthropic

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.probe_kit import Rounds  # noqa: E402

KEY = "probe-key-0123456789"
RUN_KEY = "probe-run-key-9876543210"
ECHO = "probe-echo-7f3a"
MODEL = "probe-model"
SHORT = 0.5
SLOW = 3.0
ANTHROPIC_STATUSES = (401, 403, 404, 429, 500, 529)
OPENAI_STATUSES = (401, 404, 429, 500)
SCRUBBED_PREFIXES = ("ANTHROPIC_", "OPENAI_", "LANGSMITH_", "LANGCHAIN_")
SCRUBBED_NAMES = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY")

type Reply = tuple[int, dict[str, object], float]


@dataclass(frozen=True)
class Seen:
    """서버가 받은 요청 하나."""

    method: str
    path: str
    headers: dict[str, str]


class _Server(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False

    def __init__(self, script: Callable[[Seen], Reply]) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.script = script
        self.seen: list[Seen] = []

    def handle_error(
        self, request: socket.socket | tuple[bytes, socket.socket], client_address: object
    ) -> None:
        # 클라이언트가 쉬는 연결을 끊으면 표준 라이브러리가 그 추적을 표준 오류에 찍어 출력을
        # 가린다. 연결 쪽 오류만 삼키고, 스크립트의 버그 같은 다른 예외는 그대로 찍게 둔다.
        if isinstance(sys.exc_info()[1], OSError):
            return
        super().handle_error(request, client_address)


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _serve(self) -> None:
        length = int(self.headers.get("content-length", "0"))
        if length:
            self.rfile.read(length)
        server = self.server
        if not isinstance(server, _Server):
            raise TypeError("가짜 서버가 아니다")
        seen = Seen(self.command, self.path, {k.lower(): v for k, v in self.headers.items()})
        server.seen.append(seen)
        status, body, delay = server.script(seen)
        time.sleep(delay)
        raw = json.dumps(body).encode()
        try:
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
        except OSError:
            return  # 기한에 걸린 클라이언트가 먼저 끊었다

    do_GET = _serve  # noqa: N815
    do_POST = _serve  # noqa: N815

    def log_message(self, *args: object) -> None:
        return


@contextmanager
def serving(script: Callable[[Seen], Reply]) -> Iterator[tuple[str, list[Seen]]]:
    server = _Server(script)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", server.seen
    finally:
        server.shutdown()
        server.server_close()


@contextmanager
def environment(**values: str) -> Iterator[None]:
    before = {name: os.environ.get(name) for name in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for name, value in before.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


class _Collected(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.lines: list[tuple[str, str, str]] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.lines.append((record.name, record.levelname, record.getMessage()))


@contextmanager
def logging_at(level: int) -> Iterator[list[tuple[str, str, str]]]:
    root = logging.getLogger()
    handler = _Collected()
    before = root.level
    root.addHandler(handler)
    root.setLevel(level)
    try:
        yield handler.lines
    finally:
        root.setLevel(before)
        root.removeHandler(handler)


def scrub_environment() -> list[str]:
    """요청의 행선지와 키를 바꿀 수 있는 변수를 지운다. 지운 이름만 돌려준다."""
    names = [
        name
        for name in os.environ
        if name.upper().startswith(SCRUBBED_PREFIXES) or name.upper() in SCRUBBED_NAMES
    ]
    for name in names:
        del os.environ[name]
    return sorted(names)


def closed_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port: int = probe.getsockname()[1]
    return port


def model_body(model_id: str) -> dict[str, object]:
    return {
        "type": "model",
        "id": model_id,
        "display_name": model_id,
        "created_at": "2026-01-01T00:00:00Z",
    }


def error_body(status: int) -> dict[str, object]:
    """서버가 받은 키를 글에 되울리는 오류 본문. 예외의 글에 무엇이 실리는지 보려는 것이다."""
    message = f"{ECHO} status {status} key {KEY}"
    return {"type": "error", "error": {"type": "probe_error", "message": message}}


def fixed(status: int, body: dict[str, object], delay: float = 0.0) -> Callable[[Seen], Reply]:
    return lambda _seen: (status, body, delay)


def paged(seen: Seen) -> Reply:
    query = parse_qs(urlsplit(seen.path).query)
    if query.get("after_id") == ["probe-b"]:
        last = {"data": [model_body("probe-c")], "has_more": False}
        return 200, {**last, "first_id": "probe-c", "last_id": "probe-c"}, 0.0
    first = {"data": [model_body("probe-a"), model_body("probe-b")], "has_more": True}
    return 200, {**first, "first_id": "probe-a", "last_id": "probe-b"}, 0.0


def served(seen: Seen) -> Reply:
    one = {"id": "served-a", "object": "model", "created": 0, "owned_by": "probe"}
    if urlsplit(seen.path).path.endswith("/models"):
        other = {**one, "id": "served-b"}
        return 200, {"object": "list", "data": [one, other], "has_more": True}, 0.0
    return 200, one, 0.0


def run_or_check(seen: Seen) -> Reply:
    if seen.method == "GET":
        return 200, model_body(MODEL), 0.0
    return 404, error_body(404), 0.0


async def attempt(
    call: Callable[[str], Awaitable[object]], url: str
) -> tuple[object, Exception | None, float]:
    started = time.perf_counter()
    try:
        value = await call(url)
    except Exception as error:  # noqa: BLE001  어떤 예외로 닿는지가 재는 것이다
        return None, error, round(time.perf_counter() - started, 2)
    return value, None, round(time.perf_counter() - started, 2)


def kind(error: Exception | None) -> str:
    if error is None:
        return "예외 없음"
    return f"{type(error).__module__}.{type(error).__qualname__}"


def bases(error: Exception | None, module: object) -> list[str]:
    """그 예외가 속하는 SDK의 공개 예외 이름. 화면의 갈래를 무엇으로 가를지 보려는 것이다."""
    names = ("APIStatusError", "APIConnectionError", "APITimeoutError", "APIError")
    return [name for name in names if isinstance(error, getattr(module, name))]


def emit(case: str, **data: object) -> None:
    print(json.dumps({"case": case, **data}, ensure_ascii=False, default=repr), flush=True)


async def anthropic_retrieve(url: str) -> object:
    async with anthropic.AsyncAnthropic(api_key=KEY, base_url=url, max_retries=0) as client:
        return await client.models.retrieve(MODEL)


async def anthropic_default_retries(url: str) -> object:
    async with anthropic.AsyncAnthropic(api_key=KEY, base_url=url) as client:
        return await client.models.retrieve(MODEL)


async def anthropic_short(url: str) -> object:
    async with anthropic.AsyncAnthropic(
        api_key=KEY, base_url=url, max_retries=0, timeout=SHORT
    ) as client:
        return await client.models.retrieve(MODEL)


async def openai_list(url: str) -> object:
    async with openai.AsyncOpenAI(api_key=KEY, base_url=f"{url}/v1", max_retries=0) as client:
        page = await client.models.list()
        return [model.id for model in page.data]


async def openai_short(url: str) -> object:
    async with openai.AsyncOpenAI(
        api_key=KEY, base_url=f"{url}/v1", max_retries=0, timeout=SHORT
    ) as client:
        page = await client.models.list()
        return [model.id for model in page.data]


async def status_rows(
    statuses: tuple[int, ...], call: Callable[[str], Awaitable[object]], module: object
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for status in statuses:
        with serving(fixed(status, error_body(status))) as (url, seen):
            _, error, elapsed = await attempt(call, url)
            rows.append(
                {
                    "status": status,
                    "error": kind(error),
                    "bases": bases(error, module),
                    "status_code": getattr(error, "status_code", None),
                    "requests": len(seen),
                    "echo_in_text": ECHO in str(error),
                    "key_in_text": KEY in str(error),
                    "text": str(error)[:160],
                    "seconds": elapsed,
                }
            )
    return rows


def all_single(rows: list[dict[str, object]]) -> bool:
    return bool(rows) and all(
        row["status_code"] == row["status"] and row["requests"] == 1 for row in rows
    )


def named(rows: list[dict[str, object]]) -> str:
    return ", ".join(f"{row['status']} {str(row['error']).rsplit('.', 1)[-1]}" for row in rows)


async def measure(rounds: Rounds) -> None:
    with rounds.round("versions") as current:
        packages = ("anthropic", "openai", "httpx2", "langchain-anthropic")
        found = {name: version(name) for name in packages}
        emit("versions", **found, python=sys.version.split()[0], scrubbed=scrub_environment())
        text = ", ".join(f"{name} {value}" for name, value in found.items())
        current.mark(measured=len(found) == len(packages), result=text)

    with rounds.round("anthropic_retrieve") as current:
        with serving(fixed(200, model_body(MODEL))) as (url, seen):
            value, error, _ = await attempt(anthropic_retrieve, url)
            sent = [(one.method, one.path) for one in seen]
            headers = seen[0].headers if seen else {}
        emit(
            "anthropic_retrieve",
            sent=sent,
            error=kind(error),
            returned_id=getattr(value, "id", None),
            key_header=headers.get("x-api-key") == KEY,
            authorization_header="authorization" in headers,
            version_header=headers.get("anthropic-version"),
            user_agent=headers.get("user-agent"),
        )
        current.mark(
            measured=len(sent) == 1 and getattr(value, "id", None) == MODEL,
            result=" ".join(sent[0]) if sent else "요청 없음",
        )

    with rounds.round("anthropic_statuses") as current:
        rows = await status_rows(ANTHROPIC_STATUSES, anthropic_retrieve, anthropic)
        emit("anthropic_statuses", rows=rows)
        current.mark(measured=all_single(rows), result=named(rows))

    with rounds.round("anthropic_default_retries") as current:
        with serving(fixed(500, error_body(500))) as (url, seen):
            _, error, elapsed = await attempt(anthropic_default_retries, url)
            count = len(seen)
        emit("anthropic_default_retries", error=kind(error), requests=count, seconds=elapsed)
        current.mark(measured=count >= 2, result=f"기본 설정은 500에 요청 {count}건")

    with rounds.round("refused") as current:
        port = closed_port()
        url = f"http://127.0.0.1:{port}"
        _, first, first_seconds = await attempt(anthropic_retrieve, url)
        _, second, second_seconds = await attempt(openai_list, url)
        emit(
            "refused",
            anthropic={
                "error": kind(first),
                "bases": bases(first, anthropic),
                "seconds": first_seconds,
                "text": str(first)[:160],
            },
            openai={
                "error": kind(second),
                "bases": bases(second, openai),
                "seconds": second_seconds,
                "text": str(second)[:160],
            },
        )
        current.mark(
            measured=isinstance(first, anthropic.APIConnectionError)
            and not isinstance(first, anthropic.APITimeoutError)
            and isinstance(second, openai.APIConnectionError)
            and not isinstance(second, openai.APITimeoutError),
            result=f"anthropic {kind(first).rsplit('.', 1)[-1]} {first_seconds}초, "
            f"openai {kind(second).rsplit('.', 1)[-1]} {second_seconds}초",
        )

    with rounds.round("timed_out") as current:
        with serving(fixed(200, model_body(MODEL), SLOW)) as (url, seen):
            _, first, first_seconds = await attempt(anthropic_short, url)
            first_requests = len(seen)
        with serving(served_slowly) as (url, seen):
            _, second, second_seconds = await attempt(openai_short, url)
            second_requests = len(seen)
        emit(
            "timed_out",
            anthropic={
                "error": kind(first),
                "bases": bases(first, anthropic),
                "seconds": first_seconds,
                "requests": first_requests,
            },
            openai={
                "error": kind(second),
                "bases": bases(second, openai),
                "seconds": second_seconds,
                "requests": second_requests,
            },
        )
        current.mark(
            measured=first_requests == 1
            and second_requests == 1
            and first_seconds < SLOW
            and second_seconds < SLOW
            and isinstance(first, anthropic.APITimeoutError)
            and isinstance(second, openai.APITimeoutError),
            result=f"anthropic {kind(first).rsplit('.', 1)[-1]} {first_seconds}초, "
            f"openai {kind(second).rsplit('.', 1)[-1]} {second_seconds}초",
        )

    with rounds.round("anthropic_list_pages") as current, serving(paged) as (url, seen):
        async with anthropic.AsyncAnthropic(api_key=KEY, base_url=url, max_retries=0) as client:
            await client.models.list()
            plain = [one.path for one in seen]
            seen.clear()
            page = await client.models.list(limit=1000)
            first_page = [one.path for one in seen]
            first_ids = [model.id for model in page.data]
            seen.clear()
            every = [model.id async for model in client.models.list(limit=1000)]
            walked = [one.path for one in seen]
        emit(
            "anthropic_list_pages",
            plain=plain,
            first_page=first_page,
            first_ids=first_ids,
            has_more=page.has_more,
            walked=walked,
            every=every,
        )
        current.mark(
            measured=first_page == ["/v1/models?limit=1000"]
            and any("after_id=probe-b" in path for path in walked),
            result=f"첫 쪽만 읽으면 요청 {len(first_page)}건에 {len(first_ids)}개, "
            f"끝까지 돌면 요청 {len(walked)}건에 {len(every)}개",
        )

    with rounds.round("openai_list") as current, serving(served) as (url, seen):
        async with openai.AsyncOpenAI(api_key=KEY, base_url=f"{url}/v1", max_retries=0) as client:
            page = await client.models.list()
            first_ids = [model.id for model in page.data]
            headers = seen[0].headers if seen else {}
            first_page = [(one.method, one.path) for one in seen]
            seen.clear()
            every = [model.id async for model in client.models.list()]
            walked = [one.path for one in seen]
            seen.clear()
            await client.models.retrieve("served-a")
            single = [(one.method, one.path) for one in seen]
        emit(
            "openai_list",
            first_page=first_page,
            first_ids=first_ids,
            bearer=headers.get("authorization") == f"Bearer {KEY}",
            user_agent=headers.get("user-agent"),
            walked=walked,
            every=every,
            single=single,
        )
        current.mark(
            measured=first_page == [("GET", "/v1/models")],
            result=f"GET /v1/models, 서버가 has_more를 줘도 끝까지 요청 {len(walked)}건",
        )

    with rounds.round("openai_statuses") as current:
        rows = await status_rows(OPENAI_STATUSES, openai_list, openai)
        emit("openai_statuses", rows=rows)
        current.mark(measured=all_single(rows), result=named(rows))

    with rounds.round("anthropic_follows_run") as current, serving(run_or_check) as (url, seen):
        with environment(ANTHROPIC_API_URL=url, ANTHROPIC_API_KEY=RUN_KEY):
            chat = ChatAnthropic(model_name=MODEL, max_tokens_to_sample=16, timeout=None, stop=None)
            bare = anthropic.AsyncAnthropic()
            bare_address = str(bare.base_url)
            await bare.close()
            _, run_error, _ = await attempt(lambda _url: chat.ainvoke("ping"), url)
            run_sent = [
                (one.method, one.path, one.headers.get("x-api-key") == RUN_KEY) for one in seen
            ]
            seen.clear()
            async with anthropic.AsyncAnthropic(
                api_key=chat.anthropic_api_key.get_secret_value(),
                base_url=chat.anthropic_api_url,
                max_retries=0,
            ) as client:
                found_model = await client.models.retrieve(MODEL)
            check_sent = [
                (one.method, one.path, one.headers.get("x-api-key") == RUN_KEY) for one in seen
            ]
        emit(
            "anthropic_follows_run",
            chat_address_is_server=chat.anthropic_api_url == url,
            bare_address=bare_address,
            run_error=kind(run_error),
            run_sent=run_sent,
            check_sent=check_sent,
            returned_id=found_model.id,
        )
        current.mark(
            measured=("POST", "/v1/messages", True) in run_sent
            and ("GET", f"/v1/models/{MODEL}", True) in check_sent,
            result=f"실행과 확인이 같은 서버와 같은 키, 인자 없는 클라이언트는 {bare_address}",
        )

    with rounds.round("log_lines") as current:
        counts: dict[str, dict[str, int]] = {}
        leaked: dict[str, list[str]] = {}
        shown: list[tuple[str, str, str]] = []
        for label, level in (
            ("WARNING", logging.WARNING),
            ("INFO", logging.INFO),
            ("DEBUG", logging.DEBUG),
        ):
            with logging_at(level) as lines:
                with serving(fixed(200, model_body(MODEL))) as (url, _):
                    await attempt(anthropic_retrieve, url)
                with serving(fixed(401, error_body(401))) as (url, _):
                    await attempt(anthropic_retrieve, url)
                with serving(served) as (url, _):
                    await attempt(openai_list, url)
                per_logger: dict[str, int] = {}
                for name, _, _ in lines:
                    per_logger[name] = per_logger.get(name, 0) + 1
                counts[label] = per_logger
                leaked[label] = sorted({name for name, _, text in lines if KEY in text})
                if level == logging.INFO:
                    shown = [(name, rank, text[:160]) for name, rank, text in lines]
        emit("log_lines", counts=counts, key_in_lines_of=leaked, info_lines=shown)
        positive = any(
            name.startswith("httpx2") and f"/v1/models/{MODEL}" in text and "200" in text
            for name, _, text in shown
        )
        totals = {label: sum(per.values()) for label, per in counts.items()}
        current.mark(
            measured=positive,
            result=f"WARNING {totals['WARNING']}줄, INFO {totals['INFO']}줄, DEBUG "
            f"{totals['DEBUG']}줄. 키가 든 줄의 로거: {leaked}",
        )


def served_slowly(seen: Seen) -> Reply:
    status, body, _ = served(seen)
    return status, body, SLOW


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    rounds = Rounds()
    asyncio.run(measure(rounds))
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
