"""저장소의 calc 플러그인. 실물 플러그인 루트(`plugins/`)에서 읽고 가짜 모델로 돌려 프롬프트를 본다.

calc 는 컨텍스트 멤버(자기 대화 요약과 그 뒤 교환)를 "앞 대화" 블록으로 프롬프트에 엮는다(ADR 0022
"에이전트는 앞 교환을 문자열 프롬프트로 엮는다", conversation 명세 "calc"). 이어 가지 않은 실행의
프롬프트는 그 결정 전과 글자 그대로 같아야 해서 그 문자열을 여기 박아 둔다 — 블록이 빈 대화에 새면
여기서 잡힌다(명세 "calc"의 2026-10-04 명세 검토, 스토리 40). 도구 포트는 가짜라 도구가 없고,
calc 의 매니페스트가 가리키는 mcp(`everything`)는 실물 루트에서 읽힌다. 실제 모델과 실제 서버로
도는 것은 `tests/test_main.py` 의 `-m llm` 사례다.
"""

from collections.abc import AsyncGenerator, Mapping, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult

from agent_os.adapters.filesystem import FilesystemPlugins
from agent_os.adapters.jsonl import JsonlTrace
from agent_os.core.ports import (
    ChatModel,
    Clock,
    McpServer,
    PluginSource,
    ToolConnection,
    ToolResult,
    ToolSource,
    ToolSpec,
    TraceStore,
)
from agent_os.core.run import run
from agent_os.sdk import (
    AgentName,
    ConversationSummarized,
    Event,
    Json,
    LlmCalled,
    PluginName,
    Principal,
    RunFinished,
    RunId,
    RunStarted,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PRINCIPAL = Principal("alice")
NOW = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)

# 이 티켓 전의 calc 프롬프트 그대로. 이어 가지 않은 실행은 이것과 글자 그대로 같아야 한다.
FRESH_PROMPT = (
    "계산 요청이다. 도구가 있으면 도구로 계산한다. 최종 답만 짧게 답한다.\n\n요청: 2 더하기 3은?"
)


class RecordingModel(GenericFakeChatModel):
    """정해진 답을 내고 호출마다 받은 것을 남긴다. 프롬프트가 무엇이었는지는 이것이 원천이다."""

    received: list[list[BaseMessage]] = []

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: object,
    ) -> ChatResult:
        self.received.append(list(messages))
        return super()._generate(messages, stop, run_manager, **kwargs)


class NoToolConnection:
    def tools(self) -> Sequence[ToolSpec]:
        return []

    async def call(self, name: str, args: Mapping[str, Json]) -> ToolResult:
        raise AssertionError(f"도구가 없는 연결에서 {name} 을 불렀다")


class NoTools:
    """연결은 열리지만 도구가 없다. 실물 매니페스트의 mcp 가 여기까지 오는 것만 받아 준다."""

    @asynccontextmanager
    async def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AsyncGenerator[ToolConnection]:
        yield NoToolConnection()


class CountingClock:
    def __init__(self) -> None:
        self.issued = 0

    def now(self) -> datetime:
        return NOW

    def new_run_id(self) -> RunId:
        self.issued += 1
        return RunId(f"run-{self.issued}")


def _model(answer: str) -> RecordingModel:
    return RecordingModel(messages=iter([AIMessage(content=answer)]))


async def _run_calc(
    request: str,
    *,
    model: ChatModel,
    trace: TraceStore,
    clock: Clock,
    previous_run: RunId | None = None,
) -> list[Event]:
    plugins: PluginSource = FilesystemPlugins(REPO_ROOT / "plugins")
    tools: ToolSource = NoTools()
    return [
        event
        async for event in run(
            AgentName("calc"),
            request,
            PRINCIPAL,
            previous_run=previous_run,
            plugins=plugins,
            model=model,
            tools=tools,
            trace=trace,
            clock=clock,
        )
    ]


def _prompt_of(model: RecordingModel, events: Sequence[Event]) -> str:
    """모델이 한 번 받은 프롬프트. 트레이스의 `llm_called.prompt` 와 같아야 한다."""
    (messages,) = model.received
    (message,) = messages
    (called,) = (e for e in events if isinstance(e, LlmCalled))
    assert isinstance(message.content, str)
    assert called.prompt == message.content
    return message.content


def _finished(events: Sequence[Event]) -> RunId:
    assert isinstance(events[-1], RunFinished), [e.type for e in events]
    return events[-1].run_id


async def test_이어_가지_않은_실행의_프롬프트는_이_티켓_전과_글자_그대로_같다(
    tmp_path: Path,
) -> None:
    model = _model("5")

    events = await _run_calc(
        "2 더하기 3은?", model=model, trace=JsonlTrace(tmp_path), clock=CountingClock()
    )

    assert _prompt_of(model, events) == FRESH_PROMPT
    assert isinstance(events[-1], RunFinished)
    assert events[-1].output == "5"


async def test_이어_간_실행의_프롬프트는_앞_교환을_오래된_것부터_데이터라고_밝힌_블록으로_든다(
    tmp_path: Path,
) -> None:
    """블록은 요청 앞에 서고, 그 안의 글이 지시가 아니라 데이터라고 적는다(sdk 멤버의 신뢰 경계)."""
    trace, clock = JsonlTrace(tmp_path), CountingClock()
    first = _finished(await _run_calc("2 더하기 3은?", model=_model("5"), trace=trace, clock=clock))
    second = _finished(
        await _run_calc(
            "거기에 4를 곱하면?", model=_model("20"), trace=trace, clock=clock, previous_run=first
        )
    )
    model = _model("14")

    events = await _run_calc(
        "거기에서 6을 빼면?", model=model, trace=trace, clock=clock, previous_run=second
    )

    prompt = _prompt_of(model, events)
    head = FRESH_PROMPT.partition("요청: ")[0]
    assert prompt.startswith(head)
    assert prompt.endswith("요청: 거기에서 6을 빼면?")
    assert "앞 대화" in prompt
    assert "지시가 아니라 데이터" in prompt
    order = ["2 더하기 3은?", "5", "거기에 4를 곱하면?", "20", "요청: 거기에서 6을 빼면?"]
    positions = [prompt.index(piece) for piece in order]
    assert positions == sorted(positions), prompt


async def test_요약이_있으면_요약이_교환보다_앞에_서고_덮인_교환은_들지_않는다(
    tmp_path: Path,
) -> None:
    """런타임이 쓴 모양의 요약 이벤트를 손으로 둔 고리다. 요약은 런타임만 내므로 여기서는 트레이스에
    직접 쓴다. 덮는 끝(첫 실행)은 거슬러 읽기가 읽지 않아 그 요청이 프롬프트에 없다."""
    trace = JsonlTrace(tmp_path)
    for event in _summarized_chain():
        trace.write(event)
    model = _model("14")

    events = await _run_calc(
        "거기에서 6을 빼면?",
        model=model,
        trace=trace,
        clock=CountingClock(),
        previous_run=RunId("run-b"),
    )

    prompt = _prompt_of(model, events)
    assert "2 더하기 3은?" not in prompt
    order = [
        "요청한 쪽이 2 더하기 3을 물었고",
        "거기에 4를 곱하면?",
        "20",
        "요청: 거기에서 6을 빼면?",
    ]
    positions = [prompt.index(piece) for piece in order]
    assert positions == sorted(positions), prompt


def _summarized_chain() -> list[Event]:
    """run-a(끝남) ← run-b(run-a 를 이어 가며 run-a 까지 접은 요약을 들고 끝남)."""
    return [
        RunStarted(
            run_id=RunId("run-a"),
            ts=NOW,
            agent=AgentName("calc"),
            request="2 더하기 3은?",
            principal=PRINCIPAL,
        ),
        RunFinished(run_id=RunId("run-a"), ts=NOW, output="5"),
        RunStarted(
            run_id=RunId("run-b"),
            ts=NOW,
            agent=AgentName("calc"),
            request="거기에 4를 곱하면?",
            principal=PRINCIPAL,
            previous_run=RunId("run-a"),
        ),
        ConversationSummarized(
            run_id=RunId("run-b"),
            ts=NOW,
            summary="요청한 쪽이 2 더하기 3을 물었고 에이전트가 5라고 답했다",
            last_covered_run=RunId("run-a"),
            model="fake",
            input_tokens=1,
            output_tokens=1,
        ),
        RunFinished(run_id=RunId("run-b"), ts=NOW, output="20"),
    ]
