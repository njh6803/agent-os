"""레벨 스윕의 모집단을 소급 측정 결과로 재고, 사전 등록 절이 고정된 판 그대로인지 보고, 스윕을
판정한다.

`population`은 소급 측정 프로브의 `branches.json`(`../session_cost/`)만 읽어, 스윕이 다룰 수 있는
브랜치가 작업 종류마다 얼마나 되는지 찍는다. 스윕은 지시문으로 연 세션의 모델 줄만 바꾸므로 그
브랜치만 갈래에 든다. 지시문으로 열렸다는 것은 그 브랜치의 첫 사람 트리거에 `다음 작업:`이 든
것이다(`collect.py`의 `directive_features`). 종류는 소급 측정 사전 등록의 브랜치
종류다(`branches.json`의 `kind`). 세는 것은 `state`가 `MERGED`이고 비용이 0보다 큰 브랜치다.

`prereg`는 README 사전 등록 절의 SHA-256이 `PREREG_SHA256`과 같은지 본다.

`judge`는 `collect.py --since <SWEEP_START>`가 쓴 스윕 기간의 `branches.json`을 읽어 README 사전
등록대로 종류마다 한 번 판정한다. 판정의 순수 함수와 그 순서(입력의 조건, 표지 모집단, 배정,
판정하지 않는 조건, 주된 판정과 되풀이)는 `tools/model_sweep_judge.py`에 있고 `tests/tools/`의
pytest가 고정한다. 이 파일은 그 앞뒤를 한다. 두 사전 등록 절(이 README와
`../session_cost/README.md`) 가운데 하나라도 해시가 다르거나 그 도구가 입력의 조건을 내면 갈래를
견주지 않고 1로 끝난다. 그렇지 않으면 소급 측정의 표지 넷을 `analyze.py`의 `markers`로 셈해 문턱을
넘은 표지의 이름을 도구에 넘기고, 종류마다 표와 판정을 찍는다.

`--today`는 판정 시점 전에 합성한 입력으로 판정 경로를 돌려 볼 때만 쓴다. 스윕 기록으로 판정 시점
전에 갈래를 견주지 않는다(사전 등록 "판정 시점과 되풀이"). 그래서 `--today`는 meta의 `synthetic`이
참인 입력에만 받고, 그런 입력은 실제 판정에 받지 않는다. `collect.py`는 그 칸을 쓰지 않는다.

판은 판정할 때 체크아웃에 있는 파일들(`collect.py`, `costs.py`, `analyze.py`, `sweep.py`,
`tools/model_sweep.py`, `tools/model_sweep_judge.py`)의 해시와, 입력을 쓴 `collect.py`가 meta에 남긴
자기 해시(`collect_sha256`)를 함께 찍는다. 둘이 다르면 입력을 쓴 뒤 모으는 코드가 바뀐 것이다.

못 보는 것: `branches.json`은 2026-10-12까지 병합된 브랜치라 그 뒤의 처리량은 보지
않는다(`population`). 주마다의 수는 병합 시각(UTC)의 ISO 주로 셈하고 첫 주와 마지막 주는 일부만
든다. 첫 사람 트리거가 지시문이 아닌 브랜치가 사람이 연 세션인지 지시문 없이 이어 간 세션인지는
가르지 않는다. PR이 없는 브랜치는 `branches.json`에 행이 없어 "병합만 빠진" 표지에 들지
않는다(meta의 `branches_without_pr`에 이름과 기록 수만 남는다). 판정이 못 보는 것은 그 도구의
독스트링이다.

종료 코드: `population`은 0, 입력이 없으면 2. `prereg`는 같으면 0, 다르거나 절이 없으면 1. `judge`는
판정(결론 없음 포함)을 찍었으면 0, 판정하지 않았으면 1, 입력이 없거나 `meta`·`branches`가 없으면 2.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, date, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SESSION_COST = HERE.parent / "session_cost"
sys.path.insert(0, str(SESSION_COST))
sys.path.insert(0, str(ROOT))
import analyze  # noqa: E402

from tools import model_sweep as tool  # noqa: E402
from tools import model_sweep_judge as sweep_judge  # noqa: E402

README = HERE / "README.md"
BRANCHES = SESSION_COST / "branches.json"
PREREG_SHA256 = "8a1c774f9c5ab85d8b4d2400191f91916703f2db469b4bba003bd2c72d3a1649"
RECORDED_BASE = sweep_judge.ARM_RECORD[tool.BASE]  # 기준 갈래의 기록 모델·레벨
KINDS = ["구현", "하네스", "명세", "티켓", "디자인", "문서", "수정"]
Z = 1.645 + 0.842
REDUCTIONS = (0.3, 0.4, 0.5)

type Row = sweep_judge.Row


def preregistration() -> tuple[bool, str]:
    current = tool.prereg_section(README.read_text(encoding="utf-8"))
    if not current:
        return False, "README에 사전 등록 절이 없다"
    digest = hashlib.sha256(current.encode("utf-8")).hexdigest()
    if digest != PREREG_SHA256:
        return False, f"사전 등록 절의 SHA-256 {digest} 이 고정한 값 {PREREG_SHA256} 과 다르다"
    return True, f"사전 등록 절은 고정한 판 그대로다(SHA-256 {digest[:12]}…)"


def prereg() -> int:
    intact, why = preregistration()
    print(why)
    return 0 if intact else 1


def n_k(sigma: float, reduction: float) -> int:
    """소급 측정 사전 등록 "스윕의 판정 기준"의 식. 감소율만 바꿔 넣을 수 있게 했다."""
    delta = math.log(1 / (1 - reduction))
    return math.ceil(2 * Z**2 * sigma**2 / delta**2)


def sigma(rows: list[Row]) -> float | None:
    costs = [r["cost"] for r in rows]
    logs = [math.log(c) for c in costs if isinstance(c, int | float) and c > 0]
    return statistics.stdev(logs) if len(logs) >= 3 else None


def at_base(row: Row) -> bool:
    share = row.get("top_share")
    return (
        row.get("top_model_effort") == RECORDED_BASE
        and isinstance(share, int | float)
        and share >= 0.9
    )


def iso_week(stamp: object) -> str:
    when = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    return when.strftime("%G-W%V")


def describe(name: str, rows: list[Row]) -> str:
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
    directive = sweep_judge.directive
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
            label = f"지시문으로 열린 것의 본 세션 최대 모델·레벨이 {RECORDED_BASE}"
            print(f"  {label}: {top[RECORDED_BASE]}/{len(led)}")
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
    for kind in tool.SWEPT:
        costs: dict[str, list[float]] = defaultdict(list)
        for b in merged:
            if b["kind"] == kind and directive(b) and at_base(b):
                costs[iso_week(b["merged"])].append(float(b["cost"]))
        cells = ", ".join(
            f"{week} ${statistics.median(v):.1f}({len(v)}개)" for week, v in sorted(costs.items())
        )
        print(f"- {kind}: {cells}")
    return 0


# --- 판정 -----------------------------------------------------------------------------------------


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def head_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
        )
    except OSError:
        return "알 수 없음"
    return out.stdout.strip() or "알 수 없음"


VERSIONED = [
    SESSION_COST / "collect.py",
    SESSION_COST / "costs.py",
    SESSION_COST / "analyze.py",
    HERE / "sweep.py",
    ROOT / "tools" / "model_sweep.py",
    ROOT / "tools" / "model_sweep_judge.py",
]


def input_blockers(
    meta: dict[str, analyze.Json],
    rows: list[Row],
    registered: dict[str, tuple[str, ...]],
    today: date | None,
) -> list[str]:
    """갈래를 견주기 전에 막는 조건. 두 사전 등록 절의 해시는 여기서, 나머지는 도구가 본다.
    `today`는 `--today`로 준 날짜다."""
    blockers = [why for intact, why in (preregistration(), analyze.preregistration()) if not intact]
    blockers += sweep_judge.input_problems(meta, today, datetime.now(UTC).date())
    return blockers + sweep_judge.kind_problems(rows, registered, tool.SWEPT)


def failed_markers(meta: dict[str, analyze.Json]) -> list[str]:
    """소급 측정의 표지 넷 가운데 판정을 막는 것의 이름. 막는지는 `analyze.markers`의 통과 여부(모든
    값이 문턱 이하)가 정하고, 이름은 표의 넷째 칸이 "넘는다"인 표지다. 값이 NaN이면 그 칸이
    "안"인데도 통과가 아니어서, 그때는 이름 대신 그 뜻을 넘긴다(셀프 리뷰 명세 축)."""
    marker_rows, markers_ok = analyze.markers(meta)
    if markers_ok:
        return []
    names = [row[0] for row in marker_rows if row[3] == "넘는다"]
    return names or ["문턱과 견줄 수 없는 값(NaN)이 있다"]


def print_header(path: Path, meta: dict[str, analyze.Json], today: date | None) -> None:
    print("# 레벨 스윕 판정")
    print()
    print(f"- {preregistration()[1]}")
    print(f"- 소급 측정: {analyze.preregistration()[1]}")
    versions = ", ".join(f"{f.name} {file_digest(f)}" for f in VERSIONED)
    print(f"- 판(SHA-256 앞 12자리): HEAD {head_commit()}, {versions}")
    written = str(meta.get("collect_sha256") or "없음")[:12]
    day = f"{today}(--today)" if today is not None else str(datetime.now(UTC).date())
    print(f"- 입력: {path}(since {meta.get('since')}, 쓴 collect.py {written}), 날짜 {day}")


def kind_lines(kind: str, result: sweep_judge.KindJudgment) -> list[str]:
    s = result.split
    head = ["갈래", "모집단", "n_k", "배정 모델·레벨이 최대인 몫", *sweep_judge.MARKS]
    table_rows = [
        [
            a,
            str(len(s.arms[a])),
            str(sweep_judge.N_K[kind]),
            f"{sweep_judge.top_share(s.arms[a], a):.2f}",
        ]
        + [str(s.marks[a][m]) for m in sweep_judge.MARKS]
        for a in tool.ARMS
    ]
    out = [f"## {kind}", "", analyze.table(head, table_rows), ""]
    out.append(f"- `브랜치:` 줄이 없어 배정하지 못한 표지 지시문: {s.no_branch}")
    out.extend(f"- {line}" for line in result.runs)
    if result.reasons:
        out.append("")
        out.extend(f"- 판정하지 않는 조건: {why}" for why in result.reasons)
    return out


def judge(path: Path, today: date | None) -> int:
    """`today`는 `--today`로 준 날짜다(합성 입력에만)."""
    if not path.exists():
        start = sweep_judge.SWEEP_START
        print(f"{path} 이 없다. collect.py --since {start} 를 먼저 돌린다", file=sys.stderr)
        return 2
    data = json.loads(path.read_text(encoding="utf-8"))
    meta, rows = data.get("meta"), data.get("branches")
    if not isinstance(meta, dict) or not isinstance(rows, list):
        print(f"{path} 에 meta 나 branches 가 없다", file=sys.stderr)
        return 2
    registered = tool.prereg_kinds(tool.prereg_section(README.read_text(encoding="utf-8")))
    blockers = input_blockers(meta, rows, registered, today)
    print_header(path, meta, today)
    if blockers:
        print()
        for b in blockers:
            print(f"- 판정하지 않는다: {b}")
        return 1
    marker_rows, _ = analyze.markers(meta)
    print()
    print("## 소급 측정의 표지 넷(스윕 기간)")
    print()
    print(analyze.table(["표지", "값", "문턱", "넘는가"], marker_rows))
    failed = failed_markers(meta)
    summary: list[str] = []
    for kind in registered:
        result = sweep_judge.judge_kind(kind, rows, failed, tool.SWEPT)
        print()
        print("\n".join(kind_lines(kind, result)))
        summary.append(f"- {kind}: **{result.verdict}**")
    print()
    print("## 판정")
    print()
    print("\n".join(summary))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    pop = sub.add_parser("population", help="스윕이 다룰 수 있는 브랜치를 종류마다 센다")
    pop.add_argument("--branches", type=Path, default=BRANCHES)
    sub.add_parser("prereg", help="사전 등록 절이 고정한 판 그대로인지 본다")
    jud = sub.add_parser("judge", help="스윕 기간의 branches.json 으로 종류마다 판정한다")
    jud.add_argument("--branches", type=Path, required=True)
    jud.add_argument("--today", type=date.fromisoformat, help="합성 입력으로 돌려 볼 때만 쓴다")
    args = parser.parse_args()
    if args.command == "population":
        return population(args.branches)
    if args.command == "judge":
        return judge(args.branches, args.today)
    return prereg()


if __name__ == "__main__":
    sys.exit(main())
