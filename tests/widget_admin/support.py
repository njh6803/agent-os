"""위젯 관리 서버 시험의 도우미. 표에 줄을 SQL 로 직접 넣고, 앱을 지어 부른다.

데이터베이스를 가짜로 바꾸지 않는다. 이 서버의 일은 거의 다 표를 읽는 질의라 가짜로 본 시험은 질의를
보지 못한다(명세 widget-admin-server Testing Decisions).
"""

from __future__ import annotations

import io
from collections.abc import AsyncGenerator, Mapping
from contextlib import asynccontextmanager

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from tests.postgres_support import plain
from tools.database_for_tests import ScopedDatabase

from widget_admin.database import WidgetAdminDatabase
from widget_admin.server import create_app

# 위젯 설정의 열아홉 칸을 전부 채운 값. 답의 열쇠는 `schema_version` 과 이 열아홉이다.
FULL_SETTINGS: Mapping[str, object] = {
    "agent": "assistant",
    "heading": "도우미",
    "intro": "무엇이든 물어보세요.",
    "theme": "nokcheong",
    "mode": "dark",
    "placeholder": "질문을 입력하세요",
    "notice_summary": "답변은 부정확할 수 있습니다.",
    "notice_full": "첫째 문단입니다.\n\n둘째 문단입니다.\n줄바꿈이 한 번 있습니다.",
    "login_url": "https://example.com/login",
    "login_label": "로그인",
    "logout_url": "https://example.com/logout",
    "logout_method": "new_window",
    "expiry_notice_style": "banner",
    "tab_title": "도우미 창",
    "contact_url": "https://example.com/contact",
    "example_questions": ["첫 질문", "둘째 질문"],
    "hide_mode_switch": True,
    "login_prompt_style": "intro_button",
    "notice_full_style": "overlay",
}

BODY_KEYS = frozenset({"schema_version", *FULL_SETTINGS})


async def insert_site(
    database: ScopedDatabase, name: str, settings: Mapping[str, object] | None = None
) -> None:
    """`sites` 에 줄 하나를 넣는다. 넣지 않은 칸은 표의 기본값이다."""
    values = {"name": name, **(settings or {})}
    columns = ", ".join(values)
    marks = ", ".join(f":{key}" for key in values)
    async with plain(database) as connection:
        await connection.execute(text(f"INSERT INTO sites ({columns}) VALUES ({marks})"), values)
        await connection.commit()


@asynccontextmanager
async def client_for(
    database: WidgetAdminDatabase, stderr: io.StringIO | None = None
) -> AsyncGenerator[AsyncClient]:
    """지은 앱을 `ASGITransport` 로 부르는 클라이언트."""
    app = create_app(database=database, stderr=stderr or io.StringIO())
    async with client_of(app) as client:
        yield client


@asynccontextmanager
async def client_of(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://widget-admin.test") as client:
        yield client
