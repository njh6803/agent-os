"""매니페스트가 디스크 형식의 규약을 지키는지. 종류별 필드 자리와 형식 버전."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from agent_os.sdk import McpServer, PluginKind, PluginName, approval_conflicts, parse_manifest

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


def _top_level(manifest: str, line: str) -> str:
    """[server] 표 앞에 넣는다. 표 뒤에 붙이면 그 표의 키가 되어 다른 이유로 거부된다."""
    return manifest.replace("[server]", f"{line}\n\n[server]", 1)


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
        parse_manifest(_top_level(MCP, "mcp = []"))


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


def test_에이전트는_승인이_필요한_도구를_안_적으면_빈_목록이다() -> None:
    assert parse_manifest(AGENT).requires_approval == ()


def test_에이전트는_승인_없이는_부를_수_없는_도구_이름을_적는다() -> None:
    manifest = parse_manifest(AGENT + 'requires_approval = ["send_email"]\n')

    assert manifest.requires_approval == ("send_email",)


def test_에이전트가_아니면_승인_목록을_갖지_못한다() -> None:
    with pytest.raises(ValidationError):
        parse_manifest(_top_level(MCP, "requires_approval = []"))


def test_mcp_서버는_마스킹할_인자를_안_적으면_비어_있다() -> None:
    manifest = parse_manifest(MCP)

    assert manifest.server is not None
    assert manifest.server.secret_args == {}


def test_mcp_서버는_트레이스에_마스킹할_인자를_도구별로_적는다() -> None:
    manifest = parse_manifest(MCP + '\n[server.secret_args]\nsend_email = ["api_key"]\n')

    assert manifest.server is not None
    assert manifest.server.secret_args == {"send_email": ("api_key",)}


def _server(secret_args: str = "") -> McpServer:
    manifest = parse_manifest(MCP + secret_args)
    assert manifest.server is not None
    return manifest.server


def test_마스킹된_인자를_가진_도구는_승인_대상이_될_수_없다() -> None:
    agent = parse_manifest(AGENT + 'requires_approval = ["send_email", "read_inbox"]\n')
    servers = {PluginName("mailer"): _server('\n[server.secret_args]\nsend_email = ["api_key"]\n')}

    assert approval_conflicts(agent, servers) == ("send_email",)


def test_마스킹이_걸리지_않은_도구는_승인_대상이_될_수_있다() -> None:
    agent = parse_manifest(AGENT + 'requires_approval = ["read_inbox"]\n')
    servers = {PluginName("mailer"): _server('\n[server.secret_args]\nsend_email = ["api_key"]\n')}

    assert approval_conflicts(agent, servers) == ()


def test_승인_대상이_없으면_마스킹이_있어도_성립한다() -> None:
    agent = parse_manifest(AGENT)
    servers = {PluginName("mailer"): _server('\n[server.secret_args]\nsend_email = ["api_key"]\n')}

    assert approval_conflicts(agent, servers) == ()


def test_마스킹할_인자가_실제로_없으면_승인_대상이_될_수_있다() -> None:
    """빈 목록은 마스킹이 아니다. 복원할 수 없는 인자가 없으므로 금지의 근거가 없다."""
    agent = parse_manifest(AGENT + 'requires_approval = ["send_email"]\n')
    servers = {PluginName("mailer"): _server("\n[server.secret_args]\nsend_email = []\n")}

    assert approval_conflicts(agent, servers) == ()


# 저장소의 플러그인 디렉터리. 아래 테스트 하나만 디스크를 읽는다 — 재는 것이 코드가 아니라 저장소다.
REPO_PLUGINS = Path(__file__).resolve().parents[2] / "plugins"


def test_저장소의_매니페스트_중_secret_args_를_선언한_것이_없다() -> None:
    """관리 API 의 트레이스 상세가 마스킹되지 않은 이벤트를 내보내도 된다는 판단이 기댄 사실을
    불변식으로 바꾼다(ADR 0009 의 2026-09-22 이력). 처음 선언하는 날 이 테스트가 빨개지고, 그 순간이
    곧 열린 문제 셋을 닫을지 정해야 하는 순간이다. 막는 것은 선언이 아니라 결정 없이 지나가는
    것이고, 이 테스트를 지우는 것이 그 결정을 내리는 방법이다.

    파일마다 파싱하므로 읽히지 않는 매니페스트는 선언이 있는지 판정할 수 없어 여기서 함께 실패한다.
    mcp 매니페스트를 하나라도 읽었는지 보는 이유는 이 검사가 아무것도 읽지 않고 초록이 되는 길을
    막기 위해서다 — `secret_args` 는 mcp 에만 있다."""
    paths = sorted(REPO_PLUGINS.glob("*/*/plugin.toml"))
    manifests = [parse_manifest(path.read_text(encoding="utf-8")) for path in paths]
    declaring = [
        manifest.name
        for manifest in manifests
        if manifest.server is not None and manifest.server.secret_args
    ]

    assert any(manifest.kind is PluginKind.MCP for manifest in manifests), "mcp 를 읽지 않았다"
    assert declaring == []
