"""도구 목록을 쪽으로 나눠 내는 가짜 stdio MCP 서버(시제품). 첫 인자가 모양이다.

- `empty`: 도구 하나와 빈 커서를 낸다. 빈 커서를 끝으로 보지 않는 클라이언트는 그 커서로 거듭
  묻는다.
- `endless`: 묻는 커서와 상관없이 도구 하나와 같은 커서를 낸다. 끝나지 않는 목록이다.

고수준 `MCPServer`는 커서를 고를 수 없어 저수준 `Server`로 짓는다.
"""

from __future__ import annotations

import sys

import anyio
from mcp.server.context import ServerRequestContext
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from mcp.types import ListToolsResult, PaginatedRequestParams, Tool

TOOL = Tool(name="paged", input_schema={"type": "object"})
CURSORS = {"empty": "", "endless": "again"}


async def main(shape: str) -> None:
    cursor = CURSORS[shape]

    async def list_tools(
        ctx: ServerRequestContext[dict[str, object]], params: PaginatedRequestParams | None
    ) -> ListToolsResult:
        return ListToolsResult(tools=[TOOL], next_cursor=cursor)

    server = Server("paged", on_list_tools=list_tools)
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


if __name__ == "__main__":
    anyio.run(main, sys.argv[1])
