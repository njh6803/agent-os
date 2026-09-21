"""BaseAgent 프로토콜이 async generator로 구현 가능하고 이벤트가 흐르는지.

에이전트는 시각과 식별자를 컨텍스트에서만 받는다. 그래야 같은 입력으로 재실행할 수 있다.
"""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

from agent_os.sdk import AgentContext, BaseAgent, Event, RunFinished, RunId

FIXED_NOW = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)


class FakeContext:
    run_id = RunId("r1")

    def now(self) -> datetime:
        return FIXED_NOW

    async def llm(self, prompt: str) -> str:
        return f"echo:{prompt}"

    async def tool(self, name: str, **args: object) -> str:
        return "unused"


class EchoAgent:
    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        answer = await ctx.llm(request)
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=answer)


async def _collect(agent: BaseAgent, ctx: AgentContext) -> list[Event]:
    return [event async for event in agent.run("hi", ctx)]


async def test_agent_yields_event_stream() -> None:
    events = await _collect(EchoAgent(), FakeContext())
    assert [event.type for event in events] == ["run_finished"]
    assert isinstance(events[-1], RunFinished)
    assert events[-1].output == "echo:hi"


async def test_에이전트는_시각과_식별자를_컨텍스트에서_받는다() -> None:
    events = await _collect(EchoAgent(), FakeContext())
    assert events[0].run_id == "r1"
    assert events[0].ts == FIXED_NOW
