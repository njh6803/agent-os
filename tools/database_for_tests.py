"""테스트 컨테이너의 데이터베이스를 쓰는 일: 주소 고르기, 서버가 답하는지 보기, 만들고 지우기.

pytest 픽스처(`tests/database.py`)와 러너(`tools/run_checks.py`), e2e-stack 이 같은 일을 하므로
픽스처만 든 파일 하나로는 셋이 함께 쓰지 못한다. 그래서 일은 이 모듈에, 픽스처는 `tests/database.py`
에 둔다. `agent_os` 도 위젯 관리 서버의 패키지도 import 하지 않는다. 패키지마다 다른
것(마이그레이션을 올리는 함수와 데이터베이스 이름의 접두)은 부르는 쪽이 인자로 넘긴다.

**주소.** 시험이 붙는 주소는 환경 변수 `AGENT_OS_TEST_DATABASE_URL` 이 있으면 그 값, 없으면 테스트
컨테이너(`compose.test.yaml`)의 기본 주소다. 값에는 비밀번호가 들 수 있어 `DatabaseAddress` 의
`repr` 과 문자열에 싣지 않는다(pytest 가 실패한 단언을 풀어 쓰는 줄에 그 `repr` 이 실린다). 질의
문자열(`?` 뒤)이나 `@` 가 둘 이상인 값은 받지 않는다. 질의의 `database` 가 시험마다의 이름을 덮어
시험이 관리 데이터베이스에 표를 올릴 수 있고, 둘째 `@` 앞의 비밀번호 조각이 글에 실릴 수 있어서다.

**이름.** 템플릿은 `<접두>_template_<32자>`, 시험마다의 데이터베이스는 `<접두>_test_<32자>`,
e2e-stack 이 만드는 것은 `<접두>_e2e_<32자>` 다. 32자는 `uuid4` 의 16진수다. 테스트 컨테이너 하나를
워크트리와 세션이 함께 쓰므로 무작위 토막으로 겹치지 않게 한다. PostgreSQL 의 이름은 63바이트까지라
접두는 21자까지다.

**명령줄.** `create <접두>` 는 템플릿을 거치지 않은 빈 데이터베이스를 `<접두>_e2e_…` 로 만들고 그
주소를 표준 출력에 한 줄로 찍는다(e2e-stack 이 그 뒤 `agent-os migrate` 를 스스로 돌린다).
`drop <이름>` 은 위 이름의 꼴에 맞는 이름만 지우고, 맞지 않으면 아무것도 지우지 않고 1 로 끝난다.
시험이 만들지 않은 기본 데이터베이스(`agent_os`)를 잘못된 인자 하나로 지우지 않게 하려는 것이다.
서버가 답하지 않으면 둘 다 시험 쪽 글을 표준 오류에 찍고 1 로 끝난다.

못 보는 것: 시험 프로세스가 죽어 지우지 못한 데이터베이스는 컨테이너를 다시 띄울 때까지 남는다.
이름이 무작위라 다음 시험과 부딪치지 않는다. 남은 것을 가려 치우지는 않는다.
"""

from __future__ import annotations

import asyncio
import re
import sys
import uuid
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass

from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

URL_ENV = "AGENT_OS_TEST_DATABASE_URL"
DEFAULT_URL = "postgresql://agent_os:agent_os@127.0.0.1:25432/agent_os"
UP_COMMAND = "docker compose -f compose.test.yaml up -d --wait"
CONNECT_SECONDS = 5.0
MAX_PREFIX = 21
_DRIVER = "postgresql+asyncpg"
_PREFIX = re.compile(r"[a-z0-9_]+")
_KINDS = ("template", "test", "e2e")
_NAME = re.compile(rf"[a-z0-9_]{{1,{MAX_PREFIX}}}_(?:{'|'.join(_KINDS)})_[0-9a-f]{{32}}")

_QUERY_PROBLEM = (
    f"{URL_ENV} 에 질의 문자열(? 뒤)이 들어 있어 받지 않습니다. "
    "질의가 시험마다의 데이터베이스 이름을 덮을 수 있습니다."
)
_UNREADABLE_PROBLEM = (
    f"{URL_ENV} 을 읽지 못했습니다. 값에는 비밀번호가 들어 있어 여기 찍지 않습니다. "
    "비밀번호에 @ 가 들면 주소를 읽지 못하므로, 비밀번호는 영문자와 숫자만 씁니다."
)

Migrate = Callable[[str], Awaitable[None]]


class DatabaseProblem(Exception):
    """시험 쪽 글을 든 예외. 글은 값을 되울리지 않는다."""


@dataclass(frozen=True)
class DatabaseAddress:
    """테스트 컨테이너의 주소. `repr` 과 문자열에 비밀번호가 없다."""

    url: URL
    from_env: bool

    @property
    def place(self) -> str:
        return f"{self.url.host}:{self.url.port or 5432}/{self.url.database}"

    def with_database(self, name: str) -> URL:
        """경로의 데이터베이스 이름만 바꾼 접속용 주소."""
        return self.url.set(drivername=_DRIVER, database=name)

    def text_for(self, name: str) -> str:
        """`postgresql://…` 꼴의 접속 문자열(비밀번호를 포함한다). 어댑터와 `migrate` 에 넘긴다."""
        return self.url.set(database=name).render_as_string(hide_password=False)

    def __repr__(self) -> str:
        return f"DatabaseAddress({self.place})"

    __str__ = __repr__


@dataclass(frozen=True)
class ScopedDatabase:
    """시험이 쓰는 데이터베이스 하나. `repr` 에 이름과 자리만 있고 비밀번호가 없다."""

    address: DatabaseAddress
    name: str

    @property
    def place(self) -> str:
        """글에 싣는 `호스트:포트/이름`. 계정과 비밀번호는 싣지 않는다."""
        return f"{self.address.url.host}:{self.address.url.port or 5432}/{self.name}"

    def text(self) -> str:
        """접속 문자열(`postgresql://…`, 비밀번호를 포함한다). 어댑터와 `migrate` 에 넘긴다."""
        return self.address.text_for(self.name)


def resolve_address(environ: Mapping[str, str]) -> DatabaseAddress:
    """시험이 붙을 주소. 받지 않는 값이면 `DatabaseProblem` 이고 글에 비밀번호가 없다."""
    given = environ.get(URL_ENV)
    from_env = given is not None and given.strip() != ""
    raw = given if from_env and given is not None else DEFAULT_URL
    if "?" in raw:
        raise DatabaseProblem(_QUERY_PROBLEM)
    if raw.count("@") > 1:
        raise DatabaseProblem(_UNREADABLE_PROBLEM)
    try:
        url = make_url(raw)
    except (ArgumentError, ValueError):
        raise DatabaseProblem(_UNREADABLE_PROBLEM) from None
    if url.drivername != "postgresql" or not url.host or not url.database:
        raise DatabaseProblem(_UNREADABLE_PROBLEM)
    return DatabaseAddress(url=url, from_env=from_env)


def prefix_problem(prefix: str) -> str | None:
    """접두가 소문자, 숫자, 밑줄이 아니거나 21자를 넘으면 그 이유. 시험을 띄우기 전에 멈추는 데
    쓴다."""
    if _PREFIX.fullmatch(prefix) is None:
        return f"데이터베이스 이름의 접두 {prefix!r} 은 소문자, 숫자, 밑줄만 쓴다"
    if len(prefix) > MAX_PREFIX:
        return (
            f"데이터베이스 이름의 접두 {prefix!r} 은 {MAX_PREFIX}자까지다(이름이 63바이트까지라서)"
        )
    return None


def make_name(prefix: str, kind: str) -> str:
    """`<접두>_<종류>_<32자>`. 접두와 종류가 틀렸으면 `ValueError`."""
    problem = prefix_problem(prefix)
    if problem is not None:
        raise ValueError(problem)
    if kind not in _KINDS:
        raise ValueError(f"종류는 {', '.join(_KINDS)} 가운데 하나다: {kind!r}")
    return f"{prefix}_{kind}_{uuid.uuid4().hex}"


def is_scoped_name(name: str) -> bool:
    """시험이 만든 이름의 꼴인가. `drop` 이 이 꼴만 지운다."""
    return _NAME.fullmatch(name) is not None


def _chain(error: BaseException) -> list[BaseException]:
    seen: list[BaseException] = []
    current: BaseException | None = error
    while current is not None and all(current is not item for item in seen):
        seen.append(current)
        current = current.__cause__ or current.__context__
    return seen


def reason_of(error: BaseException) -> str:
    """닿지 못한 까닭. 오류 번호, 없으면 가장 안쪽 `OSError` 의 클래스 이름, 없으면 바깥 예외의
    이름. 드라이버가 낸 글은 싣지 않는다(계정이나 주소의 조각이 섞일 수 있다)."""
    for item in _chain(error):
        state = getattr(item, "sqlstate", None)
        if isinstance(state, str):
            return f"오류 번호 {state}"
    os_errors = [item for item in _chain(error) if isinstance(item, OSError)]
    return type(os_errors[-1] if os_errors else error).__name__


def unreachable_text(address: DatabaseAddress, error: BaseException) -> str:
    """서버가 답하지 않을 때의 시험 쪽 글."""
    reason = reason_of(error)
    if address.from_env:
        return (
            f"{URL_ENV} 이 가리키는 테스트 데이터베이스({address.place})에 "
            f"닿지 못했습니다({reason})."
        )
    return (
        f"테스트 데이터베이스({address.place})에 닿지 못했습니다({reason}). "
        f"이 명령으로 띄우십시오: {UP_COMMAND}"
    )


async def server_problem(
    address: DatabaseAddress, *, seconds: float = CONNECT_SECONDS
) -> str | None:
    """서버가 질의 하나에 답하면 `None`, 아니면 시험 쪽 글. 연결을 묶어 두지 않는다(`NullPool`)."""
    engine = create_async_engine(
        address.with_database(address.url.database or ""), poolclass=NullPool, hide_parameters=True
    )
    try:
        async with asyncio.timeout(seconds), engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except Exception as error:  # 갈래는 까닭의 글에 담긴다
        return unreachable_text(address, error)
    finally:
        await engine.dispose()
    return None


async def _admin(address: DatabaseAddress, statement: str) -> None:
    """관리 연결에서 문장 하나를 자동 커밋으로 친다. 데이터베이스를 만들고 지우는 문장은 트랜잭션
    밖이다."""
    engine = create_async_engine(
        address.with_database(address.url.database or ""),
        poolclass=NullPool,
        isolation_level="AUTOCOMMIT",
        hide_parameters=True,
    )
    try:
        async with engine.connect() as connection:
            await connection.execute(text(statement))
    finally:
        await engine.dispose()


async def create_database(
    address: DatabaseAddress, name: str, *, template: str | None = None
) -> None:
    """빈 데이터베이스, 또는 `template` 을 복제한 데이터베이스를 만든다."""
    clone = f' TEMPLATE "{template}"' if template is not None else ""
    await _admin(address, f'CREATE DATABASE "{name}"{clone}')


async def drop_database(address: DatabaseAddress, name: str) -> None:
    """쓰는 연결이 있어도 지운다(`WITH (FORCE)`). 없는 이름이어도 오류가 아니다."""
    await _admin(address, f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


async def build_template(address: DatabaseAddress, prefix: str, migrate: Migrate) -> str:
    """템플릿을 만들어 마이그레이션을 한 번 올리고 이름을 돌려준다. 올리다 실패하면 지우고 다시
    던진다."""
    name = make_name(prefix, "template")
    await create_database(address, name)
    try:
        await migrate(address.text_for(name))
    except BaseException:
        await drop_database(address, name)
        raise
    return name


async def _create_cli(prefix: str, environ: Mapping[str, str]) -> int:
    problem = prefix_problem(prefix)
    if problem is not None:
        sys.stderr.write(f"{problem}\n")
        return 1
    try:
        address = resolve_address(environ)
    except DatabaseProblem as error:
        sys.stderr.write(f"{error}\n")
        return 1
    unreachable = await server_problem(address)
    if unreachable is not None:
        sys.stderr.write(f"{unreachable}\n")
        return 1
    name = make_name(prefix, "e2e")
    await create_database(address, name)
    sys.stdout.write(f"{address.text_for(name)}\n")
    return 0


async def _drop_cli(name: str, environ: Mapping[str, str]) -> int:
    if not is_scoped_name(name):
        sys.stderr.write(
            "지울 수 있는 이름의 꼴이 아닙니다. "
            "<접두>_(e2e|test|template)_<16진수 32자> 만 지웁니다.\n"
        )
        return 1
    try:
        address = resolve_address(environ)
    except DatabaseProblem as error:
        sys.stderr.write(f"{error}\n")
        return 1
    unreachable = await server_problem(address)
    if unreachable is not None:
        sys.stderr.write(f"{unreachable}\n")
        return 1
    await drop_database(address, name)
    return 0


def main(argv: Sequence[str], environ: Mapping[str, str]) -> int:
    if len(argv) == 2 and argv[0] == "create":
        return asyncio.run(_create_cli(argv[1], environ))
    if len(argv) == 2 and argv[0] == "drop":
        return asyncio.run(_drop_cli(argv[1], environ))
    sys.stderr.write("사용법: database_for_tests.py create <접두> | drop <이름>\n")
    return 1


if __name__ == "__main__":
    import os

    sys.exit(main(sys.argv[1:], os.environ))
