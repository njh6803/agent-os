"""아침 보고를 그린다. 보고는 종합 하나와 분야별 넷(비용, 작업, 작업 환경, 실험)이고, 예약 작업
다섯이 `tools/morning_collect.py`의 수집 JSON으로 하나씩 부른다(지시문은 `tools/morning_tasks/`).

보고는 두 손이 함께 쓴다. 수치와 표는 수집 도구가 JSON(`<날짜>.data.json`, `Data`)으로 내고, 작업
이름·결론·그래서·할 일·정할 것은 예약 작업의 모델이 보고마다의 메모 JSON(`<날짜>.<보고>.notes.json`,
`Notes`)으로 쓴다. 이 도구는 둘을 합쳐 `<날짜>.<보고>.md`를 그린다. 수치는 모델의 손을 거치지 않고,
작업 이름은 이 도구가 붙인다(모델이 수치를 옮기던 판은 같은 사실이 여러 절에 되풀이되고 PR 번호가
이름 없이 괄호에만 적혔다, 2026-10-20 시험 보고).

형식의 근거는 `.scratch/morning-report-split/design.md`다. 표를 구분 없이 늘어놓은 판(2026-10-19
보고, 372줄에 표 24개)을 사용자가 읽기 어렵다고 했고(일지 2026-10-20-39), BLUF·민토·Amazon
WBR·What/So what/Now what·Google SRE·Few·영국 정부 표 지침에서 규칙을 옮겼다.

그리는 것.
- 종합(`summary`): 첫 줄에 오늘 정할 것의 수와 메모의 결론, 주간 한도(지금 몫, 초기화까지 남은 때,
  보고하는 날 쓴 몫과 하루 예산, 최근 24시간 속도로 차는 시각, 환산 비율), 오늘 정할 것(질문·추천·
  근거·확인할 수치와 그 상태), 평소와 다른 것(경보이거나 7일 안에서 홀로 최고·최저인 지표만 표로,
  다른 날과 같은 값이거나 평소와 같은 최고·최저는 빼고(`verdict`), 원인은 메모. 나머지는 이름만 한
  줄), 직접 하실 일, 오늘 나오는 분야별 보고. 제안 상태는 지난 상태 파일(`<날짜>.state.json`)과 견줘
  `신규`, `효과 확인됨`(확인할 수치가 바라는 쪽으로 움직였다)이다. 진행 중과 보류는 제안과 PR을 잇는
  기록이 없어 `UNKNOWN_STATE`로 적는다. 확인할 수치의 열쇠가 지난 상태와 다르면 견주지 않는다.
- 분야별: 머리에 메모의 결론과 "이 보고에서 정할 것", 그 보고로 가는 표마다 블록 하나(`### <결론>`,
  `<질문> · <기간> · <단위>`, 표, 그래서, 할 일), 끝에 그 보고로 가는 절의 줄("그 밖의 수")과 원본.
  결론·그래서·할 일은 메모가 표의 열쇠(`Table.key`)로 쓰고, 질문·기간·단위·칸 이름은 수집 도구가
  고정한다. 모든 행이 `(수집 안 됨)`인 칸은 그리지 않는다. 예약 작업의 답을 그리는 앱이
  `<details>`를 접지 못하고 태그를 글자로 보였다(일지 2026-10-20-28). 그래서 HTML 태그를 쓰지
  않는다.

작업 표기. 작업이 나오는 곳에는 번호·이름·내용을 함께 쓰되, 내용은 그 작업이 처음 나온 자리에만
쓰고 뒤에서는 번호와 이름만 쓴다. 수집 도구의 칸은 `{{name:N}}`·`{{content:N}}`(PR),
`{{qname:N}}`·`{{qcontent:N}}`(대기열 행), `{{branch:B}}`(PR 없는 브랜치), `{{work:B}}`(브랜치의
작업. PR이 있으면 그 PR의 이름, 없으면 메모의 브랜치 이름과 브랜치), `{{group:N}}`(병합 PR의 분류)로
자리를 남기고, 표의 내용 칸은 뒤에서 `→ 「<질문>」 표`로 가리킨다. 수집 도구가 쓴 줄은 `{{ref:N}}`,
모델이 쓴 글은 `#N`과 `대기열 N`을 찾아 같은 규칙으로 `<번호> <이름>(<내용>)`을 붙인다. PR 제목을
가져오지 못했으면 `LOOKUP_FAILED`로 적는다(이름을 지을 근거가 없어 경고하지 않는다). 메모에 이름이
없으면 `NO_NAME`, 내용이 없으면 `NO_CONTENT`로 적고 경고한다.

경고하는 것(stderr, 그리기는 그대로 한다).
- 메모에 그 보고의 결론(`heads`)이 없다. 분야별 보고의 표에 결론·그래서·할 일(`blocks`)이 빠졌다.
  할 일이 없으면 "없음"으로 쓴다.
- 종합의 평소와 다른 지표에 원인(`causes`)이 없다. 오늘 정할 것이 `MAX_DECISIONS`개를 넘는다(Google
  SRE의 경보 원칙: 오늘 손써야 하는 것만).
- 메모에 이름이나 내용이 없는 작업, 번호 바로 뒤에 조사가 붙은 작업 번호(이름을 끼우면 받침이
  어긋난다), 두 문장 이상인 할 일의 까닭(`SENTENCE_END`).
- 메모 JSON을 읽지 못했다(빈 메모로 그린다). 예약 작업은 `경고:` 줄마다 메모를 고치므로 이것도
  경고다.

못 보는 것.
- 메모의 글이 사실인지는 보지 않는다. 수치는 표에서만 오고, 글은 해석이다.
- 모델이 글에 작업 번호를 `#N`·`대기열 N` 꼴이 아닌 모양(`PR 301`)으로 쓰면 이름을 붙이지 않는다.
  `대기열 238·243`처럼 번호를 이어 쓰면 앞 번호에만 붙인다. `대기열 3회`처럼 수 뒤에 세는 말
  (`COUNTERS`)이 붙으면 행 번호로 보지 않으므로, `대기열 238건` 같은 행 번호도 놓친다.
- 문장 수는 `다.`로 끝나는 문장만 센다. `…함.`이나 물음표로 끝나는 문장은 세지 않는다.
- 같은 사실이 두 보고에 되풀이되는지는 표의 자리(`Table.report`)로만 막는다. 모델의 글이 표의 수치를
  다시 적으면 막지 못한다.

쓰임: `uv run python tools/morning_report.py --reports <폴더> --day YYYY-MM-DD --report <보고>`.
종료 0은 그렸다(경고는 stderr), 2는 수집 JSON을 읽지 못했거나 보고·상태 파일을 쓰지 못했다.
"""

from __future__ import annotations

import argparse
import io
import json
import math
import re
import statistics
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

FORMAT = 3
SPARK = "▁▂▃▄▅▆▇█"
GAP = "·"
LOOKUP_FAILED = "(제목 조회 실패)"
NO_NAME = "(이름 없음)"
NO_CONTENT = "(내용 없음)"
UNCOLLECTED = "(수집 안 됨)"
UNKNOWN_STATE = "진행 중·보류는 수집 안 됨"
UNKNOWN_CAUSE = "원인 모름"
UNITS = {"money": "$", "int": "", "float1": "", "float2": ""}  # `Metric.kind`마다 값의 단위
REPORTS = {
    "summary": "종합 보고",
    "cost": "비용 보고",
    "work": "작업 보고",
    "environment": "작업 환경 보고",
    "experiment": "실험 보고",
}
POINT_REPORTS = frozenset({"cost", "work"})  # `주간 한도(%p)` 칸이 있는 보고
MAX_DECISIONS = 3
DAILY_BUDGET = 100 / 7  # 주간 한도를 이레로 나눈 하루 몫(%p)
WEEKDAYS = "월화수목금토일"
PLACEHOLDER = re.compile(r"\{\{(name|content|qname|qcontent|ref|branch|work|group):([^{}]+)\}\}")
COUNTERS = "회개줄행건"  # `대기열 3회`처럼 수 뒤에 붙으면 행 번호가 아니라 셈이다
REF = re.compile(rf"#(\d+)|대기열 (\d+)(?![\d{COUNTERS}])")
PR_KIND = re.compile(r"^(\w+)(?:\(.*?\))?!?:")
HANGUL = re.compile(r"[가-힣]")
SENTENCE_END = re.compile(r"(?<=다)\.(?:\s|$)")


# JSON 풀이. `json_*`는 수집 도구(`morning_collect`·`morning_sources`)도 가져다 쓴다. 이 도구는
# 스크립트로 돌아 `tools` 패키지를 가져오지 못하므로 함께 쓰는 것을 이 파일에 둔다. 이 도구를
# `-m`으로 부르게 되면 `json_*`를 공용 모듈로 옮겨 바깥 명령 층이 그리기 도구에 기대지 않게 한다.


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
    """표 하나는 질문 하나다. `key`는 메모가 결론·그래서·할 일을 다는 열쇠, `report`는 이 표가 가는
    보고(`REPORTS`의 열쇠)다. 질문·기간·단위는 블록의 부제가 되고 기본값이 없어, 빠진 표는 수집
    도구가 짓지 못하고(타입) 읽지도 못한다(`of`). 기간이 적히지 않은 7일치 표가 하루치 표와 같은
    모양으로 섞였다(설계의 문제 5)."""

    key: str
    report: str
    question: str
    period: str
    unit: str
    head: tuple[str, ...]
    align: str
    rows: tuple[tuple[str, ...], ...]

    def to_json(self) -> Json:
        rows: list[Json] = [list(r) for r in self.rows]
        head: list[Json] = list(self.head)
        return {
            "key": self.key,
            "report": self.report,
            "question": self.question,
            "period": self.period,
            "unit": self.unit,
            "head": head,
            "align": self.align,
            "rows": rows,
        }

    @staticmethod
    def of(j: Json) -> Table:
        o = json_obj(j)
        names = ("key", "report", "question", "period", "unit")
        key, report, question, period, unit = (json_str(o.get(k)) for k in names)
        for name, v in zip(names, (key, report, question, period, unit), strict=True):
            if not v:
                raise ValueError(f"수집 JSON의 표에 {name}이 없다")
        if report not in REPORTS:
            raise ValueError(f"수집 JSON의 표 {key}의 report가 보고 다섯 밖이다: {report}")
        return Table(
            key,
            report,
            question,
            period,
            unit,
            _strs(o.get("head")),
            json_str(o.get("align")),
            tuple(_strs(r) for r in json_list(o.get("rows"))),
        )


@dataclass(frozen=True)
class Section:
    """수집 도구의 절 하나. 표는 저마다 갈 보고를 들고, 줄(`lines`)과 원본은 `report`로 간다."""

    number: int
    title: str
    report: str
    tables: tuple[Table, ...]
    lines: tuple[str, ...]
    source: str

    def to_json(self) -> Json:
        tables: list[Json] = [t.to_json() for t in self.tables]
        lines: list[Json] = list(self.lines)
        return {
            "number": self.number,
            "title": self.title,
            "report": self.report,
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
            json_str(o.get("report")),
            tuple(Table.of(t) for t in json_list(o.get("tables"))),
            _strs(o.get("lines")),
            json_str(o.get("source")),
        )


@dataclass(frozen=True)
class Limit:
    """주간 한도(주간 · 모든 모델) 한 점과 그 어림. `percent`·`at`·`resets`는 예약 작업이 앱의
    `get_usage`에서 찍은 값이고(`tools/morning_limit.py`), 나머지는 수집 도구가 같은 계정의 장부
    비용으로 어림한다. `rate`는 한도 1%당 API 환산 달러(이번 창의 비용 `spent` ÷ `percent`),
    `day_points`는 보고하는 날 쓴 몫(%p), `speed`는 최근 24시간의 시간당 몫(%p), `full_at`은 그
    속도로 차는 시각이고 초기화 전에 차지 않으면 None이다. 비율은 장부를 채우기 전에 찍은
    점(`basis_at`, `basis_percent`)으로 내므로 `spent`도 그 점까지의 비용이고, 그런 점이 없으면 셋이
    None이다. 한도가 비용에 비례해 찬다는 가정은 재지 않았다(설계의 "주간 한도")."""

    percent: int
    at: str
    resets: str
    account: str
    rate: float | None
    spent: float
    day_points: float | None
    speed: float | None
    full_at: str | None
    basis_at: str | None
    basis_percent: int | None

    def to_json(self) -> Json:
        return {
            "percent": self.percent,
            "at": self.at,
            "resets": self.resets,
            "account": self.account,
            "rate": self.rate,
            "spent": self.spent,
            "day_points": self.day_points,
            "speed": self.speed,
            "full_at": self.full_at,
            "basis_at": self.basis_at,
            "basis_percent": self.basis_percent,
        }

    @staticmethod
    def of(j: Json) -> Limit | str:
        """찍지 못했으면 그 까닭(`missing`)이다."""
        o = json_obj(j)
        percent = json_int(o.get("percent"))
        if percent is None:
            return json_str(o.get("missing")) or "한도 값이 없다"
        full_at, basis_at = o.get("full_at"), o.get("basis_at")
        return Limit(
            percent,
            json_str(o.get("at")),
            json_str(o.get("resets")),
            json_str(o.get("account")),
            _num(o.get("rate")),
            _num(o.get("spent")) or 0.0,
            _num(o.get("day_points")),
            _num(o.get("speed")),
            full_at if isinstance(full_at, str) else None,
            basis_at if isinstance(basis_at, str) else None,
            json_int(o.get("basis_percent")),
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
    최근 일지의 "다음" 절이다. `limit`은 주간 한도의 어림이거나 찍지 못한 까닭이다."""

    day: date
    made: str
    metrics: tuple[Metric, ...]
    values: dict[str, Value]
    sections: tuple[Section, ...]
    prs: dict[int, Pr]
    queue: dict[int, QueueRow]
    branches: dict[str, str]
    journal: str
    limit: Limit | str

    def to_json(self) -> Json:
        metrics: list[Json] = [m.to_json() for m in self.metrics]
        sections: list[Json] = [s.to_json() for s in self.sections]
        values: dict[str, Json] = {k: v.to_json() for k, v in self.values.items()}
        prs: dict[str, Json] = {str(k): v.to_json() for k, v in self.prs.items()}
        queue: dict[str, Json] = {str(k): v.to_json() for k, v in self.queue.items()}
        branches: dict[str, Json] = {k: v for k, v in self.branches.items()}
        limit: Json = (
            self.limit.to_json() if isinstance(self.limit, Limit) else {"missing": self.limit}
        )
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
            "limit": limit,
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
            Limit.of(o.get("limit")),
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
class Decision:
    """종합 보고의 오늘 정할 것 하나. `check`는 수집 JSON `values`의 열쇠, `better`는 그 값이 바라는
    쪽(`down`·`up`)이다. 같은 `id`로 다시 내면 지난 상태와 견준다."""

    id: str
    question: str
    recommend: str
    basis: str
    check: str
    better: str

    @staticmethod
    def of(j: Json) -> Decision:
        o = json_obj(j)
        names = ("id", "question", "recommend", "basis", "check", "better")
        return Decision(*(json_str(o.get(k)) for k in names))


@dataclass(frozen=True)
class Head:
    """보고 머리. 결론 두세 줄과 그 보고에서 정할 것(없으면 빈 튜플)."""

    conclusion: str
    decide: tuple[str, ...]

    @staticmethod
    def of(j: Json) -> Head:
        o = json_obj(j)
        return Head(json_str(o.get("conclusion")), _strs(o.get("decide")))


@dataclass(frozen=True)
class Block:
    """표 하나를 감싸는 글. 결론은 블록의 제목, 그래서는 뜻, 할 일은 다음 행동이다."""

    conclusion: str
    so_what: str
    todo: str

    @staticmethod
    def of(j: Json) -> Block:
        o = json_obj(j)
        return Block(
            json_str(o.get("conclusion")), json_str(o.get("so_what")), json_str(o.get("todo"))
        )


@dataclass(frozen=True)
class Notes:
    """모델이 보고마다 쓰는 메모. `heads`는 보고 열쇠마다의 머리, `blocks`는 표 열쇠마다의 글,
    `causes`는 지표 열쇠마다 평소와 다른 원인이다."""

    prs: dict[int, Named]
    queue: dict[int, Named]
    branches: dict[str, str]
    todos: tuple[Todo, ...]
    decisions: tuple[Decision, ...]
    heads: dict[str, Head]
    blocks: dict[str, Block]
    causes: dict[str, str]

    @staticmethod
    def of(j: Json) -> Notes:
        o = json_obj(j)
        return Notes(
            _numbered(o.get("prs"), Named.of),
            _numbered(o.get("queue"), Named.of),
            {k: json_str(v) for k, v in json_obj(o.get("branches")).items()},
            tuple(Todo.of(t) for t in json_list(o.get("todos"))),
            tuple(Decision.of(d) for d in json_list(o.get("decisions"))),
            {k: Head.of(v) for k, v in json_obj(o.get("heads")).items()},
            {k: Block.of(v) for k, v in json_obj(o.get("blocks")).items()},
            {k: json_str(v) for k, v in json_obj(o.get("causes")).items()},
        )


# 지난 상태


@dataclass(frozen=True)
class Seen:
    """제안 하나의 상태. `since`는 처음 낸 날, `value`는 그날 보고의 확인할 수치, `check`는 그
    수치의 열쇠(`Decision.check`)다. 열쇠가 바뀐 제안은 지난 값과 견주지 않는다."""

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


# 지표와 표


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
    """창은 그날을 포함한 7일(`series[1:]`)이다. 그날이 창의 다른 날 모두보다 높아야 최고, 낮아야
    최저다. 창 밖의 첫날(`series[0]`)은 견주는 날에 들지 않고 평소(`baseline`)에만 든다. 다른 날과
    같은 값으로 최고·최저인 날과 평소와 같은 날은 정상이다(그 전날 하루만 5이고 나머지가 0인 지표가
    `| 읽지 못한 기록 줄 | 0 | 0 | +0 | 원인 모름 |`으로 평소와 다른 것에 올랐다, 일지
    2026-10-21-04). 평소와 같은 홀로 최고·최저는 창의 다른 날에 값이 하루뿐이고 창 밖의 첫날에 값이
    있을 때 난다(`(8, 없음×5, 2, 5)`). 다른 날과의 같음과 평소와의 같음은 모두 부동소수 오차
    (`math.isclose`) 안이면 같다고 본다. 평소는 두 값의 평균일 수 있고, 같은 금액도 세션 비용을 더한
    순서가 다르면 한 ulp 갈린다(`0.1 + 0.2`와 `0.3`)."""
    if alarm is not None:
        return f"⚠ 경보 ({alarm})" if alarm else "⚠ 경보"
    today = series[-1]
    if today is None:
        return "-"
    base = baseline(series)
    if base is not None and math.isclose(today, base):
        return "정상"
    others = [v for v in series[1:-1] if v is not None]
    if not others:
        return "정상"
    top, bottom = max(others), min(others)
    if today > top and not math.isclose(today, top):
        return "7일 중 최고"
    if today < bottom and not math.isclose(today, bottom):
        return "7일 중 최저"
    return "정상"


def unusual(m: Metric) -> bool:
    """평소와 다른 지표: 경보이거나 `verdict`가 7일 중 최고·최저로 본 지표다(Amazon WBR: 예외만
    본다)."""
    return bool(m.series) and verdict(m.series, m.alarm) not in ("정상", "-")


def fmt(kind: str, v: float | None) -> str:
    """정밀도는 필요한 만큼만 둔다(Few). 달러는 소수점 없이 적는다."""
    if v is None:
        return "-"
    if kind == "money":
        return f"${v:,.0f}"
    if kind == "int":
        return f"{v:,.0f}"
    if kind == "float2":
        return f"{v:.2f}"
    return f"{v:.1f}"


def change(kind: str, today: float | None, base: float | None) -> str:
    """평소 대비 차이. 평소가 0이면 백분율이 없어 수로 적는다."""
    if today is None or base is None:
        return "-"
    if base:
        return f"{today / base - 1:+.0%}"
    return f"+{fmt(kind, today - base)}" if today >= base else f"-{fmt(kind, base - today)}"


def metric_row(m: Metric) -> list[str]:
    """지표 | 어제 | 평소(앞 7일 중앙값) | 차이."""
    s = m.series
    if not s:
        return [m.label, UNCOLLECTED, "-", "-"]
    today, base = s[-1], baseline(s)
    return [m.label, fmt(m.kind, today), fmt(m.kind, base), change(m.kind, today, base)]


def _cell(text: str) -> str:
    return text.replace("\r", "").replace("\n", " ").replace("|", "\\|")


def table_lines(head: Sequence[str], align: str, rows: Sequence[Sequence[str]]) -> list[str]:
    marks_of = {"l": "---", "r": "--:", "c": ":-:"}
    marks = [marks_of.get(a, "---") for a in align.ljust(len(head), "l")]
    return [
        "| " + " | ".join(_cell(h) for h in head) + " |",
        "|" + "|".join(marks) + "|",
        *("| " + " | ".join(_cell(c) for c in row) + " |" for row in rows),
    ]


def shown_columns(t: Table) -> list[int]:
    """그릴 칸. 모든 행이 `(수집 안 됨)`인 칸은 뺀다(영국 정부 표 지침: 내용 없는 칸을 두지
    않는다)."""
    return [
        i
        for i in range(len(t.head))
        if not t.rows or any(i >= len(r) or r[i] != UNCOLLECTED for r in t.rows)
    ]


# 제안 상태


def amount(v: float, unit: str) -> str:
    """값과 단위. 달러는 앞에 붙이고 10 이상이면 소수점 없이(Few), 그 아래는 둘째 자리까지 적는다.
    나머지는 천 이상이면 정수로 적는다."""
    if unit == "$":
        return f"${v:,.0f}" if abs(v) >= 10 else f"${v:,.2f}"
    return (f"{v:,.0f}" if abs(v) >= 1000 else f"{v:,.1f}") + unit


def check_state(prev: Seen | None, value: float | None, better: str) -> str:
    """지난 상태에 없던 제안은 `신규`, 확인할 수치가 바라는 쪽으로 움직였으면 `효과 확인됨`이다. 그
    밖의 진행 중·보류는 제안과 PR을 잇는 기록이 없어 가르지 못한다."""
    if prev is None:
        return "신규"
    if prev.value is not None and value is not None:
        improved = value < prev.value if better == "down" else value > prev.value
        if improved:
            return "효과 확인됨"
    return UNKNOWN_STATE


def check_text(d: Decision, values: Mapping[str, Value], prev: Seen | None) -> str:
    v = values.get(d.check)
    if v is None:
        return f"{d.check} {UNCOLLECTED}"
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
        뒤에서는 `→ <그 자리>`로 가리키며, `{{ref:N}}`은 `expand`처럼 쓴다."""
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
        if kind == "work":
            return self._work(arg, marks)
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

    def _work(self, branch: str, marks: Marks) -> tuple[str, Marks]:
        """브랜치의 작업 이름과 브랜치. 그 브랜치의 PR이 있으면 PR의 이름이고(가장 큰 번호), 없으면
        메모의 브랜치 이름이나 커밋 제목이며, 둘 다 없으면(`main`) 브랜치만 적는다."""
        numbers = [n for n, p in self.data.prs.items() if p.branch == branch]
        if numbers:
            name, _, lack = self.pr_parts(max(numbers))
            return f"{name} (`{branch}`)", marks.lacking(lack)
        if branch in self.notes.branches or branch in self.data.branches:
            return f"{self._branch(branch)} (`{branch}`)", marks
        return f"`{branch}`", marks

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


def _when(t: datetime) -> str:
    return f"{t:%m-%d} {t:%H:%M}"


def _weekday(d: date) -> str:
    return f"{d:%m-%d}({WEEKDAYS[d.weekday()]})"


def _left(span: timedelta) -> str:
    hours = max(0, int(span.total_seconds() // 3600))
    days, hours = divmod(hours, 24)
    return f"{days}일 {hours}시간" if days else f"{hours}시간"


def _limit_lines(limit: Limit | str) -> list[str]:
    """종합의 주간 한도 절. 시각은 찍은 시각(`at`)의 시간대로 적는다."""
    if isinstance(limit, str):
        return [f"- 주간 한도 {UNCOLLECTED}: {limit}"]
    at, resets = json_time(limit.at), json_time(limit.resets)
    if at is None or resets is None:
        return [f"- 주간 한도 {UNCOLLECTED}: 찍은 시각이나 초기화 시각을 읽지 못했다"]
    # get_usage는 초기화 시각을 UTC로, 초 아래 꼬리(59.733초)를 붙여 준다
    resets = (resets + timedelta(seconds=30)).replace(second=0, microsecond=0)
    resets = resets.astimezone(at.tzinfo)
    out = [
        f"- 지금 **{limit.percent}%** 썼습니다(주간 · 모든 모델, {_when(at)} 기준)."
        f" 초기화({_weekday(resets.date())} {resets:%H:%M})까지 {_left(resets - at)} 남았습니다."
    ]
    if limit.day_points is not None:
        out.append(
            f"- 어제 약 **{limit.day_points:.0f}%p**를 썼습니다. 하루 예산 {DAILY_BUDGET:.0f}%p"
            f"(100%를 7일로 나눈 값)의 {limit.day_points / DAILY_BUDGET:.1f}배입니다."
        )
    full = json_time(limit.full_at) if limit.full_at else None
    if limit.speed is not None and full is not None:
        out.append(
            f"- 최근 24시간 속도(시간당 약 {limit.speed:.1f}%p)면 **{_weekday(full.date())}"
            f" {full:%H}시께** 찹니다. 추가 사용이 꺼져 있으면 그때부터 초기화까지 이 계정으로"
            " 작업할 수 없습니다."
        )
    elif limit.speed is not None:
        out.append(
            f"- 최근 24시간 속도는 시간당 약 {limit.speed:.1f}%p이고, 이 속도면 초기화 전에 차지"
            " 않습니다."
        )
    basis = json_time(limit.basis_at) if limit.basis_at else None
    if limit.rate is not None and basis is not None:
        out.append(
            f"- 환산: 주간 한도 1% ≈ API 환산 ${limit.rate:,.0f}({_when(basis)}에 찍은"
            f" {limit.basis_percent}%와 그때까지 이번 창의 {limit.account} 비용"
            f" ${limit.spent:,.0f}). 한도가 비용에 비례해 찬다는 가정은 재지 않았습니다."
        )
    else:
        out.append(
            "- 어제 쓴 몫과 속도는 어림하지 않았습니다. 장부(하루 한 번 채운다)를 채우기 전에 찍은"
            " 한도 기록이 없거나, 그 기록의 몫이나 그때까지의 비용이 0이라 1%당 비용을 낼 수"
            " 없습니다. 기록이 처음 쌓인 날이면 다음 날부터 나옵니다."
        )
    return out


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


@dataclass
class Draft:
    """그리는 동안 쌓는 것. 표지는 글이 문서에 나오는 차례로 넘겨야 내용이 처음 자리에 붙는다."""

    namer: Namer
    marks: Marks = field(default_factory=Marks)
    warnings: list[str] = field(default_factory=list[str])

    def expand(self, text: str, where: str) -> str:
        out, self.marks = self.namer.expand(text, where, self.marks)
        return out

    def fill(self, text: str, where: str) -> str:
        out, self.marks = self.namer.fill(text, where, self.marks)
        return out

    def finish(self) -> list[str]:
        out = list(self.warnings)
        if self.marks.missing:
            out.append(f"메모에 이름이나 내용이 없는 작업: {', '.join(sorted(self.marks.missing))}")
        if self.marks.glued:
            glued = ", ".join(sorted(self.marks.glued))
            out.append(f"작업 번호 바로 뒤에 조사가 붙었다(이름을 끼우면 받침이 어긋난다): {glued}")
        return out


def _decision_lines(
    data: Data, notes: Notes, state: Mapping[str, Seen], draft: Draft
) -> tuple[list[str], dict[str, Seen]]:
    """오늘 정할 것과 오늘의 제안 상태."""
    if len(notes.decisions) > MAX_DECISIONS:
        draft.warnings.append(
            f"오늘 정할 것이 {len(notes.decisions)}개로 {MAX_DECISIONS}개를 넘는다"
            "(오늘 손써야 하는 것만 남긴다)"
        )
    where = "오늘 정할 것"
    out: list[str] = []
    new_state: dict[str, Seen] = {}
    for i, d in enumerate(notes.decisions, start=1):
        prev = state.get(d.id)
        if prev is not None and prev.check != d.check:
            prev = replace(prev, value=None)  # 다른 지표의 값과 견주지 않는다
        value = data.values.get(d.check)
        today = value.value if value is not None else None
        out += [
            f"**{i}. {draft.expand(d.question, where)}**",
            f"- 추천: {draft.expand(d.recommend, where)}",
            f"- 근거: {draft.expand(d.basis, where)}",
            f"- 확인할 수치: {check_text(d, data.values, prev)}"
            f"({check_state(prev, today, d.better)})",
            "",
        ]
        new_state[d.id] = Seen(prev.since if prev is not None else data.day, today, d.check)
    return out or ["없음", ""], new_state


def _unusual_lines(data: Data, notes: Notes, draft: Draft) -> list[str]:
    """평소와 다른 지표의 표와, 평소대로인 지표·모으지 못한 지표의 이름."""
    odd = [m for m in data.metrics if unusual(m)]
    calm = [m.label for m in data.metrics if m.series and not unusual(m)]
    lost = [m.label for m in data.metrics if not m.series]
    out = ["평소는 앞 7일의 중앙값입니다.", ""]
    rows: list[list[str]] = []
    for m in odd:
        cause = notes.causes.get(m.key, "")
        if not cause:
            draft.warnings.append(
                f"평소와 다른 지표 {m.key}({m.label})에 메모의 causes가 없다"
                f"(모르면 {UNKNOWN_CAUSE})"
            )
        rows.append([*metric_row(m), draft.expand(cause, "평소와 다른 것") or UNKNOWN_CAUSE])
    if rows:
        out += [*table_lines(("지표", "어제", "평소", "차이", "원인"), "lrrrl", rows), ""]
    else:
        out += ["평소와 다른 지표가 없습니다.", ""]
    if calm:
        out += [f"**평소대로:** {', '.join(calm)}", ""]
    if lost:
        out += [f"**모으지 못한 것:** {', '.join(lost)}", ""]
    return out


def _today_reports(day: date) -> str:
    """보고하는 날 다음 날(예약 작업이 도는 날)에 나오는 분야별 보고."""
    daily = "비용 보고(09:30), 작업 보고(09:45)"
    if (day + timedelta(days=1)).weekday() == 0:
        return f"{daily}, 작업 환경 보고(10:00), 실험 보고(10:15)."
    return f"{daily}. 작업 환경 보고와 실험 보고는 월요일에 나옵니다."


def _summary(
    data: Data, notes: Notes, state: Mapping[str, Seen], draft: Draft
) -> tuple[list[str], dict[str, Seen]]:
    head = notes.heads.get("summary")
    if head is None or not head.conclusion:
        draft.warnings.append("메모의 heads에 summary 보고의 결론이 없다")
    conclusion = draft.expand(head.conclusion, "결론") if head is not None else ""
    out = [
        f"# 종합 보고 · {data.day.isoformat()}({WEEKDAYS[data.day.weekday()]})",
        "",
        f"**오늘 정할 것 {len(notes.decisions)}개.** {conclusion}".rstrip(),
        "",
        "## 주간 한도",
        "",
        *_limit_lines(data.limit),
        "",
        "## 오늘 정할 것",
        "",
    ]
    decisions, new_state = _decision_lines(data, notes, state, draft)
    out += [*decisions, "## 평소와 다른 것", "", *_unusual_lines(data, notes, draft)]
    todos: list[str] = []
    for t in notes.todos:
        line, draft.marks = _todo_line(t, data, draft.namer, draft.marks)
        todos.append(line)
        draft.warnings += _todo_warnings(t)
    out += ["## 직접 하실 일", "", *(todos or ["없음"]), ""]
    out += ["## 오늘 나오는 분야별 보고", "", _today_reports(data.day)]
    return out, new_state


def _block_lines(t: Table, notes: Notes, draft: Draft) -> list[str]:
    """표 하나의 블록: 결론 제목, 질문·기간·단위, 표, 그래서, 할 일."""
    where = f"「{t.question}」 표"
    block = notes.blocks.get(t.key, Block("", "", ""))
    missing = [
        n
        for n, v in (("결론", block.conclusion), ("그래서", block.so_what), ("할 일", block.todo))
        if not v
    ]
    if missing:
        josa = "가" if missing[-1] == "그래서" else "이"
        draft.warnings.append(f"표 {t.key}({t.question})의 메모에 {'·'.join(missing)}{josa} 없다")
    title = draft.expand(block.conclusion, where) or "(결론 없음)"
    columns = shown_columns(t)
    rows = [[draft.fill(r[i], where) if i < len(r) else "" for i in columns] for r in t.rows]
    head = [t.head[i] for i in columns]
    align = "".join(t.align.ljust(len(t.head), "l")[i] for i in columns)
    return [
        "---",
        "",
        f"### {title}",
        "",
        f"{t.question} · {t.period} · {t.unit}",
        "",
        *table_lines(head, align, rows),
        "",
        f"**그래서:** {draft.expand(block.so_what, where)}",
        "",
        f"**할 일:** {draft.expand(block.todo, where)}",
        "",
    ]


def _field(data: Data, notes: Notes, report: str, draft: Draft) -> list[str]:
    head = notes.heads.get(report)
    if head is None or not head.conclusion:
        draft.warnings.append(f"메모의 heads에 {report} 보고의 결론이 없다")
    conclusion = draft.expand(head.conclusion, "결론") if head is not None else ""
    decide = [draft.expand(x, "결론") for x in head.decide] if head is not None else []
    out = [
        f"# {REPORTS[report]} · {data.day.isoformat()}({WEEKDAYS[data.day.weekday()]})",
        "",
        f"**결론:** {conclusion}".rstrip(),
        "",
        f"**이 보고에서 정할 것:** {' / '.join(decide) or '없음'}",
        "",
    ]
    limit = data.limit
    if report in POINT_REPORTS and isinstance(limit, Limit) and limit.rate is not None:
        out += [
            f'주간 한도(%p)는 비용을 "주간 한도 1% ≈ API 환산 ${limit.rate:,.0f}"로 나눈'
            " 어림입니다. 앱이 알려 주는 것은 계정 전체의 % 하나뿐이라, 작업과 모델의 몫은 비용"
            " 비율로 나눴습니다.",
            "",
        ]
    sections = sorted(data.sections, key=lambda s: s.number)
    nothing: list[str] = []
    for s in sections:
        for t in s.tables:
            if t.report != report:
                continue
            if t.rows:
                out += _block_lines(t, notes, draft)
            else:
                nothing.append(f"- {t.question}: 해당 없음({t.period})")
    lines = [draft.fill(x, "그 밖의 수") for s in sections if s.report == report for x in s.lines]
    lines += nothing
    if lines:
        out += ["---", "", "## 그 밖의 수", "", *lines, ""]
    used = [
        s.source
        for s in sections
        if s.report == report or any(t.report == report for t in s.tables)
    ]
    sources = list(dict.fromkeys(used))
    out.append(f"원본: {'; '.join(sources) or '없음'}")
    return out


def render(
    data: Data, notes: Notes, state: Mapping[str, Seen], report: str
) -> tuple[str, dict[str, Seen] | None, list[str]]:
    """보고서 글, 오늘의 제안 상태(종합만, 나머지는 None), 경고."""
    draft = Draft(Namer(data, notes))
    new_state: dict[str, Seen] | None = None
    if report == "summary":
        out, new_state = _summary(data, notes, state, draft)
    else:
        out = _field(data, notes, report, draft)
    return "\n".join(out).rstrip() + "\n", new_state, draft.finish()


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
    """`day` 앞의 가장 늦은 종합 메모가 고른 확인할 수치의 열쇠. 수집 도구가 이 열쇠의 값을 순위와
    상관없이 남겨, 값이 줄어 순위에서 빠진 제안도 상태를 잰다. 메모가 없거나 읽지 못하면 비었다."""
    path = _latest_before(reports, day, ".summary.notes.json")
    if path is None:
        return frozenset()
    try:
        notes = Notes.of(_read_json(path))
    except (OSError, ValueError):
        return frozenset()
    return frozenset(d.check for d in notes.decisions if d.check)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="아침 보고를 그린다")
    p.add_argument("--reports", type=Path, required=True, help="수집·메모·보고 파일이 든 폴더")
    p.add_argument("--day", type=date.fromisoformat, required=True, help="보고하는 날(어제)")
    p.add_argument("--report", choices=tuple(REPORTS), required=True, help="그릴 보고")
    return p


def main(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    reports: Path = args.reports
    day: date = args.day
    report: str = args.report
    try:
        data = Data.of(_read_json(reports / f"{day.isoformat()}.data.json"))
    except (OSError, ValueError) as error:
        sys.stderr.write(f"수집 JSON을 읽지 못했다: {error}\n")
        return 2
    notes_path = reports / f"{day.isoformat()}.{report}.notes.json"
    unread: list[str] = []
    try:
        notes = Notes.of(_read_json(notes_path)) if notes_path.exists() else Notes.of({})
    except (OSError, ValueError) as error:
        unread.append(f"메모 JSON을 읽지 못해 빈 메모로 그렸다(메모 전체를 다시 쓴다): {error}")
        notes = Notes.of({})
    text, new_state, warnings = render(data, notes, latest_state(reports, day), report)
    warnings = [*unread, *warnings]
    out = reports / f"{day.isoformat()}.{report}.md"
    try:
        out.write_text(text, encoding="utf-8")
        if new_state is not None:
            state_text = json.dumps(state_json(new_state), ensure_ascii=False, indent=1)
            (reports / f"{day.isoformat()}.state.json").write_text(state_text, encoding="utf-8")
    except OSError as error:
        sys.stderr.write(f"보고 파일을 쓰지 못했다: {error}\n")
        return 2
    for w in warnings:
        sys.stderr.write(f"경고: {w}\n")
    print(out)
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1:]))
