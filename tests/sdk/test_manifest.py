"""매니페스트가 디스크 형식의 규약을 지키는지. 종류별 필드 자리와 형식 버전."""

import pytest
from pydantic import ValidationError

from agent_os.sdk import PluginKind, parse_manifest

AGENT = """
schema_version = "1"
kind = "agent"
name = "echo"
version = "0.1.0"
entrypoint = "echo.agent:EchoAgent"
"""

MCP = """
schema_version = "1"
kind = "mcp"
name = "fs"
version = "0.1.0"

[server]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-everything"]
"""


def test_agent_manifest_parses() -> None:
    manifest = parse_manifest(AGENT)
    assert manifest.kind is PluginKind.AGENT
    assert manifest.entrypoint == "echo.agent:EchoAgent"


def test_unknown_kind_is_rejected() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(AGENT.replace('kind = "agent"', 'kind = "graph"'))


def test_entrypoint_belongs_to_agent_only() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(MCP + 'entrypoint = "x:y"\n')
    with pytest.raises(ValidationError):
        parse_manifest(AGENT.replace('entrypoint = "echo.agent:EchoAgent"\n', ""))


def test_형식_버전이_없으면_거부한다() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(AGENT.replace('schema_version = "1"\n', ""))


def test_모르는_형식_버전은_거부한다() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(AGENT.replace('schema_version = "1"', 'schema_version = "2"'))


def test_플러그인_종류는_넷이고_model이_있다() -> None:
    assert {kind.value for kind in PluginKind} == {"agent", "mcp", "skill", "model"}


def test_에이전트는_MCP_서버를_안_적으면_빈_목록이다() -> None:
    assert parse_manifest(AGENT).mcp == ()


def test_에이전트는_쓸_MCP_서버_이름을_적는다() -> None:
    manifest = parse_manifest(AGENT + 'mcp = ["everything"]\n')
    assert manifest.mcp == ("everything",)


def test_에이전트가_아니면_MCP_서버_목록을_갖지_못한다() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(MCP + "mcp = []\n")


def test_mcp는_서버_실행_명령과_인자를_가진다() -> None:
    manifest = parse_manifest(MCP)
    assert manifest.server is not None
    assert manifest.server.command == "npx"
    assert manifest.server.args == ("-y", "@modelcontextprotocol/server-everything")


def test_mcp는_서버_표가_없으면_거부한다() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(MCP.split("[server]")[0])


def test_mcp가_아니면_서버_표를_갖지_못한다() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(AGENT + '[server]\ncommand = "npx"\n')
