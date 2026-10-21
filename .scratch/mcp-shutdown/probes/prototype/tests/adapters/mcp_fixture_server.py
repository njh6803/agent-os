"""테스트용 stdio MCP 서버. 네트워크도 Node 도 없이 어댑터를 진짜 서버에 물리기 위한 것.

`sys.executable 이 파일` 로 띄운다. add 는 성공, fail 은 isError 를 돌려준다.
"""

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

server = MCPServer("fixture")


@server.tool()
def add(a: int, b: int) -> int:
    return a + b


@server.tool()
def fail(reason: str) -> str:
    # mcp 2 의 MCPServer 는 ToolError 가 아닌 예외의 글을 서버 기록에만 남기고 클라이언트에는
    # 고정 문구를 보낸다. 사유가 결과에 실리게 ToolError 를 던진다.
    raise ToolError(reason)


if __name__ == "__main__":
    server.run()
