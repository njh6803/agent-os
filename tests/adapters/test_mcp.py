"""MCP ToolSource. 파이썬으로 쓴 진짜 stdio 서버(mcp_fixture_server.py)에 붙는다. 네트워크가 없다.

세션을 async 픽스처로 열지 않는다. pytest-asyncio 가 픽스처의 setup 과 teardown 을 다른 태스크에서
돌리는데 MCP 의 stdio 클라이언트는 anyio 취소 범위라 같은 태스크에서 닫혀야 한다(ADR 0007 이력).
그래서 테스트 본문에서 async with 로 열고 닫는다.
"""

import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import pytest

from agent_os.adapters.mcp import McpTools
from agent_os.core.ports import ToolSession, ToolSource
from agent_os.sdk import McpServer, PluginName

FIXTURE = McpServer(
    command=sys.executable, args=(str(Path(__file__).with_name("mcp_fixture_server.py")),)
)


@asynccontextmanager
async def _fixture_session() -> AsyncGenerator[ToolSession]:
    tools: ToolSource = McpTools()
    async with tools.connect({PluginName("fixture"): FIXTURE}) as session:
        yield session


async def test_서버의_도구_목록과_입력_스키마를_준다() -> None:
    async with _fixture_session() as session:
        specs = {spec.name: spec for spec in session.tools()}

    assert set(specs) == {"add", "fail"}
    properties = specs["add"].input_schema["properties"]
    assert isinstance(properties, dict)
    assert set(properties) == {"a", "b"}


async def test_도구를_부르면_결과_텍스트가_온다() -> None:
    async with _fixture_session() as session:
        result = await session.call("add", {"a": 2, "b": 3})

    assert result.ok is True
    assert result.content == "5"


async def test_도구가_에러를_내면_실패로_표시되고_에러_내용이_온다() -> None:
    async with _fixture_session() as session:
        result = await session.call("fail", {"reason": "overflow"})

    assert result.ok is False
    assert "overflow" in result.content


async def test_없는_도구는_에러다() -> None:
    async with _fixture_session() as session:
        with pytest.raises(LookupError, match="nope"):
            await session.call("nope", {})


async def test_서버_기동_실패는_연결_단계에서_예외다() -> None:
    tools: ToolSource = McpTools()
    broken = McpServer(command="definitely-not-a-command-agent-os")

    with pytest.raises(FileNotFoundError):
        async with tools.connect({PluginName("broken"): broken}):
            pass


async def test_서버를_지정하지_않으면_도구_없이_연다() -> None:
    tools: ToolSource = McpTools()

    async with tools.connect({}) as opened:
        assert list(opened.tools()) == []
