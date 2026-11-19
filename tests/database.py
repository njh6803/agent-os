"""데이터베이스를 쓰는 시험의 pytest 픽스처를 짓는 함수들.

데이터베이스를 만들고 지우는 일은 `tools/database_for_tests.py` 가 하고, 여기서는 그 일에
pytest 의 수명(세션, 시험 하나)을 이을 뿐이다. 이 파일은 `agent_os` 도 위젯 관리 서버의 패키지도
import 하지 않는다. 패키지마다 다른 것 둘(데이터베이스 이름의 접두와 마이그레이션을 올리는 함수)은
그 패키지의 시험 폴더에 있는 `conftest.py` 가 이 함수들을 불러 픽스처를 지을 때 인자로 넘긴다.

네 픽스처가 나온다.

- `database_address`(세션): 시험이 붙을 주소. 서버가 답하지 않거나 주소를 받지 않으면 `pytest.fail`
  이라 이 픽스처를 받는 시험은 모두 setup 오류다. skip 이 아니다(원칙 II).
- `database_template`(세션): 마이그레이션을 한 번 올린 템플릿 데이터베이스. xdist 의 작업자는 저마다
  세션이라 작업자마다 하나가 생기고, 세션이 끝날 때 지운다.
- `database`(시험 하나): 템플릿을 복제한 데이터베이스. 시험이 끝나면 `DROP DATABASE … WITH (FORCE)`.
- `empty_database`(시험 하나): 템플릿을 거치지 않은 빈 데이터베이스. 판의 갈래를 시험용 폴더로
  만드는 시험이 쓴다. 이름과 지우는 때는 `database` 와 같다.

세션 범위 픽스처가 `loop_scope="session"` 인 비동기 픽스처인 까닭은 시험에서 `asyncio.run()` 을 직접
부르지 않는다는 규칙 때문이다(`.claude/rules/tests.md`, ADR 0007). 세션 루프에 매인 객체는 넘기지
않고 문자열과 값 객체만 시험의 루프로 넘긴다.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from tools.database_for_tests import (
    DatabaseAddress,
    DatabaseProblem,
    Migrate,
    ScopedDatabase,
    build_template,
    create_database,
    drop_database,
    make_name,
    prefix_problem,
    resolve_address,
    server_problem,
)


def database_address_fixture() -> object:
    """시험이 붙을 주소를 내는 세션 픽스처. 서버가 답하지 않으면 그 자리에서 실패한다."""

    @pytest_asyncio.fixture(scope="session", loop_scope="session", name="database_address")
    async def fixture() -> DatabaseAddress:
        try:
            address = resolve_address(os.environ)
        except DatabaseProblem as error:
            pytest.fail(str(error), pytrace=False)
        problem = await server_problem(address)
        if problem is not None:
            pytest.fail(problem, pytrace=False)
        return address

    return fixture


def database_template_fixture(prefix: str, migrate: Migrate) -> object:
    """마이그레이션을 올린 템플릿 데이터베이스의 이름을 내는 세션 픽스처.

    접두가 틀렸으면 시험을 띄우기 전에, 곧 이 함수를 부르는 `conftest.py` 를 읽을 때 멈춘다.
    """
    problem = prefix_problem(prefix)
    if problem is not None:
        raise ValueError(problem)

    @pytest_asyncio.fixture(scope="session", loop_scope="session", name="database_template")
    async def fixture(database_address: DatabaseAddress) -> AsyncIterator[str]:
        name = await build_template(database_address, prefix, migrate)
        try:
            yield name
        finally:
            await drop_database(database_address, name)

    return fixture


def database_fixture(prefix: str) -> object:
    """템플릿을 복제한 데이터베이스를 시험마다 내는 픽스처."""

    @pytest_asyncio.fixture(name="database")
    async def fixture(
        database_address: DatabaseAddress, database_template: str
    ) -> AsyncIterator[ScopedDatabase]:
        name = make_name(prefix, "test")
        await create_database(database_address, name, template=database_template)
        try:
            yield ScopedDatabase(address=database_address, name=name)
        finally:
            await drop_database(database_address, name)

    return fixture


def empty_database_fixture(prefix: str) -> object:
    """템플릿을 거치지 않은 빈 데이터베이스를 시험마다 내는 픽스처."""

    @pytest_asyncio.fixture(name="empty_database")
    async def fixture(database_address: DatabaseAddress) -> AsyncIterator[ScopedDatabase]:
        name = make_name(prefix, "test")
        await create_database(database_address, name)
        try:
            yield ScopedDatabase(address=database_address, name=name)
        finally:
            await drop_database(database_address, name)

    return fixture
