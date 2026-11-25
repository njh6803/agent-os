"""항목 3(함수 길). 맞는 비밀번호, 틀린 비밀번호, 없는 계정용 가짜 저장 값의 견줌 시간.

CPU 하나에 고정하고(`--cpus`), 묶음(block)을 `--n` 번 돈다. 묶음 하나는 갈래마다 한 번씩을 섞은
차례로 바로 이어 돈다(큰 차의 대조는 열 묶음에 한 번). 같은 묶음 안의 호출은 서로 1초 안쪽이라 같은
PC 의 부하가 천천히 바뀌는 몫이 묶음 안의 차에서 빠진다. `--repeats` 번 되풀이한다. 한 번마다 두
시간을 잰다. 벽시계 시간(`time.perf_counter`)과 그 스레드가 쓴 CPU 시간(`time.thread_time`)이다.
벽시계 시간이 공격자가 보는 쪽이다. 견줌은 제품이 할 모양처럼 `VerifyMismatchError` 를 잡아 거짓으로
바꾼다.

갈래.
- `correct`: 저장 값과 맞는 비밀번호. 참이어야 한다.
- `wrong_same_length`: 같은 길이의 틀린 비밀번호. 거짓이어야 한다.
- `wrong_long`: 128 자의 틀린 비밀번호. 거짓이어야 한다.
- `unknown_dummy`: 시작할 때 정해진 설정으로 만든 가짜 저장 값과 견줌. 거짓이어야 한다.
- `unknown_hash`: 없는 계정에 견줌 대신 해시를 한 번 만든다. 머리가 정해진 설정이어야 한다.
- `control_default_dummy`: 양성 대조(큰 차). 가짜 저장 값을 `PasswordHasher()` 의 기본 설정
  (m=65536, t=3, p=4)으로 만든 판. 거짓이어야 한다.
- `control_plus_0_25ms`, `control_plus_1ms`, `control_plus_5ms`: 양성 대조(작은 차). 맞는 비밀번호의
  견줌 뒤에 그만큼 바쁘게 기다린다(CPU 도 그만큼 쓴다). 참이어야 한다.

`--arms` 에 쉼표로 이름을 주면 그 갈래만 돈다(할당기 설정의 값을 프로세스 사이에서 견줄 때 쓴다,
`run.py` 의 `alloc`). 데우기는 첫 갈래로 한다.

`--threads N`(N 이 2 이상, 실행 `9f1d11` 뒤에 더했다)은 갈래의 호출 하나를 주 스레드가 아니라 같은
스레드 N 개(`ThreadPoolExecutor(max_workers=N)`, 프로세스 내내 같은 스레드)에서 한꺼번에 돈다. N
개가 `threading.Barrier` 에서 만나 함께 시작하고, 표본은 스레드마다 하나라 호출 하나가 표본 N 개다.
한 스레드에서 도는 판에서는 모든 할당이 주 아레나로 가서 아레나 수를 묶는 설정이 바꿀 것이
없어(어림, glibc 코드를 읽지 않았다) 여러 스레드가 함께 해시하는 자리를 흉내 낸다. 그 상황이 났다는
표지로 호출마다 견줌 안에 동시에 있던 스레드 수의 최대값이 N 인 호출의 수(`full`)와 견줌을 맡은
스레드의 가짓수(`threads`)를 `concurrency` 에 낸다.

`RESULT <json>` 한 줄. 갈래마다 `[묶음 번호, 벽시계 초, CPU 초]` 의 목록과 기대한 결과가 나온 수,
이 프로세스가 본 메모리 할당기 설정(`malloc_env`)을 낸다. 판정은 `run.py` 다.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import secrets
import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from common import PASSWORD, WRONG_LONG, WRONG_SAME_LENGTH, hasher, parse_cpus, pin

PREFIX = "$argon2id$v=19$m=19456,t=2,p=1$"
BIG_CONTROL = "control_default_dummy"
BIG_EVERY = 10


def busy_wait(seconds: float) -> None:
    until = time.perf_counter() + seconds
    while time.perf_counter() < until:
        pass


def arms() -> dict[str, tuple[Callable[[], object], object]]:
    ph = hasher()
    stored = ph.hash(PASSWORD)
    dummy = ph.hash(secrets.token_urlsafe(18) + "A1!")
    default_dummy = PasswordHasher().hash(secrets.token_urlsafe(18) + "A1!")

    def verify(target: str, password: str) -> bool:
        try:
            return ph.verify(target, password)
        except VerifyMismatchError:
            return False

    def plus(seconds: float) -> bool:
        outcome = verify(stored, PASSWORD)
        busy_wait(seconds)
        return outcome

    def fresh_hash() -> bool:
        return ph.hash(PASSWORD).startswith(PREFIX)

    return {
        "correct": (lambda: verify(stored, PASSWORD), True),
        "wrong_same_length": (lambda: verify(stored, WRONG_SAME_LENGTH), False),
        "wrong_long": (lambda: verify(stored, WRONG_LONG), False),
        "unknown_dummy": (lambda: verify(dummy, PASSWORD), False),
        "unknown_hash": (fresh_hash, True),
        BIG_CONTROL: (lambda: verify(default_dummy, PASSWORD), False),
        "control_plus_0_25ms": (lambda: plus(0.00025), True),
        "control_plus_1ms": (lambda: plus(0.001), True),
        "control_plus_5ms": (lambda: plus(0.005), True),
    }


Timed = tuple[object, float, float]


def timed(call: Callable[[], object]) -> Timed:
    """(결과, 벽시계 초, CPU 초)."""
    started, started_cpu = time.perf_counter(), time.thread_time()
    outcome = call()
    cpu = time.thread_time() - started_cpu
    return outcome, time.perf_counter() - started, cpu


@dataclass
class Together:
    """같은 스레드 N 개에서 호출 하나를 한꺼번에 돈다(`--threads`)."""

    count: int
    pool: ThreadPoolExecutor
    lock: threading.Lock = field(default_factory=threading.Lock)
    inside: int = 0
    peak: int = 0
    calls: int = 0
    full: int = 0
    idents: set[int] = field(default_factory=set[int])

    def run(self, call: Callable[[], object]) -> list[Timed]:
        barrier = threading.Barrier(self.count)
        with self.lock:
            self.peak = 0

        def task() -> Timed:
            barrier.wait()
            with self.lock:
                self.inside += 1
                self.peak = max(self.peak, self.inside)
                self.idents.add(threading.get_ident())
            try:
                return timed(call)
            finally:
                with self.lock:
                    self.inside -= 1

        futures = [self.pool.submit(task) for _ in range(self.count)]
        found = [future.result() for future in futures]
        self.calls += 1
        self.full += int(self.peak == self.count)
        return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cpus", default="")
    parser.add_argument("--n", type=int, default=400)
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--seed", type=int, default=11)
    parser.add_argument("--arms", default="")
    parser.add_argument("--threads", type=int, default=1)
    args = parser.parse_args()
    cpus = pin(parse_cpus(args.cpus))
    table = arms()
    if args.arms:
        keep = args.arms.split(",")
        table = {name: table[name] for name in keep}
    together = (
        Together(args.threads, ThreadPoolExecutor(max_workers=args.threads))
        if args.threads > 1
        else None
    )

    def invoke(call: Callable[[], object]) -> list[Timed]:
        return [timed(call)] if together is None else together.run(call)

    chooser = random.Random(args.seed)
    repeats: list[dict[str, object]] = []
    for _ in range(10):
        invoke(next(iter(table.values()))[0])
    if together is not None:
        together.calls = together.full = 0
    for _ in range(args.repeats):
        samples: dict[str, list[list[float]]] = {name: [] for name in table}
        expected: dict[str, int] = {name: 0 for name in table}
        for block in range(args.n):
            names = [name for name in table if name != BIG_CONTROL or block % BIG_EVERY == 0]
            chooser.shuffle(names)
            for name in names:
                call, want = table[name]
                for outcome, wall, cpu in invoke(call):
                    samples[name].append([block, wall, cpu])
                    expected[name] += int(outcome == want)
        repeats.append({"samples": samples, "expected": expected})
    concurrency: dict[str, int] = {}
    if together is not None:
        together.pool.shutdown(wait=True)
        concurrency = {
            "threads_wanted": together.count,
            "calls": together.calls,
            "full": together.full,
            "threads": len(together.idents),
        }
    malloc_env = {
        name: os.environ[name]
        for name in sorted(os.environ)
        if name.startswith("MALLOC_") or name == "GLIBC_TUNABLES"
    }
    result = {
        "kind": "timing",
        "blocks": args.n,
        "cpus": cpus,
        "malloc_env": malloc_env,
        "concurrency": concurrency,
        "repeats": repeats,
    }
    print(f"RESULT {json.dumps(result)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
