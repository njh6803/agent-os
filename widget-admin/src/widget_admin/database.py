"""위젯 관리 서버의 데이터베이스 객체: 연결 묶음 하나, 표 올리기, 설정 읽기(ADR 0064).

엔진을 짓고 연결을 여는 코드는 `widget_admin` 안에서 이 모듈뿐이다. 연결 문자열을
읽는 일, 닿을 때까지 다시 시도하는 일, 표의 판을 견주는 일은 이 판에 없고 서버를 띄우는 명령의
몫이다(티켓 03). 이 판의 객체는 주소 글을 받아 엔진을 짓고, 표를 올리고(`migrate`), 설정 한 줄을
읽고(`read_widget_settings`), 닫는다(`close`).

**엔진 설정은 Agent OS 의 어댑터와 같다.** 연결이 끊긴 것을 쓰지 않도록 `pool_pre_ping=True` 이고,
`hide_parameters=True` 로 SQL 의 바인드 값이 역추적에 실리지 않게 한다. 사이트 이름은 누구나 고를 수
있는 값이라 기록에 남기지 않는다.

**읽기는 칸을 이름으로 고른다.** `SELECT *` 가 아니다. 표에 칸이 더 생겨도(다른 묶음이나 뒤의 판이
더한 칸) 응답에 새지 않는다.

**마이그레이션은 객체가 연 연결로 돈다.** alembic 환경(`migrations/env.py`)은 `config.attributes` 로
받은 연결을 쓰고 스스로 이벤트 루프를 열지 않는다. 올리기 전체는 `engine.begin()` 트랜잭션 하나다.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import Connection, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from widget_admin.settings import (
    COLUMNS,
    SCHEMA_VERSION,
    ExpiryNoticeStyle,
    LoginPromptStyle,
    LogoutMethod,
    Mode,
    NoticeFullStyle,
    Theme,
    WidgetSettings,
)

MIGRATIONS = Path(__file__).resolve().parent / "migrations"
PRODUCT_VERSIONS = MIGRATIONS / "versions"

_SELECT = text(f"SELECT {', '.join(COLUMNS)} FROM sites WHERE name = :name")


class WidgetAdminDatabase:
    """연결 묶음 하나와 위젯 설정 표를 다루는 객체."""

    def __init__(self, url_text: str) -> None:
        # 접속 주소의 앞부분을 드라이버가 붙은 꼴로 바꾼다. 이 판은 주소를 읽어 검사하지 않는다.
        driver_url = url_text.replace("postgresql://", "postgresql+asyncpg://", 1)
        self._engine: AsyncEngine = create_async_engine(
            driver_url, pool_pre_ping=True, hide_parameters=True
        )

    async def migrate(self) -> None:
        """표를 마지막 판까지 올린다. 실패하면 예외를 던진다."""
        async with self._engine.begin() as connection:
            await connection.run_sync(self._upgrade)

    async def read_widget_settings(self, site: str) -> WidgetSettings | None:
        """사이트 하나의 위젯 설정(질의). 등록되지 않은 이름이면 `None`. 데이터베이스 실패는
        던진다."""
        async with self._engine.connect() as connection:
            result = await connection.execute(_SELECT, {"name": site})
            row = result.mappings().first()
        if row is None:
            return None
        return WidgetSettings(
            schema_version=SCHEMA_VERSION,
            agent=row["agent"],
            heading=row["heading"],
            intro=row["intro"],
            theme=_word(Theme, row["theme"]),
            mode=_word(Mode, row["mode"]),
            placeholder=row["placeholder"],
            notice_summary=row["notice_summary"],
            notice_full=row["notice_full"],
            login_url=row["login_url"],
            login_label=row["login_label"],
            logout_url=row["logout_url"],
            logout_method=_word(LogoutMethod, row["logout_method"]),
            expiry_notice_style=_word(ExpiryNoticeStyle, row["expiry_notice_style"]),
            tab_title=row["tab_title"],
            contact_url=row["contact_url"],
            example_questions=tuple(row["example_questions"]),
            hide_mode_switch=row["hide_mode_switch"],
            login_prompt_style=_word(LoginPromptStyle, row["login_prompt_style"]),
            notice_full_style=_word(NoticeFullStyle, row["notice_full_style"]),
        )

    async def close(self) -> None:
        """연결 묶음을 닫는다. 남은 연결이 없게 한다."""
        await self._engine.dispose()

    def _config(self) -> Config:
        config = Config()
        # configparser 의 `%` 해석을 피한다. 경로를 설정 파일 없이 코드로 준다.
        config.set_main_option("script_location", str(MIGRATIONS).replace("%", "%%"))
        config.set_main_option("version_locations", str(PRODUCT_VERSIONS).replace("%", "%%"))
        # 폴더는 하나이므로 경로에 들 수 없는 줄바꿈으로 가른다.
        config.set_main_option("path_separator", "newline")
        return config

    def _upgrade(self, connection: Connection) -> None:
        config = self._config()
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


def _word[Word: (Theme, Mode, LogoutMethod, ExpiryNoticeStyle, LoginPromptStyle, NoticeFullStyle)](
    kind: type[Word], value: object
) -> Word | None:
    """표의 글을 이름 있는 어휘로 바꾼다(질의). 칸이 비었으면 `None`. 어휘 밖의 글은 표의 `CHECK` 가
    막으므로 여기서 예외가 나면 표가 규칙을 어긴 것이다."""
    if value is None:
        return None
    return kind(value)
