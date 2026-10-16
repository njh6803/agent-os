"""pytest 를 같은 시각에 두 벌 돌려, 세션 둘이 겹쳐 커밋할 때의 부하를 잰다(ADR 0035).

`pytest_run.py` 를 두 프로세스로 한꺼번에 띄운다. 두 벌이 실제로 겹쳐 돌았는지는 시작과 끝의
시각으로 대 본다(한쪽의 시작이 다른 쪽의 끝보다 앞서야 한다). 같은 체크아웃에서 pytest 만 돌리므로
web verify 등 다른 검사가 얹는 부하와, 서로 다른 워크트리에서 도는 실제 세션의 조건은 빠진다.

표지: 두 껍질의 표지(통과 집계 줄, xdist 가 뜬 줄)가 있고 두 벌이 겹쳐 돌았을 때만 측정이다. 아니면
종료 코드를 1 로 낸다. 사례가 실패한 것은 측정의 결과라 `failed` 에 센다.

돌리는 법: 저장소 루트에서
`uv run python .scratch/harness/probes/precommit_xdist/pair.py [프로세스 수]`. 표준 출력이
`results/pair.txt` 다. 원본 출력은 `results/pair_a_pytest.txt` 와 `pair_b_pytest.txt`.

못 보는 것: 위에서 빠진 부하. 한 번의 값이라 회차 사이의 흔들림.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
RESULTS = HERE / "results"
NAMES = ("a", "b")


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "8"
    outs = {name: RESULTS / f"pair_{name}_pytest.txt" for name in NAMES}
    for out in outs.values():
        Path(f"{out}.json").unlink(missing_ok=True)
    zero = time.monotonic()
    procs: dict[str, subprocess.Popen[bytes]] = {}
    starts: dict[str, float] = {}
    for name in NAMES:
        command = ["uv", "run", "python", str(HERE / "pytest_run.py"), mode, str(outs[name])]
        procs[name] = subprocess.Popen(command, cwd=ROOT, stdout=subprocess.DEVNULL)
        starts[name] = time.monotonic() - zero
    ends: dict[str, float] = {}
    while len(ends) < len(NAMES):
        for name, proc in procs.items():
            if name not in ends and proc.poll() is not None:
                ends[name] = time.monotonic() - zero
        time.sleep(1)
    overlapped = max(starts.values()) < min(ends.values())
    bad = not overlapped
    for name in NAMES:
        path = Path(f"{outs[name]}.json")
        row = (
            json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"missing": ["요약"]}
        )
        bad = bad or bool(row["missing"])
        times = {"start_s": round(starts[name], 1), "end_s": round(ends[name], 1)}
        print(json.dumps({"run": name, **times, **row}, ensure_ascii=False), flush=True)
    print(json.dumps({"겹쳐 돌았다": overlapped}, ensure_ascii=False), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
