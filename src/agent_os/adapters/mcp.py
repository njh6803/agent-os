"""MCP ToolSource. mcp 의 클라이언트와 세션으로 서버에 붙어 도구 목록을 주고 도구를 부른다.

서버마다 연결과 세션 하나를 열어 connect 가 살아 있는 동안 유지한다. MCP 의 타입은 여기서
ToolSpec 과 ToolResult 로 바뀌고 밖으로 나가지 않는다. 도구가 isError 를 돌려주면 ok=false 다.

매니페스트의 `[server]` 는 `transport` 로 stdio 와 http 두 모양이다(ADR 0049). stdio 는 서버
프로세스를 띄워 붙고, http 는 원격 서버의 주소에 streamable HTTP 로 붙는다. 서버를 여는 문맥과
실패를 바꾸는 자리는 두 전송이 함께 쓰고 세션을 여는 자리만 갈린다. 아래 "닫기"와 "런처"의 서술은
stdio 모양의 것이다.

**http 모양은 실행마다 붙고 닫는다.** 접속 직전에 `[server.headers]` 의 환경 변수를 매니페스트에
적힌 순서로 읽어 `httpx2.AsyncClient` 의 기본 헤더로 싣는다. 값의 내용은 판정하지 않고(빈 문자열도
있는 것이다) 막는 것은 ASCII 인쇄 가능 글자와 탭이 아닌 글자가 든 값, 그리고 공백이나 탭으로
시작하거나 끝나는 값이다. 라이브러리가 그런 값을 글에 실어 거부하기 때문이다. 환경 변수가 없거나
값을 쓸 수 없으면 붙지 않고 문구가 헤더 이름과 변수 이름을 든다(값은 어디에도 없다). 기한은 mcp 가
자기 클라이언트에 쓰는 값이고 `trust_env` 와 `follow_redirects` 는 기본값이다. 같은 출처의
리디렉션은 라이브러리가 자기 요청마다 스스로 따른다. 응답 훅 하나가 POST 응답마다 상태를 받아 두고
2xx 면 지운다. 여는 동안 실패했을 때 받아 둔 상태가 있으면 원인 끝에
` (HTTP <상태 코드> <이유 구절>)` 로 덧붙인다. 라이브러리는 본문이 JSON-RPC 오류가 아닌 오류
응답(401 등)을 상태 코드 없는 예외로 바꾸므로, 이것이 꺼진 서버와 틀린 토큰을 문구에서 가른다. 응답
본문은 읽지 않는다. GET 알림 흐름의 405 와 라이브러리가 따른 307 이 뒤의 다른 실패에 붙지 않게 POST
의 2xx 에서 지운다.

**http 모양은 취소된 실행에서도 세션 종료 요청을 보내고 닫는다.** 라이브러리의 종료 요청은 끄고
(`terminate_on_close=False`) 어댑터가 자기 클라이언트로 DELETE 를 직접 보낸다. 실행 기한이나 serve
의 종료로 취소된 실행은 라이브러리 문맥을 닫는 `await` 에서 취소를 다시 받아 라이브러리의 요청이
나가지 못하기 때문이다(라이브러리 코드를 읽은 해석이고, 프로브는 요청이 닿지 않는 것까지만 쟀다).
문맥은 보호 없이 닫고, 같은 `finally` 의 보호 범위 안에서 종료 요청과
클라이언트 닫기를 한다(문맥을 닫는 호출을 보호로 감싸면 anyio 가 범위 중첩 위반으로 거부한다).
종료 요청에는 `[server.headers]` 를 포함한 클라이언트의 기본 헤더에 `mcp-session-id`(응답 훅이
`mcp-session-id` 응답 헤더에서 받아 둔 값)와 `mcp-protocol-version`(`initialize()` 결과)을 더하며,
세션 번호를 받지 못했으면(여는 도중 실패, `initialize` 응답 헤더가 오기 전의 취소, 세션을 두지 않는
서버) 보내지 않는다. 응답은 보지 않고
`httpx2.HTTPError` 와 유예의 초과를 삼키며 기록하지 않는다. 유예(`CLOSE_GRACE_SECONDS`, 2초)는 종료
요청에만 걸려 있어 서버가 답하지 않아도 클라이언트 닫기는 건너뛰지 않는다. 그러므로 기한으로
취소된 실행의 끝은 종료 요청에 답하지 않는 서버 하나당 2초까지 늦어질 수 있고(서버는 차례로
닫으므로 ADR 0034, 늦춤은 서버 수에 비례한다), 기한의 결말(원인 `timeout`)은 그대로다. 종료
요청에 답하는 서버라면 정상 닫기는 늦어지지 않는다(왕복이 Windows 0.0~0.016초, Linux
0.002~0.005초. `.scratch/mcp-http/spec.md` 의 "닫기"). 종료 요청의 리디렉션은
`follow_redirects=False` 로 받아 직접 따르되, 같은 출처(http 에서 https 로 올리는 것 포함)이고
메서드가 그대로이며 주소에 사용자 정보가 없는 것만 `client.max_redirects` 번까지 따른다. 그 밖의
위치로는 세션 번호도 헤더도 실려 가지 않고 그 응답으로 끝난다. 연결 방식과 알려진 한계의 근거는
`.scratch/mcp-http/spec.md` 의 "닫기"(ADR 0049 의 이력)다. 닫을 프로세스가 없으므로 stdio 의 "닫는
시간"(아래, 2초 유예와 프로세스 트리 끄기)은 http 만 쓰는 연결에 걸리지 않는다.

**서버가 되울린 헤더 값은 실패 문구에서 가린다.** 서버가 400 이상의 오류 응답에 JSON-RPC 오류를
담아 받은 `Authorization` 값을 글에 되울리면 라이브러리가 그 글을 그대로 예외로 올린다. 가릴 글은
헤더마다 환경에서 읽은 값 전체와, 값이 공백 하나로 나뉜 `<낱말> <나머지>` 꼴이면 그 나머지다.
8자보다 짧은 글은 가리지 않는다. 가리는 자리는 이 어댑터가 짓는 두 문구, 곧 여는 동안의
ConnectionError 와 도구 호출이 실패할 때의 RuntimeError 다. 긴 글부터 글자 그대로 찾아
`[가림: 헤더 <헤더 이름>]` 으로 바꾸고, 가린 것이 있으면 그 예외를 원인을 잇지 않고(`from None`)
던진다. 알려진 한계는 셋이다. 서버가 값을 바꿔(인코딩, 일부, 대소문자) 되울리면 놓친다. 8자보다 짧은
값은 가리지 않는다. 도구가 오류로 돌려준 결과(isError)의 본문은 예외가 아니라 도구 결과로 모델과
트레이스에 가므로 가리지 않는다.

**로그.** 이 어댑터는 로그를 쓰지 않는다. 다만 mcp 의 클라이언트
로거(`mcp.client.streamable_http`)는 DEBUG 로 메시지 전체(`Sending client message: …`)를 찍는데,
거기에 도구 호출의 인자가 그대로 들어 `secret_args` 로 가린 값이 로그에 남는다. 그래서 이 모듈을
불러 들일 때 그 로거에 DEBUG 기록을 버리는 필터를 단다. 로거를 낮추는 수준 설정과 달리 누가 그
로거의 수준을 다시 올려도 걸러진다. httpx2 가 INFO 로 찍는 `HTTP Request: POST <주소 전체>` 는 쿼리
문자열을 싣지만 라이브러리의 동작이라 막지 않는다 (배포 안내의 몫이다). 헤더 값은 `mcp`·`httpx2`·
`httpcore2` 로거의 DEBUG 줄에 실리지 않는다(`.scratch/mcp-http` 의 프로브가 그 셋을 쟀다.
접속이 막힌 `unauthorized` 와 `closed_port` 사례에는 양성 대조가 없다).

**던지는 예외의 타입은 내장이다(`.scratch/mcp-shutdown/spec.md` 의 "경계를 넘는 예외").** 원인
(`__cause__`)에는 mcp 의 원래 예외가 남는다. 서버를 여는 동안(띄우기나 접속, 세션 열기,
`initialize()`, 도구 목록 읽기)의 실패는 서버 이름과 매니페스트의 명령(http 모양이면 주소)과 원인을
든 ConnectionError 이고 원래 예외가 `__cause__` 다. 다만 서버가 되울린 헤더 값을 가렸으면 원인을
잇지 않는다. 문구의 주소는 매니페스트의 `url` 그대로이고(쿼리 문자열 포함이라 쿼리에 비밀을 적으면
`run_failed` 에 남는다. ADR 0049 가 정한 한계다) 개행 같은 제어 문자만 이스케이프한다. 취소는
바꾸지 않는다.
서버들이 같은 이름의 도구를 내면 연결을 열며 모으는 자리에서 도구와 겹친 두 서버를 든 ValueError 로
실패한다. 서버를 차례로 열며 모으므로 겹친 서버 뒤의 서버는 열리지 않고, 셋 이상이 겹쳐도 문구에는
처음 겹친 둘만 든다. 도구 호출의 실패는 서버와 도구를 든 RuntimeError 다. 연결 안(부르는 쪽)에서 난
예외는 그 객체 그대로 나온다. mcp 의 태스크 그룹이 그것을 그룹으로 두 겹 감싸므로, 겹마다 그 하나만
들었으면 벗긴다. 닫기에서 다른 예외가 더 났으면 그 그룹을 그대로 낸다. core 가 연결 안의 yield 에
멈춘 제너레이터를 닫을 때 들어가는 GeneratorExit 도 같다. 벗기지 않으면 결말을 쓴 실행이 그 그룹을
밖으로 올린다.

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
import logging
import math
import os
import shutil
import sys
from collections.abc import AsyncGenerator, Generator, Mapping, Sequence
from contextlib import AsyncExitStack, asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypeGuard

import anyio
import httpx2
from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client
from mcp.types import (
    CallToolResult,
    EmbeddedResource,
    PaginatedRequestParams,
    TextContent,
    TextResourceContents,
    Tool,
)

from agent_os.core.ports import ToolConnection, ToolResult, ToolSpec
from agent_os.sdk import HttpServer, Json, McpServer, PluginName, StdioServer

# 윈도우가 아닌 OS 에서 서버 앞에 세우는 런처(그 모듈의 독스트링).
LAUNCHER = Path(__file__).with_name("mcp_launcher.py")
# 도구 목록을 읽는 쪽 수의 상한. 이 어댑터가 mcp 를 직접 쓰기 전에 기대던 라이브러리(ADR 0034 가
# 바꾼 것)와 같은 값이다(`_all_tools`).
MAX_TOOL_PAGES = 1000
# 이보다 짧은 헤더 값은 실패 문구에서 가리지 않는다. 상관없는 글자까지 바꾸게 되기 때문이다.
MIN_REDACTED_LENGTH = 8
# http 전송의 세션 종료 요청을 기다리는 유예. stdio 상류가 서버가 스스로 끝나기를 기다리는 유예와
# 같은 값이다(ADR 0034·0049). 종료 요청에만 걸린다(`_end_session`).
CLOSE_GRACE_SECONDS = 2


class _NoDebug(logging.Filter):
    """DEBUG 기록을 버린다. 아래 필터가 붙는 이유는 모듈 독스트링의 "로그"다."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno > logging.DEBUG


logging.getLogger("mcp.client.streamable_http").addFilter(_NoDebug())


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
                    earlier = routes.get(route.tool.name)
                    if earlier is not None:
                        raise ValueError(
                            f"같은 이름의 도구가 둘이다: {route.tool.name} "
                            f"({earlier.server}, {route.server})"
                        )
                    routes[route.tool.name] = route
            yield McpConnection(routes)


@dataclass(frozen=True)
class _Route:
    """도구 하나와 그 도구를 가진 서버의 이름과 세션."""

    server: PluginName
    session: ClientSession
    tool: Tool
    attempt: _Attempt


class McpConnection:
    def __init__(self, routes: Mapping[str, _Route]) -> None:
        self._routes = dict(routes)

    def tools(self) -> Sequence[ToolSpec]:
        return [
            ToolSpec(
                name=route.tool.name,
                server=route.server,
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
            message, masked = route.attempt.redact(
                f"MCP 서버 {route.server}의 도구 {name} 호출이 실패했다: {_describe(error)}"
            )
            # 가린 것이 있으면 `from None` 이다(`_connecting` 과 같은 까닭이고 `except` 안에서
            # 던진다).
            if masked:
                raise RuntimeError(message) from None
            raise RuntimeError(message) from error
        return ToolResult(ok=not result.is_error, content=_text_of(result))


@asynccontextmanager
async def _opened(name: PluginName, server: McpServer) -> AsyncGenerator[list[_Route]]:
    """서버 하나의 도구들을 내주고, 나갈 때 그 서버를 닫는다.

    여는 동안의 실패는 서버 이름과 명령(http 모양이면 주소)을 든 ConnectionError 다(`_connecting`).
    이 서버의 태스크 그룹 두 겹을 지나 나온 예외는 여기서 겉봉을 벗긴다(`_Escaped`). 서버마다 이
    문맥 하나를 두어, 탈출 스택을 인자로 받아 거기에 등록하는 꼴(출력 인자)을 두지 않는다.
    """
    escaped = _Escaped()
    attempt = _Attempt()
    unwrapped: BaseException | None = None
    try:
        async with AsyncExitStack() as stack:
            with escaped.watching():
                with _connecting(name, server, attempt):
                    session, tools = await stack.enter_async_context(_session(server, attempt))
                yield [
                    _Route(server=name, session=session, tool=tool, attempt=attempt)
                    for tool in tools
                ]
    except BaseExceptionGroup as group:
        unwrapped = escaped.unwrap(group)
        if unwrapped is None:
            raise
    # except 밖에서 던진다. 안에서 던지면 벗긴 예외의 문맥(`__context__`)이 그것을 품은 그룹이 된다.
    if unwrapped is not None:
        raise unwrapped


@contextmanager
def _connecting(name: PluginName, server: McpServer, attempt: _Attempt) -> Generator[None]:
    """이 안의 예외를 서버 이름과 명령(http 모양이면 주소)과 원인을 든 ConnectionError 로 바꾼다.
    원인의 글은 예외 그룹을 펼친 것이고, 서버가 오류 응답을 돌려줬으면 그 상태가 끝에 붙는다.
    헤더 값을 되울린 글은 가리고, 가린 것이 있으면 원인을 잇지 않는다(`_Attempt.redact`).
    취소는 Exception 이 아니라 바꾸지 않는다."""
    try:
        yield
    except Exception as error:
        _forget_own_cancellation(error)
        message, masked = attempt.redact(
            f"MCP 서버 {name}({_where(server)})에 붙지 못했다: "
            f"{_describe(error)}{attempt.status_suffix()}"
        )
        # 가린 것이 있으면 `from None` 이라 `__cause__` 가 비고 트레이스백도 원래 예외를 싣지
        # 않는다. `__context__` 는 남지만 core 는 그것을 취소를 찾는 데만 쓴다. `except` 밖에서
        # 던지는 모양은 쓰지 않는다. 그 모양은 core 가 닫기의 정리 코드가 덮은 취소를 `__context__`
        # 로 찾는 길을 막는다.
        if masked:
            raise ConnectionError(message) from None
        raise ConnectionError(message) from error


def _forget_own_cancellation(error: BaseException) -> None:
    """원래 예외의 문맥 사슬에서 mcp 가 자기 태스크 그룹을 취소하며 남긴 취소를 뗀다.

    서버가 연결을 거절하면 상류의 전송 태스크가 실패하고 그 그룹이 세션을 여는 코드를 취소한다.
    그 취소는 그룹을 나오며 난 실제 예외의 `__context__` 에 남는다. core 는 닫기의 정리 코드가
    덮은 기한의 취소를 `__context__` 에서 찾아 다시 던지므로(`_cancellation_under`), 그대로
    두면 서버를 못 찾은 실패가 기한이나 바깥의 취소로 읽혀 `run_failed` 없이 취소로 끝난다.
    바깥 범위가 취소되는 중이면(`current_effective_deadline` 이 -inf) 그 취소는 진짜라 건드리지
    않는다. 아닐 때만 사슬을 따라가며 취소를 문맥으로 가진 자리를 끊는다.
    """
    if anyio.current_effective_deadline() == -math.inf:
        return
    cancelled = anyio.get_cancelled_exc_class()
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if isinstance(current.__context__, cancelled):
            current.__context__ = None
            return
        current = current.__context__


def _where(server: McpServer) -> str:
    """실패 문구의 괄호에 들 것. stdio 면 매니페스트의 명령, http 면 매니페스트의 주소다.

    주소는 글자 그대로 싣되(ADR 0049 결정 "주소") 개행 같은 제어 문자는 이스케이프한다. 읽는 단계의
    검사는 개행이 든 주소를 받으므로(`urlsplit` 이 개행을 지운다), 그대로 실으면 문구가 줄을 바꿔
    로그가 위조된다.
    """
    if not isinstance(server, HttpServer):
        return server.command
    return "".join(
        char if char.isprintable() else char.encode("unicode_escape").decode("ascii")
        for char in server.url
    )


@asynccontextmanager
async def _session(
    server: McpServer, attempt: _Attempt
) -> AsyncGenerator[tuple[ClientSession, list[Tool]]]:
    """서버에 붙어 세션을 열고 도구 목록을 읽는다. 나갈 때 세션과 연결을 닫는다.

    서버를 여는 문맥과 실패를 바꾸는 자리는 두 전송이 함께 쓰고, 세션을 여는 자리만 모양으로 갈린다.
    """
    if isinstance(server, HttpServer):
        async with _http_session(server, attempt) as opened:
            yield opened
    else:
        async with _stdio_session(server) as opened:
            yield opened


@asynccontextmanager
async def _stdio_session(
    server: StdioServer,
) -> AsyncGenerator[tuple[ClientSession, list[Tool]]]:
    parameters = _parameters(server)
    async with stdio_client(parameters) as (read, write), ClientSession(read, write) as session:
        await session.initialize()
        yield session, await _all_tools(session)


@asynccontextmanager
async def _http_session(
    server: HttpServer, attempt: _Attempt
) -> AsyncGenerator[tuple[ClientSession, list[Tool]]]:
    """매니페스트의 주소에 streamable HTTP 로 붙는다. 환경을 읽는 코드는 이 갈래에만 있다.

    클라이언트의 기본 헤더가 `[server.headers]` 의 값이다. 기한은 mcp 가 자기 클라이언트에 쓰는
    값(접속·쓰기·풀 30초, 읽기 300초)이고 `trust_env` 와 `follow_redirects` 는 기본값이다. 같은
    출처의 리디렉션은 라이브러리가 자기 요청마다 스스로 따른다. 응답 훅이 오류 응답의 상태와 세션
    번호를 받아 둔다. 종료 요청(DELETE)은 라이브러리가 아니라 `finally` 의 보호 범위 안에서 어댑터가
    보낸다(`_end_session`). 취소된 실행도 그 자리를 지난다.
    """
    headers = _read_headers(server, attempt)
    timeout = httpx2.Timeout(30, read=300)
    client = httpx2.AsyncClient(
        headers=headers, timeout=timeout, event_hooks={"response": [attempt.on_response]}
    )
    try:
        async with (
            streamable_http_client(server.url, http_client=client, terminate_on_close=False) as (
                read,
                write,
            ),
            ClientSession(read, write) as session,
        ):
            initialized = await session.initialize()
            attempt.protocol_version = initialized.protocol_version
            yield session, await _all_tools(session)
    finally:
        # 라이브러리 문맥을 닫은 뒤의 `finally` 다. 취소된 실행은 그 문맥을 닫는 `await` 에서 취소를
        # 다시 받으므로 보호는 여기에 둔다. 문맥을 닫는 호출을 감싸면 라이브러리 안의 취소 범위와
        # 중첩이 어긋나 anyio 가 거부한다(`.scratch/mcp-http/probes` 의 `deadline_shield_exit`).
        with anyio.CancelScope(shield=True):
            await _end_session(client, server.url, attempt)
            await client.aclose()


async def _end_session(client: httpx2.AsyncClient, url: str, attempt: _Attempt) -> None:
    """세션 종료 요청(DELETE)을 서버에 보낸다. 응답은 보지 않고 실패도 삼킨다.

    유예는 이 요청에만 걸린다. 클라이언트를 닫는 일까지 한 유예에 두면 요청이 유예에 걸렸을 때
    닫기가 건너뛰어진다. 세션 번호를 받지 못했으면(`initialize` 전에 실패했거나 서버가 주지 않았다)
    보내지 않는다.
    """
    if attempt.session_id is None:
        return
    headers = {
        "accept": "application/json, text/event-stream",
        "content-type": "application/json",
        "mcp-session-id": attempt.session_id,
    }
    if attempt.protocol_version is not None:
        headers["mcp-protocol-version"] = attempt.protocol_version
    with anyio.move_on_after(CLOSE_GRACE_SECONDS):
        try:
            await _delete(client, url, headers)
        except httpx2.HTTPError:
            pass  # 닫는 중의 실패는 실행의 결말을 바꾸지 않는다(응답은 보지 않는다)


async def _delete(client: httpx2.AsyncClient, url: str, headers: Mapping[str, str]) -> None:
    """DELETE 를 보낸다. 리디렉션은 `follow_redirects=False` 로 받고, 같은 서버 안에서 메서드가
    그대로인 것만 `client.max_redirects` 번까지 따른다. 그 밖의 리디렉션은 그 응답으로 끝낸다.

    httpx2 의 횟수 상한은 한 번의 `send` 안에서만 세므로 따른 횟수를 여기서 센다. 따르지 않은
    위치로는 `Authorization` 밖의 인증 헤더도 세션 번호도 실려 가지 않는다.
    """
    request = client.build_request("DELETE", url, headers=dict(headers))
    followed = 0
    while True:
        response = await client.send(request, follow_redirects=False)
        following = response.next_request
        if following is None or followed == client.max_redirects:
            return
        if not _stays_in_server(response.request, following):
            return
        request = following
        followed += 1


def _stays_in_server(sent: httpx2.Request, following: httpx2.Request) -> bool:
    """다음 요청이 방금 보낸 요청과 같은 서버 안이고 메서드가 그대로이며 사용자 정보가 없는가.

    같은 서버는 scheme·호스트·포트가 같거나, 기본 포트를 쓰는 같은 호스트의 http 에서 https 로
    올리는 것이다. 라이브러리가 자기 요청의 리디렉션을 따르는 조건과 같되 사용자 정보는 보낸 요청의
    것이어도 거른다(매니페스트가 url 의 사용자 정보를 거부하므로 실효 차이는 없다). 그 판정은 비공개
    모듈이라 가져다 쓰지 않고, httpx2 의 공개 API 만 쓴다. httpx2 는 기본 포트를 `None` 으로 두고
    호스트를 소문자로 바꾼다. 302·303 은 메서드를 GET 으로 바꾸므로 여기서 걸러진다.
    """
    old, new = sent.url, following.url
    same_origin = (old.scheme, old.host, old.port) == (new.scheme, new.host, new.port)
    https_upgrade = (
        old.host == new.host
        and old.scheme == "http"
        and old.port is None
        and new.scheme == "https"
        and new.port is None
    )
    return following.method == sent.method and not new.userinfo and (same_origin or https_upgrade)


def _read_headers(server: HttpServer, attempt: _Attempt) -> dict[str, str]:
    """`[server.headers]` 의 환경 변수를 매니페스트에 적힌 순서로 읽는다.

    값의 내용은 보지 않는다. 빈 문자열도 있는 것으로 본다. 막는 것은 둘이다. 값에 ASCII 인쇄 가능
    글자와 탭이 아닌 글자가 든 경우, 그리고 값이 공백이나 탭으로 시작하거나 끝나는 경우다.
    라이브러리는 개행이 든 값을 그 값 전체를 실은 예외로, 비ASCII 글자를 그 글자를 실은 예외로,
    앞뒤에 공백이나 탭이 붙은 값을 그 값을 실은 예외로 거부하므로(손으로 `httpx2` 를 대 봤다),
    라이브러리에 넘기기 전에 막아야 값이 `run_failed` 로 트레이스에 남지 않는다. 어느 문장에도 값은
    없다.
    """
    headers: dict[str, str] = {}
    problems: list[str] = []
    for header, variable in server.headers.items():
        value = os.environ.get(variable)
        if value is None:
            problems.append(f"헤더 {header}의 환경 변수 {variable}이 없다")
        elif value != value.strip(" \t") or not all(
            char == "\t" or " " <= char <= "~" for char in value
        ):
            problems.append(
                f"헤더 {header}의 환경 변수 {variable}의 값에 헤더 값으로 쓸 수 없는 글자가 있다"
            )
        else:
            headers[header] = value
            attempt.protect(header, value)
    if problems:
        raise _HeaderUnusable("; ".join(problems))
    return headers


class _HeaderUnusable(Exception):
    """헤더의 환경 변수가 없거나 값을 쓸 수 없다. 글에는 이름만 있고 값이 없다."""


@dataclass
class _Attempt:
    """서버 하나에 붙는 한 번의 곁정보. 실패 문구를 지을 때, 도구 호출이 실패할 때, 닫으며 세션
    종료 요청을 보낼 때 쓴다.

    `secrets` 는 서버가 오류 글에 되울릴 수 있어 가릴 글이다. 헤더마다 환경에서 읽은 값 전체와, 값이
    공백 하나로 나뉜 `<낱말> <나머지>` 꼴이면 그 나머지(`Bearer <토큰>` 의 토큰)다. 8자보다 짧은
    글은 가리지 않는다. 상관없는 글자까지 바꾸게 되기 때문이다. `status` 는 마지막 POST 응답이 2xx
    가 아니었을 때의 그 상태다. `session_id` 는 응답 헤더 `mcp-session-id` 로 받아 둔 세션 번호이고
    `protocol_version` 은 `initialize` 결과의 프로토콜 판이다. 둘 다 종료 요청(`_end_session`)이
    쓰며, 서버가 세션 번호를 주지 않았으면 `session_id` 는 `None` 이고 종료 요청을 보내지 않는다.
    """

    secrets: list[tuple[str, str]] = field(default_factory=list[tuple[str, str]])
    status: str | None = None
    session_id: str | None = None
    protocol_version: str | None = None

    def protect(self, header: str, value: str) -> None:
        head, space, rest = value.partition(" ")
        candidates = [value, rest] if head and space else [value]
        self.secrets.extend(
            (header, text) for text in candidates if len(text) >= MIN_REDACTED_LENGTH
        )

    def redact(self, text: str) -> tuple[str, bool]:
        """긴 글부터 글자 그대로 찾아 `[가림: 헤더 <헤더 이름>]` 으로 바꾼다. 가린 것이 있었는지도
        준다."""
        masked = False
        for header, secret in sorted(self.secrets, key=lambda pair: len(pair[1]), reverse=True):
            if secret in text:
                text = text.replace(secret, f"[가림: 헤더 {header}]")
                masked = True
        return text, masked

    def status_suffix(self) -> str:
        return "" if self.status is None else f" ({self.status})"

    async def on_response(self, response: httpx2.Response) -> None:
        """모든 응답의 `mcp-session-id` 헤더를 세션 번호로 받아 둔다. POST 응답마다 받아 둔 상태를
        바꾸고 2xx 면 지운다. GET 과 DELETE 의 응답은 상태로 받아 두지 않는다.

        라이브러리가 삼킨 GET 알림 흐름의 405 나, 라이브러리가 따른 307 이 뒤의 다른 실패에 붙지
        않게 한다. 응답 본문은 읽지 않는다.
        """
        session = response.headers.get("mcp-session-id")
        if session:
            self.session_id = session
        if response.request.method != "POST":
            return
        self.status = (
            None if response.is_success else f"HTTP {response.status_code} {response.reason_phrase}"
        )


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


def _parameters(server: StdioServer) -> StdioServerParameters:
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
    """ExceptionGroup 은 겉만 보면 원인을 알 수 없어서 안의 예외를 펼친다. 헤더 환경 변수의 문제는
    종류 이름 없이 그 글만 낸다(글이 곧 원인이다)."""
    if isinstance(error, _HeaderUnusable):
        return str(error)
    if _is_group(error):
        return "; ".join(_describe(inner) for inner in error.exceptions)
    return f"{type(error).__name__}: {error}"


def _is_group(error: BaseException) -> TypeGuard[BaseExceptionGroup[BaseException]]:
    """isinstance 로 좁히면 pyright 가 타입 인자를 Unknown 으로 둔다. 여기서 명시한다."""
    return isinstance(error, BaseExceptionGroup)
