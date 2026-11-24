"""항목 2 와 항목 3(HTTP 길)의 서버. 작은 Starlette 앱을 `uvicorn.run` 으로 띄운다.

제품 코드가 아니다. 서버를 띄우는 모양은 `src/agent_os/main.py` 의 `uvicorn.run(...)` 을
따랐다(프로세스 하나, 루프와 HTTP 구현은 uvicorn 의 기본값, 접근 기록 켜짐). 경로는 다섯이다.

- `POST /login`: 몸통 `{"username", "password"}`. 있는 계정이면 그 저장 값과, 없는 계정이면 서버가
  뜰 때 만든 가짜 저장 값과 견준다(ADR 0062 "없는 계정 이름으로 온 로그인에도 같은 계산을 한 번").
  `--mode thread` 는 견줌을 `anyio.to_thread.run_sync` 로 넘기고, `--limit` 이 0 이 아니면 그 수의
  해시 전용 `anyio.CapacityLimiter` 를 넘긴다. `--mode pool` 은 견줌을 해시만 도는 스레드
  `--limit` 개(`concurrent.futures.ThreadPoolExecutor`, 이름 머리 `POOL_PREFIX`)에
  `run_in_executor` 로 넘긴다(실행 `9f1d11` 뒤에 더했다. 짜임은 `burst.py` 의 `--pool`).
  `--mode direct` 는 이벤트 루프에서 바로 견준다(루프가
  막히는 것을 `/health` 가 알아보는지의 양성 대조). `--mode sleep` 은 견줌 대신 `time.sleep` 을 같은
  길로 넘긴다(CPU 를 쓰지 않는 스레드의 대조). 이름이 `skip-` 로 시작하는 없는 계정은 계산 없이 바로
  401 을 낸다. 없는 계정에 계산을 하지 않는 판을 흉내 낸 항목 3 의 양성 대조(큰 차)다. 이름이
  `plus1ms-`·`plus5ms-` 로 시작하는 없는 계정은 가짜 저장 값과 견준 뒤 1ms·5ms 를 그 스레드에서
  바쁘게 기다린다. 항목 3 의 양성 대조(작은 차)다.
- `GET /health`: 루프에서 바로 답한다. 그때 견줌 안에 있던 스레드 수를 싣는다.
- `GET /thread-health`: 아무것도 하지 않는 함수를 기본 스레드 한도로 스레드에 넘긴 뒤 답한다. 해시가
  기본 한도의 자리를 차지하면 다른 스레드 일이 기다리는지 본다.
- `GET /stats`: 견줌 안에 동시에 있던 스레드 수의 최대값, 서버가 뜬 뒤 견줌을 맡은 스레드의
  가짓수(되돌리지 않는다), 그 스레드 이름이 모두 `POOL_PREFIX` 로 시작하는지(`dedicated`), 한도,
  상주 메모리, 루프의 종류.
- `POST /reset`: 그 최대값을 지금 값으로 되돌린다.
"""

from __future__ import annotations

import argparse
import asyncio
import secrets
import threading
import time
from collections.abc import AsyncIterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass, field

import anyio
import anyio.to_thread
import uvicorn
from argon2.exceptions import VerifyMismatchError
from common import PASSWORD, USER, hasher, memory, parse_cpus, pin
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

SLEEP_SECONDS = 0.04
EXTRA = {"plus1ms-": 0.001, "plus5ms-": 0.005}
POOL_PREFIX = "hashpool"


@dataclass
class State:
    mode: str
    limit: int
    cpus: list[int]
    lock: threading.Lock = field(default_factory=threading.Lock)
    inside: int = 0
    peak_inside: int = 0
    limiter: anyio.CapacityLimiter | None = None
    default_tokens: float = 0
    hash_threads: set[int] = field(default_factory=set[int])
    hash_names: set[str] = field(default_factory=set[str])
    pool: ThreadPoolExecutor | None = None


def build(state: State) -> Starlette:
    ph = hasher()
    users = {USER: ph.hash(PASSWORD)}
    dummy = ph.hash(secrets.token_urlsafe(18) + "A1!")

    def extra_for(name: str) -> float:
        for prefix, seconds in EXTRA.items():
            if name.startswith(prefix) and name not in users:
                return seconds
        return 0.0

    def check_then_wait(target: str, password: str, extra: float) -> bool:
        outcome = check(target, password)
        until = time.perf_counter() + extra
        while time.perf_counter() < until:
            pass
        return outcome

    def check(target: str, password: str) -> bool:
        with state.lock:
            state.inside += 1
            state.peak_inside = max(state.peak_inside, state.inside)
            state.hash_threads.add(threading.get_ident())
            state.hash_names.add(threading.current_thread().name)
        try:
            if state.mode == "sleep":
                time.sleep(SLEEP_SECONDS)
                return password == PASSWORD and target is users[USER]
            try:
                return ph.verify(target, password)
            except VerifyMismatchError:
                return False
        finally:
            with state.lock:
                state.inside -= 1

    async def login(request: Request) -> JSONResponse:
        body = await request.json()
        name = str(body["username"])
        password = str(body["password"])
        if name.startswith("skip-") and name not in users:
            return JSONResponse({"ok": False}, status_code=401)
        target = users.get(name, dummy)
        extra = extra_for(name)
        if state.mode == "direct":
            ok = check_then_wait(target, password, extra)
        elif state.pool is not None:
            loop = asyncio.get_running_loop()
            ok = await loop.run_in_executor(state.pool, check_then_wait, target, password, extra)
        else:
            ok = await anyio.to_thread.run_sync(
                check_then_wait, target, password, extra, limiter=state.limiter
            )
        ok = ok and name in users
        return JSONResponse({"ok": ok}, status_code=200 if ok else 401)

    async def health(request: Request) -> JSONResponse:
        del request
        return JSONResponse({"inside": state.inside})

    def read_inside() -> int:
        return state.inside

    async def thread_health(request: Request) -> JSONResponse:
        del request
        inside = await anyio.to_thread.run_sync(read_inside)
        return JSONResponse({"inside": inside})

    async def stats(request: Request) -> JSONResponse:
        del request
        rss, peak = memory()
        return JSONResponse(
            {
                "mode": state.mode,
                "limit": state.limit,
                "cpus": state.cpus,
                "peak_inside": state.peak_inside,
                "hash_threads": len(state.hash_threads),
                "dedicated": bool(state.hash_names)
                and all(name.startswith(POOL_PREFIX) for name in state.hash_names),
                "tokens": state.limit or state.default_tokens,
                "default_tokens": state.default_tokens,
                "rss": rss,
                "peak": peak,
                "loop": type(asyncio.get_running_loop()).__name__,
            }
        )

    async def reset(request: Request) -> JSONResponse:
        del request
        with state.lock:
            state.peak_inside = state.inside
        return JSONResponse({"peak_inside": state.peak_inside})

    @asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        del app
        state.default_tokens = anyio.to_thread.current_default_thread_limiter().total_tokens
        if state.mode == "pool":
            state.pool = ThreadPoolExecutor(max_workers=state.limit, thread_name_prefix=POOL_PREFIX)
        elif state.limit:
            state.limiter = anyio.CapacityLimiter(state.limit)
        yield
        if state.pool is not None:
            state.pool.shutdown(wait=True, cancel_futures=True)

    return Starlette(
        routes=[
            Route("/login", login, methods=["POST"]),
            Route("/health", health),
            Route("/thread-health", thread_health),
            Route("/stats", stats),
            Route("/reset", reset, methods=["POST"]),
        ],
        lifespan=lifespan,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--mode", choices=("thread", "direct", "sleep", "pool"), default="thread")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--cpus", default="")
    args = parser.parse_args()
    cpus = pin(parse_cpus(args.cpus))
    state = State(mode=args.mode, limit=args.limit, cpus=cpus)
    uvicorn.run(build(state), host="127.0.0.1", port=args.port, lifespan="on")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
