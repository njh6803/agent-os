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
from pathlib import Path
from typing import TextIO

from agent_os.adapters.anthropic import anthropic_chat_model, resolve_model_name
from agent_os.adapters.clock import SystemClock
from agent_os.adapters.filesystem import FilesystemPlugins
from agent_os.adapters.jsonl import JsonlTrace
from agent_os.adapters.mcp import McpTools
from agent_os.channel.cli.main import (
    EXIT_FAILED,
    ResumeArgs,
    RunArgs,
    parse_args,
    resume_command,
    run_command,
)
from agent_os.core.ports import ChatModel
from agent_os.sdk import Principal

PLUGINS_ROOT = Path("plugins")


def main(argv: list[str] | None = None) -> int:
    _use_utf8(sys.stdout, sys.stderr)
    args = parse_args(argv)
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


async def _run(args: RunArgs, model: ChatModel) -> int:
    return await run_command(
        args.agent,
        args.request,
        Principal(getpass.getuser()),
        plugins=FilesystemPlugins(PLUGINS_ROOT),
        model=model,
        tools=McpTools(),
        trace=JsonlTrace(args.traces),
        clock=SystemClock(),
        stdout=sys.stdout,
        stderr=sys.stderr,
        progress=sys.stderr if args.verbose else None,
    )


async def _resume(args: ResumeArgs, model: ChatModel) -> int:
    """승인자는 요청한 주체와 같은 출처에서 온다. 자기 승인은 허용한다(ADR 0009)."""
    return await resume_command(
        args.run_id,
        args.decision,
        Principal(getpass.getuser()),
        plugins=FilesystemPlugins(PLUGINS_ROOT),
        model=model,
        tools=McpTools(),
        trace=JsonlTrace(args.traces),
        clock=SystemClock(),
        stdout=sys.stdout,
        stderr=sys.stderr,
        progress=sys.stderr if args.verbose else None,
    )


def _use_utf8(*streams: TextIO) -> None:
    """Windows 콘솔의 cp949 가 한국어 진단을 깨뜨리지 않게 한다(CLAUDE.md 환경 함정)."""
    for stream in streams:
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
