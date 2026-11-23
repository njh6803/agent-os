"""MCP ToolSource. 파이썬으로 쓴 진짜 stdio 서버(mcp_fixture_server.py)와 루프백의 streamable HTTP
서버(`tests/mcp_http_server.py`, 띄우는 도우미는 `tests/mcp_http.py`)에 붙는다. 바깥 네트워크가
없다.

세션을 async 픽스처로 열지 않는다. pytest-asyncio 가 픽스처의 setup 과 teardown 을 다른 태스크에서
돌리는데 MCP 의 stdio 클라이언트는 anyio 취소 범위라 같은 태스크에서 닫혀야 한다(ADR 0007 이력).
그래서 테스트 본문에서 async with 로 열고 닫는다.

닫기 절(ADR 0034)은 가짜 프로세스(`mcp_lingering.py`)가 살아 있는지를 하트비트로 본다. 프로세스마다
0.1초에 1바이트씩 파일에 쓰고, 닫은 뒤 그 파일이 1초 동안 자라지 않으면 멈춘 것이다. 프로세스
번호로 살아 있는지 묻지 않는다. 끝난 프로세스의 번호는 다른 프로세스가 다시 쓰고, 감싼 프로세스
아래 서버의 번호는 클라이언트가 모른다. 대가로 멈춰 있지만 살아 있는 프로세스(쓰기가 막힌 것, 일시
정지된 것)는 멈춘 것으로 보인다. 남은 것은 테스트가 끝날 때 멈춤 파일로 끝내고, 그것도 놓치면 120초
뒤 스스로 끝난다.
"""

import logging
import socket
import subprocess
import sys
import time
import traceback
from collections.abc import AsyncGenerator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path

import anyio
import pytest
from tests.mcp_http import free_port, serving

from agent_os.adapters.mcp import REMOTE_CHECK_SECONDS, STDIO_CHECK_SECONDS, McpTools
from agent_os.core.ports import Reached, ToolConnection, ToolSource, Unreached
from agent_os.sdk import HttpServer, PluginName, StdioServer

FIXTURE = StdioServer(
    command=sys.executable, args=(str(Path(__file__).with_name("mcp_fixture_server.py")),)
)
# 가짜 프로세스. 테스트는 importlib 모드라 같은 폴더의 모듈을 import 하지 못해 경로와 파일 이름으로
# 가리킨다. 하트비트는 `<역할>.hb`, 멈춤 파일은 `stop` 이다(그 모듈의 독스트링).
LINGERING = Path(__file__).with_name("mcp_lingering.py")
STOP = "stop"
PAGED = Path(__file__).with_name("mcp_paged_server.py")
# 쪽 나눔 사례의 기한. 커서를 끝까지 따르지 못하는 어댑터는 같은 쪽을 끝없이 물어 기한이 없으면
# 멈춘다. 끝없는 목록 사례(1000쪽)는 명세의 시제품이 Windows 에서 홀로 2.5~2.9초, 두 OS 를 함께 돈
# 회차에 6.13초였다(`.claude/rules/tests.md` 의 시간 단언).
PAGED_WITHIN_SECONDS = 30
# 가짜 프로세스가 뜨고 하트비트가 생기기까지의 상한. 파이썬을 두세 번 띄운다. 다른 세션의 테스트와
# 겹친 부하(CPU 86%)에서 홀로 돈 명세의 시제품 사례 하나가 12.5초 걸렸고, 20초로 두던 판은 전체
# 회차에서 그 기다림을 넘겼다(`.claude/rules/tests.md` 의 시간 단언).
APPEAR_WITHIN_SECONDS = 30
# 사례 5의 상한. 그 자식은 새 파이썬에서 어댑터와 mcp 를 불러 들인 뒤에야 연결을 연다. 이 PC 에서
# 홀로 연결 표지까지 9.8~12.3초였고(하트비트 둘은 그보다 먼저 생겼다), 30초로 두던 판은 pre-commit
# 러너의 부하에서 표지 셋이 모두 생기기 전에 그 기다림을 넘겼다(일지 2026-10-21-14, 손으로 봤다).
CONNECT_WITHIN_SECONDS = 120
# 닫은 뒤 하트비트가 멈추기를 기다리는 기한. 판정의 꼴은 `_멈췄다` 다.
STOP_WITHIN_SECONDS = 15


@asynccontextmanager
async def _fixture_connection() -> AsyncGenerator[ToolConnection]:
    tools: ToolSource = McpTools()
    async with tools.connect({PluginName("fixture"): FIXTURE}) as connection:
        yield connection


async def test_서버의_도구_목록과_입력_스키마를_준다() -> None:
    async with _fixture_connection() as connection:
        specs = {spec.name: spec for spec in connection.tools()}

    assert set(specs) == {"add", "fail", "blocks"}
    properties = specs["add"].input_schema["properties"]
    assert isinstance(properties, dict)
    assert set(properties) == {"a", "b"}


async def test_도구_명세는_그_도구를_낸_서버_플러그인의_이름을_든다() -> None:
    """서버 하나만 여는 양성 대조이기도 하다. 겹치는 이름이 없으면 그대로 열린다."""
    async with _fixture_connection() as connection:
        servers = {spec.name: spec.server for spec in connection.tools()}

    assert servers == {
        "add": PluginName("fixture"),
        "fail": PluginName("fixture"),
        "blocks": PluginName("fixture"),
    }


async def test_같은_이름의_도구를_낸_서버_둘은_두_서버_이름을_든_값_오류다() -> None:
    """같은 픽스처 서버를 두 플러그인 이름으로 열어 같은 이름을 만든다. 예외는 예외 그룹이 아니라
    정한 내장 타입 그대로 나와야 한다. 앞서 연 서버의 태스크 그룹이 그것을 감싸는 길을 문맥이
    벗기는지를 이 단언이 잰다."""
    tools: ToolSource = McpTools()
    servers = {PluginName("first"): FIXTURE, PluginName("second"): FIXTURE}

    message = r"같은 이름의 도구가 둘이다: \w+ \(first, second\)"
    with pytest.raises(ValueError, match=message) as raised:
        async with tools.connect(servers):
            pytest.fail("겹친 연결이 열렸다")

    assert type(raised.value) is ValueError


async def test_겹친_서버_뒤의_서버는_열리지_않는다() -> None:
    """셋째 서버는 띄울 수 없는 명령이다. 열렸다면 ConnectionError 가 났을 것이다."""
    tools: ToolSource = McpTools()
    broken = StdioServer(command="definitely-not-a-command-agent-os")
    servers = {
        PluginName("first"): FIXTURE,
        PluginName("second"): FIXTURE,
        PluginName("third"): broken,
    }

    with pytest.raises(ValueError, match=r"\(first, second\)") as raised:
        async with tools.connect(servers):
            pytest.fail("겹친 연결이 열렸다")

    assert type(raised.value) is ValueError


async def test_도구를_부르면_결과_텍스트가_온다() -> None:
    async with _fixture_connection() as connection:
        result = await connection.call("add", {"a": 2, "b": 3})

    assert result.ok is True
    assert result.content == "5"


async def test_결과의_글은_텍스트_블록과_텍스트_리소스를_차례로_이어_붙인_것이다() -> None:
    """이미지 블록은 글에 들지 않는다."""
    async with _fixture_connection() as connection:
        result = await connection.call("blocks", {})

    assert result.ok is True
    assert result.content == "앞리소스뒤"


async def test_도구가_에러를_내면_실패로_표시되고_에러_내용이_온다() -> None:
    async with _fixture_connection() as connection:
        result = await connection.call("fail", {"reason": "overflow"})

    assert result.ok is False
    assert "overflow" in result.content


async def test_없는_도구는_에러다() -> None:
    async with _fixture_connection() as connection:
        with pytest.raises(LookupError, match="nope"):
            await connection.call("nope", {})


async def test_서버_기동_실패는_서버_이름과_명령을_든_연결_오류다() -> None:
    tools: ToolSource = McpTools()
    broken = StdioServer(command="definitely-not-a-command-agent-os")

    with pytest.raises(
        ConnectionError, match="broken.*definitely-not-a-command-agent-os"
    ) as raised:
        async with tools.connect({PluginName("broken"): broken}):
            pass
    assert isinstance(raised.value.__cause__, FileNotFoundError)


# --- 원격 서버(streamable HTTP, ADR 0049) ---

REMOTE = PluginName("remote")
TOKEN_VARIABLE = "AGENT_OS_TEST_TOKEN"
SECOND_VARIABLE = "AGENT_OS_TEST_SECOND"
# 서버가 되울릴 수 있는 비밀과 쿼리 문자열의 비밀. 둘 다 8자 이상이라 가리는 대상이다.
TOKEN = "echo-secret-9f3a"
QUERY_SECRET = "query-secret-4b9d"
# 기한이 도구 호출 도중에 오게 하는 사례의 기한. 서버가 호출을 받은 뒤여야 해서 1초보다 넉넉히 둔다.
DEADLINE_SECONDS = 2
# 종료 요청에 답하지 않는 서버의 닫기. 어댑터의 유예는 2초이고 홀로 돌려 2초 남짓이었다. 하한은
# 유예가 걸렸는지 보고, 상한은 `.claude/rules/tests.md` 의 시간 단언대로 그 몇 배다.
GRACE_FLOOR_SECONDS = 1.8
GRACE_CEILING_SECONDS = 15.0


def _remote(url: str, **headers: str) -> HttpServer:
    """헤더 인자는 헤더 이름 -> 환경 변수 이름이다. 파이썬 이름에 못 쓰는 `-` 는 `_` 로 적는다."""
    return HttpServer(
        transport="http",
        url=url,
        headers={name.replace("_", "-"): variable for name, variable in headers.items()},
    )


def _traceback_text(error: BaseException) -> str:
    return "".join(traceback.format_exception(error))


async def test_원격_서버의_도구가_stdio_서버의_도구와_같은_연결에_서고_서버_이름이_실린다(
    tmp_path: Path,
) -> None:
    """두 서버 가운데 하나가 http 여도 `ToolSpec.server` 는 그 도구를 낸 서버 플러그인의
    이름이다."""
    with serving(tmp_path) as fixture:
        servers = {**_paged("empty"), REMOTE: _remote(fixture.url)}
        async with McpTools().connect(servers) as connection:
            owners = {spec.name: spec.server for spec in connection.tools()}
            result = await connection.call("add", {"a": 2, "b": 3})

    assert owners == {
        "paged": PluginName("paged"),
        "add": REMOTE,
        "slow": REMOTE,
        "keep": REMOTE,
    }
    assert result.ok is True
    assert result.content == "5"


async def test_헤더_변수의_값이_서버의_요청_헤더에_닿고_빈_값도_그대로_닿는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(TOKEN_VARIABLE, f"Bearer {TOKEN}")
    monkeypatch.setenv(SECOND_VARIABLE, "")

    with serving(tmp_path) as fixture:
        remote = _remote(fixture.url, Authorization=TOKEN_VARIABLE, X_Empty=SECOND_VARIABLE)
        async with McpTools().connect({REMOTE: remote}) as connection:
            await connection.call("add", {"a": 1, "b": 1})
        posted = fixture.headers_of("POST")

    assert posted
    assert all(headers["authorization"] == f"Bearer {TOKEN}" for headers in posted)
    assert all(headers["x-empty"] == "" for headers in posted)


async def test_헤더_변수가_없으면_붙지_않고_문구가_헤더_이름과_변수_이름을_든다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(TOKEN_VARIABLE, raising=False)
    monkeypatch.setenv(SECOND_VARIABLE, "present")

    with serving(tmp_path) as fixture:
        remote = _remote(fixture.url, Authorization=TOKEN_VARIABLE, X_Other=SECOND_VARIABLE)
        with pytest.raises(ConnectionError) as raised:
            async with McpTools().connect({REMOTE: remote}):
                pytest.fail("헤더 변수가 없는데 열렸다")
        reached = fixture.requests()

    expected = (
        f"MCP 서버 remote({fixture.url})에 붙지 못했다: "
        f"헤더 Authorization의 환경 변수 {TOKEN_VARIABLE}이 없다"
    )
    assert str(raised.value) == expected
    assert reached == [], "변수가 없는데 서버에 붙었다"


async def test_변수가_둘_없으면_둘을_매니페스트_순서로_잇는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv(TOKEN_VARIABLE, raising=False)
    monkeypatch.delenv(SECOND_VARIABLE, raising=False)

    remote = _remote(f"http://127.0.0.1:{free_port()}/mcp", X_B=SECOND_VARIABLE, X_A=TOKEN_VARIABLE)
    with pytest.raises(ConnectionError) as raised:
        async with McpTools().connect({REMOTE: remote}):
            pytest.fail("헤더 변수가 없는데 열렸다")

    assert str(raised.value).endswith(
        f": 헤더 X-B의 환경 변수 {SECOND_VARIABLE}이 없다; "
        f"헤더 X-A의 환경 변수 {TOKEN_VARIABLE}이 없다"
    )


async def test_끝에_개행이_붙은_값은_붙지_않고_값은_어디에도_남지_않는다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """파일에서 읽은 비밀의 끝에는 개행이 흔히 붙는다. 라이브러리가 그 값을 글에 실어 거부하므로
    라이브러리에 넘기기 전에 막는다."""
    monkeypatch.setenv(TOKEN_VARIABLE, f"Bearer {TOKEN}\n")

    remote = _remote(f"http://127.0.0.1:{free_port()}/mcp", Authorization=TOKEN_VARIABLE)
    with pytest.raises(ConnectionError) as raised:
        async with McpTools().connect({REMOTE: remote}):
            pytest.fail("개행이 든 값으로 열렸다")

    assert str(raised.value).endswith(
        f": 헤더 Authorization의 환경 변수 {TOKEN_VARIABLE}의 값에 "
        "헤더 값으로 쓸 수 없는 글자가 있다"
    )
    assert TOKEN not in _traceback_text(raised.value)


@pytest.mark.parametrize("value", [f" {TOKEN}", f"{TOKEN} ", f"\t{TOKEN}", f"{TOKEN}\t", "ab "])
async def test_앞뒤에_공백이나_탭이_붙은_값은_붙지_않고_거부_글에도_실리지_않는다(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    """라이브러리는 앞뒤의 공백과 탭이 든 값을 그 값을 실은 예외로 거부한다. 8자보다 짧은 값은
    가림도 닿지 않으므로 라이브러리에 넘기기 전에 막는다."""
    monkeypatch.setenv(TOKEN_VARIABLE, value)

    remote = _remote(f"http://127.0.0.1:{free_port()}/mcp", Authorization=TOKEN_VARIABLE)
    with pytest.raises(ConnectionError) as raised:
        async with McpTools().connect({REMOTE: remote}):
            pytest.fail("앞뒤에 공백이나 탭이 든 값으로 열렸다")

    assert str(raised.value).endswith(
        f": 헤더 Authorization의 환경 변수 {TOKEN_VARIABLE}의 값에 "
        "헤더 값으로 쓸 수 없는 글자가 있다"
    )
    assert "Illegal header value" not in _traceback_text(raised.value)


async def test_꺼진_서버의_문구는_이름과_쿼리_문자열이_든_주소_그대로이고_비밀은_글과_로그에_없다(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setenv(TOKEN_VARIABLE, f"Bearer {TOKEN}")
    caplog.set_level(logging.WARNING)
    url = f"http://127.0.0.1:{free_port()}/mcp?token={QUERY_SECRET}#frag"

    with pytest.raises(ConnectionError, match=r"^MCP 서버 remote\(") as raised:
        async with McpTools().connect({REMOTE: _remote(url, Authorization=TOKEN_VARIABLE)}):
            pytest.fail("닫힌 포트에 열렸다")

    assert str(raised.value).startswith(f"MCP 서버 remote({url})에 붙지 못했다: ")
    assert "ConnectError" in str(raised.value)
    assert TOKEN not in _traceback_text(raised.value)
    # 라이브러리가 자기 태스크 그룹을 취소하며 남긴 취소가 문맥에 남으면 core 가 이 실패를 기한이나
    # 바깥의 취소로 읽는다(core 시험이 그 결과를 재고, 여기는 원인을 고정한다).
    chain: list[BaseException] = []
    link: BaseException | None = raised.value
    while link is not None and link not in chain:
        chain.append(link)
        link = link.__context__
    assert not any(isinstance(link, anyio.get_cancelled_exc_class()) for link in chain)
    # 지금의 구현으로는 빨개질 수 없는 회귀 단언이다. 뒤에 주소를 찍는 로거가 기본 수준으로 들어오면
    # 빨개진다(명세 "로그"). 이 티켓의 수락으로 세지 않는다.
    assert QUERY_SECRET not in caplog.text


async def test_개행이_든_주소는_문구에서_이스케이프되어_줄을_바꾸지_못한다() -> None:
    """읽는 단계는 개행이 든 주소를 받는다(`urlsplit` 이 개행을 지운다). 그 주소가 문구에 줄바꿈째
    실리면 로그가 위조된다."""
    url = f"http://127.0.0.1:{free_port()}/mcp\nFORGED line"

    with pytest.raises(ConnectionError) as raised:
        async with McpTools().connect({REMOTE: _remote(url)}):
            pytest.fail("닫힌 포트에 열렸다")

    assert "\n" not in str(raised.value)
    assert "\\nFORGED line" in str(raised.value)


async def test_틀린_토큰으로_401을_받으면_원인_끝에_상태가_붙는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """라이브러리는 본문이 JSON-RPC 오류가 아닌 401 을 상태 코드 없는 예외로 바꾼다. 응답 훅이 받아
    둔 상태가 꺼진 서버와 틀린 토큰을 문구에서 가른다."""
    monkeypatch.setenv(TOKEN_VARIABLE, "Bearer wrong-token-0000")

    with serving(tmp_path, "--expect-authorization", "Bearer right-token-1111") as fixture:
        remote = _remote(fixture.url, Authorization=TOKEN_VARIABLE)
        with pytest.raises(ConnectionError) as raised:
            async with McpTools().connect({REMOTE: remote}):
                pytest.fail("틀린 토큰으로 열렸다")
        reached = fixture.headers_of("POST")

    assert str(raised.value).endswith(" (HTTP 401 Unauthorized)")
    assert reached, "요청이 서버에 닿지 않았다"
    assert reached[0]["authorization"] == "Bearer wrong-token-0000"
    assert "wrong-token-0000" not in _traceback_text(raised.value)


def _값이_어디에도_없다(error: BaseException) -> None:
    """문구, 원인 체인, 펼친 트레이스백 어디에도 서버가 되울린 값이 없다. `from None` 이 없으면
    `__cause__` 는 비어도 `__context__` 의 원래 예외가 트레이스백에 실린다."""
    assert TOKEN not in str(error)
    assert error.__cause__ is None
    assert error.__suppress_context__ is True
    assert TOKEN not in _traceback_text(error)


async def test_서버가_되울린_값은_여는_동안의_실패_문구에서_가려진다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(TOKEN_VARIABLE, f"Bearer {TOKEN}")

    with serving(tmp_path, "--echo", "initialize") as fixture:
        remote = _remote(fixture.url, Authorization=TOKEN_VARIABLE)
        with pytest.raises(ConnectionError) as raised:
            async with McpTools().connect({REMOTE: remote}):
                pytest.fail("되울린 401 로 열렸다")
        reached = fixture.headers_of("POST")

    assert reached[0]["authorization"] == f"Bearer {TOKEN}", "값이 서버에 닿지 않았다(양성 대조)"
    assert "bad credentials" in str(raised.value)
    assert str(raised.value).count("[가림: 헤더 Authorization]") == 2
    _값이_어디에도_없다(raised.value)


async def test_서버가_되울린_값은_도구_호출_실패_문구에서도_가려진다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(TOKEN_VARIABLE, f"Bearer {TOKEN}")

    with serving(tmp_path, "--echo", "tools/call") as fixture:
        remote = _remote(fixture.url, Authorization=TOKEN_VARIABLE)
        async with McpTools().connect({REMOTE: remote}) as connection:
            with pytest.raises(RuntimeError, match="remote.*add.*호출이 실패했다") as raised:
                await connection.call("add", {"a": 1, "b": 2})

    assert "bad credentials" in str(raised.value)
    assert "[가림: 헤더 Authorization]" in str(raised.value)
    _값이_어디에도_없다(raised.value)


async def test_같은_출처의_307_은_라이브러리가_따라가서_초기화와_도구_호출이_선다(
    tmp_path: Path,
) -> None:
    with serving(tmp_path, "--redirect") as fixture:
        async with McpTools().connect({REMOTE: _remote(fixture.url)}) as connection:
            result = await connection.call("add", {"a": 2, "b": 3})
        paths = [row["path"] for row in fixture.requests() if row["method"] == "POST"]

    assert result.content == "5"
    assert "/mcp" in paths, "리디렉션을 받는 첫 요청이 없다"
    assert "/mcp/" in paths, "라이브러리가 307 을 따르지 않았다"


async def test_지나간_307_은_뒤의_실패_원인_끝에_붙지_않는다(tmp_path: Path) -> None:
    """마지막 POST 가 307 을 지나 2xx 로 끝났다. 응답 훅이 POST 의 2xx 에서 받아 둔 상태를 지우지
    않으면 옛 규칙(2xx 가 아닌 응답의 마지막 하나)대로 지나간 307 이 붙는다."""
    with serving(tmp_path, "--redirect", "--list-error") as fixture:
        with pytest.raises(ConnectionError) as raised:
            async with McpTools().connect({REMOTE: _remote(fixture.url)}):
                pytest.fail("도구 목록이 거절되었는데 열렸다")

    assert "tool list refused" in str(raised.value)
    assert "HTTP 307" not in str(raised.value)


async def test_정상으로_닫으면_종료_요청이_앞선_요청과_같은_세션_번호로_서버에_닿는다(
    tmp_path: Path,
) -> None:
    with serving(tmp_path) as fixture:
        async with McpTools().connect({REMOTE: _remote(fixture.url)}) as connection:
            await connection.call("add", {"a": 1, "b": 1})
        deleted = fixture.headers_of("DELETE")
        sessions = {
            h["mcp-session-id"] for h in fixture.headers_of("POST") if "mcp-session-id" in h
        }

    assert len(deleted) == 1
    assert len(sessions) == 1
    assert deleted[0]["mcp-session-id"] in sessions
    assert deleted[0]["mcp-protocol-version"]
    assert deleted[0]["content-type"] == "application/json"
    assert deleted[0]["accept"] == "application/json, text/event-stream"


async def test_도구_호출_도중에_기한이_오면_종료_요청이_같은_세션_번호로_닿고_기한의_표지가_참이다(
    tmp_path: Path,
) -> None:
    """core 의 실행 타임아웃과 같은 범위(`move_on_after`)다. 보호된 닫기가 기한의 취소를 삼키지
    않아야 하고(`cancelled_caught`), 닫기에서 예외가 새지 않아야 한다."""
    with serving(tmp_path) as fixture:
        with anyio.move_on_after(60) as scope:
            async with McpTools().connect({REMOTE: _remote(fixture.url)}) as connection:
                scope.deadline = anyio.current_time() + DEADLINE_SECONDS
                await connection.call("slow", {"seconds": 30})
        deleted = fixture.headers_of("DELETE")
        sessions = {
            h["mcp-session-id"] for h in fixture.headers_of("POST") if "mcp-session-id" in h
        }

    assert fixture.slow_marker.exists(), "서버가 도구 호출을 받지 않았다"
    assert scope.cancelled_caught
    assert len(deleted) == 1, "기한에 취소된 실행이 종료 요청을 보내지 않았다"
    assert deleted[0]["mcp-session-id"] in sessions


async def test_종료_요청에_답하지_않는_서버는_닫기를_2초_안팎에_돌려보낸다(tmp_path: Path) -> None:
    """상한은 홀로 돌린 시간(2초 남짓)의 넉넉한 배수다. 하한은 유예가 실제로 걸렸는지 본다."""
    with serving(tmp_path, "--delete-sleep", "30") as fixture:
        async with McpTools().connect({REMOTE: _remote(fixture.url)}) as connection:
            await connection.call("add", {"a": 1, "b": 1})
            closing = time.monotonic()
        elapsed = time.monotonic() - closing
        deleted = fixture.headers_of("DELETE")

    assert len(deleted) == 1, "종료 요청이 서버에 닿지 않았다"
    assert elapsed >= GRACE_FLOOR_SECONDS, f"유예가 걸리지 않았다: {elapsed:.2f}초"
    assert elapsed < GRACE_CEILING_SECONDS, f"닫기가 {elapsed:.2f}초 걸렸다"


async def test_여는_도중_실패해_세션_번호를_받지_못했으면_종료_요청을_보내지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(TOKEN_VARIABLE, "Bearer wrong-token-0000")

    with serving(tmp_path, "--expect-authorization", "Bearer right-token-1111") as fixture:
        with pytest.raises(ConnectionError):
            async with McpTools().connect(
                {REMOTE: _remote(fixture.url, Authorization=TOKEN_VARIABLE)}
            ):
                pytest.fail("틀린 토큰으로 열렸다")
        methods = [row["method"] for row in fixture.requests()]

    assert "POST" in methods, "서버에 닿지 않았다"
    assert "DELETE" not in methods


async def test_세션_번호를_주지_않는_서버는_정상으로_닫히고_종료_요청을_받지_않는다(
    tmp_path: Path,
) -> None:
    with serving(tmp_path, "--stateless") as fixture:
        async with McpTools().connect({REMOTE: _remote(fixture.url)}) as connection:
            result = await connection.call("add", {"a": 2, "b": 3})
        methods = [row["method"] for row in fixture.requests()]

    assert (result.ok, result.content) == (True, "5")
    assert "DELETE" not in methods


async def test_리디렉션하는_서버에서도_정상_닫기의_종료_요청이_슬래시를_붙인_최종_주소에_닿는다(
    tmp_path: Path,
) -> None:
    with serving(tmp_path, "--redirect") as fixture:
        async with McpTools().connect({REMOTE: _remote(fixture.url)}) as connection:
            await connection.call("add", {"a": 1, "b": 1})
        deleted = [row for row in fixture.requests() if row["method"] == "DELETE"]

    assert "/mcp/" in [row["path"] for row in deleted], "종료 요청이 최종 주소에 닿지 않았다"


async def test_리디렉션하는_서버에서도_취소된_실행의_종료_요청이_슬래시를_붙인_최종_주소에_닿는다(
    tmp_path: Path,
) -> None:
    with serving(tmp_path, "--redirect") as fixture:
        with anyio.move_on_after(60) as scope:
            async with McpTools().connect({REMOTE: _remote(fixture.url)}) as connection:
                scope.deadline = anyio.current_time() + DEADLINE_SECONDS
                await connection.call("slow", {"seconds": 30})
        deleted = [row for row in fixture.requests() if row["method"] == "DELETE"]

    assert scope.cancelled_caught
    assert "/mcp/" in [row["path"] for row in deleted], "종료 요청이 최종 주소에 닿지 않았다"


async def test_종료_요청을_다른_출처로_돌려보내면_그_출처에는_요청이_닿지_않고_닫기가_돌아온다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(TOKEN_VARIABLE, f"Bearer {TOKEN}")
    other_folder = tmp_path / "other"
    other_folder.mkdir()

    with serving(other_folder) as other, serving(tmp_path, "--delete-redirect", other.url) as main:
        remote = _remote(main.url, Authorization=TOKEN_VARIABLE)
        async with McpTools().connect({REMOTE: remote}) as connection:
            await connection.call("add", {"a": 1, "b": 1})
        sent_to_main = [row["method"] for row in main.requests()]
        sent_to_other = other.requests()

    assert "DELETE" in sent_to_main, "종료 요청이 원래 서버에 닿지 않았다"
    assert sent_to_other == [], f"다른 출처에 요청이 닿았다: {sent_to_other}"


async def test_종료_요청의_연결이_끊겨도_닫기는_예외_없이_돌아온다(tmp_path: Path) -> None:
    with serving(tmp_path, "--delete-drop") as fixture:
        async with McpTools().connect({REMOTE: _remote(fixture.url)}) as connection:
            await connection.call("add", {"a": 1, "b": 1})
        deleted = fixture.headers_of("DELETE")

    assert len(deleted) == 1, "종료 요청이 서버에 닿지 않았다"


async def test_원격_서버가_뒤에_있어도_앞선_stdio_서버를_연_뒤_연결_오류_하나다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """앞 서버의 태스크 그룹 안에서 난 실패도 그 그룹에 싸이지 않고 연결 오류 하나로 나온다."""
    url = f"http://127.0.0.1:{free_port()}/mcp"
    servers = {PluginName("fixture"): FIXTURE, REMOTE: _remote(url)}

    with pytest.raises(ConnectionError, match=rf"remote\({url}\)"):
        async with McpTools().connect(servers):
            pytest.fail("닫힌 포트에 열렸다")


async def test_둘째_서버가_열리지_않아도_연결_오류_하나다() -> None:
    """둘째 서버의 실패는 먼저 연 서버의 태스크 그룹 안에서 나므로 그 그룹에도 싸인다."""
    tools: ToolSource = McpTools()
    broken = StdioServer(command="definitely-not-a-command-agent-os")

    with pytest.raises(ConnectionError, match="broken.*definitely-not-a-command-agent-os"):
        async with tools.connect({PluginName("fixture"): FIXTURE, PluginName("broken"): broken}):
            pass


async def test_여는_도중의_취소는_연결_오류로_바꾸지_않는다() -> None:
    """실행 타임아웃이 서버를 띄우는 도중에 오는 모양이다. 취소가 연결 오류로 바뀌면 범위가 그
    취소를 받지 못하고 연결 오류가 밖으로 나온다."""
    with anyio.move_on_after(0) as scope:
        async with McpTools().connect({PluginName("fixture"): FIXTURE}):
            pytest.fail("취소된 연결이 열렸다")

    assert scope.cancelled_caught


async def test_뜨자마자_끝나는_서버는_서버_이름을_든_연결_오류_하나다() -> None:
    """세션을 연 뒤 실패하므로 그 예외가 상류의 태스크 그룹을 지나 두 겹으로 싸인다. 어댑터가
    벗겨 그 `ConnectionError` 하나로 낸다."""
    tools: ToolSource = McpTools()
    exiting = StdioServer(command=sys.executable, args=("-c", "pass"))

    with pytest.raises(ConnectionError, match="exiting.*Connection closed"):
        async with tools.connect({PluginName("exiting"): exiting}):
            pass


class _본문의_예외(Exception):
    pass


async def test_연결_안에서_던진_예외_그룹은_그_그룹_그대로_나온다() -> None:
    """부르는 쪽이 스스로 낸 그룹도 겉봉(상류의 태스크 그룹 두 겹)만 벗고 그 객체로 나온다."""
    thrown = ExceptionGroup("본문", [_본문의_예외()])

    with pytest.raises(ExceptionGroup) as raised:
        async with _fixture_connection():
            raise thrown
    assert raised.value is thrown


async def test_연결_안의_yield_에_멈춘_제너레이터는_예외_없이_닫힌다() -> None:
    """core 는 연결을 연 채 이벤트를 내는 제너레이터를 그 자리에서 닫는다(트레이스 쓰기가 실패한
    실행, `core/run.py` 의 `_drive`). 닫기가 넣는 GeneratorExit 를 상류의 태스크 그룹이 감싼 채
    두면 `aclose` 가 `BaseExceptionGroup` 을 내고, 결말을 쓴 실행도 그것을 밖으로 올린다."""

    async def 연결_안에서_낸다() -> AsyncGenerator[str]:
        async with _fixture_connection():
            yield "연결 안"

    events = 연결_안에서_낸다()
    assert await anext(events) == "연결 안"
    await events.aclose()


async def test_서버를_지정하지_않으면_도구_없이_연다() -> None:
    tools: ToolSource = McpTools()

    async with tools.connect({}) as opened:
        assert list(opened.tools()) == []


def _paged(shape: str) -> dict[PluginName, StdioServer]:
    server = StdioServer(command=sys.executable, args=(str(PAGED), shape))
    return {PluginName("paged"): server}


async def test_빈_커서는_도구_목록의_끝이다() -> None:
    """빈 커서로 다시 물으면 같은 쪽이 끝없이 온다."""
    with anyio.fail_after(PAGED_WITHIN_SECONDS):
        async with McpTools().connect(_paged("empty")) as connection:
            names = [spec.name for spec in connection.tools()]

    assert names == ["paged"]


async def test_끝나지_않는_도구_목록은_쪽_수의_상한에서_서버를_든_연결_오류다() -> None:
    with (
        anyio.fail_after(PAGED_WITHIN_SECONDS),
        pytest.raises(ConnectionError, match="paged.*1000쪽"),
    ):
        async with McpTools().connect(_paged("endless")):
            pass


# --- 닫기(ADR 0034) ---


@pytest.fixture
def folder(tmp_path: Path) -> Iterator[Path]:
    """가짜 프로세스의 하트비트와 표지가 놓이는 폴더. 끝날 때 멈춤 파일로 남은 것을 끝낸다."""
    yield tmp_path
    (tmp_path / STOP).touch()


def _lingering(role: str, folder: Path) -> dict[PluginName, StdioServer]:
    server = StdioServer(command=sys.executable, args=(str(LINGERING), role, str(folder)))
    return {PluginName("lingering"): server}


async def _생길_때까지_기다린다(path: Path) -> None:
    with anyio.fail_after(APPEAR_WITHIN_SECONDS):
        while not path.exists():
            await anyio.sleep(0.05)


def _멈췄다(*paths: Path) -> None:
    """15초 안에 하트비트가 모두 1초 동안 자라지 않으면 지난다.

    한 번만 견주지 않고 기한까지 거듭 견준다(`tests/tools/test_run_checks.py` 의 `_stops_growing`).
    부하에서 꺼지는 프로세스의 마지막 쓰기를 산 프로세스로 읽지 않는다. 실패하면 마지막 견줌에서
    자란 하트비트를 든다.
    """
    끝 = time.monotonic() + STOP_WITHIN_SECONDS
    자란: list[str] = []
    while time.monotonic() < 끝:
        크기 = [path.stat().st_size for path in paths]
        time.sleep(1)
        자란 = [
            path.name for path, 앞 in zip(paths, 크기, strict=True) if path.stat().st_size != 앞
        ]
        if not 자란:
            return
    pytest.fail(f"닫은 뒤에도 {STOP_WITHIN_SECONDS}초 동안 {', '.join(자란)} 하트비트가 자란다")


async def test_도구_호출_도중에_기한이_오면_감싼_프로세스_아래의_서버까지_내려간다(
    folder: Path,
) -> None:
    """core 의 실행 타임아웃과 같은 범위(`move_on_after`)다. 범위가 기한의 취소를 받았는지
    (`cancelled_caught`)로 기한을 본다 — 보호된 닫기가 그 취소를 삼키지 않는다."""
    with anyio.move_on_after(60) as scope:
        async with McpTools().connect(_lingering("wrapper", folder)) as connection:
            await _생길_때까지_기다린다(folder / "stay.hb")
            scope.deadline = anyio.current_time() + 1
            await connection.call("slow", {"seconds": 30})

    assert (folder / "slow").exists(), "서버가 도구 호출을 받지 않았다"
    assert scope.cancelled_caught
    _멈췄다(folder / "wrapper.hb", folder / "stay.hb")


async def test_스스로_끝나며_자식을_남기는_서버를_닫으면_그_자식도_내려간다(folder: Path) -> None:
    """상류는 유예 안에 스스로 끝난 서버의 트리를 끄지 않는다. 윈도우는 Job Object 를 닫아 남은
    자식을 거두고, POSIX 는 런처가 서버의 프로세스 그룹을 끈다."""
    async with McpTools().connect(_lingering("leaving", folder)):
        await _생길_때까지_기다린다(folder / "child.hb")

    _멈췄다(folder / "child.hb")


# 사례 5의 자식. 연결을 연 뒤 표지 파일을 남기고 기다린다. 테스트가 그 표지와 서버의 하트비트를 본
# 뒤 이 프로세스를 강제로 끈다.
_CONNECTED = "connected"
_PARENT = """
import sys
from pathlib import Path

import anyio

from agent_os.adapters.mcp import McpTools
from agent_os.sdk import StdioServer, PluginName

lingering, folder, connected = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
server = StdioServer(command=sys.executable, args=(lingering, "wrapper", str(folder)))


async def main() -> None:
    async with McpTools().connect({PluginName("lingering"): server}):
        (folder / connected).touch()
        await anyio.sleep(120)


anyio.run(main)
"""


def test_연결을_연_프로세스가_갑자기_죽어도_서버가_내려간다(folder: Path) -> None:
    """윈도우는 그 프로세스가 끝나며 Job Object 가 닫히고, POSIX 는 런처가 부모가 바뀐 것을 보고
    서버의 프로세스 그룹을 끈다."""
    beats = (folder / "wrapper.hb", folder / "stay.hb")
    ready = (folder / _CONNECTED, *beats)
    parent = subprocess.Popen(
        [sys.executable, "-c", _PARENT, str(LINGERING), str(folder), _CONNECTED]
    )
    try:
        end = time.monotonic() + CONNECT_WITHIN_SECONDS
        while (
            not all(path.exists() for path in ready)
            and parent.poll() is None
            and time.monotonic() < end
        ):
            time.sleep(0.05)
        # 표지가 생기기 전에 끝났으면(연결 실패) 기한을 채우지 않고 그 종료 코드를 든다.
        exited = parent.poll()
    finally:
        parent.kill()
        parent.wait()

    missing = [path.name for path in ready if not path.exists()]
    assert not missing, (
        f"{CONNECT_WITHIN_SECONDS}초 안에 생기지 않았다: {missing}"
        f"(연결을 여는 프로세스의 종료 코드: {exited})"
    )
    _멈췄다(*beats)


async def test_연결_안에서_난_예외는_감싸이지_않고_나오며_서버가_내려간다(folder: Path) -> None:
    thrown = _본문의_예외()

    with pytest.raises(_본문의_예외) as raised:
        async with McpTools().connect(_lingering("wrapper", folder)):
            await _생길_때까지_기다린다(folder / "stay.hb")
            raise thrown

    assert raised.value is thrown
    _멈췄다(folder / "wrapper.hb", folder / "stay.hb")


async def test_도구_호출_도중에_서버가_죽으면_서버와_도구를_든_RuntimeError_다(
    folder: Path,
) -> None:
    async with McpTools().connect(_lingering("stay", folder)) as connection:
        with pytest.raises(RuntimeError, match="lingering.*crash.*Connection closed"):
            await connection.call("crash", {})


# --- 접속 확인(ADR 0067) ---

# 확인이 돌아오기까지의 상한. 프로세스를 띄우고 기한을 일부러 넘기게 하는 사례가 있어 홀로 돌려 몇
# 초인 값의 넉넉한 배수로 둔다(`.claude/rules/tests.md` 의 시간 단언).
CHECK_WITHIN_SECONDS = 120
# 기한 전에 끝나야 하는 사례(붙는 서버)에 주는 확인의 기한. 상한보다 짧아야 기한이 상한을 앞선다.
LONG_DEADLINE_SECONDS = 100
# 기한에 닿아 끊기는 사례의 기한. 서버가 세션을 연 뒤에 늦게 답하는 사례는 세션이 열리기 전에 기한이
# 오면 종료 요청을 확인할 수 없어, 초기화가 끝나기에 넉넉하게 둔다.
REMOTE_DEADLINE_SECONDS = 8
STDIO_DEADLINE_SECONDS = 8
# 도구가 하나도 없는 stdio 서버.
_NO_TOOLS = "from mcp.server.mcpserver import MCPServer; MCPServer('none', log_level='ERROR').run()"
# 초기화에 답하지 않는 stdio 서버. 입력을 읽지 않고 하트비트만 쓴다. 표준 라이브러리만 불러 띄워서
# 부하에서도 기한 안에 뜬다.
_SILENT = """
import sys, time
from pathlib import Path

beat = Path(sys.argv[1]) / "silent.hb"
end = time.monotonic() + 120
while time.monotonic() < end and not (beat.parent / "stop").exists():
    with beat.open("ab") as file:
        file.write(b".")
    time.sleep(0.1)
"""


def _timeout_reason(name: PluginName, where: str, seconds: str) -> str:
    return f"MCP 서버 {name}({where})에 붙지 못했다: {seconds}초 안에 준비되지 않았다"


async def test_접속_확인의_기본_기한은_원격_10초_stdio_20초다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """중계 제한 30초 안에 stdio 의 기한과 닫는 시간이 들어야 한다(명세 "기한"). 어댑터를 인자
    없이 만들어 확인을 부르면 확인 함수가 받는 기한을 본다."""
    seen: list[float] = []

    async def recording(_name: PluginName, _server: object, seconds: float) -> Reached:
        seen.append(seconds)
        return Reached()

    monkeypatch.setattr("agent_os.adapters.mcp._check", recording)
    tools = McpTools()
    await tools.check_remote(REMOTE, _remote("http://127.0.0.1:1/mcp"))
    await tools.check_stdio(PluginName("any"), StdioServer(command="none"))

    assert seen == [10, 20]
    assert (REMOTE_CHECK_SECONDS, STDIO_CHECK_SECONDS) == (10, 20)


async def test_원격_서버가_붙으면_Reached이고_세션을_닫는다(tmp_path: Path) -> None:
    with anyio.fail_after(CHECK_WITHIN_SECONDS), serving(tmp_path) as fixture:
        outcome = await McpTools().check_remote(REMOTE, _remote(fixture.url))
        deleted = fixture.headers_of("DELETE")
        sessions = {
            h["mcp-session-id"] for h in fixture.headers_of("POST") if "mcp-session-id" in h
        }

    assert outcome == Reached()
    assert len(deleted) == 1, "확인이 세션 종료 요청을 보내지 않았다"
    assert deleted[0]["mcp-session-id"] in sessions


async def test_원격_서버_확인_한_번이_서버에_보내는_요청의_수(tmp_path: Path) -> None:
    """화면이 30초마다 되풀이하므로 바깥 서버가 받는 몫이다(명세 "간격과 보이지 않는 탭"). 알림
    흐름을 여는 GET 은 닫기와의 겹침에 따라 없을 수 있어 많아야 하나로 본다."""
    with anyio.fail_after(CHECK_WITHIN_SECONDS), serving(tmp_path) as fixture:
        await McpTools().check_remote(REMOTE, _remote(fixture.url))
        methods = [str(row["method"]) for row in fixture.requests()]

    assert methods.count("POST") == 3
    assert methods.count("DELETE") == 1
    assert methods.count("GET") <= 1
    assert len(methods) == methods.count("POST") + methods.count("DELETE") + methods.count("GET")


async def test_도구가_하나도_없는_stdio_서버도_Reached다() -> None:
    name = PluginName("none")
    server = StdioServer(command=sys.executable, args=("-c", _NO_TOOLS))

    with anyio.fail_after(CHECK_WITHIN_SECONDS):
        outcome = await McpTools(stdio_check_seconds=LONG_DEADLINE_SECONDS).check_stdio(
            name, server
        )

    assert outcome == Reached()


async def test_닫힌_포트의_원격_서버는_연결_오류의_글로_Unreached다() -> None:
    url = f"http://127.0.0.1:{free_port()}/mcp"

    with anyio.fail_after(CHECK_WITHIN_SECONDS):
        outcome = await McpTools().check_remote(REMOTE, _remote(url))

    assert type(outcome) is Unreached
    assert type(outcome.reason) is str
    assert outcome.reason.startswith(f"MCP 서버 remote({url})에 붙지 못했다: ")
    assert "ConnectError" in outcome.reason
    assert "(HTTP " not in outcome.reason


async def test_틀린_토큰의_원격_서버는_글_끝에_HTTP_401이_붙은_Unreached다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(TOKEN_VARIABLE, "Bearer wrong-token-0000")

    with (
        anyio.fail_after(CHECK_WITHIN_SECONDS),
        serving(tmp_path, "--expect-authorization", "Bearer right-token-1111") as fixture,
    ):
        remote = _remote(fixture.url, Authorization=TOKEN_VARIABLE)
        outcome = await McpTools().check_remote(REMOTE, remote)

    assert type(outcome) is Unreached
    assert outcome.reason.startswith(f"MCP 서버 remote({fixture.url})에 붙지 못했다: ")
    assert outcome.reason.endswith(" (HTTP 401 Unauthorized)")
    assert "wrong-token-0000" not in outcome.reason


async def test_서버가_헤더_값을_오류_본문에_되울려도_Unreached의_글에는_그_값이_없다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(TOKEN_VARIABLE, f"Bearer {TOKEN}")

    with (
        anyio.fail_after(CHECK_WITHIN_SECONDS),
        serving(tmp_path, "--echo", "initialize") as fixture,
    ):
        remote = _remote(fixture.url, Authorization=TOKEN_VARIABLE)
        outcome = await McpTools().check_remote(REMOTE, remote)
        sent = fixture.headers_of("POST")

    assert sent[0]["authorization"] == f"Bearer {TOKEN}", "값이 서버에 닿지 않았다(양성 대조)"
    assert type(outcome) is Unreached
    assert "bad credentials" in outcome.reason
    assert "[가림: 헤더 Authorization]" in outcome.reason
    assert TOKEN not in outcome.reason


async def test_환경_변수가_없는_헤더는_붙지_않고_변수_이름을_든_Unreached다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """도구 쪽에는 확인을 거부하는 구성 오류가 따로 없다. 실행이 여는 동안 실패하는 것은 모두
    Unreached 의 까닭이다."""
    monkeypatch.delenv(TOKEN_VARIABLE, raising=False)

    with anyio.fail_after(CHECK_WITHIN_SECONDS), serving(tmp_path) as fixture:
        remote = _remote(fixture.url, Authorization=TOKEN_VARIABLE)
        outcome = await McpTools().check_remote(REMOTE, remote)
        received = fixture.requests()

    assert type(outcome) is Unreached
    assert f"헤더 Authorization의 환경 변수 {TOKEN_VARIABLE}이 없다" in outcome.reason
    assert received == [], "환경 변수가 없는데 서버에 요청이 갔다"


async def test_도구_목록에_늦게_답하는_원격_서버는_기한_뒤_시간_초과의_글이고_세션을_닫는다(
    tmp_path: Path,
) -> None:
    """기한의 취소가 어댑터 안에서 연결 오류로 바뀌면 시간 초과 대신 연결 오류의 글이 나온다."""
    with (
        anyio.fail_after(CHECK_WITHIN_SECONDS),
        serving(tmp_path, "--list-sleep", "60") as fixture,
    ):
        tools = McpTools(remote_check_seconds=REMOTE_DEADLINE_SECONDS)
        outcome = await tools.check_remote(REMOTE, _remote(fixture.url))
        deleted = fixture.headers_of("DELETE")

    assert outcome == Unreached(_timeout_reason(REMOTE, fixture.url, str(REMOTE_DEADLINE_SECONDS)))
    assert len(deleted) == 1, "기한에 닿아 끊긴 확인이 세션 종료 요청을 보내지 않았다"


async def test_초기화에_답하지_않는_원격_서버도_기한_뒤_시간_초과의_글이다() -> None:
    """붙기는 했지만 답이 없다. 서버가 세션 번호를 주지 못해 종료 요청은 없다."""
    with socket.socket() as listening:
        listening.bind(("127.0.0.1", 0))
        listening.listen()
        url = f"http://127.0.0.1:{listening.getsockname()[1]}/mcp"
        with anyio.fail_after(CHECK_WITHIN_SECONDS):
            tools = McpTools(remote_check_seconds=1.5)
            outcome = await tools.check_remote(REMOTE, _remote(url))

    assert outcome == Unreached(_timeout_reason(REMOTE, url, "1.5"))


async def test_닫는_동안_난_예외는_바꾸지_않고_그대로_올린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def failing(*_args: object) -> None:
        raise RuntimeError("닫기가 실패했다")

    monkeypatch.setattr("agent_os.adapters.mcp._end_session", failing)

    with anyio.fail_after(CHECK_WITHIN_SECONDS), serving(tmp_path) as fixture:
        with pytest.raises(RuntimeError, match="닫기가 실패했다"):
            await McpTools().check_remote(REMOTE, _remote(fixture.url))


async def test_바깥의_취소는_삼키지_않는다(tmp_path: Path) -> None:
    """확인의 기한이 아니라 바깥 범위가 취소하면 그대로 취소로 끝난다."""
    with anyio.fail_after(CHECK_WITHIN_SECONDS), serving(tmp_path, "--list-sleep", "60") as fixture:
        with anyio.move_on_after(2) as outer:
            await McpTools().check_remote(REMOTE, _remote(fixture.url))
            pytest.fail("취소되지 않았다")

    assert outer.cancelled_caught


async def test_stdio_서버가_붙으면_Reached이고_확인이_끝난_뒤_프로세스가_남지_않는다(
    folder: Path,
) -> None:
    """이 서버는 입력이 닫혀도 끝나지 않는다. 확인이 닫는 길(ADR 0034)로 프로세스를 끈다."""
    name = PluginName("lingering")
    server = _lingering("stay", folder)[name]

    with anyio.fail_after(CHECK_WITHIN_SECONDS):
        outcome = await McpTools(stdio_check_seconds=LONG_DEADLINE_SECONDS).check_stdio(
            name, server
        )

    assert outcome == Reached()
    assert (folder / "stay.hb").exists(), "서버가 뜨지 않았다"
    _멈췄다(folder / "stay.hb")


async def test_명령을_찾지_못한_stdio_서버는_연결_오류의_글로_Unreached다() -> None:
    name = PluginName("broken")
    server = StdioServer(command="definitely-not-a-command-agent-os")

    with anyio.fail_after(CHECK_WITHIN_SECONDS):
        outcome = await McpTools().check_stdio(name, server)

    assert type(outcome) is Unreached
    assert outcome.reason.startswith(
        "MCP 서버 broken(definitely-not-a-command-agent-os)에 붙지 못했다: "
    )
    assert "FileNotFoundError" in outcome.reason


async def test_초기화에_답하지_않는_stdio_서버는_기한_뒤_시간_초과의_글이고_프로세스가_남지_않는다(
    folder: Path,
) -> None:
    server = StdioServer(command=sys.executable, args=("-c", _SILENT, str(folder)))
    name = PluginName("silent")

    with anyio.fail_after(CHECK_WITHIN_SECONDS):
        tools = McpTools(stdio_check_seconds=STDIO_DEADLINE_SECONDS)
        outcome = await tools.check_stdio(name, server)

    assert outcome == Unreached(_timeout_reason(name, sys.executable, str(STDIO_DEADLINE_SECONDS)))
    assert (folder / "silent.hb").exists(), "서버가 뜨지 않았다"
    _멈췄다(folder / "silent.hb")


async def test_기한의_취소가_연결_오류로_바뀌어_나와도_시간_초과의_글이다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """라이브러리 안에서 취소가 다른 예외로 바뀌어 여는 단계의 변환(`_connecting`)이 연결 오류로
    올리는 경우다. 기한이 왔는지는 예외가 아니라 범위가 보므로 연결 오류의 글이 나오면 안 된다."""

    @asynccontextmanager
    async def translating(*_args: object) -> AsyncGenerator[None]:
        try:
            await anyio.sleep_forever()
        except anyio.get_cancelled_exc_class():
            raise ConnectionError("취소가 연결 오류로 바뀌었다") from None
        yield

    monkeypatch.setattr("agent_os.adapters.mcp._opened", translating)

    with anyio.fail_after(CHECK_WITHIN_SECONDS):
        tools = McpTools(remote_check_seconds=0.2)
        outcome = await tools.check_remote(REMOTE, _remote("http://127.0.0.1:1/mcp"))

    assert outcome == Unreached(_timeout_reason(REMOTE, "http://127.0.0.1:1/mcp", "0.2"))


async def test_글이_빈_연결_오류도_비지_않은_글의_Unreached다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """응답 계약이 빈 글을 거부해, 빈 글이 가면 관리가 500이다. 여는 단계의 변환(`_connecting`)을
    지나지 않은 연결 오류는 글이 빌 수 있다."""

    @asynccontextmanager
    async def failing(*_args: object) -> AsyncGenerator[None]:
        raise BrokenPipeError
        yield

    monkeypatch.setattr("agent_os.adapters.mcp._opened", failing)

    with anyio.fail_after(CHECK_WITHIN_SECONDS):
        outcome = await McpTools().check_remote(REMOTE, _remote("http://127.0.0.1:1/mcp"))

    assert outcome == Unreached("BrokenPipeError")


async def test_도구_목록을_읽은_뒤_닫는_도중에_기한이_오면_Reached다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """붙었다는 사실은 닫는 길이 끊겨도 바뀌지 않는다. 이 시험은 닫기가 끝나지 않는 서버를 흉내
    내고, 기한은 닫는 동안에 온다."""

    @asynccontextmanager
    async def hanging_close(*_args: object) -> AsyncGenerator[list[object]]:
        yield []
        await anyio.sleep_forever()

    monkeypatch.setattr("agent_os.adapters.mcp._opened", hanging_close)

    with anyio.fail_after(CHECK_WITHIN_SECONDS):
        outcome = await McpTools(remote_check_seconds=0.3).check_remote(
            REMOTE, _remote("http://127.0.0.1:1/mcp")
        )

    assert outcome == Reached()


async def test_도구_목록을_읽은_뒤_닫는_도중의_연결_오류는_바꾸지_않고_올린다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """여는 단계 밖(닫는 동안)에서 난 연결 오류는 Unreached 의 까닭이 아니다. 관리 경로가 500으로
    답하도록 그대로 올린다."""

    @asynccontextmanager
    async def failing_close(*_args: object) -> AsyncGenerator[list[object]]:
        yield []
        raise ConnectionError("닫는 동안 끊겼다")

    monkeypatch.setattr("agent_os.adapters.mcp._opened", failing_close)

    with anyio.fail_after(CHECK_WITHIN_SECONDS):
        with pytest.raises(ConnectionError, match="닫는 동안 끊겼다"):
            await McpTools().check_remote(REMOTE, _remote("http://127.0.0.1:1/mcp"))
