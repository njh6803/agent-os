"""CLI 채널. 실행을 요청하는 명령(run)이 여기에 붙는다.

표준 출력은 출력 문자열만 싣는다. 표준 에러는 둘을 싣고 규칙이 다르다. 실패 진단은 언제나 나가고,
진행 이벤트는 progress 스트림이 주어졌을 때만 한 줄에 JSON 하나로 나간다(트레이스와 같은 직렬화).
종료 코드는 성공 0, 실패 1. 어댑터는 main.py 가 만들어 넘기고 채널은 표시만 결정한다.
"""

from __future__ import annotations

import argparse
from collections.abc import AsyncIterator
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path
from typing import TextIO

from agent_os.core.ports import (
    ChatModel,
    Clock,
    PluginError,
    PluginSource,
    ToolSource,
    TraceSink,
)
from agent_os.core.run import run
from agent_os.sdk import AgentName, Event, Principal, RunFailed, RunFinished

DEFAULT_TRACES = Path("traces")


@dataclass(frozen=True)
class RunArgs:
    agent: AgentName
    request: str
    model: str | None
    traces: Path
    verbose: bool


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-os", description="플러그인 기반 에이전트 런타임")
    parser.add_argument("--version", action="version", version=version("agent-os"))
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run", help="에이전트에 요청 하나를 던진다")
    run_parser.add_argument("agent", help="plugins/agents/ 아래 에이전트 이름")
    run_parser.add_argument("request", help="요청 문자열")
    run_parser.add_argument("--model", help="모델 이름. 없으면 AGENT_OS_MODEL, 그다음 기본값")
    run_parser.add_argument("--verbose", action="store_true", help="진행 이벤트를 표준 에러로")
    run_parser.add_argument(
        "--traces", type=Path, default=DEFAULT_TRACES, help="트레이스 디렉터리 (기본 traces/)"
    )
    return parser


def parse_run_args(argv: list[str] | None) -> RunArgs:
    namespace = build_parser().parse_args(argv)
    return RunArgs(
        agent=AgentName(str(namespace.agent)),
        request=str(namespace.request),
        model=None if namespace.model is None else str(namespace.model),
        traces=Path(namespace.traces),
        verbose=bool(namespace.verbose),
    )


async def run_command(
    agent: AgentName,
    request: str,
    principal: Principal,
    *,
    plugins: PluginSource,
    model: ChatModel,
    tools: ToolSource,
    trace: TraceSink,
    clock: Clock,
    stdout: TextIO,
    stderr: TextIO,
    progress: TextIO | None,
) -> int:
    """종료 코드를 돌려준다. 실행 전 오류(PluginError)는 트레이스 없이 진단만 적는다."""
    events = run(
        agent,
        request,
        principal,
        plugins=plugins,
        model=model,
        tools=tools,
        trace=trace,
        clock=clock,
    )
    try:
        return await _show(events, stdout=stdout, stderr=stderr, progress=progress)
    except PluginError as error:
        stderr.write(f"{error}\n")
        return 1


async def _show(
    events: AsyncIterator[Event], *, stdout: TextIO, stderr: TextIO, progress: TextIO | None
) -> int:
    """마지막 종료 이벤트가 종료 코드를 정한다. 종료 이벤트가 없으면 실패다."""
    exit_code = 1
    async for event in events:
        if progress is not None:
            progress.write(event.model_dump_json() + "\n")
        if isinstance(event, RunFinished):
            stdout.write(event.output + "\n")
            exit_code = 0
        elif isinstance(event, RunFailed):
            stderr.write(f"실행 실패: {event.error}\n")
            exit_code = 1
    return exit_code
