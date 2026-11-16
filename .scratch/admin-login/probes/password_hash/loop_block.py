"""해시하는 동안 같은 이벤트 루프의 다른 코루틴이 도는지 재서 `RESULT <json>` 줄로 낸다.

틱 코루틴 하나가 `anyio.sleep(0)` 으로 루프에 차례를 넘기며 돌 때마다 시각을 적는다. 작업 하나가
도는 동안 틱이 몇 번 찍혔는지(`ticks`)와 틱 사이의 가장 긴 틈(`max_gap_ms`)을 작업에 걸린 시간
(`work_ms`)과 함께 낸다. 작업 앞 0.3초 동안의 가장 긴 틈(`idle_max_ms`)은 아무것도 시키지 않았을
때의 잡음이다. 셈과 갈래의 판정은 `run.py` 가 한다.

작업(`job`)은 다섯이다. 후보마다 요약 줄의 해시 한 번(`rows.py`), 긴 Argon2 해시, 대조 둘이다.
  긴 판     `argon2 m=262144,t=4,p=1`. 권고 줄이 아니다. 요약 줄의 Argon2 해시는 수십 ms 라 틈
            하나의 잡음에 판정이 흔들릴 수 있어, 같은 호출 길을 scrypt 만큼 길게 한 번 더 본다.
  gil-held  `sum(range(N))`. 한 번의 C 호출 안에서 GIL 을 쥔 채 돈다고 보고 고른 대조다. 스레드에
            넘겨도 루프가 멈추면 이 틱이 "GIL 을 쥔 스레드"를 알아본다는 뜻이고, 그래야 해시를
            스레드에 넘긴 갈래에서 틱이 이어진 것을 "해시가 GIL 을 놓는다"로 읽을 수 있다.
  gil-free  `time.sleep`. GIL 을 놓는 호출이다. 스레드에 넘기면 틱이 이어진다는 대조다.

갈래(`mode`)는 셋이다.
  thread    `await anyio.to_thread.run_sync(작업)`. 서버가 해시를 스레드에 넘기는 길이다.
  direct    코루틴 안에서 작업을 바로 부른다(해시만).
  parallel  작업 넷을 `anyio.to_thread.run_sync` 넷으로 한꺼번에 넘긴다. 걸린 시간을 thread 갈래의
            한 번과 견준다. GIL 을 놓으면 한 번과 비슷하고 쥐면 네 배에 가깝다.

틱 코루틴은 쉬지 않고 돌아 주 스레드가 GIL 을 거의 내내 쥔다. 그래서 thread 갈래의 `work_ms` 에는
작업 스레드가 GIL 을 넘겨받기를 기다린 시간이 섞인다. 해시 한 번의 시간은 `bench.py` 의 것을 쓴다.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from functools import partial
from importlib import metadata
from itertools import pairwise

import anyio
import anyio.to_thread
from rows import PASSWORD, Row, bind, headline

IDLE_SECONDS = 0.3
TAIL_SECONDS = 0.05
PARALLEL = 4
SUM_N = 10_000_000
SLEEP_SECONDS = 0.3
LONG = Row("argon2", "m=262144,t=4,p=1", "긴 판(권고 줄이 아니다)", (262144, 4, 1))
HELD = "gil-held sum(range)"
FREE = "gil-free time.sleep"


@dataclass(frozen=True)
class Job:
    name: str
    call: Callable[[], str]
    check: Callable[[str], bool]
    is_hash: bool


def held() -> str:
    return str(sum(range(SUM_N)))


def free() -> str:
    started = time.perf_counter()
    time.sleep(SLEEP_SECONDS)
    return str(time.perf_counter() - started)


def jobs() -> list[Job]:
    found: list[Job] = []
    for row in (headline("scrypt"), headline("argon2"), LONG):
        bound = bind(row)
        found.append(
            Job(bound.row.key, partial(bound.hash_password, PASSWORD), bound.genuine, is_hash=True)
        )
    expected = str(SUM_N * (SUM_N - 1) // 2)
    found.append(Job(HELD, held, lambda text: text == expected, is_hash=False))
    found.append(Job(FREE, free, lambda text: float(text) >= SLEEP_SECONDS, is_hash=False))
    return found


async def ticker(stamps: list[float]) -> None:
    while True:
        stamps.append(time.perf_counter())
        await anyio.sleep(0)


async def direct(job: Job) -> list[str]:
    return [job.call()]


async def threaded(job: Job) -> list[str]:
    return [await anyio.to_thread.run_sync(job.call)]


async def parallel(job: Job) -> list[str]:
    outputs: list[str] = []

    async def one() -> None:
        outputs.append(await anyio.to_thread.run_sync(job.call))

    async with anyio.create_task_group() as group:
        for _ in range(PARALLEL):
            group.start_soon(one)
    return outputs


MODES: dict[str, tuple[Callable[[Job], Awaitable[list[str]]], int]] = {
    "thread": (threaded, 1),
    "direct": (direct, 1),
    "parallel": (parallel, PARALLEL),
}


def longest(stamps: list[float]) -> float:
    return max((later - earlier for earlier, later in pairwise(stamps)), default=0.0)


async def observe(job: Job, mode: str, index: int) -> dict[str, object]:
    work, count = MODES[mode]
    stamps: list[float] = []
    outputs: list[str] = []
    started = ended = 0.0
    async with anyio.create_task_group() as group:
        group.start_soon(ticker, stamps)
        await anyio.sleep(IDLE_SECONDS)
        started = time.perf_counter()
        outputs = await work(job)
        ended = time.perf_counter()
        await anyio.sleep(TAIL_SECONDS)
        group.cancel_scope.cancel()
    before = [stamp for stamp in stamps if stamp <= started]
    inside = [stamp for stamp in stamps if started < stamp < ended]
    after = [stamp for stamp in stamps if stamp >= ended]
    return {
        "kind": "loop",
        "job": job.name,
        "mode": mode,
        "round": index + 1,
        "genuine": len(outputs) == count and all(job.check(text) for text in outputs),
        "work_ms": round((ended - started) * 1000, 2),
        "ticks": len(inside),
        "max_gap_ms": round(longest([*before[-1:], *inside, *after[:1]]) * 1000, 2),
        "idle_ticks": len(before),
        "idle_max_ms": round(longest(before) * 1000, 2),
        "after_ticks": len(after),
    }


async def run(rounds: int) -> None:
    environment = {
        "kind": "loop-env",
        "loop": type(asyncio.get_running_loop()).__name__,
        "thread_limit": anyio.to_thread.current_default_thread_limiter().total_tokens,
        "anyio": metadata.version("anyio"),
        "switch_interval": sys.getswitchinterval(),
        "platform": sys.platform,
    }
    print(f"RESULT {json.dumps(environment, ensure_ascii=False)}", flush=True)
    for index in range(rounds):
        for job in jobs():
            for mode in MODES:
                if mode == "direct" and not job.is_hash:
                    continue
                result = await observe(job, mode, index)
                print(f"RESULT {json.dumps(result, ensure_ascii=False)}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=5)
    args = parser.parse_args()
    rounds: int = args.rounds
    anyio.run(run, rounds)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
