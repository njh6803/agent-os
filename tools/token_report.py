"""토큰 사용량 장부와 보고서(ADR 0033, `.scratch/token-usage/spec.md`의 "사용량 장부와 보고서
도구").

토큰과 비용을 재는 기본 길은 이 도구다. 세션 기록을 장부로 옮기고, 장부의 토큰에 단가표를 곱해
환산 비용을 낸다. 같은 세션 기록이 폴더 둘(주 폴더와 워크트리 폴더)에 겹치거나 포크한 세션에 앞
세션의 응답이 복사되어 있어도 응답 ID로 한 번만 센다. 글자 수에 근사 가중치를 곱해 토큰을
어림하지 않는다. 설계 인터뷰의 셈이 그렇게 틀렸다(대기열 273).

사용:
    uv run --no-project python tools/token_report.py daily [--projects 폴더] [--out 폴더]
        [--tz +09:00] [--today YYYY-MM-DD]
명령은 셋이다. `ingest`는 세션 기록을 읽어 장부를 갱신하고(`--full`은 `state.json`을 무시하고 남은
기록을 모두 다시 읽는다. 계정 기록은 건드리지 않는다), `report`는 장부에서 일간 보고서와 요약
파일을 만들고 보관 수를 넘은 일간 보고서를 지우며, `daily`는 둘을 차례로 한다. 표준 라이브러리만
써서 저장소의 가상 환경 없이 돈다(작업 스케줄러가 그렇게 부른다).

인자의 기본값: 세션 기록 폴더는 `~/.claude/projects/`, 출력 폴더는 주 체크아웃(git 공용 디렉터리의
부모)의 `.scratch/token-report/`, 시간대는 이 PC의 지금 오프셋, 오늘은 그 시간대의 오늘이다.
시간대는 `+09:00` 같은 고정 오프셋이다. 이 PC의 파이썬에는 IANA 시간대 자료가 없다.

출력 폴더:
- `ledger/YYYY-MM.jsonl`: 그 달(지역 시간대)의 장부 행. 행은 셋이고 모두 형식 판 칸 `v`(지금 1)와
  종류 칸 `kind`를 든다. `call`은 모델 응답 하나(응답 ID, UTC 시각, 세션 ID, 서브에이전트 ID와
  유형, 기록 폴더, 브랜치, 모델, 노력, 토큰 다섯, 세션 컨텍스트, 같은 기록 파일의 직전 호출과의 초
  간격), `session`은 메인 세션 하나(세션 ID, 첫 기록의 시각), `unreadable`은 읽지 못한 기록 줄
  하나(그 앞 기록의 시각에 귀속한다)다. 환산 비용은 적지 않는다. 단가표를 고치면 지난 보고서도 같은
  셈으로 다시 만들어지게 하기 위해서다. 칸을 더하는 것은 판을 올리지 않고, 있던 칸의 뜻이나 형을
  바꾸면 판을 올리고 옛 판을 읽는 길을 둔다. 읽는 쪽은 모르는 칸을 무시한다.
- `ledger/accounts.jsonl`: 세션 시작 훅이 덧붙이는 계정 기록(명세 "계정 기록의 줄"). 이 도구는
  읽기만 한다. 세션의 계정은 그 세션 ID의 줄 가운데 `account_uuid`가 `null`이 아닌 마지막 줄의
  이메일이고, 서브에이전트는 부모 세션의 계정이며, 줄이 없으면 "계정 모름"이다.
- `daily/YYYY-MM-DD.md`: `--today`의 전날까지 최근 7일의 일간 보고서. `report`가 그 7일을 모두 다시
  만들므로 빠진 날과 지운 폴더가 채워진다. 그 이름 모양의 보통 파일 가운데 그 7일보다 이른 날의
  것만 지운다(더 뒤의 `--today`로 만든 것은 남는다). 링크와 폴더, 이름이 다른 파일은 그대로 두고,
  `daily`가 링크면 아무것도 하지 않고 2로 끝난다.
- `summary.txt`: 최근 일간 보고서의 요약, 여덟 줄 이하. 첫 줄은 글자 그대로 `보고서 날짜:
  YYYY-MM-DD`이고 세션 시작 훅이 이 줄을 읽는다.
- `state.json`: 마지막 `ingest`의 시작 시각. `ingest.lock`: 명령이 도는 동안의 잠금 파일. 잠금이
  있으면 둘째 실행은 기다리지 않고 알린 뒤 3으로 끝난다.

증분과 멱등: `ingest`는 지난 실행의 한 시간 전보다 뒤에 바뀐 기록 파일만 다시 읽고, 그 기록 파일의
행을 새로 읽은 행으로 갈아 끼운다. 새로 읽은 사본에 없는 응답의 옛 행은 남긴다(긴 사본이 지워져
짧은 사본을 읽은 때). 겹친 사본은 가장 긴 것을 읽는다. 같은 응답 ID가 여러 세션에 있으면 먼저
시작한 세션의 행만 남긴다. 시작 시각을 모르는 세션(부모 기록이 없는 서브에이전트)이 직전 장부에서
그 응답을 가졌으면 그대로 갖는다. 다시 읽은 기록의 가장 이른 달의 전달부터 장부를 읽어 견준다.
다시 읽지 않은 행은 읽어 온 달 파일에 그대로 두고 새로 읽은 행만 지금 시간대로 달을 가르며,
`report`는 보고할 날의 앞뒤 하루까지 달 파일을 읽는다. 그래서 실행마다 시간대 인자가 달라도 행이
겹치거나 빠지지 않는다. 기록 파일이 지워져도 그 행은 남는다. 세션 기록 폴더가 없으면 장부와
`state.json`을 건드리지 않고 2로 끝난다(`state.json`을 올리면 그 앞의 기록을 건너뛴다). 달 파일과
요약 파일은 임시 파일에 써서 `os.replace`로 바꿔 넣는다. 줄바꿈 없이 잘린 마지막 줄은 세션이 쓰는
도중이라 읽지도 경보에 세지도 않는다. 모델이 `<synthetic>`인 기록은 모델 호출이 아니라 들이지
않는다.

옮긴 코드: 호출 모으기(응답 ID마다 출력 토큰이 가장 큰 usage), 메인 세션·서브에이전트·모델·노력·
유형으로 가르기, 서브에이전트 유형 잇기는 `.scratch/harness/probes/token_usage/measure.py`의
`calls`·`split`·`agent_types`에서 옮겼다. 유형은 서브에이전트 기록 옆의 `agent-<ID>.meta.json`의
`agentType`을 먼저 보고, 없으면 부모 기록의 Agent 호출과 그 결과의 `agentId`로 잇는다. 기록 폴더
이름은 `folder_name_of`가 주 체크아웃의 경로에서 만든다(프로브의 `REPO_PREFIX`를 대신한다). 지표
1~6은 이 저장소와 다른 프로젝트를 가르지 않아 지금은 시험만 그 함수를 부른다.

못 보는 것:
- 세션 기록에 남지 않는 호출(웹 검색 요금, Claude Code 밖의 API 호출)과 청구액·한도의 남은 양.
- 기록 파일이 첫 `ingest` 전에 지워졌으면 그 호출은 장부에 없다.
- 계정 기록이 없는 세션(세션 시작 훅을 들이기 전, 다른 프로젝트)은 계정을 가르지 못한다.
- 시작 시각을 모르는 세션끼리 응답 ID가 겹치면 어느 쪽이 먼저 시작했는지 모른다. 직전 장부의 주인이
  남고, 둘 다 처음 들면 세션 ID 순이다.
- 끊긴 실행이 남긴 잠금 파일은 사람이 지울 때까지 남아, 그동안 모든 실행이 3으로 끝나고 요약이
  낡는다.
- 지표 7~12, 주간·4주 보고서, 세션 행의 나머지 칸은 아직 없다(티켓 03).
"""

from __future__ import annotations

import argparse
import bisect
import io
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
import time
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

FORMAT = 1
# 시작 시각을 모르는 행의 순위 칸. 시각끼리 견주는 자리에 None 대신 둔다.
_NO_TIME = datetime.min.replace(tzinfo=UTC)
KEEP_DAILY = 7
SPIKE = 1.5
MIN_DAYS = 4
UNKNOWN_ACCOUNT = "계정 모름"
LOCK = "ingest.lock"
DAILY_NAME = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\.md")
MONTH_NAME = re.compile(r"([0-9]{4}-[0-9]{2})\.jsonl")
GIT_TIMEOUT = 10


# 단가표


@dataclass(frozen=True)
class Price:
    input: float
    output: float
    cache_read: float


# 달러/백만 토큰. `.scratch/harness/probes/session_cost/costs.py`의 표를 2026-10-16에 옮겼다. 출처는
# 그 독스트링이다. 입력·출력은 claude-api 스킬(Claude Code 2.1.295 번들, 모델 표는 2026-10-06
# 캐시), 캐시 읽기는 같은 번들의 `shared/prompt-caching.md` 배수이고, 캐시 쓰기는 5분이 입력의
# 1.25배, 1시간이 2배다. `claude-sonnet-5-5`의 캐시 읽기는 공식 가격표(2026-10-13)의 0.05배가
# 아니라 Claude Code가 셈한 0.1배다(그 프로브의 README "2026-10-13 캐시 읽기 단가 대조").
# `claude-haiku-5-5`는 프롬프트 10만 토큰 이하의 단가다. 웹 검색 요금은 표에 없다.
PRICES: dict[str, Price] = {
    "claude-opus-5-5": Price(4.0, 20.0, 0.20),
    "claude-fable-5-1": Price(10.0, 50.0, 0.25),
    "claude-sonnet-5-5": Price(2.0, 10.0, 0.20),
    "claude-haiku-5-5": Price(0.10, 0.50, 0.01),
    "claude-opus-5": Price(5.0, 25.0, 0.50),
    "claude-opus-4-8": Price(5.0, 25.0, 0.50),
    "claude-opus-4-7": Price(5.0, 25.0, 0.50),
    "claude-sonnet-5": Price(2.0, 10.0, 0.20),
    "claude-haiku-4-5": Price(1.0, 5.0, 0.10),
}


def price_of(model: str) -> Price | None:
    """날짜가 붙은 이름(`claude-haiku-4-5-20251001`)은 날짜를 떼고 찾는다."""
    head, _, tail = model.rpartition("-")
    return PRICES.get(head if tail.isdigit() and len(tail) == 8 else model)


# JSON 읽기


def _obj(v: Json) -> dict[str, Json]:
    return v if isinstance(v, dict) else {}


def _list(v: Json) -> list[Json]:
    return v if isinstance(v, list) else []


def _str(v: Json) -> str | None:
    return v if isinstance(v, str) else None


def _int(v: Json) -> int:
    return v if isinstance(v, int) and not isinstance(v, bool) else 0


def _parse_json(text: str) -> Json:
    # `json.loads`의 반환형은 Any라, 여기서 `Json`으로 받아 뒤의 좁히기가 타입 검사를 지나게 한다.
    return json.loads(text)


def _time(v: Json) -> datetime | None:
    """UTC 시각. 읽지 못하거나 시간대가 없으면 None이다."""
    s = _str(v)
    if s is None:
        return None
    try:
        t = datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None
    return t.astimezone(UTC) if t.tzinfo is not None else None


def _iso(t: datetime) -> str:
    base = t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S")
    ms = t.microsecond // 1000
    return f"{base}.{ms:03d}Z" if ms else f"{base}Z"


# 장부의 행


@dataclass(frozen=True)
class Call:
    id: str
    at: str
    session: str
    agent: str | None
    agent_type: str | None
    project: str
    branch: str | None
    model: str
    effort: str | None
    input: int
    cache_read: int
    cache_write_5m: int
    cache_write_1h: int
    output: int
    context: int
    gap_s: float | None

    def row(self) -> dict[str, Json]:
        return {
            "v": FORMAT,
            "kind": "call",
            "id": self.id,
            "at": self.at,
            "session": self.session,
            "agent": self.agent,
            "agent_type": self.agent_type,
            "project": self.project,
            "branch": self.branch,
            "model": self.model,
            "effort": self.effort,
            "input": self.input,
            "cache_read": self.cache_read,
            "cache_write_5m": self.cache_write_5m,
            "cache_write_1h": self.cache_write_1h,
            "output": self.output,
            "context": self.context,
            "gap_s": self.gap_s,
        }

    @staticmethod
    def of(r: dict[str, Json]) -> Call:
        gap = r.get("gap_s")
        return Call(
            id=_str(r.get("id")) or "",
            at=_str(r.get("at")) or "",
            session=_str(r.get("session")) or "",
            agent=_str(r.get("agent")),
            agent_type=_str(r.get("agent_type")),
            project=_str(r.get("project")) or "",
            branch=_str(r.get("branch")),
            model=_str(r.get("model")) or "",
            effort=_str(r.get("effort")),
            input=_int(r.get("input")),
            cache_read=_int(r.get("cache_read")),
            cache_write_5m=_int(r.get("cache_write_5m")),
            cache_write_1h=_int(r.get("cache_write_1h")),
            output=_int(r.get("output")),
            context=_int(r.get("context")),
            gap_s=float(gap)
            if isinstance(gap, int | float) and not isinstance(gap, bool)
            else None,
        )

    def cost(self) -> float | None:
        """달러. 단가표에 없는 모델이면 None이다."""
        p = price_of(self.model)
        if p is None:
            return None
        return (
            self.input * p.input
            + self.output * p.output
            + self.cache_read * p.cache_read
            + self.cache_write_5m * p.input * 1.25
            + self.cache_write_1h * p.input * 2.0
        ) / 1e6


@dataclass(frozen=True)
class SessionRow:
    session: str
    start: str

    def row(self) -> dict[str, Json]:
        return {"v": FORMAT, "kind": "session", "session": self.session, "start": self.start}


@dataclass(frozen=True)
class Unreadable:
    session: str
    agent: str | None
    file: str
    line: int
    at: str

    def row(self) -> dict[str, Json]:
        return {
            "v": FORMAT,
            "kind": "unreadable",
            "session": self.session,
            "agent": self.agent,
            "file": self.file,
            "line": self.line,
            "at": self.at,
        }


@dataclass
class Ledger:
    calls: list[Call] = field(default_factory=list[Call])
    sessions: list[SessionRow] = field(default_factory=list[SessionRow])
    unreadable: list[Unreadable] = field(default_factory=list[Unreadable])

    def extend(self, other: Ledger) -> None:
        self.calls.extend(other.calls)
        self.sessions.extend(other.sessions)
        self.unreadable.extend(other.unreadable)


type StreamKey = tuple[str, str | None]


def _stream_of(r: Call | SessionRow | Unreadable) -> StreamKey:
    return (r.session, None) if isinstance(r, SessionRow) else (r.session, r.agent)


def read_ledger_file(path: Path) -> Ledger:
    out = Ledger()
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = _obj(_parse_json(line))
        kind = r.get("kind")
        if kind == "call":
            out.calls.append(Call.of(r))
        elif kind == "session":
            out.sessions.append(
                SessionRow(_str(r.get("session")) or "", _str(r.get("start")) or "")
            )
        elif kind == "unreadable":
            out.unreadable.append(
                Unreadable(
                    _str(r.get("session")) or "",
                    _str(r.get("agent")),
                    _str(r.get("file")) or "",
                    _int(r.get("line")),
                    _str(r.get("at")) or "",
                )
            )
    return out


# 세션 기록 읽기


@dataclass(frozen=True)
class Copy:
    path: Path
    folder: str
    size: int
    mtime: float


def discover(projects: Path) -> dict[StreamKey, list[Copy]]:
    """기록 파일을 (세션 ID, 서브에이전트 ID)마다 모은다. 겹친 사본은 같은 열쇠에 든다."""
    found: dict[StreamKey, list[Copy]] = defaultdict(list)
    if not projects.is_dir():
        return found
    for folder in sorted(projects.iterdir()):
        if not folder.is_dir():
            continue
        paths: list[tuple[StreamKey, Path]] = [((p.stem, None), p) for p in folder.glob("*.jsonl")]
        paths += [
            ((p.parent.parent.name, p.stem.removeprefix("agent-")), p)
            for p in folder.glob("*/subagents/agent-*.jsonl")
        ]
        for key, p in paths:
            try:
                st = p.stat()
            except FileNotFoundError:
                continue
            found[key].append(Copy(p, folder.name, st.st_size, st.st_mtime))
    return found


def longest(copies: list[Copy]) -> Copy:
    return max(copies, key=lambda c: (c.size, c.folder))


@dataclass(frozen=True)
class Record:
    line: int
    data: dict[str, Json]


def read_records(path: Path) -> tuple[list[Record], list[int]]:
    """줄마다 JSON 객체를 낸다. 읽지 못한 줄은 번호로 따로 낸다. 줄바꿈 없는 마지막 줄은 버린다."""
    parts = path.read_bytes().split(b"\n")
    parts.pop()
    records: list[Record] = []
    bad: list[int] = []
    for i, raw in enumerate(parts, 1):
        if not raw.strip():
            continue
        try:
            data = _parse_json(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            bad.append(i)
            continue
        if isinstance(data, dict):
            records.append(Record(i, data))
        else:
            bad.append(i)
    return records, bad


def _blocks(d: dict[str, Json]) -> list[dict[str, Json]]:
    return [b for b in _list(_obj(d.get("message")).get("content")) if isinstance(b, dict)]


def agent_types(records: list[Record]) -> dict[str, str]:
    """부모 기록의 Agent 호출과 그 결과의 `agentId`로 잇는다. 유형을 생략한 호출은 결과의
    `agentType`을 괄호로 단다."""
    uses: dict[str, str | None] = {}
    out: dict[str, str] = {}
    for rec in records:
        d = rec.data
        if d.get("type") == "assistant":
            for b in _blocks(d):
                if b.get("type") == "tool_use" and b.get("name") == "Agent":
                    uses[_str(b.get("id")) or ""] = _str(_obj(b.get("input")).get("subagent_type"))
        result = _obj(d.get("toolUseResult"))
        agent_id = _str(result.get("agentId"))
        if d.get("type") != "user" or agent_id is None:
            continue
        for b in _blocks(d):
            tid = _str(b.get("tool_use_id"))
            if tid is not None and tid in uses:
                named = uses[tid]
                out[agent_id] = named or f"(생략→{_str(result.get('agentType')) or '?'})"
    return out


def meta_type(sub_path: Path) -> str | None:
    meta = sub_path.with_name(sub_path.stem + ".meta.json")
    try:
        data = _parse_json(meta.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return _str(_obj(data).get("agentType"))


@dataclass
class _Response:
    """응답 하나의 줄들. 첫 줄의 기록, 출력 토큰이 가장 큰 usage, 첫 줄 번호, 시각이 있는 첫 줄의
    시각."""

    first: dict[str, Json]
    usage: dict[str, Json]
    line: int
    at: datetime | None


def _cache_writes(u: dict[str, Json]) -> tuple[int, int]:
    """TTL 갈래가 없거나 합이 맞지 않으면 남는 쓰기를 5분으로 본다(싼 쪽)."""
    total = _int(u.get("cache_creation_input_tokens"))
    cc = _obj(u.get("cache_creation"))
    w5 = _int(cc.get("ephemeral_5m_input_tokens"))
    w1 = _int(cc.get("ephemeral_1h_input_tokens"))
    if w5 + w1 != total:
        w1 = min(w1, total)
        w5 = total - w1
    return w5, w1


def read_stream(key: StreamKey, copy: Copy, agent_type: str | None) -> Ledger:
    """기록 파일 하나를 장부 행으로 옮긴다."""
    session, agent = key
    records, bad = read_records(copy.path)
    out = Ledger()
    order: list[str] = []
    responses: dict[str, _Response] = {}
    stamps: list[tuple[int, datetime]] = []
    for rec in records:
        d = rec.data
        t = _time(d.get("timestamp"))
        if t is not None:
            stamps.append((rec.line, t))
        if d.get("type") != "assistant":
            continue
        m = _obj(d.get("message"))
        u = m.get("usage")
        model = _str(m.get("model")) or "(모름)"
        if not isinstance(u, dict) or model == "<synthetic>":
            continue
        mid = _str(m.get("id")) or _str(d.get("uuid")) or f"{copy.path.name}:{rec.line}"
        seen = responses.get(mid)
        if seen is None:
            order.append(mid)
            responses[mid] = _Response(d, u, rec.line, t)
            continue
        if seen.at is None:
            seen.at = t
        if _int(u.get("output_tokens")) > _int(seen.usage.get("output_tokens")):
            seen.usage = u
    prev: datetime | None = None
    for mid in order:
        r = responses[mid]
        d, u, t = r.first, r.usage, r.at
        m = _obj(d.get("message"))
        if t is None:
            # 어느 줄에도 시각이 없는 응답은 날에 귀속하지 못해 읽지 못한 줄로 센다.
            bad.append(r.line)
            continue
        w5, w1 = _cache_writes(u)
        inp = _int(u.get("input_tokens"))
        read = _int(u.get("cache_read_input_tokens"))
        out.calls.append(
            Call(
                id=mid,
                at=_iso(t),
                session=session,
                agent=agent,
                agent_type=agent_type,
                project=copy.folder,
                branch=_str(d.get("gitBranch")),
                model=_str(m.get("model")) or "(모름)",
                effort=_str(d.get("effort")),
                input=inp,
                cache_read=read,
                cache_write_5m=w5,
                cache_write_1h=w1,
                output=_int(u.get("output_tokens")),
                context=inp + read + w5 + w1,
                gap_s=None if prev is None else round((t - prev).total_seconds(), 3),
            )
        )
        prev = t
    if agent is None and stamps:
        out.sessions.append(SessionRow(session, _iso(min(stamps, key=lambda s: s[0])[1])))
    fallback = datetime.fromtimestamp(copy.mtime, UTC)
    lines = [n for n, _ in stamps]
    for line in sorted(set(bad)):
        i = bisect.bisect_left(lines, line)
        at = stamps[i - 1][1] if i else (stamps[i][1] if stamps else fallback)
        out.unreadable.append(Unreadable(session, agent, copy.path.name, line, _iso(at)))
    return out


# 시간대와 달


def parse_tz(text: str) -> timezone:
    m = re.fullmatch(r"([+-])(\d{2}):(\d{2})", text)
    if m is None:
        raise argparse.ArgumentTypeError(f"시간대는 +09:00 같은 고정 오프셋이다: {text}")
    delta = timedelta(hours=int(m.group(2)), minutes=int(m.group(3)))
    return timezone(-delta if m.group(1) == "-" else delta)


def local_date(at: str, tz: timezone) -> date:
    t = _time(at)
    return t.astimezone(tz).date() if t is not None else date.min


def month_of(at: str, tz: timezone) -> str:
    return local_date(at, tz).strftime("%Y-%m")


def _row_time(r: Call | SessionRow | Unreadable) -> str:
    return r.start if isinstance(r, SessionRow) else r.at


def _prev_month(month: str) -> str:
    y, m = (int(x) for x in month.split("-"))
    return f"{y - 1}-12" if m == 1 else f"{y}-{m - 1:02}"


# 파일 쓰기


def write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        os.replace(tmp, path)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise


def is_link(p: Path) -> bool:
    return p.is_symlink() or p.is_junction()


class LockedError(Exception):
    pass


class Lock:
    """출력 폴더의 잠금 파일. 이미 있으면 기다리지 않고 `LockedError`를 낸다."""

    def __init__(self, out: Path) -> None:
        self.path = out / LOCK

    def __enter__(self) -> Lock:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as e:
            raise LockedError(str(self.path)) from e
        os.close(fd)
        return self

    def __exit__(self, *_: object) -> None:
        self.path.unlink(missing_ok=True)


# ingest


def _owner_rank(
    c: Call, starts: dict[str, str], held: dict[str, StreamKey]
) -> tuple[int, datetime, str, str]:
    """같은 응답 ID의 행 가운데 남길 것의 순위(작을수록 앞). 시작 모를 세션이 직전 장부에서 그
    응답을 가졌으면 그대로 갖고, 시작을 아는 세션끼리는 이른 쪽이 이기며, 나머지 시작 모를 세션은
    진다."""
    start = _time(starts.get(c.session))
    if start is not None:
        return (1, start, c.session, c.agent or "")
    rank = 0 if held.get(c.id) == _stream_of(c) else 2
    return (rank, _NO_TIME, c.session, c.agent or "")


def _sorted_rows(rows: Iterable[Call | SessionRow | Unreadable]) -> list[dict[str, Json]]:
    def key(r: Call | SessionRow | Unreadable) -> tuple[str, str, str, str, str]:
        if isinstance(r, SessionRow):
            return ("0", r.start, r.session, "", "")
        if isinstance(r, Call):
            return ("1", r.at, r.session, r.agent or "", r.id)
        return ("2", r.at, r.session, r.agent or "", f"{r.line:09d}")

    return [r.row() for r in sorted(rows, key=key)]


type Row = Call | SessionRow | Unreadable
type Placed = tuple[str, Row]


def changed_since(out: Path) -> float | None:
    """지난 `ingest`의 한 시간 전(유닉스 시각). `state.json`이 없거나 읽지 못하면 None이다."""
    state_path = out / "state.json"
    if not state_path.is_file():
        return None
    last = _time(_obj(_parse_json(state_path.read_text(encoding="utf-8"))).get("last_ingest"))
    return None if last is None else last.timestamp() - 3600


def _agent_type(
    key: StreamKey,
    copy: Copy,
    streams: dict[StreamKey, list[Copy]],
    parents: dict[str, dict[str, str]],
) -> str | None:
    """서브에이전트 유형. `meta.json`을 먼저 보고, 없으면 부모 기록의 Agent 호출로 잇는다."""
    session, agent = key
    if agent is None:
        return None
    found = meta_type(copy.path)
    if found is not None or (session, None) not in streams:
        return found
    if session not in parents:
        parents[session] = agent_types(read_records(longest(streams[(session, None)]).path)[0])
    return parents[session].get(agent)


def _read_changed(
    streams: dict[StreamKey, list[Copy]], changed: list[StreamKey]
) -> tuple[Ledger, set[StreamKey]]:
    """바뀐 기록을 읽는다. 훑은 뒤 지워진 기록은 건너뛰어 그 기록의 옛 행이 남는다."""
    parents: dict[str, dict[str, str]] = {}
    fresh = Ledger()
    keys: set[StreamKey] = set()
    for key in changed:
        copy = longest(streams[key])
        try:
            rows = read_stream(key, copy, _agent_type(key, copy, streams, parents))
        except FileNotFoundError:
            continue
        fresh.extend(rows)
        keys.add(key)
    return fresh, keys


def _place(
    old_months: dict[str, Ledger], fresh: Ledger, fresh_keys: set[StreamKey], tz: timezone
) -> tuple[list[Placed], dict[str, StreamKey]]:
    """달 파일에 둘 행과 직전 장부의 응답 주인. 다시 읽은 기록의 옛 행은 새 행으로 갈아 끼우되,
    새로 읽은 사본에 없는 응답(긴 사본이 지워져 짧은 사본을 읽었을 때)의 옛 행은 남긴다. 다시 읽지
    않은 행은 읽어 온 달 파일에 그대로 둔다. 시간대 인자가 바뀌어도 읽지 않은 달 파일로 옮겨 그
    파일을 덮지 않게 하기 위해서다. 새로 읽은 행만 지금 시간대로 달을 가른다."""
    fresh_ids = {(_stream_of(c), c.id) for c in fresh.calls}
    placed: list[Placed] = []
    held: dict[str, StreamKey] = {}
    for month, old in old_months.items():
        held.update((c.id, _stream_of(c)) for c in old.calls)
        placed += [(month, c) for c in old.calls if (_stream_of(c), c.id) not in fresh_ids]
        placed += [(month, s) for s in old.sessions if _stream_of(s) not in fresh_keys]
        placed += [(month, u) for u in old.unreadable if _stream_of(u) not in fresh_keys]
    fresh_rows: list[Row] = [*fresh.calls, *fresh.sessions, *fresh.unreadable]
    placed += [(month_of(_row_time(r), tz), r) for r in fresh_rows]
    return placed, held


def choose_owners(placed: list[Placed], held: dict[str, StreamKey]) -> list[Placed]:
    """응답 ID마다 한 행만 남긴다(`_owner_rank`). 호출 행이 아닌 행은 그대로 둔다."""
    starts = {r.session: r.start for _, r in placed if isinstance(r, SessionRow)}
    owner: dict[str, tuple[str, Call]] = {}
    for month, r in placed:
        if not isinstance(r, Call):
            continue
        prev = owner.get(r.id)
        if prev is None or _owner_rank(r, starts, held) < _owner_rank(prev[1], starts, held):
            owner[r.id] = (month, r)
    return [*owner.values(), *((m, r) for m, r in placed if not isinstance(r, Call))]


def ingest(projects: Path, out: Path, tz: timezone, since: float | None) -> None:
    """`since`(유닉스 시각)보다 뒤에 바뀐 기록을 다시 읽어 장부를 갱신한다. None이면 남은 기록을
    모두 다시 읽고 모든 달 파일과 견준다."""
    if not projects.is_dir():
        # state를 올리면 다음 실행이 그 앞의 기록을 건너뛴다.
        raise ToolError(f"세션 기록 폴더가 없다: {projects}. 장부와 state.json을 그대로 둔다")
    started = time.time()
    ledger_dir = out / "ledger"
    streams = discover(projects)
    changed = [
        k
        for k, copies in sorted(streams.items(), key=lambda kv: (kv[0][0], kv[0][1] or ""))
        if since is None or any(c.mtime > since for c in copies)
    ]
    fresh, fresh_keys = _read_changed(streams, changed)
    existing = sorted(
        m.group(1)
        for name in (os.listdir(ledger_dir) if ledger_dir.is_dir() else [])
        if (m := MONTH_NAME.fullmatch(name))
    )
    fresh_rows: list[Row] = [*fresh.calls, *fresh.sessions, *fresh.unreadable]
    load: list[str] = []
    if fresh_rows:
        first = min(month_of(_row_time(r), tz) for r in fresh_rows)
        load = existing if since is None else [m for m in existing if m >= _prev_month(first)]
    old_months = {m: read_ledger_file(ledger_dir / f"{m}.jsonl") for m in load}
    placed, held = _place(old_months, fresh, fresh_keys, tz)
    by_month: dict[str, list[Row]] = {m: [] for m in load}
    for month, r in choose_owners(placed, held):
        by_month.setdefault(month, []).append(r)
    for month, rows in sorted(by_month.items()):
        body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in _sorted_rows(rows))
        write_atomic(ledger_dir / f"{month}.jsonl", body)
    state: dict[str, Json] = {
        "v": FORMAT,
        "last_ingest": _iso(datetime.fromtimestamp(started, UTC)),
    }
    write_atomic(out / "state.json", json.dumps(state) + "\n")
    print(f"기록 파일 {len(changed)}개를 다시 읽고 달 파일 {len(by_month)}개를 썼다: {ledger_dir}")


# 계정


def read_accounts(path: Path) -> dict[str, str]:
    """세션 ID -> 계정 이름(이메일, 없으면 계정 ID). `account_uuid`가 null인 줄은 앞을 덮지
    않는다."""
    accounts: dict[str, str] = {}
    if not path.is_file():
        return accounts
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            r = _obj(_parse_json(line))
        except json.JSONDecodeError:
            continue
        sid = _str(r.get("session_id"))
        uuid = _str(r.get("account_uuid"))
        if sid is not None and uuid is not None:
            accounts[sid] = _str(r.get("email")) or uuid
    return accounts


# report


def _money(v: float) -> str:
    return f"{v:,.2f}"


def _share(part: float, total: float) -> str:
    return f"{part / total:.1%}" if total > 0 else "해당 없음"


def _table(head: list[str], align: str, rows: list[list[str]]) -> list[str]:
    if not rows:
        return ["해당 없음"]
    return [
        "| " + " | ".join(head) + " |",
        "|" + "|".join("--:" if a == "r" else "---" for a in align) + "|",
        *("| " + " | ".join(r) + " |" for r in rows),
    ]


@dataclass
class Tally:
    cost: float = 0.0
    calls: int = 0

    def add(self, c: float | None) -> None:
        self.cost += c or 0.0
        self.calls += 1


@dataclass
class SessionTally:
    tally: Tally = field(default_factory=Tally)
    max_context: int = 0
    project: str = ""
    branch: str | None = None
    last_main: str = ""


@dataclass
class Day:
    day: date
    calls: list[Call]
    unreadable: int
    total: Tally = field(default_factory=Tally)
    accounts: dict[str, Tally] = field(default_factory=dict[str, Tally])
    kinds: dict[str, Tally] = field(default_factory=dict[str, Tally])
    models: dict[tuple[str, str, str], Tally] = field(
        default_factory=dict[tuple[str, str, str], Tally]
    )
    types: dict[str, Tally] = field(default_factory=dict[str, Tally])
    sessions: dict[str, SessionTally] = field(default_factory=dict[str, SessionTally])
    unknown_models: dict[str, int] = field(default_factory=dict[str, int])


def tally_day(day: date, calls: list[Call], unreadable: int, accounts: dict[str, str]) -> Day:
    d = Day(day, calls, unreadable)
    d.kinds = {"메인 세션": Tally(), "서브에이전트": Tally()}
    for c in sorted(calls, key=lambda c: (c.at, c.session, c.agent or "", c.id)):
        cost = c.cost()
        if cost is None:
            d.unknown_models[c.model] = d.unknown_models.get(c.model, 0) + 1
        kind = "메인 세션" if c.agent is None else "서브에이전트"
        model = c.model.removeprefix("claude-")
        d.total.add(cost)
        d.accounts.setdefault(accounts.get(c.session, UNKNOWN_ACCOUNT), Tally()).add(cost)
        d.kinds[kind].add(cost)
        d.models.setdefault((kind, model, c.effort or "(없음)"), Tally()).add(cost)
        if c.agent is not None:
            d.types.setdefault(c.agent_type or "(미상)", Tally()).add(cost)
        s = d.sessions.setdefault(c.session, SessionTally())
        s.tally.add(cost)
        if c.agent is None:
            s.max_context = max(s.max_context, c.context)
            s.project, s.branch, s.last_main = c.project, c.branch, c.at
        elif not s.project:
            s.project = c.project
    return d


def _by_cost[K](items: dict[K, Tally]) -> list[tuple[K, Tally]]:
    return sorted(items.items(), key=lambda kv: (-kv[1].cost, -kv[1].calls, str(kv[0])))


@dataclass(frozen=True)
class Alarms:
    alarms: list[str]
    notes: list[str]


def alarms_of(d: Day, previous: list[Day]) -> Alarms:
    alarms: list[str] = []
    notes: list[str] = []
    busy = [p.total.cost for p in previous if p.total.calls]
    if len(busy) < MIN_DAYS:
        notes.append(
            f"비용 급증은 비교하지 않았다: 지난 7일 가운데 호출이 있던 날이 {len(busy)}일로"
            " 넷보다 적다"
        )
    else:
        median = statistics.median(busy)
        if d.total.cost > median * SPIKE:
            alarms.append(
                f"경보: 환산 비용 ${_money(d.total.cost)}이 지난 7일 가운데 호출이 있던"
                f" {len(busy)}일의 중앙값 ${_money(median)}의 {SPIKE}배를 넘는다"
            )
    parts: list[str] = []
    if d.unknown_models:
        n = sum(d.unknown_models.values())
        parts.append(f"단가표에 없는 모델의 호출 {n}회({', '.join(sorted(d.unknown_models))})")
    if d.unreadable:
        parts.append(f"읽지 못한 기록 줄 {d.unreadable}개")
    if parts:
        alarms.append("경보: " + ", ".join(parts))
    return Alarms(alarms, notes)


def render_day(d: Day, a: Alarms, starts: dict[str, str], tz: timezone) -> str:
    total = d.total.cost
    lines = [
        f"# 토큰 사용 일간 보고서: {d.day.isoformat()}",
        "",
        f"지역 시간대 {_tz_text(tz)}의 하루다. 비용은 장부의 토큰에 단가표"
        "(`tools/token_report.py`의 `PRICES`)를 곱한 API 환산 달러다.",
        "",
    ]
    if not d.total.calls:
        lines += ["호출 없음", ""]
    lines += ["## 1. 경보", ""]
    lines += [f"- {x}" for x in a.alarms] or ["- 없음"]
    lines += [f"- {x}" for x in a.notes]
    lines += [
        "",
        "## 2. 합계와 계정별",
        "",
        f"모델 호출 {d.total.calls}회, 환산 비용 ${_money(total)}",
        "",
    ]
    money = ["환산 비용($)", "몫", "호출"]
    calls = d.total.calls > 0
    lines += _table(
        ["계정", *money],
        "lrrr",
        [[k, _money(v.cost), _share(v.cost, total), str(v.calls)] for k, v in _by_cost(d.accounts)],
    )
    lines += ["", "## 3. 메인 세션과 서브에이전트", ""]
    lines += _table(
        ["구분", *money],
        "lrrr",
        [
            [k, _money(v.cost), _share(v.cost, total), str(v.calls)]
            for k, v in d.kinds.items()
            if calls
        ],
    )
    lines += ["", "## 4. 모델·노력별", ""]
    lines += _table(
        ["구분", "모델", "노력", *money],
        "lllrrr",
        [
            [k[0], k[1], k[2], _money(v.cost), _share(v.cost, total), str(v.calls)]
            for k, v in _by_cost(d.models)
        ],
    )
    lines += ["", "## 5. 서브에이전트 유형별", "", "몫은 그날 전체 비용에 대한 것이다.", ""]
    lines += _table(
        ["유형", *money],
        "lrrr",
        [[k, _money(v.cost), _share(v.cost, total), str(v.calls)] for k, v in _by_cost(d.types)],
    )
    lines += [
        "",
        "## 6. 상위 세션 다섯",
        "",
        "비용과 호출은 메인 세션과 그 서브에이전트를 합친 것이고,"
        " 세션 컨텍스트는 메인 세션의 것이다.",
        "",
    ]
    top = sorted(d.sessions.items(), key=lambda kv: (-kv[1].tally.cost, -kv[1].tally.calls, kv[0]))
    lines += _table(
        ["세션", "기록 폴더", "브랜치", "시작", "환산 비용($)", "최대 세션 컨텍스트", "호출"],
        "llllrrr",
        [
            [
                sid[:8],
                s.project,
                s.branch or "(모름)",
                _local_text(starts.get(sid), tz),
                _money(s.tally.cost),
                f"{s.max_context:,}",
                str(s.tally.calls),
            ]
            for sid, s in top[:5]
        ],
    )
    return "\n".join(lines) + "\n"


def _tz_text(tz: timezone) -> str:
    off = tz.utcoffset(None)
    sign = "-" if off < timedelta(0) else "+"
    minutes = abs(int(off.total_seconds())) // 60
    return f"{sign}{minutes // 60:02}:{minutes % 60:02}"


def _local_text(at: str | None, tz: timezone) -> str:
    t = _time(at)
    return t.astimezone(tz).strftime("%Y-%m-%d %H:%M") if t is not None else "(모름)"


def render_summary(d: Day, a: Alarms, report: Path) -> str:
    head = f"환산 비용 ${_money(d.total.cost)}"
    if d.total.calls:
        head += " (" + ", ".join(f"{k} ${_money(v.cost)}" for k, v in _by_cost(d.accounts)) + ")"
    lines = [f"보고서 날짜: {d.day.isoformat()}", head, *(a.alarms or ["경보 없음"])]
    lines.append(f"보고서: {report}")
    return "\n".join(lines) + "\n"


def _months(days: Iterable[date]) -> list[str]:
    return sorted({d.strftime("%Y-%m") for d in days})


def stale_reports(daily: Path, keep_from: date) -> list[Path]:
    """그 이름 모양의 보통 파일 가운데 보고할 7일(`keep_from`부터)보다 이른 날의 것. 링크·폴더,
    그보다 뒤의 날(다른 `--today`로 만든 것)은 들지 않는다."""
    return sorted(
        p
        for p in daily.iterdir()
        if DAILY_NAME.fullmatch(p.name)
        and p.name < f"{keep_from.isoformat()}.md"
        and not is_link(p)
        and p.is_file()
    )


def read_session_rows(path: Path) -> list[SessionRow]:
    """달 파일의 세션 행. 세션 행이 파일 머리에 모여 있어(`_sorted_rows`) 다른 행에서 멈춘다."""
    rows: list[SessionRow] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            r = _obj(_parse_json(line))
            if r.get("kind") != "session":
                break
            rows.append(SessionRow(_str(r.get("session")) or "", _str(r.get("start")) or ""))
    return rows


def report(out: Path, tz: timezone, today: date) -> None:
    daily = out / "daily"
    if is_link(daily):
        raise ToolError(f"보고서 폴더가 링크라 쓰지도 지우지도 않는다: {daily}")
    last = today - timedelta(days=1)
    window = [last - timedelta(days=i) for i in range(KEEP_DAILY - 1, -1, -1)]
    span = [last - timedelta(days=i) for i in range(KEEP_DAILY + 7)]
    # 앞뒤 하루를 더 읽는다. 시간대 인자가 실행마다 다르면 행이 이웃 달 파일에 들 수 있다.
    wide = [span[-1] - timedelta(days=1), *span, last + timedelta(days=1)]
    ledger_dir = out / "ledger"
    ledger = Ledger()
    for month in _months(wide):
        p = ledger_dir / f"{month}.jsonl"
        if p.is_file():
            ledger.extend(read_ledger_file(p))
    accounts = read_accounts(ledger_dir / "accounts.jsonl")
    # 상위 세션의 시작은 그 세션이 시작한 달 파일에 있다. 앞선 달은 세션 행만 읽는다.
    starts: dict[str, str] = {}
    for name in sorted(os.listdir(ledger_dir) if ledger_dir.is_dir() else []):
        if MONTH_NAME.fullmatch(name) and name.removesuffix(".jsonl") < _months(wide)[0]:
            starts.update((s.session, s.start) for s in read_session_rows(ledger_dir / name))
    starts.update((s.session, s.start) for s in ledger.sessions)
    calls_by: dict[date, list[Call]] = defaultdict(list)
    for c in ledger.calls:
        calls_by[local_date(c.at, tz)].append(c)
    bad_by: dict[date, int] = defaultdict(int)
    for u in ledger.unreadable:
        bad_by[local_date(u.at, tz)] += 1
    days = {d: tally_day(d, calls_by[d], bad_by[d], accounts) for d in span}
    daily.mkdir(parents=True, exist_ok=True)
    summary = ""
    for d in window:
        alarms = alarms_of(days[d], [days[d - timedelta(days=i)] for i in range(1, 8)])
        path = daily / f"{d.isoformat()}.md"
        write_atomic(path, render_day(days[d], alarms, starts, tz))
        summary = render_summary(days[d], alarms, path)
    write_atomic(out / "summary.txt", summary)
    gone = stale_reports(daily, window[0])
    for p in gone:
        p.unlink(missing_ok=True)
    print(f"일간 보고서 {len(window)}개를 쓰고 {len(gone)}개를 지웠다: {daily}")


class ToolError(Exception):
    pass


# 경로


def folder_name_of(checkout: Path) -> str:
    """Claude Code가 그 체크아웃의 세션 기록을 두는 폴더 이름. 영문자와 숫자 밖의 글자를 `-`로
    바꾼다(`C:\\project\\agent`는 `C--project-agent`, 2026-10-16 폴더 목록으로 손으로 봤다)."""
    return re.sub(r"[^A-Za-z0-9]", "-", str(checkout))


def main_checkout() -> Path:
    """이 파일이 든 저장소의 git 공용 디렉터리의 부모."""
    done = subprocess.run(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=Path(__file__).resolve().parent,
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        check=True,
    )
    return Path(done.stdout.strip()).parent


def _today(text: str) -> date:
    try:
        return date.fromisoformat(text)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"날짜는 YYYY-MM-DD다: {text}") from e


def _parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--projects", type=Path, help="세션 기록 폴더(기본 ~/.claude/projects)")
    common.add_argument(
        "--out", type=Path, help="출력 폴더(기본 주 체크아웃의 .scratch/token-report)"
    )
    common.add_argument("--tz", type=parse_tz, help="지역 시간대, +09:00 같은 고정 오프셋")
    common.add_argument(
        "--today", type=_today, help="오늘 날짜 YYYY-MM-DD(기본 지역 시간대의 오늘)"
    )
    parser = argparse.ArgumentParser(
        prog="token_report.py", description="토큰 사용량 장부와 보고서. 자세한 것은 독스트링."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    ing = sub.add_parser("ingest", parents=[common], help="세션 기록을 읽어 장부를 갱신한다")
    ing.add_argument("--full", action="store_true", help="state.json을 무시하고 모두 다시 읽는다")
    sub.add_parser("report", parents=[common], help="장부에서 일간 보고서와 요약을 만든다")
    sub.add_parser("daily", parents=[common], help="ingest와 report를 차례로 한다")
    return parser


def main(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    command: str = args.command
    projects: Path = args.projects or Path.home() / ".claude" / "projects"
    tz: timezone = args.tz or parse_tz(_tz_text(_local_tz()))
    today: date = args.today or datetime.now(tz).date()
    try:
        out: Path = args.out or main_checkout() / ".scratch" / "token-report"
    except (OSError, subprocess.SubprocessError) as e:
        print(f"주 체크아웃을 찾지 못했다. --out을 준다: {e}", file=sys.stderr)
        return 2
    try:
        with Lock(out):
            if command != "report":
                since = None if getattr(args, "full", False) else changed_since(out)
                ingest(projects, out, tz, since)
            if command != "ingest":
                report(out, tz, today)
    except LockedError as e:
        print(f"다른 실행이 도는 중이라 멈춘다. 잠금 파일: {e}", file=sys.stderr)
        print("멈춘 실행이 남긴 잠금이면 그 파일을 지우고 다시 돌린다.", file=sys.stderr)
        return 3
    except ToolError as e:
        print(str(e), file=sys.stderr)
        return 2
    return 0


def _local_tz() -> timezone:
    off = datetime.now().astimezone().utcoffset() or timedelta(0)
    return timezone(off)


if __name__ == "__main__":
    # 윈도의 파이프는 PYTHONUTF8이 없으면 cp949다. 한글 출력이 깨지지 않게 고정한다.
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1:]))
