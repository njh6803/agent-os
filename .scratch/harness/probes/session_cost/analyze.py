"""`branches.json`을 읽어 측정 표지, 양성 대조, 기준선, 사전 등록한 가설의 판정, 탐색 표를 찍는다.

판정의 문턱과 모집단은 README의 사전 등록 절이 원천이다. 이 파일은 그 절의 SHA-256이
`PREREG_SHA256`(절이 처음 들어간 커밋 `bd3cdd5`의 판)과 같은지 먼저 본다. squash 병합 뒤의
main에서는 "처음 커밋된 판"이 병합 커밋이 되므로 git 이력이 아니라 이 값으로 고정한다. 다르면 가설을
판정하지 않고 탐색으로만 찍는다. 판정하지 않는 조건에 걸려도 같다.

부트스트랩은 표준 라이브러리 `random.Random(0)`으로 2,000번 다시 뽑고, 90% 구간은 정렬한 값의
5번째와 95번째 백분위 (가까운 순위)다. 다시 뽑은 표본의 순위가 모두 같아 ρ를 셀 수 없는 회차는 빼고
그 수를 찍는다.

종료 코드: 0 사전 등록이 그대로이고 판정하지 않는 조건이 없다(가설이 서지 않은 것도 0이다), 1 사전
등록이 바뀌었거나 판정하지 않는 조건에 걸렸다, 2 입력이 없다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from costs import Json

HERE = Path(__file__).resolve().parent
README = HERE / "README.md"
START, END = "<!-- 사전 등록 시작 -->", "<!-- 사전 등록 끝 -->"
PREREG_COMMIT = "bd3cdd5"
PREREG_SHA256 = "027b80d2cab0dc1a5bebfa323c02b4af74bee27af4c63727f9c16d48b6a1cb62"
SEED, RESAMPLES = 0, 2000
MIN_SAMPLE, MIN_GROUP = 20, 5
DELTA = math.log(1 / 0.7)
Z = 1.645 + 0.842
PRICE_OUTSIDE_LIMIT = 0.05
OUTCOMES = ["cost", "turn_min", "interventions", "rework"]

type Row = dict[str, Json]


def section(text: str) -> str:
    if START not in text or END not in text:
        return ""
    return text.split(START, 1)[1].split(END, 1)[0]


def preregistration() -> tuple[bool, str]:
    current = section(README.read_text(encoding="utf-8"))
    if not current:
        return False, "README에 사전 등록 절이 없다"
    digest = hashlib.sha256(current.encode("utf-8")).hexdigest()
    if digest != PREREG_SHA256:
        return False, f"사전 등록 절의 SHA-256({digest[:12]}…)이 {PREREG_COMMIT}의 판과 다르다"
    return True, f"사전 등록 절은 {PREREG_COMMIT}의 판 그대로다(SHA-256 {digest[:12]}…)"


# --- 통계 -----------------------------------------------------------------------------------------


def ranks(v: Sequence[float]) -> list[float]:
    """같은 값은 평균 순위."""
    order = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
            j += 1
        for k in range(i, j + 1):
            r[order[k]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x: Sequence[float], y: Sequence[float]) -> float | None:
    if len(x) < 3:
        return None
    rx, ry = ranks(x), ranks(y)
    mx, my = statistics.fmean(rx), statistics.fmean(ry)
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry, strict=True))
    sx = math.sqrt(sum((a - mx) ** 2 for a in rx))
    sy = math.sqrt(sum((b - my) ** 2 for b in ry))
    return sxy / (sx * sy) if sx and sy else None


def percentile_ci(values: list[float]) -> tuple[float, float]:
    s = sorted(values)
    return s[int(0.05 * (len(s) - 1))], s[int(0.95 * (len(s) - 1))]


def boot_rho(x: list[float], y: list[float]) -> tuple[tuple[float, float] | None, int]:
    """대상을 다시 뽑은 ρ의 90% 구간과, ρ를 셀 수 없어 뺀 회차의 수."""
    rng = random.Random(SEED)
    got: list[float] = []
    skipped = 0
    n = len(x)
    for _ in range(RESAMPLES):
        idx = [rng.randrange(n) for _ in range(n)]
        r = spearman([x[i] for i in idx], [y[i] for i in idx])
        if r is None:
            skipped += 1
        else:
            got.append(r)
    return (percentile_ci(got) if got else None), skipped


def boot_median_ratio(a: list[float], b: list[float]) -> tuple[float, float] | None:
    rng = random.Random(SEED)
    got: list[float] = []
    for _ in range(RESAMPLES):
        ma = statistics.median(rng.choice(a) for _ in a)
        mb = statistics.median(rng.choice(b) for _ in b)
        if mb > 0:
            got.append(ma / mb)
    return percentile_ci(got) if got else None


def num(r: Row, key: str) -> float:
    v = r.get(key)
    return float(v) if isinstance(v, int | float) and not isinstance(v, bool) else 0.0


def feat(r: Row, group: str, key: str) -> float | None:
    f = r.get(group)
    if not isinstance(f, dict):
        return None
    v = f.get(key)
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    return float(v) if isinstance(v, int | float) else None


def quartiles(v: list[float]) -> tuple[float, float, float]:
    if len(v) < 2:
        m = v[0] if v else float("nan")
        return m, m, m
    qs = statistics.quantiles(v, n=4, method="inclusive")
    return qs[0], statistics.median(v), qs[2]


def pairs_of(pop: list[Row], group: str, key: str, outcome: str) -> tuple[list[float], list[float]]:
    xs: list[float] = []
    ys: list[float] = []
    for r in pop:
        x = feat(r, group, key)
        if x is not None:
            xs.append(x)
            ys.append(num(r, outcome))
    return xs, ys


# --- 표 -------------------------------------------------------------------------------------------


def table(head: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(out)


def f2(x: float | None) -> str:
    return "-" if x is None or math.isnan(x) else f"{x:.2f}"


def ci_text(ci: tuple[float, float] | None) -> str:
    return f"[{ci[0]:.2f}, {ci[1]:.2f}]" if ci else "-"


def val(meta: dict[str, Json], *path: str) -> float:
    cur: Json = meta
    for p in path:
        cur = cur.get(p) if isinstance(cur, dict) else None
    return float(cur) if isinstance(cur, int | float) and not isinstance(cur, bool) else 0.0


def markers(meta: dict[str, Json]) -> tuple[list[list[str]], bool]:
    """사전 등록의 판정하지 않는 조건 가운데 표본 수 밖의 넷."""
    responses = val(meta, "responses_in_repo")
    in_repo = val(meta, "cost_in_repo")
    missing = meta.get("merged_prs_without_responses")
    window = val(meta, "merged_prs_in_window")
    pairs = val(meta, "price_check", "pairs")
    checks = [
        (
            "usage 없는 응답의 몫",
            val(meta, "responses_without_usage") / responses if responses else 1.0,
            0.01,
        ),
        (
            "귀속되지 않은 비용의 몫",
            val(meta, "cost_unattributed") / in_repo if in_repo else 1.0,
            0.2,
        ),
        (
            "귀속된 응답이 없는 병합 PR의 몫",
            (len(missing) if isinstance(missing, list) else 0) / window if window else 1.0,
            0.2,
        ),
        (
            "단가 대조에서 두 끝 밖인 쌍의 몫",
            val(meta, "price_check", "outside_count") / pairs if pairs else 1.0,
            PRICE_OUTSIDE_LIMIT,
        ),
    ]
    rows = [[name, f"{v:.3f}", f"{lim}", "넘는다" if v > lim else "안"] for name, v, lim in checks]
    return rows, all(v <= lim for _, v, lim in checks)


def baselines(pop: list[Row], title: str) -> str:
    counts = Counter(str(r["kind"]) for r in pop)
    rows: list[list[str]] = []
    for k, n in counts.most_common():
        g = [r for r in pop if r["kind"] == k]
        cost = [num(r, "cost") for r in g]
        logs = [math.log(c) for c in cost if c > 0]
        sigma = statistics.stdev(logs) if len(logs) >= 3 else None
        n_k = math.ceil(2 * Z**2 * sigma**2 / DELTA**2) if sigma else None
        mean = statistics.fmean(cost)
        cv = statistics.stdev(cost) / mean if len(cost) >= 2 and mean else None
        q1, med, q3 = quartiles(cost)
        post = [num(r, "cost_post_pr") / num(r, "cost") for r in g if num(r, "cost") > 0]
        sub = [num(r, "cost_sub") / num(r, "cost") for r in g if num(r, "cost") > 0]
        think = [num(r, "thinking_share") for r in g if r.get("thinking_share") is not None]
        rows.append(
            [
                k,
                str(n),
                f"{med:.1f}",
                f"{q1:.1f}~{q3:.1f}",
                f2(cv),
                f2(sigma),
                str(n_k) if n_k else "-",
                f"{statistics.median(num(r, 'turn_min') for r in g):.0f}",
                f"{statistics.median(num(r, 'model_min') for r in g):.0f}",
                f"{statistics.median(num(r, 'tool_min') for r in g):.0f}",
                f"{statistics.median(num(r, 'turns') for r in g):.0f}",
                f"{statistics.median(num(r, 'interventions') for r in g):.0f}",
                f"{statistics.median(num(r, 'rework') for r in g):.0f}",
                f2(statistics.median(post)) if post else "-",
                f2(statistics.median(sub)) if sub else "-",
                f2(statistics.median(think)) if think else "-",
            ]
        )
    head = ["종류", "n", "비용 중앙값($)", "사분위($)", "CV", "σ(로그)", "n_k", "턴 시간(분)"]
    head += ["모델 시간(분)", "도구 시간(분)", "턴 수", "개입", "재작업", "PR 뒤 몫"]
    head += ["서브에이전트 몫", "생각 몫"]
    return f"### {title}\n\n" + table(head, rows)


def population(rows: list[Row]) -> list[Row]:
    """사전 등록의 모집단: main에 병합된 PR의 브랜치 가운데 귀속된 응답이 하나 이상인 것."""
    return [
        r
        for r in rows
        if r.get("merged")
        and r.get("base_ref") == "main"
        and (num(r, "msgs_main") + num(r, "msgs_sub")) > 0
    ]


def feature_population(rows: list[Row]) -> list[Row]:
    """가설 1·2의 모집단: 위 모집단의 구현 브랜치 가운데 merge-base 판본의 티켓을 찾은 것."""
    return [
        r
        for r in population(rows)
        if r["kind"] == "구현" and isinstance(r.get("ticket_features"), dict)
    ]


NO_JUDGMENT = "결론 없음"


def verdict_rho(xs: list[float], ys: list[float], judge: bool) -> tuple[str, float | None, str]:
    rho = spearman(xs, ys)
    ci, skipped = boot_rho(xs, ys) if len(xs) >= 3 else (None, 0)
    if not judge:
        v = f"{NO_JUDGMENT}(사전 등록 또는 판정하지 않는 조건)"
    elif len(xs) < MIN_SAMPLE:
        v = f"{NO_JUDGMENT}(표본 {len(xs)} < {MIN_SAMPLE})"
    elif rho is not None and ci is not None and rho >= 0.3 and ci[0] > 0:
        v = "선다"
    else:
        v = "서지 않는다"
    return v, rho, f"{ci_text(ci)}(뺀 회차 {skipped})"


def hypothesis_1(pop: list[Row], judge: bool) -> list[list[str]]:
    rows: list[list[str]] = []
    for outcome, label in (("cost", "합"), ("cost_main", "본 세션만")):
        xs, ys = pairs_of(pop, "ticket_features", "open_decisions", outcome)
        v, rho, ci = verdict_rho(xs, ys, judge)
        late = [r for r in pop if not r.get("early")]
        lx, ly = pairs_of(late, "ticket_features", "open_decisions", outcome)
        late_rho = spearman(lx, ly)
        if v == "선다" and (late_rho is None or late_rho < 0.2):
            v = "시기와 섞여 선다"
        rows.append([label, v, str(len(xs)), f2(rho), ci, f"{f2(late_rho)} (n={len(lx)})"])
    return rows


def hypothesis_2(pop: list[Row], judge: bool) -> list[list[str]]:
    rows: list[list[str]] = []
    for outcome, label in (("cost", "합"), ("cost_main", "본 세션만")):
        contact = [num(r, outcome) for r in pop if feat(r, "ticket_features", "contract") == 1.0]
        other = [num(r, outcome) for r in pop if feat(r, "ticket_features", "contract") == 0.0]
        m_c = statistics.median(contact) if contact else None
        m_o = statistics.median(other) if other else None
        ratio = m_c / m_o if m_c is not None and m_o else None
        ci = boot_median_ratio(contact, other) if contact and other else None
        if not judge:
            v = f"{NO_JUDGMENT}(사전 등록 또는 판정하지 않는 조건)"
        elif len(contact) + len(other) < MIN_SAMPLE or min(len(contact), len(other)) < MIN_GROUP:
            v = f"{NO_JUDGMENT}(표본 {len(contact)}/{len(other)})"
        elif ratio is not None and ci is not None and ratio >= 1.5 and ci[0] > 1:
            v = "선다"
        else:
            v = "서지 않는다"
        rows.append(
            [
                label,
                v,
                f"{len(contact)} / {len(other)}",
                f"{f2(m_c)} / {f2(m_o)}",
                f2(ratio),
                ci_text(ci),
            ]
        )
    return rows


def combine(rows: list[list[str]]) -> str:
    """합으로 선 판정이 본 세션 비용으로 서지 않으면 그렇게 붙인다(사전 등록 "모집단과 결과
    변수")."""
    total, main = rows[0][1], rows[1][1]
    if total.endswith("선다") and not main.endswith("선다"):
        return f"{total}. 서브에이전트 셈에 따라 갈린다"
    return total


def explore(pop: list[Row], group: str, keys: list[str]) -> str:
    rows: list[list[str]] = []
    for k in keys:
        cells = [k]
        for o in OUTCOMES:
            xs, ys = pairs_of(pop, group, k, o)
            cells.append(f"{f2(spearman(xs, ys))} (n={len(xs)})")
        rows.append(cells)
    return table(["지표", *[f"ρ: {o}" for o in OUTCOMES]], rows)


TICKET_KEYS = ["criteria", "cmd_share", "open_decisions", "chars", "contract", "layers", "files"]
TICKET_KEYS += ["blocked_by", "adr_refs", "title_open", "first_ticket"]
DIRECTIVE_KEYS = ["chars", "directive", "contract", "layers", "files", "adr_refs", "read_refs"]
DIRECTIVE_KEYS += ["carry_chars"]


def report(meta: dict[str, Json], rows: list[Row]) -> tuple[str, bool]:
    intact, why = preregistration()
    marker_rows, markers_ok = markers(meta)
    judge = intact and markers_ok
    pop = population(rows)
    feature_pop = feature_population(rows)
    homogeneous = [
        r
        for r in pop
        if r.get("top_model_effort") == "claude-opus-5-5/xhigh" and num(r, "top_share") >= 0.9
    ]
    out: list[str] = ["## 사전 등록", "", f"- {why}", "", "## 측정 표지", ""]
    out.append(table(["표지", "값", "문턱", "넘는가"], marker_rows))
    out.append("")
    out.append(
        f"- 서브에이전트 응답 {val(meta, 'sub_responses'):.0f} 가운데 최종 usage가 없는 것 "
        f"{val(meta, 'sub_partial'):.0f}, 그 비용 ${val(meta, 'cost_sub_partial'):.0f} "
        f"(이 저장소 비용 ${val(meta, 'cost_in_repo'):.0f})"
    )
    out.append(f"- 저장소 밖 기록의 비용 ${val(meta, 'cost_outside_repo'):.0f}")
    no_pr = json.dumps(meta.get("branches_without_pr"), ensure_ascii=False)
    out.append(f"- PR을 찾지 못한 브랜치 이름: {no_pr}")
    out.append(
        f"- 단가표에 없는 모델의 응답: {json.dumps(meta.get('unknown_models'), ensure_ascii=False)}"
    )
    out += ["", "## 양성 대조", ""]
    out.append(
        f"- 단가: `cost-state` 금액이 두 끝 밖인 쌍 {val(meta, 'price_check', 'outside_count'):.0f}"
        f" / {val(meta, 'price_check', 'pairs'):.0f}"
    )
    pc = meta.get("price_check")
    positions = pc.get("positions") if isinstance(pc, dict) else None
    for m, v in positions.items() if isinstance(positions, dict) else []:
        out.append(f"  - {m} 두 끝 사이의 자리(0=모두 5분, 1=모두 1시간): {json.dumps(v)}")
    out.append(f"- 기록 기반 비용 / `cost-state` 금액: {json.dumps(meta.get('cost_state_ratio'))}")
    out.append(
        f"- 턴 시간(Claude Code 대 이 프로브, 초): {json.dumps(meta.get('turn_duration_control'))}"
    )
    out += ["", "## 가설 (사전 등록)", ""]
    h1 = hypothesis_1(feature_pop, judge)
    out.append(f"가설 1: **{combine(h1)}**")
    out.append("")
    out.append(table(["비용", "판정", "n", "ρ", "90% 구간", "이른 시기 뺀 ρ"], h1))
    out.append("")
    dist = Counter(
        int(x) for x in pairs_of(feature_pop, "ticket_features", "open_decisions", "cost")[0]
    )
    out.append(f"열린 결정 수의 분포: {sorted(dist.items())}")
    out.append("")
    h2 = hypothesis_2(feature_pop, judge)
    out.append(f"가설 2: **{combine(h2)}**")
    out.append("")
    out.append(table(["비용", "판정", "n(접촉/비접촉)", "중앙값($)", "비", "90% 구간"], h2))
    out += ["", "## 기준선 (탐색)", ""]
    out.append(baselines(pop, f"병합된 브랜치 전부 (n={len(pop)})"))
    out.append("")
    out.append(
        baselines(
            homogeneous, f"본 세션 비용의 90% 이상이 opus-5-5/xhigh인 것 (n={len(homogeneous)})"
        )
    )
    out += ["", "## 모델·레벨 분포 (탐색)", ""]
    dist2 = Counter(str(r.get("top_model_effort")) for r in pop)
    out.append(
        table(
            ["본 세션 비용이 가장 큰 모델/레벨", "브랜치"],
            [[k, str(v)] for k, v in dist2.most_common()],
        )
    )
    out += ["", "## 사전 지표 (탐색)", "", f"feature 티켓 (n={len(feature_pop)})", ""]
    out.append(explore(feature_pop, "ticket_features", TICKET_KEYS))
    others = [r for r in pop if r["kind"] != "구현"]
    out += ["", f"feature 밖의 브랜치, 첫 사람 메시지 (n={len(others)})", ""]
    out.append(explore(others, "directive_features", DIRECTIVE_KEYS))
    out += ["", "## 재작업과 지연된 실패 (탐색)", ""]
    keys = ["commits_after_pr", "ci_failures", "followup_mentions", "retro_rows", "reverts"]
    keys += ["diagnosing_bugs", "tool_errors", "hook_blocks", "ask_user", "interrupts"]
    out.append(table(["합", "값"], [[k, f"{sum(num(r, k) for r in pop):.0f}"] for k in keys]))
    turn = sum(num(r, "turn_min") for r in pop)
    tail = sum(num(r, "trailing_min") for r in pop)
    out.append("")
    out.append(
        f"- 턴 끝의 `system` 기록 꼬리(턴 시간에 든다): {tail:.0f}분 / 턴 시간 합 {turn:.0f}분, "
        f"꼬리가 있는 브랜치 {sum(1 for r in pop if num(r, 'trailing_min') >= 1)}개(1분 이상)"
    )
    early = [num(r, "cost") for r in pop if r.get("early")]
    late = [num(r, "cost") for r in pop if not r.get("early")]
    out.append("")
    out.append(
        f"- 이른 시기 {len(early)}개의 비용 중앙값 "
        f"{f2(statistics.median(early) if early else None)}, 그 뒤 {len(late)}개 "
        f"{f2(statistics.median(late) if late else None)}"
    )
    return "\n".join(out), judge


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--data", type=Path, default=HERE / "branches.json")
    args = p.parse_args()
    if not args.data.exists():
        print(f"analyze: {args.data} 가 없다. collect.py 를 먼저 돌린다", file=sys.stderr)
        return 2
    data = json.loads(args.data.read_text(encoding="utf-8"))
    text, judge = report(data["meta"], data["branches"])
    print(text)
    return 0 if judge else 1


if __name__ == "__main__":
    sys.exit(main())
