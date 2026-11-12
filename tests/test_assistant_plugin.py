"""저장소의 기본 에이전트 묶음(`assistant`, 스킬 `cite-sources`, 연결 `doc-search`, 규칙 파일의 표).

저장소의 `plugins/` 를 임시 루트에 복사하고 `doc-search` 의 주소만 가짜 문서 검색 서버
(`tests/fake_doc_search_server.py`)의 것으로 바꿔 쓴다. 실제 플러그인 어댑터(`FilesystemPlugins`),
실제 MCP 어댑터(`McpTools`), 대본 모델로 런타임의 실행 함수(`run`·`resume`)를 부른다. 환경 변수
`DOC_SEARCH_AUTHORIZATION` 은 시험이 준다(base-agent 명세 "플러그인 꾸러미의 시험").

보는 것은 바깥에서 보이는 동작이다. 모델이 받은 프롬프트의 글자, 트레이스의 이벤트, 가짜 서버가 받은
요청이다. 에이전트 코드의 함수나 상수는 부르지 않는다. 가짜 서버는 모듈 안의 시험이 나눠 쓰는
하나이고(띄우는 데 오래 걸린다), 시험은 자기가 시작하기 전의 기록 수를 재 두었다가 그 뒤의 기록만
본다. 실제 모델로 도는 것은 티켓 05의 시험이다.
"""

import itertools
import shutil
import tomllib
from collections.abc import Generator, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeGuard

import pytest
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import LanguageModelInput
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.messages.tool import ToolCall as LangchainToolCall
from langchain_core.outputs import ChatResult
from langchain_core.runnables import Runnable
from tests.fake_doc_search import DocSearchFixture, serving
from tests.fake_doc_search_server import FORMAT_VERSION, PARENTAL_TEXTS
from tests.fake_models import FakeModels

from agent_os.adapters.filesystem import FilesystemPlugins
from agent_os.adapters.jsonl import JsonlTrace
from agent_os.adapters.mcp import McpTools
from agent_os.core.ports import Rule, Rules, RuleSet, TraceStore
from agent_os.core.run import Approve, Deny, resume, run
from agent_os.sdk import (
    AgentName,
    Event,
    HttpServer,
    LlmCalled,
    PluginKind,
    PluginManifest,
    PluginName,
    Principal,
    RunFailed,
    RunFinished,
    RunId,
    RunPaused,
    Skill,
    ToolCalled,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGINS = REPO_ROOT / "plugins"
PRINCIPAL = Principal("alice")
NOW = datetime(2026, 11, 12, 12, 0, tzinfo=UTC)
DEFAULT_MODEL = PluginName("claude-opus-5")
VARIABLE = "DOC_SEARCH_AUTHORIZATION"
AUTHORIZATION = "Bearer bundle-token-2222"
CHILD_CARE_ID = "6f1c2a9e-4b7d-4e15-9c3a-2d8b7e5f0a11"
QUESTION = "육아휴직은 최대 몇 년까지 쓸 수 있어?"
# 스킬 문서가 정한 근거 없음의 문장. 스킬 파일이 이 글자를 담는지 본다(명세 "스킬 cite-sources").
NOT_FOUND = (
    "등록된 문서에서 관련 내용을 찾지 못했으니, 다른 표현이나 다른 질문으로 다시 물어봐 주세요."
)
SERVER_URL_LINE = 'url = "http://rag-engine:8000/mcp"'


class ScriptedModel(GenericFakeChatModel):
    """정해진 응답을 내고 호출마다 받은 메시지와 붙은 도구의 이름을 남기는 대본 모델."""

    received: list[list[BaseMessage]] = []
    bound: list[list[str]] = []

    def bind_tools(
        self,
        tools: Sequence[object],
        *,
        tool_choice: str | None = None,
        **kwargs: object,
    ) -> Runnable[LanguageModelInput, AIMessage]:
        self.bound.append([str(tool["name"]) for tool in tools if _is_named(tool)])
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: object,
    ) -> ChatResult:
        self.received.append(list(messages))
        return super()._generate(messages, stop, run_manager, **kwargs)


def _is_named(tool: object) -> TypeGuard[Mapping[str, object]]:
    """langchain 에 넘기는 도구 dict. `isinstance` 로 좁히면 타입 인자가 Unknown 이 된다."""
    return isinstance(tool, Mapping) and "name" in tool


_CALL_IDS = itertools.count(1)


def _call(name: str, **args: str | bool) -> AIMessage:
    """모델이 한 턴에 낸 도구 호출 하나."""
    return AIMessage(
        content="",
        tool_calls=[LangchainToolCall(name=name, args=dict(args), id=f"call-{next(_CALL_IDS)}")],
    )


def _search() -> AIMessage:
    return _call("search", query="육아휴직 기간")


def _read_document() -> AIMessage:
    return _call("get_document", document_id=CHILD_CARE_ID, include_text=True)


def _model(*replies: AIMessage | str) -> ScriptedModel:
    return ScriptedModel(
        messages=iter([AIMessage(content=r) if isinstance(r, str) else r for r in replies])
    )


class CountingClock:
    def __init__(self) -> None:
        self.issued = 0

    def now(self) -> datetime:
        return NOW

    def new_run_id(self) -> RunId:
        self.issued += 1
        return RunId(f"run-{self.issued}")


@pytest.fixture(scope="module")
def fake_server(tmp_path_factory: pytest.TempPathFactory) -> Generator[DocSearchFixture]:
    """모듈이 나눠 쓰는 가짜 검색 서버. 기대한 `Authorization` 이 아닌 요청은 401 로 막는다."""
    with serving(
        tmp_path_factory.mktemp("doc_search"), "--expect-authorization", AUTHORIZATION
    ) as server:
        yield server


@pytest.fixture(autouse=True)
def authorization(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(VARIABLE, AUTHORIZATION)


def _root(tmp_path: Path, server: DocSearchFixture) -> Path:
    """저장소 `plugins/` 의 사본. `doc-search` 의 주소만 가짜 검색 서버의 것이다."""
    root = tmp_path / "plugins"
    shutil.copytree(PLUGINS, root, ignore=shutil.ignore_patterns("__pycache__"))
    _edit(root / "mcp" / "doc-search" / "plugin.toml", SERVER_URL_LINE, f'url = "{server.url}"')
    return root


def _edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == 1, text
    path.write_text(text.replace(old, new), encoding="utf-8")


async def _run(
    request: str,
    *,
    model: ScriptedModel,
    root: Path,
    trace: TraceStore,
    clock: CountingClock,
    previous_run: RunId | None = None,
) -> list[Event]:
    return [
        event
        async for event in run(
            AgentName("assistant"),
            request,
            PRINCIPAL,
            previous_run=previous_run,
            default_model=DEFAULT_MODEL,
            plugins=FilesystemPlugins(root),
            models=FakeModels(model),
            tools=McpTools(),
            trace=trace,
            clock=clock,
        )
    ]


async def _resume(
    run_id: RunId,
    decision: Approve | Deny,
    *,
    model: ScriptedModel,
    root: Path,
    trace: TraceStore,
    clock: CountingClock,
) -> list[Event]:
    stored = trace.read(run_id)
    assert stored is not None
    return [
        event
        async for event in resume(
            run_id,
            len(stored.events) - 1,
            decision,
            PRINCIPAL,
            default_model=DEFAULT_MODEL,
            plugins=FilesystemPlugins(root),
            models=FakeModels(model),
            tools=McpTools(),
            trace=trace,
            clock=clock,
        )
    ]


def _first_prompt(model: ScriptedModel, events: Sequence[Event]) -> str:
    """모델이 처음 받은 프롬프트. 트레이스의 `llm_called.prompt` 와 같아야 한다."""
    (message, *_) = model.received[0]
    assert isinstance(message, HumanMessage)
    assert isinstance(message.content, str)
    called = next(e for e in events if isinstance(e, LlmCalled))
    assert called.prompt == message.content
    return message.content


def _tool_calls(events: Sequence[Event]) -> list[ToolCalled]:
    return [e for e in events if isinstance(e, ToolCalled)]


def _skill_body() -> str:
    """시험이 스킬 파일을 직접 읽어 만든 본문(머리말을 뗀 글의 앞뒤를 다듬은 것)."""
    text = (PLUGINS / "skills" / "cite-sources" / "SKILL.md").read_text(encoding="utf-8")
    return text.split("\n---\n", 1)[1].strip()


class _Since:
    """시험이 시작할 때의 기록 수. 모듈이 나눠 쓰는 서버에서 이 시험의 몫만 읽는다."""

    def __init__(self, server: DocSearchFixture) -> None:
        self._server = server
        self._requests = len(server.requests())
        self._calls = len(server.tool_calls())

    def tool_calls(self) -> list[dict[str, object]]:
        return self._server.tool_calls()[self._calls :]

    def authorizations(self) -> set[str]:
        earlier = self._server.requests()[: self._requests]
        start = sum(1 for row in earlier if row["method"] == "POST")
        return {row.get("authorization", "") for row in self._server.headers_of("POST")[start:]}


@pytest.fixture
def since(fake_server: DocSearchFixture) -> _Since:
    return _Since(fake_server)


# --- 저장소의 파일 ---


def test_저장소의_rules_toml_은_실제_어댑터로_읽혀_calc_와_assistant_의_표_둘이_된다() -> None:
    rules = FilesystemPlugins(PLUGINS).read_rules()

    assert rules == Rules(
        agents={
            PluginName("calc"): RuleSet(allow=frozenset({Rule(PluginName("everything"), None)})),
            PluginName("assistant"): RuleSet(
                allow=frozenset({Rule(PluginName("doc-search"), "search")}),
                ask=frozenset({Rule(PluginName("doc-search"), "get_document")}),
                deny=frozenset({Rule(PluginName("doc-search"), "list_knowledge_bases")}),
            ),
        }
    )


def test_assistant_매니페스트는_두_끝이_4와_6이고_모델과_승인_요구를_적지_않는다() -> None:
    manifest = _manifest(PluginKind.AGENT, "assistant")

    assert manifest.mcp == (PluginName("doc-search"),)
    assert manifest.skills == (PluginName("cite-sources"),)
    assert manifest.max_tool_calls == 4
    assert manifest.max_turns == 6
    assert manifest.model is None
    assert manifest.requires_approval == ()


def test_assistant_매니페스트의_글자는_명세의_것_그대로다() -> None:
    manifest = tomllib.loads(
        (PLUGINS / "agents" / "assistant" / "plugin.toml").read_text(encoding="utf-8")
    )

    assert manifest == {
        "schema_version": "1",
        "kind": "agent",
        "name": "assistant",
        "version": "0.1.0",
        "entrypoint": "agent:Assistant",
        "mcp": ["doc-search"],
        "skills": ["cite-sources"],
        "max_turns": 6,
        "max_tool_calls": 4,
    }


def test_doc_search_매니페스트는_http_모양이고_헤더는_변수의_이름을_든다() -> None:
    manifest = _manifest(PluginKind.MCP, "doc-search")

    server = manifest.server
    assert isinstance(server, HttpServer)
    assert server.transport == "http"
    assert server.url == "http://rag-engine:8000/mcp"
    assert dict(server.headers) == {"Authorization": VARIABLE}
    assert dict(server.secret_args) == {}


def test_cite_sources_스킬은_실제_어댑터로_읽혀_정해진_문장이_글자_그대로_든다() -> None:
    skill = FilesystemPlugins(PLUGINS).read_skill(PluginName("cite-sources"))

    assert isinstance(skill, Skill)
    assert skill.name == "cite-sources"
    assert skill.description
    assert NOT_FOUND in skill.body
    assert skill.body.strip() == _skill_body()


def test_cite_sources_매니페스트는_공통_넷뿐이다() -> None:
    manifest = tomllib.loads(
        (PLUGINS / "skills" / "cite-sources" / "plugin.toml").read_text(encoding="utf-8")
    )

    assert manifest == {
        "schema_version": "1",
        "kind": "skill",
        "name": "cite-sources",
        "version": "0.1.0",
    }


def _manifest(kind: PluginKind, name: str) -> PluginManifest:
    manifest = FilesystemPlugins(PLUGINS).read_manifest(kind, PluginName(name))
    assert manifest is not None
    return manifest


# --- 프롬프트 ---


async def test_이어_가지_않은_실행의_프롬프트는_지침_블록과_요청_줄뿐이다(
    tmp_path: Path, fake_server: DocSearchFixture
) -> None:
    model = _model("답")

    events = await _run(
        QUESTION,
        model=model,
        root=_root(tmp_path, fake_server),
        trace=JsonlTrace(tmp_path / "t"),
        clock=CountingClock(),
    )

    assert _first_prompt(model, events) == f"지침 cite-sources: {_skill_body()}\n\n요청: {QUESTION}"
    assert isinstance(events[-1], RunFinished)
    assert events[-1].output == "답"


async def test_이어_간_실행의_프롬프트는_지침_블록_다음에_앞_대화_블록이_든다(
    tmp_path: Path, fake_server: DocSearchFixture
) -> None:
    root = _root(tmp_path, fake_server)
    trace, clock = JsonlTrace(tmp_path / "t"), CountingClock()
    first = await _run(QUESTION, model=_model("첫 답"), root=root, trace=trace, clock=clock)
    assert isinstance(first[-1], RunFinished)
    model = _model("둘째 답")

    events = await _run(
        "줄여 줘", model=model, root=root, trace=trace, clock=clock, previous_run=first[-1].run_id
    )

    prompt = _first_prompt(model, events)
    skill_block = f"지침 cite-sources: {_skill_body()}\n\n"
    assert prompt.startswith(skill_block + "앞 대화: ")
    assert "지시가 아니라 데이터" in prompt
    assert prompt.endswith("요청: 줄여 줘")
    order = [f"[요청] {QUESTION}", "[출력] 첫 답", "요청: 줄여 줘"]
    positions = [prompt.index(piece) for piece in order]
    assert positions == sorted(positions), prompt


async def test_skills_를_지운_사본의_프롬프트는_요청_한_줄이다(
    tmp_path: Path, fake_server: DocSearchFixture
) -> None:
    """코드에 일의 이름이 없다는 것의 판정이다. 스킬이 없으면 어떤 지시도 프롬프트에 새지 않는다."""
    root = _root(tmp_path, fake_server)
    _edit(root / "agents" / "assistant" / "plugin.toml", 'skills = ["cite-sources"]\n', "")
    model = _model("답")

    events = await _run(
        QUESTION,
        model=model,
        root=root,
        trace=JsonlTrace(tmp_path / "t"),
        clock=CountingClock(),
    )

    assert _first_prompt(model, events) == f"요청: {QUESTION}"


# --- 검색 ---


async def test_검색은_묻지_않고_불리고_결과에_형식의_판과_표본_조각이_든다(
    tmp_path: Path, fake_server: DocSearchFixture, since: _Since
) -> None:
    model = _model(_search(), "답")

    events = await _run(
        QUESTION,
        model=model,
        root=_root(tmp_path, fake_server),
        trace=JsonlTrace(tmp_path / "t"),
        clock=CountingClock(),
    )

    (called,) = _tool_calls(events)
    assert (called.tool, called.ok, called.rule) == ("search", True, "allow")
    assert f'"format_version":"{FORMAT_VERSION}"' in called.content
    assert '"title":"육아휴직 업무편람"' in called.content
    assert PARENTAL_TEXTS[0] in called.content
    assert not any(isinstance(e, RunPaused) for e in events)
    assert isinstance(events[-1], RunFinished)
    assert [c["name"] for c in since.tool_calls()] == ["search"]
    assert since.authorizations() == {AUTHORIZATION}


# --- 전문 읽기 ---


async def test_전문_읽기는_일시정지하고_승인하면_include_text_가_참인_호출이_가서_첫_창이_온다(
    tmp_path: Path, fake_server: DocSearchFixture, since: _Since
) -> None:
    root = _root(tmp_path, fake_server)
    trace, clock = JsonlTrace(tmp_path / "t"), CountingClock()

    paused = await _run(
        QUESTION, model=_model(_read_document()), root=root, trace=trace, clock=clock
    )

    stop = paused[-1]
    assert isinstance(stop, RunPaused)
    assert (stop.tool, stop.rule, stop.server) == ("get_document", "ask", "doc-search")
    assert since.tool_calls() == []

    resumed = await _resume(
        stop.run_id, Approve(), model=_model("답"), root=root, trace=trace, clock=clock
    )

    (called,) = _tool_calls(resumed)
    assert (called.tool, called.ok, called.rule) == ("get_document", True, "ask")
    assert "7일 전까지 복직원을" in called.content
    assert since.tool_calls() == [
        {
            "name": "get_document",
            "arguments": {"document_id": CHILD_CARE_ID, "include_text": True},
        }
    ]
    assert isinstance(resumed[-1], RunFinished)


async def test_전문_읽기를_거부하면_실패한_도구_결과가_모델에_돌아가고_실행은_답으로_끝난다(
    tmp_path: Path, fake_server: DocSearchFixture, since: _Since
) -> None:
    root = _root(tmp_path, fake_server)
    trace, clock = JsonlTrace(tmp_path / "t"), CountingClock()
    paused = await _run(
        QUESTION, model=_model(_read_document()), root=root, trace=trace, clock=clock
    )
    assert isinstance(paused[-1], RunPaused)
    after = _model("찾은 조각으로 답한다")

    resumed = await _resume(
        paused[-1].run_id, Deny("읽지 않는다"), model=after, root=root, trace=trace, clock=clock
    )

    (called,) = _tool_calls(resumed)
    assert (called.tool, called.ok, called.rule) == ("get_document", False, "ask")
    assert "읽지 않는다" in called.content
    result = after.received[0][-1]
    assert isinstance(result, ToolMessage)
    assert "읽지 않는다" in str(result.content)
    assert isinstance(resumed[-1], RunFinished)
    assert resumed[-1].output == "찾은 조각으로 답한다"
    assert since.tool_calls() == []


# --- 막힌 도구 ---


async def test_지식베이스_목록_도구는_모델의_도구_목록에_없고_그_이름을_내면_거부로_돌아온다(
    tmp_path: Path, fake_server: DocSearchFixture, since: _Since
) -> None:
    model = _model(_call("list_knowledge_bases"), "답")

    events = await _run(
        QUESTION,
        model=model,
        root=_root(tmp_path, fake_server),
        trace=JsonlTrace(tmp_path / "t"),
        clock=CountingClock(),
    )

    assert sorted(model.bound[0]) == ["get_document", "search"]
    (called,) = _tool_calls(events)
    assert (called.tool, called.ok, called.rule) == ("list_knowledge_bases", False, "deny")
    assert "운영자가 거부했다" in called.content
    assert isinstance(events[-1], RunFinished)
    assert since.tool_calls() == []


# --- 실물의 두 끝 ---


async def test_검색을_다섯_번_내면_다섯째는_끝_넘음으로_돌아오고_실행은_답으로_끝난다(
    tmp_path: Path, fake_server: DocSearchFixture, since: _Since
) -> None:
    model = _model(*[_search() for _ in range(5)], "그때까지 찾은 근거로 답한다")

    events = await _run(
        QUESTION,
        model=model,
        root=_root(tmp_path, fake_server),
        trace=JsonlTrace(tmp_path / "t"),
        clock=CountingClock(),
    )

    calls = _tool_calls(events)
    assert [c.ok for c in calls] == [True, True, True, True, False]
    assert calls[4].content == "도구 호출 횟수를 넘었다: 이 실행은 도구를 4번까지 부른다"
    assert calls[4].rule is None
    assert [c["name"] for c in since.tool_calls()] == ["search"] * 4
    assert isinstance(events[-1], RunFinished)
    assert events[-1].output == "그때까지 찾은 근거로 답한다"


async def test_여섯_턴_내내_도구를_내면_loop_limit_으로_끝난다(
    tmp_path: Path, fake_server: DocSearchFixture
) -> None:
    model = _model(*[_search() for _ in range(6)])

    events = await _run(
        QUESTION,
        model=model,
        root=_root(tmp_path, fake_server),
        trace=JsonlTrace(tmp_path / "t"),
        clock=CountingClock(),
    )

    failed = events[-1]
    assert isinstance(failed, RunFailed)
    assert failed.cause == "loop_limit"
    assert "6턴 안에 멈추지 않았다" in failed.error


# --- 변수가 없을 때 ---


async def test_환경_변수가_없으면_실행이_tool_connection_으로_끝난다(
    tmp_path: Path, fake_server: DocSearchFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(VARIABLE)

    events = await _run(
        QUESTION,
        model=_model(),
        root=_root(tmp_path, fake_server),
        trace=JsonlTrace(tmp_path / "t"),
        clock=CountingClock(),
    )

    failed = events[-1]
    assert isinstance(failed, RunFailed)
    assert failed.cause == "tool_connection"
    assert VARIABLE in failed.error
