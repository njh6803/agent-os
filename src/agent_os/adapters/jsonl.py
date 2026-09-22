"""JSONL TraceStore. 트레이스는 이벤트를 그대로 저장한 것이지 별도 수집 층이 아니다(원칙 V).

`<directory>/<run_id>.jsonl`. 한 줄에 JSON 하나. 첫 줄은 형식 버전과 실행 식별자를 담은 헤더다.
형식 2 부터 이벤트가 재개의 입력이 될 만큼 두껍다(ADR 0009). 형식 1 파일도 읽는다. 관리가 옛
트레이스를 보여 줄 수 있어야 하기 때문이고, 재개만 성립하지 않는다. 그 판정은 읽는 쪽이 헤더의
버전을 `Trace.schema_version` 으로 돌려주면 core 가 한다.
이벤트 줄은 pydantic 의 model_dump_json() 그대로라 채널의 진행 표시와 같은 직렬화다.
읽는 쪽은 모르는 이벤트 종류를 만나면 원문을 보존한다. 형식을 바꾸면 ADR 을 남긴다.

단건과 목록이 같은 파일을 다르게 읽는다. 단건은 줄 전부를 엄격히 읽고 어디서 걸리든 PluginError
이고, 목록은 헤더와 첫 줄과 마지막 줄만 보고 읽히지 않는 파일을 표지로 남긴다. 파일마다 전부
파싱하면 목록 하나가 모든 실행의 모든 이벤트를 메모리에 올리기 때문이고, 그렇게 갈라도 되는
이유는 ADR 0012 의 2026-09-22 이력에 있다.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from pydantic import AwareDatetime, BaseModel, ConfigDict, TypeAdapter, ValidationError

from agent_os.core.ports import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    Cursor,
    PluginError,
    RunRow,
    RunStatus,
    RunSummary,
    Trace,
    TraceSchemaVersion,
    UnknownEvent,
    UnreadableTrace,
    cursor_of,
    order_key,
    run_status,
)
from agent_os.sdk import Event, RunId, RunStarted, is_run_id

TRACE_SCHEMA_VERSION: TraceSchemaVersion = "2"

_EVENT = TypeAdapter[Event](Event)


class TraceHeader(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    # 읽기는 형식 1 도 받는다. 쓰기는 항상 TRACE_SCHEMA_VERSION 이다.
    schema_version: TraceSchemaVersion
    run_id: RunId


class _EventEdge(BaseModel):
    """이벤트 줄에서 시각만. 모르는 종류의 줄에서도 읽히는 이유는 모든 이벤트에 있기 때문이다.

    마지막 시각이 마지막 이벤트에서 오는데 그 줄이 모르는 종류면 판별 유니온으로는 읽을 수 없다.
    시각이 없는 줄은 요약의 일곱 필드를 채울 수 없으므로 표지가 된다. 부분 요약을 두지 않는다.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    ts: AwareDatetime


class JsonlTrace:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def write(self, event: Event) -> None:
        path = self._path(event.run_id)
        self._directory.mkdir(parents=True, exist_ok=True)
        is_new = not path.exists()
        with path.open("a", encoding="utf-8") as file:
            if is_new:
                header = TraceHeader(schema_version=TRACE_SCHEMA_VERSION, run_id=event.run_id)
                file.write(header.model_dump_json() + "\n")
            file.write(event.model_dump_json() + "\n")

    def read(self, run_id: RunId) -> Trace | None:
        """부재는 None, 손상은 PluginError. 손상의 범위는 읽고 디코딩하고 파싱하는 전부다.

        포장하지 않으면 빈 파일의 IndexError 와 비UTF-8 의 UnicodeDecodeError 와 pydantic 의
        검증 오류가 그대로 올라와 채널의 `except PluginError` 를 지나친다(ADR 0012 이력).
        """
        path = self._path(run_id)
        if not path.exists():
            return None
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
            header = TraceHeader.model_validate_json(lines[0])
            events = tuple(_read_event(line) for line in lines[1:])
        except (OSError, IndexError, ValueError) as error:
            # ValidationError 와 UnicodeDecodeError 가 둘 다 ValueError 다.
            raise PluginError(f"트레이스를 읽을 수 없다: {path}\n{error}") from error
        return Trace(run_id=header.run_id, schema_version=header.schema_version, events=events)

    def list(
        self,
        *,
        status: RunStatus | None = None,
        limit: int | None = None,
        after: Cursor | None = None,
    ) -> tuple[RunRow, ...]:
        """디렉터리를 훑어 요약을 전부 만든 뒤 자른다. 색인을 붙이면 이 메서드만 바뀐다.

        상한이 있는 이유가 여기다. 전부 만든 뒤 자르므로 상한이 없으면 요청 하나가 "실행이 쌓여도
        목록 응답이 그만큼 커지지 않는다"를 무력화한다. 파일당 비용은 줄 셋의 파싱이다.
        """
        size = _page_size(limit)
        rows = [_row(path) for path in self._files()]
        if status is not None:
            # 표지는 상태가 없어 함께 빠진다. 승인자의 멈춘 실행 목록에 섞여 들어오지 않는다.
            rows = [row for row in rows if isinstance(row, RunSummary) and row.status == status]
        # 행마다 키를 한 번만 만든다. 정렬과 커서 비교가 같은 값을 봐야 페이지가 어긋나지 않는다.
        # 키로만 정렬하는 이유는 행 자체가 비교 가능해야 한다는 숨은 요구를 만들지 않기 위해서다.
        keyed = [(order_key(cursor_of(row)), row) for row in rows]
        keyed.sort(key=lambda pair: pair[0], reverse=True)
        if after is not None:
            edge = order_key(after)
            keyed = [pair for pair in keyed if pair[0] < edge]
        return tuple(row for _, row in keyed[:size])

    def _files(self) -> Iterator[Path]:
        """`<run_id>.jsonl` 중 이름이 실행 식별자인 것만. 그 밖은 런타임이 만들 수 없는 이름이다.

        빼는 이유는 되물을 수 없는 식별자를 목록에 싣지 않기 위해서다. 표지로 내면 그 식별자로
        상세를 물을 수 없어(형식 위반이라 포트에 닿기 전에 끝난다) 죽은 행이 된다.
        """
        if not self._directory.is_dir():
            return
        for path in sorted(self._directory.glob("*.jsonl")):
            if is_run_id(path.stem):
                yield path

    def _path(self, run_id: RunId) -> Path:
        return self._directory / f"{run_id}.jsonl"


def _page_size(limit: int | None) -> int:
    if limit is None:
        return DEFAULT_LIMIT
    if not 1 <= limit <= MAX_LIMIT:
        raise ValueError(f"limit 은 1 과 {MAX_LIMIT} 사이여야 한다: {limit}")
    return limit


def _row(path: Path) -> RunRow:
    run_id = RunId(path.stem)
    try:
        return _summarize(run_id, _edges(path))
    except (OSError, ValueError) as error:
        # 이유에 서버 경로가 실리는 것은 이 경계에서 노출이 아니다. 루프백 전용이고 인증 뒤이므로
        # 읽는 사람이 곧 그 파일시스템의 주인이다(admin-api 명세, ADR 0011).
        return UnreadableTrace(run_id=run_id, reason=f"{path}: {error}")


@dataclass(frozen=True)
class _Edges:
    """요약을 만드는 데 필요한 줄 셋. 이름이 있는 이유는 셋 다 str 이라 순서가 뒤바뀌어도
    타입이 잡지 못하기 때문이다."""

    header: str
    first: str
    last: str


def _edges(path: Path) -> _Edges:
    """헤더와 첫 이벤트 줄과 마지막 이벤트 줄. 가운데는 파싱하지 않는다.

    줄을 흘려 보며 셋만 들고 있으므로 파일이 길어도 파싱은 셋이고 메모리는 줄 셋이다(읽기 자체는
    끝까지 흘린다). 요약의 일곱 필드가 정확히 이 셋에서 온다 — 형식 버전은 헤더, 에이전트와
    주체와 시작 시각은 첫 줄, 실행 상태와 마지막 시각은 마지막 줄.
    """
    with path.open(encoding="utf-8") as file:
        lines = (stripped for stripped in (line.strip() for line in file) if stripped)
        header = next(lines, "")
        first = next(lines, "")
        last = first
        for line in lines:
            last = line
    if not header:
        raise ValueError("빈 파일이라 헤더가 없다")
    if not first:
        raise ValueError("이벤트가 없어 실행을 요약할 수 없다")
    return _Edges(header=header, first=first, last=last)


def _summarize(run_id: RunId, edges: _Edges) -> RunSummary:
    head = TraceHeader.model_validate_json(edges.header)
    if head.run_id != run_id:
        raise ValueError(f"헤더의 실행 식별자가 파일 이름과 다르다: {head.run_id}")
    started = _EVENT.validate_json(edges.first)
    if not isinstance(started, RunStarted):
        raise ValueError(f"시작 이벤트로 열리지 않는다: {started.type}")
    ending = _read_event(edges.last)
    return RunSummary(
        run_id=run_id,
        status=run_status(ending),
        schema_version=head.schema_version,
        started_at=started.ts,
        last_at=_last_at(ending, edges.last),
        agent=started.agent,
        principal=started.principal,
    )


def _last_at(ending: Event | UnknownEvent, line: str) -> datetime:
    """마지막 이벤트의 시각. 아는 종류면 읽은 것에서 그대로 오고 모르는 종류면 줄에서 뽑는다."""
    if isinstance(ending, UnknownEvent):
        return _EventEdge.model_validate_json(line).ts
    return ending.ts


def _read_event(line: str) -> Event | UnknownEvent:
    try:
        return _EVENT.validate_json(line)
    except ValidationError as error:
        if all(detail["type"] == "union_tag_invalid" for detail in error.errors()):
            return UnknownEvent(raw=line)
        raise
