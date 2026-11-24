"""항목 2 와 항목 3(HTTP 길)의 클라이언트. 하위 명령이 셋이다. 클라이언트는 httpx 다.

- `sample`: `/health` 와 `/thread-health` 를 번갈아 하나씩 차례로 보내고 5ms 쉰다. 보낸 시각
  (`time.monotonic`), 걸린 시간, 서버가 실은 견줌 안의 스레드 수를 한 줄씩 JSON 으로 `--out` 에
  쓴다. `--stop` 파일이 생기거나 `--max-seconds` 가 지나면 끝난다. 로그인 부하와 다른 프로세스라서
  부하를 보내는 쪽의 루프가 바쁜 것이 이 시간에 섞이지 않는다.
- `load`: K 마다 `--rounds` 번, 서버의 최대값을 되돌리고(`/reset`), 연결 K 개를 미리 열고(`/health`
  K 개), `--gap` 초 쉰 뒤 로그인 K 개를 한꺼번에 보낸다. 회차마다 `WINDOW <json>` 한 줄을 낸다. 창의
  시작은 K 개를 보내기 직전, 끝은 마지막 응답을 받은 때다(둘 다 `time.monotonic`). 리눅스의
  `time.monotonic` 은 프로세스 사이에 같은 시계라 `sample` 의 보낸 시각과 맞댈 수 있다.
- `timing`: 있는 계정의 맞는 비밀번호, 있는 계정의 틀린 비밀번호, 없는 계정, 계산하지 않는 없는 계정
  (`skip-`, 큰 차의 양성 대조), 견준 뒤 1ms·5ms 를 더 쓰는 없는 계정(`plus1ms-`·`plus5ms-`, 작은
  차의 양성 대조)을 하나씩 보내 걸린 시간을 잰다. 묶음 하나가 여섯 갈래를 한 번씩 섞은 차례로 바로
  이어 보내고, 묶음을 `--n` 번 돈다. 갈래마다 `[묶음 번호, 초]` 의 목록을 `RESULT <json>` 한 줄로
  낸다. 같은 묶음의 두 갈래를 짝지어 견주는 것은 `run.py` 다.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import anyio
import httpx
from common import PASSWORD, USER, WRONG_SAME_LENGTH, parse_cpus, pin

SAMPLE_PAUSE = 0.005


def sample(base: str, out: Path, stop: Path, max_seconds: float) -> int:
    deadline = time.monotonic() + max_seconds
    paths = ("/health", "/thread-health")
    turn = 0
    with (
        httpx.Client(base_url=base, timeout=120) as client,
        out.open("w", encoding="utf-8") as file,
    ):
        while not stop.exists() and time.monotonic() < deadline:
            path = paths[turn % 2]
            turn += 1
            sent = time.monotonic()
            response = client.get(path)
            latency = time.monotonic() - sent
            record = {
                "path": path,
                "sent": sent,
                "latency": latency,
                "status": response.status_code,
                "inside": response.json().get("inside"),
            }
            file.write(json.dumps(record) + "\n")
            time.sleep(SAMPLE_PAUSE)
    return 0


async def login_once(
    client: httpx.AsyncClient,
    body: dict[str, str],
    start: float,
    latencies: list[float],
    answers: list[tuple[int, bool]],
) -> None:
    response = await client.post("/login", json=body)
    latencies.append(time.monotonic() - start)
    answers.append((response.status_code, bool(response.json().get("ok"))))


async def load(base: str, ks: list[int], rounds: int, gap: float) -> int:
    limits = httpx.Limits(max_connections=256, max_keepalive_connections=256)
    body = {"username": USER, "password": PASSWORD}
    async with httpx.AsyncClient(base_url=base, timeout=300, limits=limits) as client:
        for k in ks:
            for index in range(rounds):
                await client.post("/reset")
                async with anyio.create_task_group() as group:
                    for _ in range(k):
                        group.start_soon(client.get, "/health")
                warm_end = time.monotonic()
                await anyio.sleep(gap)
                latencies: list[float] = []
                answers: list[tuple[int, bool]] = []
                start = time.monotonic()
                async with anyio.create_task_group() as group:
                    for _ in range(k):
                        group.start_soon(login_once, client, body, start, latencies, answers)
                end = time.monotonic()
                stats = (await client.get("/stats")).json()
                window = {
                    "k": k,
                    "round": index,
                    "warm_end": warm_end,
                    "start": start,
                    "end": end,
                    "latencies": latencies,
                    "ok": sum(1 for status, ok in answers if status == 200 and ok),
                    "stats": stats,
                }
                print(f"WINDOW {json.dumps(window)}", flush=True)
    return 0


def timing(base: str, n: int, seed: int) -> int:
    arms = {
        "correct": (USER, PASSWORD, 200),
        "wrong": (USER, WRONG_SAME_LENGTH, 401),
        "unknown": ("nobody", PASSWORD, 401),
        "skip_control": ("skip-nobody", PASSWORD, 401),
        "plus1ms_control": ("plus1ms-nobody", PASSWORD, 401),
        "plus5ms_control": ("plus5ms-nobody", PASSWORD, 401),
    }
    chooser = random.Random(seed)
    samples: dict[str, list[list[float]]] = {name: [] for name in arms}
    expected: dict[str, int] = {name: 0 for name in arms}
    with httpx.Client(base_url=base, timeout=120) as client:
        for _ in range(10):
            client.post("/login", json={"username": USER, "password": PASSWORD})
        for block in range(n):
            names = list(arms)
            chooser.shuffle(names)
            for name in names:
                user, password, status = arms[name]
                started = time.perf_counter()
                response = client.post("/login", json={"username": user, "password": password})
                samples[name].append([block, time.perf_counter() - started])
                expected[name] += int(response.status_code == status)
    result = {"kind": "http_timing", "blocks": n, "samples": samples, "expected": expected}
    print(f"RESULT {json.dumps(result)}", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("sample", "load", "timing"))
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--cpus", default="")
    parser.add_argument("--out", default="")
    parser.add_argument("--stop", default="")
    parser.add_argument("--max-seconds", type=float, default=900)
    parser.add_argument("--ks", default="1,4,16,40,100")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--gap", type=float, default=1.0)
    parser.add_argument("--n", type=int, default=80)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    pin(parse_cpus(args.cpus))
    base = f"http://127.0.0.1:{args.port}"
    if args.command == "sample":
        return sample(base, Path(args.out), Path(args.stop), args.max_seconds)
    if args.command == "load":
        ks = [int(part) for part in args.ks.split(",")]
        return anyio.run(load, base, ks, args.rounds, args.gap)
    return timing(base, args.n, args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
