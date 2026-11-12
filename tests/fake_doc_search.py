"""`tests/fake_doc_search_server.py`(가짜 문서 검색 서버)를 별도 프로세스로 띄우는 도우미. 플러그인
꾸러미 시험과 실제 모델 시험 같은, 문서 검색 서버가 필요한 시험이 붙는 도우미다
(`from tests.fake_doc_search import serving`). 꾸러미 시험과 프로브가 지금 쓴다.

띄우고 끄는 일은 원격 MCP 서버 픽스처(`tests/mcp_http.py`)의 `HttpFixture`가 한다. 서버는 루프백의
빈 포트에 뜨고, 프로세스는 이 도우미가 쥔 핸들로만 끈다. 이 모듈은 서버만 바꾸고, 도구 호출의 기록을
읽는 `tool_calls`를 더한다. 선택 인자는 서버 모듈의 독스트링이다.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from tests.mcp_http import HttpFixture

SERVER = Path(__file__).with_name("fake_doc_search_server.py")


class DocSearchFixture(HttpFixture):
    """뜬 가짜 검색 서버 하나. 받은 요청의 헤더(`headers_of`)와 도구 호출을 읽는다."""

    def __init__(self, folder: Path, *options: str) -> None:
        super().__init__(folder, *options, server=SERVER)

    def tool_calls(self) -> list[dict[str, object]]:
        """서버가 받은 도구 호출을 받은 순서로. 줄마다 name과 arguments(받은 그대로)다.

        끝 넘음 모드로 실패한 호출도 서버가 받은 것이라 든다."""
        return [
            {"name": row["tool"], "arguments": row["arguments"]}
            for row in self.requests()
            if "tool" in row
        ]


@contextmanager
def serving(folder: Path, *options: str) -> Generator[DocSearchFixture]:
    """서버를 띄워 포트가 열린 것을 본 뒤 내주고, 나갈 때 끈다."""
    fixture = DocSearchFixture(folder, *options)
    try:
        fixture.wait_ready()
        yield fixture
    finally:
        fixture.stop()
