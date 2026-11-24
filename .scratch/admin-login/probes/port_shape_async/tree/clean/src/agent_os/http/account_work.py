"""트랜잭션 하나를 여는 계정 포트와 그 안의 작업 객체. 프로브(`port_shape_async`)가 임시 사본의
`agent_os.http` 에만 둔다.

제품 코드가 아니다. 명세(`.scratch/admin-login/spec.md` "한 트랜잭션에 묶을 일")의 모양을 잰다.
포트(`AccountTransactions`)는 트랜잭션 하나를 여는 메서드 `transaction()` 하나이고, 그것이 비동기
문맥 관리자(`AbstractAsyncContextManager`)를 돌려준다. 그 안에서 받는 작업 객체(`AccountWork`)가
줄을 잠가 읽는 `lock` 과 횟수와 잠금을 적는 `write_failures` 를 가진다. 판정의 규칙(몇 번째에
잠그는지)은 이 모듈의 함수가 갖고, 어댑터는 잠그고 읽고 적기만 한다. 어댑터는 이 모듈을 가져오지
않는다.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextlib import AbstractAsyncContextManager
from datetime import datetime
from typing import Protocol

from agent_os.http.accounts import AccountRow

LOCK_AFTER = 2

type Compare = Callable[[], Awaitable[None]]


class AccountWork(Protocol):
    """트랜잭션 하나 안의 읽기와 쓰기."""

    async def lock(self, name: str) -> AccountRow | None: ...

    async def write_failures(
        self, name: str, *, failures: int, locked_until: datetime | None
    ) -> None: ...


class AccountTransactions(Protocol):
    """트랜잭션 하나를 여는 포트. 블록을 정상으로 나오면 적고, 예외로 나오면 되돌린다."""

    def transaction(self) -> AbstractAsyncContextManager[AccountWork]: ...


class AbortedAfterWrite(Exception):
    """적은 뒤 일부러 낸 예외. 같은 트랜잭션에서 다시 읽은 횟수를 싣는다."""

    def __init__(self, seen_inside: int) -> None:
        super().__init__("적은 뒤 멈췄다")
        self.seen_inside = seen_inside


async def record_failed_attempt(
    store: AccountTransactions, name: str, *, at: datetime, compare: Compare
) -> int | None:
    """로그인 시도 하나. 줄을 잠가 읽고, 견주고(`compare`, 비밀번호 견줌의 자리), 횟수와 잠금을
    적는다. 한 트랜잭션이다. 적은 횟수를 돌려주고, 줄이 없으면 `None`."""
    async with store.transaction() as work:
        row = await work.lock(name)
        if row is None:
            return None
        await compare()
        failures = row.failures + 1
        locked_until = at if failures >= LOCK_AFTER else row.locked_until
        await work.write_failures(name, failures=failures, locked_until=locked_until)
        return failures


async def write_then(store: AccountTransactions, name: str, *, add: int, abort: bool) -> int:
    """횟수에 `add` 를 더해 적고 같은 트랜잭션에서 다시 읽는다. `abort` 면 그 값을 실은 예외로
    블록을 나오고, 아니면 그 값을 돌려준다."""
    async with store.transaction() as work:
        row = await work.lock(name)
        if row is None:
            raise LookupError("줄이 없다")
        await work.write_failures(name, failures=row.failures + add, locked_until=row.locked_until)
        again = await work.lock(name)
        if again is None:
            raise LookupError("적은 뒤 줄이 없다")
        if abort:
            raise AbortedAfterWrite(again.failures)
        return again.failures


async def read_failures(store: AccountTransactions, name: str) -> int | None:
    """새 트랜잭션에서 읽은 횟수. 줄이 없으면 `None`."""
    async with store.transaction() as work:
        row = await work.lock(name)
        return None if row is None else row.failures
