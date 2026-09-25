"""agent-os 명령의 진입점. 조합 층.

채널, 관리, 어댑터를 조립해 넘기는 유일한 자리다. 슬라이스 2에서 `serve`가
`agent_os.server`를 부른다.
"""

from __future__ import annotations

import asyncio
import getpass
import io
import os
import sys
from typing import TextIO

import uvicorn

from agent_os.adapters.anthropic import anthropic_chat_model, resolve_model_name
from agent_os.adapters.clock import SystemClock
from agent_os.adapters.filesystem import FilesystemPlugins
from agent_os.adapters.jsonl import JsonlTrace
from agent_os.adapters.mcp import McpTools
from agent_os.channel.cli.main import (
    EXIT_FAILED,
    EXIT_FINISHED,
    ResumeArgs,
    RunArgs,
    ServeArgs,
    parse_args,
    resume_command,
    run_command,
)
from agent_os.core.ports import ChatModel
from agent_os.sdk import Principal
from agent_os.server import create_app

# 토큰은 환경변수로만 들어온다(ADR 0011, ADR 0015). 명령줄 인자는 프로세스 목록과 셸 이력에 남는다.
ADMIN_TOKEN_ENV = "AGENT_OS_ADMIN_TOKEN"
CHANNEL_TOKEN_ENV = "AGENT_OS_CHANNEL_TOKEN"
# 바인딩을 허용하는 주소 전부. 자라면 ADR 0011 의 이력에 쌓는다. 집합이 아니라 열인 이유는
# 진단에 그대로 실려서, 순서가 실행마다 달라지면 운영자가 읽는 문장이 달라지기 때문이다.
LOOPBACK_HOSTS = ("127.0.0.1", "::1")

_NO_ADMIN_TOKEN_DIAGNOSTIC = (
    f"{ADMIN_TOKEN_ENV} 가 비어 있다. 관리 API 는 토큰 없이 서지 않는다(ADR 0011).\n"
    f"  인증 없는 서버를 띄워 놓고 401 만 보게 되는 것을 막으려고 시작 자리에서 끝낸다.\n"
    f"  값을 정해 {ADMIN_TOKEN_ENV} 로 넘긴 뒤 다시 친다."
)
_NO_CHANNEL_TOKEN_DIAGNOSTIC = (
    f"{CHANNEL_TOKEN_ENV} 가 비어 있다. 채널도 토큰 없이 서지 않는다(ADR 0015).\n"
    f"  채널만 조용히 끄고 관리만 세우지 않으려고 시작 자리에서 끝낸다.\n"
    f"  관리 토큰과 다른 값을 정해 {CHANNEL_TOKEN_ENV} 로 넘긴 뒤 다시 친다."
)
_SAME_TOKENS_DIAGNOSTIC = (
    f"{ADMIN_TOKEN_ENV} 와 {CHANNEL_TOKEN_ENV} 가 같다. 두 토큰은 서로 달라야 한다(ADR 0015).\n"
    f"  같으면 트레이스를 읽는 권한이 실행을 일으키는 권한이 되고, 요청 시점에는 그것을 알아챌\n"
    f"  길이 없다. 둘 중 하나를 다른 값으로 정한 뒤 다시 친다."
)
_NOT_LOOPBACK_DIAGNOSTIC = (
    "--host 는 루프백만 받는다({allowed}). 받은 값: {host}\n"
    "  벗어나면 토큰이 헤더에 평문으로 실리고 마스킹되지 않은 트레이스도 평문으로 나간다.\n"
    "  원격에서 보려면 SSH 포트 포워딩을 쓴다: ssh -L {port}:127.0.0.1:{port} <서버>"
)


def main(argv: list[str] | None = None) -> int:
    _use_utf8(sys.stdout, sys.stderr)
    args = parse_args(argv)
    # serve 를 먼저 가르는 이유는 관리 API 가 읽기 전용이라 모델이 필요 없기 때문이다. 모델을
    # 여기서 풀면 serve 가 쓰지도 않는 값의 부재로 실패한다.
    if isinstance(args, ServeArgs):
        return _serve(args)
    try:
        model = _chat_model(args.model)
    except ValueError as error:
        sys.stderr.write(f"{error}\n")
        return EXIT_FAILED
    if isinstance(args, ResumeArgs):
        return asyncio.run(_resume(args, model))
    return asyncio.run(_run(args, model))


def _chat_model(name: str | None) -> ChatModel:
    """모델 이름은 플래그, 환경변수, 기본값 순. 빈 지정은 실행 전에 거부한다."""
    return anthropic_chat_model(resolve_model_name(os.environ, name))


def _serve(args: ServeArgs) -> int:
    """관리 API 를 세운다. 구성 오류는 요청 시점이 아니라 여기서 끝난다(ADR 0011).

    실행 식별자가 생기기 전이라 트레이스가 없는 `PluginError` 계열과 같은 성격이다. 진단을 모아
    한 번에 내는 이유는 하나씩 내면 운영자가 고치고 다시 치고 또 막히기 때문이다.

    마지막 줄에 닿기 전에 검사가 끝나 있어야 한다. 순서가 뒤집히면 토큰 없는 서버가 잠시라도
    서고, 그것이 이 명령이 막으려던 바로 그 상태다.
    """
    admin_token = os.environ.get(ADMIN_TOKEN_ENV, "")
    channel_token = os.environ.get(CHANNEL_TOKEN_ENV, "")
    problems = _configuration_problems(args, admin_token, channel_token)
    if problems:
        sys.stderr.write("".join(f"{problem}\n" for problem in problems))
        return EXIT_FAILED
    uvicorn.run(
        create_app(
            plugins=FilesystemPlugins(args.plugins_root),
            trace=JsonlTrace(args.traces),
            admin_token=admin_token,
            channel_token=channel_token,
            stderr=sys.stderr,
        ),
        host=args.host,
        port=args.port,
    )
    return EXIT_FINISHED


def _configuration_problems(args: ServeArgs, admin_token: str, channel_token: str) -> list[str]:
    """서버가 서지 못하는 이유 전부. 비어 있으면 선다.

    토큰은 있나 없나, 같나 다르나만 보고 값을 진단에 싣지 않는다(원칙 V). 구성을 되읊는 진단이
    비밀을 같이 되읊는 자리이고, 표준 에러는 셸 이력과 CI 로그로 흘러간다.

    공백만 있는 토큰도 없는 것으로 본다. 환경변수 하나의 오타가 "설정했다고 믿는 서버"를 만드는
    것이 이 명령이 막으려는 상태이고, `_decision` 이 공백뿐인 거부 사유를 없는 것으로 보는 것과
    같은 판단이다. 대신 통과한 토큰은 다듬지 않고 그대로 넘긴다 — 비밀을 조용히 고쳐 넘기면
    운영자가 정한 값과 서버가 요구하는 값이 갈린다. 같은지도 다듬지 않은 값으로 본다.

    두 토큰이 같다는 진단은 채널 토큰이 있을 때만 낸다. 없는 쪽이 있으면 그 진단이 먼저이고,
    둘 다 비어 "같다"는 것은 고칠 거리가 아니다.
    """
    problems: list[str] = []
    if not admin_token.strip():
        problems.append(_NO_ADMIN_TOKEN_DIAGNOSTIC)
    if not channel_token.strip():
        problems.append(_NO_CHANNEL_TOKEN_DIAGNOSTIC)
    elif channel_token == admin_token:
        problems.append(_SAME_TOKENS_DIAGNOSTIC)
    if args.host not in LOOPBACK_HOSTS:
        problems.append(
            _NOT_LOOPBACK_DIAGNOSTIC.format(
                allowed=", ".join(LOOPBACK_HOSTS), host=args.host, port=args.port
            )
        )
    return problems


async def _run(args: RunArgs, model: ChatModel) -> int:
    return await run_command(
        args.agent,
        args.request,
        Principal(getpass.getuser()),
        plugins=FilesystemPlugins(args.plugins_root),
        model=model,
        tools=McpTools(),
        trace=JsonlTrace(args.traces),
        clock=SystemClock(),
        stdout=sys.stdout,
        stderr=sys.stderr,
        progress=sys.stderr if args.verbose else None,
        traces=args.traces,
        plugins_root=args.plugins_root,
    )


async def _resume(args: ResumeArgs, model: ChatModel) -> int:
    """승인자는 요청한 주체와 같은 출처에서 온다. 자기 승인은 허용한다(ADR 0009)."""
    return await resume_command(
        args.run_id,
        args.decision,
        Principal(getpass.getuser()),
        plugins=FilesystemPlugins(args.plugins_root),
        model=model,
        tools=McpTools(),
        trace=JsonlTrace(args.traces),
        clock=SystemClock(),
        stdout=sys.stdout,
        stderr=sys.stderr,
        progress=sys.stderr if args.verbose else None,
        traces=args.traces,
        plugins_root=args.plugins_root,
    )


def _use_utf8(*streams: TextIO) -> None:
    """Windows 콘솔의 cp949 가 한국어 진단을 깨뜨리지 않게 한다(CLAUDE.md 환경 함정)."""
    for stream in streams:
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
