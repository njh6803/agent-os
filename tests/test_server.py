"""주 이음매. create_app() 이 만든 앱에 ASGI 로 요청을 넣고 바깥 행동만 단언한다.

바탕으로 재는 것은 셋이다 — 모든 라우트가 보호를 켜지 않아도 기본으로 막힌다는 것, 에러가 언제나
같은 봉투로 나간다는 것, 인증 없이 경계 밖으로 나가는 응답이 /health 하나뿐이라는 것. 그 위에
데이터 라우트가 하나씩 붙는다. 플러그인 둘은 파일 끝에 있다.

가짜 포트는 상속하지 않고 시그니처로 만족하며 픽스처가 포트 타입으로 annotate 한다. 그 한 줄이
포트 적합성이 검증되는 자리다. 네트워크도 디스크도 타지 않는다.
"""

import dataclasses
import inspect
import io
from collections.abc import AsyncIterator, Sequence
from typing import get_type_hints

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from agent_os import server as server_module
from agent_os.admin import http as admin_http
from agent_os.admin.auth import PUBLIC_PATHS
from agent_os.admin.http import Health
from agent_os.core.ports import (
    Cursor,
    ManifestRow,
    PluginError,
    PluginSource,
    RunRow,
    RunStatus,
    ToolSource,
    Trace,
    TraceStore,
    UnreadableManifest,
)
from agent_os.sdk import (
    PLUGIN_NAME_PATTERN,
    BaseAgent,
    Event,
    McpServer,
    PluginKind,
    PluginManifest,
    PluginName,
    RunId,
    parse_manifest,
)
from agent_os.server import create_app

TOKEN = "t0ken-that-only-tests-know"
BEARER = {"Authorization": f"Bearer {TOKEN}"}
# allowlist 밖이면서 라우트가 없는 경로. 토큰이 없으면 401 이고 있으면 404 라는 것이 곧 미들웨어가
# 라우팅보다 먼저라는 사실이다. 데이터 라우트가 붙어도 이 경로는 문서에 없어 그 대조가 유지된다.
GUARDED = "/unrouted"


CALC = parse_manifest(
    """
schema_version = "1"
kind = "agent"
name = "calc"
version = "0.1.0"
entrypoint = "agent:Calc"
mcp = ["everything"]
requires_approval = ["add"]
"""
)
EVERYTHING = parse_manifest(
    """
schema_version = "1"
kind = "mcp"
name = "everything"
version = "0.1.0"

[server]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-everything"]
"""
)
SUMMARIZE = parse_manifest(
    """
schema_version = "1"
kind = "skill"
name = "summarize"
version = "0.1.0"
"""
)
SONNET = parse_manifest(
    """
schema_version = "1"
kind = "model"
name = "sonnet"
version = "0.1.0"
"""
)
BROKEN = UnreadableManifest(
    kind=PluginKind.AGENT,
    name="broken",
    reason="매니페스트를 읽을 수 없다: plugins/agents/broken/plugin.toml",
)


class FakePlugins:
    """디렉터리 대신 행 목록을 든다. 부른 횟수를 세어 검증이 포트보다 먼저 끝나는지 본다.

    읽히지 않는 행에는 어댑터와 같은 비대칭으로 답한다 — 목록에서는 표지, 단건에서는 PluginError.
    어댑터가 실제로 그렇게 답한다는 것은 `tests/adapters/test_filesystem.py` 가 잰다.
    """

    def __init__(self, rows: Sequence[ManifestRow] = ()) -> None:
        self._rows = tuple(rows)
        self.calls = 0

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None:
        self.calls += 1
        for row in self._rows:
            if row.kind is not kind or row.name != name:
                continue
            if isinstance(row, UnreadableManifest):
                raise PluginError(row.reason)
            return row
        return None

    def list_manifests(self, kind: PluginKind) -> Sequence[ManifestRow]:
        self.calls += 1
        return tuple(row for row in self._rows if row.kind is kind)

    def load_agent(self, manifest: PluginManifest) -> BaseAgent:
        raise NotImplementedError("관리는 실행을 일으키지 않는다")


class FakeTrace:
    """트레이스 라우트는 05·06 의 것이라 불리지 않는다. 불리면 그 자체가 결함이라 터뜨린다."""

    def write(self, event: Event) -> None:
        raise NotImplementedError("관리는 읽기 전용이다")

    def read(self, run_id: RunId) -> Trace | None:
        raise NotImplementedError("트레이스 상세는 06 의 것이다")

    def list(
        self,
        *,
        status: RunStatus | None = None,
        limit: int | None = None,
        after: Cursor | None = None,
    ) -> Sequence[RunRow]:
        raise NotImplementedError("트레이스 목록은 05 의 것이다")


@pytest.fixture
def stderr() -> io.StringIO:
    """서버 표준 에러. 실패 하나가 남기는 한 줄을 테스트가 읽는 자리다."""
    return io.StringIO()


@pytest.fixture
def plugins() -> FakePlugins:
    """종류 넷에 하나 이상씩과 읽을 수 없는 것 하나. 행 순서는 어댑터처럼 종류 안에서 이름순이다."""
    return FakePlugins(rows=(BROKEN, CALC, EVERYTHING, SUMMARIZE, SONNET))


@pytest.fixture
def app(stderr: io.StringIO, plugins: FakePlugins) -> FastAPI:
    source: PluginSource = plugins
    trace: TraceStore = FakeTrace()
    return create_app(plugins=source, trace=trace, token=TOKEN, stderr=stderr)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://admin.test") as opened:
        yield opened


def _documented_paths(app: FastAPI) -> tuple[str, ...]:
    """앱이 아는 경로 전부. 라우트를 더하면 전수 검사의 대상이 저절로 는다."""
    paths = app.openapi().get("paths", {})
    return tuple(str(path) for path in paths)


def _route_that_raises(app: FastAPI, path: str, error: Exception) -> None:
    """예외를 상태 코드로 옮기는 표를 미는 지렛대.

    표의 갈래 중에는 진짜 라우트로 일으키기 어려운 것이 있다(예기치 않은 예외). 이 라우트는 표가
    실제로 도는지 보기 위한 것이고, 진짜 라우트가 닿는 갈래는 그 라우트로 다시 잰다.
    """

    @app.get(path)
    def _raise() -> Health:
        raise error


async def test_헬스체크만_토큰_없이_답한다(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_인증_없이_지나가는_경로의_목록은_헬스체크_하나다() -> None:
    """목록이 문서 없이 자라는 것이 fail-open 으로 돌아가는 길이다(ADR 0011)."""
    assert PUBLIC_PATHS == frozenset({"/health"})


async def test_헬스체크_응답이_내부_구성을_싣지_않는다(client: AsyncClient) -> None:
    """인증 없이 경계 밖으로 나가는 유일한 응답이다(스토리 42)."""
    body = (await client.get("/health")).json()

    assert list(body) == ["status"]


async def test_allowlist_밖의_모든_경로가_토큰_없이_401이다(
    app: FastAPI, client: AsyncClient
) -> None:
    """라우트를 더하고 보호를 잊으면 이 테스트가 깨진다. fail-closed 라 벨트이지 전부가 아니다."""
    documented = _documented_paths(app)
    guarded = [path for path in documented if path not in PUBLIC_PATHS]
    assert guarded, "allowlist 밖 경로가 없으면 이 전수 검사는 401 을 한 번도 재지 않는다"

    for path in documented:
        response = await client.get(path)
        expected = 200 if path in PUBLIC_PATHS else 401
        assert response.status_code == expected, path


async def test_문서에_없는_경로도_토큰_없이는_404가_아니라_401이다(client: AsyncClient) -> None:
    """미들웨어가 라우팅보다 먼저다. 인증 없는 요청이 어떤 경로가 실재하는지 알 수 없다."""
    assert (await client.get(GUARDED)).status_code == 401


async def test_틀린_토큰도_빈_토큰도_401이다(client: AsyncClient) -> None:
    """헤더 부재를 빈 문자열로 다루는 구현과 겹치면 그 자체가 fail-open 이다."""
    headers: tuple[dict[str, str], ...] = (
        {},
        {"Authorization": "Bearer wrong-token"},
        {"Authorization": "Bearer"},
        {"Authorization": "Bearer "},
        {"Authorization": ""},
        {"Authorization": TOKEN},
        {"Authorization": f"Basic {TOKEN}"},
    )

    for header in headers:
        response = await client.get(GUARDED, headers=header)
        assert response.status_code == 401, header


async def test_비ASCII_토큰도_500이_아니라_401이다(client: AsyncClient) -> None:
    """원격 입력이 상태 코드를 바꾸지 못한다. `hmac` 의 str 비교는 non-ASCII 에서 TypeError 다.

    바이트로 미는 이유는 헤더가 원래 바이트이기 때문이다. 클라이언트 라이브러리가 ASCII 만
    보내 주더라도 경계에 실제로 닿는 것은 임의의 바이트다.
    """
    headers = {b"Authorization": "Bearer 토큰이-아닌-값".encode()}

    response = await client.get(GUARDED, headers=headers)

    assert response.status_code == 401


async def test_허용되지_않는_메서드도_봉투이고_어휘가_넷_안에_있다(client: AsyncClient) -> None:
    """405 는 프레임워크가 내는 것이라 표에 없다. 어휘를 넷으로 지키려고 계열로 접는다."""
    response = await client.post("/health")

    assert response.status_code == 405
    assert response.json()["code"] == "invalid_request"


async def test_405가_어떤_메서드를_쓸_수_있는지_알려_준다(client: AsyncClient) -> None:
    """RFC 9110 이 405 에 Allow 를 요구한다. 라우터가 붙인 헤더를 봉투가 버리면 안 된다."""
    response = await client.post("/health")

    assert "GET" in response.headers["Allow"]


async def test_401이_어떤_인증을_쓰는지_알려_준다(client: AsyncClient) -> None:
    """RFC 9110 이 401 에 WWW-Authenticate 를 요구한다. 방식을 알리는 것은 노출이 아니다 —
    401 자체가 이미 인증이 필요하다고 말한다."""
    response = await client.get(GUARDED)

    assert response.headers["WWW-Authenticate"] == "Bearer"


async def test_맞는_토큰은_미들웨어를_지나_라우팅까지_간다(client: AsyncClient) -> None:
    """401 이 아니라 404 라는 것이 곧 지나갔다는 뜻이다. 이 경로에는 라우트가 없다."""
    assert (await client.get(GUARDED, headers=BEARER)).status_code == 404


def test_빈_토큰으로는_앱을_세울_수_없다(stderr: io.StringIO) -> None:
    """토큰 없이 도는 서버를 기본값으로 남기지 않는다. 진단과 종료 코드는 03 의 것이다."""
    plugins: PluginSource = FakePlugins()
    trace: TraceStore = FakeTrace()

    with pytest.raises(ValueError):
        create_app(plugins=plugins, trace=trace, token="", stderr=stderr)


async def test_에러_응답이_봉투이고_code_가_상태_코드와_짝이다(client: AsyncClient) -> None:
    response = await client.get(GUARDED)
    body = response.json()

    assert set(body) == {"code", "message", "violations", "request_id"}
    assert body["code"] == "unauthorized"
    assert body["message"]
    assert body["violations"] == []


async def test_성공_응답은_봉투가_아니고_추적_식별자가_헤더로_나간다(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.headers["X-Request-Id"]
    assert "request_id" not in response.json()


async def test_에러_봉투의_추적_식별자가_헤더와_같은_값이다(client: AsyncClient) -> None:
    response = await client.get(GUARDED)

    assert response.json()["request_id"] == response.headers["X-Request-Id"]


async def test_요청마다_추적_식별자가_다르다(client: AsyncClient) -> None:
    first = (await client.get("/health")).headers["X-Request-Id"]
    second = (await client.get("/health")).headers["X-Request-Id"]

    assert first != second


async def test_에러_하나가_서버_표준_에러에_같은_추적_식별자로_한_줄_남는다(
    client: AsyncClient, stderr: io.StringIO
) -> None:
    """화면에서 본 오류를 서버 기록과 잇는 상관 키다. 감사 로그가 아니다(스토리 31)."""
    response = await client.get(GUARDED)

    lines = stderr.getvalue().splitlines()
    assert len(lines) == 1
    assert response.headers["X-Request-Id"] in lines[0]


async def test_성공한_요청은_서버_표준_에러에_남지_않는다(
    client: AsyncClient, stderr: io.StringIO
) -> None:
    """누가 무엇을 조회했는지는 남기지 않는다. 감사 로그는 비목표다."""
    await client.get("/health")

    assert stderr.getvalue() == ""


async def test_요청이_들고_온_토큰이_응답에도_서버_기록에도_나타나지_않는다(
    client: AsyncClient, stderr: io.StringIO
) -> None:
    """원칙 V. 맞는 토큰도 틀린 토큰도 되울리지 않는다."""
    wrong = "secret-looking-value-from-the-wire"

    rejected = await client.get(GUARDED, headers={"Authorization": f"Bearer {wrong}"})
    accepted = await client.get(GUARDED, headers=BEARER)

    assert wrong not in rejected.text
    assert wrong not in stderr.getvalue()
    assert TOKEN not in accepted.text
    assert TOKEN not in stderr.getvalue()


async def test_없는_경로는_404이고_code_가_not_found_다(client: AsyncClient) -> None:
    response = await client.get("/nowhere", headers=BEARER)

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


async def test_core_의_구성_오류는_500이고_code_가_internal_error_다(
    app: FastAPI, client: AsyncClient
) -> None:
    """부재가 이미 404 로 갈리므로 PluginError 에 남는 것은 서버 디스크의 문제뿐이다(ADR 0010)."""
    _route_that_raises(app, "/broken", PluginError("매니페스트를 읽을 수 없다: plugin.toml"))

    response = await client.get("/broken", headers=BEARER)

    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert "plugin.toml" in response.json()["message"]


async def test_예기치_않은_실패도_봉투이고_내부_문구를_밖으로_내지_않는다(
    app: FastAPI, client: AsyncClient, stderr: io.StringIO
) -> None:
    """운영자는 서버 기록에서 원인을 찾고 클라이언트는 상관 키만 받는다."""
    _route_that_raises(app, "/oops", RuntimeError("내부 사정이 담긴 문구"))

    response = await client.get("/oops", headers=BEARER)

    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert "내부 사정이 담긴 문구" not in response.text
    assert "내부 사정이 담긴 문구" in stderr.getvalue()
    assert response.headers["X-Request-Id"] == response.json()["request_id"]


async def test_질의_형식_오류는_422이고_violations_가_점으로_이은_경로를_든다(
    app: FastAPI, client: AsyncClient
) -> None:
    """422 는 FastAPI 가 내고 봉투만 우리 것이다. 질의 검증 자체는 04·05 의 것이다."""

    @app.get("/paged")
    def _paged(limit: int = 1) -> Health:  # pragma: no cover - 검증에서 끝나 몸통에 닿지 않는다
        return Health(status="ok")

    response = await client.get("/paged?limit=not-a-number", headers=BEARER)

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "invalid_request"
    assert [violation["field"] for violation in body["violations"]] == ["query.limit"]
    assert body["violations"][0]["message"]


def test_스키마에_이름_있는_타입이_나온다(app: FastAPI) -> None:
    """생성 클라이언트의 타입 이름이 익명 구조체가 되지 않는다(스토리 28)."""
    components = app.openapi().get("components", {})
    schemas = components.get("schemas", {})

    assert {"Health", "ErrorEnvelope", "Violation"} <= set(schemas)


def test_에러_봉투의_code_어휘가_상태_코드와_1대1인_넷이다(app: FastAPI) -> None:
    """어휘가 openapi.json 에 박힌다. 슬라이스 3 이 에러 처리를 한 곳에서 받는 근거다."""
    schemas = app.openapi().get("components", {}).get("schemas", {})

    assert set(schemas["ErrorCode"]["enum"]) == {
        "unauthorized",
        "invalid_request",
        "not_found",
        "internal_error",
    }


def test_create_app_이_도구_포트를_받지_않는다() -> None:
    """조회가 MCP 서버를 띄우는 것이 구조적으로 불가능하다(스토리 7)."""
    parameters = inspect.signature(create_app).parameters

    assert "tools" not in parameters
    assert ToolSource not in get_type_hints(create_app).values()


def test_모듈_수준_전역_앱이_없다() -> None:
    """전역 앱은 import 시점에 경로를 고정해 테스트가 진짜 파일시스템을 쓰게 만든다(ADR 0010)."""
    assert "app" not in vars(server_module)


# 플러그인 — 등록된 것을 한 곳에서 본다(티켓 04)


async def test_플러그인_목록이_종류들을_한_평평한_목록으로_주고_항목마다_종류를_든다(
    client: AsyncClient,
) -> None:
    """클라이언트가 종류로 가른다. 종류마다 경로가 갈리면 PRD 의 "한 곳"이 아니다(스토리 2)."""
    response = await client.get("/plugins", headers=BEARER)

    assert response.status_code == 200
    rows = response.json()
    assert [(row["kind"], row["name"]) for row in rows] == [
        ("agent", "broken"),
        ("agent", "calc"),
        ("mcp", "everything"),
        ("skill", "summarize"),
        ("model", "sonnet"),
    ]


async def test_목록의_항목이_매니페스트_그대로라_승인_대상_도구가_보인다(
    client: AsyncClient,
) -> None:
    """가드레일의 범위를 코드를 읽지 않고 안다(스토리 3). interrupts 가 필드로 닫은 것을 읽는
    면이다."""
    rows = (await client.get("/plugins", headers=BEARER)).json()

    calc = next(row for row in rows if row["name"] == "calc")
    assert calc == CALC.model_dump(mode="json")
    assert calc["requires_approval"] == ["add"]


async def test_mcp_매니페스트의_command_와_args_도_가리지_않고_내보낸다(
    client: AsyncClient,
) -> None:
    """가리지 않는 것이 결정이고 경계는 인증이다(ADR 0009 의 2026-09-22 이력, 네 번째 열린 문제).

    MCP 구성을 디버깅하는 사람이 정확히 이 둘을 봐야 한다. 가리는 날에는 이 테스트가 먼저 바뀐다.
    """
    rows = (await client.get("/plugins", headers=BEARER)).json()

    everything = next(row for row in rows if row["name"] == "everything")
    assert everything["server"]["command"] == "npx"
    assert everything["server"]["args"] == ["-y", "@modelcontextprotocol/server-everything"]


async def test_읽을_수_없는_매니페스트가_있어도_나머지가_오고_그것은_종류_이름_이유를_든_표지다(
    client: AsyncClient,
) -> None:
    """조용히 빠지면 등록했다고 믿는 것과 실제가 어긋나고, 전체가 실패하면 무엇이 살아 있는지조차
    모른다(스토리 5·6)."""
    response = await client.get("/plugins", headers=BEARER)

    assert response.status_code == 200
    rows = response.json()
    assert {
        "kind": "agent",
        "name": "broken",
        "reason": "매니페스트를 읽을 수 없다: plugins/agents/broken/plugin.toml",
    } in rows
    assert {row["name"] for row in rows} == {"broken", "calc", "everything", "summarize", "sonnet"}


async def test_플러그인_하나를_물으면_매니페스트를_통째로_돌려준다(client: AsyncClient) -> None:
    """목록이 말해 주지 않는 세부를 확인하는 자리다(스토리 4)."""
    response = await client.get("/plugins/agent/calc", headers=BEARER)

    assert response.status_code == 200
    assert response.json() == CALC.model_dump(mode="json")


async def test_없는_플러그인은_404이고_code_가_not_found_다(client: AsyncClient) -> None:
    """내 오타와 서버의 문제가 갈린다(스토리 18). 같은 이름이라도 종류가 다르면 없는 것이다."""
    for path in ("/plugins/agent/nothing", "/plugins/mcp/calc"):
        response = await client.get(path, headers=BEARER)

        assert response.status_code == 404, path
        assert response.json()["code"] == "not_found", path


async def test_읽을_수_없는_매니페스트는_목록에서는_표지이고_단건으로는_500이다(
    client: AsyncClient,
) -> None:
    """비대칭이 의도다(ADR 0012 의 2026-09-22 이력). 목록은 "무엇이 있나"라서 하나가 깨져도 나머지가
    답이고, 단건은 그 파일 하나를 달라는 것이라 실패가 곧 답이다. 4xx 면 운영자가 잘못 요청했다고
    믿고 깨진 파일을 못 찾는다(스토리 19)."""
    rows = (await client.get("/plugins", headers=BEARER)).json()
    single = await client.get("/plugins/agent/broken", headers=BEARER)

    assert any(row["name"] == "broken" and "reason" in row for row in rows)
    assert single.status_code == 500
    assert single.json()["code"] == "internal_error"
    assert "plugins/agents/broken/plugin.toml" in single.json()["message"]


async def test_없는_종류는_422이고_포트가_불리지_않는다(
    client: AsyncClient, plugins: FakePlugins
) -> None:
    """없는 종류는 부재가 아니라 형식 오류다. 404 면 그런 종류가 있는데 비었다고 읽힌다."""
    response = await client.get("/plugins/agents/calc", headers=BEARER)

    assert response.status_code == 422
    assert [violation["field"] for violation in response.json()["violations"]] == ["path.kind"]
    assert plugins.calls == 0


# 루트를 벗어나려는 이름들. 경로 조각이 `plugins/{kind}/{name}/plugin.toml` 로 그대로 조립되므로
# 하나라도 포트에 닿으면 루트 밖을 읽는다. 퍼센트 인코딩으로 적는 이유는 httpx 가 맨 `..` 조각을
# 보내기 전에 정규화해 지워 버리기 때문이다 — 그러면 요청이 `/plugins` 로 가서 이 단언이 엉뚱한
# 이유로 통과한다. 서버는 이것들을 디코딩된 채로 받는다(`%2F` 는 `/` 가 된다).
ESCAPING_NAMES = (
    "%2E%2E",  # ..
    "..%2F..%2Fetc",  # ../../etc
    "..%5C..%5Csecret",  # ..\..\secret — 윈도가 주 환경이라 역슬래시도 구분자다
    "%2Fetc%2Fpasswd",  # /etc/passwd — pathlib 의 / 는 오른쪽이 절대 경로면 왼쪽을 버린다
    "C:%5CWindows",  # C:\Windows
    "C:%2FWindows",  # C:/Windows
)


async def test_루트를_벗어나려는_이름은_422이고_포트가_아예_불리지_않는다(
    client: AsyncClient, plugins: FakePlugins
) -> None:
    """검증이 파일시스템에 닿기 전에 끝난다(스토리 43). 404 와 500 이 갈리는 것 자체가 임의 경로의
    파일 존재를 알려 주는 오라클이라, 포트가 한 번이라도 불리면 그 오라클이 열린다."""
    for name in ESCAPING_NAMES:
        response = await client.get(f"/plugins/agent/{name}", headers=BEARER)

        assert response.status_code == 422, name
        fields = [violation["field"] for violation in response.json()["violations"]]
        assert fields == ["path.name"], name
    assert plugins.calls == 0


async def test_개행이_섞인_이름도_422이고_포트가_불리지_않는다(
    client: AsyncClient, plugins: FakePlugins
) -> None:
    """형식 위반은 자리가 어디든 422 다. 라우팅 정규식이 파이썬 `re` 라서 `.` 은 개행을 넘지 못하고
    `$` 는 마지막 개행 앞에서도 맞는다. 그 규칙대로면 가운데 개행은 라우트가 안 맞아 404 가 되고
    꼬리 개행은 떼어져 `calc` 로 읽힌다. 둘 다 내 오타와 서버의 문제를 가르는 표를 어긴다."""
    for name in ("calc%0A", "%0Acalc", "calc%0Ax"):
        response = await client.get(f"/plugins/agent/{name}", headers=BEARER)

        assert response.status_code == 422, name
    assert plugins.calls == 0


def test_경로에_거는_이름_패턴이_sdk_가_매니페스트에_거는_그것이고_계약에_박힌다(
    app: FastAPI,
) -> None:
    """새 규칙이 아니라 있는 계약을 조회 쪽에도 거는 것이다."""
    parameters = app.openapi()["paths"]["/plugins/{kind}/{name}"]["get"]["parameters"]
    name = next(parameter for parameter in parameters if parameter["name"] == "name")

    assert name["schema"]["pattern"] == PLUGIN_NAME_PATTERN


def test_문서화된_에러_응답이_전부_봉투이고_내는_에러를_빠뜨리지_않는다(app: FastAPI) -> None:
    """라우트를 더하며 적는 것을 잊으면 이 테스트가 깨진다. 401 은 미들웨어가 내는 것이라
    프레임워크가 적어 주지 않고, FastAPI 가 파라미터 있는 라우트에 붙이는 제 422 모양은 우리 봉투가
    아니라 그대로 두면 계약이 거짓말을 한다."""
    document = app.openapi()
    envelope = {"$ref": "#/components/schemas/ErrorEnvelope"}

    for path, operations in document["paths"].items():
        for method, operation in operations.items():
            where = f"{method} {path}"
            responses = operation["responses"]
            errors = {status for status in responses if not status.startswith("2")}
            assert "500" in errors, where
            if path not in PUBLIC_PATHS:
                assert "401" in errors, where
            if operation.get("parameters"):
                assert "422" in errors, where
            for status in errors:
                schema = responses[status]["content"]["application/json"]["schema"]
                assert schema == envelope, (where, status)
    assert "404" in document["paths"]["/plugins/{kind}/{name}"]["get"]["responses"]
    assert "HTTPValidationError" not in document["components"]["schemas"]


def test_표지의_HTTP_모양이_core_의_표지와_같은_필드를_든다() -> None:
    """관리 쪽 모델이 core 의 표지를 옮긴 것이라 필드 목록이 두 곳이다. core 에 필드가 늘면 여기가
    빨개져 관리 쪽이 조용히 뒤처지지 않는다. 매니페스트에 별도 타입을 두지 않은 이유가 이것이다
    (ADR 0010 의 2026-09-23 이력)."""
    assert set(admin_http.UnreadableManifest.model_fields) == {
        field.name for field in dataclasses.fields(UnreadableManifest)
    }


def test_늘_실리는_매니페스트_필드는_계약에서도_required_다(app: FastAPI) -> None:
    """서버는 필드를 언제나 전부 싣는다. 기본값 있는 필드가 required 에서 빠지면 생성 클라이언트가
    `requires_approval` 을 선택 필드로 받는다 — 이 티켓이 보이려는 바로 그 필드다."""
    schemas = app.openapi()["components"]["schemas"]

    assert set(schemas["PluginManifest"]["required"]) == set(PluginManifest.model_fields)
    assert set(schemas["McpServer"]["required"]) == set(McpServer.model_fields)
    assert set(schemas["UnreadableManifest"]["required"]) == {"kind", "name", "reason"}


def test_플러그인_목록의_행_타입이_이름_있는_스키마다(app: FastAPI) -> None:
    """생성 클라이언트가 익명 유니온 대신 이름 있는 타입을 받는다(스토리 28)."""
    document = app.openapi()
    schemas = document["components"]["schemas"]
    ok = document["paths"]["/plugins"]["get"]["responses"]["200"]
    items = ok["content"]["application/json"]["schema"]["items"]

    assert items == {"$ref": "#/components/schemas/PluginRow"}
    assert schemas["PluginRow"] == {
        "anyOf": [
            {"$ref": "#/components/schemas/PluginManifest"},
            {"$ref": "#/components/schemas/UnreadableManifest"},
        ]
    }
