"""항목 1. 로그인 K 개가 한꺼번에 들어올 때 프로세스의 최고 상주 메모리와 요청 하나의 걸린 시간.

프로세스 하나에 갈래 하나다. `run.py` 가 갈래마다 새 프로세스로 띄우고 마지막 줄 `RESULT <json>` 을
읽는다. 순서는 이렇다. CPU 를 고정하고(`--cpus`), 아주 작은 설정의 해시로 가져오기와 라이브러리의 첫
몫을 바닥에 넣은 뒤 바닥(`rss_before`, `peak_before`)을 읽는다. 그다음 저장 값 하나를 정해진
설정으로 만들고(해시 한 번), K 개의 견줌(맞는 비밀번호)을 한꺼번에 `anyio.to_thread.run_sync` 로
넘긴다. `--limit 0` 이면 AnyIO 의 기본 스레드 한도를, 아니면 그 수의 `anyio.CapacityLimiter` 를
넘긴다.

재려는 상황이 났다는 표지는 이 프로세스가 직접 센 값이다. K 개의 견줌이 모두 참이고, 견줌 함수에
들어가 아직 나오지 않은 스레드 수의 최대값(`peak_inside`)이 한도를 넘지 않는다. 그 최대값이 실제로
겹친 해시의 수이고 결과와 함께 낸다. 판정은 `run.py` 가 한다.

끝난 뒤의 상주. 끝난 직후(`rss_after`)와 0.5초 뒤(`rss_idle`)를 읽는다. `--late` 초를 주면 그만큼 더
쉬고, 빈 일 하나를 `anyio.to_thread.run_sync` 로 넘기고, 1초 더 쉰 뒤(`rss_late`)도 읽는다. AnyIO 의
일꾼 스레드는 10초(`MAX_IDLE_TIME`) 넘게 논 것이 스스로 끝나지 않는다. 다음 `run_sync` 가 놀던 일꾼
하나를 꺼내 쓸 때 오래 논 나머지에게 끝내라고 넣는다(코드를 읽었다, anyio 4.15.1
`_backends/_asyncio.py` 1045행, 2674~2696행). 그래서 빈 일 하나가 그 정리를 부른다. 그것이 났다는
표지는 살아 있는 스레드 수(`threads_late`)가 2(주 스레드와 빈 일을 맡은 일꾼 하나)인 것이다. 첫 판은
빈 일 없이 12초 쉬고 1 을 기다렸는데, 시험 실행에서 41 과 5(한도 40 과 4 의 일꾼이 모두 살아
있었다)가 나와 고쳤다.

`--repeat N` 은 같은 K 개를 한 프로세스에서 N 번 잇달아 넘기고, 번마다 끝난 직후의 상주와 최고
상주를 `repeats` 에 낸다. 끝난 뒤에 남는 상주가 새는 것(번마다 는다)인지 다시 쓰는 것(첫 번 뒤로
늘지 않는다)인지 가른다. 메모리 할당기의 설정(`GLIBC_TUNABLES`, `MALLOC_` 로 시작하는 환경 변수)은
`run.py` 가 환경으로 주고, 이 프로세스가 본 값을 `malloc_env` 에 낸다.

`--churn N` 은 해시를 넘기기 0.3초 전부터 다 넘길 때까지, 해시가 아닌 스레드 일(5ms 잠들기)을 기본
스레드 한도로 N 개씩 쉬지 않고 넘긴다. 제품에서 FastAPI 의 동기 경로가 같은 일꾼 스레드 묶음을 쓰는
것을 흉내 낸다. 해시 전용 한도가 동시 해시의 수를 묶어도, 해시가 여러 일꾼 스레드에 돌아가며 얹히면
남는 상주가 그 한도보다 커지는지 본다. 표지로 해시를 넘기는 동안 그 일이 한 번 이상 돈 수
(`churn_during`)를 낸다. 모든 갈래에서 견줌을 맡은 일꾼 스레드의 가짓수(`hash_threads`)도 낸다.

`--pool N` 은 해시를 AnyIO 의 일꾼 묶음이 아니라 해시만 도는 스레드 N 개에서 돌린다(실행 `9f1d11`
뒤에 더했다). `concurrent.futures.ThreadPoolExecutor(max_workers=N)` 를 만들고 견줌마다
`asyncio.get_running_loop().run_in_executor(pool, check)` 를 기다린다. 동시에 도는 견줌은 그 묶음의
스레드 수가 묶으므로 `CapacityLimiter` 를 따로 두지 않는다(`tokens` 가 N). 그 묶음의 스레드는 이름이
`POOL_PREFIX` 로 시작한다. 그래서 견줌을 맡은 스레드의 이름(`hash_names`)이 모두 그 머리인 것이
해시가 전용 스레드에서 돌았다는 표지다(`dedicated`). AnyIO 의 일꾼 스레드는 이름이 다르다. 묶음은
0.5초 뒤의 읽기(와 늦게 읽기)를 마친 뒤 닫는다. 그 전까지 전용 스레드는 살아 있다.

`--work sleep` 은 대조다. 견줌 대신 `time.sleep` 을 같은 길로 넘긴다. 스레드 수만큼 메모리가 느는
것이 해시의 몫이 아니라 스레드의 몫이라는 해석을 가른다. `--work control` 은 메모리 읽기의 양성
대조다. 64 MiB 를 잡아 쪽(4096 바이트)마다 한 바이트를 쓴다(선례 `../password_hash/peak_memory.py`).

걸린 시간은 K 개를 넘기기 직전의 시각부터 그 요청의 결과를 받은 시각까지다(`time.perf_counter`).
"""

from __future__ import annotations

import argparse
import asyncio
import gc
import json
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

import anyio
import anyio.to_thread
from common import MIB, PASSWORD, hasher, memory, parse_cpus, pin, tiny_hasher

CONTROL_BYTES = 64 * MIB
PAGE = 4096
SLEEP_SECONDS = 0.04
WORKER_EXIT_WAIT = 1.0
CHURN_SLEEP = 0.005
CHURN_WARMUP = 0.3
POOL_PREFIX = "hashpool"


def nothing() -> None:
    """늦게 읽기 전에 일꾼 스레드 하나를 깨우는 빈 일."""


def control() -> dict[str, object]:
    rss_before, peak_before = memory()
    buffer = bytearray(CONTROL_BYTES)
    for offset in range(0, CONTROL_BYTES, PAGE):
        buffer[offset] = 1
    rss_after, peak_after = memory()
    return {
        "genuine": sum(buffer[::PAGE]) == CONTROL_BYTES // PAGE,
        "nominal_bytes": CONTROL_BYTES,
        "rss_before": rss_before,
        "peak_before": peak_before,
        "rss_after": rss_after,
        "peak_after": peak_after,
    }


def churn_step() -> None:
    """해시가 아닌 스레드 일(제품의 동기 경로를 흉내 낸다)."""
    time.sleep(CHURN_SLEEP)


@dataclass
class Shape:
    k: int
    limit: int
    work: str
    late: float
    repeat: int
    churn: int
    pool: int


async def burst(shape: Shape) -> dict[str, object]:
    ph = hasher()
    rss_before, peak_before = memory()
    stored = ph.hash(PASSWORD)
    lock = threading.Lock()
    inside = 0
    peak_inside = 0
    hash_threads: set[int] = set()
    hash_names: set[str] = set()
    pool = (
        ThreadPoolExecutor(max_workers=shape.pool, thread_name_prefix=POOL_PREFIX)
        if shape.pool
        else None
    )

    def check() -> bool:
        nonlocal inside, peak_inside
        with lock:
            inside += 1
            peak_inside = max(peak_inside, inside)
            hash_threads.add(threading.get_ident())
            hash_names.add(threading.current_thread().name)
        try:
            if shape.work == "sleep":
                time.sleep(SLEEP_SECONDS)
                return True
            return ph.verify(stored, PASSWORD)
        finally:
            with lock:
                inside -= 1

    default_tokens = anyio.to_thread.current_default_thread_limiter().total_tokens
    limiter = anyio.CapacityLimiter(shape.limit) if shape.limit else None
    tokens = shape.pool or shape.limit or default_tokens
    latencies: list[float] = []
    results: list[bool] = []
    started = time.perf_counter()
    finished = anyio.Event()
    churn_calls = 0

    async def one() -> None:
        if pool is None:
            outcome = await anyio.to_thread.run_sync(check, limiter=limiter)
        else:
            outcome = await asyncio.get_running_loop().run_in_executor(pool, check)
        latencies.append(time.perf_counter() - started)
        results.append(outcome)

    async def wave() -> list[float]:
        async with anyio.create_task_group() as group:
            for _ in range(shape.k):
                group.start_soon(one)
        return list(memory())

    async def churner() -> None:
        nonlocal churn_calls
        while not finished.is_set():
            await anyio.to_thread.run_sync(churn_step)
            churn_calls += 1

    async with anyio.create_task_group() as outer:
        for _ in range(shape.churn):
            outer.start_soon(churner)
        if shape.churn:
            await anyio.sleep(CHURN_WARMUP)
        churn_before = churn_calls
        started = time.perf_counter()
        repeats = [await wave()]
        wall = time.perf_counter() - started
        for _ in range(shape.repeat - 1):
            repeats.append(await wave())
        churn_during = churn_calls - churn_before
        finished.set()
    rss_after, peak_after = repeats[0]
    gc.collect()
    await anyio.sleep(0.5)
    rss_idle, _ = memory()
    threads_idle = threading.active_count()
    late: dict[str, object] = {}
    if shape.late:
        await anyio.sleep(shape.late)
        await anyio.to_thread.run_sync(nothing)
        await anyio.sleep(WORKER_EXIT_WAIT)
        late = {"rss_late": memory()[0], "threads_late": threading.active_count()}
    if pool is not None:
        pool.shutdown(wait=True)
    return late | {
        "genuine": len(results) == shape.k * shape.repeat and all(results),
        "peak_inside": peak_inside,
        "hash_threads": len(hash_threads),
        "hash_names": sorted(hash_names),
        "dedicated": bool(hash_names) and all(n.startswith(POOL_PREFIX) for n in hash_names),
        "pool": shape.pool,
        "churn_during": churn_during,
        "tokens": tokens,
        "default_tokens": default_tokens,
        "latencies": latencies[: shape.k],
        "repeats": repeats,
        "malloc_env": {
            name: os.environ[name]
            for name in sorted(os.environ)
            if name.startswith("MALLOC_") or name == "GLIBC_TUNABLES"
        },
        "wall": wall,
        "rss_before": rss_before,
        "peak_before": peak_before,
        "rss_after": rss_after,
        "peak_after": peak_after,
        "rss_idle": rss_idle,
        "threads_idle": threads_idle,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--k", type=int, required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--cpus", default="")
    parser.add_argument("--work", choices=("argon2", "sleep", "control"), default="argon2")
    parser.add_argument("--late", type=float, default=0)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--churn", type=int, default=0)
    parser.add_argument("--pool", type=int, default=0)
    args = parser.parse_args()
    cpus = pin(parse_cpus(args.cpus))
    tiny_hasher().hash(PASSWORD)
    gc.collect()
    result: dict[str, object] = {
        "kind": "burst",
        "k": args.k,
        "limit": args.limit,
        "work": args.work,
        "cpus": cpus,
    }
    if args.work == "control":
        result.update(control())
    else:
        shape = Shape(args.k, args.limit, args.work, args.late, args.repeat, args.churn, args.pool)
        result.update(anyio.run(burst, shape))
    print(f"RESULT {json.dumps(result)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
