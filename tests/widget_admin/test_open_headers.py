"""다른 출처에 여는 머리 셋은 위젯 설정 접두사 아래의 모든 응답에만 붙는다(명세 widget-admin-server
"응답 머리", "경로의 접두사").

200, 404, 405, 500, 핸들러가 놓친 예외의 500 모두에 붙고, `/health`와 접두사 밖의 경로에는 붙지
않는다. 허용 메서드와 자격 증명 머리는 싣지 않는다. 비교는 경로 조각 단위라 `/widget-settingsx` 는
접두사 밖이다.
"""

from __future__ import annotations

import io

import pytest
from fastapi import APIRouter, FastAPI
from httpx import Response
from tests.widget_admin.support import client_for, client_of, insert_site
from tools.database_for_tests import ScopedDatabase

from widget_admin.database import WidgetAdminDatabase
from widget_admin.server import create_app

OPEN = {
    "access-control-allow-origin": "*",
    "access-control-expose-headers": "X-Request-Id",
    "cache-control": "no-store",
}
NEVER = ("access-control-allow-methods", "access-control-allow-credentials")


def _has_all(response: Response) -> bool:
    return all(response.headers.get(name) == value for name, value in OPEN.items())


def _has_none(response: Response) -> bool:
    return not any(name in response.headers for name in OPEN)


def _no_extras(response: Response) -> bool:
    return not any(name in response.headers for name in NEVER)


async def test_200에_머리_셋이_붙는다(
    database: ScopedDatabase, opened: WidgetAdminDatabase
) -> None:
    await insert_site(database, "acme")

    async with client_for(opened) as client:
        response = await client.get("/widget-settings/acme")

    assert response.status_code == 200
    assert _has_all(response)
    assert _no_extras(response)


async def test_404에_머리_셋이_붙는다(opened: WidgetAdminDatabase) -> None:
    async with client_for(opened) as client:
        unregistered = await client.get("/widget-settings/nobody")
        malformed = await client.get("/widget-settings/Nobody")
        bare_prefix = await client.get("/widget-settings")

    for response in (unregistered, malformed, bare_prefix):
        assert response.status_code == 404
        assert _has_all(response)


@pytest.mark.parametrize("method", ["POST", "HEAD", "OPTIONS", "PUT", "DELETE"])
async def test_읽기_말고_다른_메서드는_405_봉투이고_머리_셋이_붙는다(
    method: str, opened_on_empty: WidgetAdminDatabase
) -> None:
    async with client_for(opened_on_empty) as client:
        response = await client.request(method, "/widget-settings/acme")

    assert response.status_code == 405
    assert _has_all(response)
    assert _no_extras(response)
    assert "x-request-id" in response.headers
    if method != "HEAD":
        assert response.json()["code"] == "invalid_request"


async def test_데이터베이스_실패의_500에_머리_셋이_붙는다(
    opened_on_empty: WidgetAdminDatabase,
) -> None:
    async with client_for(opened_on_empty) as client:
        response = await client.get("/widget-settings/acme")

    assert response.status_code == 500
    assert _has_all(response)
    assert "x-request-id" in response.headers


def _app_with_raising_route(database: WidgetAdminDatabase) -> FastAPI:
    app = create_app(database=database, stderr=io.StringIO())
    router = APIRouter()

    @router.get("/widget-settings/_boom/under")
    async def under() -> None:
        raise RuntimeError("핸들러가 놓친 예외")

    @router.get("/health-boom")
    async def outside() -> None:
        raise RuntimeError("핸들러가 놓친 예외")

    app.include_router(router)
    return app


async def test_핸들러가_놓친_예외의_500에도_접두사_아래면_머리_셋이_붙는다(
    opened_on_empty: WidgetAdminDatabase,
) -> None:
    app = _app_with_raising_route(opened_on_empty)

    async with client_of(app) as client:
        under = await client.get("/widget-settings/_boom/under")
        outside = await client.get("/health-boom")

    assert under.status_code == 500
    assert under.json()["code"] == "internal_error"
    assert _has_all(under)
    assert "x-request-id" in under.headers
    assert outside.status_code == 500
    assert _has_none(outside)


@pytest.mark.parametrize(
    "path",
    [
        "/health",
        "/operator/anything",
        "/internal/anything",
        "/widget-settingsx",
        "/widget-settingsx/a",
    ],
)
async def test_접두사_밖의_응답에는_머리가_붙지_않는다(
    path: str, opened_on_empty: WidgetAdminDatabase
) -> None:
    async with client_for(opened_on_empty) as client:
        response = await client.get(path)

    assert _has_none(response)
    assert "x-request-id" in response.headers
    if path != "/health":
        assert response.status_code == 404
        assert response.json()["code"] == "not_found"


async def test_health는_데이터베이스에_묻지_않고_200이다(
    opened_on_empty: WidgetAdminDatabase,
) -> None:
    async with client_for(opened_on_empty) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
