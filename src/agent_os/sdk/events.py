"""이벤트 타입. 원칙 V: 실행은 이벤트 스트림이다.

플러그인이 import하는 공개 표면이자 JSONL 트레이스로 디스크에 남는 형식이다.
그래서 이 파일은 이 저장소에서 가장 바꾸기 어려운 열 줄이다.

TODO(사용자): 이벤트 종류와 Event 유니온을 아래에 정의한다. 정할 것 셋.
1. 종류. 최소 후보: run_started, llm_called, tool_called, run_finished, run_failed.
2. 공통 필드. run_id는 원칙 V가 강제한다. 순번(seq)을 둘지, ts만으로 충분한지.
3. 판별 방식. 종류별 클래스 + Literal type 필드의 판별 유니온인가,
   단일 클래스 + type 문자열 + payload dict인가.
   전자는 타입 검사가 보호하고, 후자는 종류를 추가해도 스키마가 안 바뀐다.

권장 형태:

    class RunStarted(BaseEvent):
        type: Literal["run_started"] = "run_started"
        agent: str

    Event = RunStarted | LlmCalled | ...
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BaseEvent(BaseModel):
    """모든 이벤트의 공통 필드. run_id는 필수(원칙 V). ts는 timezone-aware."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    ts: datetime


# TODO(사용자): 여기에 이벤트 종류와 Event 유니온을 정의한다.
