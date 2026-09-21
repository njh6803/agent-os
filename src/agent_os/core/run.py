"""주 이음매. 에이전트 이름, 요청, 주체와 포트 다섯을 받아 이벤트를 내는 async generator.

로더, 루프, 도구 연결, 트레이스 기록, 실패 정책이 전부 이 아래에 있어서 기본 스위트가 이 지점
하나를 민다. run_started 와 run_failed 는 런타임이 내고, 에이전트는 run_finished 하나를 마지막에
낸다. 에이전트가 낸 다른 이벤트는 그대로 통과한다. 여기서 내는 모든 이벤트는 TraceStore 에 쓴다.

실행 전과 실행 중의 경계: 없는 플러그인, 매니페스트 오류, 진입점 import 실패, 없는 mcp 이름은
실행 식별자를 만들기 전에 PluginError 로 끝나 트레이스가 없다. MCP 서버 기동 실패부터는 실행
안이라 run_failed 로 끝나고 트레이스가 남는다.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from datetime import datetime
from typing import TypeGuard

from agent_os.core.loop import run_loop
from agent_os.core.model import ModelReply
from agent_os.core.ports import (
    ChatModel,
    Clock,
    PluginError,
    PluginSource,
    ToolConnection,
    ToolResult,
    ToolSource,
    TraceStore,
)
from agent_os.sdk import (
    AgentName,
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
    ToolCall,
    ToolCalled,
    ToolError,
    approval_conflicts,
    secret_args_by_tool,
)

MASKED = "***"


def _mask(
    tool: str, args: Mapping[str, Json], secrets: Mapping[str, tuple[str, ...]]
) -> Mapping[str, Json]:
    """선언된 인자를 가려 이벤트에 담는다. 실제 도구 호출에는 진짜 값이 그대로 간다.

    마스킹하는 자리가 core 이고 트레이스 어댑터가 아닌 이유는, 원칙 V 가 금하는 것이 파일이
    아니라 이벤트이고 secret_args 를 아는 것도 core 이기 때문이다(ADR 0009).
    """
    names = secrets.get(tool, ())
    if not names:
        return args
    return {key: MASKED if key in names else value for key, value in args.items()}


class _Context:
    """AgentContext 를 시그니처로 만족한다. 루프 안에서 생긴 이벤트를 순서대로 쌓아 둔다."""

    def __init__(
        self,
        run_id: RunId,
        clock: Clock,
        model: ChatModel,
        tools: ToolConnection,
        secrets: Mapping[str, tuple[str, ...]],
    ) -> None:
        self.run_id = run_id
        self._clock = clock
        self._model = model
        self._tools = tools
        self._secrets = secrets
        self._pending: list[Event] = []

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
        """도구가 ok=false 를 돌려주든 예외를 던지든 에이전트에게는 같은 ToolError 다."""
        result = await _call_safely(self._tools, name, args)
        self._record_tool_call(name, args, result)
        if not result.ok:
            raise ToolError(result.content)
        return result.content

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
                text=reply.text,
                tool_calls=tuple(
                    ToolCall(
                        id=call.id,
                        name=call.name,
                        args=_mask(call.name, call.args, self._secrets),
                    )
                    for call in reply.tool_calls
                ),
            )
        )

    def _record_tool_call(self, name: str, args: Mapping[str, Json], result: ToolResult) -> None:
        self._pending.append(
            ToolCalled(
                run_id=self.run_id,
                ts=self.now(),
                tool=name,
                ok=result.ok,
                args=_mask(name, args, self._secrets),
                content=result.content,
            )
        )


async def run(
    agent: AgentName,
    request: str,
    principal: Principal,
    *,
    plugins: PluginSource,
    model: ChatModel,
    tools: ToolSource,
    trace: TraceStore,
    clock: Clock,
) -> AsyncIterator[Event]:
    manifest = _read_agent_manifest(plugins, agent)
    servers = _resolve_servers(plugins, manifest)
    _reject_masked_approvals(manifest, servers)
    secrets = secret_args_by_tool(servers)
    instance = plugins.load_agent(manifest)
    run_id = clock.new_run_id()

    def emit(event: Event) -> Event:
        trace.write(event)
        return event

    async def execute() -> AsyncIterator[Event]:
        """도구를 연결한 채 에이전트를 돌린다. 실패해도 그때까지 쌓인 이벤트를 먼저 흘린다."""
        async with tools.connect(servers) as connection:
            ctx = _Context(run_id, clock, model, connection, secrets)
            try:
                async for event in instance.run(request, ctx):
                    for pending in ctx.take_events():
                        yield pending
                    yield event
            finally:
                for pending in ctx.take_events():
                    yield pending

    yield emit(
        RunStarted(run_id=run_id, ts=clock.now(), agent=agent, request=request, principal=principal)
    )
    last: Event | None = None
    try:
        async for event in execute():
            last = event
            yield emit(event)
    except Exception as error:
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


def _reject_masked_approvals(
    manifest: PluginManifest, servers: Mapping[PluginName, McpServer]
) -> None:
    """금지 규칙을 실행 식별자가 생기기 전에 거부로 바꾼다. 이유는 sdk 의 approval_conflicts."""
    conflicts = approval_conflicts(manifest, servers)
    if conflicts:
        raise PluginError(
            f"마스킹된 인자를 가진 도구는 승인 대상이 될 수 없다: {', '.join(conflicts)}"
        )


async def _call_safely(tools: ToolConnection, name: str, args: dict[str, Json]) -> ToolResult:
    try:
        return await tools.call(name, args)
    except Exception as error:
        return ToolResult(ok=False, content=_describe(error))


def _describe(error: BaseException) -> str:
    """ExceptionGroup 은 겉만 보면 원인을 알 수 없어서 안의 예외를 펼친다."""
    if _is_group(error):
        inner = "; ".join(_describe(e) for e in error.exceptions)
        return f"{type(error).__name__}[{inner}]"
    return f"{type(error).__name__}: {error}"


def _is_group(error: BaseException) -> TypeGuard[BaseExceptionGroup[BaseException]]:
    """isinstance 로 좁히면 pyright 가 타입 인자를 Unknown 으로 둔다. 여기서 명시한다."""
    return isinstance(error, BaseExceptionGroup)
