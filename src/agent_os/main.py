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
from agent_os.channel.cli.main import RunArgs, parse_run_args, run_command
from agent_os.sdk import Principal

PLUGINS_ROOT = Path("plugins")


def main(argv: list[str] | None = None) -> int:
    _use_utf8(sys.stdout, sys.stderr)
    args = parse_run_args(argv)
    return asyncio.run(_run(args))


async def _run(args: RunArgs) -> int:
    return await run_command(
        args.agent,
        args.request,
        Principal(getpass.getuser()),
        plugins=FilesystemPlugins(PLUGINS_ROOT),
        model=anthropic_chat_model(resolve_model_name(os.environ, args.model)),
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
