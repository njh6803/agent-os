"""런타임이 모델·도구 호출 안에서 만든 이벤트(`llm_called`, `tool_called`)가 `run()` 에서 언제
나오는지 잰다.

web-widget 명세의 "실시간 중계" 절의 근거다. `core/run.py`(934f8dfa)를 읽으면 그 이벤트는 컨텍스트의
`_pending` 에 쌓였다가 에이전트가 다음 이벤트를 낼 때(`_relay` 의 `take_events`)나 에이전트의 몫이
끝날 때 한꺼번에 나온다. 저장소의 계산 에이전트처럼 `ctx.llm()` 한 번이 루프 전체이고 그 뒤에
`run_finished` 를 내는 에이전트라면, 도구 줄과 모델 호출은 루프가 끝난 뒤 결말 바로 앞에 몰려
나온다는 해석이다. 위젯이 실행 도중 도구 줄을 쌓거나 "<도구> 부르는 중" 을 보이려면 이것이 갈린다.
같은 스크립트를 시제품(`live_relay.patch`)을 댄 사본에서 돌리면 그 시제품이 해석을 뒤집는지 본다.
두 사본을 나란히 돌리는 것은 `live_relay.py` 다.

갈래는 넷이고 모두 같은 가짜 포트(`TOOLS` 의 도구는 호출마다 `DELAY` 초 잠들고 `INSTANT` 는 바로
끝난다. 가짜 모델은 도구 둘을 차례로 요청한 뒤 글을 낸다)로 돈다.

- 한 번 갈래. `ctx.llm()` 한 번 뒤 `run_finished` 를 낸다(`plugins/agents/calc` 의 모양). 해석이
  맞으면 모델 호출 셋과 도구 호출 둘이 모두 도구 둘의 잠(2 × `DELAY`)이 지난 뒤 결말 바로 앞에
  나온다.
- 대조 갈래(양성 대조). 에이전트가 `ctx.tool()` 로 도구를 하나씩 부르고 그 사이에 자기 이벤트 하나를
  낸다. 해석이 맞으면 첫 도구의 `tool_called` 는 첫 잠 하나 뒤, 둘째 잠 전에 나온다. 이 갈래가 일찍
  나오는 이벤트를 보여야 재는 장치(받은 시각)가 늦게 나오는 것과 일찍 나오는 것을 가른다는 것이
  선다. 대조가 늦게 나오면 "이벤트는 에이전트의 다음 이벤트가 아니라 실행 끝에야 나온다" 는 다른
  해석이 남는다.
- 동시 갈래. 도구 둘을 `asyncio.gather` 로 함께 부른다. 시제품은 이벤트를 기록하는 자리에서
  몸통이 다음을 청할 때까지 기다리므로, 그 기다림이 두 호출을 줄 세우면 결말이 잠 둘 뒤로
  밀린다. 겹쳐 돌았으면 결말이 잠 하나 남짓 뒤다(문턱 1.5 × `DELAY`).
- 많은 호출 갈래. 잠들지 않는 도구를 `MANY` 번 부른다. 결말까지의 시간을 호출 수로 나눠 이벤트
  하나가 몸통을 지나는 비용을 낸다. 두 사본의 값을 견주는 것이 쓰임이고 한 사본의 값만으로는
  판정하지 않는다.

판정. 한 번·대조 갈래는 시작부터의 시각이 아니라 간격 둘로 판정한다(`_verdict`). 첫 모델 호출 앞의
준비 시간(이 PC에서 0.4초 안팎)이 시각에 섞이기 때문이다. 첫 도구 줄과 결말 사이에 둘째 도구의
잠이 끼면 도구 줄이 실행 도중 나온 것이고, 도구를 요청한 모델 호출과 첫 도구 줄 사이에 첫 도구의
잠이 끼면 요청이 그 도구를 부르기 전에 나온 것이다. 문턱은 잠의 0.8배다.

표지. 첫 줄 `core: <경로>` 는 이 실행이 읽은 `core/run.py` 의 경로다. `live_relay.py` 가 이 줄로 그
사본을 읽었는지 본다. 회차마다 그 갈래의 상황이 났는지 먼저 본다. 마지막 이벤트가 `run_finished`
이고, 가짜 도구가 기대한 수만큼 실제로 불렸고(가짜 연결의 기록), 런타임의 `tool_called` 가 그 수만큼
나왔다. 한 번·대조 갈래는 차례까지, 동시 갈래는 차례 없이 본다. 하나라도 아니거나 갈래가
`BRANCH_SECONDS` 안에 끝나지 않으면(맞물림이 멈춘 것이다) 측정이 아니라 세고 1로 끝난다. 결론은
측정인 회차의 도착 시각만으로 낸다.

쓰임: 저장소 루트에서 `uv run python .scratch/web-widget/probes/event_timing.py`
"""

from __future__ import annotations

import asyncio
import sys
import time
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Mapping, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import LanguageModelInput
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.messages.tool import ToolCall as LangchainToolCall
from langchain_core.outputs import ChatResult
from langchain_core.runnables import Runnable

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tools.probe_kit import Rounds  # noqa: E402

from agent_os.core import run as core_run  # noqa: E402
from agent_os.core.ports import (  # noqa: E402
    Cursor,
    ManifestRow,
    PluginKey,
    RunRow,
    RunStatus,
    ToolConnection,
    ToolResult,
    ToolSpec,
    Trace,
    WriteOutcome,
)
from agent_os.core.run import run  # noqa: E402
from agent_os.sdk import (  # noqa: E402
    AgentContext,
    AgentName,
    BaseAgent,
    Event,
    Json,
    McpServer,
    PluginKind,
    PluginManifest,
    PluginName,
    Principal,
    RunFinished,
    RunId,
    ToolCalled,
    parse_manifest,
)

DELAY = 0.5
TOOLS = ("lookup", "policy")
# 잠들지 않는 도구와 많은 호출 갈래가 그것을 부르는 수. 이벤트 하나가 지나는 비용을 잰다.
INSTANT = "instant"
MANY = 2000
NOW = datetime(2026, 10, 23, 12, 0, tzinfo=UTC)


class _Clock:
    def __init__(self) -> None:
        self._issued = 0

    def now(self) -> datetime:
        return NOW

    def new_run_id(self) -> RunId:
        self._issued += 1
        return RunId(f"run-{self._issued}")


class _Trace:
    def __init__(self) -> None:
        self.events: list[Event] = []

    def write(self, event: Event) -> None:
        self.events.append(event)

    def read(self, run_id: RunId) -> Trace | None:
        found = tuple(e for e in self.events if e.run_id == run_id)
        return Trace(run_id=run_id, schema_version="3", events=found) if found else None

    def list(
        self,
        *,
        status: RunStatus | None = None,
        limit: int | None = None,
        after: Cursor | None = None,
    ) -> tuple[RunRow, ...]:
        raise NotImplementedError


class _Plugins:
    def __init__(self, agent: BaseAgent) -> None:
        self._agent = agent

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None:
        if kind is PluginKind.AGENT and name == "shop":
            return parse_manifest(
                'schema_version = "1"\nkind = "agent"\nname = "shop"\nversion = "0.1.0"\n'
                'entrypoint = "agent:Agent"\nmcp = ["store"]\n'
            )
        if kind is PluginKind.MCP and name == "store":
            return parse_manifest(
                'schema_version = "1"\nkind = "mcp"\nname = "store"\nversion = "0.1.0"\n'
                '[server]\ncommand = "fake"\n'
            )
        return None

    def list_manifests(self, kind: PluginKind) -> tuple[ManifestRow, ...]:
        raise NotImplementedError

    def load_agent(self, manifest: PluginManifest) -> BaseAgent:
        return self._agent

    def read_disabled(self) -> frozenset[PluginKey]:
        return frozenset()

    def write_enabled(self, kind: PluginKind, name: PluginName, *, enabled: bool) -> WriteOutcome:
        raise NotImplementedError


class _SlowConnection:
    """`TOOLS` 의 도구는 `DELAY` 초 잠든 뒤, `INSTANT` 는 바로 성공한다. 불린 도구를 차례로
    적는다."""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def tools(self) -> Sequence[ToolSpec]:
        return [
            ToolSpec(name=n, description=n, input_schema={"type": "object", "properties": {}})
            for n in (*TOOLS, INSTANT)
        ]

    async def call(self, name: str, args: Mapping[str, Json]) -> ToolResult:
        if name in TOOLS:
            await asyncio.sleep(DELAY)
        self.calls.append(name)
        return ToolResult(ok=True, content=f"{name}:ok")


class _Tools:
    def __init__(self) -> None:
        self.connection = _SlowConnection()

    @asynccontextmanager
    async def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AsyncGenerator[ToolConnection]:
        yield self.connection


class _Model(GenericFakeChatModel):
    """도구를 붙이는 것을 받아들이기만 하는 가짜. 응답은 정해진 차례다."""

    def bind_tools(
        self,
        tools: Sequence[object],
        *,
        tool_choice: str | None = None,
        **kwargs: object,
    ) -> Runnable[LanguageModelInput, AIMessage]:
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: object,
    ) -> ChatResult:
        return super()._generate(messages, stop, run_manager, **kwargs)


def _request(name: str, index: int) -> AIMessage:
    return AIMessage(content="", tool_calls=[LangchainToolCall(name=name, args={}, id=f"c{index}")])


def _model() -> _Model:
    reply = AIMessage(
        content="done",
        response_metadata={"model_name": "fake-model"},
        usage_metadata={"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
    )
    return _Model(messages=iter([_request(TOOLS[0], 1), _request(TOOLS[1], 2), reply]))


class _OneShot:
    """`plugins/agents/calc` 의 모양. `ctx.llm()` 한 번이 루프 전체다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        output = await ctx.llm(request)
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=output)


class _Stepwise:
    """양성 대조. 도구를 직접 하나씩 부르고 그 사이에 자기 이벤트를 낸다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        first = await ctx.tool(TOOLS[0])
        yield ToolCalled(run_id=ctx.run_id, ts=ctx.now(), tool="agent-step", ok=True)
        second = await ctx.tool(TOOLS[1])
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=f"{first},{second}")


class _Concurrent:
    """도구 둘을 함께 부른다(`asyncio.gather`). 두 잠이 겹치면 결말이 잠 하나 뒤에 온다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        results = await asyncio.gather(ctx.tool(TOOLS[0]), ctx.tool(TOOLS[1]))
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=",".join(results))


class _Many:
    """잠들지 않는 도구를 `MANY` 번 부른다. 이벤트 하나가 몸통을 지나는 비용을 잰다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        for _ in range(MANY):
            await ctx.tool(INSTANT)
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output="done")


@dataclass(frozen=True)
class _Arrival:
    type: str
    tool: str
    seconds: float


async def _arrivals(agent: BaseAgent, tools: _Tools) -> list[_Arrival]:
    began = time.perf_counter()
    arrivals: list[_Arrival] = []
    async for event in run(
        AgentName("shop"),
        "우산 배송",
        Principal("probe"),
        plugins=_Plugins(agent),
        model=_model(),
        tools=tools,
        trace=_Trace(),
        clock=_Clock(),
    ):
        tool = event.tool if isinstance(event, ToolCalled) else ""
        arrivals.append(_Arrival(event.type, tool, time.perf_counter() - began))
    return arrivals


def _runtime_calls(arrivals: list[_Arrival], names: Sequence[str]) -> list[str]:
    return [a.tool for a in arrivals if a.type == "tool_called" and a.tool in names]


def _paced(arrivals: list[_Arrival], tools: _Tools) -> bool:
    """한 번·대조 갈래의 상황. 결말이 끝남이고, 런타임의 도구 호출 둘이 차례로 잠든 뒤 끝났다."""
    return (
        bool(arrivals)
        and arrivals[-1].type == "run_finished"
        and _runtime_calls(arrivals, TOOLS) == list(TOOLS)
        and tools.connection.calls == list(TOOLS)
    )


def _together(arrivals: list[_Arrival], tools: _Tools) -> bool:
    """동시 갈래의 상황. 결말이 끝남이고, 도구 둘이 차례와 무관하게 하나씩 불려 끝났다."""
    return (
        bool(arrivals)
        and arrivals[-1].type == "run_finished"
        and sorted(_runtime_calls(arrivals, TOOLS)) == sorted(TOOLS)
        and sorted(tools.connection.calls) == sorted(TOOLS)
    )


def _overlapped(arrivals: list[_Arrival]) -> str:
    """두 잠이 겹쳤으면 결말이 잠 하나 남짓 뒤다. 맞물림이 둘을 줄 세웠으면 잠 둘 뒤다."""
    finished = arrivals[-1].seconds
    return f"두 도구가 겹쳐 돌았다={finished < 1.5 * DELAY} (결말 {finished:.2f}s)"


def _counted(arrivals: list[_Arrival], tools: _Tools) -> bool:
    """많은 호출 갈래의 상황. 결말이 끝남이고, 도구가 `MANY` 번 불려 그만큼 도구 줄이 나왔다."""
    return (
        bool(arrivals)
        and arrivals[-1].type == "run_finished"
        and len(_runtime_calls(arrivals, (INSTANT,))) == MANY
        and tools.connection.calls.count(INSTANT) == MANY
    )


def _per_call(arrivals: list[_Arrival]) -> str:
    total = arrivals[-1].seconds
    return f"호출 하나에 {total / MANY * 1_000_000:.0f}µs (전체 {total:.2f}s)"


def _verdict(arrivals: list[_Arrival]) -> str:
    """간격 둘로 판정한다. 시작부터의 시각은 첫 모델 호출 앞의 준비 시간이 섞여 쓰지 않는다.

    도구 줄이 실행 도중 나오면 첫 도구 줄과 결말 사이에 둘째 도구의 잠(`DELAY`)이 끼고, 모아 두었다
    한꺼번에 나오면 그 간격이 0이다. 도구를 요청한 모델 호출이 그 도구를 부르기 전에 나오면 그 모델
    호출과 첫 도구 줄 사이에 첫 도구의 잠이 낀다. 문턱은 잠의 0.8배다.
    """
    first_tool = next(a for a in arrivals if a.type == "tool_called" and a.tool == TOOLS[0])
    finished = arrivals[-1]
    tool_live = finished.seconds - first_tool.seconds >= 0.8 * DELAY
    asked = [a for a in arrivals if a.type == "llm_called" and a.seconds <= first_tool.seconds]
    if not asked:
        return f"도구 줄이 결말보다 앞섰다={tool_live}, 도구를 요청한 모델 호출=없음"
    ask_live = first_tool.seconds - asked[-1].seconds >= 0.8 * DELAY
    return f"도구 줄이 결말보다 앞섰다={tool_live}, 요청이 도구 줄보다 앞섰다={ask_live}"


def _line(arrivals: list[_Arrival]) -> str:
    return ", ".join(
        f"{a.type}{'(' + a.tool + ')' if a.tool else ''}@{a.seconds:.2f}s" for a in arrivals
    )


type _Situation = Callable[[list[_Arrival], _Tools], bool]
type _Judge = Callable[[list[_Arrival]], str]

BRANCHES: tuple[tuple[str, Callable[[], BaseAgent], _Situation, _Judge], ...] = (
    ("한 번 갈래", _OneShot, _paced, _verdict),
    ("대조 갈래", _Stepwise, _paced, _verdict),
    ("동시 갈래", _Concurrent, _together, _overlapped),
    ("많은 호출 갈래", _Many, _counted, _per_call),
)
# 한 갈래의 기한(초). 넘기면 예외로 끝나 측정 아님으로 센다 — 맞물림이 멈춘 것이다.
BRANCH_SECONDS = 30


async def main() -> int:
    # 어느 core 를 쟀는지. 패치한 사본을 재는 `live_relay.py` 가 이 줄로 그 사본을 읽었는지 본다.
    print(f"core: {Path(core_run.__file__).resolve()}")
    rounds = Rounds()
    for label, make, situation, judge in BRANCHES:
        with rounds.round(label) as current:
            tools = _Tools()
            async with asyncio.timeout(BRANCH_SECONDS):
                arrivals = await _arrivals(make(), tools)
            if len(arrivals) < 20:
                print(f"{label}: {_line(arrivals)}")
            if not situation(arrivals, tools):
                current.mark(measured=False, result="상황이 나지 않았다")
                continue
            result = judge(arrivals)
            print(f"{label}: {result}")
            current.mark(measured=True, result=result)
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
