"""토큰 사용 명세(`.scratch/token-usage/spec.md`)가 정하는 값 둘을 세션 기록으로 잰다.

`~/.claude/projects/` 아래에서 이 저장소와 그 워크트리의 세션 기록(.jsonl, 폴더 이름이
`C--project-agent`이거나 `C--project-agent--`로 시작한다)만 읽는다. 훅이 이 저장소의 프로젝트
설정에만 등록되기 때문이다. 비용은 `.scratch/harness/probes/session_cost/costs.py`의 단가표로 환산한
달러다. 같은 세션 기록이 프로젝트 폴더 둘(워크트리 폴더와 주 폴더)에 겹쳐 있을 수 있어 메인 세션
파일은 파일 이름(세션 ID)으로, 서브에이전트 파일은 부모 세션 ID와 파일 이름으로 한 번만 읽는다. 한
파일 안의 모델 호출은 응답 ID로 한 번만 센다. 창은 파일의 수정 시각으로 고르고, `boundaries`는 그
가운데 창 안에서 시작한 세션만 쓴다. 창은 실행 시각에서 거슬러 세므로 같은 명령도 돌리는 날마다 수가
다르다. 명세가 든 수는 README의 실행 기록이다.

하위 명령:
- `results <시간>`: Read·Bash·PowerShell 결과의 글자 수 분포. 범위(`offset`·`limit`)를 주지 않은
  결과만 문턱과 견주어, 문턱마다 그 문턱을 넘은 결과의 수, 세션과 파일·명령의 쌍(같은 대상에 한 번만
  알린다면 그 수), 기록 항목 무게(글자 수 × 그 뒤 실려 간 호출 수, 세션 컨텍스트가 직전의 절반
  아래로 줄면 거기서 끊는다) 가운데 몫을 낸다. 무게의 분모는 기록에 남은 항목(사람 입력, 모델 글,
  도구 입력과 결과, 첨부)이다. 시스템 지침, 도구 정의, 기록에 남지 않는 사고 과정은 빠진다.
- `boundaries <시간>`: 메인 세션에서 세션 컨텍스트가 처음 20만 토큰을 넘은 뒤 처음 오는 경계의 종류,
  그 지점의 세션 컨텍스트, 그 뒤의 환산 비용, 그 사이 40만을 넘었는지. 규칙 둘을 견준다. ADR 0033의
  단계 경계(성공한 `git commit`, 성공한 `gh pr create`나 MCP의 PR 만들기)와, 거기에 후보 "셀프 리뷰
  시작"을 더한 것이다. 셀프 리뷰 시작은 Skill 도구의 `skill`이 `code-review`이거나, `.claude`로
  시작하는 경로 접두에 `:code-review`가 붙은 것(워크트리 세션의 스킬 이름)이다. 커밋은 그 세션이
  PR을 연 앞인지 뒤인지로 가른다.

표지: `results`는 세 도구의 결과, `boundaries`는 메인 세션의 모델 호출과 경계를 하나도 읽지 못하면
측정이 아니라고 보고 2로 끝난다.

못 보는 것:
- 성공은 도구 결과의 `is_error`로만 가른다. 셸이 0으로 끝났지만 커밋이 만들어지지 않은 경우(바꾼
  것이 없다는 git의 출력)는 성공으로 센다. 셀프 리뷰 시작은 Skill 호출이 있었는지만 본다.
- 커밋 판정은 명령 문자열 어디서든 `git`(`-c`·`-C` 앞 옵션 포함) 뒤의 `commit`을 찾는다. 명령 위치만
  보는 훅보다 넓어, 따옴표나 heredoc 속 `git commit`도 센다. 별칭과 스크립트 안의 커밋은 놓친다.
- Claude Code가 읽기 상한으로 잘라 낸 Read 결과는 가르지 못했다. 결과 본문에 잘랐다는 표지가 없었다.
- 이 세션이 연 PR만 안다. 앞 세션이 PR을 연 브랜치의 커밋은 "PR을 열기 전"으로 센다.
- 글자 수는 토큰이 아니다. 한국어와 코드는 글자당 토큰이 달라 무게의 몫은 어림이다.
- 단가표에 없는 모델의 호출은 비용에서 빠지고 그 수를 따로 찍는다.
- 겹친 사본은 경로 정렬로 앞의 것(주 폴더의 것)을 읽는다. 2026-10-16 PR 직전 버그 리뷰가 겹친
  15쌍에서 워크트리 폴더의 사본이 모두 주 폴더 사본의 바이트 접두인 것을 봤다. 응답 ID는 한 파일
  안에서만 거르므로, 포크한 세션이 복사해 온 응답은 두 세션에서 모두 센다(같은 리뷰가 7일에 약
  0.6%로 셌다).
- 세션이 쓰는 도중이라 줄바꿈 없이 잘린 마지막 줄은 읽지 않고 넘긴다. 그 밖의 깨진 줄은 예외로
  끝난다.
- "문턱을 넘은 호출에서 그 경계까지"의 호출 수는 문턱을 넘은 호출 자신부터 센다. 그 호출이 경계를
  냈으면 1이다.
"""

from __future__ import annotations

import importlib.util
import json
import re
import statistics
import sys
import time
from collections import Counter, defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType

ROOT = Path.home() / ".claude" / "projects"
REPO_FOLDER = "C--project-agent"
TOOLS = ("Read", "Bash", "PowerShell")
THRESHOLDS = (10_000, 15_000, 20_000, 30_000, 40_000)
HANDOFF_AT = 200_000
COMMIT = re.compile(r"(?<![\w-])git(?:\s+-[cC]\s+\S+)*\s+commit(?![\w-])")
PR_CREATE = re.compile(r"(?<![\w-])gh\s+pr\s+create(?![\w-])")


def _load_costs() -> ModuleType:
    path = Path(__file__).resolve().parents[2] / "harness/probes/session_cost/costs.py"
    spec = importlib.util.spec_from_file_location("costs", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"단가표를 읽지 못했다: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["costs"] = module
    spec.loader.exec_module(module)
    return module


costs = _load_costs()


def records(p: Path) -> Iterator[dict]:
    """기록 한 줄씩. 줄바꿈 없이 잘린 마지막 줄(쓰는 도중의 세션)만 넘기고 나머지 깨진 줄은
    예외다."""
    with open(p, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.strip():
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                if line.endswith("\n"):
                    raise
                return


def blocks_of(d: dict) -> list[dict]:
    m = d.get("message")
    c = m.get("content") if isinstance(m, dict) else None
    return [b for b in c if isinstance(b, dict)] if isinstance(c, list) else []


def text_len(content: object) -> int:
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(
            len(str(b.get("text", "")))
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    return 0


def context_of(usage: dict) -> int:
    return (
        int(usage.get("input_tokens", 0))
        + int(usage.get("cache_creation_input_tokens", 0))
        + int(usage.get("cache_read_input_tokens", 0))
    )


def time_of(d: dict) -> datetime | None:
    try:
        t = datetime.fromisoformat(str(d.get("timestamp", "")).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo is not None else None


def is_self_review(skill: str) -> bool:
    """명세가 인계 훅에 정한 셀프 리뷰 판정과 같다."""
    if skill == "code-review":
        return True
    prefix, _, name = skill.rpartition(":")
    return name == "code-review" and prefix.startswith(".claude")


def repo_jsonl(hours: float) -> Iterator[Path]:
    """창 안에서 바뀐 이 저장소의 기록 파일 전부(메인 세션과 서브에이전트)."""
    cut = time.time() - hours * 3600
    for p in sorted(ROOT.rglob("*.jsonl")):
        folder = p.relative_to(ROOT).parts[0]
        in_repo = folder == REPO_FOLDER or folder.startswith(REPO_FOLDER + "--")
        if in_repo and p.stat().st_mtime >= cut:
            yield p


def session_files(hours: float) -> Iterator[Path]:
    """메인 세션 기록. 겹친 사본은 세션 ID로 하나만 낸다."""
    seen: set[str] = set()
    for p in repo_jsonl(hours):
        if "subagents" not in p.parts and p.stem not in seen:
            seen.add(p.stem)
            yield p


def subagent_files(hours: float) -> Iterator[Path]:
    """서브에이전트 기록. 겹친 사본은 부모 세션 ID와 파일 이름으로 하나만 낸다."""
    seen: set[str] = set()
    for p in repo_jsonl(hours):
        key = f"{p.parent.parent.name}/{p.stem}"
        if "subagents" in p.parts and key not in seen:
            seen.add(key)
            yield p


@dataclass
class Result:
    tool: str
    chars: int
    key: str
    ranged: bool
    weight: float = 0.0


@dataclass
class SessionScan:
    """한 세션 기록의 도구 결과와 기록 항목 무게의 합."""

    results: list[Result] = field(default_factory=list)
    total_weight: float = 0.0


def scan_results(p: Path) -> SessionScan:
    """도구 결과를 모으고 모든 항목의 무게 합과 결과마다의 무게를 매긴다.

    무게 = 글자 수 × 그 항목이 들어온 뒤 실려 간 호출 수. 세션 컨텍스트가 직전의 절반 아래로 줄면
    (압축) 그때까지 쌓인 항목은 거기서 끊는다.
    """
    scan = SessionScan()
    uses: dict[str, tuple[str, str, bool]] = {}
    open_items: list[tuple[int, int, Result | None]] = []
    ids: set[str] = set()
    idx = prev = 0

    def close(end: int) -> None:
        for chars, start, res in open_items:
            w = chars * max(end - start, 0)
            scan.total_weight += w
            if res is not None:
                res.weight += w
        open_items.clear()

    for d in records(p):
        kind = d.get("type")
        m = d.get("message") if isinstance(d.get("message"), dict) else {}
        if kind == "assistant":
            u = m.get("usage")
            mid = str(m.get("id") or d.get("uuid"))
            if isinstance(u, dict) and mid not in ids and str(m.get("model")) != "<synthetic>":
                ids.add(mid)
                idx += 1
                c = context_of(u)
                if prev > 100_000 and c < prev * 0.5:
                    close(idx)
                prev = c
            for b in blocks_of(d):
                if b.get("type") == "tool_use":
                    name = str(b.get("name"))
                    inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                    if name == "Read":
                        key = str(inp.get("file_path", "")).replace("\\", "/")
                        ranged = "offset" in inp or "limit" in inp
                    else:
                        key = re.sub(r"\s+", " ", str(inp.get("command", "")))
                        ranged = False
                    uses[str(b.get("id"))] = (name, key, ranged)
                    open_items.append((len(json.dumps(inp, ensure_ascii=False)), idx, None))
                elif b.get("type") == "text":
                    open_items.append((len(str(b.get("text", ""))), idx, None))
        elif kind == "user":
            c = m.get("content")
            if isinstance(c, str):
                open_items.append((len(c), idx, None))
            for b in blocks_of(d):
                if b.get("type") == "tool_result":
                    name, key, ranged = uses.get(str(b.get("tool_use_id")), ("?", "", False))
                    n = text_len(b.get("content"))
                    res = Result(name, n, key, ranged) if name in TOOLS else None
                    if res is not None:
                        scan.results.append(res)
                    open_items.append((n, idx, res))
                elif b.get("type") == "text":
                    open_items.append((len(str(b.get("text", ""))), idx, None))
        elif kind == "attachment":
            a = d.get("attachment")
            if isinstance(a, dict) and a.get("type") != "prompt_snapshot":
                open_items.append((len(json.dumps(a, ensure_ascii=False)), idx, None))
    close(idx + 1)
    return scan


def describe_spread(values: list[int]) -> str:
    """중앙값, 90%, 99%, 최대를 한 줄 글로."""
    if len(values) < 2:
        return f"값 {len(values)}개"
    q = statistics.quantiles(values, n=100, method="inclusive")
    return f"중앙값 {q[49]:,.0f}, 90% {q[89]:,.0f}, 99% {q[98]:,.0f}, 최대 {max(values):,}"


def report_results(label: str, scans: list[SessionScan]) -> int:
    results = [r for s in scans for r in s.results]
    total_weight = sum(s.total_weight for s in scans) or 1.0
    print(f"\n## {label}: 세션 {len(scans)}개, 결과 {len(results):,}개")
    for tool in TOOLS:
        mine = [r for r in results if r.tool == tool]
        if not mine:
            print(f"\n### {tool}: 결과 없음")
            continue
        chars = sum(r.chars for r in mine) or 1
        print(f"\n### {tool}: {len(mine):,}개, {sum(r.chars for r in mine):,}자")
        print(f"글자 수 분포: {describe_spread([r.chars for r in mine])}")
        if tool == "Read":
            print(f"범위를 준 것 {sum(r.ranged for r in mine):,}개")
        print(
            "\n| 문턱(자) | 넘은 결과 | 결과의 몫 | 글자의 몫 | 세션·대상 쌍 | 쌍이 난 세션 ",
            end="",
        )
        print("| 무게의 몫 |")
        print("|--:|--:|--:|--:|--:|--:|--:|")
        for t in THRESHOLDS:
            over = [
                (i, r)
                for i, s in enumerate(scans)
                for r in s.results
                if r.tool == tool and r.chars > t and not r.ranged
            ]
            pairs = {(i, r.key) for i, r in over}
            print(
                f"| {t:,} | {len(over):,} | {len(over) / len(mine):.1%} "
                f"| {sum(r.chars for _, r in over) / chars:.1%} | {len(pairs):,} "
                f"| {len({i for i, _ in over}):,} "
                f"| {sum(r.weight for _, r in over) / total_weight:.2%} |"
            )
    return len(results)


def cmd_results(hours: float) -> None:
    """범위 없이 받은 결과만 문턱과 견준다(범위를 준 읽기에는 알릴 까닭이 없다)."""
    mains = [scan_results(p) for p in session_files(hours)]
    subs = [scan_results(p) for p in subagent_files(hours)]
    print(f"최근 {hours:g}시간(파일 수정 시각), 이 저장소")
    n = report_results("메인 세션", mains) + report_results("서브에이전트", subs)
    if n == 0:
        print("표지 없음: Read·Bash·PowerShell 결과를 하나도 읽지 못했다. 측정이 아니다.")
        raise SystemExit(2)


@dataclass
class Call:
    when: datetime | None
    context: int
    cost: float | None


@dataclass
class Boundary:
    kind: str
    at_call: int
    candidate: bool


def scan_boundaries(p: Path) -> tuple[list[Call], list[Boundary]]:
    calls: list[Call] = []
    marks: list[Boundary] = []
    ids: set[str] = set()
    pending: dict[str, str] = {}
    pr_opened = False
    for d in records(p):
        kind = d.get("type")
        m = d.get("message") if isinstance(d.get("message"), dict) else {}
        if kind == "assistant":
            u = m.get("usage")
            mid = str(m.get("id") or d.get("uuid"))
            model = str(m.get("model"))
            if isinstance(u, dict) and mid not in ids and model != "<synthetic>":
                ids.add(mid)
                calls.append(Call(time_of(d), context_of(u), costs.cost(model, costs.Usage.of(u))))
            for b in blocks_of(d):
                if b.get("type") != "tool_use":
                    continue
                name = str(b.get("name"))
                inp = b.get("input") if isinstance(b.get("input"), dict) else {}
                command = str(inp.get("command", ""))
                if name == "Skill" and is_self_review(str(inp.get("skill", ""))):
                    marks.append(Boundary("셀프 리뷰 시작", len(calls), candidate=True))
                elif name.endswith("create_pull_request"):
                    pending[str(b.get("id"))] = "pr"
                elif name in ("Bash", "PowerShell") and PR_CREATE.search(command):
                    pending[str(b.get("id"))] = "pr"
                elif name in ("Bash", "PowerShell") and COMMIT.search(command):
                    if "--dry-run" not in command:
                        pending[str(b.get("id"))] = "commit"
        elif kind == "user":
            for b in blocks_of(d):
                if b.get("type") != "tool_result":
                    continue
                what = pending.pop(str(b.get("tool_use_id")), None)
                if what is None or b.get("is_error") is True:
                    continue
                if what == "pr":
                    marks.append(Boundary("PR 열기", len(calls), candidate=False))
                    pr_opened = True
                else:
                    label = "커밋(이 세션이 PR을 연 뒤)" if pr_opened else "커밋(PR을 열기 전)"
                    marks.append(Boundary(label, len(calls), candidate=False))
    return calls, marks


@dataclass
class Outcome:
    """20만을 넘은 세션 하나에서, 그 뒤 처음 온 경계에서 인계했다면."""

    kind: str
    after_cost: float
    at_context: int | None
    gap_calls: int | None
    over_400k_first: bool


def outcome_of(calls: list[Call], marks: list[Boundary], cross: int) -> Outcome:
    """그 사이 40만을 넘었으면 40만 자동 압축이 먼저 왔을 것으로 센다."""
    first = next((b for b in marks if b.at_call > cross), None)
    if first is None:
        rest = sum(c.cost or 0.0 for c in calls[cross:])
        return Outcome("넘은 뒤 경계가 없었다", rest, None, None, False)
    return Outcome(
        first.kind,
        sum(c.cost or 0.0 for c in calls[first.at_call :]),
        calls[first.at_call - 1].context,
        first.at_call - cross,
        max(c.context for c in calls[cross : first.at_call]) > 400_000,
    )


def print_rule(title: str, outcomes: list[Outcome]) -> None:
    kinds = Counter(o.kind for o in outcomes)
    after: dict[str, float] = defaultdict(float)
    for o in outcomes:
        after[o.kind] += o.after_cost
    print(f"\n### {title}")
    print("| 20만을 넘은 뒤 처음 온 것 | 세션 | 그 뒤 비용 |")
    print("|---|--:|--:|")
    for k, n in kinds.most_common():
        print(f"| {k} | {n} | ${after[k]:,.2f} |")
    gaps = [o.gap_calls for o in outcomes if o.gap_calls is not None]
    contexts = [o.at_context for o in outcomes if o.at_context is not None]
    if gaps:
        print(f"문턱을 넘은 호출에서 그 경계까지: 호출 중앙값 {statistics.median(gaps):,.0f}")
        first_400k = sum(o.over_400k_first for o in outcomes)
        print(f"그 사이 40만을 넘은 세션(40만 자동 압축이 먼저 왔을 것): {first_400k}")
        print(f"그 경계의 세션 컨텍스트: {describe_spread(contexts)}")


def cmd_boundaries(hours: float) -> None:
    """이 저장소의 메인 세션 가운데 창 안에서 시작한 것만 쓴다(앞부분이 창 밖이면 문턱을 넘는 자리를
    모른다). 규칙 둘을 견준다. ADR 0033의 경계(커밋, PR 열기)와, 거기에 후보(셀프 리뷰 시작)를
    더한 것이다."""
    cutoff = datetime.now(UTC) - timedelta(hours=hours)
    adr: list[Outcome] = []
    with_candidate: list[Outcome] = []
    all_marks: Counter[str] = Counter()
    mark_context: dict[str, list[int]] = defaultdict(list)
    not_crossed = over_400k = 0
    sessions = calls_n = marks_n = unpriced = 0
    total_cost = 0.0
    for p in session_files(hours):
        calls, marks = scan_boundaries(p)
        if len(calls) < 2 or calls[0].when is None or calls[0].when < cutoff:
            continue
        sessions += 1
        calls_n += len(calls)
        marks_n += len(marks)
        for b in marks:
            all_marks[b.kind] += 1
            mark_context[b.kind].append(calls[b.at_call - 1].context)
        unpriced += sum(c.cost is None for c in calls)
        total_cost += sum(c.cost or 0.0 for c in calls)
        if max(c.context for c in calls) > 400_000:
            over_400k += 1
        cross = next((i for i, c in enumerate(calls) if c.context > HANDOFF_AT), None)
        if cross is None:
            not_crossed += 1
            continue
        adr.append(outcome_of(calls, [b for b in marks if not b.candidate], cross))
        with_candidate.append(outcome_of(calls, marks, cross))
    if calls_n == 0 or marks_n == 0:
        print("표지 없음: 메인 세션의 모델 호출이나 단계 경계를 하나도 읽지 못했다. 측정이 아니다.")
        raise SystemExit(2)
    print(
        f"최근 {hours:g}시간에 시작한 이 저장소의 메인 세션 {sessions}개, 모델 호출 {calls_n:,}회, "
        f"경계 {marks_n}개, 환산 비용 ${total_cost:,.2f}(단가표 밖 {unpriced}회)"
    )
    print(f"세션 컨텍스트가 20만을 넘지 않은 세션 {not_crossed}개, 40만을 넘은 세션 {over_400k}개")
    print_rule("ADR 0033의 경계(커밋, PR 열기)", adr)
    print_rule("후보(셀프 리뷰 시작)를 더한 경계", with_candidate)
    print("\n모든 경계의 종류와 그때의 세션 컨텍스트:")
    for k, n in all_marks.most_common():
        print(f"- {k}: {n}개, {describe_spread(mark_context[k])}")


def main(argv: list[str]) -> None:
    if len(argv) != 3 or argv[1] not in ("results", "boundaries"):
        raise SystemExit("사용법: measure.py results|boundaries <시간>")
    hours = float(argv[2])
    if argv[1] == "results":
        cmd_results(hours)
    else:
        cmd_boundaries(hours)


if __name__ == "__main__":
    main(sys.argv)
