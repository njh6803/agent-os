"""주 이음매. 에이전트 이름, 요청, 주체와 포트 다섯을 받아 이벤트를 내는 async generator.

로더, 루프, 도구 연결, 트레이스 기록, 실패 정책이 전부 이 아래에 있어서 기본 스위트가 이 지점
하나를 민다. run_started 와 run_failed 는 런타임이 내고, 에이전트는 run_finished 하나를 마지막에
낸다. 에이전트가 낸 다른 이벤트는 그대로 통과한다. 여기서 내는 모든 이벤트는 TraceSink 에 쓴다.

실행 전과 실행 중의 경계: 없는 플러그인, 매니페스트 오류, 진입점 import 실패, 없는 mcp 이름은
실행 식별자를 만들기 전에 PluginError 로 끝나 트레이스가 없다. MCP 서버 기동 실패부터는 실행
안이라 run_failed 로 끝나고 트레이스가 남는다.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from datetime import datetime
from typing import TypeGuard

from agent_os.core.loop import run_loop
from agent_os.core.model import ModelReply
from agent_os.core.ports import (
    ChatModel,
    Clock,
    PluginError,
    PluginSource,
    ToolSession,
    ToolSource,
    TraceSink,
)
from agent_os.sdk import (
    AgentName,
    BaseAgent,
    Event,
    Json,
    LlmCalled,
    McpServer,
    PluginKind,
    PluginManifest,
    PluginName,
    Principal,
    RunFailed,
    RunFinished,
    RunId,
    RunStarted,
    ToolCalled,
    ToolError,
)


class _Context:
    """AgentContext 를 시그니처로 만족한다. 루프 안에서 생긴 이벤트를 record 로 쌓는다."""

    def __init__(
        self,
        run_id: RunId,
        clock: Clock,
        model: ChatModel,
        tools: ToolSession,
        record: Callable[[Event], None],
    ) -> None:
        self.run_id = run_id
        self._clock = clock
        self._model = model
        self._tools = tools
        self._record = record

    def now(self) -> datetime:
        return self._clock.now()

    async def llm(self, prompt: str) -> str:
        return await run_loop(
            self._model,
            prompt,
            tools=self._tools,
            on_model_call=self._record_model_call,
            on_tool_call=self._record_tool_call,
        )

    async def tool(self, name: str, **args: Json) -> str:
        result = await self._tools.call(name, args)
        self._record_tool_call(name, result.ok)
        if not result.ok:
            raise ToolError(result.content)
        return result.content

    def _record_model_call(self, reply: ModelReply) -> None:
        self._record(
            LlmCalled(
                run_id=self.run_id,
                ts=self.now(),
                model=reply.model,
                input_tokens=reply.input_tokens,
                output_tokens=reply.output_tokens,
            )
        )

    def _record_tool_call(self, name: str, ok: bool) -> None:
        self._record(ToolCalled(run_id=self.run_id, ts=self.now(), tool=name, ok=ok))


async def run(
    agent: AgentName,
    request: str,
    principal: Principal,
    *,
    plugins: PluginSource,
    model: ChatModel,
    tools: ToolSource,
    trace: TraceSink,
    clock: Clock,
) -> AsyncIterator[Event]:
    manifest = _read_agent_manifest(plugins, agent)
    instance = plugins.load_agent(manifest)
    servers = _resolve_servers(plugins, manifest)
    run_id = clock.new_run_id()
    pending: list[Event] = []

    def emit(event: Event) -> Event:
        trace.write(event)
        return event

    def drain() -> list[Event]:
        """호출 안의 이벤트가 에이전트의 다음 이벤트보다 앞선다는 순서 보장이 여기서 지켜진다."""
        taken, pending[:] = pending[:], []
        return taken

    yield emit(
        RunStarted(run_id=run_id, ts=clock.now(), agent=agent, request=request, principal=principal)
    )
    last: Event | None = None
    try:
        async with tools.connect(servers) as session:
            ctx = _Context(run_id, clock, model, session, pending.append)
            async for event in _events_of(instance, request, ctx, drain):
                last = event
                yield emit(event)
    except Exception as error:
        for event in drain():
            yield emit(event)
        yield emit(RunFailed(run_id=run_id, ts=clock.now(), error=_describe(error)))
        return
    if not isinstance(last, RunFinished):
        yield emit(
            RunFailed(run_id=run_id, ts=clock.now(), error="에이전트가 run_finished 없이 끝났다")
        )


def _read_agent_manifest(plugins: PluginSource, agent: AgentName) -> PluginManifest:
    manifest = plugins.read_manifest(PluginKind.AGENT, PluginName(agent))
    if manifest is None:
        raise PluginError(f"에이전트 플러그인이 없다: {agent}")
    return manifest


def _resolve_servers(
    plugins: PluginSource, manifest: PluginManifest
) -> dict[PluginName, McpServer]:
    """매니페스트가 지정한 mcp 플러그인만. 비어 있으면 도구가 없다(ADR 0002)."""
    servers: dict[PluginName, McpServer] = {}
    for name in manifest.mcp:
        mcp = plugins.read_manifest(PluginKind.MCP, name)
        if mcp is None or mcp.server is None:
            raise PluginError(f"에이전트 {manifest.name} 이 지정한 mcp 플러그인이 없다: {name}")
        servers[name] = mcp.server
    return servers


async def _events_of(
    agent: BaseAgent, request: str, ctx: _Context, drain: Callable[[], list[Event]]
) -> AsyncIterator[Event]:
    async for event in agent.run(request, ctx):
        for pending in drain():
            yield pending
        yield event
    for pending in drain():
        yield pending


def _describe(error: BaseException) -> str:
    """ExceptionGroup 은 겉만 보면 원인을 알 수 없어서 안의 예외를 펼친다."""
    if _is_group(error):
        inner = "; ".join(_describe(e) for e in error.exceptions)
        return f"{type(error).__name__}[{inner}]"
    return f"{type(error).__name__}: {error}"


def _is_group(error: BaseException) -> TypeGuard[BaseExceptionGroup[BaseException]]:
    """isinstance 로 좁히면 pyright 가 타입 인자를 Unknown 으로 둔다. 여기서 명시한다."""
    return isinstance(error, BaseExceptionGroup)
