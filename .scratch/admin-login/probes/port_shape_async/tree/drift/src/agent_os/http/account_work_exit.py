"""트랜잭션 포트가 돌려주는 문맥 관리자의 둘째 타입 인자(`__aexit__` 의 반환)를 바꿔 적은 판
(port_shape_async 대조군). 임시 사본의 대조군 나무에만 두고 돌리지 않는다.

`AbstractAsyncContextManager[T]` 의 둘째 인자는 번들 typeshed 에서 기본이 `bool | None` 이다.

- `SwallowingTransactions`: 둘째 인자를 `bool` 로 적는다. 블록의 예외를 삼킬 수 있다는 뜻이다.
- `NoneExitTransactions`: 둘째 인자를 `None` 으로 적는다. 삼키지 않는다는 뜻이다.

`after_block_*` 는 블록 안에서 지은 이름을 블록 뒤에서 쓴다. 타입 검사가 블록 뒤를 블록이 예외로
끝난 뒤에도 닿는 자리로 보는지가 둘째 인자에 따라 갈리는지 본다.
"""

from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Protocol

from agent_os.http.account_work import AccountTransactions, AccountWork


class SwallowingTransactions(Protocol):
    def transaction(self) -> AbstractAsyncContextManager[AccountWork, bool]: ...


class NoneExitTransactions(Protocol):
    def transaction(self) -> AbstractAsyncContextManager[AccountWork, None]: ...


async def after_block_default(store: AccountTransactions, name: str) -> int:
    async with store.transaction() as work:
        row = await work.lock(name)
        failures = 0 if row is None else row.failures
    return failures


async def after_block_swallowing(store: SwallowingTransactions, name: str) -> int:
    async with store.transaction() as work:
        row = await work.lock(name)
        failures = 0 if row is None else row.failures
    return failures


async def read_on_none_exit(store: NoneExitTransactions, name: str) -> int | None:
    async with store.transaction() as work:
        row = await work.lock(name)
        return None if row is None else row.failures
