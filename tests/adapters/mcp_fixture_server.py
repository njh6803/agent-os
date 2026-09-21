"""테스트용 stdio MCP 서버. 네트워크도 Node 도 없이 어댑터를 진짜 서버에 물리기 위한 것.

`sys.executable 이 파일` 로 띄운다. add 는 성공, fail 은 isError 를 돌려준다.
"""

from mcp.server.fastmcp import FastMCP

server = FastMCP("fixture")


@server.tool()
def add(a: int, b: int) -> int:
    return a + b


@server.tool()
def fail(reason: str) -> str:
    raise ValueError(reason)


if __name__ == "__main__":
    server.run()
