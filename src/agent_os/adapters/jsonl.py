"""JSONL TraceSink. 트레이스는 이벤트를 그대로 저장한 것이지 별도 수집 층이 아니다(원칙 V).

`<directory>/<run_id>.jsonl`. 한 줄에 JSON 하나. 첫 줄은 형식 버전과 실행 식별자를 담은 헤더다.
형식 2 부터 이벤트가 재개의 입력이 될 만큼 두껍다(ADR 0009). 형식 1 파일도 읽는다. 관리가 옛
트레이스를 보여 줄 수 있어야 하기 때문이고, 재개만 성립하지 않는다.
이벤트 줄은 pydantic 의 model_dump_json() 그대로라 채널의 진행 표시와 같은 직렬화다.
읽는 쪽은 모르는 이벤트 종류를 만나면 원문을 보존한다. 형식을 바꾸면 ADR 을 남긴다.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, TypeAdapter, ValidationError

from agent_os.sdk import Event, RunId

TRACE_SCHEMA_VERSION = "2"

_EVENT = TypeAdapter[Event](Event)


class TraceHeader(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    # 읽기는 형식 1 도 받는다. 쓰기는 항상 TRACE_SCHEMA_VERSION 이다.
    schema_version: Literal["1", "2"]
    run_id: RunId


@dataclass(frozen=True)
class UnknownEvent:
    """이 런타임이 모르는 종류. 원문을 그대로 들고 있어 옛 도구가 새 트레이스를 지우지 않는다."""

    raw: str


@dataclass(frozen=True)
class Trace:
    header: TraceHeader
    events: tuple[Event | UnknownEvent, ...]


class JsonlTrace:
    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def write(self, event: Event) -> None:
        path = self._directory / f"{event.run_id}.jsonl"
        self._directory.mkdir(parents=True, exist_ok=True)
        is_new = not path.exists()
        with path.open("a", encoding="utf-8") as file:
            if is_new:
                header = TraceHeader(schema_version=TRACE_SCHEMA_VERSION, run_id=event.run_id)
                file.write(header.model_dump_json() + "\n")
            file.write(event.model_dump_json() + "\n")


def read_trace(path: Path) -> Trace:
    lines = path.read_text(encoding="utf-8").splitlines()
    header = TraceHeader.model_validate_json(lines[0])
    return Trace(header=header, events=tuple(_read_event(line) for line in lines[1:]))


def _read_event(line: str) -> Event | UnknownEvent:
    try:
        return _EVENT.validate_json(line)
    except ValidationError as error:
        if all(detail["type"] == "union_tag_invalid" for detail in error.errors()):
            return UnknownEvent(raw=line)
        raise
