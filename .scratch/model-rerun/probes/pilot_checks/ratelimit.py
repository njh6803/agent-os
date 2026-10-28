"""rate_limit_event를 status별로 묶어, 맨 위 utilization과 unifiedWindows의 utilization 유무를 센다.

`<회차>/stream/*.jsonl`의 rate_limit_event마다 (status, 맨 위 utilization 유무, 창마다 utilization이
있는지, 창 이름들)을 세어 수와 함께 찍는다. 단언하지 않는 관찰 스크립트이고 읽기만 한다.

    uv run python .scratch/model-rerun/probes/pilot_checks/ratelimit.py \
        --rounds C:/Users/User/rerun-rounds
"""

import argparse
import json
from collections import Counter
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--rounds", type=Path, required=True, help="회차 폴더들의 뿌리")
ROOT: Path = parser.parse_args().rounds

c = Counter()
for sf in ROOT.glob("*/stream/*.jsonl"):
    for line in sf.open(encoding="utf-8", errors="replace"):
        if '"rate_limit_event"' not in line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") != "rate_limit_event":
            continue
        info = ev.get("rate_limit_info", {})
        uw = info.get("unifiedWindows") or {}
        uw_ok = bool(uw) and all(isinstance(w, dict) and "utilization" in w for w in uw.values())
        c[
            (
                info.get("status"),
                "top" if info.get("utilization") is not None else "no-top",
                "uw-ok" if uw_ok else "uw-missing",
                tuple(sorted(uw)),
            )
        ] += 1
for k, v in sorted(c.items(), key=str):
    print(v, k)
