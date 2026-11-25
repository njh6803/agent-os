"""읽는 경로의 나머지 갈래: 없는 것의 404, 데이터베이스 실패의 500, 표에 늘어난 칸(명세
widget-admin-server "읽는 경로", "오류 봉투와 기록").

등록되지 않은 이름과 꼴이 틀린 이름은 글자까지 같은 404 봉투여야 한다. 위젯이 둘을 가르면 이름을
하나씩 대 보는 탐색이 갈래로 정보를 얻는다. 꼴이 틀린 이름은 데이터베이스에 묻지 않는다. 빈
데이터베이스는 표가 없어 모든 질의가 실패하므로, 꼴이 틀린 이름이 404 로 답하는 것이 곧 묻지
않았다는 증거다.
"""

from __future__ import annotations

import io

import pytest
from sqlalchemy import text
from tests.postgres_support import plain
from tests.widget_admin.support import BODY_KEYS, client_for, insert_site
from tools.database_for_tests import ScopedDatabase

from widget_admin.database import WidgetAdminDatabase

NOT_FOUND: dict[str, object] = {"code": "not_found", "message": "찾는 것이 없다", "violations": []}

# 경로에 그대로 보낼 꼴이 틀린 이름. 퍼센트 인코딩은 httpx 가 보내기 전에 풀지 않는다.
MALFORMED = [
    "Acme",
    "a",
    "a" * 64,
    "1acme",
    "-acme",
    "acme_site",
    "한글",
    "a%2Fb",
    "%2E%2E",
    "acme%0A",
    "acme%20",
]


def _without_request_id(body: dict[str, object]) -> dict[str, object]:
    return {key: value for key, value in body.items() if key != "request_id"}


async def test_등록되지_않은_이름은_404_봉투다(
    database: ScopedDatabase, opened: WidgetAdminDatabase
) -> None:
    async with client_for(opened) as client:
        response = await client.get("/widget-settings/nobody")

    assert response.status_code == 404
    assert _without_request_id(response.json()) == NOT_FOUND
    assert response.json()["request_id"] == response.headers["X-Request-Id"]


@pytest.mark.parametrize("name", MALFORMED)
async def test_꼴이_틀린_이름은_등록되지_않은_이름과_글자까지_같은_404이고_묻지_않는다(
    name: str, opened_on_empty: WidgetAdminDatabase
) -> None:
    async with client_for(opened_on_empty) as client:
        response = await client.get(f"/widget-settings/{name}")

    assert response.status_code == 404
    assert _without_request_id(response.json()) == NOT_FOUND


@pytest.mark.parametrize("path", ["/widget-settings/", "/widget-settings", "/nothing-here"])
async def test_라우터가_찾지_못한_경로도_같은_404_봉투다(
    path: str, opened_on_empty: WidgetAdminDatabase
) -> None:
    async with client_for(opened_on_empty) as client:
        response = await client.get(path)

    assert response.status_code == 404
    assert _without_request_id(response.json()) == NOT_FOUND


async def test_끝에_슬래시를_붙인_이름은_돌려보내지_않고_404다(
    database: ScopedDatabase, opened: WidgetAdminDatabase
) -> None:
    await insert_site(database, "acme")

    async with client_for(opened) as client:
        response = await client.get("/widget-settings/acme/")

    assert response.status_code == 404
    assert "location" not in response.headers


async def test_표에_늘어난_칸은_응답에_새지_않는다(
    database: ScopedDatabase, opened: WidgetAdminDatabase
) -> None:
    await insert_site(database, "acme")
    async with plain(database) as connection:
        await connection.execute(text("ALTER TABLE sites ADD COLUMN secret text DEFAULT 'x'"))
        await connection.commit()

    async with client_for(opened) as client:
        response = await client.get("/widget-settings/acme")

    assert response.status_code == 200
    assert set(response.json()) == BODY_KEYS
    # 열쇠만이 아니라 늘어난 칸의 값도 답의 어디에도 없다.
    assert "secret" not in response.text


async def test_데이터베이스가_답하지_못하면_500_봉투이고_기록은_한_줄이다(
    opened_on_empty: WidgetAdminDatabase,
) -> None:
    stderr = io.StringIO()
    async with client_for(opened_on_empty, stderr) as client:
        response = await client.get("/widget-settings/acme-secret-name-q7x")

    body = response.json()
    assert response.status_code == 500
    assert body["code"] == "internal_error"
    assert body["message"] == "서버가 요청을 처리하지 못했다"
    assert body["violations"] == []
    # 봉투에도 사이트 이름이 없다.
    assert "acme-secret-name-q7x" not in response.text
    lines = stderr.getvalue().splitlines()
    assert len(lines) == 1
    assert f"request_id={body['request_id']}" in lines[0]
    assert "status=500" in lines[0]
    # 기록에는 사이트 이름도 경로도 접속 주소의 꼴(`계정:비밀번호@`)도 없다.
    assert "acme-secret-name-q7x" not in lines[0]
    assert "/widget-settings" not in lines[0]
    assert "@" not in lines[0]


async def test_성공한_요청은_기록에_남지_않는다(
    database: ScopedDatabase, opened: WidgetAdminDatabase
) -> None:
    await insert_site(database, "acme")
    stderr = io.StringIO()
    async with client_for(opened, stderr) as client:
        response = await client.get("/widget-settings/acme")

    assert response.status_code == 200
    assert "X-Request-Id" in response.headers
    assert stderr.getvalue() == ""
