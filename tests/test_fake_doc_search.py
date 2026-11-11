"""가짜 문서 검색 서버 픽스처(`tests/fake_doc_search_server.py`, 띄우는 쪽은
`tests/fake_doc_search.py`)의 시험. 실제 MCP 클라이언트로 띄운 서버에 붙어, 문서 검색
서버(rag-engine)의 모양으로 답하는지 본다. 바깥 네트워크가 없다.

세션을 async 픽스처로 열지 않고 테스트 본문에서 `async with`로 연다(`.claude/rules/tests.md`의 MCP
항목). 서버 프로세스를 새로 띄우는 비용이 크므로 시험 하나가 서버 하나를 띄워 여러 호출을 본다.
"""

import json
import socket
import time
import uuid
from collections.abc import AsyncGenerator, Mapping
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TypeGuard

import httpx2
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from mcp.types import CallToolResult, TextContent
from tests.fake_doc_search import DocSearchFixture, serving
from tests.fake_doc_search_server import (
    DEFAULT_TEXT_MAX_CHARS,
    DOCUMENTS,
    FORMAT_VERSION,
    OVER_LIMIT,
    ErrorCode,
    RequestError,
    guarded,
)

CHILD_CARE_ID = "6f1c2a9e-4b7d-4e15-9c3a-2d8b7e5f0a11"
ANNUAL_LEAVE_ID = "2b9e4d7a-8c1f-4f3e-a2b6-5d0c9e8f1b22"
TRAVEL_ID = "9c4a1f6e-3d2b-4c8a-b5e7-7f1d2a3c4b33"
COMPANY_CAR_ID = "4e7b2c9d-6a1f-4d3b-9e8c-1a2b3c4d5e44"
AUTHORIZATION = "Bearer fixture-token-1111"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
# 창 상한을 작게 줘 785자 전문을 셋 이상의 창으로 나눈다(티켓 02, 명세의 표본).
SMALL_WINDOW = 320
# 끈 뒤 포트가 닫히기까지의 상한. 끈 직후에는 포트가 아직 열려 있을 수 있어(이 PC에서 한 번 봤다)
# 닫히기를 기한까지 기다리는 값이고, 다른 세션과 겹친 부하를 고려해 넉넉히 잡았다
# (`.claude/rules/tests.md`의 시간 단언).
CLOSED_WITHIN_SECONDS = 30


def _is_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _object(value: object) -> dict[str, object]:
    assert _is_object(value), f"객체가 아니다: {value!r}"
    return value


def _items(value: object) -> list[object]:
    assert _is_list(value), f"배열이 아니다: {value!r}"
    return value


@asynccontextmanager
async def _session(
    fixture: DocSearchFixture, headers: Mapping[str, str] | None = None
) -> AsyncGenerator[ClientSession]:
    client = httpx2.AsyncClient(headers=dict(headers or {}), timeout=httpx2.Timeout(30, read=60))
    try:
        async with (
            streamable_http_client(fixture.url, http_client=client) as (read, write),
            ClientSession(read, write) as session,
        ):
            await session.initialize()
            yield session
    finally:
        await client.aclose()


def _text(result: CallToolResult) -> str:
    block = result.content[0]
    assert isinstance(block, TextContent), f"글이 아니다: {block!r}"
    return block.text


def _structured(result: CallToolResult) -> dict[str, object]:
    assert not result.is_error, _text(result)
    return _object(result.structured_content)


def _problem(result: CallToolResult) -> dict[str, object]:
    """실패 결과의 글을 Problem Details로 읽는다. 글이 JSON으로 시작하지 않으면 여기서 빨개진다."""
    assert result.is_error, f"실패 결과가 아니다: {_text(result)}"
    text = _text(result)
    assert text.startswith("{"), f"JSON으로 시작하지 않는다: {text!r}"
    return _object(json.loads(text))


async def _search(
    session: ClientSession, query: str, **arguments: object
) -> list[dict[str, object]]:
    result = await session.call_tool("search", {"query": query, **arguments})
    return [_object(item) for item in _items(_structured(result)["results"])]


async def _document(
    session: ClientSession, document_id: str, **arguments: object
) -> CallToolResult:
    return await session.call_tool("get_document", {"document_id": document_id, **arguments})


async def test_도구_셋과_출력_스키마와_판이_실제_서버의_모양이다(tmp_path: Path) -> None:
    with serving(tmp_path) as fixture:
        async with _session(fixture) as session:
            tools = {tool.name: tool for tool in (await session.list_tools()).tools}
            assert set(tools) == {"search", "get_document", "list_knowledge_bases"}
            for tool in tools.values():
                assert tool.output_schema is not None, tool.name
                assert tool.annotations is not None
                assert tool.annotations.read_only_hint is True
            assert set(tools["search"].input_schema["required"]) == {"query"}
            assert set(tools["search"].input_schema["properties"]) == {
                "query",
                "top_k",
                "knowledge_base",
                "filter",
            }
            assert tools["get_document"].input_schema["required"] == ["document_id"]
            assert set(tools["get_document"].input_schema["properties"]) == {
                "document_id",
                "include_text",
                "offset",
                "max_chars",
            }
            assert f"1부터 {DEFAULT_TEXT_MAX_CHARS}까지" in (
                tools["get_document"].description or ""
            )

            result = await session.call_tool("list_knowledge_bases", {})
            listed = _structured(result)
            assert listed["format_version"] == FORMAT_VERSION
            assert listed["knowledge_bases"] == [
                {
                    "name": "default",
                    "description": "표본",
                    "document_count": len(DOCUMENTS),
                    "is_default": True,
                }
            ]
            # 결과 글은 띄어쓰기 없는 JSON 하나이고 structured content와 같은 내용이다.
            text = _text(result)
            assert text == json.dumps(json.loads(text), separators=(",", ":"), ensure_ascii=False)
            assert json.loads(text) == listed


async def test_창_상한을_줄이면_도구_설명_글의_수도_따른다(tmp_path: Path) -> None:
    with serving(tmp_path, "--text-max-chars", str(SMALL_WINDOW)) as fixture:
        async with _session(fixture) as session:
            tools = {tool.name: tool for tool in (await session.list_tools()).tools}
            description = tools["get_document"].description or ""
            assert f"1부터 {SMALL_WINDOW}까지" in description
            assert f"주지 않으면 {SMALL_WINDOW}다" in description
            assert str(DEFAULT_TEXT_MAX_CHARS) not in description


async def test_검색은_질문이_무엇이든_조각을_top_k개_돌려주고_점수는_높은_순이다(
    tmp_path: Path,
) -> None:
    with serving(tmp_path) as fixture:
        async with _session(fixture) as session:
            found = await _search(session, "육아휴직 급여는 얼마인가")
            assert len(found) == 7  # 표본의 조각은 일곱이고 기본 top_k는 10이다
            assert [item["rank"] for item in found] == list(range(1, 8))
            scores = [float(str(item["score"])) for item in found]
            assert scores == sorted(scores, reverse=True)
            assert found[0]["title"] == "육아휴직 업무편람"
            assert "통상임금의 80퍼센트" in str(found[0]["text"])

            assert len(await _search(session, "육아휴직", top_k=3)) == 3
            # 무관한 질문에도 점수가 낮은 조각이 온다. 관련 없음의 판단은 모델에 남는다.
            unrelated = await _search(session, "zzzz qqqq")
            assert len(unrelated) == 7
            assert all(float(str(item["score"])) < 0.1 for item in unrelated)


async def test_조각의_위치는_형식마다_실제처럼_온다(tmp_path: Path) -> None:
    with serving(tmp_path) as fixture:
        async with _session(fixture) as session:
            found = await _search(session, "휴가 출장 차량 육아휴직")
            by_key: dict[str, list[dict[str, object]]] = {}
            for item in found:
                by_key.setdefault(str(item["key"]), []).append(_object(item["location"]))

            pdf_pages = [str(location["page"]) for location in by_key["annual-leave.pdf"]]
            assert sorted(pdf_pages) == ["3", "5"], f"PDF 조각의 쪽이 3과 5가 아니다: {pdf_pages}"
            for key in ("annual-leave.pdf", "travel-expense.pdf"):
                for location in by_key[key]:
                    assert location["page"] is not None, f"PDF 조각에 쪽이 없다: {key}"
                    assert location["section"] == []
                    assert location["block_kind"] == "paragraph"

            docx = by_key["parental-leave.docx"]
            assert len(docx) == 3
            for location in docx:
                assert location["page"] is None
            assert sorted(json.dumps(loc["section"], ensure_ascii=False) for loc in docx) == sorted(
                json.dumps(path, ensure_ascii=False)
                for path in (
                    ["제2장 육아휴직", "2.1 휴직 기간"],
                    ["제2장 육아휴직", "2.3 신청 절차"],
                    ["제2장 육아휴직", "2.4 급여"],
                )
            )

            hwpx = by_key["company-car.hwpx"]
            assert hwpx[0]["page"] is None
            assert hwpx[0]["section"] == ["제1장 총칙", "1.1 목적"]


async def test_전문_창은_include_text가_참일_때만_오고_text_length는_늘_온다(
    tmp_path: Path,
) -> None:
    with serving(tmp_path) as fixture:
        async with _session(fixture) as session:
            without = _structured(await _document(session, CHILD_CARE_ID))
            assert without["format_version"] == FORMAT_VERSION
            assert without["text"] is None, (
                f"include_text가 거짓인데 창이 왔다: {without['text']!r}"
            )
            assert without["next_offset"] is None
            assert isinstance(without["text_length"], int)
            assert without["mime"] == DOCX_MIME
            assert without["chunk_counts"] == {"default": 3}

            with_text = _structured(await _document(session, CHILD_CARE_ID, include_text=True))
            assert with_text["text_length"] == without["text_length"]
            assert isinstance(with_text["text"], str)
            assert with_text["next_offset"] is None
            assert len(with_text["text"]) == with_text["text_length"]


async def test_전문의_모양은_문서마다_넷이다(tmp_path: Path) -> None:
    with serving(tmp_path) as fixture:
        async with _session(fixture) as session:
            # 1. 제목 줄이 든 DOCX 전문. 복직 절차의 "7일"은 조각에 없고 전문에만 있다.
            docx = _structured(await _document(session, CHILD_CARE_ID, include_text=True))
            docx_text = str(docx["text"])
            assert "# 제2장 육아휴직" in docx_text
            assert "\n\n## 2.6 복직 절차\n\n" in docx_text
            assert "7일" in docx_text
            for item in await _search(session, "복직 절차 7일", top_k=50):
                assert "복직" not in str(item["text"])

            # 2. 제목 줄이 없는 PDF 전문. 해외 일비 "60달러"는 전문에만 있다.
            pdf = _structured(await _document(session, TRAVEL_ID, include_text=True))
            pdf_text = str(pdf["text"])
            assert not any(line.startswith("#") for line in pdf_text.splitlines())
            assert "60달러" in pdf_text
            for item in await _search(session, "해외 출장 일비 60달러", top_k=50):
                assert "60달러" not in str(item["text"])

            # 3. 비어 오는 전문. 칸 셋이 모두 null이다.
            empty = _structured(await _document(session, ANNUAL_LEAVE_ID, include_text=True))
            assert (empty["text_length"], empty["text"], empty["next_offset"]) == (None, None, None)

            # 4. 한 창보다 긴 전문은 아래 창 시험이 본다.
            car = _structured(await _document(session, COMPANY_CAR_ID))
            assert car["text_length"] == 785


async def test_긴_전문은_블록_경계에서_잘린_창으로_이어_읽는다(tmp_path: Path) -> None:
    with serving(tmp_path, "--text-max-chars", str(SMALL_WINDOW)) as fixture:
        async with _session(fixture) as session:
            windows: list[str] = []
            offset = 0
            length = 0
            while True:
                result = _structured(
                    await _document(session, COMPANY_CAR_ID, include_text=True, offset=offset)
                )
                length = int(str(result["text_length"]))
                window = str(result["text"])
                assert 0 < len(window) <= SMALL_WINDOW
                windows.append(window)
                next_offset = result["next_offset"]
                if next_offset is None:
                    break
                assert isinstance(next_offset, int)
                assert next_offset == offset + len(window)
                offset = next_offset
            assert len(windows) == 3
            # 창은 블록 경계에서 잘려, 다음 창이 블록 사이의 빈 줄에서 시작한다.
            starts = [window[:2] for window in windows[1:]]
            assert starts == ["\n\n"] * len(starts), f"창이 블록 경계에서 잘리지 않았다: {starts!r}"
            assert sum(len(window) for window in windows) == length
            # "최대 4일"은 첫 창에만, "35만원"은 셋째 창에만 있다.
            assert ["최대 4일" in window for window in windows] == [True, False, False]
            assert ["35만원" in window for window in windows] == [False, False, True]
            # 제목 블록과 그 아래 문단은 서로 다른 블록이라 첫 창이 제목 줄로 끝날 수 있다.
            assert windows[0].startswith("# 제1장 총칙")

            # 마지막 창은 next_offset이 null이고, 작게 준 max_chars도 따른다.
            small = _structured(
                await _document(session, COMPANY_CAR_ID, include_text=True, max_chars=50)
            )
            assert len(str(small["text"])) <= 50
            assert small["next_offset"] is not None


async def test_입력이_틀리면_invalid_argument와_not_found의_Problem_Details를_낸다(
    tmp_path: Path,
) -> None:
    with serving(tmp_path) as fixture:
        async with _session(fixture) as session:
            invalid_calls: list[tuple[str, dict[str, object]]] = [
                ("search", {"query": "   "}),
                ("search", {"query": "휴가", "top_k": 0}),
                ("search", {"query": "휴가", "top_k": 51}),
                ("search", {"query": "휴가", "filter": {"updated_after": "2026-01-01T00:00:00"}}),
                ("search", {"query": "휴가", "filter": {"updated_before": "어제"}}),
                ("get_document", {"document_id": "not-a-uuid"}),
                ("get_document", {"document_id": CHILD_CARE_ID, "max_chars": 0}),
                ("get_document", {"document_id": CHILD_CARE_ID, "max_chars": 20001}),
                ("get_document", {"document_id": CHILD_CARE_ID, "offset": -1}),
                (
                    "get_document",
                    {"document_id": CHILD_CARE_ID, "include_text": True, "offset": 99999},
                ),
            ]
            for name, arguments in invalid_calls:
                problem = _problem(await session.call_tool(name, arguments))
                assert problem["code"] == "invalid_argument", (name, arguments)
                assert problem["status"] == 422
                assert problem["title"] == "입력이 올바르지 않다"
                assert problem["type"] == "about:blank"
                assert "detail" not in problem
                uuid.UUID(str(problem["request_id"]))

            kb = _problem(
                await session.call_tool("search", {"query": "휴가", "knowledge_base": "other"})
            )
            assert (kb["code"], kb["status"]) == ("knowledge_base_not_found", 404)

            missing = _problem(await _document(session, str(uuid.uuid4())))
            assert (missing["code"], missing["status"]) == ("document_not_found", 404)

            # include_text가 거짓이면 전문이 없는 문서에서 offset이 길이를 넘어도 오류가 아니다.
            ok = await _document(session, CHILD_CARE_ID, offset=99999)
            assert not ok.is_error


def test_예상하지_못한_예외는_internal_error의_실패_결과가_된다() -> None:
    def explode() -> CallToolResult:
        raise ValueError("비밀 값이 든 메시지")

    result = guarded(explode)
    assert result.is_error
    problem = _object(json.loads(_text(result)))
    assert (problem["code"], problem["status"]) == ("internal_error", 500)
    assert problem["title"] == "서버 내부 오류"
    # 예외의 글은 결과에 싣지 않는다.
    assert "비밀 값" not in _text(result)

    def reject() -> CallToolResult:
        raise RequestError(ErrorCode.SEARCH_UNAVAILABLE)

    assert _object(json.loads(_text(guarded(reject))))["code"] == "search_unavailable"


async def test_검색_실패_모드는_search_unavailable로_실패하되_다른_도구는_산다(
    tmp_path: Path,
) -> None:
    with serving(tmp_path, "--search-down") as fixture:
        async with _session(fixture) as session:
            down = _problem(await session.call_tool("search", {"query": "휴가"}))
            assert (down["code"], down["status"]) == ("search_unavailable", 503)
            # 입력 검증이 먼저다. 빈 질의는 서버가 내려가 있어도 invalid_argument다.
            bad = _problem(await session.call_tool("search", {"query": " "}))
            assert bad["code"] == "invalid_argument"
            assert not (await _document(session, CHILD_CARE_ID)).is_error


async def test_끝_넘음_모드는_N번째_뒤의_호출을_런타임의_문구로_실패시킨다(tmp_path: Path) -> None:
    with serving(tmp_path, "--tool-cap", "2") as fixture:
        async with _session(fixture) as session:
            assert not (await session.call_tool("search", {"query": "휴가"})).is_error
            assert not (await session.call_tool("list_knowledge_bases", {})).is_error
            over = await session.call_tool("search", {"query": "휴가"})
            assert over.is_error
            assert _text(over) == OVER_LIMIT.format(limit=2), (
                f"끝 넘음 문구가 아니다: {_text(over)}"
            )
            assert _text(over) == "도구 호출 횟수를 넘었다: 이 실행은 도구를 2번까지 부른다"
            again = await _document(session, CHILD_CARE_ID)
            assert again.is_error
            assert _text(again) == OVER_LIMIT.format(limit=2)
        # 서버는 호출을 받은 것으로 센다. 넘은 호출도 기록에 남는다.
        assert len(fixture.tool_calls()) == 4


async def test_빈_색인_모드는_검색이_빈_results를_내고_조각_수가_0이다(tmp_path: Path) -> None:
    with serving(tmp_path, "--empty-index") as fixture:
        async with _session(fixture) as session:
            result = _structured(await session.call_tool("search", {"query": "육아휴직"}))
            assert result["format_version"] == FORMAT_VERSION
            assert result["knowledge_base"] == "default"
            assert result["results"] == []
            document = _structured(await _document(session, CHILD_CARE_ID))
            assert document["chunk_counts"] == {"default": 0}
            # 입력 검증은 빈 색인에서도 먼저 돈다.
            assert (
                _problem(await session.call_tool("search", {"query": " "}))["code"]
                == "invalid_argument"
            )


async def test_기대한_Authorization이_아니면_401로_막고_맞으면_통과한다(tmp_path: Path) -> None:
    with serving(tmp_path, "--expect-authorization", AUTHORIZATION) as fixture:
        initialize = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "probe", "version": "0"},
            },
        }
        accept = {"accept": "application/json, text/event-stream"}
        async with httpx2.AsyncClient(timeout=30) as http:
            missing = await http.post(fixture.url, json=initialize, headers=accept)
            wrong = await http.post(
                fixture.url, json=initialize, headers={**accept, "authorization": "Bearer other"}
            )
            right = await http.post(
                fixture.url, json=initialize, headers={**accept, "authorization": AUTHORIZATION}
            )
        statuses = (missing.status_code, wrong.status_code)
        assert statuses == (401, 401), f"틀린 Authorization을 막지 않았다: {statuses}"
        assert right.status_code == 200

        async with _session(fixture, {"Authorization": AUTHORIZATION}) as session:
            assert not (await session.call_tool("list_knowledge_bases", {})).is_error
        # 막힌 요청도 기록에 남는다. 서버에 닿은 헤더를 시험이 읽는다.
        received = [h.get("authorization") for h in fixture.headers_of("POST")]
        assert received[:3] == [None, "Bearer other", AUTHORIZATION]
        assert received.count(AUTHORIZATION) >= 2


async def test_받은_요청의_헤더와_도구_호출의_이름과_인자를_시험이_읽는다(tmp_path: Path) -> None:
    with serving(tmp_path) as fixture:
        async with _session(fixture, {"Authorization": AUTHORIZATION, "X-Probe": "yes"}) as session:
            await session.call_tool("search", {"query": "휴가", "top_k": 2})
            await _document(session, CHILD_CARE_ID, include_text=True)
            await _document(session, TRAVEL_ID)
        calls = fixture.tool_calls()
        assert [call["name"] for call in calls] == ["search", "get_document", "get_document"]
        assert calls[0]["arguments"] == {"query": "휴가", "top_k": 2}
        assert calls[1]["arguments"] == {"document_id": CHILD_CARE_ID, "include_text": True}
        assert calls[2]["arguments"] == {"document_id": TRAVEL_ID}
        # 초기화 요청이 서버에 닿았고 그 헤더에 시험이 준 값이 있다.
        posts = fixture.headers_of("POST")
        assert posts
        assert all(h.get("authorization") == AUTHORIZATION for h in posts)
        assert all(h.get("x-probe") == "yes" for h in posts)
        # 도구 호출이 아닌 요청(initialize 등)은 도구 호출의 기록에 들지 않는다.
        assert len(fixture.requests()) > len(calls)


async def test_띄운_쪽이_핸들로_끄면_포트가_닫힌다(tmp_path: Path) -> None:
    with serving(tmp_path) as fixture:
        port = fixture.port
        assert _listening(port)
        assert fixture.url == f"http://127.0.0.1:{port}/mcp"
    # 윈도의 venv 파이썬은 실행기가 진짜 파이썬을 자식으로 띄운다. 리뷰 서브에이전트가 이 PC에서
    # 프로세스 트리를 읽어 확인했고(2026-11-11, 실행기 아래에 진짜 인터프리터가 자식으로 있었고
    # `terminate()` 뒤 3초 안에 사라졌다), 끈 직후 포트가 열려 있는 것은 이 PC에서 한 번 봤다.
    # 그래서 끝나기를 한 번만 견주지 않고 기한까지 거듭 견준다.
    end = time.monotonic() + CLOSED_WITHIN_SECONDS
    while _listening(port) and time.monotonic() < end:
        time.sleep(0.1)
    assert not _listening(port), f"{CLOSED_WITHIN_SECONDS}초 뒤에도 포트 {port}가 열려 있다"


def _listening(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False
