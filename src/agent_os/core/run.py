"""주 이음매. 에이전트 이름, 요청, 주체와 포트를 받아 이벤트를 내는 async generator.

로더, 루프, 트레이스 기록, 실패 정책이 전부 이 아래에 있어서 기본 스위트가 이 지점 하나를 민다.
run_started 와 run_failed 는 런타임이 내고, 에이전트는 run_finished 하나를 마지막에 낸다.
에이전트가 낸 다른 이벤트는 그대로 통과한다. 여기서 내는 모든 이벤트는 TraceSink 에 쓴다(원칙 V).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime

from agent_os.core.loop import run_loop
from agent_os.core.model import ModelReply
from agent_os.core.ports import ChatModel, Clock, PluginError, PluginSource, TraceSink
from agent_os.sdk import (
    AgentName,
    BaseAgent,
    Event,
    LlmCalled,
    PluginKind,
    PluginName,
    Principal,
    RunFailed,
    RunFinished,
    RunId,
    RunStarted,
)


class _Context:
    """AgentContext 를 시그니처로 만족한다. 루프 안에서 생긴 이벤트를 순서대로 쌓아 둔다."""

    def __init__(self, run_id: RunId, clock: Clock, model: ChatModel) -> None:
        self.run_id = run_id
        self._clock = clock
        self._model = model
        self._pending: list[Event] = []

    def now(self) -> datetime:
        return self._clock.now()

    async def llm(self, prompt: str) -> str:
        return await run_loop(self._model, prompt, on_model_call=self._record_model_call)

    async def tool(self, name: str, **args: object) -> str:
        # TODO(first-slice/07): ToolSource 를 통해 모델을 거치지 않고 부른다
        raise LookupError(f"도구가 없다: {name}")

    def take_events(self) -> list[Event]:
        """쌓인 이벤트를 비우며 돌려준다. 호출 안의 이벤트가 에이전트의 다음 이벤트보다 앞선다."""
        taken, self._pending = self._pending, []
        return taken

    def _record_model_call(self, reply: ModelReply) -> None:
        self._pending.append(
            LlmCalled(
                run_id=self.run_id,
                ts=self.now(),
                model=reply.model,
                input_tokens=reply.input_tokens,
                output_tokens=reply.output_tokens,
            )
        )


async def run(
    agent: AgentName,
    request: str,
    principal: Principal,
    *,
    plugins: PluginSource,
    model: ChatModel,
    trace: TraceSink,
    clock: Clock,
) -> AsyncIterator[Event]:
    instance = _load(plugins, agent)
    run_id = clock.new_run_id()
    ctx = _Context(run_id, clock, model)

    def emit(event: Event) -> Event:
        trace.write(event)
        return event

    yield emit(
        RunStarted(run_id=run_id, ts=clock.now(), agent=agent, request=request, principal=principal)
    )
    last: Event | None = None
    try:
        async for event in _events_of(instance, request, ctx):
            last = event
            yield emit(event)
    except Exception as error:
        for event in ctx.take_events():
            yield emit(event)
        yield emit(RunFailed(run_id=run_id, ts=clock.now(), error=_describe(error)))
        return
    if not isinstance(last, RunFinished):
        yield emit(
            RunFailed(run_id=run_id, ts=clock.now(), error="에이전트가 run_finished 없이 끝났다")
        )


def _load(plugins: PluginSource, agent: AgentName) -> BaseAgent:
    """실행 전 단계. 여기서 나는 오류는 실행 식별자도 트레이스도 없이 PluginError 로 끝난다."""
    manifest = plugins.read_manifest(PluginKind.AGENT, PluginName(agent))
    if manifest is None:
        raise PluginError(f"에이전트 플러그인이 없다: {agent}")
    return plugins.load_agent(manifest)


async def _events_of(agent: BaseAgent, request: str, ctx: _Context) -> AsyncIterator[Event]:
    async for event in agent.run(request, ctx):
        for pending in ctx.take_events():
            yield pending
        yield event
    for pending in ctx.take_events():
        yield pending


def _describe(error: Exception) -> str:
    return f"{type(error).__name__}: {error}"
