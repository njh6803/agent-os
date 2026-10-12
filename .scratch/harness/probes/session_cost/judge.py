"""모델 판정 실험. 티켓만 본 `claude-opus-5-5`가 드러난 난이도(턴 수, 바뀐 파일 수, 턴 시간 합)를
맞히는지 잰다.

설계와 판정 문턱은 README의 사전 등록 절 "모델 판정 실험"이 원천이다. 판정자는 저장소를 읽지 않고
`CLAUDE.md`(그것이 `@`로 싣는 헌법 원칙을 펼친 것), 기준 티켓 열 개(merge-base 판본의 본문과 실제
결과), 대상 티켓 하나(merge-base 판본)만 본다. `CLAUDE.md`는 지금 체크아웃의 판이다. 대상마다 그때의
판을 주면 캐시가 깨져 금액이 커지고, 이 실험이 묻는 것은 티켓 본문의 정보라 규약의 판 차이는 작다고
본 어림이다.

하위 명령 셋.

- `plan`: 대상·기준 티켓의 수, 호출 수, 토큰과 금액의 어림을 찍는다. API를 부르지 않는다. 토큰은
  글자 수로 어림한다 (한국어 마크다운에서 글자 1.2개를 토큰 하나로 본 가운데 값과 0.8개를 하나로 본
  위 끝).
- `run --yes`: API를 부른다. 응답마다 `judge_results.jsonl`에 한 줄을 덧붙이고, 이미 있는 (PR,
  회차)는 건너뛴다. 멈춤 까닭이 `end_turn`이 아니거나, 응답한 모델(`resp.model`)이 `MODEL`이
  아니거나, 답이 스키마에 맞지 않거나, API 오류면 측정이 아닌 회차로 적고 다시 돌면 다시 묻는다.
  대체 모델(fallbacks)은 켜지 않는다. 다른 모델이 답하면 판정자가 섞인다. 응답한 모델을 적는 것은 첫
  실행 도중에 더해, 그 전의 판이 쓴 회차에는 그 칸이 없다(`score`가 그 수를 찍는다).
- `score`: 순위(Spearman ρ)와 보정(80% 범위가 실제 값을 담은 비율)을 찍는다. 세 회차가 모두 측정인
  대상만 센다.

돌리는 법(워크트리 루트에서, 판은 README의 "돌리는 법"):
`uv run --with anthropic==1.7.0 --env-file ../../../.env python <이 파일> run --yes`.
종료 코드: 0 완료, 1 측정이 아닌 회차나 대상이 있다(`run`·`score`), 2 입력이나 인자가 없다.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from analyze import (
    RESAMPLES,
    TICKET_KEYS,
    Row,
    boot_rho,
    feat,
    feature_population,
    num,
    spearman,
)
from costs import PRICES, Json

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "judge_results.jsonl"
MODEL = "claude-opus-5-5"
EFFORT = "high"
REPEATS = 3
ANCHORS = 10
MAX_TOKENS = 16000
AXES = ("ambiguity", "scope", "novelty", "verification", "contract")
MIN_TARGETS = 20


SYSTEM = """너는 소프트웨어 작업의 크기를 시작하기 전에 어림하는 판정자다. 저장소는 볼 수 없다.

아래에 셋이 온다. 저장소의 작업 규약(CLAUDE.md), 같은 저장소에서 실제로 끝난 기준 티켓
열 개와 그 결과, 그리고 어림할 대상 티켓 하나. 티켓 본문은 작업을 시작하기 전의 판이다.

결과의 단위는 셋이다.
- 턴 수: 사람의 메시지나 작업 알림 같은 계기 하나부터 다음 계기 전까지를 한 턴으로 센,
  그 티켓의 브랜치에서 일한 모든 세션의 턴 수.
- 파일 수: 그 티켓의 PR이 바꾼 파일 수.
- 턴 시간(분): 에이전트가 일한 턴 시간의 합. 사람을 기다린 빈 시간은 빠진다.

대상 티켓에 대해 셋마다 80% 범위(실제 값이 그 안에 들 확률이 80%인 아래 끝과 위 끝)를
낸다. 기준 티켓의 결과를 눈금으로 삼는다. 그리고 축 다섯을 1~3으로 채점하고 축마다 이유
한 줄을 쓴다.
- ambiguity(모호함): 요구가 열려 있어 판단과 결정이 필요한 정도.
- scope(범위): 손대는 층과 파일의 넓이.
- novelty(새로움): 저장소에 선례가 없는 정도.
- verification(검증의 어려움): 끝났는지를 기계로 확인하기 어려운 정도.
- contract(계약 접촉): sdk, openapi.json, 헌법 같은 계약에 닿는 정도.
"""

SCHEMA: dict[str, Json] = {
    "type": "object",
    "properties": {
        "turns": {
            "type": "object",
            "properties": {"low": {"type": "integer"}, "high": {"type": "integer"}},
            "required": ["low", "high"],
            "additionalProperties": False,
        },
        "files": {
            "type": "object",
            "properties": {"low": {"type": "integer"}, "high": {"type": "integer"}},
            "required": ["low", "high"],
            "additionalProperties": False,
        },
        "minutes": {
            "type": "object",
            "properties": {"low": {"type": "number"}, "high": {"type": "number"}},
            "required": ["low", "high"],
            "additionalProperties": False,
        },
        "axes": {
            "type": "object",
            "properties": {
                a: {
                    "type": "object",
                    "properties": {
                        "score": {"type": "integer", "enum": [1, 2, 3]},
                        "reason": {"type": "string"},
                    },
                    "required": ["score", "reason"],
                    "additionalProperties": False,
                }
                for a in AXES
            },
            "required": list(AXES),
            "additionalProperties": False,
        },
    },
    "required": ["turns", "files", "minutes", "axes"],
    "additionalProperties": False,
}


def git(*args: str) -> str:
    out = subprocess.run(["git", *args], cwd=HERE, capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args[:2])} 가 {out.returncode}로 끝났다: {out.stderr.strip()[:200]}"
        )
    return out.stdout


def population(rows: list[Row]) -> list[Row]:
    """가설 1·2의 모집단(`analyze.feature_population`). 티켓 본문을 다시 읽을 경로와 커밋이 있는
    것만."""
    return [
        r
        for r in feature_population(rows)
        if isinstance(r.get("ticket"), str) and isinstance(r.get("base"), str)
    ]


def conforms(answer: Json) -> bool:
    """답이 `SCHEMA`에 맞는지(사전 등록의 "스키마에 맞는 JSON"). 구조화 출력이 보장하지만 측정
    표지로 다시 본다."""
    if not isinstance(answer, dict) or set(answer) != {"turns", "files", "minutes", "axes"}:
        return False
    for key, kinds in (("turns", (int,)), ("files", (int,)), ("minutes", (int, float))):
        span = answer[key]
        if not isinstance(span, dict) or set(span) != {"low", "high"}:
            return False
        if not all(isinstance(span[e], kinds) and not isinstance(span[e], bool) for e in span):
            return False
    axes = answer["axes"]
    if not isinstance(axes, dict) or set(axes) != set(AXES):
        return False
    return all(
        isinstance(v, dict)
        and set(v) == {"score", "reason"}
        and v["score"] in (1, 2, 3)
        and isinstance(v["reason"], str)
        for v in axes.values()
    )


def split(pop: list[Row]) -> tuple[list[Row], list[Row]]:
    """비용 순으로 세워 같은 간격으로 고른 열 개가 기준이고 나머지가 대상이다."""
    ordered = sorted(pop, key=lambda r: (num(r, "cost"), str(r["branch"])))
    if len(ordered) <= ANCHORS:
        return ordered, []
    picks = sorted({round(i * (len(ordered) - 1) / (ANCHORS - 1)) for i in range(ANCHORS)})
    anchors = [ordered[i] for i in picks]
    chosen = {str(r["branch"]) for r in anchors}
    return anchors, [r for r in ordered if str(r["branch"]) not in chosen]


def ticket_text(r: Row) -> str:
    return git("show", f"{r['base']}:{r['ticket']}")


def claude_md() -> str:
    top = Path(git("rev-parse", "--show-toplevel").strip())
    text = (top / "CLAUDE.md").read_text(encoding="utf-8")
    principles = (top / "docs" / "constitution" / "principles.md").read_text(encoding="utf-8")
    return text.replace("@docs/constitution/principles.md", principles)


def anchors_block(anchors: list[Row]) -> str:
    parts = ["# 기준 티켓 열 개 (실제 결과)"]
    for i, r in enumerate(anchors, 1):
        parts.append(
            f"\n## 기준 {i}: {r['ticket']}\n"
            f"실제 결과: 턴 수 {int(num(r, 'turns'))}, 파일 수 {int(num(r, 'changed_files'))}, "
            f"턴 시간 {num(r, 'turn_min'):.0f}분\n\n{ticket_text(r)}"
        )
    return "\n".join(parts)


def target_block(r: Row) -> str:
    return f"# 대상 티켓: {r['ticket']}\n\n{ticket_text(r)}"


def load_rows() -> list[Row]:
    data = json.loads((HERE / "branches.json").read_text(encoding="utf-8"))
    rows = data["branches"]
    return rows if isinstance(rows, list) else []


def plan(rows: list[Row]) -> int:
    pop = population(rows)
    anchors, targets = split(pop)
    if not targets:
        print("대상이 없다", file=sys.stderr)
        return 2
    prefix = len(SYSTEM) + len(claude_md()) + len(anchors_block(anchors))
    per_target = [len(target_block(r)) for r in targets]
    calls = len(targets) * REPEATS
    p = PRICES[MODEL]
    out_tokens = (2000, 6000)
    lines = [
        f"모집단 {len(pop)}, 기준 {len(anchors)}, 대상 {len(targets)}, 회차 {REPEATS}",
        f"호출 {calls}",
        f"모델 {MODEL}, 노력 {EFFORT}, max_tokens {MAX_TOKENS}, 캐시는 기본(5분) TTL",
        f"고정 앞부분 {prefix:,}자, 대상 티켓 평균 {statistics.fmean(per_target):,.0f}자",
    ]
    for label, chars_per_token, out in (
        ("가운데", 1.2, out_tokens[0]),
        ("위 끝", 0.8, out_tokens[1]),
    ):
        pre = prefix / chars_per_token
        tgt = sum(per_target) * REPEATS / chars_per_token
        usd = (
            pre * p.input * 1.25  # 첫 호출의 캐시 쓰기. 회차 사이가 5분을 넘지 않는다고 본다
            + pre * (calls - 1) * p.cache_read
            + tgt * p.input
            + calls * out * p.output
        ) / 1e6
        lines.append(
            f"{label}: 앞부분 {pre:,.0f} 토큰, 대상 합 {tgt:,.0f} 토큰, "
            f"출력 호출당 {out:,} → 약 ${usd:.2f}"
        )
    lines.append("기준 티켓: " + ", ".join(str(r["branch"]) for r in anchors))
    print("\n".join(lines))
    return 0


def done_keys() -> set[tuple[int, int]]:
    if not RESULTS.exists():
        return set()
    keys: set[tuple[int, int]] = set()
    for line in RESULTS.read_text(encoding="utf-8").splitlines():
        o = json.loads(line)
        if o.get("measured"):
            keys.add((int(o["pr"]), int(o["round"])))
    return keys


def run(rows: list[Row], limit: int | None) -> int:
    import anthropic  # 판을 고정해 `uv run --with` 로 받는다. 프로젝트 의존성이 아니다

    pop = population(rows)
    anchors, targets = split(pop)
    client = anthropic.Anthropic()
    system = [
        {"type": "text", "text": SYSTEM},
        {"type": "text", "text": claude_md()},
        {"type": "text", "text": anchors_block(anchors), "cache_control": {"type": "ephemeral"}},
    ]
    done = done_keys()
    failed = 0
    called = 0
    for rnd in range(1, REPEATS + 1):
        for r in targets:
            pr = int(num(r, "pr"))
            if (pr, rnd) in done:
                continue
            if limit is not None and called >= limit:
                break
            called += 1
            record: dict[str, Json] = {
                "pr": pr,
                "branch": r["branch"],
                "round": rnd,
                "at": datetime.now(UTC).isoformat(),
                "model": MODEL,
                "effort": EFFORT,
                "sdk": anthropic.__version__,
            }
            try:
                resp = client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    system=system,
                    messages=[{"role": "user", "content": target_block(r)}],
                    output_config={
                        "effort": EFFORT,
                        "format": {"type": "json_schema", "schema": SCHEMA},
                    },
                )
            except anthropic.APIError as e:
                record |= {"measured": False, "why": f"API 오류: {type(e).__name__}: {e}"[:500]}
            else:
                u = resp.usage
                record["usage"] = {
                    "input": u.input_tokens,
                    "output": u.output_tokens,
                    "cache_read": u.cache_read_input_tokens or 0,
                    "cache_write": u.cache_creation_input_tokens or 0,
                }
                record["stop_reason"] = resp.stop_reason
                record["served_model"] = resp.model
                text = next((b.text for b in resp.content if b.type == "text"), "")
                try:
                    answer: Json = json.loads(text)
                except json.JSONDecodeError:
                    answer = None
                if resp.stop_reason != "end_turn":
                    record |= {"measured": False, "why": f"stop_reason {resp.stop_reason}"}
                elif not resp.model.startswith(MODEL):
                    record |= {"measured": False, "why": f"다른 모델이 답했다: {resp.model}"}
                elif not conforms(answer):
                    record |= {"measured": False, "why": "스키마에 맞지 않는다", "text": text[:500]}
                else:
                    record |= {"measured": True, "answer": answer}
            failed += 0 if record.get("measured") else 1
            with RESULTS.open("a", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            print(
                f"{pr} 회차 {rnd}: {'측정' if record.get('measured') else record.get('why')}",
                flush=True,
            )
    print(f"측정이 아닌 회차 {failed}", file=sys.stderr)
    return 1 if failed else 0


def score(rows: list[Row]) -> int:
    """측정인 회차는 다시 본다: 멈춤 까닭이 `end_turn`이고 답이 스키마에 맞고, 응답한 모델을
    적었으면 그것이 `MODEL`인 것. 응답한 모델을 적기 전의 판(`served_model` 없음)이 쓴 회차는 그
    수를 따로 찍는다."""
    answers: dict[int, list[dict[str, Json]]] = {}
    not_measured = 0
    without_model = 0
    for line in RESULTS.read_text(encoding="utf-8").splitlines() if RESULTS.exists() else []:
        o = json.loads(line)
        served = o.get("served_model")
        ok = (
            o.get("measured")
            and o.get("stop_reason") == "end_turn"
            and conforms(o.get("answer"))
            and (served is None or str(served).startswith(MODEL))
        )
        if ok:
            answers.setdefault(int(o["pr"]), []).append(o)
            without_model += 1 if served is None else 0
        else:
            not_measured += 1
    pop = population(rows)
    _, targets = split(pop)
    complete = [r for r in targets if len(answers.get(int(num(r, "pr")), [])) >= REPEATS]
    if len(complete) < 3:
        print(f"세 회차가 모두 측정인 대상이 {len(complete)}개다", file=sys.stderr)
        return 1

    def value(r: Row, *path: str) -> float:
        """그 대상의 세 회차에서 답의 `path` 값의 중앙값."""
        vals: list[float] = []
        for o in answers[int(num(r, "pr"))][:REPEATS]:
            cur: Json = o["answer"]
            for p in path:
                cur = cur.get(p) if isinstance(cur, dict) else None
            if isinstance(cur, int | float) and not isinstance(cur, bool):
                vals.append(float(cur))
        return statistics.median(vals)

    def med(r: Row, path: tuple[str, str]) -> float:
        return value(r, *path)

    def axis(r: Row, name: str) -> float:
        return value(r, "axes", name, "score")

    actual_min = [num(r, "turn_min") for r in complete]
    mid = [
        math.sqrt(max(med(r, ("minutes", "low")), 0.1) * max(med(r, ("minutes", "high")), 0.1))
        for r in complete
    ]
    rho = spearman(mid, actual_min)
    ci, skipped = boot_rho(mid, actual_min)
    ind: list[tuple[str, float]] = []
    for k in TICKET_KEYS:
        xs = [feat(r, "ticket_features", k) for r in complete]
        pairs = [(x, y) for x, y in zip(xs, actual_min, strict=True) if x is not None]
        rr = spearman([x for x, _ in pairs], [y for _, y in pairs])
        if rr is not None:
            ind.append((k, abs(rr)))
    best = max(ind, key=lambda t: t[1]) if ind else ("-", 0.0)
    if len(complete) < MIN_TARGETS:
        verdict = f"판정하지 않음(대상 {len(complete)} < {MIN_TARGETS})"
    elif rho is not None and ci is not None and rho >= 0.4 and ci[0] > 0 and rho >= best[1] + 0.1:
        verdict = "쓸모 있다"
    else:
        verdict = "쓸모 있다고 볼 수 없다"
    ci_s = f"[{ci[0]:.2f}, {ci[1]:.2f}]" if ci else "-"
    lines = [
        f"대상 {len(complete)}(세 회차 모두 측정), 측정이 아닌 회차 {not_measured}",
        f"응답한 모델을 적기 전의 판이 쓴 측정 회차 {without_model}",
        f"시간 가운데 값 대 실제 턴 시간: ρ = {rho if rho is None else round(rho, 3)}",
        f"부트스트랩 {RESAMPLES}회 90% 구간 {ci_s}(뺀 회차 {skipped})",
        f"사전 지표의 |ρ| 가운데 가장 큰 것: {best[0]} {best[1]:.3f}",
        f"판정: {verdict}",
    ]
    for key, actual_key in (
        ("turns", "turns"),
        ("files", "changed_files"),
        ("minutes", "turn_min"),
    ):
        inside = sum(
            1
            for r in complete
            if med(r, (key, "low")) <= num(r, actual_key) <= med(r, (key, "high"))
        )
        cover = inside / len(complete)
        calibrated = "보정됨" if 0.6 <= cover <= 0.95 else "아님"
        lines.append(f"보정 {key}: {inside}/{len(complete)} = {cover:.2f} ({calibrated})")
    core = [num(r, "turn_min") - num(r, "trailing_min") for r in complete]
    lines.append(f"(탐색) 턴 끝의 system 기록 꼬리를 뺀 턴 시간과: ρ = {spearman(mid, core)}")
    costs = [num(r, "cost") for r in complete]
    lines.append(f"(탐색) 시간 가운데 값 대 비용: ρ = {spearman(mid, costs)}")
    total = [sum(axis(r, a) for a in AXES) for r in complete]
    lines.append(f"(탐색) 축 합 대 비용: ρ = {spearman(total, costs)}")
    for a in AXES:
        lines.append(f"(탐색) {a} 대 비용: ρ = {spearman([axis(r, a) for r in complete], costs)}")
    print("\n".join(lines))
    return 1 if not_measured else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("plan")
    r = sub.add_parser("run")
    r.add_argument("--yes", action="store_true", help="호출 수와 금액을 사람이 승인했다")
    r.add_argument("--limit", type=int, help="이번 실행의 호출 수 상한(요청 모양을 먼저 볼 때)")
    sub.add_parser("score")
    args = p.parse_args()
    rows = load_rows()
    if args.cmd == "plan":
        return plan(rows)
    if args.cmd == "run":
        if not args.yes:
            print(
                "run 은 --yes 가 있어야 API 를 부른다. 먼저 plan 의 금액을 승인받는다",
                file=sys.stderr,
            )
            return 2
        return run(rows, args.limit)
    return score(rows)


if __name__ == "__main__":
    sys.exit(main())
