"""위젯 관리 서버의 데이터베이스 객체: 연결 묶음 하나, 뜰 때의 확인, 표의 판 견줌, 표 올리기, 설정
읽기.

엔진을 짓고 연결을 여는 코드는 `widget_admin` 안에서 이 모듈뿐이다(ADR 0064, ADR 0066). Agent OS 의
어댑터(`agent_os.adapters.postgres.database`)와 같은 일을 하는 사본이고, 포트와 어댑터를 나누지
않는다. 위젯 관리 서버에는 바깥을 모르게 지킬 core 가 없고, 이 서버의 일은 거의 다 표를 읽는 질의라
가짜 데이터베이스로는 질의를 볼 수 없어서다.

**엔진 설정은 Agent OS 와 같다.** 연결이 끊긴 것을 쓰지 않도록 `pool_pre_ping=True` 이고,
`hide_parameters=True` 로 SQL 의 바인드 값이 역추적에 실리지 않게 한다. 사이트 이름은 누구나 고를 수
있는 값이라 기록에 남기지 않는다.

**찍는 글은 값을 되울리지 않는다.** 연결 문자열에는 비밀번호가 들어 있어(원칙 V) 글에는 주소의
`호스트:포트/데이터베이스` 자리와 갈래, 까닭(오류 번호나 예외의 클래스 이름)만 싣는다. 접속 실패
글에는 드라이버가 낸 글도 싣지 않는다. 계정 이름이나 주소의 조각이 섞일 수 있어서다. 다만 올리다
실패했을 때는 마이그레이션을 고치는 사람이 원인을 읽도록 예외 사슬의 역추적을 덧붙이고, 그 안에는
드라이버와 서버가 낸 글이 든다. 서버가 낸 오류 글 자체가 값을 싣는 실패(형 변환 실패, 유일 제약
위반의 DETAIL)는 `hide_parameters` 로 막지 못한다. 그런 값이 든 열을 건드리는 마이그레이션은 그 값을
싣는 실패가 나지 않게 짓는다.

**시도 하나를 통째로 제한 시간으로 감싼다.** 연결을 얻는 것부터 판을 다 읽는 것까지다. 드라이버의
접속 인자(`timeout`)는 연결을 맺는 데만 걸려서, 다른 연결이 판 기록 표를 잠가 두면 연결은 열려도 판
읽기가 잠금이 풀릴 때까지 기다린다.

**마이그레이션은 객체가 연 연결로 돈다.** alembic 환경(`migrations/env.py`)은 `config.attributes` 로
받은 연결을 쓰고 스스로 이벤트 루프를 열지 않는다. 올리기 전체는 `engine.begin()` 트랜잭션 하나다.
환경의 `context.begin_transaction()` 은 이미 열린 바깥 트랜잭션을 알아보고 아무것도 열지 않으므로
실제 겹은 하나다.

**읽기는 칸을 이름으로 고른다.** `SELECT *` 가 아니다. 표에 칸이 더 생겨도(다른 묶음이나 뒤의 판이
더한 칸) 응답에 새지 않는다.

못 보는 것: 올리기를 보낸 뒤 응답을 받기 전에 연결이 끊긴 때는 표가 이미 올라갔을 수 있는데 "올리다
실패했다" 글이 "올리기 전 그대로"라고 적는다. 그때 다시 친 `migrate` 는 표의 실제 판을 읽으므로
올라갔으면 "이미 마지막 판"을 찍는다. 같은 데이터베이스를 둘이 함께 올리는 경우는 막지 않는다(명세
Out of Scope 의 multi-instance).
"""

from __future__ import annotations

import asyncio
import enum
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError
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

DRIVER = "postgresql+asyncpg"
DEFAULT_PORT = 5432
DEFAULT_RETRY_SECONDS = 30.0
DEFAULT_RETRY_INTERVAL = 1.0
DEFAULT_ATTEMPT_SECONDS = 5.0

_SELECT = text(f"SELECT {', '.join(COLUMNS)} FROM sites WHERE name = :name")

_NONE = "없음"
_BEHIND = "데이터베이스의 표가 이 판보다 뒤처져 있습니다. widget-admin migrate 를 먼저 돌리십시오."
_AHEAD = "데이터베이스가 이 판보다 새롭습니다. 되돌리려면 올리기 전의 백업을 복원하십시오."
_PASSWORD_HINT = (
    "  .env 의 비밀번호만 바꿨다면 데이터베이스 안의 비밀번호도 바꿔야 합니다."
    ' 배포 안내의 "데이터베이스 비밀번호 바꾸기"를 보십시오.'
)
_HALF_BUILT_HINT = (
    "  처음 띄우기가 끝나기 전에 서버가 꺼졌다면 데이터베이스가 반쯤 만들어진 채 남았을 수"
    ' 있습니다. 배포 안내의 "띄우기가 끊겼을 때"를 보십시오.'
)
_UNEXPECTED_HINT = (
    "  이 판의 결함일 수 있습니다. 예외의 글과 역추적은 비밀번호가 섞일 수 있어 찍지 않습니다."
)


class Failure(enum.Enum):
    """접속 실패의 갈래. 잠시 뒤 다시 시도할 것은 `TRANSIENT` 하나다."""

    TRANSIENT = "transient"
    PASSWORD = "password"
    NOT_ALLOWED = "not_allowed"
    NO_DATABASE = "no_database"
    OTHER = "other"


class Alignment(enum.Enum):
    """표의 판을 이 판의 마지막 판과 견준 결과."""

    CURRENT = "current"
    BEHIND = "behind"
    AHEAD = "ahead"


def _chain(error: BaseException) -> list[BaseException]:
    """예외와 그 원인들. SQLAlchemy 가 감싼 경우에도 드라이버의 예외를 찾으려고 따라간다."""
    seen: list[BaseException] = []
    current: BaseException | None = error
    while current is not None and all(current is not item for item in seen):
        seen.append(current)
        current = current.__cause__ or current.__context__
    return seen


def sqlstate_of(error: BaseException) -> str | None:
    """예외 사슬에서 찾은 PostgreSQL 의 오류 번호. 없으면 `None`."""
    for item in _chain(error):
        state = getattr(item, "sqlstate", None)
        if isinstance(state, str):
            return state
    return None


def failure_kind(error: BaseException) -> Failure:
    """실패를 갈래 다섯으로 가른다. 예외의 클래스가 아니라 오류 번호와 `OSError` 여부로 가른다."""
    state = sqlstate_of(error)
    if state is None:
        reached_os = any(isinstance(item, OSError) for item in _chain(error))
        return Failure.TRANSIENT if reached_os else Failure.OTHER
    if state == "28P01":
        return Failure.PASSWORD
    if state == "28000":
        return Failure.NOT_ALLOWED
    if state == "3D000":
        return Failure.NO_DATABASE
    if state == "57P03" or state.startswith("08"):
        return Failure.TRANSIENT
    return Failure.OTHER


def reason_of(error: BaseException) -> str:
    """멈출 때의 글에 싣는 까닭. 오류 번호, 없으면 가장 안쪽 `OSError` 의 클래스 이름, 없으면 바깥
    예외의 클래스 이름이다. 드라이버가 낸 글은 싣지 않는다."""
    state = sqlstate_of(error)
    if state is not None:
        return f"오류 번호 {state}"
    os_errors = [item for item in _chain(error) if isinstance(item, OSError)]
    return type(os_errors[-1] if os_errors else error).__name__


# 멈출 때와 다시 시도할 때 찍는 글을 짓는 자리. 값(자리 표시, 까닭, 판)을 글자로 받는 순수 함수라,
# 배포 안내의 시험(widget-admin-server 04 가 더한다)이 자리 표시를 넣어 불러 안내의 표가 제품의 글을
# 빠짐없이 싣는지 본다. 객체의
# 메서드는 값을 채워 이 함수들을 부른다. Agent OS 쪽의 같은 이름의 함수와 글자가 같고, 다른 것은
# 표가 뒤처졌다는 글(`_BEHIND`)의 명령 이름뿐이다.


def retry_notice(place: str, retry_seconds: float) -> str:
    """처음 실패한 뒤 한 번 찍는 알림. 멈추는 글이 아니다."""
    seconds = f"{retry_seconds:g}초 동안 다시 시도합니다."
    return f"데이터베이스({place})에 아직 닿지 못해 최대 {seconds}"


def unreached_text(kind: Failure, place: str, reason: str, retry_seconds: float) -> str:
    """접속 실패 갈래마다의 멈출 때의 글. 값을 되울리지 않는다."""
    match kind:
        case Failure.TRANSIENT:
            waited = f"{retry_seconds:g}초 동안 다시 시도했습니다"
            return f"데이터베이스({place})에 닿지 못했습니다. {waited}({reason})."
        case Failure.PASSWORD:
            refused = "계정이나 비밀번호를 받아들이지 않았습니다"
            return f"데이터베이스({place})가 {refused}({reason}).\n{_PASSWORD_HINT}"
        case Failure.NOT_ALLOWED:
            refused = "이 접속을 허락하지 않았습니다"
            return f"데이터베이스({place})가 {refused}({reason}).\n{_HALF_BUILT_HINT}"
        case Failure.NO_DATABASE:
            check = "주소의 데이터베이스 이름을 확인하십시오."
            return f"데이터베이스({place})가 없습니다({reason}). {check}\n{_HALF_BUILT_HINT}"
        case Failure.OTHER:
            return f"데이터베이스({place})에 접속하지 못했습니다({reason})."


def misaligned_text(alignment: Alignment, shown: str, head: str) -> str:
    """표의 판이 이 판과 맞지 않을 때의 글. 맞는(`CURRENT`) 표에는 글이 없어 `ValueError` 다."""
    if alignment is Alignment.BEHIND:
        return f"{_BEHIND}\n  표의 판은 {shown}이고 이 판의 마지막 판은 {head}입니다."
    if alignment is Alignment.AHEAD:
        return f"{_AHEAD}\n  표의 판은 {shown}이고 이 판이 아는 마지막 판은 {head}입니다."
    raise ValueError("판이 맞는 표에는 맞지 않는 글이 없다")


def unexpected_text(place: str, reason: str) -> str:
    """확인이 글 대신 예외를 던졌을 때의 글."""
    stopped = "뜻밖의 오류로 멈췄습니다"
    return f"데이터베이스({place})를 확인하다 {stopped}({reason}).\n{_UNEXPECTED_HINT}"


def close_text(place: str, reason: str) -> str:
    """닫기가 예외를 던졌을 때의 글."""
    return f"데이터베이스({place})의 연결을 닫다 오류가 났습니다({reason})."


def upgrade_failed_text(reason: str, before: str) -> str:
    """표를 올리다 실패했을 때의 첫 줄. 부르는 쪽이 그 뒤에 예외의 역추적을 붙인다."""
    return f"표를 올리다 실패했습니다({reason}). 표의 판은 올리기 전 그대로 {before}입니다."


def upgraded_text(before: str, head: str) -> str:
    """표를 올렸을 때의 글."""
    return f"표를 {before}에서 {head}으로 올렸습니다."


def already_current_text(head: str) -> str:
    """올릴 것이 없을 때의 글."""
    return f"표가 이미 마지막 판({head})입니다."


class DatabaseUrl:
    """읽은 연결 문자열. `repr` 과 `str` 에 비밀번호가 없다. 접속에만 원래 값을 쓴다."""

    def __init__(self, url: URL) -> None:
        self._url = url

    @property
    def place(self) -> str:
        """글에 싣는 `호스트:포트/데이터베이스`. 계정과 비밀번호는 싣지 않는다."""
        return f"{self._url.host}:{self._url.port or DEFAULT_PORT}/{self._url.database}"

    def for_driver(self) -> URL:
        """드라이버를 붙인 접속용 주소. 이 모듈 안에서만 쓴다."""
        return self._url.set(drivername=DRIVER)

    def __repr__(self) -> str:
        return f"DatabaseUrl({self.place})"

    __str__ = __repr__


def parse_database_url(value: str) -> DatabaseUrl | None:
    """연결 문자열을 읽는다. 읽지 못하면 `None` 이고, 문구는 부르는 쪽이 값을 되울리지 않고 짓는다.

    `postgresql://계정:비밀번호@호스트:포트/데이터베이스` 꼴로 쓴다. 이 꼴 밖에서 받지 않는 것은
    드라이버 이름이 붙은 꼴과 다른 이름, 질의 문자열(`?` 뒤), `@` 가 둘 이상인 값, 읽을 때
    `ValueError` 가 나는 값이다. 그 밖의 어긋남(계정이나 포트를 적지 않은 값 등)은 SQLAlchemy 가
    읽는 대로 읽고 따로 막지 않는다. 질의 문자열은 그 값이 경로에서 읽은 연결 인자를 덮어 쓸 수
    있고, `sslmode` 같은 libpq 의 질의는 asyncpg 가 몰라 첫 질의에서 죽어서 받지 않는다. `@` 가
    둘 이상이면 비밀번호에 `@` 가 든 것이고, SQLAlchemy 는 비밀번호를 첫 `@` 앞에서 잘라 나머지를
    호스트로 읽으므로 비밀번호의 조각이 글의 자리에 실린다.
    """
    if value.count("@") > 1 or "?" in value:
        return None
    try:
        url = make_url(value)
    except (ArgumentError, ValueError):
        return None
    if url.drivername != "postgresql" or not url.host or not url.database or url.query:
        return None
    return DatabaseUrl(url)


@dataclass(frozen=True)
class Reached:
    """데이터베이스에 닿아 읽은 판 기록 표의 판. 표가 없거나 줄이 없으면 `None`."""

    revision: str | None


@dataclass(frozen=True)
class Unreached:
    """닿지 못한 이유를 담은 멈출 때의 글."""

    problem: str


@dataclass(frozen=True)
class MigrateResult:
    """`migrate` 의 결과. `message` 는 그대로 찍는 글이고 `ok` 는 종료 코드 0 이다."""

    ok: bool
    message: str


def _current_revision(connection: Connection) -> str | None:
    return MigrationContext.configure(connection).get_current_revision()


class WidgetAdminDatabase:
    """연결 묶음 하나와 위젯 설정 표, 표의 판을 다루는 객체."""

    def __init__(
        self,
        url: DatabaseUrl,
        *,
        notice: Callable[[str], None],
        versions: Path = PRODUCT_VERSIONS,
        retry_seconds: float = DEFAULT_RETRY_SECONDS,
        retry_interval: float = DEFAULT_RETRY_INTERVAL,
        attempt_seconds: float = DEFAULT_ATTEMPT_SECONDS,
    ) -> None:
        self._place = url.place
        self._versions = versions
        self._retry_seconds = retry_seconds
        self._retry_interval = retry_interval
        self._attempt_seconds = attempt_seconds
        self._notice = notice
        self._engine: AsyncEngine = create_async_engine(
            url.for_driver(), pool_pre_ping=True, hide_parameters=True
        )

    @property
    def place(self) -> str:
        return self._place

    async def startup_problem(self) -> str | None:
        """닿아서 표의 판을 견준다. 문제가 없으면 `None`, 있으면 멈출 때의 글."""
        reached = await self._reach()
        if isinstance(reached, Unreached):
            return reached.problem
        alignment = self._align(reached.revision)
        if alignment is Alignment.CURRENT:
            return None
        return self._misaligned_text(alignment, reached.revision)

    async def migrate(self) -> MigrateResult:
        """표를 이 판의 마지막 판까지 올린다. 더 새로운 표는 건드리지 않고 멈춘다.

        견줌이 맞으면 alembic 을 부르지 않는다. 견줌과 올리기가 예외를 던지면(마이그레이션 파일을
        읽다 난 것 등) 그대로 올라가고, 부르는 쪽이 `unexpected_problem` 으로 글을 짓는다. 올리다 난
        실패는 여기서 글로 바꾼다.
        """
        reached = await self._reach()
        if isinstance(reached, Unreached):
            return MigrateResult(ok=False, message=reached.problem)
        alignment = self._align(reached.revision)
        head = self._head()
        if alignment is Alignment.AHEAD:
            return MigrateResult(
                ok=False, message=self._misaligned_text(alignment, reached.revision)
            )
        if alignment is Alignment.CURRENT:
            return MigrateResult(ok=True, message=already_current_text(head or _NONE))
        before = reached.revision or _NONE
        try:
            async with self._engine.begin() as connection:
                await connection.run_sync(self._upgrade)
        except Exception as error:  # 어떤 실패든 글로 바꿔 판의 상태를 알린다
            first = upgrade_failed_text(reason_of(error), before)
            trace = "".join(traceback.format_exception(error))
            return MigrateResult(ok=False, message=f"{first}\n{trace}".rstrip("\n"))
        return MigrateResult(ok=True, message=upgraded_text(before, head or _NONE))

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

    def unexpected_problem(self, error: BaseException) -> str:
        """확인이 글 대신 예외를 던졌을 때의 글. 예외의 글과 역추적은 싣지 않는다."""
        return unexpected_text(self._place, reason_of(error))

    def close_problem(self, error: BaseException) -> str:
        """닫기가 예외를 던졌을 때의 글. 예외의 글과 역추적은 싣지 않는다."""
        return close_text(self._place, reason_of(error))

    async def close(self) -> None:
        """연결 묶음을 닫는다. 남은 연결이 없게 한다."""
        await self._engine.dispose()

    async def _attempt(self) -> str | None:
        """시도 하나. 연결을 얻는 것부터 판을 다 읽는 것까지 통째로 제한 시간에 건다."""
        async with asyncio.timeout(self._attempt_seconds):
            async with self._engine.connect() as connection:
                return await connection.run_sync(_current_revision)

    async def _reach(self) -> Reached | Unreached:
        deadline = time.monotonic() + self._retry_seconds
        noticed = False
        while True:
            try:
                return Reached(await self._attempt())
            except Exception as error:  # 갈래는 failure_kind 가 가른다
                kind = failure_kind(error)
                if kind is not Failure.TRANSIENT or time.monotonic() >= deadline:
                    return Unreached(self._describe(kind, error))
            if not noticed:
                self._notice(retry_notice(self._place, self._retry_seconds))
                noticed = True
            await asyncio.sleep(self._retry_interval)

    def _describe(self, kind: Failure, error: BaseException) -> str:
        """갈래마다의 멈출 때의 글. 값을 되울리지 않는다."""
        return unreached_text(kind, self._place, reason_of(error), self._retry_seconds)

    def _config(self) -> Config:
        config = Config()
        # configparser 의 `%` 해석을 피한다. 경로를 설정 파일 없이 코드로 준다.
        config.set_main_option("script_location", str(MIGRATIONS).replace("%", "%%"))
        config.set_main_option("version_locations", str(self._versions).replace("%", "%%"))
        # 폴더는 하나이므로 경로에 들 수 없는 줄바꿈으로 가른다. `os` 로 두면 경로의 `;`(POSIX 는
        # `:`)에서 갈려 폴더를 못 찾고, 판이 있는 폴더가 조용히 빈 폴더로 취급된다.
        config.set_main_option("path_separator", "newline")
        return config

    def _script(self) -> ScriptDirectory:
        return ScriptDirectory.from_config(self._config())

    def _head(self) -> str | None:
        return self._script().get_current_head()

    def _align(self, revision: str | None) -> Alignment:
        """표의 판과 이 판의 마지막 판을 견준다. 모르는 번호는 모두 더 새로운 것으로 본다."""
        script = self._script()
        head = script.get_current_head()
        if revision == head:
            return Alignment.CURRENT
        known = {item.revision for item in script.walk_revisions()}
        if revision is None or revision in known:
            return Alignment.BEHIND
        return Alignment.AHEAD

    def _misaligned_text(self, alignment: Alignment, revision: str | None) -> str:
        shown, head = revision or _NONE, self._head() or _NONE
        return misaligned_text(alignment, shown, head)

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
