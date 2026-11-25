"""`GET /widget-settings/<사이트 이름>` 의 갈래 넷과 답의 모양(명세 widget-admin-server "읽는 경로",
"답의 모양", "판 표시").

진짜 테스트 데이터베이스에 위젯 설정을 SQL 로 넣고, 앱을 짓는 함수로 지은 앱을 `ASGITransport` 로
부른다. 값은 표에서 바꾸지 않고 그대로 실린다.
"""

from __future__ import annotations

from tests.widget_admin.support import BODY_KEYS, FULL_SETTINGS, client_for, insert_site
from tools.database_for_tests import ScopedDatabase

from widget_admin.database import WidgetAdminDatabase


async def test_넣은_위젯_설정이_판_표시와_열아홉_열쇠로_실린다(
    database: ScopedDatabase, opened: WidgetAdminDatabase
) -> None:
    await insert_site(database, "acme", FULL_SETTINGS)

    async with client_for(opened) as client:
        response = await client.get("/widget-settings/acme")

    assert response.status_code == 200
    assert response.json() == {"schema_version": 1, **FULL_SETTINGS}


async def test_값을_넣지_않은_칸은_null이고_예시_질문은_빈_목록_밝기_스위치_숨기기는_거짓이다(
    database: ScopedDatabase, opened: WidgetAdminDatabase
) -> None:
    await insert_site(database, "bare-site")

    async with client_for(opened) as client:
        response = await client.get("/widget-settings/bare-site")

    body = response.json()
    assert response.status_code == 200
    assert set(body) == BODY_KEYS
    assert body["schema_version"] == 1
    assert body["example_questions"] == []
    assert body["hide_mode_switch"] is False
    nulls = BODY_KEYS - {"schema_version", "example_questions", "hide_mode_switch"}
    assert {key: body[key] for key in nulls} == dict.fromkeys(nulls)
