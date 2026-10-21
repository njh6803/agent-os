"""MCP ToolSource. mcp 의 stdio 클라이언트와 세션으로 서버에 붙어 도구 목록을 주고 도구를 부른다.

서버마다 프로세스와 세션 하나를 열어 connect 가 살아 있는 동안 유지한다. MCP 의 타입은 여기서
ToolSpec 과 ToolResult 로 바뀌고 밖으로 나가지 않는다. 도구가 isError 를 돌려주면 ok=false 다.

**던지는 예외의 타입은 내장이다(`.scratch/mcp-shutdown/spec.md` 의 "경계를 넘는 예외").** 원인
(`__cause__`)에는 mcp 의 원래 예외가 남는다. 서버를 여는 동안(띄우기, 세션 열기, `initialize()`,
도구 목록 읽기)의 실패는 서버 이름과 매니페스트의 명령과 원인을 든 ConnectionError 이고 원래 예외가
`__cause__` 다. 취소는 바꾸지 않는다.
도구 호출의 실패는 서버와 도구를 든 RuntimeError 다. 연결 안(부르는 쪽)에서 난 예외는 그 객체 그대로
나온다. mcp 의 태스크 그룹이 그것을 그룹으로 두 겹 감싸므로, 겹마다 그 하나만 들었으면 벗긴다.
닫기에서 다른 예외가 더 났으면 그 그룹을 그대로 낸다. core 가 연결 안의 yield 에 멈춘 제너레이터를
닫을 때 들어가는 GeneratorExit 도 같다. 벗기지 않으면 결말을 쓴 실행이 그 그룹을 밖으로 올린다.

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
from collections.abc import AsyncGenerator, Generator, Mapping, Sequence
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import TypeGuard

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
        """서버들을 매니페스트에 적힌 순서로 열고, 탈출 스택이 연 순서의 반대로 닫는다."""
        async with AsyncExitStack() as stack:
            routes: dict[str, _Route] = {}
            for name, server in servers.items():
                for route in await stack.enter_async_context(_opened(name, server)):
                    routes[route.tool.name] = route
            yield McpConnection(routes)


@dataclass(frozen=True)
class _Route:
    """도구 하나와 그 도구를 가진 서버의 이름과 세션."""

    server: PluginName
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
        try:
            result = await route.session.call_tool(name, dict(args))
        except Exception as error:
            raise RuntimeError(
                f"MCP 서버 {route.server}의 도구 {name} 호출이 실패했다: {_describe(error)}"
            ) from error
        return ToolResult(ok=not result.is_error, content=_text_of(result))


@asynccontextmanager
async def _opened(name: PluginName, server: McpServer) -> AsyncGenerator[list[_Route]]:
    """서버 하나의 도구들을 내주고, 나갈 때 그 서버를 닫는다.

    여는 동안의 실패는 서버 이름과 명령을 든 ConnectionError 다(`_connecting`). 이 서버의 태스크
    그룹 두 겹을 지나 나온 예외는 여기서 겉봉을 벗긴다(`_Escaped`). 서버마다 이 문맥 하나를 두어,
    탈출 스택을 인자로 받아 거기에 등록하는 꼴(출력 인자)을 두지 않는다.
    """
    escaped = _Escaped()
    unwrapped: BaseException | None = None
    try:
        async with AsyncExitStack() as stack:
            with escaped.watching():
                with _connecting(name, server):
                    session, tools = await stack.enter_async_context(_session(server))
                yield [_Route(server=name, session=session, tool=tool) for tool in tools]
    except BaseExceptionGroup as group:
        unwrapped = escaped.unwrap(group)
        if unwrapped is None:
            raise
    # except 밖에서 던진다. 안에서 던지면 벗긴 예외의 문맥(`__context__`)이 그것을 품은 그룹이 된다.
    if unwrapped is not None:
        raise unwrapped


@contextmanager
def _connecting(name: PluginName, server: McpServer) -> Generator[None]:
    """이 안의 예외를 서버 이름과 명령과 원인을 든 ConnectionError 로 바꾼다. 원인의 글은 예외
    그룹을 펼친 것이다. 취소는 Exception 이 아니라 바꾸지 않는다."""
    try:
        yield
    except Exception as error:
        raise ConnectionError(
            f"MCP 서버 {name}({server.command})에 붙지 못했다: {_describe(error)}"
        ) from error


@asynccontextmanager
async def _session(server: McpServer) -> AsyncGenerator[tuple[ClientSession, list[Tool]]]:
    """서버를 띄워 세션을 열고 도구 목록을 읽는다. 나갈 때 세션과 프로세스를 닫는다."""
    parameters = _parameters(server)
    async with stdio_client(parameters) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        yield session, await _all_tools(session)


class _Escaped:
    """연결 안에서 빠져나온 예외를 기억해 두고, 닫기를 지나 그룹에 싸여 나오면 그것을 찾는다."""

    def __init__(self) -> None:
        self._errors: list[BaseException] = []

    @contextmanager
    def watching(self) -> Generator[None]:
        """이 안에서 빠져나온 예외를 기억한다. 여는 동안의 실패와, 연결 안(부르는 쪽)에서 난 예외와
        닫기가 넣은 GeneratorExit 를 함께 덮는다."""
        try:
            yield
        except BaseException as error:
            self._errors.append(error)
            raise

    def unwrap(self, group: BaseExceptionGroup[BaseException]) -> BaseException | None:
        """한 겹씩 하나만 든 그룹을 따라 내려가다 기억한 객체를 만나면 그것, 못 만나면 없음.

        만나는 대로 멈춘다. 안쪽에서 던진 것이 그 자신 예외 그룹이면(에이전트가 낸 그룹) 그 속까지
        내려가지 않는다. 잎까지 내려가 견주면 그 경우 겉봉을 벗기지 못한다.
        """
        current: BaseException = group
        while not any(current is error for error in self._errors):
            if not _is_group(current) or len(current.exceptions) != 1:
                return None
            current = current.exceptions[0]
        return current


def _parameters(server: McpServer) -> StdioServerParameters:
    """서버를 띄울 명령. 윈도우가 아니면 런처를 앞에 세우고, 그 전에 명령이 있는지 본다.

    명령이 없다는 실패가 런처 안에서 나면 클라이언트에는 연결이 닫힌 것으로만 보이므로 여기서
    `FileNotFoundError`를 낸다. 여는 단계(`_connecting`) 안이라 연결 오류의 원인이 된다.
    `shutil.which`는 실행 권한이 있는 파일만 찾으므로 있지만 실행할 수 없는 명령도 이 예외다.
    윈도우에서는 찾아보지 않는다. 상류가 `.cmd`·`.ps1`까지 붙여 찾고, 없으면 같은 예외를 낸다
    (`.scratch/mcp-shutdown/spec.md` 의 "서버를 여는 실패").
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


def _describe(error: BaseException) -> str:
    """ExceptionGroup 은 겉만 보면 원인을 알 수 없어서 안의 예외를 펼친다."""
    if _is_group(error):
        return "; ".join(_describe(inner) for inner in error.exceptions)
    return f"{type(error).__name__}: {error}"


def _is_group(error: BaseException) -> TypeGuard[BaseExceptionGroup[BaseException]]:
    """isinstance 로 좁히면 pyright 가 타입 인자를 Unknown 으로 둔다. 여기서 명시한다."""
    return isinstance(error, BaseExceptionGroup)
