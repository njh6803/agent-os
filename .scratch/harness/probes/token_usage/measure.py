"""토큰 사용 방침(ADR 0033)의 근거가 된 세션 기록 측정.

`~/.claude/projects/` 아래 세션 기록(.jsonl)을 읽어 하위 명령마다 하나를 잰다. 비용은
`../session_cost/costs.py`의 단가표(Claude Code의 셈)로 환산한 달러다. 같은 세션 기록이 프로젝트
폴더 둘에 겹쳐 있을 수 있어(워크트리 폴더와 주 폴더), 모델 호출은 응답 ID로 전체에서 한 번만 센다.
시간 창은 실행 시각에서 거슬러 세므로 같은 명령도 돌리는 날마다 수가 다르다. 창의 뜻은 둘이다.
`split`·`idle`은 기록의 시각으로 자르고, `simulate`는 창 안에서 시작한 세션만 쓴다.
`reads`·`plugins`· `rereads`는 파일의 수정 시각으로 골라 그 파일의 기록 전체를 센다. ADR이 든 수는
README의 실행 기록이다. `compactions`만 시간 인자가 없고 나머지는 `<시간>`이 꼭 있어야 한다.

하위 명령:
- `split <시간>`: 환산 비용을 메인 세션과 서브에이전트, 모델·노력, 서브에이전트 유형, 프로젝트로
  나눈다.
- `idle <시간>`: 직전 모델 호출과의 간격별로 세션 컨텍스트 절반 이상을 캐시에 다시 쓴 비율, 캐시
  쓰기의 TTL 갈래, `tools/wait_ci.py`를 백그라운드로 띄운 뒤 깨어난 호출.
- `simulate <시간>`: 자동 압축 지점을 낮췄다면 메인 세션이 읽은 세션 컨텍스트가 얼마나
  줄었을지(어림, 가정은 `_simulate` 독스트링)와 시작 컨텍스트의 분포.
- `compactions`: 기록 전체에서 실제로 일어난 압축의 전후.
- `reads <시간>`: 메인 세션 컨텍스트에 들어온 항목을 "글자 수 × 그 뒤 실려 간 호출 수"로 무게를 매겨
  구성 요소별로 나누고, 무게가 큰 Read 파일과 Bash 명령을 든다.
- `plugins <시간>`: 이 저장소(`C--project-agent`로 시작하는 폴더) 세션이 부른 스킬과 MCP 서버,
  그리고 창 안에서 가장 큰 첫 스킬 목록의 출처별 글자 수.
- `rereads <시간>`: 같은 세션에서 바뀌지 않은 파일을 다시 읽은 Read(다시 읽기 후보, 정의는
  `cmd_rereads` 독스트링).

표지: 하위 명령마다 재려는 것을 하나도 읽지 못하면 측정이 아니라고 보고 2로 끝난다.
`simulate`·`reads`는 모델 호출(usage가 든 assistant 기록), `split`은 단가표 안의 모델 호출,
`idle`은 단가표 안의 메인 세션 모델 호출과 백그라운드로 띄운 `wait_ci`, `compactions`는 압축 경계,
`plugins`는 Skill 호출과 메인 세션의 첫 스킬 목록, `rereads`는 Read 결과다.

못 보는 것:
- 세션 기록에는 계정이 없다. 여러 계정의 세션이 섞여도 가르지 못한다.
- `simulate`는 압축 뒤의 증가가 압축 전과 같다고 가정한다. 압축이 작업 품질에 주는 영향은 재지
  않는다.
- `reads`의 단위는 글자다. 한국어와 코드는 글자당 토큰이 달라 비중은 어림이다. 기록에 남지 않는
  모델 출력(사고 과정)은 세지 못한다.
- 서브에이전트 유형은 부모 세션의 Agent 호출과 그 결과의 `agentId`로 잇는다. 부모 기록이 창 밖이거나
  지워졌으면 "(미상)"이다.
- 단가표에 없는 모델의 호출은 비용에서 빠지고, 그 호출 수를 따로 찍는다.
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
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import ModuleType

ROOT = Path.home() / ".claude" / "projects"
RESULT_ID = re.compile(r'"tool_use_id":"([^"]+)"')
REPO_PREFIX = "C--project-agent"
# 작업 트리를 바꾸는 git 하위 명령만. `merge-base`, `worktree list`, 커밋 메시지 속 낱말은 걸리지
# 않는다.
GIT_MUTATION = re.compile(
    r"(?<![\w-])git(?:\s+-[cC]\s+\S+)*\s+(?:pull|merge|checkout|switch|rebase|reset|restore|stash"
    r"|cherry-pick|am|worktree\s+(?:add|remove|move|prune))(?![\w-])"
)


def is_repo_folder(name: str) -> bool:
    """이 저장소와 그 워크트리의 기록 폴더. 이름이 같은 접두로 시작하는 다른 저장소는 뺀다."""
    return name == REPO_PREFIX or name.startswith(REPO_PREFIX + "--")


def _load_costs() -> ModuleType:
    path = Path(__file__).resolve().parent.parent / "session_cost" / "costs.py"
    spec = importlib.util.spec_from_file_location("costs", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"단가표를 읽지 못했다: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["costs"] = module
    spec.loader.exec_module(module)
    return module


costs = _load_costs()


def recent_files(hours: float | None) -> list[Path]:
    cut = 0.0 if hours is None else time.time() - hours * 3600
    return [p for p in ROOT.rglob("*.jsonl") if p.stat().st_mtime >= cut]


def is_sub(p: Path) -> bool:
    return "subagents" in p.parts


def project_of(p: Path) -> str:
    folder = p.relative_to(ROOT).parts[0]
    return "agent(워크트리 포함)" if is_repo_folder(folder) else folder


def lines(p: Path) -> Iterator[dict]:
    with open(p, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)


def ctx_of(u: dict) -> int:
    return (
        int(u.get("input_tokens", 0))
        + int(u.get("cache_creation_input_tokens", 0))
        + int(u.get("cache_read_input_tokens", 0))
    )


def time_of(d: dict) -> datetime | None:
    """기록의 시각. 읽지 못하거나 시간대가 없으면(창의 시각과 견주지 못한다) None이다."""
    try:
        t = datetime.fromisoformat(str(d.get("timestamp", "")).replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo is not None else None


def calls(p: Path, seen: set[str], cutoff: datetime | None) -> Iterator[tuple[dict, dict]]:
    """파일 안의 모델 호출을 (기록, usage)로, 처음 나온 순서대로 낸다.

    한 응답은 블록마다 줄이 따로이고 앞 줄의 `output_tokens`는 스트리밍 중간값이다. 그래서 응답
    ID마다 줄을 모아 출력 토큰이 가장 큰 usage를 쓰고, 기록의 `content`는 모든 줄의 블록을 합친다.
    시각은 첫 줄의 것이다. 다른 파일에서 이미 나온 응답 ID와 합성 메시지는 뺀다.
    """
    order: list[str] = []
    first: dict[str, dict] = {}
    best: dict[str, dict] = {}
    blocks: dict[str, list] = {}
    for d in lines(p):
        if d.get("type") != "assistant":
            continue
        m = d.get("message")
        if not isinstance(m, dict):
            continue
        u = m.get("usage")
        if not isinstance(u, dict) or str(m.get("model")) == "<synthetic>":
            continue
        mid = str(m.get("id") or d.get("uuid"))
        if mid in seen:
            continue
        if mid not in first:
            order.append(mid)
            first[mid] = d
            best[mid] = u
            blocks[mid] = []
        elif int(u.get("output_tokens", 0)) > int(best[mid].get("output_tokens", 0)):
            best[mid] = u
        content = m.get("content")
        if isinstance(content, list):
            blocks[mid].extend(content)
    for mid in order:
        d = first[mid]
        if cutoff is not None:
            when = time_of(d)
            if when is None or when < cutoff:
                continue
        seen.add(mid)
        merged = dict(d)
        merged["message"] = dict(d["message"], content=blocks[mid])
        yield merged, best[mid]


def cutoff_of(hours: float) -> datetime:
    return datetime.now(UTC) - timedelta(hours=hours)


def require(n: int, what: str) -> None:
    if n == 0:
        print(f"표지 없음: {what}을(를) 하나도 읽지 못했다. 측정이 아니다.")
        raise SystemExit(2)


def share_table(title: str, agg: dict[str, float], total: float, top: int = 15) -> None:
    print(f"\n## {title}")
    print("| 항목 | 환산 비용($) | 비중 |")
    print("|---|--:|--:|")
    for k, v in sorted(agg.items(), key=lambda kv: -kv[1])[:top]:
        print(f"| {k} | {v:,.2f} | {v / total:.1%} |")


def agent_types(session_file: Path) -> dict[str, str]:
    """agentId -> subagent_type. 생략이면 결과의 agentType을 괄호로 붙인다."""
    uses: dict[str, str | None] = {}
    out: dict[str, str] = {}
    for d in lines(session_file):
        c = d.get("message", {}).get("content") if isinstance(d.get("message"), dict) else None
        if d.get("type") == "assistant" and isinstance(c, list):
            for b in c:
                if b.get("type") == "tool_use" and b.get("name") == "Agent":
                    uses[b["id"]] = b.get("input", {}).get("subagent_type")
        tur = d.get("toolUseResult")
        if (
            d.get("type") == "user"
            and isinstance(tur, dict)
            and tur.get("agentId")
            and isinstance(c, list)
        ):
            for b in c:
                tid = b.get("tool_use_id") if isinstance(b, dict) else None
                if tid in uses:
                    st = uses[tid] or f"(생략→{tur.get('agentType') or '?'})"
                    out[str(tur["agentId"])] = st
    return out


def cmd_split(hours: float) -> None:
    cutoff = cutoff_of(hours)
    seen: set[str] = set()
    by_kind: dict[str, float] = defaultdict(float)
    by_model: dict[str, float] = defaultdict(float)
    by_type: dict[str, float] = defaultdict(float)
    by_project: dict[str, float] = defaultdict(float)
    unknown = 0
    n = 0
    files = recent_files(hours)
    types: dict[str, str] = {}
    for parent in {p.parent.parent.with_suffix(".jsonl") for p in files if is_sub(p)}:
        if parent.is_file():
            types.update(agent_types(parent))
    for p in files:
        kind = "서브에이전트" if is_sub(p) else "메인 세션"
        sub_type = types.get(p.stem.removeprefix("agent-"), "(미상)") if is_sub(p) else ""
        for d, u in calls(p, seen, cutoff):
            model = str(d["message"].get("model"))
            c = costs.cost(model, costs.Usage.of(u))
            n += 1
            if c is None:
                unknown += 1
                continue
            effort = str(d.get("effort") or "(없음)")
            by_kind[kind] += c
            by_model[f"{kind} {model.removeprefix('claude-')} {effort}"] += c
            by_project[project_of(p)] += c
            if sub_type:
                by_type[sub_type] += c
    require(n - unknown, "단가표 안의 모델 호출")
    total = sum(by_kind.values()) or 1.0
    print(f"최근 {hours:g}시간, 모델 호출 {n:,}회(단가표 밖 {unknown}회), 환산 비용 ${total:,.2f}")
    share_table("메인 세션과 서브에이전트", by_kind, total)
    share_table("모델·노력", by_model, total)
    share_table("서브에이전트 유형(전체 비용 대비)", by_type, total)
    share_table("프로젝트", by_project, total, top=8)


def cmd_idle(hours: float) -> None:
    cutoff = cutoff_of(hours)
    seen: set[str] = set()
    buckets = [(0, 5), (5, 10), (10, 30), (30, 60), (60, 10**9)]
    stat: dict[int, list[int]] = {lo: [0, 0] for lo, _ in buckets}
    w5 = w1 = 0
    total = rewrite_cost = wake_cost = 0.0
    wakes: list[tuple[float, int, bool]] = []
    ci_launch = 0
    n = unknown = 0
    for p in recent_files(hours):
        if is_sub(p):
            continue
        prev: datetime | None = None
        waiting = False
        for d, u in calls(p, seen, cutoff):
            t = time_of(d)
            if t is None:  # 창으로 거른 `calls`가 이미 뺀다
                continue
            n += 1
            model = str(d["message"].get("model"))
            us = costs.Usage.of(u)
            priced = costs.cost(model, us)
            if priced is None:
                unknown += 1
            c = priced or 0.0
            total += c
            w5 += us.write_5m
            w1 += us.write_1h
            ctx = ctx_of(u)
            rewrote = (us.write_5m + us.write_1h) > ctx * 0.5
            if prev is not None and ctx > 50000:
                gap = (t - prev).total_seconds() / 60
                lo = max(b for b, _ in buckets if gap >= b)
                stat[lo][0] += 1
                if rewrote:
                    stat[lo][1] += 1
                    if lo == 60:
                        # 캐시 쓰기 몫만 단가표의 셈(`costs.cost`)으로 낸다.
                        writes_only = costs.Usage(
                            0, 0, 0, 0, us.write_5m, us.write_1h, thinking_known=False
                        )
                        rewrite_cost += costs.cost(model, writes_only) or 0.0
                if waiting and gap > 2:
                    wakes.append((gap, ctx, rewrote))
                    wake_cost += c
                    waiting = False
            prev = t
            for b in d["message"].get("content") or []:
                if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("name") == "Bash":
                    inp = b.get("input", {})
                    if "wait_ci" in str(inp.get("command", "")) and inp.get("run_in_background"):
                        waiting = True
                        ci_launch += 1
    require(n - unknown, "단가표 안의 메인 세션 모델 호출")
    require(ci_launch, "백그라운드로 띄운 wait_ci")
    print(
        f"최근 {hours:g}시간 메인 세션, 모델 호출 {n:,}회(단가표 밖 {unknown}회),"
        f" 환산 비용 ${total:,.2f}"
    )
    print(
        "\n| 직전 호출과의 간격 | 호출(세션 컨텍스트 5만 초과) | 절반 이상을 다시 쓴 호출 | 비율 |"
    )
    print("|---|--:|--:|--:|")
    for lo, hi in buckets:
        a, r = stat[lo]
        label = f"{lo}~{hi}분" if hi < 10**9 else f"{lo}분 이상"
        print(f"| {label} | {a:,} | {r:,} | {r / a if a else 0:.0%} |")
    print(f"\n캐시 쓰기 TTL: 5분 {w5:,} 토큰, 1시간 {w1:,} 토큰")
    print(
        f"60분 이상 쉰 뒤 다시 쓴 캐시 쓰기 비용: ${rewrite_cost:,.2f} ({rewrite_cost / total:.1%})"
    )
    print(f"\nwait_ci 백그라운드 실행 {ci_launch}회, 2분 넘게 쉬고 깨어난 호출 {len(wakes)}회")
    if wakes:
        gaps = sorted(g for g, _, _ in wakes)
        print(f"- 대기 중앙값 {statistics.median(gaps):.1f}분, 최대 {gaps[-1]:.1f}분")
        print(f"- 세션 컨텍스트 절반 이상을 다시 쓴 호출 {sum(1 for _, _, r in wakes if r)}회")
        print(f"- 깨어난 호출의 비용 ${wake_cost:,.2f} ({wake_cost / total:.2%})")


def _simulate(
    per_session: list[list[int]], threshold: int, summary: int, reread: int
) -> tuple[int, int]:
    """압축 지점이 threshold였다면 읽은 세션 컨텍스트 합과 압축 횟수.

    가정(어림): 호출마다 늘어난 양은 압축 뒤에도 같다. 압축 뒤 세션 컨텍스트는 시작 컨텍스트에
    요약(summary)과 다시 읽기(reread)를 더한 것이다. 압축 호출은 그때의 세션 컨텍스트를 한 번 더
    읽는다. 실제 기록에서 절반 아래로 줄어든 자리는 증가를 0으로 둔다.
    """
    total = comps = 0
    for ctxs in per_session:
        now = ctxs[0]
        total += now
        for prev, cur in zip(ctxs, ctxs[1:], strict=False):
            if cur >= prev * 0.5:
                now += max(cur - prev, 0)
            if now > threshold:
                total += now
                comps += 1
                now = ctxs[0] + summary + reread
            total += now
    return total, comps


def cmd_simulate(hours: float) -> None:
    """창 안에서 시작한 세션만 쓴다. 창 앞에서 시작한 세션은 창 안 첫 호출이 이미 커서, 그것을 시작
    컨텍스트로 두면 압축 뒤 값이 문턱을 넘어 호출마다 압축한 것으로 센다(PR 직전 버그 리뷰가
    짚었다). 절감률의 분모는 실제 합이 아니라 압축하지 않는 시뮬레이션의 합이다. 증가를 다시 쌓는
    셈과 실제 기록의 차이를 빼려는 것이다."""
    cutoff = cutoff_of(hours)
    seen: set[str] = set()
    per_session: list[list[int]] = []
    started_before = unreadable_start = 0
    for p in recent_files(hours):
        if is_sub(p):
            continue
        pairs = [(d, ctx_of(u)) for d, u in calls(p, seen, None)]
        pairs = [(d, c) for d, c in pairs if c > 0]
        if len(pairs) < 2:
            continue
        # `calls`는 cutoff가 없으면 시각을 읽지 않는다. 못 읽는 세션은 빼고 그 수를 적는다.
        start = time_of(pairs[0][0])
        if start is None:
            unreadable_start += 1
            continue
        if start < cutoff:
            started_before += 1
            continue
        per_session.append([c for _, c in pairs])
    require(len(per_session), "창 안에서 시작해 모델 호출이 둘 이상인 메인 세션")
    actual, _ = _simulate(per_session, 10**12, 20_000, 30_000)
    firsts = sorted(c[0] for c in per_session)
    print(
        f"최근 {hours:g}시간에 시작한 메인 세션 {len(per_session)}개"
        f"(창 앞에서 시작한 {started_before}개, 첫 호출의 시각을 못 읽은 {unreadable_start}개 뺌),"
        f" 압축하지 않을 때 읽는 합 {actual:,} 토큰"
    )
    q = statistics.quantiles(firsts, n=4)
    print(f"시작 컨텍스트: 중앙값 {statistics.median(firsts):,.0f}, 사분위 {q[0]:,.0f}~{q[2]:,.0f}")
    print("\n| 자동 압축 지점 | 압축 횟수 | 세션당 | 읽은 세션 컨텍스트 절감률 |")
    print("|--:|--:|--:|--:|")
    for t in (150_000, 200_000, 300_000, 400_000, 500_000):
        total, comps = _simulate(per_session, t, 20_000, 30_000)
        print(f"| {t:,} | {comps} | {comps / len(per_session):.1f} | {1 - total / actual:.0%} |")


def _first_input_kind(s: str) -> str:
    """압축 뒤 첫 user 기록의 출처. 사람이 친 글만 '사람'이고, 앱이 넣은 것은 그 출처로 가른다."""
    if s.startswith(("Base directory for this skill", "(Re-invocation of")):
        return "스킬 재주입"
    if s.startswith(("Another Claude session", "<cross-session")):
        return "세션 간 메시지"
    if s.startswith("<"):
        return "앱 알림"
    return "사람"


def cmd_compactions() -> None:
    """같은 압축이 포크한 세션 기록에 복사되므로 압축 경계 기록의 uuid로 한 번만 센다. 임시 폴더
    (`AppData-Local-Temp`)의 시험 세션은 뺀다."""
    rows = []
    boundaries: set[str] = set()
    kinds: Counter[str] = Counter()
    for p in ROOT.rglob("*.jsonl"):
        if is_sub(p) or "AppData-Local-Temp" in p.parent.name:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        if '"compact_boundary"' not in text:
            continue
        recs = [json.loads(x) for x in text.split("\n") if x.strip()]
        for i, d in enumerate(recs):
            if not (d.get("type") == "system" and d.get("subtype") == "compact_boundary"):
                continue
            if str(d.get("uuid")) in boundaries:
                continue
            boundaries.add(str(d.get("uuid")))
            meta = d.get("compactMetadata") or {}
            before: set[str] = set()
            for e in recs[:i]:
                for b in _blocks(e):
                    if b.get("type") == "tool_use" and b.get("name") == "Read":
                        before.add(_path_key(b))
            summary = 0
            first_ctx = 0
            n_calls = reads = rereads = 0
            human = ""
            ids: set[str] = set()
            for e in recs[i + 1 :]:
                if e.get("type") == "system" and e.get("subtype") == "compact_boundary":
                    break
                if e.get("isCompactSummary"):
                    summary = len(_text(e))
                    continue
                m = e.get("message") if isinstance(e.get("message"), dict) else {}
                if e.get("type") == "assistant" and isinstance(m.get("usage"), dict):
                    mid = str(m.get("id") or e.get("uuid"))
                    if mid not in ids and str(m.get("model")) != "<synthetic>":
                        ids.add(mid)
                        n_calls += 1
                        first_ctx = first_ctx or ctx_of(m["usage"])
                    if n_calls <= 30:
                        for b in _blocks(e):
                            if b.get("type") == "tool_use" and b.get("name") == "Read":
                                reads += 1
                                rereads += _path_key(b) in before
                elif e.get("type") == "user" and not human:
                    s = _text(e).strip()
                    skip = (
                        "<system",
                        "<task",
                        "<command",
                        "<local-command",
                        "[Request",
                        "This session is being continued",
                    )
                    if s and not s.startswith(skip):
                        human = f"[{_first_input_kind(s)}] " + re.sub(r"\s+", " ", s)[:50]
            kinds[human.split("]")[0].lstrip("[") if human else "없음"] += 1
            rows.append(
                (
                    p.parent.name[-26:],
                    p.stem[:8],
                    meta.get("trigger"),
                    meta.get("preTokens") or 0,
                    summary,
                    first_ctx,
                    n_calls,
                    reads,
                    rereads,
                    human,
                )
            )
    require(len(rows), "압축 경계")
    print(f"실제 압축 {len(rows)}건(압축 경계 uuid로 중복 제거, 임시 폴더의 시험 세션 제외)")
    print("압축 뒤 첫 입력의 출처: " + ", ".join(f"{k} {v}" for k, v in kinds.most_common()) + "\n")
    head = [
        "폴더/세션",
        "계기",
        "압축 전",
        "요약 글자",
        "압축 뒤 첫 세션 컨텍스트",
        "뒤 호출",
        "뒤 30호출 Read",
        "다시 읽기",
        "압축 뒤 첫 사람 입력",
    ]
    print("| " + " | ".join(head) + " |")
    print("|---|---|--:|--:|--:|--:|--:|--:|---|")
    for r in rows:
        cells = [f"{r[0]}/{r[1]}", str(r[2]), *(f"{x:,}" for x in r[3:6]), *map(str, r[6:])]
        print("| " + " | ".join(cells) + " |")


def _blocks(e: dict) -> list[dict]:
    m = e.get("message")
    c = m.get("content") if isinstance(m, dict) else None
    return [b for b in c if isinstance(b, dict)] if isinstance(c, list) else []


def _text(e: dict) -> str:
    m = e.get("message")
    c = m.get("content") if isinstance(m, dict) else None
    if isinstance(c, str):
        return c
    return " ".join(str(b.get("text", "")) for b in _blocks(e) if b.get("type") == "text")


def _path_key(b: dict) -> str:
    return str(b.get("input", {}).get("file_path", "")).replace("\\", "/").lower()


def _rlen(content: object) -> int:
    if isinstance(content, str):
        return len(content)
    if isinstance(content, list):
        return sum(
            len(str(b.get("text", "")))
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    return 0


def _user_kind(s: str) -> str:
    h = s.lstrip()[:40]
    for prefix, kind in (
        ("<task-notification", "알림"),
        ("<system-reminder", "시스템 알림"),
        ("<command-", "명령"),
    ):
        if h.startswith(prefix):
            return f"사용자 줄:{kind}"
    return "사용자 줄:사람 입력"


def _flush(
    items: list[tuple[str, int, int, str]],
    end: int,
    weight: dict[str, float],
    per_key: dict[str, float],
) -> None:
    """쌓인 항목마다 글자 수 × (end - 들어온 호출 번호)를 무게에 더하고 비운다."""
    for cat, n, start, key in items:
        w = n * max(end - start, 0)
        weight[cat] += w
        if key:
            per_key[key] += w
    items.clear()


def cmd_reads(hours: float) -> None:
    """무게 = 글자 수 × 그 항목이 들어온 뒤 실려 간 호출 수. 세션 컨텍스트가 직전의 절반 아래로 줄면
    거기서 끊는다."""
    cutoff = time.time() - hours * 3600
    weight: dict[str, float] = defaultdict(float)
    per_key: dict[str, float] = defaultdict(float)
    sessions = 0
    calls_n = 0
    seen_files: set[str] = set()
    for p in ROOT.rglob("*.jsonl"):
        if is_sub(p) or p.stat().st_mtime < cutoff or p.stem in seen_files:
            continue
        seen_files.add(p.stem)
        sessions += 1
        names: dict[str, tuple[str, str]] = {}
        pending: list[tuple[str, int, int, str]] = []
        idx = prev = 0
        ids: set[str] = set()
        for d in lines(p):
            t = d.get("type")
            m = d.get("message") if isinstance(d.get("message"), dict) else {}
            if t == "assistant":
                u = m.get("usage")
                mid = str(m.get("id") or d.get("uuid"))
                if isinstance(u, dict) and mid not in ids and str(m.get("model")) != "<synthetic>":
                    ids.add(mid)
                    idx += 1
                    c = ctx_of(u)
                    if prev > 100000 and c < prev * 0.5:
                        _flush(pending, idx, weight, per_key)
                    prev = c
                for b in _blocks(d):
                    bt = b.get("type")
                    if bt == "text":
                        pending.append(("모델 글", len(str(b.get("text", ""))), idx, ""))
                    elif bt == "tool_use":
                        nm = str(b.get("name"))
                        inp = b.get("input", {})
                        key = ""
                        if nm == "Read":
                            key = (
                                "Read "
                                + str(inp.get("file_path", ""))
                                .replace("\\", "/")
                                .split("/worktrees/")[-1]
                            )
                        elif nm == "Bash":
                            key = "Bash " + re.sub(r"\s+", " ", str(inp.get("command", "")))[:70]
                        names[b["id"]] = (nm, key)
                        pending.append(
                            (f"도구 입력:{nm}", len(json.dumps(inp, ensure_ascii=False)), idx, "")
                        )
            elif t == "user":
                c = m.get("content")
                if isinstance(c, str):
                    pending.append((_user_kind(c), len(c), idx, ""))
                for b in _blocks(d):
                    if b.get("type") == "tool_result":
                        nm, key = names.get(b.get("tool_use_id"), ("?", ""))
                        pending.append((f"도구 결과:{nm}", _rlen(b.get("content")), idx, key))
                    elif b.get("type") == "text":
                        s = str(b.get("text", ""))
                        pending.append((_user_kind(s), len(s), idx, ""))
            elif t == "attachment":
                a = d.get("attachment")
                at = a.get("type") if isinstance(a, dict) else "?"
                if at != "prompt_snapshot":
                    pending.append((f"첨부:{at}", len(json.dumps(a, ensure_ascii=False)), idx, ""))
        _flush(pending, idx + 1, weight, per_key)
        calls_n += idx
    require(calls_n, "메인 세션의 모델 호출")
    total = sum(weight.values()) or 1.0
    print(f"최근 {hours:g}시간 메인 세션 {sessions}개, 모델 호출 {calls_n:,}회")
    print("(prompt_snapshot 첨부는 모델로 가지 않는 진단 기록으로 보고 뺐다)")
    print("\n| 구성 요소 | 무게 비중 |")
    print("|---|--:|")
    for k, v in sorted(weight.items(), key=lambda kv: -kv[1])[:16]:
        print(f"| {k} | {v / total:.1%} |")
    print("\n무게가 큰 Read 파일과 Bash 명령:")
    for k, v in sorted(per_key.items(), key=lambda kv: -kv[1])[:12]:
        print(f"- {v / total:.2%} {k[-100:]}")


def _skill_source(name: str) -> str:
    """`플러그인:스킬`이면 플러그인 이름, 워크트리 경로가 붙은 프로젝트 스킬과 접두 없는 것은 한
    묶음."""
    if ":" in name and not name.startswith(".claude"):
        return name.split(":")[0]
    return "(프로젝트·내장)"


def cmd_plugins(hours: float) -> None:
    cut = time.time() - hours * 3600
    mcp: Counter[str] = Counter()
    skills: Counter[str] = Counter()
    # 창 안에서 가장 큰 첫 스킬 목록(세션, 판, 본문). 다른 세션이 시험으로 띄운 헤드리스 세션은
    # 목록이 짧아(2026-10-15 이 하위 명령의 첫 판이 가장 최근 것을 집어 스킬 11개, 5,310자를 찍었다)
    # 가장 최근 것은 대표값이 아니다.
    largest: tuple[str, str, str] = ("", "", "")
    files = 0
    # 같은 세션 기록이 폴더 둘에 겹쳐 있어 도구 호출은 ID로 한 번만 센다.
    tool_ids: set[str] = set()
    for folder in ROOT.iterdir():
        if not folder.is_dir() or not is_repo_folder(folder.name):
            continue
        for p in folder.rglob("*.jsonl"):
            if p.stat().st_mtime < cut:
                continue
            files += 1
            for d in lines(p):
                if d.get("type") == "attachment":
                    a = d.get("attachment")
                    # 추가분(isInitial 거짓)이 아니라 메인 세션에 처음 실린 목록만 견준다.
                    if (
                        isinstance(a, dict)
                        and a.get("type") == "skill_listing"
                        and a.get("isInitial") is True
                        and not is_sub(p)
                        and len(str(a.get("content", ""))) > len(largest[2])
                    ):
                        largest = (p.stem[:8], str(d.get("version")), str(a.get("content", "")))
                for b in _blocks(d):
                    if b.get("type") != "tool_use" or str(b.get("id")) in tool_ids:
                        continue
                    tool_ids.add(str(b.get("id")))
                    n = str(b.get("name"))
                    if n.startswith("mcp__"):
                        mcp[n.split("__")[1]] += 1
                    elif n == "Skill":
                        skills[_skill_source(str(b.get("input", {}).get("skill")))] += 1
    require(files, "이 저장소의 세션 기록")
    require(sum(skills.values()), "Skill 호출")
    require(len(largest[2]), "메인 세션의 첫 스킬 목록")
    print(f"최근 {hours:g}시간 이 저장소 기록 {files}개")
    print("\n스킬 호출(플러그인 이름 또는 프로젝트·내장):")
    for k, v in skills.most_common():
        print(f"- {k}: {v}")
    print("\nMCP 서버 호출:")
    for k, v in mcp.most_common():
        print(f"- {k}: {v}")
    groups: dict[str, int] = defaultdict(int)
    for ln in largest[2].splitlines():
        m = re.match(r"^- ([\w.-]+):[\w.-]+:", ln)
        groups[m.group(1) if m else "(내장·프로젝트·사용자)"] += len(ln) + 1
    print(
        f"\n가장 큰 첫 스킬 목록(세션 {largest[0]}, 판 {largest[1]}) {len(largest[2]):,}자, 출처별:"
    )
    for k, v in sorted(groups.items(), key=lambda kv: -kv[1]):
        print(f"- {k}: {v:,}자")


def cmd_rereads(hours: float) -> None:
    """같은 세션에서 바뀌지 않은 파일을 다시 읽은 Read를 센다.

    다시 읽기 후보: 같은 경로를 같은 범위(offset, limit)로, 또는 전체를 이미 읽었는데 다시 읽은 것.
    그 사이에 Edit·Write·NotebookEdit로 그 파일을 고쳤거나, 압축이 있었거나, 작업 트리를 바꾸는 git
    명령 (pull, merge, checkout 등)이 돌았으면 세지 않는다. 낭비라는 판정이 아니다. 긴 세션
    컨텍스트에서 앞의 내용을 정확히 짚으려고 다시 읽는 것도 여기 든다. git 밖의 Bash(sed,
    스크립트)로 바뀐 파일은 보지 못해 후보를 많게 셀 수 있다.
    """
    cut = time.time() - hours * 3600
    total = dup = reads = dups = git_resets = 0
    by_file: dict[str, int] = defaultdict(int)
    done: set[str] = set()
    for p in ROOT.rglob("*.jsonl"):
        if is_sub(p) or p.stat().st_mtime < cut or p.stem in done:
            continue
        done.add(p.stem)
        seen: dict[str, set[tuple[object, object]]] = defaultdict(set)
        pending: dict[str, tuple[str, tuple[object, object], bool]] = {}
        for d in lines(p):
            if d.get("type") == "system" and d.get("subtype") == "compact_boundary":
                seen.clear()
            for b in _blocks(d):
                if b.get("type") == "tool_use":
                    name = str(b.get("name"))
                    key = _path_key(b)
                    if name in ("Edit", "Write", "NotebookEdit", "MultiEdit"):
                        seen.pop(key, None)
                    elif name in ("Bash", "PowerShell") and GIT_MUTATION.search(
                        str(b.get("input", {}).get("command", ""))
                    ):
                        git_resets += 1
                        seen.clear()
                    elif name == "Read":
                        inp = b.get("input", {})
                        rng = (inp.get("offset"), inp.get("limit"))
                        again = rng in seen[key] or (None, None) in seen[key]
                        pending[b["id"]] = (key, rng, again)
                elif b.get("type") == "tool_result" and b.get("tool_use_id") in pending:
                    key, rng, again = pending.pop(b["tool_use_id"])
                    n = _rlen(b.get("content"))
                    reads += 1
                    total += n
                    if again:
                        dups += 1
                        dup += n
                        by_file[key.split("/worktrees/")[-1]] += n
                    seen[key].add(rng)
    require(reads, "메인 세션의 Read 결과")
    print(f"최근 {hours:g}시간 메인 세션 {len(done)}개, Read {reads:,}회 {total:,}자")
    print(f"작업 트리를 바꾸는 git 명령 {git_resets:,}회(그 뒤의 읽기는 후보에서 뺐다)")
    print(f"다시 읽기 후보 {dups:,}회 {dup:,}자 (Read 글자의 {dup / (total or 1):.1%})")
    print("\n다시 읽은 글자가 많은 파일:")
    for k, v in sorted(by_file.items(), key=lambda kv: -kv[1])[:10]:
        print(f"- {v:,}자 {k[-90:]}")


def main(argv: list[str]) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if not argv:
        raise SystemExit(__doc__)
    print(f"실행 시각 {datetime.now(UTC):%Y-%m-%dT%H:%MZ}, 기록 {ROOT}")
    cmd, rest = argv[0], argv[1:]
    if cmd == "compactions":
        cmd_compactions()
        return
    handlers = {
        "split": cmd_split,
        "idle": cmd_idle,
        "simulate": cmd_simulate,
        "reads": cmd_reads,
        "plugins": cmd_plugins,
        "rereads": cmd_rereads,
    }
    if cmd not in handlers or len(rest) != 1:
        raise SystemExit(__doc__)
    handlers[cmd](float(rest[0]))


if __name__ == "__main__":
    main(sys.argv[1:])
