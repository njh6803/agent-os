"""아침 보고(일일 보고)를 그린다. 아침 보고 예약 작업이 `tools/morning_collect.py` 다음에 부른다.

보고는 두 손이 함께 쓴다. 수치와 표는 수집 도구가 JSON(`<날짜>.data.json`, `Data`)으로 내고, 작업
이름·요약·할 일·제안·해석은 예약 작업의 모델이 메모 JSON(`<날짜>.notes.json`, `Notes`)으로 쓴다. 이
도구는 둘을 합쳐 `<날짜>.md`를 그린다. 모델이 수치를 손으로 옮기던 판(2026-10-20 시험 보고)은 같은
사실이 여러 절에 되풀이되고(워크트리 20개·claude 프로세스 54개와 `/tidy-checkouts` 권고가 "한눈에
보기"와 "병렬 세션 최적화" 두 절에) PR 번호가 이름 없이 괄호에만 적혔다(`(#301)`). 그래서 수치는
모델의 손을 거치지 않고, 작업 이름은 이 도구가 붙인다.

그리는 것(차례를 바꾸지 않는다).
- 머리: 경보·직접 하실 일·개선 제안의 수.
- 핵심 지표: 지표마다 어제, 전날, 어제까지 7일의 추이(`SPARK`), 7일 기준(그날을 뺀 앞 7일 가운데
  값이 있는 날의 중앙값), 판정. 판정은 수집 도구가 경보로 넘긴 지표면 `⚠ 경보 (<까닭>)`, 아니면 7일
  안의 최고·최저, 아니면 정상이다. 경보 문장은 이 칸에만 있다.
- 직접 하실 일: 메모의 할 일. 대기열 행이면 제목을 `대기열 <번호> (<회차>회차) <이름>`으로 짓는다.
- 개선 제안: 표와, 표 아래 접힌 "바꿀 것". 상태는 지난 상태 파일(`<날짜>.state.json`)과 견줘
  `신규`, `효과 확인됨`(확인할 수치가 바라는 쪽으로 움직였다)이다. 진행 중과 보류는 제안과 PR을 잇는
  기록이 없어 `UNKNOWN_STATE`로 적는다. 확인할 수치의 열쇠가 지난 상태와 다르면 견주지 않는다.
- 상세: 머리에 수집 JSON과 모은 시각을 적고, 절마다 `<details>`로 접고 끝에 원본을 한 줄로 적는다.

작업 표기. 작업이 나오는 곳에는 번호·이름·내용을 함께 쓰되, 내용은 그 작업이 처음 나온 자리에만
쓰고 뒤에서는 번호와 이름만 쓴다. 수집 도구의 칸은 `{{name:N}}`·`{{content:N}}`(PR),
`{{qname:N}}`·`{{qcontent:N}}`(대기열 행), `{{branch:B}}`(브랜치), `{{group:N}}`(병합 PR의 분류)로
자리를 남기고, 표의 내용 칸은 뒤에서 `→ <처음 나온 자리>`로 가리킨다. 수집 도구가 쓴 줄은
`{{ref:N}}`, 모델이 쓴 글은 `#N`과 `대기열 N`을 찾아 같은 규칙으로 `<번호> <이름>(<내용>)`을 붙인다.
PR 제목을 가져오지 못했으면 `LOOKUP_FAILED`로 적는다(이름을 지을 근거가 없어 경고하지 않는다).
메모에 이름이 없으면 `NO_NAME`, 내용이 없으면 `NO_CONTENT`로 적고 경고한다.

경고하는 것(stderr, 그리기는 그대로 한다).
- 메모에 이름이나 내용이 없는 작업, 번호 바로 뒤에 조사가 붙은 작업 번호(이름을 끼우면 받침이
  어긋난다).
- 할 일의 까닭이 두 문장 이상이거나(`SENTENCE_END`), 제안의 난이도가 `DIFFICULTIES` 밖의 낱말이다.
- 상세 절의 목록 줄 수가 `MAX_LIST`를 넘는다. 수집 줄과 메모 줄을 나눠 세고, 메모가 그 절에 쓸 수
  있는 줄 수를 알린다.
- 메모 JSON을 읽지 못했다(빈 메모로 그린다). 예약 작업은 `경고:` 줄마다 메모를 고치므로 이것도
  경고다.

못 보는 것.
- 메모의 글이 사실인지는 보지 않는다. 수치는 표에서만 오고, 글은 해석이다.
- 모델이 글에 작업 번호를 `#N`·`대기열 N` 꼴이 아닌 모양(`PR 301`)으로 쓰면 이름을 붙이지 않는다.
  `대기열 238·243`처럼 번호를 이어 쓰면 앞 번호에만 붙인다. `대기열 3회`처럼 수 뒤에 세는 말
  (`COUNTERS`)이 붙으면 행 번호로 보지 않으므로, `대기열 238건` 같은 행 번호도 놓친다.
- 문장 수는 `다.`로 끝나는 문장만 센다. `…함.`이나 물음표로 끝나는 문장은 세지 않는다.
- 같은 사실이 두 절에 되풀이되는지는 표의 자리로만 막는다. 모델의 글이 표의 수치를 다시 적으면
  막지 못한다.

쓰임: `uv run python tools/morning_report.py --reports <폴더> --day YYYY-MM-DD`. 종료 0은
그렸다(경고는 stderr), 2는 수집 JSON을 읽지 못했다.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import statistics
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime
from pathlib import Path

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

FORMAT = 2
SPARK = "▁▂▃▄▅▆▇█"
GAP = "·"
LOOKUP_FAILED = "(제목 조회 실패)"
NO_NAME = "(이름 없음)"
NO_CONTENT = "(내용 없음)"
UNCOLLECTED = "(수집 안 됨)"
MAX_LIST = 5
NEXT_SECTION = 6  # 메모의 다음 할 일을 붙이는 상세 절(어제 작업과 다음 할 일)
UNITS = {"money": "$", "int": "", "float1": "", "float2": ""}  # `Metric.kind`마다 값의 단위
UNKNOWN_STATE = "(진행 중·보류는 수집 안 됨)"
PLACEHOLDER = re.compile(r"\{\{(name|content|qname|qcontent|ref|branch|group):([^{}]+)\}\}")
COUNTERS = "회개줄행건"  # `대기열 3회`처럼 수 뒤에 붙으면 행 번호가 아니라 셈이다
REF = re.compile(rf"#(\d+)|대기열 (\d+)(?![\d{COUNTERS}])")
PR_KIND = re.compile(r"^(\w+)(?:\(.*?\))?!?:")
HANGUL = re.compile(r"[가-힣]")
SENTENCE_END = re.compile(r"(?<=다)\.(?:\s|$)")
DIFFICULTIES = ("쉬움", "보통", "어려움")


# JSON 풀이. `json_*`는 수집 도구(`morning_collect`·`morning_sources`)도 가져다 쓴다. 이 도구는
# 스크립트로 돌아 `tools` 패키지를 가져오지 못하므로 함께 쓰는 것을 이 파일에 둔다.


def json_obj(v: Json) -> dict[str, Json]:
    return v if isinstance(v, dict) else {}


def json_list(v: Json) -> list[Json]:
    return v if isinstance(v, list) else []


def json_str(v: Json) -> str:
    return v if isinstance(v, str) else ""


def json_int(v: Json) -> int | None:
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def json_time(v: Json) -> datetime | None:
    """ISO 시각. 시간대가 없으면 UTC로 읽는다."""
    try:
        t = datetime.fromisoformat(json_str(v))
    except ValueError:
        return None
    return t if t.tzinfo is not None else t.replace(tzinfo=UTC)


def _num(v: Json) -> float | None:
    if isinstance(v, bool):
        return None
    return float(v) if isinstance(v, int | float) else None


def _strs(v: Json) -> tuple[str, ...]:
    return tuple(json_str(x) for x in json_list(v))


def _day(v: Json) -> date | None:
    try:
        return date.fromisoformat(json_str(v))
    except ValueError:
        return None


def pr_kind(title: str) -> str:
    """PR 제목의 앞머리(`fix(test): …`의 `fix`). 없으면 `(없음)`이다."""
    m = PR_KIND.match(title)
    return m.group(1) if m else "(없음)"


# 수집 JSON


@dataclass(frozen=True)
class Metric:
    """핵심 지표 한 줄. `series`는 보고하는 날의 7일 앞부터 그날까지 여덟 값이고, 값이 없는 날은
    None이다. 그 값을 아예 모으지 못했으면(gh 실패) 빈 튜플이다. `alarm`이 None이면 경보가 아니고,
    빈 글이면 까닭 없는 경보다."""

    key: str
    label: str
    kind: str
    series: tuple[float | None, ...]
    alarm: str | None

    def to_json(self) -> Json:
        series: list[Json] = list(self.series)
        return {
            "key": self.key,
            "label": self.label,
            "kind": self.kind,
            "series": series,
            "alarm": self.alarm,
        }

    @staticmethod
    def of(j: Json) -> Metric:
        o = json_obj(j)
        alarm = o.get("alarm")
        return Metric(
            json_str(o.get("key")),
            json_str(o.get("label")),
            json_str(o.get("kind")),
            tuple(_num(x) for x in json_list(o.get("series"))),
            alarm if isinstance(alarm, str) else None,
        )


@dataclass(frozen=True)
class Table:
    head: tuple[str, ...]
    align: str
    rows: tuple[tuple[str, ...], ...]

    def to_json(self) -> Json:
        rows: list[Json] = [list(r) for r in self.rows]
        head: list[Json] = list(self.head)
        return {"head": head, "align": self.align, "rows": rows}

    @staticmethod
    def of(j: Json) -> Table:
        o = json_obj(j)
        return Table(
            _strs(o.get("head")),
            json_str(o.get("align")),
            tuple(_strs(r) for r in json_list(o.get("rows"))),
        )


@dataclass(frozen=True)
class Section:
    number: int
    title: str
    tables: tuple[Table, ...]
    lines: tuple[str, ...]
    source: str

    def to_json(self) -> Json:
        tables: list[Json] = [t.to_json() for t in self.tables]
        lines: list[Json] = list(self.lines)
        return {
            "number": self.number,
            "title": self.title,
            "tables": tables,
            "lines": lines,
            "source": self.source,
        }

    @staticmethod
    def of(j: Json) -> Section:
        o = json_obj(j)
        return Section(
            json_int(o.get("number")) or 0,
            json_str(o.get("title")),
            tuple(Table.of(t) for t in json_list(o.get("tables"))),
            _strs(o.get("lines")),
            json_str(o.get("source")),
        )


@dataclass(frozen=True)
class Pr:
    """이름을 지을 PR. `title`이 None이면 제목을 가져오지 못했다."""

    number: int
    title: str | None
    body: str
    branch: str

    def to_json(self) -> Json:
        return {"title": self.title, "body": self.body, "branch": self.branch}

    @staticmethod
    def of(number: int, j: Json) -> Pr:
        o = json_obj(j)
        title = o.get("title")
        return Pr(
            number,
            title if isinstance(title, str) else None,
            json_str(o.get("body")),
            json_str(o.get("branch")),
        )


@dataclass(frozen=True)
class QueueRow:
    number: int
    rounds: int | None
    human: bool
    what: str

    def to_json(self) -> Json:
        return {"rounds": self.rounds, "human": self.human, "what": self.what}

    @staticmethod
    def of(number: int, j: Json) -> QueueRow:
        o = json_obj(j)
        return QueueRow(
            number, json_int(o.get("rounds")), o.get("human") is True, json_str(o.get("what"))
        )


@dataclass(frozen=True)
class Value:
    """제안의 확인할 수치로 고를 수 있는 값."""

    label: str
    value: float
    unit: str

    def to_json(self) -> Json:
        return {"label": self.label, "value": self.value, "unit": self.unit}

    @staticmethod
    def of(j: Json) -> Value | None:
        o = json_obj(j)
        v = _num(o.get("value"))
        return None if v is None else Value(json_str(o.get("label")), v, json_str(o.get("unit")))


def _numbered[T](j: Json, make: Callable[[int, Json], T]) -> dict[int, T]:
    out: dict[int, T] = {}
    for k, v in json_obj(j).items():
        if k.isdigit():
            out[int(k)] = make(int(k), v)
    return out


@dataclass(frozen=True)
class Data:
    """수집 도구의 출력. `branches`는 PR이 없는 브랜치의 마지막 커밋 제목이고, `journal`은 가장
    최근 일지의 "다음" 절이다. `alarms`는 머리에 적는 경보 수이고 `token_report.alarms_of`가 센다.
    그래서 지표 표의 경보 줄 수와 다를 수 있다(단가표에 없는 모델과 읽지 못한 줄은 한 경보다)."""

    day: date
    made: str
    metrics: tuple[Metric, ...]
    values: dict[str, Value]
    sections: tuple[Section, ...]
    prs: dict[int, Pr]
    queue: dict[int, QueueRow]
    branches: dict[str, str]
    journal: str
    alarms: int

    def to_json(self) -> Json:
        metrics: list[Json] = [m.to_json() for m in self.metrics]
        sections: list[Json] = [s.to_json() for s in self.sections]
        values: dict[str, Json] = {k: v.to_json() for k, v in self.values.items()}
        prs: dict[str, Json] = {str(k): v.to_json() for k, v in self.prs.items()}
        queue: dict[str, Json] = {str(k): v.to_json() for k, v in self.queue.items()}
        branches: dict[str, Json] = {k: v for k, v in self.branches.items()}
        return {
            "format": FORMAT,
            "day": self.day.isoformat(),
            "made": self.made,
            "metrics": metrics,
            "values": values,
            "sections": sections,
            "prs": prs,
            "queue": queue,
            "branches": branches,
            "journal": self.journal,
            "alarms": self.alarms,
        }

    @staticmethod
    def of(j: Json) -> Data:
        """다른 형식의 수집 JSON은 칸이 빠져 조용히 틀리게 그리므로 읽지 않는다(ValueError)."""
        o = json_obj(j)
        if o.get("format") != FORMAT:
            raise ValueError(f"수집 JSON의 형식 {o.get('format')}이 이 도구의 {FORMAT}와 다르다")
        day = _day(o.get("day"))
        if day is None:
            raise ValueError("수집 JSON에 day가 없다")
        values = {
            k: v for k, x in json_obj(o.get("values")).items() if (v := Value.of(x)) is not None
        }
        return Data(
            day,
            json_str(o.get("made")),
            tuple(Metric.of(m) for m in json_list(o.get("metrics"))),
            values,
            tuple(Section.of(s) for s in json_list(o.get("sections"))),
            _numbered(o.get("prs"), Pr.of),
            _numbered(o.get("queue"), QueueRow.of),
            {k: json_str(v) for k, v in json_obj(o.get("branches")).items()},
            json_str(o.get("journal")),
            json_int(o.get("alarms")) or 0,
        )


# 메모 JSON


@dataclass(frozen=True)
class Named:
    name: str
    content: str
    group: str = ""

    @staticmethod
    def of(_number: int, j: Json) -> Named:
        o = json_obj(j)
        return Named(json_str(o.get("name")), json_str(o.get("content")), json_str(o.get("group")))


@dataclass(frozen=True)
class Todo:
    title: str
    why: str
    queue: int | None = None

    @staticmethod
    def of(j: Json) -> Todo:
        o = json_obj(j)
        return Todo(json_str(o.get("title")), json_str(o.get("why")), json_int(o.get("queue")))


@dataclass(frozen=True)
class Proposal:
    """`check`는 수집 JSON `values`의 열쇠, `better`는 그 값이 바라는 쪽(`down`·`up`)이다."""

    id: str
    title: str
    basis: str
    effect: str
    difficulty: str
    decision: str
    check: str
    better: str
    change: tuple[str, ...]

    @staticmethod
    def of(j: Json) -> Proposal:
        o = json_obj(j)
        return Proposal(
            json_str(o.get("id")),
            json_str(o.get("title")),
            json_str(o.get("basis")),
            json_str(o.get("effect")),
            json_str(o.get("difficulty")),
            json_str(o.get("decision")),
            json_str(o.get("check")),
            json_str(o.get("better")),
            _strs(o.get("change")),
        )


@dataclass(frozen=True)
class Notes:
    """모델이 쓰는 메모. `remarks`는 상세 절 번호마다의 해석 줄, `next`는 다음 할 일 줄이다."""

    prs: dict[int, Named]
    queue: dict[int, Named]
    branches: dict[str, str]
    todos: tuple[Todo, ...]
    proposals: tuple[Proposal, ...]
    remarks: dict[int, tuple[str, ...]]
    next: tuple[str, ...]

    @staticmethod
    def of(j: Json) -> Notes:
        o = json_obj(j)
        return Notes(
            _numbered(o.get("prs"), Named.of),
            _numbered(o.get("queue"), Named.of),
            {k: json_str(v) for k, v in json_obj(o.get("branches")).items()},
            tuple(Todo.of(t) for t in json_list(o.get("todos"))),
            tuple(Proposal.of(p) for p in json_list(o.get("proposals"))),
            _numbered(o.get("remarks"), lambda _n, v: _strs(v)),
            _strs(o.get("next")),
        )


# 지난 상태


@dataclass(frozen=True)
class Seen:
    """제안 하나의 상태. `since`는 처음 낸 날, `value`는 그날 보고의 확인할 수치, `check`는 그
    수치의 열쇠(`Proposal.check`)다. 열쇠가 바뀐 제안은 지난 값과 견주지 않는다."""

    since: date
    value: float | None
    check: str = ""


def read_state(j: Json) -> dict[str, Seen]:
    out: dict[str, Seen] = {}
    for k, v in json_obj(j).items():
        o = json_obj(v)
        since = _day(o.get("since"))
        if since is not None:
            out[k] = Seen(since, _num(o.get("value")), json_str(o.get("check")))
    return out


def state_json(state: Mapping[str, Seen]) -> Json:
    return {
        k: {"since": s.since.isoformat(), "value": s.value, "check": s.check}
        for k, s in state.items()
    }


# 핵심 지표


def sparkline(values: Sequence[float | None]) -> str:
    known = [v for v in values if v is not None]
    if not known:
        return GAP * len(values)
    lo, hi = min(known), max(known)
    out: list[str] = []
    for v in values:
        if v is None:
            out.append(GAP)
        elif hi == lo:
            out.append(SPARK[len(SPARK) // 2 - 1])
        else:
            out.append(SPARK[round((v - lo) / (hi - lo) * (len(SPARK) - 1))])
    return "".join(out)


def baseline(series: Sequence[float | None]) -> float | None:
    """그날을 뺀 앞 날들 가운데 값이 있는 날의 중앙값."""
    known = [v for v in series[:-1] if v is not None]
    return statistics.median(known) if known else None


def verdict(series: Sequence[float | None], alarm: str | None) -> str:
    if alarm is not None:
        return f"⚠ 경보 ({alarm})" if alarm else "⚠ 경보"
    today = series[-1]
    if today is None:
        return "-"
    window = [v for v in series[1:] if v is not None]
    if len(set(window)) > 1 and today == max(window):
        return "7일 중 최고"
    if len(set(window)) > 1 and today == min(window):
        return "7일 중 최저"
    return "정상"


def fmt(kind: str, v: float | None) -> str:
    if v is None:
        return "-"
    if kind == "money":
        return f"${v:,.2f}"
    if kind == "int":
        return f"{v:,.0f}"
    if kind == "float2":
        return f"{v:.2f}"
    return f"{v:.1f}"


def metric_row(m: Metric) -> list[str]:
    s = m.series
    if not s:
        return [m.label, UNCOLLECTED, "-", "", "-", "-"]
    today = s[-1]
    previous = s[-2] if len(s) >= 2 else None
    return [
        m.label,
        fmt(m.kind, today),
        fmt(m.kind, previous),
        sparkline(s[1:]),
        fmt(m.kind, baseline(s)),
        verdict(s, m.alarm),
    ]


def _cell(text: str) -> str:
    return text.replace("\r", "").replace("\n", " ").replace("|", "\\|")


def table_lines(t: Table) -> list[str]:
    align = {"l": "---", "r": "--:", "c": ":-:"}
    marks = [align.get(a, "---") for a in t.align.ljust(len(t.head), "l")]
    return [
        "| " + " | ".join(_cell(h) for h in t.head) + " |",
        "|" + "|".join(marks) + "|",
        *("| " + " | ".join(_cell(c) for c in row) + " |" for row in t.rows),
    ]


# 개선 제안


def amount(v: float, unit: str) -> str:
    """값과 단위. 달러는 앞에 붙이고 소수 둘째 자리까지, 나머지는 천 이상이면 정수로 적는다."""
    if unit == "$":
        return f"${v:,.2f}"
    return (f"{v:,.0f}" if abs(v) >= 1000 else f"{v:,.1f}") + unit


def proposal_state(prev: Seen | None, value: float | None, better: str) -> str:
    """지난 상태에 없던 제안은 `신규`, 확인할 수치가 바라는 쪽으로 움직였으면 `효과 확인됨`이다. 그
    밖의 진행 중·보류는 제안과 PR을 잇는 기록이 없어 가르지 못한다."""
    if prev is None:
        return "신규"
    if prev.value is not None and value is not None:
        improved = value < prev.value if better == "down" else value > prev.value
        if improved:
            return "효과 확인됨"
    return UNKNOWN_STATE


def check_text(p: Proposal, values: Mapping[str, Value], prev: Seen | None) -> str:
    v = values.get(p.check)
    if v is None:
        return f"{p.check} {UNCOLLECTED}"
    now = amount(v.value, v.unit)
    if prev is not None and prev.value is not None:
        return f"{v.label} {amount(prev.value, v.unit)} → {now}"
    return f"{v.label} {now}"


# 작업 표기


@dataclass(frozen=True)
class Marks:
    """글을 채우며 쌓는 표지. `first`는 작업 열쇠(`pr:N`·`queue:N`)마다 내용을 처음 적은 자리,
    `missing`은 메모에 이름이나 내용이 없는 작업, `glued`는 번호 바로 뒤에 조사가 붙은 작업이다."""

    first: Mapping[str, str] = field(default_factory=dict[str, str])
    missing: frozenset[str] = frozenset()
    glued: frozenset[str] = frozenset()

    def seen(self, key: str, where: str) -> Marks:
        """`key`를 처음 본 자리를 남긴 표지. 이미 보았으면 그대로다."""
        return self if key in self.first else replace(self, first={**self.first, key: where})

    def lacking(self, more: frozenset[str]) -> Marks:
        return replace(self, missing=self.missing | more) if more - self.missing else self

    def tail(self, key: str, content: str) -> str:
        """글에 쓰는 작업 표기의 꼬리. 처음 나온 자리면 `(<내용>)`이고 뒤에서는 비었다."""
        shown = content not in (NO_CONTENT, LOOKUP_FAILED)
        return f"({content})" if key not in self.first and shown else ""


def _parts(named: Named | None, label: str) -> tuple[str, str, frozenset[str]]:
    if named is None or not named.name:
        return NO_NAME, NO_CONTENT, frozenset({label})
    if not named.content:
        return named.name, NO_CONTENT, frozenset({label})
    return named.name, named.content, frozenset()


class Namer:
    """작업 자리를 채우고 글 속 작업 번호에 이름을 붙인다. 수집 JSON과 메모만 들고 상태를 갖지
    않는다. 내용을 처음 적은 자리와 빠진 이름은 `Marks`로 받아 새 표지와 함께 돌려준다."""

    def __init__(self, data: Data, notes: Notes) -> None:
        self.data = data
        self.notes = notes

    def pr_parts(self, n: int) -> tuple[str, str, frozenset[str]]:
        """PR의 (이름, 내용, 메모에 빠진 것). 제목을 가져오지 못한 PR은 이름을 지을 근거가 없어
        빠진 것으로 세지 않는다."""
        pr = self.data.prs.get(n)
        if pr is not None and pr.title is None:
            return LOOKUP_FAILED, LOOKUP_FAILED, frozenset()
        return _parts(self.notes.prs.get(n), f"#{n}")

    def queue_parts(self, n: int) -> tuple[str, str, frozenset[str]]:
        return _parts(self.notes.queue.get(n), f"대기열 {n}")

    def fill(self, text: str, where: str, marks: Marks) -> tuple[str, Marks]:
        """수집 도구가 남긴 자리 표시자를 채운다. 표의 내용 칸은 처음 나온 자리에만 내용을 쓰고
        뒤에서는 `→ <그 자리>`로 가리키며, `{{ref:N}}`은 `_mention`처럼 쓴다."""
        out: list[str] = []
        pos = 0
        for m in PLACEHOLDER.finditer(text):
            piece, marks = self._placeholder(m.group(1), m.group(2), where, marks)
            out += [text[pos : m.start()], piece]
            pos = m.end()
        return "".join([*out, text[pos:]]), marks

    def _placeholder(self, kind: str, arg: str, where: str, marks: Marks) -> tuple[str, Marks]:
        if kind == "branch":
            return self._branch(arg), marks
        n = int(arg) if arg.isdigit() else -1
        if kind == "group":
            return self._group(n), marks
        queue = kind in ("qname", "qcontent")
        key = f"queue:{n}" if queue else f"pr:{n}"
        name, content, lack = self.queue_parts(n) if queue else self.pr_parts(n)
        marks = marks.lacking(lack)
        if kind in ("name", "qname"):
            return name, marks
        if kind == "ref":
            return f"#{n} {name}{marks.tail(key, content)}", marks.seen(key, where)
        first = marks.first.get(key, where)
        return (content if first == where else f"→ {first}"), marks.seen(key, where)

    def _group(self, n: int) -> str:
        """병합 PR의 분류. 메모가 묶은 이름이고, 없으면 제목의 앞머리다."""
        named = self.notes.prs.get(n)
        if named is not None and named.group:
            return named.group
        pr = self.data.prs.get(n)
        return pr_kind(pr.title) if pr is not None and pr.title is not None else LOOKUP_FAILED

    def _branch(self, branch: str) -> str:
        written = self.notes.branches.get(branch)
        if written:
            return written
        subject = self.data.branches.get(branch)
        return f"(커밋 제목) {subject}" if subject else NO_NAME

    def expand(self, text: str, where: str, marks: Marks) -> tuple[str, Marks]:
        """모델이 쓴 글의 `#N`과 `대기열 N`에 이름을 붙인다. 처음 나온 자리면
        `<번호> <이름>(<내용>)`, 뒤에서는 `<번호> <이름>`이다. 번호 뒤에 이름이 이미 있으면 이름은
        다시 붙이지 않는다. 번호 바로 뒤에 한글이 붙으면 조사가 붙은 것으로 센다(이름을 끼우면
        받침이 어긋난다)."""
        out: list[str] = []
        pos = 0
        for m in REF.finditer(text):
            if m.start() < pos:
                continue
            pr = m.group(1) is not None
            n = int(m.group(1) or m.group(2))
            key = f"pr:{n}" if pr else f"queue:{n}"
            name, content, lack = self.pr_parts(n) if pr else self.queue_parts(n)
            marks = marks.lacking(lack)
            end = m.end()
            if text.startswith(f" {name}", end):
                end += len(name) + 1
            elif HANGUL.match(text, end):
                marks = replace(marks, glued=marks.glued | {m.group(0)})
            out += [text[pos : m.start()], f"{m.group(0)} {name}{marks.tail(key, content)}"]
            marks = marks.seen(key, where)
            pos = end
        return "".join([*out, text[pos:]]), marks


# 그리기


def _todo_line(t: Todo, data: Data, namer: Namer, marks: Marks) -> tuple[str, Marks]:
    where = "직접 하실 일"
    if t.queue is not None:
        row = data.queue.get(t.queue)
        rounds = f" ({row.rounds}회차)" if row is not None and row.rounds is not None else ""
        name, content, lack = namer.queue_parts(t.queue)
        key = f"queue:{t.queue}"
        title = f"**대기열 {t.queue}{rounds} {name}**{marks.tail(key, content)}"
        marks = marks.lacking(lack).seen(key, where)
    else:
        written, marks = namer.expand(t.title, where, marks)
        title = f"**{written}**"
    why, marks = namer.expand(t.why, where, marks)
    return f"- [ ] {title}: {why}", marks


def _todo_warnings(t: Todo) -> list[str]:
    sentences = len(SENTENCE_END.findall(t.why.strip()))
    if sentences <= 1:
        return []
    title = t.title or f"대기열 {t.queue}"
    return [f"할 일 「{title}」의 까닭이 {sentences}문장이다(한 문장으로 쓴다)"]


def _proposal_lines(
    data: Data, notes: Notes, state: Mapping[str, Seen], namer: Namer, marks: Marks
) -> tuple[list[str], dict[str, Seen], Marks, list[str]]:
    """제안 표와 접힌 "바꿀 것", 오늘의 제안 상태, 표지, 경고."""
    if not notes.proposals:
        return ["없음"], {}, marks, []
    head = (
        "#",
        "제안",
        "근거",
        "예상 효과",
        "난이도",
        "결정 필요",
        "확인할 수치 (어제 → 오늘)",
        "상태",
    )
    where = "개선 제안"
    rows: list[tuple[str, ...]] = []
    titles: list[str] = []
    new_state: dict[str, Seen] = {}
    warnings: list[str] = []
    for i, p in enumerate(notes.proposals, start=1):
        prev = state.get(p.id)
        if prev is not None and prev.check != p.check:
            prev = replace(prev, value=None)  # 다른 지표의 값과 견주지 않는다
        value = data.values.get(p.check)
        today = value.value if value is not None else None
        title, marks = namer.expand(p.title, where, marks)
        basis, marks = namer.expand(p.basis, where, marks)
        effect, marks = namer.expand(p.effect, where, marks)
        titles.append(title)
        rows.append(
            (
                str(i),
                title,
                basis,
                effect,
                p.difficulty or "-",
                p.decision or "-",
                check_text(p, data.values, prev),
                proposal_state(prev, today, p.better),
            )
        )
        if p.difficulty not in DIFFICULTIES:
            warnings.append(
                f"제안 「{p.title}」의 난이도 칸이 {'·'.join(DIFFICULTIES)} 밖의 낱말이다:"
                f" {p.difficulty or '(비었다)'}"
            )
        new_state[p.id] = Seen(prev.since if prev is not None else data.day, today, p.check)
    # 표의 행이 모두 바꿀 것보다 앞에 그려지므로, 바꿀 것은 표를 다 채운 뒤에 채운다
    details = ["<details><summary>제안별 바꿀 것</summary>", ""]
    for i, (p, title) in enumerate(zip(notes.proposals, titles, strict=True), start=1):
        details += [f"**{i}. {title}**", ""]
        changes: list[str] = []
        for c in p.change:
            written, marks = namer.expand(c, where, marks)
            changes.append(f"- {written}")
        details += changes or ["- (적지 않음)"]
        details.append("")
    details.append("</details>")
    lines = [*table_lines(Table(head, "rlllllll", tuple(rows))), "", *details]
    return lines, new_state, marks, warnings


def _section_lines(
    s: Section, notes: Notes, namer: Namer, marks: Marks
) -> tuple[list[str], Marks, list[str]]:
    """상세 절 하나의 글, 표지, 경고. 수집 도구가 쓴 표와 줄은 자리 표시자만 채우고, 메모의 해석
    줄만 글 속 작업 번호에 이름을 붙인다(수집 도구의 줄은 번호와 이름을 자리 표시자로 쓴다)."""
    where = f"상세 {s.number}"
    out = [f"<details><summary>{s.number}. {s.title}</summary>", ""]
    for t in s.tables:
        rows: list[tuple[str, ...]] = []
        for r in t.rows:
            cells: list[str] = []
            for c in r:
                filled, marks = namer.fill(c, where, marks)
                cells.append(filled)
            rows.append(tuple(cells))
        out += [*table_lines(Table(t.head, t.align, tuple(rows))), ""]
    lines: list[str] = []
    for x in s.lines:
        filled, marks = namer.fill(x, where, marks)
        lines.append(filled)
    written = [*notes.remarks.get(s.number, ()), *(notes.next if s.number == NEXT_SECTION else ())]
    for x in written:
        expanded, marks = namer.expand(x, where, marks)
        lines.append(f"- {expanded}")
    warnings: list[str] = []
    if len(lines) > MAX_LIST:
        collected = len(s.lines)
        warnings.append(
            f"{where}의 목록이 {len(lines)}줄로 {MAX_LIST}줄을 넘는다"
            f"(수집 {collected}줄, 메모 {len(written)}줄)."
            f" 메모가 이 절에 쓸 수 있는 줄은 {max(0, MAX_LIST - collected)}줄이다"
        )
    if lines:
        out += [*lines, ""]
    out += [f"원본: {s.source}", "", "</details>", ""]
    return out, marks, warnings


def render(
    data: Data, notes: Notes, state: Mapping[str, Seen]
) -> tuple[str, dict[str, Seen], list[str]]:
    """보고서 글, 오늘의 제안 상태, 경고."""
    namer = Namer(data, notes)
    marks = Marks()
    warnings: list[str] = []
    todos: list[str] = []
    for t in notes.todos:
        line, marks = _todo_line(t, data, namer, marks)
        todos.append(line)
        warnings += _todo_warnings(t)
    out = [
        f"# 일일 보고 · {data.day.isoformat()}",
        f"**경보 {data.alarms}건 · 직접 하실 일 {len(notes.todos)}건"
        f" · 개선 제안 {len(notes.proposals)}건**",
        "",
        "## 핵심 지표",
        "",
        *table_lines(
            Table(
                ("지표", "어제", "전날", "7일 추이", "7일 기준", "판정"),
                "lrrlrl",
                tuple(tuple(metric_row(m)) for m in data.metrics),
            )
        ),
        "",
        "비용은 토큰에 단가를 곱한 API 환산 달러이고 실제 청구액이 아니다. 7일 추이는 어제까지 7일,"
        " 7일 기준은 어제를 뺀 앞 7일의 중앙값이다.",
        "",
        "## 직접 하실 일",
        "",
        *(todos or ["없음"]),
        "",
        "## 개선 제안",
        "",
    ]
    proposal_lines, new_state, marks, proposal_warnings = _proposal_lines(
        data, notes, state, namer, marks
    )
    warnings += proposal_warnings
    out += [*proposal_lines, "", "---", "", "## 상세", ""]
    out += [
        f"수집 JSON `{data.day.isoformat()}.data.json`, 모은 시각 {data.made}."
        " 열린 PR·대기열·워크트리·부하는 그 시각의 값이라, 지난 날을 다시 만들면 그날이 아니라"
        " 모은 날의 값이 든다.",
        "",
    ]
    for s in sorted(data.sections, key=lambda s: s.number):
        section, marks, section_warnings = _section_lines(s, notes, namer, marks)
        out += section
        warnings += section_warnings
    if marks.missing:
        missing = ", ".join(sorted(marks.missing))
        warnings.append(f"메모에 이름이나 내용이 없는 작업: {missing}")
    if marks.glued:
        glued = ", ".join(sorted(marks.glued))
        warnings.append(
            f"작업 번호 바로 뒤에 조사가 붙었다(이름을 끼우면 받침이 어긋난다): {glued}"
        )
    return "\n".join(out).rstrip() + "\n", new_state, warnings


# CLI


def _read_json(path: Path) -> Json:
    j: Json = json.loads(path.read_text(encoding="utf-8"))
    return j


def latest_state(reports: Path, day: date) -> dict[str, Seen]:
    """`day` 앞의 가장 늦은 상태 파일. 없으면 빈 상태다."""
    path = _latest_before(reports, day, ".state.json")
    if path is None:
        return {}
    try:
        return read_state(_read_json(path))
    except (OSError, ValueError):
        return {}


def _latest_before(reports: Path, day: date, suffix: str) -> Path | None:
    """`reports`에서 이름이 `<날짜><suffix>`이고 그 날짜가 `day` 앞인 파일 가운데 가장 늦은 것."""
    found: list[tuple[date, Path]] = []
    for p in reports.glob(f"*{suffix}"):
        d = _day(p.name.removesuffix(suffix))
        if d is not None and d < day:
            found.append((d, p))
    return max(found)[1] if found else None


def latest_checks(reports: Path, day: date) -> frozenset[str]:
    """`day` 앞의 가장 늦은 메모가 고른 확인할 수치의 열쇠. 수집 도구가 이 열쇠의 값을 순위와
    상관없이 남겨, 값이 줄어 순위에서 빠진 제안도 상태를 잰다. 메모가 없거나 읽지 못하면 비었다."""
    path = _latest_before(reports, day, ".notes.json")
    if path is None:
        return frozenset()
    try:
        notes = Notes.of(_read_json(path))
    except (OSError, ValueError):
        return frozenset()
    return frozenset(p.check for p in notes.proposals if p.check)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="아침 보고를 그린다")
    p.add_argument("--reports", type=Path, required=True, help="수집·메모·보고 파일이 든 폴더")
    p.add_argument("--day", type=date.fromisoformat, required=True, help="보고하는 날(어제)")
    return p


def main(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    reports: Path = args.reports
    day: date = args.day
    try:
        data = Data.of(_read_json(reports / f"{day.isoformat()}.data.json"))
    except (OSError, ValueError) as error:
        sys.stderr.write(f"수집 JSON을 읽지 못했다: {error}\n")
        return 2
    notes_path = reports / f"{day.isoformat()}.notes.json"
    unread: list[str] = []
    try:
        notes = Notes.of(_read_json(notes_path)) if notes_path.exists() else Notes.of({})
    except (OSError, ValueError) as error:
        unread.append(f"메모 JSON을 읽지 못해 빈 메모로 그렸다(메모 전체를 다시 쓴다): {error}")
        notes = Notes.of({})
    text, new_state, warnings = render(data, notes, latest_state(reports, day))
    warnings = [*unread, *warnings]
    (reports / f"{day.isoformat()}.md").write_text(text, encoding="utf-8")
    state_text = json.dumps(state_json(new_state), ensure_ascii=False, indent=1)
    (reports / f"{day.isoformat()}.state.json").write_text(state_text, encoding="utf-8")
    for w in warnings:
        sys.stderr.write(f"경고: {w}\n")
    print(reports / f"{day.isoformat()}.md")
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1:]))
