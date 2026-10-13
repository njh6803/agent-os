"""캐시 읽기 단가가 Claude Code의 셈과 맞는지 모델마다 가른다.

`costs.py`의 캐시 읽기 단가는 claude-api 스킬 번들의 배수를 옮긴 것이다. 공식 가격표
(`platform.claude.com/docs/en/about-claude/pricing.md`)는 모델마다 배수가 달라(입력 단가의
0.025배, 0.05배, 0.1배) 둘이 어긋날 수 있다. 이 프로브는 세션마다 Claude Code가 남긴 `cost-state`
기록의 모델별 토큰으로, 배수 후보 셋 가운데 어느 것이 그 기록의 `costUSD`와 맞는지 센다. 맞는다는
것은 캐시 쓰기를 모두 5분(입력의 1.25배)으로 본 값과 모두 1시간(2배)으로 본 값 사이에 `costUSD`
(±1%)가 드는 것이다(`costs.cost_state_bounds`, `collect.py`의 `price_check`와 같은 판정). 웹 검색
요금(건당 $0.01, 같은 가격표)은 `costUSD`에서 뺀다.

갈래: 후보마다 두 끝 안에 드는 쌍의 수. 쌍의 95% 이상을 담는 후보가 하나뿐이면 Claude Code가 그
배수로 셈했다고 판정한다. 캐시 읽기가 금액의 작은 몫인 쌍은 어느 후보로도 들어 가르지 못하므로, 표의
단가로 셈한 캐시 읽기가 `costUSD`에서 차지하는 몫의 중앙값을 함께 찍는다. 그런 쌍이 많아 둘 이상의
후보가 95%를 넘으면 그 모델은 "가르지 못함"이다.

쌍이 `MIN_PAIRS`보다 적은 모델은 "쌍이 적다"로 찍고 판정하지 않는다. 프롬프트 길이로 단가가 갈리는
모델(`LENGTH_PRICED`)도 판정하지 않는다. `cost-state`는 세션의 합이라 요청마다 어느 단가
구간이었는지 가를 수 없고, 표는 짧은 프롬프트의 단가만 들어 긴 요청이 섞이면 맞는 배수도 "맞는 배수
없음"이 된다. 후보는 세 배수뿐이라, 표의 배수가 그 밖인 모델이 생기면 늘 "맞는 배수 없음"이다.
그때는 후보를 더한다.

종료 코드: 0은 판정한 모델이 하나 이상이고 그 판정이 모두 표의 배수와 같다. 1은 판정이 표와
다르거나, 맞는 배수가 없거나, 가르지 못한 모델이 있다(그 모델은 측정이 아니다). 2는 트랜스크립트
폴더가 없거나, 단가표의 모델이 든 `cost-state` 쌍이 하나도 없거나, 판정한 모델이 하나도 없다.

못 보는 것: `cost-state`는 Claude Code의 셈이지 청구서가 아니다. 그래서 이 대조는 단가표가 Claude
Code와 같은지를 볼 뿐, 실제로 청구된 금액과 같은지는 보지 않는다. 다시 시작한 세션은 뒤 프로세스의
몫만 든다(`collect.py`와 같다). 시간 창이 없다. `cost-state`에는 쓴 시각이 없어(`startTime`만 있다)
그때의 트랜스크립트 전부를 읽고, 기록이 쌓이면 쌍의 수가 바뀐다. 다시 내는 것은 어느 배수가 맞는지의
판정이다. 세션마다 마지막 `cost-state`를 고르는 규칙은 `collect.py`의 `_scan_record`와 같지만, 그
스캔은 트랜스크립트 전체를 브랜치로 묶는 일과 얽혀 있어 `cost-state` 줄만 따로 읽는다.

사용: `PYTHONUTF8=1 uv run python .scratch/harness/probes/session_cost/cache_read_fit.py`(워크트리
루트에서, 트랜스크립트는 `~/.claude/projects/`). 읽는 폴더는 이름이 `C--project-agent`로 시작하는
것이고, 이 PC의 저장소 경로 `C:/project/agent`를 Claude Code가 폴더 이름으로 바꾼
것이다(`collect.py`의 `PROJECT_PREFIX`와 같다). 저장소가 다른 경로나 다른 PC에 있으면 `PREFIX`를
고친다. 그대로 두면 쌍을 하나도 찾지 못해 2로 끝난다. 2026-10-13 결과는 같은 폴더 README의 결과
절이다.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

from costs import PRICES, Json, base_model, cost_state_bounds

PROJECTS = Path.home() / ".claude" / "projects"
PREFIX = "C--project-agent"
MULTIPLIERS = (0.025, 0.05, 0.1)
WEB_SEARCH_USD = 0.01
FIT_SHARE = 0.95
MIN_PAIRS = 5
LENGTH_PRICED = frozenset({"claude-haiku-5-5"})


def _num(v: Json) -> float:
    return float(v) if isinstance(v, int | float) and not isinstance(v, bool) else 0.0


def latest_cost_states(root: Path) -> list[dict[str, Json]]:
    """세션마다 `totalCostUSD`가 가장 큰 `cost-state` 기록. 프로세스가 끝날 때 쓰여 뒤의 것이
    크다."""
    best: dict[str, dict[str, Json]] = {}
    for d in sorted(root.iterdir()):
        if not d.is_dir() or not d.name.startswith(PREFIX):
            continue
        for f in sorted(d.rglob("*.jsonl")):
            with f.open(encoding="utf-8") as fh:
                for line in fh:
                    if '"cost-state"' not in line:
                        continue
                    try:
                        o = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(o, dict) or o.get("type") != "cost-state":
                        continue
                    sid = o.get("sessionId")
                    total = o.get("totalCostUSD")
                    if not isinstance(sid, str) or not isinstance(total, int | float):
                        continue
                    prev = best.get(sid)
                    if prev is None or float(total) >= _num(prev.get("totalCostUSD")):
                        best[sid] = o
    return list(best.values())


def fits(model: str, mu: dict[str, Json], cache_read: float) -> bool:
    bounds = cost_state_bounds(model, mu, cache_read)
    if bounds is None:
        return False
    lo, hi = bounds
    usd = _num(mu.get("costUSD")) - _num(mu.get("webSearchRequests")) * WEB_SEARCH_USD
    return lo * 0.99 - 1e-6 <= usd <= hi * 1.01 + 1e-6


def verdict(n: int, counts: list[int]) -> float | str:
    """쌍의 `FIT_SHARE` 이상을 담는 배수가 하나뿐이면 그 배수, 아니면 까닭."""
    fitted = [m for m, c in zip(MULTIPLIERS, counts, strict=True) if c >= FIT_SHARE * n]
    if len(fitted) == 1:
        return fitted[0]
    return "맞는 배수 없음" if not fitted else "가르지 못함"


def main() -> int:
    if not PROJECTS.is_dir():
        print(f"트랜스크립트 폴더가 없다: {PROJECTS}")
        return 2
    states = latest_cost_states(PROJECTS)
    by_model: dict[str, list[dict[str, Json]]] = {}
    for o in states:
        mu_all = o.get("modelUsage")
        for name, mu in mu_all.items() if isinstance(mu_all, dict) else []:
            key = base_model(name)
            if key in PRICES and isinstance(mu, dict) and _num(mu.get("costUSD")) >= 0.01:
                by_model.setdefault(key, []).append(mu)
    print(f"세션 {len(states)}개의 cost-state")
    if not by_model:
        print("단가표의 모델이 든 cost-state 쌍이 없다. 트랜스크립트 자리를 본다")
        return 2
    print()
    heads = " | ".join(f"{m}배 안" for m in MULTIPLIERS)
    print(f"| 모델 | 쌍 | 표의 배수 | {heads} | 캐시 읽기 몫 중앙값 | 판정 |")
    print("|---|---|---|" + "---|" * len(MULTIPLIERS) + "---|---|")
    code = 0
    judged = 0
    for model, p in PRICES.items():
        pairs = by_model.get(model, [])
        if not pairs:
            continue
        counts = [sum(1 for mu in pairs if fits(model, mu, p.input * m)) for m in MULTIPLIERS]
        shares = [
            _num(mu.get("cacheReadInputTokens")) * p.cache_read / 1e6 / _num(mu.get("costUSD"))
            for mu in pairs
        ]
        table = round(p.cache_read / p.input, 3)
        if model in LENGTH_PRICED:
            mark = "프롬프트 길이로 단가가 갈려 판정하지 않는다"
        elif len(pairs) < MIN_PAIRS:
            mark = f"쌍이 적다({MIN_PAIRS}보다 적어 판정하지 않는다)"
        else:
            judged += 1
            v = verdict(len(pairs), counts)
            if v == table:
                mark = "표와 같다"
            else:
                code = 1
                mark = f"{v}배, 표와 다르다" if isinstance(v, float) else v
        print(
            f"| {model} | {len(pairs)} | {table} | "
            + " | ".join(str(c) for c in counts)
            + f" | {statistics.median(shares):.3f} | {mark} |"
        )
    if judged == 0:
        print("판정한 모델이 없다. 측정이 아니다")
        return 2
    return code


if __name__ == "__main__":
    sys.exit(main())
