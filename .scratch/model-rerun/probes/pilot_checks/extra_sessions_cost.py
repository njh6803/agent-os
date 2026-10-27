"""러너가 띄우지 않은 세션(`session-ids.txt` 밖)의 공식 단가 어림을 회차마다 찍는다.

전용 설정 폴더(`--projects`)의 `C--Users-User-rerun-rounds-<회차>-clone/*.jsonl` 가운데 그 회차의
`session-ids.txt`에 없는 파일을 회차마다 세고 달러 어림과 모델을 찍는다. 단가는
`tools/rerun_cost.py`의 `PRICES`를 옮겼다(옮길 때 그 파일을 다른 세션이 고치는 중이라 import하지
않았다). 응답은 `message.id`마다 마지막 usage 하나로 세고, 캐시 쓰기는 응답의 ephemeral_5m/1h로
나눈다. 단언하지 않는 관찰 스크립트이고 읽기만 한다.

    uv run python .scratch/model-rerun/probes/pilot_checks/extra_sessions_cost.py \
        --rounds C:/Users/User/rerun-rounds --projects C:/Users/User/.claude-rerun/projects
"""

import argparse
import json
from pathlib import Path

PRICES = {
    "claude-opus-5-5": (4.0, 20.0, 0.20),
    "claude-sonnet-5-5": (2.0, 10.0, 0.10),
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
}
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--rounds", type=Path, required=True, help="회차 폴더들의 뿌리")
parser.add_argument("--projects", type=Path, required=True, help="전용 설정 폴더의 projects")
args = parser.parse_args()
ROOT: Path = args.rounds
CFG: Path = args.projects


def cost(path: Path) -> tuple[float, set[str]]:
    last: dict[str, tuple[str, dict]] = {}
    for n, line in enumerate(path.open(encoding="utf-8", errors="replace")):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        m = d.get("message") if isinstance(d, dict) else None
        if not isinstance(m, dict) or "usage" not in m or not m.get("model"):
            continue
        last[m.get("id") or f"line{n}"] = (m["model"], m["usage"])
    usd = 0.0
    models = set()
    for model, u in last.values():
        if model not in PRICES:
            models.add(model + "(단가 없음)")
            continue
        models.add(model)
        pi, po, pr = PRICES[model]
        cc = u.get("cache_creation") or {}
        w5 = cc.get("ephemeral_5m_input_tokens", 0) or 0
        w1 = cc.get("ephemeral_1h_input_tokens", 0) or 0
        if not cc:
            w5 = u.get("cache_creation_input_tokens", 0) or 0
        usd += (
            u.get("input_tokens", 0) * pi
            + u.get("output_tokens", 0) * po
            + u.get("cache_read_input_tokens", 0) * pr
            + w5 * pi * 1.25
            + w1 * pi * 2.0
        ) / 1e6
    return usd, models


total = 0.0
for rd in sorted(ROOT.iterdir()):
    ids = {x.strip() for x in (rd / "session-ids.txt").read_text().splitlines() if x.strip()}
    proj = CFG / ("C--Users-User-rerun-rounds-" + rd.name + "-clone")
    extra = [p for p in proj.glob("*.jsonl") if p.stem not in ids]
    usd = 0.0
    models: set[str] = set()
    for p in extra:
        u, m = cost(p)
        usd += u
        models |= m
    total += usd
    print(rd.name, "extra sessions", len(extra), f"official ~${usd:.4f}", sorted(models))
print(f"total ~${total:.4f}")
