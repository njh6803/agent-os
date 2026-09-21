"""MCP ToolSource. langchain-mcp-adapters 로 stdio 서버에 붙어 도구 목록을 주고 도구를 부른다.

서버마다 세션 하나를 열어 connect 가 살아 있는 동안 유지한다. MCP 와 langchain 의 타입은 여기서
ToolSpec 과 ToolResult 로 바뀌고 밖으로 나가지 않는다. 도구가 isError 를 돌려주면 ok=false 다.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Mapping, Sequence
from contextlib import AsyncExitStack, asynccontextmanager

from langchain_core.messages import ToolMessage
from langchain_core.messages.tool import ToolCall
from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import StdioConnection
from langchain_mcp_adapters.tools import load_mcp_tools

from agent_os.core.ports import ToolConnection, ToolResult, ToolSpec
from agent_os.sdk import Json, McpServer, PluginName


class McpTools:
    @asynccontextmanager
    async def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AsyncGenerator[ToolConnection]:
        client = MultiServerMCPClient({name: _stdio(server) for name, server in servers.items()})
        async with AsyncExitStack() as stack:
            tools: list[BaseTool] = []
            for name in servers:
                session = await stack.enter_async_context(client.session(name))
                tools.extend(await load_mcp_tools(session))
            yield McpConnection(tools)


class McpConnection:
    def __init__(self, tools: Sequence[BaseTool]) -> None:
        self._tools = {tool.name: tool for tool in tools}

    def tools(self) -> Sequence[ToolSpec]:
        return [
            ToolSpec(name=tool.name, description=tool.description, input_schema=_schema_of(tool))
            for tool in self._tools.values()
        ]

    async def call(self, name: str, args: Mapping[str, Json]) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            raise LookupError(f"도구가 없다: {name}")
        # ToolCall 로 부르면 ToolMessage 가 돌아와 status 로 성공 여부를 알 수 있다.
        message = await tool.ainvoke(
            ToolCall(name=name, args=dict(args), id=name, type="tool_call")
        )
        if not isinstance(message, ToolMessage):
            raise TypeError(f"도구 {name} 이 ToolMessage 가 아닌 것을 돌려줬다: {type(message)}")
        return ToolResult(ok=message.status == "success", content=message.text)


def _schema_of(tool: BaseTool) -> Mapping[str, Json]:
    """MCP 도구의 args_schema 는 서버가 준 JSON Schema dict 다.

    get_input_jsonschema() 는 Runnable 입력(str | dict | ToolCall)의 스키마라 top-level anyOf 가
    생기고 Anthropic 이 그 도구를 버린다. 도구 인자의 스키마는 args_schema 쪽이다.
    """
    schema = tool.args_schema
    if not isinstance(schema, dict):
        raise TypeError(f"MCP 도구 {tool.name} 의 args_schema 가 dict 가 아니다: {type(schema)}")
    return dict(schema)


def _stdio(server: McpServer) -> StdioConnection:
    return StdioConnection(transport="stdio", command=server.command, args=list(server.args))
