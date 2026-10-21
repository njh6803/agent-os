"""MCP ToolSource. mcp 의 stdio 클라이언트와 세션으로 서버에 붙어 도구 목록을 주고 도구를 부른다.

서버마다 프로세스와 세션 하나를 열어 connect 가 살아 있는 동안 유지한다. MCP 의 타입은 여기서
ToolSpec 과 ToolResult 로 바뀌고 밖으로 나가지 않는다. 도구가 isError 를 돌려주면 ok=false 다.

**닫기는 취소된 실행에서도 끝까지 간다(ADR 0034).** 서버들은 연 순서의 반대로 하나씩 닫는다(탈출
스택의 순서). mcp 2 의 stdio 클라이언트가 서버마다의 닫기를 취소에서 보호하므로, 실행 타임아웃이나
serve 의 종료로 취소된 실행도 서버를 닫은 뒤에 끝난다. 상류의 닫기는 서버의 입력을 닫고 서버가
스스로 끝나기를 2초 기다린 뒤, 그때까지 끝나지 않은 서버만 프로세스 트리째 끈다. 윈도우는 Job
Object 를 곧바로 끝내고, POSIX 는 그룹에 SIGTERM 을 보내 2초 안에 그룹이 사라지지 않으면 SIGKILL 을
보낸다. 윈도우는 그 뒤 Job Object 를 닫아 남은 자손을 거두고, POSIX 는 그것을 하지 않는다(mcp 2.3.0
`client/stdio.py` 의 `_stop_server_process`, 코드를 읽었다. 런처 없이 Linux 에서 잰 것은
`.scratch/mcp-shutdown/probes/README.md` 의 `exit_child_normal`). 그래서 윈도우가 아닌 OS 에서는
서버를 런처(`mcp_launcher.py`) 뒤에 띄운다. 유예 안에 스스로 끝난 서버가 남긴 자식은 런처가 서버의
프로세스 그룹째 거두고, 이 프로세스가 갑자기 죽어도 런처가 그것을 보고 그룹을 끈다(그 모듈의
독스트링). 닫는 시간에 대해 운영자와 플러그인 작성자가 알 것은 셋이다.

- 서버 하나를 닫는 시간은 서버의 모양에 달렸다. 잰 값은 입력이 닫히면 스스로 끝나는 서버가
  0.18~0.46초, 입력이 닫혀도 끝나지 않는 서버가 2.0~2.2초(상류의 유예), SIGTERM 까지 무시하는
  서버(POSIX)가 4.0초다(`.scratch/mcp-shutdown/spec.md` 의 "닫는 데 드는 시간"). 입력이 닫히면
  스스로 끝나는 서버가 가장 빨리 닫힌다.
- 서버를 차례로 닫으므로 닫는 시간은 서버 수에 비례한다.
- 그만큼 기한 뒤의 결말, HTTP 채널의 동시 실행 칸 반환, serve 의 종료가 늦다.
"""

from __future__ import annotations

import errno
import os
import shutil
import sys
from collections.abc import AsyncGenerator, Mapping, Sequence
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.types import (
    CallToolResult,
    EmbeddedResource,
    PaginatedRequestParams,
    TextContent,
    TextResourceContents,
    Tool,
)

from agent_os.core.ports import ToolConnection, ToolResult, ToolSpec
from agent_os.sdk import Json, McpServer, PluginName

# 윈도우가 아닌 OS 에서 서버 앞에 세우는 런처(그 모듈의 독스트링).
LAUNCHER = Path(__file__).with_name("mcp_launcher.py")
# 도구 목록을 읽는 쪽 수의 상한. 이 어댑터가 mcp 를 직접 쓰기 전에 기대던 라이브러리(ADR 0034 가
# 바꾼 것)와 같은 값이다(`_all_tools`).
MAX_TOOL_PAGES = 1000


class McpTools:
    @asynccontextmanager
    async def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AsyncGenerator[ToolConnection]:
        async with AsyncExitStack() as stack:
            routes: dict[str, _Route] = {}
            for server in servers.values():
                session = await _session(stack, server)
                for tool in await _all_tools(session):
                    routes[tool.name] = _Route(session=session, tool=tool)
            yield McpConnection(routes)


@dataclass(frozen=True)
class _Route:
    """도구 하나와 그 도구를 가진 서버의 세션."""

    session: ClientSession
    tool: Tool


class McpConnection:
    def __init__(self, routes: Mapping[str, _Route]) -> None:
        self._routes = dict(routes)

    def tools(self) -> Sequence[ToolSpec]:
        return [
            ToolSpec(
                name=route.tool.name,
                description=route.tool.description or "",
                input_schema=dict(route.tool.input_schema),
            )
            for route in self._routes.values()
        ]

    async def call(self, name: str, args: Mapping[str, Json]) -> ToolResult:
        route = self._routes.get(name)
        if route is None:
            raise LookupError(f"도구가 없다: {name}")
        result = await route.session.call_tool(name, dict(args))
        return ToolResult(ok=not result.is_error, content=_text_of(result))


async def _session(stack: AsyncExitStack, server: McpServer) -> ClientSession:
    read, write = await stack.enter_async_context(stdio_client(_parameters(server)))
    session = await stack.enter_async_context(ClientSession(read, write))
    await session.initialize()
    return session


def _parameters(server: McpServer) -> StdioServerParameters:
    """서버를 띄울 명령. 윈도우가 아니면 런처를 앞에 세우고, 그 전에 명령이 있는지 본다.

    명령이 없다는 실패가 런처 안에서 나면 클라이언트에는 연결이 닫힌 것으로만 보이므로 여기서
    `FileNotFoundError`를 낸다. `shutil.which`는 실행 권한이 있는 파일만 찾으므로 있지만 실행할 수
    없는 명령도 이 예외다. 윈도우에서는 찾아보지 않는다. 상류가 `.cmd`·`.ps1`까지 붙여 찾고, 없으면
    같은 예외를 낸다(`.scratch/mcp-shutdown/spec.md` 의 "서버를 여는 실패").
    """
    if sys.platform == "win32":
        return StdioServerParameters(command=server.command, args=list(server.args))
    command = shutil.which(server.command)
    if command is None:
        raise FileNotFoundError(errno.ENOENT, "실행할 수 있는 명령을 찾지 못했다", server.command)
    return StdioServerParameters(
        command=sys.executable,
        args=["-I", str(LAUNCHER), str(os.getpid()), command, *server.args],
    )


async def _all_tools(session: ClientSession) -> list[Tool]:
    """서버의 도구 전부. 목록이 쪽으로 나뉘어 오면 커서를 따라 끝까지 읽는다.

    커서가 없거나 빈 글이면 끝이고, 쪽 수가 상한을 넘으면 여는 단계가 실패한다. 앞서 기대던
    라이브러리(ADR 0034 가 바꾼 것)가 그렇게 했다(`.scratch/mcp-shutdown/spec.md` 의 "어댑터"). 빈
    커서를 끝으로 보지 않거나 상한이 없으면, 빈 커서를 내거나 커서를 무시하는 서버에 붙어 같은 쪽을
    끝없이 묻는다.
    """
    tools: list[Tool] = []
    cursor: str | None = None
    for _ in range(MAX_TOOL_PAGES):
        params = None if cursor is None else PaginatedRequestParams(cursor=cursor)
        page = await session.list_tools(params=params)
        tools.extend(page.tools)
        cursor = page.next_cursor
        if not cursor:
            return tools
    raise RuntimeError(f"도구 목록이 {MAX_TOOL_PAGES}쪽을 넘었다")


def _text_of(result: CallToolResult) -> str:
    """결과의 텍스트 블록과 텍스트 리소스의 글을 이어 붙인다. 이미지·오디오·링크 블록은 빠진다."""
    parts: list[str] = []
    for block in result.content:
        if isinstance(block, TextContent):
            parts.append(block.text)
        elif isinstance(block, EmbeddedResource) and isinstance(
            block.resource, TextResourceContents
        ):
            parts.append(block.resource.text)
    return "".join(parts)
