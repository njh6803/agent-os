"""테스트용 stdio MCP 서버. 네트워크도 Node 도 없이 어댑터를 진짜 서버에 물리기 위한 것.

`sys.executable 이 파일` 로 띄운다. add 는 성공, fail 은 isError 를 돌려준다. blocks 는 글이 아닌
블록이 섞인 결과를 돌려준다.
"""

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import EmbeddedResource, ImageContent, TextContent, TextResourceContents

server = MCPServer("fixture")


@server.tool()
def add(a: int, b: int) -> int:
    return a + b


@server.tool()
def fail(reason: str) -> str:
    # mcp 2 의 MCPServer 는 ToolError 가 아닌 예외의 글을 서버 기록에만 남기고 클라이언트에는
    # 고정 문구를 보낸다. 사유가 결과에 실리게 ToolError 를 던진다(ADR 0034).
    raise ToolError(reason)


@server.tool()
def blocks() -> list[TextContent | ImageContent | EmbeddedResource]:
    """텍스트 블록 둘 사이에 이미지 블록과 텍스트 리소스가 낀 결과."""
    return [
        TextContent(type="text", text="앞"),
        ImageContent(type="image", data="AAAA", mime_type="image/png"),
        EmbeddedResource(
            type="resource",
            resource=TextResourceContents(uri="file:///note.txt", text="리소스"),
        ),
        TextContent(type="text", text="뒤"),
    ]


if __name__ == "__main__":
    server.run()
