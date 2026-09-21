"""주 이음매. 에이전트 이름, 요청, 주체와 포트 다섯을 받아 이벤트를 내는 async generator.

로더, 루프, 도구 연결, 승인 게이트, 트레이스 기록, 실패 정책이 전부 이 아래에 있어서 기본 스위트가
이 지점 하나를 민다. run_started, run_paused, run_failed 는 런타임이 내고, 에이전트는 run_finished
하나를 마지막에 낸다. 에이전트가 낸 다른 이벤트는 그대로 통과한다. 여기서 내는 모든 이벤트는
TraceStore 에 쓴다.

실행 전과 실행 중의 경계: 없는 플러그인, 매니페스트 오류, 진입점 import 실패, 없는 mcp 이름,
마스킹과 승인이 겹치는 도구는 실행 식별자를 만들기 전에 PluginError 로 끝나 트레이스가 없다.
MCP 서버 기동 실패부터는 실행 안이라 run_failed 로 끝나고 트레이스가 남는다. 매니페스트가
가리키는 도구와 인자의 실재는 도구 목록이 연결 뒤에야 나오므로 연결 직후에 검사하고, 어긋나면
실행 안의 실패다(ADR 0009).
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping, Sequence
from datetime import datetime
from typing import NoReturn, TypeGuard

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
    ToolSpec,
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
    RunPaused,
    RunStarted,
    ToolCall,
    ToolCalled,
    ToolError,
    approval_conflicts,
    secret_args_by_tool,
)

MASKED = "***"


class _Paused(BaseException):
    """게이트가 실행을 멈추는 신호. 에이전트의 제너레이터를 지나 실행 조립부까지 올라간다.

    Exception 이 아닌 이유는 플러그인이 `except Exception` 으로 삼키면 가드레일이 아니기 때문이다.
    에이전트 코드는 신뢰 경계 밖이다. 그래도 삼키면 컨텍스트가 그 뒤의 어떤 호출도 하지 않는다.
    """


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
    """AgentContext 를 시그니처로 만족한다. 루프 안에서 생긴 이벤트를 순서대로 쌓아 둔다.

    도구 호출은 루프에서 오든 에이전트가 직접 부르든 _call 하나를 지난다. 게이트, 마스킹, 기록이
    그 한 자리에 있어서 경로를 바꿔 빠져나갈 수 없다(ADR 0009).
    """

    def __init__(
        self,
        run_id: RunId,
        clock: Clock,
        model: ChatModel,
        tools: ToolConnection,
        secrets: Mapping[str, tuple[str, ...]],
        approvals: frozenset[str],
    ) -> None:
        self.run_id = run_id
        self._paused = False
        self._clock = clock
        self._model = model
        self._tools = tools
        self._secrets = secrets
        self._approvals = approvals
        self._pending: list[Event] = []

    @property
    def paused(self) -> bool:
        """조립부가 읽는다. 플러그인이 되돌릴 수 없도록 읽기 전용이다."""
        return self._paused

    def now(self) -> datetime:
        return self._clock.now()

    async def llm(self, prompt: str) -> str:
        self._stay_paused()
        return await run_loop(
            self._model,
            prompt,
            tools=self._tools.tools(),
            call=self._call,
            on_model_call=self._record_model_call,
        )

    async def tool(self, name: str, **args: Json) -> str:
        """도구가 ok=false 를 돌려주든 예외를 던지든 에이전트에게는 같은 ToolError 다."""
        result = await self._call(name, args)
        if not result.ok:
            raise ToolError(result.content)
        return result.content

    def take_events(self) -> list[Event]:
        """쌓인 이벤트를 비우며 돌려준다. 호출 안의 이벤트가 에이전트의 다음 이벤트보다 앞선다."""
        taken, self._pending = self._pending, []
        return taken

    async def _call(self, name: str, args: Mapping[str, Json]) -> ToolResult:
        self._stay_paused()
        if name in self._approvals:
            self._pause(name, args)
        result = await _call_safely(self._tools, name, args)
        self._record_tool_call(name, args, result)
        return result

    def _pause(self, name: str, args: Mapping[str, Json]) -> NoReturn:
        """도구를 부르지 않은 채 일시정지를 기록하고 실행을 끝낸다. 재개는 04 의 일이다."""
        self._pending.append(
            RunPaused(
                run_id=self.run_id,
                ts=self.now(),
                tool=name,
                args=_mask(name, args, self._secrets),
            )
        )
        self._paused = True
        raise _Paused()

    def _stay_paused(self) -> None:
        """멈춘 뒤에는 모델도 도구도 부르지 않는다. 신호를 삼킨 에이전트가 이어 가지 못하게."""
        if self._paused:
            raise _Paused()

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
    approvals = frozenset(manifest.requires_approval)
    instance = plugins.load_agent(manifest)
    run_id = clock.new_run_id()

    def emit(event: Event) -> Event:
        trace.write(event)
        return event

    async def execute() -> AsyncIterator[Event]:
        """도구를 연결한 채 에이전트를 돌린다. 실패해도 그때까지 쌓인 이벤트를 먼저 흘린다.

        일시정지는 실패가 아니다. 신호를 여기서 받아 연결을 정상으로 닫고, 쌓인 이벤트의 끝에
        run_paused 가 있다. 에이전트가 신호를 삼키고 이어 가도 그 뒤의 이벤트는 통과시키지 않고,
        신호를 다른 예외로 감싸 올려도 멈춘 실행에 run_failed 가 덧붙지 않는다.
        """
        async with tools.connect(servers) as connection:
            _reject_unknown_declarations(approvals, secrets, connection.tools())
            ctx = _Context(run_id, clock, model, connection, secrets, approvals)
            try:
                async for event in instance.run(request, ctx):
                    for pending in ctx.take_events():
                        yield pending
                    if ctx.paused:
                        break
                    yield event
            except _Paused:
                pass
            except Exception:
                if not ctx.paused:
                    raise
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
    if not isinstance(last, RunFinished | RunPaused):
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


def _reject_unknown_declarations(
    approvals: frozenset[str],
    secrets: Mapping[str, tuple[str, ...]],
    specs: Sequence[ToolSpec],
) -> None:
    """매니페스트가 가리키는 도구와 인자가 실재하는지. 도구 목록이 연결 뒤에 나와 여기가 첫 자리다.

    오타나 중첩 프로퍼티가 게이트나 마스킹을 조용히 끄는 fail-open 을 막는다(ADR 0009 와 그
    2026-09-21 이력). 실행 안이라 run_failed 로 끝나고 트레이스가 남는다.
    """
    params = {spec.name: _param_names(spec) for spec in specs}
    for tool in approvals:
        if tool not in params:
            raise LookupError(f"requires_approval 이 가리키는 도구가 없다: {tool}")
    for tool, names in secrets.items():
        if tool not in params:
            raise LookupError(f"secret_args 가 가리키는 도구가 없다: {tool}")
        for name in names:
            if name not in params[tool]:
                raise LookupError(f"secret_args 가 가리키는 인자가 도구 {tool} 에 없다: {name}")


def _param_names(spec: ToolSpec) -> frozenset[str]:
    """JSON Schema 의 properties 키. 없으면 이름 있는 인자가 없는 도구다."""
    properties = spec.input_schema.get("properties")
    return frozenset(properties) if isinstance(properties, dict) else frozenset()


async def _call_safely(tools: ToolConnection, name: str, args: Mapping[str, Json]) -> ToolResult:
    """도구가 예외를 내도 실행은 죽지 않는다. 에러 내용을 결과로 바꿔 모델이 알게 한다."""
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
