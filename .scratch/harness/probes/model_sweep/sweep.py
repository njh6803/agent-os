"""레벨 스윕의 모집단을 소급 측정 결과로 재고, 사전 등록 절이 고정된 판 그대로인지 본다.

`population`은 소급 측정 프로브의 `branches.json`(`../session_cost/`)만 읽어, 스윕이 다룰 수 있는
브랜치가 작업 종류마다 얼마나 되는지 찍는다. 스윕은 지시문으로 연 세션의 모델 줄만 바꾸므로 그
브랜치만 갈래에 든다. 지시문으로 열렸다는 것은 그 브랜치의 첫 사람 트리거에 `다음 작업:`이 든
것이다(`collect.py`의 `directive_features`). 종류는 소급 측정 사전 등록의 브랜치
종류다(`branches.json`의 `kind`).

`prereg`는 README 사전 등록 절의 SHA-256이 `PREREG_SHA256`과 같은지 본다. 스윕의 판정 스크립트는
아직 없고, 판정할 때 이 파일에 더한다. 그때도 이 값과 대 보고, 다르면 판정하지 않는다.

세는 것은 `state`가 `MERGED`이고 비용이 0보다 큰 브랜치다. 열린 PR의 브랜치와 비용이 0인 병합
브랜치(귀속된 응답이 없는 것)는 빠진다.

못 보는 것: `branches.json`은 2026-10-12까지 병합된 브랜치라 그 뒤의 처리량은 보지 않는다. 주마다의
수는 병합 시각(UTC)의 ISO 주로 셈하고 첫 주와 마지막 주는 일부만 든다. 첫 사람 트리거가 지시문이
아닌 브랜치가 사람이 연 세션인지 지시문 없이 이어 간 세션인지는 가르지 않는다.

종료 코드: `population`은 0, 입력이 없으면 2. `prereg`는 같으면 0, 다르거나 절이 없으면 1.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
README = HERE / "README.md"
BRANCHES = HERE.parent / "session_cost" / "branches.json"
START, END = "<!-- 사전 등록 시작 -->", "<!-- 사전 등록 끝 -->"
PREREG_SHA256 = "8a1c774f9c5ab85d8b4d2400191f91916703f2db469b4bba003bd2c72d3a1649"
BASE = "claude-opus-5-5/xhigh"
KINDS = ["구현", "하네스", "명세", "티켓", "디자인", "문서", "수정"]
SWEPT = ["구현", "하네스"]
Z = 1.645 + 0.842
REDUCTIONS = (0.3, 0.4, 0.5)


def section(text: str) -> str:
    if START not in text or END not in text:
        return ""
    return text.split(START, 1)[1].split(END, 1)[0]


def prereg() -> int:
    current = section(README.read_text(encoding="utf-8"))
    if not current:
        print("README에 사전 등록 절이 없다")
        return 1
    digest = hashlib.sha256(current.encode("utf-8")).hexdigest()
    if digest != PREREG_SHA256:
        print(f"사전 등록 절의 SHA-256 {digest} 이 고정한 값 {PREREG_SHA256} 과 다르다")
        return 1
    print(f"사전 등록 절은 고정한 판 그대로다(SHA-256 {digest[:12]}…)")
    return 0


def n_k(sigma: float, reduction: float) -> int:
    """소급 측정 사전 등록 "스윕의 판정 기준"의 식. 감소율만 바꿔 넣을 수 있게 했다."""
    delta = math.log(1 / (1 - reduction))
    return math.ceil(2 * Z**2 * sigma**2 / delta**2)


def sigma(rows: list[dict[str, object]]) -> float | None:
    costs = [r["cost"] for r in rows]
    logs = [math.log(c) for c in costs if isinstance(c, int | float) and c > 0]
    return statistics.stdev(logs) if len(logs) >= 3 else None


def directive(row: dict[str, object]) -> bool:
    feats = row.get("directive_features")
    return isinstance(feats, dict) and bool(feats.get("directive"))


def at_base(row: dict[str, object]) -> bool:
    share = row.get("top_share")
    return row.get("top_model_effort") == BASE and isinstance(share, int | float) and share >= 0.9


def iso_week(stamp: object) -> str:
    when = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    return when.strftime("%G-W%V")


def describe(name: str, rows: list[dict[str, object]]) -> str:
    s = sigma(rows)
    if s is None:
        return f"{name} {len(rows)}개, σ 셀 수 없음"
    needs = ", ".join(f"{int(r * 100)}% {n_k(s, r)}" for r in REDUCTIONS)
    return f"{name} {len(rows)}개, σ {s:.2f}, n_k({needs})"


def population(path: Path) -> int:
    if not path.exists():
        print(f"{path} 이 없다. 소급 측정 프로브의 collect.py 를 먼저 돌린다", file=sys.stderr)
        return 2
    data = json.loads(path.read_text(encoding="utf-8"))
    merged = [b for b in data["branches"] if b["state"] == "MERGED" and b["cost"] > 0]
    print(f"병합되고 비용이 있는 브랜치 {len(merged)}개(branches.json, {path.name})")
    print()
    print("종류마다 무리의 σ(로그 비용)와 한 갈래의 n_k(감소율별)")
    for kind in KINDS:
        rows = [b for b in merged if b["kind"] == kind]
        if not rows:
            continue
        led = [b for b in rows if directive(b)]
        led_base = [b for b in led if at_base(b)]
        rows_base = [b for b in rows if at_base(b)]
        print(f"- {kind}: 병합 {len(rows)}개, 지시문으로 열림 {len(led)}개")
        print(f"  {describe('지시문으로 열림 · opus-5-5 xhigh 90% 이상', led_base)}")
        print(f"  {describe('opus-5-5 xhigh 90% 이상(소급 측정 결과 절의 무리)', rows_base)}")
        print(f"  {describe('지시문으로 열림 전부', led)}")
        print(f"  {describe('병합 전부', rows)}")
        if led:
            top = Counter(str(b["top_model_effort"]) for b in led)
            same = top[BASE]
            print(f"  지시문으로 열린 것의 본 세션 최대 모델·레벨이 {BASE}: {same}/{len(led)}")
            queued = sum(int(b.get("queued_human") or 0) for b in led)
            print(f"  지시문으로 열린 것의 턴 도중 사람 메시지(queued_human) 합 {queued}")
    print()
    print("주마다 지시문으로 열린 병합 브랜치(병합 시각의 ISO 주, 첫 주와 마지막 주는 일부)")
    weeks: dict[str, Counter[str]] = defaultdict(Counter)
    for b in merged:
        if directive(b):
            weeks[iso_week(b["merged"])][str(b["kind"])] += 1
    for week in sorted(weeks):
        counts = ", ".join(f"{k} {weeks[week][k]}" for k in KINDS if weeks[week][k])
        print(f"- {week}: {counts}")
    print()
    print("주마다 비용 중앙값(지시문으로 열림 · opus-5-5 xhigh 90% 이상, 병합 시각의 ISO 주)")
    for kind in SWEPT:
        costs: dict[str, list[float]] = defaultdict(list)
        for b in merged:
            if b["kind"] == kind and directive(b) and at_base(b):
                costs[iso_week(b["merged"])].append(float(b["cost"]))
        cells = ", ".join(
            f"{week} ${statistics.median(v):.1f}({len(v)}개)" for week, v in sorted(costs.items())
        )
        print(f"- {kind}: {cells}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    pop = sub.add_parser("population", help="스윕이 다룰 수 있는 브랜치를 종류마다 센다")
    pop.add_argument("--branches", type=Path, default=BRANCHES)
    sub.add_parser("prereg", help="사전 등록 절이 고정한 판 그대로인지 본다")
    args = parser.parse_args()
    if args.command == "population":
        return population(args.branches)
    return prereg()


if __name__ == "__main__":
    sys.exit(main())
