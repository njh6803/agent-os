"""재생. 재개할 때 이미 한 모델 호출과 도구 호출을 트레이스의 기록으로 대신한다(ADR 0009).

대응은 순서로, 검증은 대조로 한다. N번째 호출에 N번째 기록을 쓰되 돌려주기 전에 지금 보내려던
것이 기록과 같은지 본다. 어긋나면 Mismatch 이고 실행이 실패로 끝나며 그 실행은 재개 불가가
된다. 승인을 기다리는 사이 에이전트가 바뀌는 일은 개발 중에 늘 일어나고, 그때 조용히 다른
실행의 기록을 먹이는 것보다 시끄럽게 죽는 쪽이다.

대조 대상은 모델 호출의 프롬프트와 도구 호출의 이름·인자다. 인자는 마스킹된 것끼리 비교하므로
마스킹된 필드는 양쪽이 같은 표지가 되어 대조에서 저절로 빠진다.

에이전트가 낸 이벤트도 같은 열에서 소비한다. 트레이스에는 누가 낸 이벤트인지 표시가 없어서,
소비하지 않으면 에이전트가 지어낸 tool_called 하나가 기록을 밀어 그 뒤 대조가 전부 어긋난다.
그것도 이미 트레이스에 있는 사실이라 다시 쓰지 않는 것이 맞고, 덤으로 에이전트가 바뀌어 다른
이벤트를 내면 재개가 실패한다.

기록이 소진되는 자리가 멈췄던 자리다. 거기서 None 을 돌려주면 컨텍스트가 재개 이벤트를 내고
실제 포트를 부르기 시작한다.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from agent_os.sdk import Event, Json, LlmCalled, ToolCalled

# 재생 대상. 재개의 경계를 표시하는 이벤트는 재개 진입점이 이미 빼고 준다.
type Record = Event


class Mismatch(Exception):
    """재생하려던 것이 기록과 다르다. 무엇이 어긋났는지 말한다(사용자 스토리 11)."""


class Replay:
    """기록을 순서대로 돌려준다. 처음 실행에는 재생할 것이 없다."""

    @classmethod
    def nothing(cls) -> Replay:
        """처음 실행. 재생할 기록이 없고 재개 이벤트도 나지 않는다."""
        return cls((), resuming=False)

    @classmethod
    def of(cls, records: Sequence[Record]) -> Replay:
        """재개. 기록이 비어 있어도 재개 이벤트는 난다. 재생 구간과 실제 구간의 경계라서다."""
        return cls(tuple(records), resuming=True)

    def __init__(self, records: Sequence[Record], *, resuming: bool) -> None:
        self._records = tuple(records)
        self._resuming = resuming
        self._index = 0

    @property
    def resuming(self) -> bool:
        return self._resuming

    def take_model(self, prompt: str) -> LlmCalled | None:
        """기록된 모델 응답. 소진됐으면 None 이고 거기서부터 모델을 실제로 부른다."""
        record = self._take()
        if record is None:
            return None
        if not isinstance(record, LlmCalled):
            raise Mismatch(f"{self._at()} 기록은 {record.type} 인데 모델을 부르려 했다")
        if record.prompt != prompt:
            raise Mismatch(
                f"{self._at()} 모델 호출의 프롬프트가 기록과 다르다. "
                f"기록 {record.prompt!r}, 지금 {prompt!r}"
            )
        return record

    def take_tool(self, name: str, args: Mapping[str, Json]) -> ToolCalled | None:
        """기록된 도구 결과. 인자는 마스킹된 것끼리 비교한다."""
        record = self._take()
        if record is None:
            return None
        if not isinstance(record, ToolCalled):
            raise Mismatch(f"{self._at()} 기록은 {record.type} 인데 도구 {name} 을 부르려 했다")
        if record.tool != name:
            raise Mismatch(f"{self._at()} 기록은 도구 {record.tool} 인데 {name} 을 부르려 했다")
        if dict(record.args) != dict(args):
            raise Mismatch(
                f"{self._at()} 도구 {name} 의 인자가 기록과 다르다. "
                f"기록 {dict(record.args)}, 지금 {dict(args)}"
            )
        return record

    def take_agent_event(self, event: Event) -> None:
        """에이전트가 재생 구간에서 낸 이벤트. 이미 트레이스에 있으므로 소비만 하고 흘리지 않는다.

        모델·도구 호출과 달리 소진을 재생의 끝으로 보지 않는다. 재생 구간이 끝나는 자리는 런타임이
        실제 포트를 부르는 지점이지 에이전트가 이벤트를 내는 지점이 아니다. 기록보다 이벤트가
        많다면 에이전트가 바뀐 것이다.
        """
        record = self._take()
        if record is None:
            raise Mismatch(f"{self._at()} 기록에 없는 이벤트를 에이전트가 냈다: {event.type}")
        if record != event:
            raise Mismatch(
                f"{self._at()} 에이전트가 낸 이벤트가 기록과 다르다. "
                f"기록 {record.type}, 지금 {event.type}"
            )

    def _take(self) -> Record | None:
        if self._index >= len(self._records):
            return None
        record = self._records[self._index]
        self._index += 1
        return record

    def _at(self) -> str:
        """몇 번째에서 어긋났는지. _take 가 이미 센 뒤라 1부터의 순번이다."""
        return f"재생 {self._index}번째에서 어긋났다."
