"""검색 결과 하나가 모델 입력에서 차지하는 토큰 수를 가짜 서버와 실제 서버에서 같은 질의로 잰다(티켓
07).

    uv run --env-file <.env 경로> python \\
        .scratch/base-agent/probes/real_rag_engine/result_size.py \\
        <실제 서버 /mcp 주소> <Bearer 토큰 전체>

하는 일. 같은 질의 넷을 가짜 서버(시험 픽스처 `tests/fake_doc_search.py`를 빈 포트에 띄운다)와 실제
서버에 `search`로 보내, 도구 결과의 글(모델이 도구 결과로 받는 글)을 Anthropic의 토큰 세기
(`messages.count_tokens`, 모델 `claude-opus-5`)로 센다. 글 앞에 붙는 메시지 틀의 몫은 한 글자짜리
글의 세기를 빼서 덜어 낸다. 결과 수로 나눈 값이 "검색 결과 하나의 토큰 수"다.

표지. 서버마다 `search`가 성공했고(`is_error`가 거짓) 결과 글이 `format_version`과 비지 않은
`results`를 든 질의만 측정으로 센다. 표지가 없는 질의가 하나라도 있으면 종료 코드가
1이다(`tools/probe_kit.py`의 `Rounds`). 이 프로브는 모델의 답을 재지 않으므로 회차는 질의 하나다.
"""

from __future__ import annotations

import asyncio
import json
import sys
import tempfile
from pathlib import Path

import anthropic
import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO))

from tests.fake_doc_search import serving  # noqa: E402  저장소 루트를 경로에 넣은 뒤 가져온다
from tools.probe_kit import Rounds  # noqa: E402

MODEL = "claude-opus-5"
FAKE_AUTHORIZATION = "Bearer result-size-probe-token"
QUERIES = [
    "육아휴직은 최대 몇 년까지 쓸 수 있어?",
    "연차휴가는 며칠 주는지, 그리고 국내 출장 숙박비 상한은 얼마인지 알려줘",
    "출산 축하금은 얼마야?",
    "오늘 점심 메뉴 추천해줘",
]


async def search(url: str, authorization: str, query: str) -> tuple[bool, str]:
    """`search` 하나를 부른다. 오류 여부와 결과 글을 돌려준다."""
    # CPU 임베딩의 첫 검색이 5초를 넘을 수 있어 어댑터(`adapters/mcp.py`)와 같은 시간 제한을 준다.
    client = httpx2.AsyncClient(
        headers={"Authorization": authorization},
        timeout=httpx2.Timeout(30, read=300),
    )
    async with (
        streamable_http_client(url, http_client=client, terminate_on_close=False) as (read, write),
        ClientSession(read, write) as session,
    ):
        await session.initialize()
        result = await session.call_tool("search", {"query": query})
        text = "".join(getattr(block, "text", "") for block in result.content)
        return result.is_error, text


def count(client: anthropic.Anthropic, text: str) -> int:
    reply = client.messages.count_tokens(model=MODEL, messages=[{"role": "user", "content": text}])
    return reply.input_tokens


def results_of(text: str) -> list[object] | None:
    """표지: 결과 글이 `format_version`과 비지 않은 `results`를 들었으면 그 목록, 아니면 `None`."""
    try:
        body = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(body, dict) or "format_version" not in body:
        return None
    found = body.get("results")
    return found if isinstance(found, list) and found else None


def main() -> int:
    url, authorization = sys.argv[1], sys.argv[2]
    client = anthropic.Anthropic()
    frame = count(client, ".")
    rounds = Rounds()
    with (
        # 윈도에서는 끝난 가짜 서버가 stderr 파일을 잠시 쥐고 있어 폴더 지우기가 실패할 수 있다.
        tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as work,
        serving(Path(work), "--expect-authorization", FAKE_AUTHORIZATION) as fake,
    ):
        servers = {"가짜": (fake.url, FAKE_AUTHORIZATION), "실제": (url, authorization)}
        for query in QUERIES:
            line: list[str] = []
            with rounds.round(query) as current:
                measured = True
                for name, (address, token) in servers.items():
                    failed, text = asyncio.run(search(address, token, query))
                    found = results_of(text)
                    if failed or found is None:
                        measured = False
                        line.append(f"{name}: 표지 없음")
                        continue
                    tokens = count(client, text) - frame
                    line.append(
                        f"{name} 결과 {len(found)}개 {len(text)}자 {tokens}토큰"
                        f"(하나에 {tokens / len(found):.0f})"
                    )
                current.mark(measured=measured, result=" / ".join(line))
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
