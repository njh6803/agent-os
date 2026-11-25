"""위젯 관리 서버의 시험 픽스처.

`tests/database.py` 의 픽스처 함수에 자기 마이그레이션을 올리는 함수와 접두 `widget_admin` 을 넘겨,
이 폴더의 시험이 `widget_admin_test_…` 데이터베이스를 받게 한다. 뿌리의 시험은 지금처럼
`agent_os_test_…` 를 받는다(명세 widget-admin-server "시험 폴더와 도우미").

`database_address`(서버 주소) 는 뿌리 `conftest.py` 의 것을 그대로 쓴다. 두 묶음의 시험이 같은
테스트 컨테이너의 서버를 쓰고, 이름의 접두만 다르다.

시험이 연 `WidgetAdminDatabase` 는 픽스처가 닫는다. 닫지 않은 엔진은 연결이 남아 데이터베이스를
지울 때 걸리거나 경고를 낸다.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from tests.database import (
    database_fixture,
    database_template_fixture,
    empty_database_fixture,
)
from tools.database_for_tests import ScopedDatabase

from widget_admin.database import WidgetAdminDatabase

DATABASE_PREFIX = "widget_admin"


async def _migrate_product(url_text: str) -> None:
    """위젯 쪽 제품 마이그레이션 폴더를 템플릿 데이터베이스에 올린다. 멈추면 예외를 던진다."""
    database = WidgetAdminDatabase(url_text)
    try:
        await database.migrate()
    finally:
        await database.close()


database_template = database_template_fixture(DATABASE_PREFIX, _migrate_product)
database = database_fixture(DATABASE_PREFIX)
empty_database = empty_database_fixture(DATABASE_PREFIX)


@pytest_asyncio.fixture
async def opened(database: ScopedDatabase) -> AsyncIterator[WidgetAdminDatabase]:
    """표가 마지막 판까지 올라간 데이터베이스에 연 객체. 시험이 끝나면 닫는다."""
    opened_database = WidgetAdminDatabase(database.text())
    try:
        yield opened_database
    finally:
        await opened_database.close()


@pytest_asyncio.fixture
async def opened_on_empty(empty_database: ScopedDatabase) -> AsyncIterator[WidgetAdminDatabase]:
    """표가 하나도 없는 빈 데이터베이스에 연 객체. 질의는 모두 실패한다."""
    opened_database = WidgetAdminDatabase(empty_database.text())
    try:
        yield opened_database
    finally:
        await opened_database.close()
