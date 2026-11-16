"""도구 하나를 내는 작은 stdio MCP 서버. `loop_app.py` 의 `/mcp` 경로가 자식 프로세스로 띄운다.

서버의 이벤트 루프를 바꿨을 때 stdio MCP 서버를 띄우는 일이 그대로 되는지를 보는 데 쓴다. 저장소의
`tests/adapters/mcp_fixture_server.py` 와 같은 모양이다.
"""

from mcp.server.mcpserver import MCPServer

server = MCPServer("pg-stack-probe", log_level="ERROR")


@server.tool()
def ping() -> str:
    return "pong"


if __name__ == "__main__":
    server.run()
