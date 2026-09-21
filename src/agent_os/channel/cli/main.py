"""CLI 채널. 실행을 요청하는 명령(run)이 여기에 붙는다.

표준 출력은 실행의 결말만 싣는다. 끝나면 출력 문자열, 멈추면 실행 식별자와 승인 요청(도구 이름과
인자. 마스킹된 인자는 마스킹된 채로). 표준 에러는 둘을 싣고 규칙이 다르다. 실패 진단은 언제나
나가고, 진행 이벤트는 progress 스트림이 주어졌을 때만 한 줄에 JSON 하나로 나간다(트레이스와 같은
직렬화). 종료 코드는 성공 0, 실패 1, 일시정지 3. 일시정지가 전용 코드인 이유는 성공도 실패도
아니라는 것을 스크립트가 알아야 하기 때문이다(ADR 0009). 2 는 argparse 가 인자 오류에 쓴다.
어댑터는 main.py 가 만들어 넘기고 채널은 표시만 결정한다.
"""

from __future__ import annotations

import argparse
import json
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
    TraceStore,
)
from agent_os.core.run import run
from agent_os.sdk import AgentName, Event, Principal, RunFailed, RunFinished, RunPaused

DEFAULT_TRACES = Path("traces")
EXIT_FINISHED = 0
EXIT_FAILED = 1
EXIT_PAUSED = 3


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
    trace: TraceStore,
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
        return EXIT_FAILED


async def _show(
    events: AsyncIterator[Event], *, stdout: TextIO, stderr: TextIO, progress: TextIO | None
) -> int:
    """마지막 종료 이벤트가 종료 코드를 정한다. 종료 이벤트가 없으면 실패다."""
    exit_code = EXIT_FAILED
    async for event in events:
        if progress is not None:
            progress.write(event.model_dump_json() + "\n")
        if isinstance(event, RunFinished):
            stdout.write(event.output + "\n")
            exit_code = EXIT_FINISHED
        elif isinstance(event, RunPaused):
            stdout.write(_approval_request(event))
            exit_code = EXIT_PAUSED
        elif isinstance(event, RunFailed):
            stderr.write(f"실행 실패: {event.error}\n")
            exit_code = EXIT_FAILED
    return exit_code


def _approval_request(event: RunPaused) -> str:
    """승인자가 보는 것. 무엇을 승인하는지 모르고 승인하지 않게 도구와 인자를 그대로 보인다."""
    args = json.dumps(event.args, ensure_ascii=False)
    return f"일시정지: {event.run_id}\n도구: {event.tool}\n인자: {args}\n"
