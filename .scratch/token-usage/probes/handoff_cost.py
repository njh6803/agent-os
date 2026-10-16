"""인계의 비용(티켓 09 "인계의 비용"). 인계 쌍마다 (가) 세션 컨텍스트, (나) 인계가 만든 다시 읽기,
(다) 비용의 차를 잰다.

사용:
    uv run python .scratch/token-usage/probes/handoff_cost.py [--projects 폴더] [--repo 폴더 이름]

저장소 루트에서 돈다(`tools.token_report`를 import한다). `--projects`의 기본은
`~/.claude/projects/`, `--repo`의 기본은 주 체크아웃의 경로에서 만든 기록 폴더 이름이고, 그 이름으로
시작하는 폴더(워크트리 폴더 포함)만 읽는다. PR 상태는 `gh pr list`로 묻는다.

쌍 알아보기:
- 인계 세션(H): 메인 세션 기록의 첫 사람 입력이 `이어받을 상태: 인계:` 줄을 든 것이다(장부의
  `handoff_of`와 같은 판정). 경계는 그 줄의 `인계:` 뒤 첫 마침표 앞(`셀프 리뷰 직전`, `커밋 뒤`,
  `PR 연 뒤`)이고, 일지는 그 줄의 `docs/journal/….md`, 브랜치는 지시문의 `브랜치:` 줄이다. 같은
  세션이 두 폴더에 겹치면 가장 긴 사본(`longest`)을 읽는다.
- 앞 세션(P): H가 열리기(첫 기록) 전에 그 일지 파일을 Write·Edit·MultiEdit로 마지막으로 쓴 같은
  브랜치(그 호출 기록의 `gitBranch`)의 메인 세션이다. 없으면 표지 없는 쌍이다.
- 인계 시점: P의 기록에서 H가 열리기 전 마지막으로 남은 인계 훅의 첨부(`attachment.type`이
  `hook_additional_context`이고 글에 `인계 문턱`과 H의 경계 이름이 든 것)다. 그 첨부의 `toolUseID`가
  경계를 일으킨 도구 호출이고, 그 호출을 낸 응답의 세션 컨텍스트가 인계 시점의 세션 컨텍스트다.
  첨부가 기록에 남는 것은 2026-10-16의 실제 인계 기록 셋(precommit-xdist-runner 둘, 08의 둘째)에서
  원본으로 봤다(`toolUseID`, `hookName` `PostToolUse:Bash`). 첨부가 없거나 그 응답을 찾지 못하거나
  세션 컨텍스트가 인계 문턱 20만 이하면 표지 없는 쌍이다.
- 끝난 쌍: H가 다시 넘겼거나(H가 다른 쌍의 P다), H의 브랜치에 병합되거나 닫힌 PR이 있다. 아니면
  끝나지 않은 쌍으로 수만 적는다.
- 자동 압축 창(2026-10-16 11:41 UTC 적용, 레벨 스윕 README의 조건 변경)보다 먼저 열린 H는 표시한다.

(가) 세션 컨텍스트: H의 메인 세션 호출(응답 ID마다 하나, 첫 줄 순)의 30번째 호출과 최대의 세션
컨텍스트, 둘을 인계 시점의 세션 컨텍스트로 나눈 비. 30번째가 없으면 "해당 없음"이다. H의 압축 수와,
30번째 호출이 압축 뒤인지를 함께 낸다.

(나) 인계가 만든 다시 읽기: H의 성공한 Read 가운데 P가 인계 시점 전에(그리고 P의 마지막 압축 뒤에)
같은 파일(`file_key_of`)을 같은 범위(offset·limit)로 읽었거나 전체를 읽은 것. 그 P의 읽기 뒤로 H의
읽기 전에(두 기록의 시각으로 견준다. 두 세션의 줄 번호는 서로 견줄 수 없다) P가 그 파일을
Edit·Write·NotebookEdit·MultiEdit로 고쳤거나 작업 트리를 바꾸는 git 명령(`GIT_MUTATION`)을
돌렸으면, H가 그 읽기 전에 그렇게 했거나 압축했으면 세지 않는다. 두 세션 밖의 변경은 이 조건으로
보이지 않아 두 결과의 글을 견준다. 범위가 같으면 글 전체가 같아야 하고, P가 전체를 읽고 H가 범위를
주었으면 H 결과의 줄(`<줄 번호>\t<글>`)마다 P 결과의 같은 번호 줄과 같아야 한다. 어느 쪽 글이
비었거나 파일로 옮겨진 출력(`<persisted-output>`)이거나, 번호 줄로 견줄 것이 없으면 견줄 수 없어 그
쌍의 (나)는 측정 불가다. H가 같은 파일·범위를 두 번째로 읽은 것은 H 자신의 다시 읽기라 세지 않는다.
글자는 H 결과의 글자 수이고 토큰으로 바꾸지 않는다. H가 Read한 글자 가운데 그 몫과 가장 많이 다시
읽은 파일을 함께 낸다.

(다) 비용의 차 = 어림 − 실제.
- 어림: H의 메인 세션 호출 수 × 인계 시점의 세션 컨텍스트 × P 모델의 캐시 읽기 단가.
- 실제: 인계로만 생긴 것. H의 호출마다 "앞 세션에 이미 있던 몫" I를 정하고, 그 호출의 캐시 읽기
  가운데 I까지와, I가 직전 호출보다 는 몫 가운데 캐시 읽기로 덮이지 않은 것의 캐시 쓰기(5분·1시간을
  그 호출의 비로 나눈다)를 H 모델의 단가로 셈한다. 캐시는 앞부분부터 읽히고 시작 컨텍스트가 맨
  앞이라 읽기를 먼저 채운다(가름의 어림). 쉰 뒤 캐시가 만료되어 I를 다시 쓴 것은 앞 세션이
  계속했어도 났을 것이고 어림에 없어 두 쪽에서 뺀다. 캐시 밖 입력은 몇 토큰이라 뺀다. 거기에 P가
  인계 시점의 응답 뒤로 H의 마지막 호출 시각까지 한 메인 세션 호출(인계 절차와 깨어난 호출)의 비용
  전부(출력 포함)를 더한다. 서브에이전트 호출은 두 쪽에서 뺀다.
- I: H 첫 호출의 세션 컨텍스트(시작 컨텍스트와 지시문)에, 그 뒤 실린 (나)의 다시 읽기와 일지
  읽기(H가 그 일지를 처음 고치기 전에 Read한 것)의 토큰을 더한 값이다. 그 Read 결과의 토큰은 결과가
  실린 다음 호출의 세션 컨텍스트가 직전 호출보다 는 값에, 그 사이 도구 결과 글자 가운데 그 결과
  글자의 몫을 곱한 값이다. H가 압축되면 그 뒤로는 I를 0으로 둔다(요약 안에서 가르지 못한다).
- 가르지 못한 몫은 새 일로 보고 두 쪽에서 뺀다. 압축 뒤의 몫, (나)의 조건에 들지 않는 다시 읽기(P가
  읽고 고친 파일을 H가 다시 읽은 것 등), 지시문 밖에서 P가 이미 알던 사실을 H가 셸로 다시 알아본
  것이 그렇다. 그만큼 실제를 낮게 잡는다. 앞 세션이 계속했다면 왔을 자동 압축과, H가 지시문·일지를
  읽느라 더 한 호출이 남은 호출 수에 드는 것은 어림을 높인다. 셋 다 차를 키우는 쪽이다(티켓의 "차가
  못 보는 것"). 반대로 차를 줄이는 쪽이 하나 있다. P의 인계 뒤 호출에는 일지 쓰기가 드는데,
  계속했어도 단계를 닫을 때 일지를 썼을 것이라 그 몫만큼 실제를 높게 잡는다. 이 프로브를 지으며 본
  것이고 재지 않았다.

판단 기준(티켓의 제안): 멈추는 기준은 (다)의 중앙값이 0 이하, 알리는 기준은 (가)의 30번째 호출 비의
중앙값이 0.5 초과다. 그 값이 있는 끝난 쌍이 다섯보다 적은 기준은 판정하지 않고 값만 낸다. 멈추는
기준이 맞으면 티켓대로 P의 일지 쓰기 호출 비용을 실제에서 뺀 값을 함께 봐야 하는데, 이 프로브는 그
몫을 가르지 않는다. 그때는 판정을 사람이 쌍의 출력과 기록으로 마친다.

종료 코드: 0은 인계 쌍이 있고 모두 표지를 지났을 때, 1은 표지 없는 쌍(gh 로 PR 상태를 읽지 못한
쌍을 포함한다)이 하나라도 있거나 인계 쌍이 하나도 없을 때, 2는 기록 폴더가 없을 때다.

못 보는 것:
- 지워진 세션 기록. 앱에서 세션을 지우면 기록 파일이 없어지고 `<세션 ID>.desktop-released.json`
  (`reason` `delete`)만 남는다. 그 세션이 P면 표지 없는 쌍이다. 장부의 행은 남지만 도구 결과의 글이
  없어 (나)를 재지 못한다.
- 일지를 Bash로 쓴 P(앞 세션을 정하지 못한다).
- 인계 훅이 병렬 호출의 앞쪽에서 그 앞 응답을 읽은 경우에도, 여기서는 첨부의 `toolUseID`가 가리키는
  응답의 값을 쓴다. 훅의 문장에 적힌 값과 다를 수 있어 둘을 함께 낸다.
"""

from __future__ import annotations

import argparse
import re
import statistics
import subprocess
import sys
from bisect import bisect_right
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
from tools.token_report import (  # noqa: E402
    EDITS,
    GIT_MUTATION,
    SHELLS,
    Call,
    Copy,
    Record,
    _blocks,
    _obj,
    _str,
    _text_len,
    file_key_of,
    first_prompt_of,
    folder_name_of,
    gather_copies,
    handoff_of,
    longest,
    main_checkout,
    price_of,
    read_records,
    read_stream,
)

THRESHOLD = 200_000
NTH = 30
WINDOW_AT = "2026-10-16T11:41:00Z"
MIN_PAIRS = 5
GH_TIMEOUT = 30
_HANDOFF_LINE = re.compile(r"^이어받을 상태: 인계: ([^.\n]+)[^\n]*", re.MULTILINE)
_BRANCH_LINE = re.compile(r"^브랜치: (\S+)", re.MULTILINE)
_JOURNAL = re.compile(r"docs/journal/[\w.-]+\.md")
_HOOK_SIZE = re.compile(r"세션 컨텍스트가 ([\d,]+) 토큰으로 인계 문턱")
_NUMBERED = re.compile(r"^\s*(\d+)\t(.*)$")


@dataclass(frozen=True)
class Read:
    line: int
    key: str
    rng: tuple[object, object]
    text: str
    path: str


@dataclass
class Stream:
    """메인 세션 기록 하나를 훑은 것."""

    session: str
    path: Path
    records: list[Record]
    calls: list[Call]
    call_lines: list[int]
    reads: list[Read] = field(default_factory=list)
    edits: list[tuple[int, str]] = field(default_factory=list)
    mutations: list[int] = field(default_factory=list)
    compactions: list[int] = field(default_factory=list)
    use_line: dict[str, int] = field(default_factory=dict)
    use_message: dict[str, str] = field(default_factory=dict)
    results: list[tuple[int, int]] = field(default_factory=list)

    @property
    def start(self) -> str:
        return self.calls[0].at if self.calls else ""


def _text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(
            str(b.get("text", ""))
            for b in content
            if isinstance(b, dict) and b.get("type") == "text"
        )
    return ""


def scan(session: str, path: Path) -> Stream:
    records, _ = read_records(path)
    ledger = read_stream((session, None), _copy_of(path), None)
    first_line: dict[str, int] = {}
    for rec in records:
        m = _obj(rec.data.get("message"))
        mid = _str(m.get("id"))
        if rec.data.get("type") == "assistant" and mid is not None:
            first_line.setdefault(mid, rec.line)
    calls = [c for c in ledger.calls if c.id in first_line]
    s = Stream(session, path, records, calls, [first_line[c.id] for c in calls])
    uses: dict[str, tuple[str, dict[str, object]]] = {}
    for rec in records:
        d = rec.data
        if d.get("type") == "system" and d.get("subtype") == "compact_boundary":
            s.compactions.append(rec.line)
            continue
        for b in _blocks(d):
            if d.get("type") == "assistant" and b.get("type") == "tool_use":
                tid = _str(b.get("id")) or ""
                name = _str(b.get("name")) or ""
                inp = _obj(b.get("input"))
                uses[tid] = (name, inp)
                s.use_line[tid] = rec.line
                s.use_message[tid] = _str(_obj(d.get("message")).get("id")) or ""
                fp = _str(inp.get("file_path")) or _str(inp.get("notebook_path")) or ""
                if name in EDITS:
                    s.edits.append((rec.line, file_key_of(fp)))
                elif name in SHELLS and GIT_MUTATION.search(_str(inp.get("command")) or ""):
                    s.mutations.append(rec.line)
            elif d.get("type") == "user" and b.get("type") == "tool_result":
                s.results.append((rec.line, _text_len(b.get("content"))))
                use = uses.get(_str(b.get("tool_use_id")) or "")
                if use is None or use[0] != "Read" or b.get("is_error") is True:
                    continue
                inp = use[1]
                fp = (_str(inp.get("file_path")) or "").replace("\\", "/")
                s.reads.append(
                    Read(
                        rec.line,
                        file_key_of(fp),
                        (inp.get("offset"), inp.get("limit")),
                        _text(b.get("content")),
                        fp,
                    )
                )
    return s


def _copy_of(path: Path) -> Copy:
    st = path.stat()
    return Copy(path, path.parent.name, st.st_size, st.st_mtime)


@dataclass(frozen=True)
class Handoff:
    session: str
    path: Path
    boundary: str
    journal: str | None
    branch: str | None
    # "이어받을 상태" 줄에 일지 경로가 없어 지시문의 다른 줄(읽을 것 등)에서 찾았다.
    journal_elsewhere: bool = False


def handoff_sessions(mains: dict[str, Path]) -> list[Handoff]:
    out: list[Handoff] = []
    for session, path in mains.items():
        if "이어받을 상태: 인계:".encode() not in path.read_bytes():
            continue
        records, _ = read_records(path)
        prompt = first_prompt_of(records)
        if prompt is None or not handoff_of(prompt):
            continue
        m = _HANDOFF_LINE.search(prompt.text)
        line = m.group(0) if m else ""
        j = _JOURNAL.search(line)
        elsewhere = j is None and _JOURNAL.search(prompt.text) is not None
        if elsewhere:
            j = _JOURNAL.search(prompt.text)
        b = _BRANCH_LINE.search(prompt.text)
        out.append(
            Handoff(
                session,
                path,
                m.group(1).strip() if m else "",
                j.group(0) if j else None,
                b.group(1) if b else None,
                elsewhere,
            )
        )
    return out


def predecessor(h: Handoff, h_start: str, mains: dict[str, Path]) -> str | None:
    """H가 열리기 전에 그 일지를 Write·Edit로 마지막으로 쓴 같은 브랜치의 메인 세션."""
    if h.journal is None or h.branch is None:
        return None
    name = Path(h.journal).name.encode()
    best: tuple[str, str] | None = None
    for session, path in mains.items():
        if session == h.session or name not in path.read_bytes():
            continue
        records, _ = read_records(path)
        for rec in records:
            d = rec.data
            at = _str(d.get("timestamp")) or ""
            if (
                d.get("type") != "assistant"
                or _str(d.get("gitBranch")) != h.branch
                or at >= h_start
            ):
                continue
            for b in _blocks(d):
                if b.get("type") != "tool_use" or b.get("name") not in (
                    "Write",
                    "Edit",
                    "MultiEdit",
                ):
                    continue
                fp = (_str(_obj(b.get("input")).get("file_path")) or "").replace("\\", "/")
                if fp.endswith(h.journal) and (best is None or at > best[0]):
                    best = (at, session)
    return best[1] if best else None


@dataclass(frozen=True)
class Point:
    line: int
    call: Call
    hook_size: int | None


def handoff_point(p: Stream, boundary: str, h_start: str) -> Point | None:
    found: tuple[int, str, int | None] | None = None
    for rec in p.records:
        d = rec.data
        att = _obj(d.get("attachment"))
        if att.get("type") != "hook_additional_context":
            continue
        if (_str(d.get("timestamp")) or "") >= h_start:
            continue
        content = att.get("content")
        parts = content if isinstance(content, list) else []
        text = "\n".join(x for x in parts if isinstance(x, str))
        if "인계 문턱" not in text or f"`{boundary}`" not in text:
            continue
        size = _HOOK_SIZE.search(text)
        found = (
            rec.line,
            _str(att.get("toolUseID")) or "",
            int(size.group(1).replace(",", "")) if size else None,
        )
    if found is None:
        return None
    mid = p.use_message.get(found[1])
    for c, line in zip(p.calls, p.call_lines, strict=True):
        if c.id == mid:
            return Point(line, c, found[2])
    return None


def _same(p: Read, h: Read) -> bool | None:
    """두 결과의 글이 같은가. 견줄 수 없으면 None."""
    if not p.text or not h.text or "<persisted-output>" in p.text or "<persisted-output>" in h.text:
        return None
    if p.rng == h.rng:
        return p.text == h.text
    whole: dict[str, str] = {}
    for ln in p.text.splitlines():
        m = _NUMBERED.match(ln)
        if m:
            whole[m.group(1)] = m.group(2)
    if not whole:
        return None
    compared = 0
    for ln in h.text.splitlines():
        m = _NUMBERED.match(ln)
        if m:
            compared += 1
            if whole.get(m.group(1)) != m.group(2):
                return False
    # H 결과에 번호 줄이 하나도 없으면(알림만 든 글) 견준 것이 없어 같다고 하지 않는다.
    return True if compared else None


@dataclass
class Rereads:
    reads: list[Read]
    unmeasurable: bool


def _clock(s: Stream) -> tuple[list[int], list[str]]:
    """시각이 있는 기록의 줄과 시각. 두 세션의 줄 번호는 서로 견줄 수 없어 시각으로 견준다."""
    lines: list[int] = []
    stamps: list[str] = []
    for r in s.records:
        t = _str(r.data.get("timestamp"))
        if t:
            lines.append(r.line)
            stamps.append(t)
    return lines, stamps


def _at(clock: tuple[list[int], list[str]], line: int) -> str:
    """그 줄이나 그 앞에서 가장 가까운 기록의 시각. 없으면 빈 문자열."""
    i = bisect_right(clock[0], line)
    return clock[1][i - 1] if i else ""


def rereads(p: Stream, h: Stream, point: Point) -> Rereads:
    p_cut = max((c for c in p.compactions if c < point.line), default=0)
    p_clock, h_clock = _clock(p), _clock(h)
    found: list[Read] = []
    unmeasurable = False
    seen: set[tuple[str, tuple[object, object]]] = set()
    for hr in h.reads:
        # H 가 같은 파일·범위를 두 번째로 읽은 것은 H 자신의 다시 읽기라 인계 탓으로 세지 않는다.
        if (hr.key, hr.rng) in seen:
            continue
        seen.add((hr.key, hr.rng))
        h_at = _at(h_clock, hr.line)

        def changed_before_h(line: int, h_at: str = h_at) -> bool:
            # P 가 그 파일을 읽은 뒤의 변경 가운데 H 가 읽기 전에 난 것만 센다(티켓 "그 사이에").
            return _at(p_clock, line) <= h_at

        if any(c < hr.line for c in h.compactions):
            continue
        if any(m < hr.line for m in h.mutations) or any(
            line < hr.line and key == hr.key for line, key in h.edits
        ):
            continue
        candidates = [
            pr
            for pr in p.reads
            if p_cut < pr.line < point.line
            and pr.key == hr.key
            and (pr.rng == hr.rng or pr.rng == (None, None))
            and not any(m > pr.line and changed_before_h(m) for m in p.mutations)
            and not any(
                line > pr.line and key == pr.key and changed_before_h(line) for line, key in p.edits
            )
        ]
        if not candidates:
            continue
        verdicts = [_same(pr, hr) for pr in candidates]
        if any(v is True for v in verdicts):
            found.append(hr)
        elif any(v is None for v in verdicts):
            unmeasurable = True
    return Rereads(found, unmeasurable)


def _tokens_of(h: Stream, read_line: int, chars: int) -> int:
    """Read 결과 하나가 실린 토큰. 다음 호출의 세션 컨텍스트가 는 값 × 그 사이 결과 글자의 몫."""
    nxt = next((i for i, line in enumerate(h.call_lines) if line > read_line), None)
    if nxt is None or nxt == 0:
        return 0
    growth = max(0, h.calls[nxt].context - h.calls[nxt - 1].context)
    lo, hi = h.call_lines[nxt - 1], h.call_lines[nxt]
    total = sum(n for line, n in h.results if lo < line < hi)
    return round(growth * chars / total) if total else 0


def _cost(c: Call) -> float:
    v = c.cost()
    return v if v is not None else 0.0


@dataclass(frozen=True)
class Inherited:
    base: int
    added: int
    read: float
    write: float

    @property
    def cost(self) -> float:
        return self.read + self.write


def inherited_cost(h: Stream, extra: list[tuple[int, int]]) -> Inherited:
    """H 호출마다 앞 세션에 이미 있던 몫 I의 캐시 읽기와, I가 처음 실린 호출의 쓰기의 달러."""
    added = sorted((line, _tokens_of(h, line, n)) for line, n in extra)
    cut = min(h.compactions, default=None)
    base = h.calls[0].context if h.calls else 0
    read_cost = write_cost = 0.0
    before = 0
    for c, line in zip(h.calls, h.call_lines, strict=True):
        if cut is not None and line > cut:
            break
        i = base + sum(t for at, t in added if at < line)
        p = price_of(c.model)
        if p is None:
            continue
        read = min(i, c.cache_read)
        writes = c.cache_write_5m + c.cache_write_1h
        # 쓰기는 I가 새로 는 몫만 센다. 쉰 뒤 캐시가 만료되어 다시 쓴 것은 앞 세션이
        # 계속했어도 났을 것이고 어림에 없어 두 쪽에서 뺀다.
        w = min(max(0, i - before), writes, max(0, i - read))
        share5 = c.cache_write_5m / writes if writes else 0.0
        read_cost += read * p.cache_read / 1e6
        write_cost += w * (share5 * 1.25 + (1 - share5) * 2.0) * p.input / 1e6
        before = i
    return Inherited(base, sum(t for _, t in added), read_cost, write_cost)


def pr_states(branch: str) -> list[str] | None:
    """그 브랜치 PR 들의 상태. gh 가 실패하거나 시간을 넘기면 None(끝났는지 모른다)."""
    try:
        out = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--head",
                branch,
                "--state",
                "all",
                "--json",
                "state",
                "--jq",
                ".[].state",
            ],
            capture_output=True,
            text=True,
            timeout=GH_TIMEOUT,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.split()


def _median(values: list[float]) -> str:
    return f"{statistics.median(values):.3f}" if values else "해당 없음"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--projects", type=Path, default=Path.home() / ".claude" / "projects")
    ap.add_argument("--repo", default=None)
    args = ap.parse_args()
    if not args.projects.is_dir():
        print(f"기록 폴더가 없다: {args.projects}")
        return 2
    repo = args.repo or folder_name_of(main_checkout())
    mains = {
        session: longest(copies).path
        for (session, agent), copies in gather_copies(args.projects).items()
        if agent is None and any(c.folder.startswith(repo) for c in copies)
    }
    handoffs = handoff_sessions(mains)
    streams: dict[str, Stream] = {}

    def stream(session: str) -> Stream:
        if session not in streams:
            streams[session] = scan(session, mains[session])
        return streams[session]

    pairs: list[tuple[Handoff, Stream, Stream | None, Point | None]] = []
    for h in sorted(handoffs, key=lambda x: stream(x.session).start):
        hs = stream(h.session)
        stamps = [t for t in (_str(r.data.get("timestamp")) for r in hs.records) if t]
        ps_id = predecessor(h, min(stamps, default=hs.start), mains)
        ps = stream(ps_id) if ps_id else None
        pt = handoff_point(ps, h.boundary, hs.start) if ps else None
        pairs.append((h, hs, ps, pt))
    givers = {ps.session for _, _, ps, _ in pairs if ps is not None}

    unmarked = 0
    gh_failed = 0
    unfinished = 0
    a30: list[float] = []
    diffs: list[float] = []
    for h, hs, ps, pt in pairs:
        head = f"## H {h.session[:8]} ({h.branch}, 경계 `{h.boundary}`, 시작 {hs.start})"
        print(head)
        if hs.start < WINDOW_AT:
            print("- 자동 압축 창을 적용하기 전에 열렸다")
        if h.journal_elsewhere:
            print(f"- 이어받을 상태 줄에 일지 경로가 없어 지시문의 다른 줄에서 찾았다({h.journal})")
        if ps is None or pt is None or pt.call.context <= THRESHOLD:
            unmarked += 1
            why = (
                "앞 세션을 정하지 못했다"
                "(일지를 Write·Edit로 쓴 같은 브랜치의 메인 세션이 기록에 없다)"
                if ps is None
                else "앞 세션 기록에 그 경계의 인계 훅 첨부가 없다"
                if pt is None
                else f"인계 시점의 세션 컨텍스트 {pt.call.context:,}이 문턱 이하다"
            )
            print(f"- 표지 없음: {why}. 측정으로 세지 않는다")
            continue
        states = [] if h.session in givers or not h.branch else pr_states(h.branch)
        if states is None:
            gh_failed += 1
            print("- 표지 없음: gh 로 PR 상태를 읽지 못해 끝났는지 모른다. 측정으로 세지 않는다")
            continue
        finished = h.session in givers or any(s in ("MERGED", "CLOSED") for s in states)
        h_model = hs.calls[0].model if hs.calls else "?"
        print(f"- 앞 세션 {ps.session[:8]}, 모델 {pt.call.model} → {h_model}")
        hook = f"{pt.hook_size:,}" if pt.hook_size is not None else "모름"
        print(
            f"- 인계 시점: 응답 {pt.call.at}의 세션 컨텍스트 {pt.call.context:,}"
            f" (훅 문장의 값 {hook})"
        )
        if not finished:
            unfinished += 1
            print(f"- 끝나지 않은 쌍이다(PR 상태 {states or '없음'}). 재지 않는다")
            continue
        print("- 끝난 쌍: " + ("H가 다시 넘겼다" if h.session in givers else f"PR {states}"))
        ctx = pt.call.context
        n = len(hs.calls)
        nth = hs.calls[NTH - 1] if n >= NTH else None
        mx = max(c.context for c in hs.calls)
        after = nth is not None and any(c < hs.call_lines[NTH - 1] for c in hs.compactions)
        print(
            f"- (가) 호출 {n}회, 압축 {len(hs.compactions)}회. 30번째 "
            + (
                f"{nth.context:,} (비 {nth.context / ctx:.3f}{', 압축 뒤' if after else ''})"
                if nth
                else "해당 없음"
            )
            + f", 최대 {mx:,} (비 {mx / ctx:.3f})"
        )
        if nth is not None:
            a30.append(nth.context / ctx)
        rr = rereads(ps, hs, pt)
        read_chars = sum(len(r.text) for r in hs.reads)
        if rr.unmeasurable:
            print("- (나) 측정 불가: 견줄 글이 기록에 없는 읽기가 있다")
        else:
            got = sum(len(r.text) for r in rr.reads)
            by: dict[str, int] = {}
            for r in rr.reads:
                by[r.key] = by.get(r.key, 0) + len(r.text)
            top = max(by.items(), key=lambda kv: kv[1]) if by else None
            print(
                f"- (나) 다시 읽기 {len(rr.reads)}회 {got:,}자, H가 Read한 {read_chars:,}자의 "
                f"{(got / read_chars if read_chars else 0):.1%}"
                + (f". 가장 많은 파일 {top[0]} {top[1]:,}자" if top else "")
            )
        journal_reads = []
        if h.journal is not None:
            first_edit = min(
                (line for line, key in hs.edits if key.endswith(h.journal.lower())), default=None
            )
            journal_reads = [
                r
                for r in hs.reads
                if r.key.endswith(h.journal.lower()) and (first_edit is None or r.line < first_edit)
            ]
        extra = list({r.line: len(r.text) for r in [*rr.reads, *journal_reads]}.items())
        p_price = price_of(pt.call.model)
        estimate = n * ctx * (p_price.cache_read if p_price else 0.0) / 1e6
        h_end = hs.calls[-1].at
        giver_calls = [
            c
            for c, line in zip(ps.calls, ps.call_lines, strict=True)
            if line > pt.line and c.at <= h_end
        ]
        inherited = inherited_cost(hs, extra)
        procedure = sum(_cost(c) for c in giver_calls)
        actual = inherited.cost + procedure
        diffs.append(estimate - actual)
        print(
            f"- (다) 어림 ${estimate:.2f}(호출 {n} × {ctx:,}), 실제 ${actual:.2f}, "
            f"차 ${estimate - actual:.2f}"
        )
        print(
            f"  - 이미 있던 몫: 첫 호출 {inherited.base:,}에 "
            f"다시 읽기·일지 {inherited.added:,} 토큰. "
            f"읽기 ${inherited.read:.2f}, 쓰기 ${inherited.write:.2f}"
        )
        print(f"  - 앞 세션의 인계 뒤 호출 {len(giver_calls)}회 ${procedure:.2f}")
    print()
    print(
        f"표지 없는 쌍 {unmarked}, PR 상태를 읽지 못한 쌍 {gh_failed},"
        f" 끝나지 않은 쌍 {unfinished}, 잰 쌍 {len(diffs)}"
    )
    if not pairs:
        print(f"인계 쌍이 없다. 폴더 이름 머리 {repo!r}와 기록 폴더 {args.projects}를 본다")
    print(
        f"(가) 30번째 호출 비: 쌍 {len(a30)}, 중앙값 {_median(a30)}, 최대 {max(a30, default=0):.3f}"
    )
    print(f"(다) 차($): 쌍 {len(diffs)}, 중앙값 {_median(diffs)}, 최대 {max(diffs, default=0):.2f}")
    for name, vals, bad in (
        ("멈추는 기준", diffs, lambda m: m <= 0),
        ("알리는 기준", a30, lambda m: m > 0.5),
    ):
        if len(vals) < MIN_PAIRS:
            print(f"{name}: 쌍 {len(vals)}이 {MIN_PAIRS}보다 적어 판정하지 않는다")
        else:
            print(f"{name}: {'걸렸다' if bad(statistics.median(vals)) else '걸리지 않았다'}")
    return 1 if unmarked or gh_failed or not pairs else 0


if __name__ == "__main__":
    sys.exit(main())
