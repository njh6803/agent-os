"""주 이음매. create_app() 이 만든 앱에 ASGI 로 요청을 넣고 바깥 행동만 단언한다.

이 티켓은 데이터 라우트를 하나도 만들지 않는다. 여기서 재는 것은 셋이다 — 뒤로 붙는 모든
라우트가 보호를 켜지 않아도 기본으로 막힌다는 것, 에러가 언제나 같은 봉투로 나간다는 것,
인증 없이 경계 밖으로 나가는 응답이 /health 하나뿐이라는 것.

가짜 포트는 상속하지 않고 시그니처로 만족하며 픽스처가 포트 타입으로 annotate 한다. 그 한 줄이
포트 적합성이 검증되는 자리다. 네트워크도 디스크도 타지 않는다.
"""

import inspect
import io
from collections.abc import AsyncIterator, Sequence
from typing import get_type_hints

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from agent_os import server as server_module
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
)
from agent_os.sdk import BaseAgent, Event, PluginKind, PluginManifest, PluginName, RunId
from agent_os.server import create_app

TOKEN = "t0ken-that-only-tests-know"
BEARER = {"Authorization": f"Bearer {TOKEN}"}
# allowlist 밖이면서 라우트가 아직 없는 경로. 02 는 데이터 라우트를 만들지 않으므로 미들웨어가
# 라우팅보다 먼저 막는다는 사실을 이 경로 하나가 드러낸다.
GUARDED = "/plugins"


class FakePlugins:
    """02 는 데이터 라우트를 만들지 않으므로 불리지 않는다. 불리면 그 자체가 결함이라 터뜨린다."""

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None:
        raise NotImplementedError("플러그인 라우트는 04 의 것이다")

    def list_manifests(self, kind: PluginKind) -> Sequence[ManifestRow]:
        raise NotImplementedError("플러그인 라우트는 04 의 것이다")

    def load_agent(self, manifest: PluginManifest) -> BaseAgent:
        raise NotImplementedError("관리는 실행을 일으키지 않는다")


class FakeTrace:
    """같은 이유로 불리지 않는다. 트레이스 라우트는 05·06 의 것이다."""

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
def app(stderr: io.StringIO) -> FastAPI:
    plugins: PluginSource = FakePlugins()
    trace: TraceStore = FakeTrace()
    return create_app(plugins=plugins, trace=trace, token=TOKEN, stderr=stderr)


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

    데이터 라우트는 04·05·06 의 것이라 여기서 만들지 않는다. 이 라우트는 표가 실제로 도는지
    보기 위한 것이고, 같은 표를 그 티켓들이 진짜 라우트로 다시 잰다.
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
    """라우트를 더하고 보호를 잊으면 이 테스트가 깨진다. fail-closed 라 벨트이지 전부가 아니다.

    라우트를 하나 붙이고 도는 이유는 02 의 문서화된 경로가 `/health` 하나뿐이기 때문이다. 붙이지
    않으면 이 루프는 allowlist 만 돌아 401 을 한 번도 단언하지 않는 빈 벨트가 된다. 붙인 라우트는
    04·05·06 이 더할 라우트의 대역이고 보호를 켜지 않는다.
    """
    _route_that_raises(app, "/later", PluginError("보호가 먼저라 불리지 않는다"))
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
    """401 이 아니라 404 라는 것이 곧 지나갔다는 뜻이다. 데이터 라우트는 아직 없다."""
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
