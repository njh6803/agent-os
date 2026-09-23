"""CLI 채널. 실행을 일으키는 명령 둘, run 과 resume 이 여기에 붙는다.

serve 는 실행을 일으키지 않아 명령 자체가 여기 없고 인자만 여기서 갈린다. 관리 API 를 세우는
것은 조립이라 `main.py` 의 일이고, 채널은 `server` 를 import 할 수 없다(원칙 IV). 그래서 serve 는
모델도 진행 표시도 받지 않는다 — 받을 자리가 없는 것이 곧 그 사실이다.

표준 출력은 실행의 결말만 싣는다. 끝나면 출력 문자열, 멈추면 실행 식별자와 승인 요청(도구 이름과
인자. 마스킹된 인자는 마스킹된 채로)과 그 실행을 잇는 명령 둘(승인, 사유를 붙이는 거부). 표준
에러는 둘을 싣고 규칙이 다르다.
실패 진단은 언제나 나가고, 진행 이벤트는 progress 스트림이 주어졌을 때만 한 줄에 JSON 하나로
나간다(트레이스와 같은 직렬화). 종료 코드는 성공 0, 실패 1, 일시정지 3. 일시정지가 전용 코드인
이유는 성공도 실패도 아니라는 것을 스크립트가 알아야 하기 때문이다(ADR 0009). 2 는 argparse 가
인자 오류에 쓴다. 어댑터는 main.py 가 만들어 넘기고 채널은 표시만 결정한다.

멈춘 실행의 목록 조회는 만들지 않는다. 채널은 실행을 일으키는 면이고 관찰은 관리의 일이다.
재개는 실행 식별자 하나만 받는다. 에이전트도 요청도 주체도 트레이스가 안다.
"""

from __future__ import annotations

import argparse
import json
import shlex
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
from agent_os.core.run import Approve, Decision, Deny, resume, run
from agent_os.sdk import AgentName, Event, Principal, RunFailed, RunFinished, RunId, RunPaused

DEFAULT_TRACES = Path("traces")
DEFAULT_PLUGINS_ROOT = Path("plugins")
# 루프백만 받는 규칙은 main.py 가 판정한다(ADR 0011). 여기는 그 규칙 안의 기본값 하나다.
DEFAULT_HOST = "127.0.0.1"
# uvicorn 자신의 기본값이라 직접 띄울 때와 같은 포트다(ADR 0010 의 2026-09-23 이력).
DEFAULT_PORT = 8000
EXIT_FINISHED = 0
EXIT_FAILED = 1
EXIT_PAUSED = 3


@dataclass(frozen=True)
class RunArgs:
    agent: AgentName
    request: str
    model: str | None
    traces: Path
    plugins_root: Path
    verbose: bool


@dataclass(frozen=True)
class ResumeArgs:
    run_id: RunId
    decision: Decision
    model: str | None
    traces: Path
    plugins_root: Path
    verbose: bool


@dataclass(frozen=True)
class ServeArgs:
    """관리 API 를 세우는 데 필요한 값 넷. 비밀은 없다 — 토큰만 환경변수로 온다(ADR 0011)."""

    host: str
    port: int
    traces: Path
    plugins_root: Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="agent-os", description="플러그인 기반 에이전트 런타임")
    parser.add_argument("--version", action="version", version=version("agent-os"))
    commands = parser.add_subparsers(dest="command", required=True)
    run_parser = commands.add_parser("run", help="에이전트에 요청 하나를 던진다")
    run_parser.add_argument("agent", help="plugins/agents/ 아래 에이전트 이름")
    run_parser.add_argument("request", help="요청 문자열")
    _add_shared(run_parser)
    resume_parser = commands.add_parser("resume", help="일시정지한 실행을 이어 간다")
    resume_parser.add_argument("run_id", help="멈출 때 표준 출력에 찍힌 실행 식별자")
    # 승인과 거부 중 하나를 반드시 골라야 한다. 거부의 사유 필수는 argparse 로 표현되지 않아
    # _decision 이 본다.
    decision = resume_parser.add_mutually_exclusive_group(required=True)
    decision.add_argument("--approve", action="store_true", help="이 도구 호출을 승인한다")
    decision.add_argument(
        "--deny", action="store_true", help="이 도구 호출을 거부한다. --reason 이 필수다"
    )
    resume_parser.add_argument(
        "--reason", help="거부 사유. 실패한 도구 결과로 모델에게 돌아가고 트레이스에 남는다"
    )
    _add_shared(resume_parser)
    serve_parser = commands.add_parser("serve", help="관리 API 를 루프백에 세운다")
    serve_parser.add_argument(
        "--host", default=DEFAULT_HOST, help=f"바인딩 주소. 루프백만 (기본 {DEFAULT_HOST})"
    )
    serve_parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"바인딩 포트 (기본 {DEFAULT_PORT})"
    )
    _add_directories(serve_parser)
    return parser


def _add_shared(parser: argparse.ArgumentParser) -> None:
    """두 명령이 같이 받는 것. 재개도 재생 뒤 실제로 이어 가므로 모델이 필요하다."""
    parser.add_argument("--model", help="모델 이름. 없으면 AGENT_OS_MODEL, 그다음 기본값")
    parser.add_argument("--verbose", action="store_true", help="진행 이벤트를 표준 에러로")
    _add_directories(parser)


def _add_directories(parser: argparse.ArgumentParser) -> None:
    """명령 셋이 같이 받는 것. 읽고 쓰는 디렉터리가 작업 디렉터리에 묶이지 않게 한다."""
    parser.add_argument(
        "--traces", type=Path, default=DEFAULT_TRACES, help="트레이스 디렉터리 (기본 traces/)"
    )
    parser.add_argument(
        "--plugins-root",
        type=Path,
        default=DEFAULT_PLUGINS_ROOT,
        help="플러그인 디렉터리 (기본 plugins/)",
    )


def parse_args(argv: list[str] | None) -> RunArgs | ResumeArgs | ServeArgs:
    parser = build_parser()
    namespace = parser.parse_args(argv)
    traces = Path(namespace.traces)
    plugins_root = Path(namespace.plugins_root)
    if namespace.command == "serve":
        return ServeArgs(
            host=str(namespace.host),
            port=int(namespace.port),
            traces=traces,
            plugins_root=plugins_root,
        )
    model = None if namespace.model is None else str(namespace.model)
    verbose = bool(namespace.verbose)
    if namespace.command == "resume":
        return ResumeArgs(
            run_id=RunId(str(namespace.run_id)),
            decision=_decision(parser, namespace),
            model=model,
            traces=traces,
            plugins_root=plugins_root,
            verbose=verbose,
        )
    return RunArgs(
        agent=AgentName(str(namespace.agent)),
        request=str(namespace.request),
        model=model,
        traces=traces,
        plugins_root=plugins_root,
        verbose=verbose,
    )


def _decision(parser: argparse.ArgumentParser, namespace: argparse.Namespace) -> Decision:
    """고른 플래그를 core 가 받는 결정으로 바꾼다. 어긋난 조합은 인자 오류(종료 코드 2)다.

    거부에는 사유가 필수다. ApprovalDenied.reason 이 필수 필드라 여기서 빈 문자열을 지어내면
    사유 없는 거부가 기본값으로 굳는다(ADR 0009). 공백만 있는 사유도 없는 것으로 본다. 반대로
    승인에는 사유를 담을 자리가 없어, 조용히 버리는 대신 거부한다. 승인자가 적은 말이 어디에도
    남지 않는 것을 막기 위해서다.

    상호배타 그룹이 하나를 반드시 고르게 하므로 마지막 줄은 도달하지 않는다. 그래도 두는 것은
    플래그가 늘 때 여기를 고치지 않으면 거부가 조용히 승인으로 도는 것을 타입이 잡아 주지 않기
    때문이다.
    """
    reason = None if namespace.reason is None else str(namespace.reason).strip()
    if bool(namespace.deny):
        if not reason:
            parser.error("거부에는 --reason 으로 사유를 붙여야 한다")
        return Deny(reason=reason)
    if bool(namespace.approve):
        if reason is not None:
            parser.error("--reason 은 거부(--deny)에만 쓴다. 승인에는 사유를 담을 자리가 없다")
        return Approve()
    parser.error("승인과 거부 중 하나를 골라야 한다")


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
    traces: Path,
    plugins_root: Path,
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
    return await _report(
        events,
        stdout=stdout,
        stderr=stderr,
        progress=progress,
        traces=traces,
        plugins_root=plugins_root,
    )


async def resume_command(
    run_id: RunId,
    decision: Decision,
    approver: Principal,
    *,
    plugins: PluginSource,
    model: ChatModel,
    tools: ToolSource,
    trace: TraceStore,
    clock: Clock,
    stdout: TextIO,
    stderr: TextIO,
    progress: TextIO | None,
    traces: Path,
    plugins_root: Path,
) -> int:
    """재개할 수 없는 실행(없음, 형식 1, 일시정지 아님, 손상)은 PluginError 로 진단만 적는다."""
    events = resume(
        run_id,
        decision,
        approver,
        plugins=plugins,
        model=model,
        tools=tools,
        trace=trace,
        clock=clock,
    )
    return await _report(
        events,
        stdout=stdout,
        stderr=stderr,
        progress=progress,
        traces=traces,
        plugins_root=plugins_root,
    )


async def _report(
    events: AsyncIterator[Event],
    *,
    stdout: TextIO,
    stderr: TextIO,
    progress: TextIO | None,
    traces: Path,
    plugins_root: Path,
) -> int:
    try:
        return await _show(
            events,
            stdout=stdout,
            stderr=stderr,
            progress=progress,
            traces=traces,
            plugins_root=plugins_root,
        )
    except PluginError as error:
        stderr.write(f"{error}\n")
        return EXIT_FAILED


async def _show(
    events: AsyncIterator[Event],
    *,
    stdout: TextIO,
    stderr: TextIO,
    progress: TextIO | None,
    traces: Path,
    plugins_root: Path,
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
            stdout.write(_approval_request(event, traces, plugins_root))
            exit_code = EXIT_PAUSED
        elif isinstance(event, RunFailed):
            stderr.write(f"실행 실패: {event.error}\n")
            exit_code = EXIT_FAILED
    return exit_code


def _approval_request(event: RunPaused, traces: Path, plugins_root: Path) -> str:
    """승인자가 보는 것. 무엇을 승인하는지 모르고 승인하지 않게 도구와 인자를 그대로 보인다.

    안내하는 명령은 그대로 복사해 쓸 수 있어야 한다. 거부 줄은 `--reason` 에서 끝나 사유를 이어
    적게 한다. 자리표시자를 두면 그대로 친 것이 진짜 사유로 기록되어, 사유 없는 거부를 막자는
    규칙이 안내 줄로 우회된다.
    """
    args = json.dumps(event.args, ensure_ascii=False)
    options = _inherited_options(traces, plugins_root)
    return (
        f"일시정지: {event.run_id}\n"
        f"도구: {event.tool}\n"
        f"인자: {args}\n"
        f"승인: agent-os resume {event.run_id}{options} --approve\n"
        f"거부: agent-os resume {event.run_id}{options} --deny --reason\n"
    )


def _inherited_options(traces: Path, plugins_root: Path) -> str:
    """재개가 같은 디렉터리를 읽도록 기본값에서 벗어난 것만 붙인다. 기본이면 군더더기다.

    디렉터리를 옮겨 실행했으면 재개도 거기서 읽어야 한다. 트레이스만 물려주고 플러그인 루트를
    빠뜨리면 안내한 명령이 에이전트를 못 찾아 그대로 실패한다 — 안내가 작동하지 않으면 안내가
    아니다. 디렉터리 옵션이 늘면 여기 한 줄이 는다.
    """
    directories = (
        (traces, DEFAULT_TRACES, "--traces"),
        (plugins_root, DEFAULT_PLUGINS_ROOT, "--plugins-root"),
    )
    return "".join(
        f" {flag} {_as_argument(chosen)}"
        for chosen, default, flag in directories
        if chosen != default
    )


def _as_argument(path: Path) -> str:
    """셸이 한 인자로 읽도록 인용한다. 공백뿐 아니라 `$` 와 따옴표도 그대로 전달돼야 한다.

    직접 큰따옴표를 씌우면 그 안에서 셸이 `$` 와 백틱을 여전히 해석해, 안내한 명령이 다른
    디렉터리를 읽게 된다. 이 함수가 고치려던 실패와 같은 모양이다. 테스트가 `shlex.split` 으로
    되읽으므로 둘이 서로의 역이다.
    """
    return shlex.quote(str(path))
