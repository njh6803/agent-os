"""어댑터의 시제품. SQLAlchemy 와 alembic 을 부르는 코드는 이 모듈과 `migrations/` 뿐이다.

asyncpg 는 import 하지 않는다(스텁 없는 잠금에서 pyright strict 를 지키려는 것이다). 접속 실패는
예외의 클래스가 아니라 PostgreSQL 의 오류 번호(SQLSTATE)와 `OSError` 여부로 가른다.

마이그레이션은 어댑터가 연 연결을 `config.attributes` 로 넘겨 돌린다. `env.py` 가 `asyncio.run` 을
부르지 않으므로 이미 도는 이벤트 루프 안에서도 적용할 수 있고, 주소가 configparser 를 거치지 않는다.
"""

from __future__ import annotations

import asyncio
import enum
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from alembic import command
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

HERE = Path(__file__).resolve().parent
MIGRATIONS = HERE / "migrations"
VERSIONS = MIGRATIONS / "versions"
DRIVER = "postgresql+asyncpg"

# 명세 "멈출 때의 글"의 표를 옮긴 것이다. 첫 줄이 이유이고, 둘째 줄은 두 칸 들여 설명한다.
BEHIND = "데이터베이스의 표가 이 판보다 뒤처져 있습니다. agent-os migrate 를 먼저 돌리십시오."
AHEAD = "데이터베이스가 이 판보다 새롭습니다. 되돌리려면 올리기 전의 백업을 복원하십시오."
# 다시 시도한다는 알림의 가운데 토막. 알림 전체는 `데이터베이스(<자리>)` 뒤에 이 토막과 초가 온다
WAITING = "에 아직 닿지 못해 최대"
PASSWORD_HINT = (
    "  .env 의 비밀번호만 바꿨다면 데이터베이스 안의 비밀번호도 바꿔야 합니다."
    ' 배포 안내의 "데이터베이스 비밀번호 바꾸기"를 보십시오.'
)
HALF_BUILT_HINT = (
    "  처음 띄우기가 끝나기 전에 서버가 꺼졌다면 데이터베이스가 반쯤 만들어진 채 남았을 수"
    ' 있습니다. 배포 안내의 "띄우기가 끊겼을 때"를 보십시오.'
)


class Failure(enum.Enum):
    """접속 실패의 갈래. 잠시 뒤 다시 시도할 것은 TRANSIENT 하나다."""

    TRANSIENT = "transient"
    PASSWORD = "password"
    NOT_ALLOWED = "not_allowed"
    NO_DATABASE = "no_database"
    OTHER = "other"


def _chain(error: BaseException) -> list[BaseException]:
    """예외와 그 원인들. SQLAlchemy 가 감싼 경우에도 드라이버의 예외를 찾으려고 따라간다."""
    seen: list[BaseException] = []
    current: BaseException | None = error
    while current is not None and all(current is not item for item in seen):
        seen.append(current)
        current = current.__cause__ or current.__context__
    return seen


def sqlstate_of(error: BaseException) -> str | None:
    for item in _chain(error):
        state = getattr(item, "sqlstate", None)
        if isinstance(state, str):
            return state
    return None


def failure_kind(error: BaseException) -> Failure:
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
    """멈출 때의 글에 싣는 까닭. 오류 번호, 없으면 가장 안쪽 `OSError` 의 이름, 없으면 바깥 예외의
    이름이다. 드라이버의 글은 싣지 않는다(계정 이름이나 주소의 조각이 섞일 수 있다)."""
    state = sqlstate_of(error)
    if state is not None:
        return f"오류 번호 {state}"
    os_errors = [item for item in _chain(error) if isinstance(item, OSError)]
    return type(os_errors[-1] if os_errors else error).__name__


def parse_url(text: str) -> URL | None:
    """연결 문자열을 읽는다. 읽지 못하면 None 이고, 문구는 부르는 쪽이 값을 되울리지 않고 짓는다.

    `@` 가 둘 이상이면 읽지 않는다. 계정과 비밀번호 뒤의 `@` 하나 밖에 `@` 가 더 있으면 비밀번호에
    `@` 가 든 것이고, SQLAlchemy 는 비밀번호를 첫 `@` 앞에서 잘라 나머지를 호스트·포트·데이터베이스·
    질의로 읽으므로 비밀번호의 조각이 그 자리에 들어간다.
    """
    if text.count("@") > 1:
        return None
    try:
        url = make_url(text)
    except (ArgumentError, ValueError):
        return None
    if url.drivername != "postgresql" or not url.host or not url.database:
        return None
    return url.set(drivername=DRIVER)


@dataclass(frozen=True)
class Reached:
    revision: str | None


@dataclass(frozen=True)
class Unreached:
    problem: str


def _current_revision(connection: Connection) -> str | None:
    return MigrationContext.configure(connection).get_current_revision()


class PostgresDatabase:
    """연결 묶음 하나와 표의 판을 다루는 것. 포트(`port.Database`)를 시그니처로 만족한다."""

    def __init__(
        self,
        url: URL,
        *,
        versions: Path = VERSIONS,
        retry_seconds: float = 30.0,
        retry_interval: float = 1.0,
        notice: Callable[[str], None] = print,
        pre_ping: bool = True,
        connect_timeout: float | None = 5.0,
    ) -> None:
        self._url = url
        self._versions = versions
        self._retry_seconds = retry_seconds
        self._retry_interval = retry_interval
        self._notice = notice
        # 시도 하나의 제한 시간. 없으면 드라이버의 기본값이라 답 없는 서버에서 마감을 넘겨 기다린다
        connect_args: dict[str, float] = {}
        if connect_timeout is not None:
            connect_args["timeout"] = connect_timeout
        self._engine = create_async_engine(url, pool_pre_ping=pre_ping, connect_args=connect_args)

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    async def startup_problem(self) -> str | None:
        reached = await self._reach()
        if isinstance(reached, Unreached):
            return reached.problem
        return self._problem_for(reached.revision)

    async def migrate(self) -> str | None:
        """표를 마지막 번호까지 올린다. 모르는 더 새 번호면 건드리지 않고 문구를 돌려준다."""
        reached = await self._reach()
        if isinstance(reached, Unreached):
            return reached.problem
        problem = self._problem_for(reached.revision)
        if problem is not None and problem.startswith(AHEAD):
            return problem
        async with self._engine.begin() as connection:
            await connection.run_sync(self._upgrade)
        return None

    async def close(self) -> None:
        await self._engine.dispose()

    def raw_upgrade(self, connection: Connection) -> None:
        """판정 없이 alembic 만 부른다. alembic 이 모르는 번호에 스스로 내는 것을 재는 데 쓴다."""
        self._upgrade(connection)

    async def _reach(self) -> Reached | Unreached:
        deadline = time.monotonic() + self._retry_seconds
        noticed = False
        while True:
            try:
                async with self._engine.connect() as connection:
                    return Reached(await connection.run_sync(_current_revision))
            except Exception as error:  # 갈래는 failure_kind 가 가른다
                kind = failure_kind(error)
                if kind is not Failure.TRANSIENT or time.monotonic() >= deadline:
                    return Unreached(self._describe(kind, error))
            if not noticed:
                seconds = f"{self._retry_seconds:g}초 동안 다시 시도합니다."
                self._notice(f"데이터베이스({self._where()}){WAITING} {seconds}")
                noticed = True
            await asyncio.sleep(self._retry_interval)

    def _where(self) -> str:
        return f"{self._url.host}:{self._url.port or 5432}/{self._url.database}"

    def _describe(self, kind: Failure, error: BaseException) -> str:
        """값을 되울리지 않는다. 드라이버의 문구 대신 갈래와 까닭(`reason_of`)만 싣는다."""
        where = self._where()
        reason = reason_of(error)
        match kind:
            case Failure.TRANSIENT:
                waited = f"{self._retry_seconds:g}초 동안 다시 시도했습니다"
                return f"데이터베이스({where})에 닿지 못했습니다. {waited}({reason})."
            case Failure.PASSWORD:
                refused = "계정이나 비밀번호를 받아들이지 않았습니다"
                return f"데이터베이스({where})가 {refused}({reason}).\n{PASSWORD_HINT}"
            case Failure.NOT_ALLOWED:
                refused = "이 접속을 허락하지 않았습니다"
                return f"데이터베이스({where})가 {refused}({reason}).\n{HALF_BUILT_HINT}"
            case Failure.NO_DATABASE:
                check = "주소의 데이터베이스 이름을 확인하십시오."
                return f"데이터베이스({where})가 없습니다({reason}). {check}\n{HALF_BUILT_HINT}"
            case Failure.OTHER:
                return f"데이터베이스({where})에 접속하지 못했습니다({reason})."

    def _config(self) -> Config:
        config = Config()
        config.set_main_option("script_location", str(MIGRATIONS).replace("%", "%%"))
        config.set_main_option("version_locations", str(self._versions).replace("%", "%%"))
        config.set_main_option("path_separator", "os")
        return config

    def _problem_for(self, revision: str | None) -> str | None:
        script = ScriptDirectory.from_config(self._config())
        head = script.get_current_head()
        if revision == head:
            return None
        known = {item.revision for item in script.walk_revisions()}
        shown, last = revision or "없음", head or "없음"
        if revision is None or revision in known:
            return f"{BEHIND}\n  표의 판은 {shown}이고 이 판의 마지막 판은 {last}입니다."
        return f"{AHEAD}\n  표의 판은 {shown}이고 이 판이 아는 마지막 판은 {last}입니다."

    def _upgrade(self, connection: Connection) -> None:
        config = self._config()
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
