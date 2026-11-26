"""위젯 관리 서버 시험의 도우미. 표에 줄을 SQL 로 직접 넣고, 앱을 지어 부른다.

데이터베이스를 가짜로 바꾸지 않는다. 이 서버의 일은 거의 다 표를 읽는 질의라 가짜로 본 시험은 질의를
보지 못한다(명세 widget-admin-server Testing Decisions).
"""

from __future__ import annotations

import io
from collections.abc import AsyncGenerator, Mapping
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from tests.postgres_support import plain
from tools.database_for_tests import ScopedDatabase

from widget_admin.database import DatabaseUrl, WidgetAdminDatabase, parse_database_url
from widget_admin.server import create_app

# 시험이 짧게 주는 다시 시도 시간과 시도 하나의 제한 시간. 기본값(30초, 5초)을 쓰면 시험이 느리다.
SHORT_RETRY = 0.6
SHORT_INTERVAL = 0.1
SHORT_ATTEMPT = 0.4
# 닿아야 하는 시험은 부하가 큰 실행에서도 시간 때문에 빨개지지 않게 넉넉히 준다. 짧은 값은 시간이
# 지나는 갈래를 일부러 보는 시험만 쓴다(`.claude/rules/tests.md`).
PATIENT_RETRY = 8.0
PATIENT_ATTEMPT = 8.0
# 시간 단언의 상한은 홀로 돈 시간의 넉넉한 배수다(`.claude/rules/tests.md`).
GENEROUS = 20.0
# 비밀번호가 글에 실리는지 보려고 계정 이름과 다른, 알아볼 수 있는 값을 쓴다.
SECRET = "leak_probe_pw"

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


def database_url(value: str) -> DatabaseUrl:
    """주소 글을 읽는다. 읽지 못하면 시험이 잘못된 것이다."""
    url = parse_database_url(value)
    if url is None:
        raise AssertionError("위젯 관리 서버가 읽지 못한 주소다")
    return url


class Notices:
    """데이터베이스 객체가 알린 글을 모은다."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def __call__(self, message: str) -> None:
        self.lines.append(message)


def adapter(
    address: str,
    versions: Path,
    notices: Notices,
    *,
    retry_seconds: float = SHORT_RETRY,
    attempt_seconds: float = SHORT_ATTEMPT,
) -> WidgetAdminDatabase:
    """다시 시도 시간과 시도 하나의 제한 시간을 짧게 준 객체. 마이그레이션 폴더도 시험이 고른다."""
    return WidgetAdminDatabase(
        database_url(address),
        notice=notices,
        versions=versions,
        retry_seconds=retry_seconds,
        retry_interval=SHORT_INTERVAL,
        attempt_seconds=attempt_seconds,
    )


def patient(address: str, versions: Path, notices: Notices) -> WidgetAdminDatabase:
    """닿는 서버를 상대로 시간 제한에 걸리지 않을 넉넉한 값으로 객체를 짓는다."""
    return adapter(
        address,
        versions,
        notices,
        retry_seconds=PATIENT_RETRY,
        attempt_seconds=PATIENT_ATTEMPT,
    )


def address_of(
    database: ScopedDatabase,
    *,
    username: str | None = None,
    password: str | None = None,
    port: int | None = None,
    name: str | None = None,
) -> str:
    """접속 문자열. 계정, 비밀번호, 포트, 데이터베이스 이름 가운데 바꿀 것만 바꾼다."""
    url = database.address.url.set(database=name or database.name)
    if username is not None:
        url = url.set(username=username)
    if password is not None:
        url = url.set(password=password)
    if port is not None:
        url = url.set(port=port)
    return url.render_as_string(hide_password=False)
