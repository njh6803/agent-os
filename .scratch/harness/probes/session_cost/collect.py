"""지난 트랜스크립트와 `gh`·`git`을 읽어 브랜치마다 비용·시간·재작업·사전 지표 한 행을
`branches.json`에 쓴다.

정의(비용, 귀속, 시간, 재작업, 사전 지표)는 같은 디렉터리의 README가 원천이고, 여기는 그 구현이다.
이 파일이 기대는 기록의 모양은 2026-10-12~13에 이 PC의 `~/.claude/projects/` 기록을 스크래치
스크립트로 훑어 손으로 본 것이다(Claude Code 2.1.237~2.1.296, 데스크톱 앱).

- 응답 하나는 내용 블록마다 `assistant` 기록 한 줄이고 같은 `message.id`를 든다. usage는 조각마다
  실리며 입력과 캐시는 같고 출력은 뒤 조각이 크다. 그래서 `message.id`로 묶어 출력이 가장 큰 조각을
  센다.
- 서브에이전트 기록(`<세션>/subagents/agent-*.jsonl`)은 대부분 스트림 시작의 usage만
  남아(`stop_reason`이 비고 출력이 한 자리 수) 출력 토큰이 빠진다. 입력과 캐시는 맞다. 그런 응답의
  수를 `sub_partial`로 센다.
- 세션 하나가 여러 프로젝트 폴더에 다시 실린다(워크트리로 옮긴 세션, 포크). 본 세션 기록은 `uuid`로,
  응답은 `message.id`로 한 번만 센다.
- 사람이 친 메시지는 `origin.kind`가 `human`이다. 작업 알림·다른 세션의 메시지·SDK로 띄운 실행은
  다른 값이거나 `promptSource`가 `sdk`다. `origin`이 없는 옛 기록 가운데 중단
  표지(`[Request interrupted`)와 작업 알림은 글의 머리로 가른다.
- Claude Code가 세션마다 남긴 `cost-state` 기록은 서브에이전트와 컴팩션까지 든 모델별 토큰과
  금액이다. 프로세스가 끝날 때 쓰여 다시 시작한 세션은 뒤 프로세스의 몫만 든다. 단가표
  대조(`price_check`)와 기록 기반 비용의 몫 (`cost_state_ratio`)을 재는 데만 쓴다.

양성 대조 둘. 단가표로 셈한 모델별 금액이 `cost-state`의 금액을 5분·1시간 캐시 쓰기의 두 끝 사이에
담는지, 그리고 드물게 남은 `turn_duration` 기록(Claude Code가 잰 턴 시간)이 이 파일이 잰 턴 시간과
맞는지 찍는다.

레벨 스윕(`../model_sweep/`)을 위해 둘을 더 남긴다. 브랜치의 첫 사람 트리거
시각(`first_human_at`)과, 그 트리거가 지시문이면 줄 머리의 `모델:`·`브랜치:` 줄
값(`directive_features`의 `model_line`·`branch_line`, 줄 값 그대로)이다. `--since`는 집계의 창이다.
기록은 창과 관계없이 모두 읽어 턴·귀속과 브랜치의 첫 사람 트리거(그 시각과 지시문)를 정하고, 비용,
턴과 개입, meta의 표지는 창 안의 응답과 창 안에서 시작한 턴으로만 셈한다. 그래서 창 앞에서 시작한
브랜치는 첫 트리거가 창 앞이고 비용은 창 안 몫만 든다. 창 안의 판정, 첫 사람 트리거, 첫 지시문,
사람 개입, 남길 `cost-state` 세션은 `tools/session_cost_window.py`의 순수 함수가 정하고
`tests/tools/`의 pytest가 고정한다. 이 파일은 기록을 읽고 턴을 지어 그 함수에 넘기고, 턴과 응답을
어느 시각으로 창에 거는지(그 도구의 독스트링)를 맡는다. 예외는 시각이 없는 `cost-state`다. 창 안에
기록이 있는 세션의 것만 남기지만 그 세션의 창 앞 몫까지 들어, 단가 대조와 `cost_state_ratio`는 창
앞의 몫이 섞인다(그 비의 분자인 세션 비용도 세션 전체로 셈한다). 단가 대조는 한 기록 안의 토큰과
금액을 대 보는 것이라 그래도 어긋나지 않는다.
meta에는 `since`와 이 파일의 SHA-256(`collect_sha256`), 창 도구 `tools/session_cost_window.py`의
SHA-256(`window_sha256`)을 남겨, 판정 스크립트가 어느 창을 어느 판으로 모았는지 본다. 단가표
`costs.py`의 해시는 남기지 않는다.

돌리는 법은 README. 종료 코드: 0 썼다, 2 `gh`·`git`을 부르지 못했다.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from costs import Json, Usage, cost, cost_state_bounds

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[3]))
from tools import session_cost_window as window  # noqa: E402

PROJECTS = Path.home() / ".claude" / "projects"
PROJECT_PREFIX = "C--project-agent"

DIRECTIVE_MARK = window.DIRECTIVE_MARK
INTERRUPT_MARK = "[Request interrupted"
COMPACT_MARK = "This session is being continued"
HOOK_BLOCK = re.compile(r"hook error|PreToolUse:\w+ hook", re.IGNORECASE)
RATE_LIMIT_NOTICE = re.compile(
    r"rate limited|Review limit reached|Action not completed", re.IGNORECASE
)
SEVERITY = re.compile(
    r"\[(Critical|Major|Minor|Nit)\]|(?:🔴|🟠|🟡|🔵)\s*(Critical|Major|Minor|Trivial)",
    re.IGNORECASE,
)
DIAG_SKILL = "diagnosing-bugs"
CI_WORKFLOW = "ci"
REVERT = re.compile(r"revert|되돌", re.IGNORECASE)
SQUASH_NUMBER = re.compile(r"\(#(\d+)\)\s*$")


def squash_number(subject: str) -> int | None:
    """squash 병합 커밋 제목 끝의 `(#M)`."""
    m = SQUASH_NUMBER.search(subject)
    return int(m.group(1)) if m else None


def run(cmd: list[str], cwd: Path | None = None) -> str:
    out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if out.returncode != 0:
        raise RuntimeError(
            f"{' '.join(cmd[:4])} … 가 {out.returncode}로 끝났다: {out.stderr.strip()[:300]}"
        )
    return out.stdout


parse_ts = window.parse_ts


def seconds(a: str, b: str) -> float:
    return max(0.0, (parse_ts(b) - parse_ts(a)).total_seconds())


def norm(path: str) -> str:
    return path.replace("\\", "/").rstrip("/").lower()


# --- gh ---------------------------------------------------------------------------------------

PR_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    pullRequests(first: 20, after: $cursor, orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number title body state createdAt mergedAt headRefName baseRefName
        changedFiles additions deletions
        author { login }
        commits(first: 100) { totalCount nodes { commit {
          oid committedDate messageHeadline parents(first: 2) { totalCount nodes { oid } } } } }
        comments(first: 100) { totalCount nodes { author { login } createdAt body } }
        reviews(first: 100) { totalCount nodes { author { login } createdAt body state } }
        reviewThreads(first: 100) { totalCount nodes { comments(first: 50) {
          nodes { author { login } createdAt body } } } }
      }
    }
  }
}
"""


def fetch_prs(owner: str, name: str) -> list[Json]:
    nodes: list[Json] = []
    cursor: str | None = None
    while True:
        cmd = ["gh", "api", "graphql", "-f", f"query={PR_QUERY}", "-F", f"owner={owner}", "-F"]
        cmd += [f"name={name}"]
        if cursor:
            cmd += ["-F", f"cursor={cursor}"]
        page = json.loads(run(cmd))
        conn = page["data"]["repository"]["pullRequests"]
        nodes.extend(conn["nodes"])
        if not conn["pageInfo"]["hasNextPage"]:
            return nodes
        cursor = conn["pageInfo"]["endCursor"]


def load_gh(cache: Path, *, refresh: bool) -> tuple[list[dict[str, Json]], list[dict[str, Json]]]:
    cache.mkdir(parents=True, exist_ok=True)
    prs_path, runs_path = cache / "prs.json", cache / "runs.json"
    if refresh or not prs_path.exists():
        repo = json.loads(run(["gh", "repo", "view", "--json", "owner,name"]))
        prs_path.write_text(
            json.dumps(fetch_prs(repo["owner"]["login"], repo["name"]), ensure_ascii=False),
            encoding="utf-8",
        )
    if refresh or not runs_path.exists():
        fields = "databaseId,headBranch,conclusion,event,workflowName,createdAt"
        runs_path.write_text(
            run(["gh", "run", "list", "--limit", "5000", "--json", fields]), encoding="utf-8"
        )
    return (
        json.loads(prs_path.read_text(encoding="utf-8")),
        json.loads(runs_path.read_text(encoding="utf-8")),
    )


# --- 트랜스크립트 ---------------------------------------------------------------------------------


@dataclass
class Rec:
    """본 세션의 기록 하나. 귀속과 턴 시간에 드는 것만 든다."""

    ts: str
    kind: str  # assistant | trigger | result | other
    branch: str
    in_repo: bool
    msg_id: str = ""
    tool_uses: list[tuple[str, str, str]] = field(default_factory=list)  # (id, 이름, 스킬)
    trigger: str = ""  # human | auto | interrupt
    text: str = ""
    results: list[tuple[str, bool, bool]] = field(default_factory=list)  # (id, 오류, 훅 막음)
    denial: str = ""
    turn_duration_ms: int = 0
    queued_human: bool = False  # 턴 도중에 사람이 친 메시지(`queued_command` 첨부). 트리거가 아니다


@dataclass
class Msg:
    session: str
    model: str
    effort: str
    entry: str
    usage: Usage
    ts: str
    branch: str
    in_repo: bool
    sub: bool
    final: bool


def _text_of(content: Json) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(b.get("text", ""))
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    return ""


def _result_text(block: dict[str, Json]) -> str:
    c = block.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "\n".join(str(x.get("text", "")) for x in c if isinstance(x, dict))
    return ""


def classify_trigger(o: dict[str, Json], text: str) -> str:
    """사람(human), 자동(auto), 중단(interrupt). 컴팩션 요약은 트리거가 아니다(빈 문자열)."""
    if o.get("isCompactSummary") or text.startswith(COMPACT_MARK):
        return ""
    if text.startswith(INTERRUPT_MARK):
        return "interrupt"
    origin = o.get("origin")
    if isinstance(origin, dict):
        return "human" if origin.get("kind") == "human" else "auto"
    if o.get("promptSource") == "sdk" or o.get("turnOrigin") == "sdk":
        return "auto"
    if text.lstrip().startswith("<task-notification>"):
        return "auto"
    return "human"


@dataclass
class Scan:
    recs: dict[str, list[Rec]] = field(default_factory=lambda: defaultdict(list))
    msgs: dict[str, Msg] = field(default_factory=dict)
    cost_state: dict[str, dict[str, Json]] = field(default_factory=dict)
    no_usage: dict[str, str] = field(default_factory=dict)  # usage 없는 응답의 id: 시각
    synthetic: int = 0
    unknown_models: Counter[str] = field(default_factory=Counter)
    first_ts: str = ""
    last_ts: str = ""
    since: datetime | None = None  # 집계의 창(`--since`). 기록은 창과 관계없이 모두 읽는다

    def in_window(self, ts: str) -> bool:
        return window.in_window(ts, self.since)


def scan(projects: Path, root: str, since: datetime | None = None) -> Scan:
    s = Scan(since=since)
    seen_uuid: set[str] = set()
    dirs = sorted(p for p in projects.iterdir() if p.is_dir() and p.name.startswith(PROJECT_PREFIX))
    for d in dirs:
        for f in sorted(d.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime):
            _scan_file(s, f, sub="subagents" in f.parts, root=root, seen_uuid=seen_uuid)
    for recs in s.recs.values():
        recs.sort(key=lambda r: r.ts)
    # `cost-state`에는 시각이 없다. 창 안에 기록이 있는 세션의 것만 단가 대조와 몫에 남긴다. 창
    # 앞에서 시작한 세션의 것은 창 앞의 몫까지 들지만, 단가 대조는 한 기록 안의 토큰과 금액을 대
    # 보는 것이라 그 몫이 섞여도 어긋나지 않는다.
    if since is not None:
        stamps: dict[str, list[str]] = defaultdict(list)
        for sid, recs in s.recs.items():
            stamps[sid].extend(r.ts for r in recs)
        for m in s.msgs.values():
            stamps[m.session].append(m.ts)
        live = window.cost_state_sessions(s.cost_state, stamps, since)
        s.cost_state = {sid: cs for sid, cs in s.cost_state.items() if sid in live}
    return s


def _scan_file(s: Scan, f: Path, *, sub: bool, root: str, seen_uuid: set[str]) -> None:
    with f.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                o = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(o, dict):
                continue
            _scan_record(s, o, sub=sub, root=root, seen_uuid=seen_uuid)


def _scan_queued(
    s: Scan, o: dict[str, Json], sid: str, ts: str, root: str, seen_uuid: set[str]
) -> None:
    """턴 도중에 사람이 친 메시지는 `user` 기록 없이 `queued_command` 첨부로만 남기도
    한다(2026-10-13 기록을 손으로
    봤다: 사람이 친 것으로 보이는 31건 가운데 26건). 사전 등록의 트리거가 아니어서 사람 개입에 넣지
    않고 탐색 칸으로 센다."""
    a = o.get("attachment")
    if not isinstance(a, dict) or a.get("type") != "queued_command":
        return
    origin = a.get("origin")
    if not isinstance(origin, dict) or origin.get("kind") != "human":
        return
    uuid = o.get("uuid")
    if isinstance(uuid, str):
        if uuid in seen_uuid:
            return
        seen_uuid.add(uuid)
    cwd = norm(str(o.get("cwd") or ""))
    in_repo = cwd == root or cwd.startswith(root + "/")
    branch = str(o.get("gitBranch") or "")
    s.recs[sid].append(Rec(ts=ts, kind="other", branch=branch, in_repo=in_repo, queued_human=True))


def _scan_record(s: Scan, o: dict[str, Json], *, sub: bool, root: str, seen_uuid: set[str]) -> None:
    t = o.get("type")
    sid = o.get("sessionId")
    if t == "cost-state" and isinstance(sid, str):
        prev = s.cost_state.get(sid)
        total = o.get("totalCostUSD")
        if isinstance(total, float | int) and (
            prev is None or total >= float(str(prev.get("totalCostUSD", 0)))
        ):
            s.cost_state[sid] = o
        return
    ts = o.get("timestamp")
    if t == "attachment" and not sub and isinstance(sid, str) and isinstance(ts, str):
        _scan_queued(s, o, sid, ts, root, seen_uuid)
        return
    if (
        t not in ("assistant", "user", "system")
        or not isinstance(sid, str)
        or not isinstance(ts, str)
    ):
        return
    cwd = norm(str(o.get("cwd") or ""))
    in_repo = cwd == root or cwd.startswith(root + "/")
    branch = str(o.get("gitBranch") or "")
    if in_repo and s.in_window(ts):
        s.first_ts = ts if not s.first_ts or ts < s.first_ts else s.first_ts
        s.last_ts = ts if ts > s.last_ts else s.last_ts
    if t == "assistant":
        _scan_assistant(s, o, sid, ts, branch, in_repo=in_repo, sub=sub)
    if sub:
        return
    uuid = o.get("uuid")
    if isinstance(uuid, str):
        if uuid in seen_uuid:
            return
        seen_uuid.add(uuid)
    rec = Rec(ts=ts, kind="other", branch=branch, in_repo=in_repo)
    msg = o.get("message")
    if t == "assistant" and isinstance(msg, dict):
        rec.kind = "assistant"
        rec.msg_id = str(msg.get("id") or o.get("requestId") or "")
        content = msg.get("content")
        for b in content if isinstance(content, list) else []:
            if isinstance(b, dict) and b.get("type") == "tool_use":
                inp = b.get("input")
                skill = str(inp.get("skill", "")) if isinstance(inp, dict) else ""
                rec.tool_uses.append((str(b.get("id")), str(b.get("name")), skill))
    elif t == "user" and isinstance(msg, dict):
        content = msg.get("content")
        blocks = [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []
        results = [b for b in blocks if b.get("type") == "tool_result"]
        if results:
            rec.kind = "result"
            for b in results:
                err = bool(b.get("is_error"))
                rec.results.append(
                    (
                        str(b.get("tool_use_id")),
                        err,
                        err and bool(HOOK_BLOCK.search(_result_text(b))),
                    )
                )
            rec.denial = str(o.get("toolDenialKind") or "")
        elif not o.get("isMeta"):
            text = _text_of(content)
            kind = classify_trigger(o, text)
            if kind:
                rec.kind = "trigger"
                rec.trigger = kind
                rec.text = text[:20000] if kind == "human" else ""
    elif t == "system" and o.get("subtype") == "turn_duration":
        d = o.get("durationMs")
        rec.turn_duration_ms = d if isinstance(d, int) else 0
    s.recs[sid].append(rec)


def _scan_assistant(
    s: Scan, o: dict[str, Json], sid: str, ts: str, branch: str, *, in_repo: bool, sub: bool
) -> None:
    msg = o.get("message")
    if not isinstance(msg, dict):
        return
    model = str(msg.get("model") or "")
    if model == "<synthetic>":
        s.synthetic += 1 if s.in_window(ts) else 0
        return
    u = msg.get("usage")
    mid = str(msg.get("id") or o.get("requestId") or "")
    if not isinstance(u, dict) or not mid:
        if in_repo:
            s.no_usage.setdefault(mid or str(o.get("uuid")), ts)
        return
    usage = Usage.of(u)
    final = msg.get("stop_reason") is not None
    old = s.msgs.get(mid)
    if old is None:
        if cost(model, usage) is None and s.in_window(ts):
            s.unknown_models[model] += 1
        s.msgs[mid] = Msg(
            session=sid,
            model=model,
            effort=str(o.get("effort") or ""),
            entry=str(o.get("entrypoint") or ""),
            usage=usage,
            ts=ts,
            branch=branch,
            in_repo=in_repo,
            sub=sub,
            final=final,
        )
    elif usage.output > old.usage.output or (final and not old.final):
        old.usage = usage if usage.output >= old.usage.output else old.usage
        old.final = old.final or final


# --- 턴과 귀속 ------------------------------------------------------------------------------------


@dataclass
class Turn:
    start: str
    end: str
    trigger: str
    recs: list[Rec]
    branch: str = ""


def turns_of(recs: list[Rec]) -> list[Turn]:
    turns: list[Turn] = []
    for r in recs:
        if not r.in_repo:
            continue
        if r.kind == "trigger" or not turns:
            turns.append(Turn(start=r.ts, end=r.ts, trigger=r.trigger or "start", recs=[r]))
        else:
            turns[-1].recs.append(r)
            turns[-1].end = r.ts
    return turns


def assign_branches(turns: list[Turn], pr_branches: set[str]) -> None:
    for t in turns:
        t.branch = next((r.branch for r in t.recs if r.branch in pr_branches), "")
    known = [i for i, t in enumerate(turns) if t.branch]
    for i, t in enumerate(turns):
        if t.branch or not known:
            continue
        after = [k for k in known if k > i]
        t.branch = (
            turns[after[0]].branch if after else turns[[k for k in known if k < i][-1]].branch
        )


def union_seconds(intervals: list[tuple[datetime, datetime]]) -> float:
    total = 0.0
    cur_s: datetime | None = None
    cur_e: datetime | None = None
    for a, b in sorted(intervals):
        if cur_e is None or a > cur_e:
            if cur_s is not None and cur_e is not None:
                total += (cur_e - cur_s).total_seconds()
            cur_s, cur_e = a, b
        elif b > cur_e:
            cur_e = b
    if cur_s is not None and cur_e is not None:
        total += (cur_e - cur_s).total_seconds()
    return total


def turn_times(t: Turn) -> tuple[float, float, float]:
    """트리거부터 마지막 기록까지, 도구 시간, 사람 대기(`AskUserQuestion`) 초. 턴 시간은 첫째에서
    셋째를 뺀 것이다."""
    start, end = parse_ts(t.start), parse_ts(t.end)
    began: dict[str, tuple[datetime, str]] = {}
    tool: list[tuple[datetime, datetime]] = []
    wait: list[tuple[datetime, datetime]] = []
    for r in t.recs:
        for tid, name, _ in r.tool_uses:
            began.setdefault(tid, (parse_ts(r.ts), name))
        for tid, _, _ in r.results:
            if tid in began:
                a, name = began.pop(tid)
                span = (max(a, start), min(parse_ts(r.ts), end))
                if span[1] > span[0]:
                    (wait if name == "AskUserQuestion" else tool).append(span)
    whole = max(0.0, (end - start).total_seconds())
    return whole, union_seconds(tool), union_seconds(wait)


# --- 사전 지표 ------------------------------------------------------------------------------------

CRITERION = re.compile(r"^\s*- \[[ xX]\]")
BY_COMMAND = ("테스트", "test_", "uv run", "pnpm", "pytest", "검증 명령")
OPEN_PHRASE = re.compile(r"이 티켓이 \S*(짓|정하|정한|정할|고르|판정)")
CONTRACT_WORDS = ("sdk/", "openapi.json", "헌법", "docs/constitution")
# 사전 등록의 "이름으로 든 층": 층의 이름이 낱말로 나온 것. `main`·`http`는 브랜치나 주소의 낱말과
# 섞이지만 정의를 넓히지 않는다(탐색 지표다).
LAYERS = ("sdk", "core", "channel", "admin", "adapters", "http", "server", "main", "web")
LAYER_WORD = {name: re.compile(rf"(?<![A-Za-z0-9_-]){name}(?![A-Za-z0-9_-])") for name in LAYERS}
OPEN_TITLE = re.compile(r"조사|설계|탐색|검토|고른다|정한다|측정|잰다")
LIST_ITEM = re.compile(r"^\s*(?:\d+\.|[-*])\s+")
HEADING = re.compile(r"^#{1,6}\s")
BACKTICK_PATH = re.compile(r"`([^`\s]+\.[A-Za-z][A-Za-z0-9]{0,4})`")


def open_decisions(text: str) -> int:
    n = 0
    in_section = False
    for line in text.splitlines():
        if HEADING.match(line):
            in_section = "정할 것" in line
            continue
        if in_section:
            n += 1 if LIST_ITEM.match(line) else 0
        else:
            n += len(OPEN_PHRASE.findall(line))
    return n


def common_features(text: str) -> dict[str, Json]:
    return {
        "chars": len(text),
        "contract": any(w in text for w in CONTRACT_WORDS),
        "layers": sum(1 for p in LAYER_WORD.values() if p.search(text)),
        "files": len(set(BACKTICK_PATH.findall(text))),
        "adr_refs": len(set(re.findall(r"ADR\s*(\d{4})", text))),
    }


def ticket_features(text: str, filename: str) -> dict[str, Json]:
    lines = text.splitlines()
    criteria = [ln for ln in lines if CRITERION.match(ln)]
    by_cmd = [ln for ln in criteria if any(w in ln for w in BY_COMMAND)]
    blocked = next((ln for ln in lines if ln.startswith("**Blocked by:**")), "")
    title = next((ln for ln in lines if ln.startswith("# ")), "")
    feats = common_features(text)
    feats["contract"] = bool(feats["contract"]) or "contract" in filename
    feats.update(
        {
            "criteria": len(criteria),
            "cmd_share": round(len(by_cmd) / len(criteria), 3) if criteria else None,
            "open_decisions": open_decisions(text),
            "blocked_by": len(re.findall(r"\b\d{2}\b", blocked.split("(", 1)[0])),
            "title_open": bool(OPEN_TITLE.search(title)),
            "first_ticket": filename.startswith("01-"),
        }
    )
    return feats


def directive_line(text: str, label: str) -> str | None:
    """지시문의 줄 머리 `<label>:` 줄의 값. 지시문이 아니거나 그 줄이 없으면 None.

    레벨 스윕의 모집단(`모델:` 줄의 표지)과 배정(`브랜치:` 줄)을 세는 데 쓴다(스윕 프로브의 사전
    등록). 값을 감싼 백틱은 벗긴다."""
    if DIRECTIVE_MARK not in text:
        return None
    m = re.search(rf"^{label}:[ \t]*(.*?)[ \t]*$", text, re.MULTILINE)
    return m.group(1).strip("`") if m else None


def directive_features(text: str) -> dict[str, Json]:
    feats = common_features(text)
    read = re.search(r"읽을 것:\s*(.+)", text)
    carry = re.search(r"이어받을 상태:\s*(.+)", text)
    feats.update(
        {
            "directive": DIRECTIVE_MARK in text,
            "model_line": directive_line(text, "모델"),
            "branch_line": directive_line(text, "브랜치"),
            "read_refs": len(re.findall(r"[\w./-]+\.(?:md|py|ps1|toml|json)", read.group(1)))
            if read
            else 0,
            "carry_chars": len(carry.group(1)) if carry and carry.group(1).strip() != "없음" else 0,
        }
    )
    return feats


def kind_of(branch: str) -> str:
    head, _, rest = branch.partition("/")
    if head == "feature":
        return "구현"
    if head in ("chore", "claude"):
        return "하네스"
    if head == "fix":
        return "수정"
    if head == "docs":
        if rest.endswith("-spec"):
            return "명세"
        if rest.endswith("-tickets"):
            return "티켓"
        if "design" in rest:
            return "디자인"
        return "문서"
    return "기타"


# --- git ------------------------------------------------------------------------------------------


class Git:
    def __init__(self, repo: Path) -> None:
        self.repo = repo
        self._trees: dict[str, list[str]] = {}

    def has(self, oid: str) -> bool:
        r = subprocess.run(
            ["git", "cat-file", "-e", f"{oid}^{{commit}}"], cwd=self.repo, capture_output=True
        )
        return r.returncode == 0

    def main_before(self, iso: str) -> str:
        return run(["git", "rev-list", "-1", f"--before={iso}", "origin/main"], self.repo).strip()

    def ticket_at(self, base: str, name: str) -> tuple[str, str] | None:
        if base not in self._trees:
            out = run(["git", "ls-tree", "-r", "--name-only", base, "--", ".scratch"], self.repo)
            self._trees[base] = out.splitlines()
        path = next((p for p in self._trees[base] if p.endswith(f"/issues/{name}.md")), None)
        if path is None:
            return None
        return path, run(["git", "show", f"{base}:{path}"], self.repo)

    def main_subjects(self) -> list[str]:
        return run(["git", "log", "origin/main", "--format=%s"], self.repo).splitlines()


# --- 조립 -----------------------------------------------------------------------------------------


@dataclass
class Acc:
    cost: float = 0.0
    cost_main: float = 0.0
    cost_sub: float = 0.0
    cost_sdk: float = 0.0
    cost_post_pr: float = 0.0
    output: int = 0
    thinking: int = 0
    output_thinking_known: int = 0
    msgs_main: int = 0
    msgs_sub: int = 0
    sub_partial: int = 0
    model_effort: Counter[str] = field(default_factory=Counter)
    sessions: set[str] = field(default_factory=set)
    turns: int = 0
    human_turns: int = 0
    turn_s: float = 0.0
    tool_s: float = 0.0
    wait_s: float = 0.0
    trailing_s: float = 0.0
    human_nondirective: int = 0
    interrupts: int = 0
    ask_user: int = 0
    queued_human: int = 0
    tool_errors: int = 0
    hook_blocks: int = 0
    denials: Counter[str] = field(default_factory=Counter)
    skills: Counter[str] = field(default_factory=Counter)
    first_human: tuple[str, str] | None = None  # (ts, text)
    first_ts: str = ""


def _author(node: Json) -> str:
    if isinstance(node, dict):
        a = node.get("author")
        if isinstance(a, dict):
            return str(a.get("login") or "")
    return ""


def _parent_count(commit: dict[str, Json]) -> int:
    parents = commit.get("parents")
    total = parents.get("totalCount") if isinstance(parents, dict) else None
    return total if isinstance(total, int) else 0


def _nodes(obj: Json, key: str) -> list[dict[str, Json]]:
    """GraphQL 연결(`{"nodes": [...]}`)의 노드. 모양이 다르면 빈 목록이다."""
    if not isinstance(obj, dict):
        return []
    conn = obj.get(key)
    nodes = conn.get("nodes") if isinstance(conn, dict) else None
    return [n for n in nodes if isinstance(n, dict)] if isinstance(nodes, list) else []


def truncated_connections(pr: dict[str, Json]) -> list[str]:
    """`totalCount`보다 받은 노드가 적은 연결의 이름. `PR_QUERY`의 `first:` 상한에 잘린 것이다.
    잘리면 PR 뒤 커밋과 심각도가 덜 세어지므로 meta 에 적는다(2026-10-13 캐시에는 없었다)."""
    cut: list[str] = []
    for key in ("commits", "comments", "reviews", "reviewThreads"):
        conn = pr.get(key)
        total = conn.get("totalCount") if isinstance(conn, dict) else None
        if isinstance(total, int) and total > len(_nodes(pr, key)):
            cut.append(key)
    return cut


def review_stats(pr: dict[str, Json]) -> tuple[int, Counter[str]]:
    """사람(PR 작성자)이 아닌 계정의 코멘트·리뷰·인라인 코멘트 수와 그 본문의 심각도 표지."""
    human = _author(pr)
    bodies: list[str] = []
    for n in _nodes(pr, "comments") + _nodes(pr, "reviews"):
        if _author(n) != human:
            bodies.append(str(n.get("body") or ""))
    for th in _nodes(pr, "reviewThreads"):
        for c in _nodes(th, "comments"):
            if _author(c) != human:
                bodies.append(str(c.get("body") or ""))
    # 한도 알림은 그 말을 들고 심각도 표지가 없는 본문이다. 한도를 다룬 코드에 단 실제 지적이 "rate
    # limited"라는 말을 든다고 버리지 않는다(PR 직전 버그·성능 리뷰가 캐시에서 PR #24·#146의 Minor
    # 둘이 빠진 것을 찾았다).
    bodies = [
        b
        for b in bodies
        if b.strip() and not (RATE_LIMIT_NOTICE.search(b) and not SEVERITY.search(b))
    ]
    sev: Counter[str] = Counter()
    for b in bodies:
        for m in SEVERITY.finditer(b):
            word = (m.group(1) or m.group(2)).capitalize()
            sev["Nit" if word == "Trivial" else word] += 1
    return len(bodies), sev


def build(args: argparse.Namespace) -> dict[str, Json]:
    repo = Path(run(["git", "rev-parse", "--show-toplevel"]).strip())
    first = run(["git", "worktree", "list", "--porcelain"], repo).splitlines()[0]
    root = norm(first.removeprefix("worktree "))
    git = Git(repo)
    prs, runs = load_gh(args.cache, refresh=args.refresh)

    by_branch: dict[str, list[dict[str, Json]]] = defaultdict(list)
    for pr in prs:
        if isinstance(pr, dict):
            by_branch[str(pr["headRefName"])].append(pr)
    pr_branches = set(by_branch)

    def primary(branch: str) -> dict[str, Json]:
        cands = by_branch[branch]
        merged = [p for p in cands if p.get("mergedAt")]
        return (merged or cands)[-1]

    print("트랜스크립트를 읽는다…", file=sys.stderr)
    since = window.parse_since(args.since)
    s = scan(args.projects, root, since)
    accs: dict[str, Acc] = defaultdict(Acc)
    session_turns: dict[str, list[Turn]] = {}
    unattributed = 0.0
    outside = 0.0
    control: list[tuple[float, float]] = []
    heads: list[window.TurnHead] = []

    no_pr: Counter[str] = Counter()
    for sid, recs in s.recs.items():
        for r in recs:
            if r.in_repo and r.branch and r.branch not in pr_branches and s.in_window(r.ts):
                no_pr[r.branch] += 1
        turns = turns_of(recs)
        assign_branches(turns, pr_branches)
        session_turns[sid] = turns
        for t in turns:
            first_rec = t.recs[0]
            heads.append(window.TurnHead(t.start, t.branch, t.trigger, first_rec.text))
            # `--since`의 창은 집계에만 건다. 턴과 귀속, 브랜치의 첫 사람 트리거(모집단과 배정의
            # 재료)는 창 앞 기록까지 본다(PR #220 CodeRabbit, `tools/session_cost_window.py`)
            in_win = s.in_window(t.start)
            if in_win:
                for r in t.recs:
                    if r.turn_duration_ms:
                        control.append((r.turn_duration_ms / 1000, seconds(t.start, t.end)))
            if not t.branch:
                continue
            a = accs[t.branch]
            if not in_win:
                continue
            a.sessions.add(sid)
            a.first_ts = t.start if not a.first_ts or t.start < a.first_ts else a.first_ts
            whole, tool, wait = turn_times(t)
            a.turns += 1
            a.turn_s += max(0.0, whole - wait)
            # 탐색: 턴의 마지막 사람·모델·도구 기록 뒤에 `system` 기록만 남은 꼬리(예: 몇 분 뒤
            # 사람이 친 로컬 명령의 `local_command`). 사전 등록의 턴 시간은 이 꼬리를 담는다.
            core_end = max((r.ts for r in t.recs if r.kind != "other"), default=t.start)
            a.trailing_s += seconds(core_end, t.end)
            a.tool_s += tool
            a.wait_s += wait
            if t.trigger == "human":
                a.human_turns += 1
                if "/diagnosing-bugs" in first_rec.text[:200]:
                    a.skills[DIAG_SKILL] += 1
            elif t.trigger == "interrupt":
                a.interrupts += 1
            for r in t.recs:
                for _, name, skill in r.tool_uses:
                    if name == "AskUserQuestion":
                        a.ask_user += 1
                    if name == "Skill" and skill:
                        a.skills[skill] += 1
                for _, err, hook in r.results:
                    a.tool_errors += 1 if err else 0
                    a.hook_blocks += 1 if hook else 0
                if r.denial:
                    a.denials[r.denial] += 1
                a.queued_human += 1 if r.queued_human else 0

    first_directive = window.first_directive(heads, since)
    for branch, first in window.first_humans(heads).items():
        accs[branch].first_human = first
    heads_by_branch: dict[str, list[window.TurnHead]] = defaultdict(list)
    for h in heads:
        heads_by_branch[h.branch].append(h)
    # 첫 사람 트리거가 지시문이 아니면 과제 진술이라 개입에서 뺀다. 창 앞의 것은 세지 않았다
    for branch, a in accs.items():
        a.human_nondirective = window.human_nondirective(
            heads_by_branch[branch], a.first_human, since
        )

    turn_starts = {sid: [parse_ts(t.start) for t in ts] for sid, ts in session_turns.items()}
    msg_branch: dict[str, str] = {}
    for turns in session_turns.values():
        for t in turns:
            for r in t.recs:
                if r.kind == "assistant" and r.msg_id and t.branch:
                    msg_branch.setdefault(r.msg_id, t.branch)

    in_repo_total = 0.0
    sub_partial_cost = 0.0
    session_cost: dict[str, float] = defaultdict(float)
    for mid, m in s.msgs.items():
        c = cost(m.model, m.usage)
        if c is None:
            continue
        session_cost[m.session] += c  # cost-state 대조는 세션 전체라 창과 관계없이 더한다
        if not s.in_window(m.ts):
            continue
        if not m.in_repo:
            outside += c
            continue
        in_repo_total += c
        if m.sub and not m.final:
            sub_partial_cost += c
        if m.sub:
            starts = turn_starts.get(m.session, [])
            i = bisect.bisect_right(starts, parse_ts(m.ts)) - 1 if starts else -1
            turns = session_turns.get(m.session, [])
            branch = turns[max(i, 0)].branch if turns else ""
        else:
            branch = msg_branch.get(mid, "")
        if not branch:
            unattributed += c
            continue
        a = accs[branch]
        a.cost += c
        a.output += m.usage.output
        if m.usage.thinking_known:
            a.thinking += m.usage.thinking
            a.output_thinking_known += m.usage.output
        if m.sub:
            a.cost_sub += c
            a.msgs_sub += 1
            a.sub_partial += 0 if m.final else 1
        else:
            a.cost_main += c
            a.msgs_main += 1
            a.model_effort[f"{m.model}/{m.effort or '-'}"] += c
        if m.entry == "sdk-py":
            a.cost_sdk += c
        created = primary(branch).get("createdAt")
        if isinstance(created, str) and parse_ts(m.ts) >= parse_ts(created):
            a.cost_post_pr += c

    later_mentions: Counter[int] = Counter()
    for pr in prs:
        if not isinstance(pr, dict):
            continue
        text = f"{pr.get('title') or ''}\n{pr.get('body') or ''}"
        for n in set(re.findall(r"#(\d+)\b", text)):
            if int(n) < int(str(pr["number"])):
                later_mentions[int(n)] += 1
    queue = (repo / ".scratch" / "retro-queue.md").read_text(encoding="utf-8")
    queue_rows = [ln for ln in queue.splitlines() if re.match(r"^\| \d+ \|", ln)]
    subjects = git.main_subjects()
    runs_by_branch: dict[str, list[dict[str, Json]]] = defaultdict(list)
    for r in runs:
        if isinstance(r, dict):
            runs_by_branch[str(r.get("headBranch") or "")].append(r)

    rows: list[dict[str, Json]] = []
    truncated: dict[int, list[str]] = {}
    window_start = s.first_ts
    for branch, cands in sorted(by_branch.items(), key=lambda kv: str(primary(kv[0])["createdAt"])):
        pr = primary(branch)
        num = int(str(pr["number"]))
        created = str(pr["createdAt"])
        merged = pr.get("mergedAt")
        commits = [n.get("commit") for n in _nodes(pr, "commits")]
        commit_list = [c for c in commits if isinstance(c, dict)]
        after = sum(
            1
            for c in commit_list
            if _parent_count(c) == 1 and parse_ts(str(c.get("committedDate"))) > parse_ts(created)
        )
        base = ""
        if commit_list:
            parents = commit_list[0].get("parents")
            pn = parents.get("nodes") if isinstance(parents, dict) else None
            if isinstance(pn, list) and pn and isinstance(pn[0], dict):
                base = str(pn[0].get("oid") or "")
            if base and not git.has(base):
                base = git.main_before(str(commit_list[0].get("committedDate")))
        cut = truncated_connections(pr)
        if cut:
            truncated[num] = cut
        bot_comments, sev = review_stats(pr)
        branch_runs = [
            r
            for r in runs_by_branch.get(branch, [])
            if r.get("workflowName") == CI_WORKFLOW
            and (not merged or parse_ts(str(r["createdAt"])) <= parse_ts(str(merged)))
        ]
        ci_fail = sum(1 for r in branch_runs if r.get("conclusion") == "failure")
        tag = re.compile(rf"#{num}\b")
        reverts = sum(
            1
            for sj in subjects
            if REVERT.search(sj) and tag.search(sj) and squash_number(sj) != num
        )
        a = accs.get(branch, Acc())
        ticket_path: str | None = None
        tfeats: dict[str, Json] | None = None
        kind = kind_of(branch)
        if kind == "구현" and base:
            found = git.ticket_at(base, branch.removeprefix("feature/"))
            if found:
                ticket_path, text = found
                tfeats = ticket_features(text, Path(ticket_path).name)
        dfeats = directive_features(a.first_human[1]) if a.first_human else None
        crit_major = sev.get("Critical", 0) + sev.get("Major", 0)
        top = a.model_effort.most_common(1)
        rows.append(
            {
                "branch": branch,
                "kind": kind,
                "prs": [int(str(p["number"])) for p in cands],
                "pr": num,
                "state": pr.get("state"),
                "created": created,
                "merged": merged,
                "base_ref": pr.get("baseRefName"),
                "in_window": created >= window_start,
                "early": bool(first_directive) and created < first_directive,
                "title": pr.get("title"),
                "base": base or None,
                "changed_files": pr.get("changedFiles"),
                "additions": pr.get("additions"),
                "deletions": pr.get("deletions"),
                "commits": len(commit_list),
                "commits_after_pr": after,
                "bot_comments": bot_comments,
                "severity": dict(sev),
                "ci_runs": len(branch_runs),
                "ci_failures": ci_fail,
                "rework": after + crit_major + ci_fail,
                "followup_mentions": later_mentions.get(num, 0),
                "retro_rows": sum(1 for ln in queue_rows if tag.search(ln)),
                "reverts": reverts,
                "cost": round(a.cost, 4),
                "cost_main": round(a.cost_main, 4),
                "cost_sub": round(a.cost_sub, 4),
                "cost_sdk": round(a.cost_sdk, 4),
                "cost_post_pr": round(a.cost_post_pr, 4),
                "output_tokens": a.output,
                "thinking_tokens": a.thinking,
                "thinking_share": round(a.thinking / a.output_thinking_known, 3)
                if a.output_thinking_known
                else None,
                "msgs_main": a.msgs_main,
                "msgs_sub": a.msgs_sub,
                "sub_partial": a.sub_partial,
                "model_effort": {k: round(v, 4) for k, v in a.model_effort.most_common()},
                "top_model_effort": top[0][0] if top else None,
                "top_share": round(top[0][1] / a.cost_main, 3) if top and a.cost_main else None,
                "sessions": len(a.sessions),
                "turns": a.turns,
                "human_turns": a.human_turns,
                "turn_min": round(a.turn_s / 60, 2),
                "tool_min": round(a.tool_s / 60, 2),
                "model_min": round(max(0.0, a.turn_s - a.tool_s) / 60, 2),
                "wait_min": round(a.wait_s / 60, 2),
                "trailing_min": round(a.trailing_s / 60, 2),
                "interventions": a.human_nondirective + a.interrupts + a.ask_user,
                "human_nondirective": a.human_nondirective,
                "interrupts": a.interrupts,
                "ask_user": a.ask_user,
                "queued_human": a.queued_human,
                "tool_errors": a.tool_errors,
                "hook_blocks": a.hook_blocks,
                "denials": dict(a.denials),
                "diagnosing_bugs": a.skills.get(DIAG_SKILL, 0),
                "skills": dict(a.skills.most_common()),
                "ticket": ticket_path,
                "ticket_features": tfeats,
                "directive_features": dfeats,
                "first_human_at": a.first_human[0] if a.first_human else None,
            }
        )

    meta = build_meta(s, rows, session_cost, in_repo_total, unattributed, outside, control)
    skip = re.compile(r"^(main|HEAD|worktree-.*)$")
    meta.update(
        {
            "cost_sub_partial": round(sub_partial_cost, 2),
            "truncated_connections": {str(k): v for k, v in truncated.items()},
            "since": args.since,
            "collect_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "window_sha256": hashlib.sha256(Path(window.__file__).read_bytes()).hexdigest(),
            "window_start": window_start,
            "first_directive": first_directive,
            "branches_without_pr": {b: n for b, n in no_pr.most_common() if not skip.match(b)},
        }
    )
    return {"meta": meta, "branches": rows}


def build_meta(
    s: Scan,
    rows: list[dict[str, Json]],
    session_cost: dict[str, float],
    in_repo_total: float,
    unattributed: float,
    outside: float,
    control: list[tuple[float, float]],
) -> dict[str, Json]:
    ratios: list[float] = []
    price_out: list[str] = []
    positions: dict[str, list[float]] = defaultdict(list)
    pairs = 0  # 단가 대조에 든 모델·세션 쌍. 자리를 셀 수 없는 쌍도 든다
    for sid, cs in s.cost_state.items():
        total = cs.get("totalCostUSD")
        if isinstance(total, float | int) and total > 0 and sid in session_cost:
            ratios.append(session_cost[sid] / float(total))
        mu_all = cs.get("modelUsage")
        for model, mu in mu_all.items() if isinstance(mu_all, dict) else []:
            if not isinstance(mu, dict):
                continue
            bounds = cost_state_bounds(model, mu)
            usd = mu.get("costUSD")
            if bounds is None or not isinstance(usd, float | int) or usd < 0.01:
                continue
            lo, hi = bounds
            pairs += 1
            # 토큰 없이 요금만 든 항목(웹 검색만)은 두 끝이 0이라 자리를 셀 수 없다. 자리는 건너뛰고
            # 밖 판정은 한다(PR #209 CodeRabbit)
            if hi > lo:
                positions[model].append((float(usd) - lo) / (hi - lo))
            elif lo > 0:
                positions[model].append(float(usd) / lo)
            if not (lo * 0.99 - 1e-6 <= float(usd) <= hi * 1.01 + 1e-6):
                price_out.append(f"{sid[:8]} {model} {usd:.4f} ∉ [{lo:.4f}, {hi:.4f}]")
    in_window = [r for r in rows if r["in_window"] and r["merged"]]
    unattributed_prs = [r["pr"] for r in in_window if not r["msgs_main"] and not r["msgs_sub"]]
    windowed = [m for m in s.msgs.values() if s.in_window(m.ts)]
    in_repo = [m for m in windowed if m.in_repo]
    no_usage = {mid for mid, ts in s.no_usage.items() if s.in_window(ts)}
    sub_msgs = sum(1 for m in in_repo if m.sub)
    sub_partial = sum(1 for m in in_repo if m.sub and not m.final)

    def q(v: list[float]) -> list[float]:
        return [round(x, 3) for x in statistics.quantiles(v, n=10)] if len(v) >= 3 else v

    return {
        "transcripts": {"first": s.first_ts, "last": s.last_ts},
        "responses": len(windowed),
        "responses_in_repo": len(in_repo),
        "responses_without_usage": len(no_usage - set(s.msgs)),
        "synthetic": s.synthetic,
        "unknown_models": dict(s.unknown_models),
        "cost_in_repo": round(in_repo_total, 2),
        "cost_unattributed": round(unattributed, 2),
        "cost_outside_repo": round(outside, 2),
        "sub_responses": sub_msgs,
        "sub_partial": sub_partial,
        "merged_prs_in_window": len(in_window),
        "merged_prs_without_responses": unattributed_prs,
        "cost_state_ratio": {"n": len(ratios), "deciles": q(ratios)},
        "price_check": {
            "pairs": pairs,
            "positions": {m: {"n": len(v), "deciles": q(v)} for m, v in positions.items()},
            "outside_bounds": price_out[:50],
            "outside_count": len(price_out),
        },
        "turn_duration_control": [
            {"claude_code_s": round(a, 1), "probe_s": round(b, 1)} for a, b in control
        ],
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--projects", type=Path, default=PROJECTS)
    p.add_argument("--cache", type=Path, default=HERE / "cache")
    p.add_argument("--out", type=Path, default=HERE / "branches.json")
    p.add_argument("--refresh", action="store_true", help="gh 응답을 다시 받는다")
    p.add_argument(
        "--since",
        help="집계의 창(ISO 8601, UTC). 비용·턴·표지를 이 시각 뒤로만 센다. 스윕 판정이 쓴다",
    )
    args = p.parse_args()
    try:
        data = build(args)
    except (RuntimeError, FileNotFoundError) as e:
        print(f"collect: {e}", file=sys.stderr)
        return 2
    text = json.dumps(data, ensure_ascii=False, indent=1) + "\n"
    args.out.write_text(text, encoding="utf-8", newline="\n")
    meta = data["meta"]
    assert isinstance(meta, dict)
    print(json.dumps(meta, ensure_ascii=False, indent=1))
    print(f"썼다: {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
