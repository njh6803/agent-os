"""MCP ToolSource. mcp 의 stdio 클라이언트와 세션으로 서버에 붙어 도구 목록을 주고 도구를 부른다.

(시제품. `.scratch/mcp-shutdown/probes/full_stack.py`가 저장소 사본에 얹어 잰다. 명세가 정한 모양을
구현할 수 있다는 것을 보이는 것이고 구현 티켓이 그대로 옮길 코드가 아니다.)

서버마다 프로세스와 세션 하나를 열어 connect 가 살아 있는 동안 유지한다. MCP 의 타입은 여기서
ToolSpec 과 ToolResult 로 바뀌고 밖으로 나가지 않는다. 도구가 isError 를 돌려주면 ok=false 다.

닫기(입력 닫기 → 기다림 → 프로세스 묶음 끄기)는 mcp 의 stdio_client 가 취소에서 보호한 채 한다(ADR
0034). 서버들은 연 순서의 반대로 하나씩 닫힌다. POSIX 에서는 서버를 런처(`mcp_launcher.py`) 뒤에
띄운다. 런처가 프로세스 그룹의 우두머리가 되어, 서버가 스스로 끝나거나 이 프로세스가 죽으면 그룹을
끈다. 그래서 명령이 없는 것은 띄우기 전에 여기서 본다 — 런처 안에서 나면 연결이 닫힌 것으로만
보인다.

밖으로 나가는 예외는 내장 타입이다. 서버를 여는 동안의 실패는 서버 이름과 명령과 원인을 든
ConnectionError, 도구 호출의 실패는 RuntimeError, 연결 안(부르는 쪽)에서 난 예외는 그 객체 그대로다.
mcp 의 태스크 그룹이 연결 안의 예외를 그룹으로 두 겹 감싸므로, 감싼 것이 그 하나뿐이면 벗긴다.
core 는 연결 안의 yield 에 멈춘 제너레이터를 닫는다(트레이스 쓰기가 실패한 실행). 그때 들어오는
GeneratorExit 가 `BaseExceptionGroup` 으로 나오면 결말을 쓴 실행도 그 그룹을 밖으로 올린다.
"""

from __future__ import annotations

import errno
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

LAUNCHER = Path(__file__).with_name("mcp_launcher.py")


class McpTools:
    @asynccontextmanager
    async def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AsyncGenerator[ToolConnection]:
        escaped = _Escaped()
        unwrapped: BaseException | None = None
        try:
            async with AsyncExitStack() as stack:
                with escaped.watching():
                    connection = await _connection(stack, servers)
                    yield connection
        except BaseExceptionGroup as group:
            unwrapped = escaped.unwrap(group)
            if unwrapped is None:
                raise
        # except 밖에서 던진다. 안에서 던지면 벗긴 예외의 문맥(`__context__`)이 그것을 품은 그룹이
        # 된다.
        if unwrapped is not None:
            raise unwrapped


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


class _Escaped:
    """연결 안에서 빠져나온 예외를 기억해 두고, 닫기를 지나 그룹에 싸여 나오면 그것을 찾는다."""

    def __init__(self) -> None:
        self._errors: list[BaseException] = []

    @contextmanager
    def watching(self) -> Generator[None]:
        """이 안에서 빠져나온 예외를 기억한다. 여는 동안의 실패도 먼저 연 서버의 태스크 그룹을
        지나며 싸이므로 여는 단계까지 덮는다."""
        try:
            yield
        except BaseException as error:
            self._errors.append(error)
            raise

    def unwrap(self, group: BaseExceptionGroup[BaseException]) -> BaseException | None:
        """한 겹씩 하나만 든 그룹을 따라 내려가다 기억한 객체를 만나면 그것, 못 만나면 없음.

        만나는 대로 멈춘다. 안쪽에서 던진 것이 그 자신 예외 그룹이면(에이전트가 낸 그룹) 그 속까지
        내려가지 않는다. 첫 판은 끝까지 내려간 잎만 견줘 그 경우 겉봉을 벗기지 못했다(셀프 리뷰).
        """
        current: BaseException = group
        while not any(current is error for error in self._errors):
            if not _is_group(current) or len(current.exceptions) != 1:
                return None
            current = current.exceptions[0]
        return current


async def _connection(
    stack: AsyncExitStack, servers: Mapping[PluginName, McpServer]
) -> McpConnection:
    """서버들을 매니페스트에 적힌 순서로 연다. 닫기는 탈출 스택이 연 순서의 반대로 한다."""
    routes: dict[str, _Route] = {}
    for name, server in servers.items():
        for route in await _open(stack, name, server):
            routes[route.tool.name] = route
    return McpConnection(routes)


async def _open(stack: AsyncExitStack, name: PluginName, server: McpServer) -> list[_Route]:
    """서버 하나를 띄워 세션을 열고 도구 목록을 읽는다. 실패는 서버를 든 ConnectionError 다."""
    try:
        read, write = await stack.enter_async_context(stdio_client(_parameters(server)))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        tools = await _all_tools(session)
    except Exception as error:
        raise ConnectionError(
            f"MCP 서버 {name}({server.command})에 붙지 못했다: {_describe(error)}"
        ) from error
    return [_Route(server=name, session=session, tool=tool) for tool in tools]


def _parameters(server: McpServer) -> StdioServerParameters:
    """서버를 띄울 명령. POSIX 에서는 런처를 앞에 세우고, 그 전에 명령이 있는지 본다."""
    if sys.platform == "win32":
        return StdioServerParameters(command=server.command, args=list(server.args))
    command = shutil.which(server.command)
    if command is None:
        raise FileNotFoundError(errno.ENOENT, "명령을 찾지 못했다", server.command)
    return StdioServerParameters(
        command=sys.executable, args=["-I", str(LAUNCHER), command, *server.args]
    )


async def _all_tools(session: ClientSession) -> list[Tool]:
    """서버의 도구 전부. 목록이 쪽으로 나뉘어 오면 커서를 따라 끝까지 읽는다."""
    tools: list[Tool] = []
    cursor: str | None = None
    while True:
        params = None if cursor is None else PaginatedRequestParams(cursor=cursor)
        page = await session.list_tools(params=params)
        tools.extend(page.tools)
        cursor = page.next_cursor
        if cursor is None:
            return tools


def _text_of(result: CallToolResult) -> str:
    """결과의 텍스트 블록을 이어 붙인다. 이미지·오디오·링크 블록은 텍스트가 없어 빠진다."""
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
