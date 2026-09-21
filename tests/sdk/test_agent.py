"""BaseAgent 프로토콜이 async generator로 구현 가능하고 이벤트가 흐르는지."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime

from agent_os.sdk import AgentContext, BaseAgent, Event, RunFinished, RunStarted


class FakeContext:
    async def llm(self, prompt: str) -> str:
        return f"echo:{prompt}"

    async def tool(self, name: str, **args: object) -> str:
        return "unused"


class EchoAgent:
    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        now = datetime.now(UTC)
        yield RunStarted(run_id="r1", ts=now, agent="echo", request=request)
        answer = await ctx.llm(request)
        yield RunFinished(run_id="r1", ts=now, output=answer)


async def _collect(agent: BaseAgent, ctx: AgentContext) -> list[Event]:
    return [event async for event in agent.run("hi", ctx)]


async def test_agent_yields_event_stream() -> None:
    events = await _collect(EchoAgent(), FakeContext())
    assert [event.type for event in events] == ["run_started", "run_finished"]
    assert isinstance(events[-1], RunFinished)
    assert events[-1].output == "echo:hi"
