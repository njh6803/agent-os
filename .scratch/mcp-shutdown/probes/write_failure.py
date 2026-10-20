"""core `run()`에 진짜 MCP 어댑터를 물려, 연결이 열린 채 트레이스 쓰기가 실패한 실행이 어떻게
끝나는지 잰다(소비 지점까지).

지금 폴더의 트리를 쓴다. `agent_os`는 그 트리의 환경에서, 픽스처 서버는 그 트리의
`tests/adapters/mcp_fixture_server.py`에서 온다. 저장소에서 `uv run`으로 돌리면 지금
판(langchain-mcp-adapters, mcp 1.30.0)을, `full_stack.py`가 만든 사본에서 돌리면 시제품 어댑터(mcp
2.3.0)를 잰다. 에이전트는 도구를 직접 부른 뒤 끝나거나 예외를 낸다. 가짜 포트는
플러그인·트레이스·시계·모델이고 도구 포트만 진짜다.

사례:
- `write_2`: 둘째 쓰기(`tool_called`)만 실패한다. 실패는 연결 안의 yield 에서 나고, 런타임은
  `run_failed`를 쓴 뒤 연결 안에 멈춘 제너레이터를 닫는다(`core/run.py`의 `_drive`).
- `write_3`: 셋째 쓰기(`run_finished`)만 실패한다.
- `raise`: 에이전트가 도구 `add`를 부른 뒤 예외를 낸다. 쓰기는 실패하지 않는다.
- `tool_error`: 에이전트가 도구 `fail`을 부르고, 런타임이 그 실패로 낸 `ToolError`를 잡지 않는다.
  쓰기는 실패하지 않는다.

표지: 도구가 실제로 불렸고(쓰기 시도에 `tool_called`가 있다) 쓰기 사례는 실패시키려던 차례에 그
이벤트의 쓰기를 시도했다. 표지가 없는 사례는 측정이 아니고 종료 코드는 2다. 판정(`--expect`)은 모든
사례가 `run_failed`로 끝나는 것을 먼저 본다. 쓰기 사례는 그 글이 쓰기의 실패이고 원인이 그 밖이다.
그리고 `closed`는 `run()` 밖으로 예외가 나오지 않는 것, `escaped`는 `run()` 밖으로 `GeneratorExit`를
든 `BaseExceptionGroup`이 나오는 것이다. 예외 사례는 둘 다에서 `run()` 밖으로 예외가 나오지 않고,
`run_failed`의 글이 그 예외 하나이며 원인이 던진 자리(`raise`는 에이전트 코드, `tool_error`는 도구
실패)인 것이다. 어긋나면 종료 코드 1이다. 돌리는 명령은 `README.md`에 있다.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from pathlib import Path

import anyio
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

from agent_os.adapters.mcp import McpTools
from agent_os.core.ports import (
    Cursor,
    ManifestRow,
    PluginKey,
    PluginSource,
    RunRow,
    RunStatus,
    Trace,
    TraceStore,
    WriteOutcome,
)
from agent_os.core.run import run
from agent_os.sdk import (
    AgentContext,
    AgentName,
    BaseAgent,
    Event,
    PluginKind,
    PluginManifest,
    PluginName,
    Principal,
    RunFailed,
    RunFinished,
    RunId,
    ToolError,
    parse_manifest,
)

FIXTURE = Path.cwd() / "tests" / "adapters" / "mcp_fixture_server.py"
AGENT_ERROR = "에이전트가 낸 예외"
TOOL_ERROR = "도구가 낸 실패"
DISK_FULL = "디스크가 가득 찼다"
# 쓰기 사례마다 실패시킬 쓰기의 차례(1부터)와 그 쓰기의 이벤트.
WRITES: dict[str, tuple[int, str]] = {"write_2": (2, "tool_called"), "write_3": (3, "run_finished")}
# 예외 사례마다 `run_failed`의 글 머리, 글에 든 문구, 원인.
RAISES: dict[str, tuple[str, str, str]] = {
    "raise": ("ValueError: ", AGENT_ERROR, "agent_code"),
    "tool_error": ("ToolError: ", TOOL_ERROR, "tool_failure"),
}
CASES = (*WRITES, *RAISES)


class Agent:
    def __init__(self, case: str) -> None:
        self._case = case

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        if self._case == "tool_error":
            await ctx.tool("fail", reason=TOOL_ERROR)
        try:
            output = await ctx.tool("add", a=2, b=2)
        except ToolError as error:
            output = f"error:{error}"
        if self._case == "raise":
            raise ValueError(f"{AGENT_ERROR}, 도구 결과 {output}")
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=output)


class Plugins:
    def __init__(self, agent: BaseAgent) -> None:
        self._agent = agent

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None:
        if kind is PluginKind.AGENT:
            return parse_manifest(
                'schema_version = "1"\nkind = "agent"\nname = "calc"\nversion = "0.1.0"\n'
                'entrypoint = "agent:Agent"\nmcp = ["fixture"]\nrequires_approval = []\n'
            )
        command = Path(sys.executable).as_posix()
        return parse_manifest(
            'schema_version = "1"\nkind = "mcp"\nname = "fixture"\nversion = "0.1.0"\n'
            f'[server]\ncommand = "{command}"\nargs = ["{FIXTURE.as_posix()}"]\n'
        )

    def list_manifests(self, kind: PluginKind) -> tuple[ManifestRow, ...]:
        raise NotImplementedError

    def load_agent(self, manifest: PluginManifest) -> BaseAgent:
        return self._agent

    def read_disabled(self) -> frozenset[PluginKey]:
        return frozenset()

    def write_enabled(self, kind: PluginKind, name: PluginName, *, enabled: bool) -> WriteOutcome:
        raise NotImplementedError


class FailingTrace:
    """`failing` 번째 쓰기만 실패한다. 디스크가 잠깐 가득 찼던 것과 같다."""

    def __init__(self, failing: int | None) -> None:
        self.events: list[Event] = []
        self.attempts: list[str] = []
        self._failing = failing

    def write(self, event: Event) -> None:
        self.attempts.append(event.type)
        if len(self.attempts) == self._failing:
            raise OSError(f"트레이스를 쓸 수 없다: {DISK_FULL}")
        self.events.append(event)

    def read(self, run_id: RunId) -> Trace | None:
        return None

    def list(
        self,
        *,
        status: RunStatus | None = None,
        limit: int | None = None,
        after: Cursor | None = None,
    ) -> tuple[RunRow, ...]:
        raise NotImplementedError


class Clock:
    def now(self) -> datetime:
        return datetime(2026, 10, 20, tzinfo=UTC)

    def new_run_id(self) -> RunId:
        return RunId("run-1")


async def _case(name: str) -> dict[str, object]:
    write = WRITES.get(name)
    trace = FailingTrace(None if write is None else write[0])
    store: TraceStore = trace
    plugins: PluginSource = Plugins(Agent(name))
    yielded: list[str] = []
    escaped: BaseException | None = None
    try:
        async for event in run(
            AgentName("calc"),
            "2+2?",
            Principal("alice"),
            plugins=plugins,
            model=GenericFakeChatModel(messages=iter(())),
            tools=McpTools(),
            trace=store,
            clock=Clock(),
        ):
            yielded.append(event.type)
    except BaseException as error:
        escaped = error
    last = trace.events[-1] if trace.events else None
    return {
        "case": name,
        "measured": "tool_called" in trace.attempts and _failed_the_write(write, trace.attempts),
        "attempts": trace.attempts,
        "written": [event.type for event in trace.events],
        "yielded": yielded,
        "failed": last.error if isinstance(last, RunFailed) else None,
        "cause": last.cause if isinstance(last, RunFailed) else None,
        "escaped": None if escaped is None else type(escaped).__name__,
        "escaped_repr": None if escaped is None else repr(escaped)[:300],
    }


def _failed_the_write(write: tuple[int, str] | None, attempts: list[str]) -> bool:
    """쓰기 사례가 실패시키려던 차례에 그 이벤트의 쓰기를 시도했는가. 예외 사례는 늘 참이다."""
    if write is None:
        return True
    turn, event = write
    return len(attempts) >= turn and attempts[turn - 1] == event


def _as_expected(record: dict[str, object], expect: str) -> bool:
    failed = str(record["failed"])
    ended_failed = record["written"] == record["yielded"] and record["failed"] is not None
    raised = RAISES.get(str(record["case"]))
    if raised is not None:
        head, words, cause = raised
        return (
            ended_failed
            and record["escaped"] is None
            and failed.startswith(head)
            and words in failed
            and record["cause"] == cause
        )
    write_failed = ended_failed and DISK_FULL in failed and record["cause"] == "other"
    if expect == "closed":
        return write_failed and record["escaped"] is None
    return (
        write_failed
        and record["escaped"] == "BaseExceptionGroup"
        and "GeneratorExit" in str(record["escaped_repr"])
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--expect", choices=("closed", "escaped"), required=True)
    options = parser.parse_args()
    unmeasured: list[str] = []
    unexpected: list[str] = []
    for name in CASES:
        record = anyio.run(_case, name)
        record["as_expected"] = _as_expected(record, options.expect)
        print(json.dumps(record, ensure_ascii=False))
        if not record["measured"]:
            unmeasured.append(name)
        elif not record["as_expected"]:
            unexpected.append(name)
    print(json.dumps({"unmeasured": unmeasured, "unexpected": unexpected}, ensure_ascii=False))
    if unmeasured:
        return 2
    return 1 if unexpected else 0


if __name__ == "__main__":
    sys.exit(main())
