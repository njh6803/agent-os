"""재시도가 다 쉬는 데 걸리는 시간의 바닥을 잰다(ADR 0035, 대상은 `filesystem_read_retry.py` 와
같다).

`_retrying` 은 `_RETRY_DELAYS`(1·2·4·8·16ms, 합 31ms)만큼 차례로 `time.sleep` 한다. 시험이 "상한을
다 쓴 뒤의 PluginError" 를 31ms 문턱으로 가르려면, 다섯 번 쉰 합이 31ms 보다 짧게 끝나는 일이 없어야
한다. 이 프로브는 어댑터의 `_retrying` 을 그대로 부르되 시도마다 `PermissionError` 를 내는 함수를
넘겨, 마지막 오류가 날 때까지의 시간을 N 번 잰다. 그 시간에는 시도 여섯 번의 몫도 든다.

`--delays` 는 `_RETRY_DELAYS` 를 그 값(쉼표로 나눈 초)으로 바꿔 잰다. 변이 표
`filesystem_read_retry_mutations.toml` 이 간격을 줄인 변이의 실제 합을 보려는 것이다.

표지: 회차마다 시도가 간격 수보다 하나 많이 불렸고 마지막에 `PermissionError` 가 났다. 아니면 그
회차는 측정이 아니고 종료 코드가 1 이다.

돌리는 법: 저장소 루트에서 `uv run python <이 파일> N [--burners K] [--delays 0.0002,…]`. 부하는
`filesystem_read_retry.py` 의 것과 같다. 표준 출력은 요약 JSON 한 줄이다.

못 보는 것: 다른 OS 와 다른 파이썬의 `time.sleep`.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from filesystem_read_retry import RETRY_WINDOW_NS, all_alive, burners  # noqa: E402

from agent_os.adapters import filesystem  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", type=int)
    parser.add_argument("--burners", type=int, default=0)
    parser.add_argument("--delays", default=None, help="쉼표로 나눈 초. 없으면 어댑터의 값")
    args = parser.parse_args()
    if args.delays is not None:
        filesystem._RETRY_DELAYS = tuple(float(value) for value in args.delays.split(","))
    spent: list[int] = []
    unmeasured = 0
    with burners(args.burners) as procs:
        for _ in range(args.runs):
            attempts = 0

            def refuse() -> None:
                nonlocal attempts
                attempts += 1
                raise PermissionError(13, "probe")

            started = time.perf_counter_ns()
            try:
                filesystem._retrying(refuse)
                raised = False
            except PermissionError:
                raised = True
            elapsed = time.perf_counter_ns() - started
            if attempts != len(filesystem._RETRY_DELAYS) + 1 or not raised:
                unmeasured += 1
                continue
            spent.append(elapsed)
        alive = all_alive(procs)
    ordered = sorted(spent)
    summary = {
        "runs": args.runs,
        "burners": args.burners,
        "burners_alive": alive,
        "unmeasured": unmeasured,
        "delays": filesystem._RETRY_DELAYS,
        "min_ms": round(ordered[0] / 1e6, 3) if ordered else None,
        "median_ms": round(ordered[len(ordered) // 2] / 1e6, 3) if ordered else None,
        "max_ms": round(ordered[-1] / 1e6, 3) if ordered else None,
        "under_31ms": sum(1 for value in ordered if value < RETRY_WINDOW_NS),
    }
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 1 if unmeasured or not alive else 0


if __name__ == "__main__":
    sys.exit(main())
