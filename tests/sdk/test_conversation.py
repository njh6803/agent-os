"""컨텍스트의 대화 멤버. 값은 불변이고 플러그인이 sdk 만 import 해서 쓴다(ADR 0022)."""

import dataclasses
from collections.abc import AsyncIterator
from datetime import UTC, datetime

import pytest

from agent_os.sdk import AgentContext, BaseAgent, Conversation, Event, Exchange, RunFinished, RunId

FIXED_NOW = datetime(2026, 10, 4, 12, 0, tzinfo=UTC)
NEW = Conversation(summary=None, exchanges=())


class FakeContext:
    """시그니처로 AgentContext 를 만족한다. 멤버가 빠지면 아래의 포트 주해가 pyright 에서 깨진다."""

    run_id = RunId("r1")

    def __init__(self, conversation: Conversation = NEW) -> None:
        self.conversation = conversation

    def now(self) -> datetime:
        return FIXED_NOW

    async def llm(self, prompt: str) -> str:
        return f"echo:{prompt}"

    async def tool(self, name: str, **args: object) -> str:
        return "unused"


class WeavingAgent:
    """멤버의 값을 출력에 그대로 옮긴다. core 테스트의 판정 에이전트와 같은 모양이다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        lines = [f"summary={ctx.conversation.summary!r}"]
        lines.extend(f"{e.request}->{e.output}" for e in ctx.conversation.exchanges)
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output="\n".join(lines))


async def _output(agent: BaseAgent, ctx: AgentContext) -> str:
    events = [event async for event in agent.run("hi", ctx)]
    assert isinstance(events[-1], RunFinished)
    return events[-1].output


async def test_이어_가지_않은_실행의_멤버는_요약이_없고_교환이_비어_있다() -> None:
    assert await _output(WeavingAgent(), FakeContext()) == "summary=None"


async def test_에이전트는_요약과_교환을_오래된_것부터_읽는다() -> None:
    conversation = Conversation(
        summary="요청한 쪽이 2+2 를 물었고 에이전트가 4 라고 답했다",
        exchanges=(Exchange(request="3+3?", output="6"), Exchange(request="4+4?", output="8")),
    )

    output = await _output(WeavingAgent(), FakeContext(conversation))

    assert output.splitlines() == [
        "summary='요청한 쪽이 2+2 를 물었고 에이전트가 4 라고 답했다'",
        "3+3?->6",
        "4+4?->8",
    ]


def test_값은_불변이다() -> None:
    exchange = Exchange(request="2+2?", output="4")
    conversation = Conversation(summary=None, exchanges=(exchange,))

    # 직접 대입은 pyright 가 먼저 막는다(그것이 frozen 의 타입 쪽 효과다). 여기서 재는 것은 런타임
    # 쪽 효과라 타입 검사를 지나는 setattr 로 쓴다. 타입 우회 주석은 없다.
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(exchange, "output", "5")  # noqa: B010
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(conversation, "summary", "x")  # noqa: B010
    assert isinstance(conversation.exchanges, tuple)


def test_교환은_요청과_출력_두_문자열뿐이다() -> None:
    """도구 호출, 도구 결과, 실행 식별자, 시각을 싣지 않는다(ADR 0022)."""
    assert [f.name for f in dataclasses.fields(Exchange)] == ["request", "output"]
    assert [f.name for f in dataclasses.fields(Conversation)] == ["summary", "exchanges"]
