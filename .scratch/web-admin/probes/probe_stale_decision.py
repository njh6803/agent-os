"""오래된 화면이 보낸 결정은 무엇에 닿나. ADR 0019 의 열린 물음의 전제를 잰다.

실제 JSONL 트레이스와 파일시스템 플러그인 위에 `create_app()` 을 세우고 httpx `ASGITransport` 로
민다. 모델과 도구만 가짜다. 한 턴에 승인 대상 호출이 둘인 에이전트가 X 에서 멈춘다. 화면 A 가
관리 API 로 X 를 읽는 동안 다른 곳(B)이 X 를 승인하고, 실행은 Y 에서 다시 멈춘다. 그다음 화면 A 가
X 를 보고 누른 승인을 보낸다.

두 경우를 잰다. `differ` 는 Y 의 인자가 X 와 다르고, `same` 은 같은 도구를 같은 인자로 두 번
부른다(도구와 인자로 묶어도 가려낼 수 없는 경우). 재는 것은 다섯이다.

1. 화면 A 의 결정에 대한 응답 코드와 스트림의 종류
2. 실제로 불린 도구 호출
3. `run_paused` 가 식별자를 드는가(이벤트의 필드)
4. 결정 본문의 계약(`openapi.json` 의 `Approve`·`Deny`)이 무엇을 받는가
5. 재개 스트림의 프레임이 트레이스에 새로 붙은 줄과 같은가(클라이언트가 트레이스의 길이를
   스트림만으로 따라갈 수 있는가)

`uv run python .scratch/web-admin/probes/probe_stale_decision.py`. 네트워크를 타지 않는다.
"""

import asyncio
import io
import json
import tempfile
from collections.abc import AsyncGenerator, Mapping, Sequence
from contextlib import asynccontextmanager
from pathlib import Path

from httpx import ASGITransport, AsyncClient
from langchain_core.language_models import LanguageModelInput
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.messages.tool import ToolCall
from langchain_core.runnables import Runnable

from agent_os.adapters.clock import SystemClock
from agent_os.adapters.filesystem import FilesystemPlugins
from agent_os.adapters.jsonl import JsonlTrace
from agent_os.core.ports import ToolConnection, ToolResult, ToolSpec
from agent_os.sdk import Json, McpServer, PluginName, Principal
from agent_os.server import create_app

ADMIN = {"Authorization": "Bearer admin-probe"}
CHANNEL = {"Authorization": "Bearer channel-probe"}

AGENT_TOML = """schema_version = "1"
kind = "agent"
name = "gated"
version = "0.1.0"
entrypoint = "agent:Agent"
mcp = ["calc"]
requires_approval = ["add"]
"""
AGENT_PY = """from agent_os.sdk import RunFinished


class Agent:
    async def run(self, request, ctx):
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=await ctx.llm(request))
"""
MCP_TOML = """schema_version = "1"
kind = "mcp"
name = "calc"
version = "0.1.0"

[server]
command = "never-started"
"""


class Connection:
    def __init__(self, calls: list[tuple[str, Mapping[str, Json]]]) -> None:
        self._calls = calls

    def tools(self) -> Sequence[ToolSpec]:
        schema: Mapping[str, Json] = {"type": "object", "properties": {"a": {}, "b": {}}}
        return [ToolSpec(name="add", description="더한다", input_schema=schema)]

    async def call(self, name: str, args: Mapping[str, Json]) -> ToolResult:
        self._calls.append((name, dict(args)))
        return ToolResult(ok=True, content="ok")


class Tools:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Mapping[str, Json]]] = []

    @asynccontextmanager
    async def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AsyncGenerator[ToolConnection]:
        yield Connection(self.calls)


class Model(GenericFakeChatModel):
    def bind_tools(
        self, tools: Sequence[object], *, tool_choice: str | None = None, **kwargs: object
    ) -> Runnable[LanguageModelInput, AIMessage]:
        return self


def _plugins(root: Path) -> None:
    agent = root / "agents" / "gated"
    agent.mkdir(parents=True)
    (agent / "plugin.toml").write_text(AGENT_TOML, encoding="utf-8")
    (agent / "agent.py").write_text(AGENT_PY, encoding="utf-8")
    mcp = root / "mcp" / "calc"
    mcp.mkdir(parents=True)
    (mcp / "plugin.toml").write_text(MCP_TOML, encoding="utf-8")


def _frames(text: str) -> list[dict[str, Json]]:
    blocks = [b for b in text.split("\n\n") if b and not b.startswith(":")]
    return [json.loads(b.removeprefix("data: ")) for b in blocks]


def _trace_lines(traces: Path, run_id: str) -> list[str]:
    # 첫 줄은 형식 머리다(`TraceHeader`). 이벤트 줄만 센다.
    return (traces / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()[1:]


async def case(label: str, x: Mapping[str, Json], y: Mapping[str, Json]) -> None:
    work = Path(tempfile.mkdtemp())
    _plugins(work / "plugins")
    traces = work / "traces"
    tools = Tools()
    turn = AIMessage(
        content="",
        tool_calls=[
            ToolCall(name="add", args=dict(x), id="c1"),
            ToolCall(name="add", args=dict(y), id="c2"),
        ],
    )
    app = create_app(
        plugins=FilesystemPlugins(work / "plugins"),
        trace=JsonlTrace(traces),
        model=Model(messages=iter([turn, AIMessage(content="끝")])),
        tools=tools,
        clock=SystemClock(),
        principal=Principal("probe"),
        admin_token="admin-probe",
        channel_token="channel-probe",
        stderr=io.StringIO(),
    )
    transport = ASGITransport(app=app)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=transport, base_url="http://probe.test") as client,
    ):
        started = await client.post(
            "/runs", json={"agent": "gated", "request": "?"}, headers=CHANNEL
        )
        run_id = str(_frames(started.text)[0]["run_id"])

        # 화면 A 가 관리 API 로 멈춘 실행을 읽는다. 마지막 이벤트가 X 다.
        seen = (await client.get(f"/traces/{run_id}", headers=ADMIN)).json()
        shown = seen["events"][-1]
        shown_at = len(seen["events"]) - 1

        # 다른 곳(B)이 X 를 승인한다. 실행은 Y 에서 다시 멈춘다.
        before_b = len(_trace_lines(traces, run_id))
        b = await client.post(
            f"/runs/{run_id}/approval", json={"decision": "approve"}, headers=CHANNEL
        )
        b_frames = _frames(b.text)
        after_b = _trace_lines(traces, run_id)

        # 화면 A 가 X 를 보고 누른 승인을 보낸다.
        a = await client.post(
            f"/runs/{run_id}/approval", json={"decision": "approve"}, headers=CHANNEL
        )
        a_frames = _frames(a.text)

        final = (await client.get(f"/traces/{run_id}", headers=ADMIN)).json()["events"]

    pauses = [(i, e) for i, e in enumerate(final) if e["type"] == "run_paused"]
    print(f"== {label}: X={dict(x)} Y={dict(y)}")
    print(f"  화면 A 가 본 일시정지: 자리 {shown_at}, 도구 {shown['tool']} {shown['args']}")
    print(f"  B 의 결정: {b.status_code} {[f['type'] for f in b_frames]}")
    print(f"  B 뒤 마지막 이벤트: {b_frames[-1]['type']} {b_frames[-1].get('args')}")
    print(f"  화면 A 의 결정: {a.status_code} {[f['type'] for f in a_frames]}")
    print(f"  실제로 불린 도구: {tools.calls}")
    print(f"  트레이스의 일시정지: {[(i, e['tool'], e['args']) for i, e in pauses]}")
    print(f"  run_paused 의 필드: {sorted(pauses[0][1])}")
    appended = [json.loads(line) for line in after_b[before_b:]]
    print(f"  B 의 재개 스트림 == 트레이스에 새로 붙은 줄: {b_frames == appended}")


def contract() -> None:
    schemas = json.loads(Path("openapi.json").read_text(encoding="utf-8"))["components"]["schemas"]
    for name in ("Approve", "Deny"):
        print(
            f"== 계약 {name}: required={schemas[name].get('required')} "
            f"properties={sorted(schemas[name]['properties'])}"
        )


async def main() -> None:
    await case("differ", {"a": 2, "b": 3}, {"a": 4, "b": 5})
    await case("same", {"a": 2, "b": 3}, {"a": 2, "b": 3})
    contract()


if __name__ == "__main__":
    asyncio.run(main())
