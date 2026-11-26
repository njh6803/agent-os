"""계정 저장소를 쓰지 않는 시험이 `create_app` 에 넘기는 대역.

공유 토큰으로 도는 지금의 시험(관리 API, 운영자 채널, 최종 사용자 경로)은 계정을 읽고 쓰지 않는다.
다만 앱이 뜰 때 서명 키의 줄을 만들고(`LoginService.ready`) 로그인 쿠키가 든 요청을 검증하려면 키를
읽어야 하므로, 서명 키 둘만 메모리에서 받는다. 그 밖의 메서드는 불리면 시험이 계정을 쓰고 있다는
뜻이라 곧바로 터뜨린다. 계정을 읽고 쓰는 시험은 이 대역이 아니라 진짜 데이터베이스를 쓴다
(`.claude/rules/http.md` 의 테스트 항목).

대역은 포트를 상속하지 않고 시그니처로 만족하며, 시험이 `accounts: AccountStore = UnusedAccounts()`
처럼 포트 타입으로 annotate 한다.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import UUID

from agent_os.http.accounts import AccountRow, NewAccount, RecordKind, Taken

_UNUSED = "이 시험은 계정 저장소를 쓰지 않는다"


class _UnusedWork:
    """서명 키만 메모리에 두는 트랜잭션. 나머지는 부르면 터진다."""

    def __init__(self, store: UnusedAccounts) -> None:
        self._store = store

    async def read_signing_key(self) -> bytes | None:
        self._store.reads += 1
        key = self._store.key
        # 값을 읽은 뒤 트랜잭션을 연 채 붙잡아, 읽는 도중에 다른 요청이 오는 장면을 만든다
        if self._store.gate is not None:
            await self._store.gate.wait()
        if self._store.fail_reads > 0:
            self._store.fail_reads -= 1
            raise RuntimeError("서명 키를 읽지 못했다")
        return key

    async def ensure_signing_key(self, key: bytes, *, at: datetime) -> None:
        if self._store.key is None:
            self._store.key = key

    async def lock_system_admin(self) -> AccountRow | None:
        raise AssertionError(_UNUSED)

    async def lock(self, name: str) -> AccountRow | None:
        raise AssertionError(_UNUSED)

    async def add(self, account: NewAccount) -> AccountRow | Taken:
        raise AssertionError(_UNUSED)

    async def reset_password(self, name: str, *, password_hash: str) -> None:
        raise AssertionError(_UNUSED)

    async def end_logins(self, name: str, *, at: datetime) -> None:
        raise AssertionError(_UNUSED)

    async def record(
        self,
        kind: RecordKind,
        *,
        at: datetime,
        account: str | None,
        address: str | None = None,
    ) -> None:
        raise AssertionError(_UNUSED)

    async def any_account(self) -> bool:
        raise AssertionError(_UNUSED)

    async def set_failures(
        self, name: str, *, failures: int, locked_until: datetime | None
    ) -> None:
        raise AssertionError(_UNUSED)

    async def clear_failures(self, name: str) -> None:
        raise AssertionError(_UNUSED)

    async def delete_ended_logins(
        self, name: str, *, idle_before: datetime, total_before: datetime
    ) -> None:
        raise AssertionError(_UNUSED)

    async def open_login(self, login_id: UUID, name: str, *, at: datetime) -> None:
        raise AssertionError(_UNUSED)

    async def add_refresh_token(self, token_hash: str, login_id: UUID, *, at: datetime) -> None:
        raise AssertionError(_UNUSED)

    async def end_login(self, login_id: UUID, *, at: datetime) -> None:
        raise AssertionError(_UNUSED)


class UnusedAccounts:
    """계정을 쓰지 않는 시험의 계정 저장소. 서명 키 하나만 메모리에 둔다."""

    def __init__(self) -> None:
        self.key: bytes | None = None
        # 서명 키 읽기를 센다. `gate` 가 있으면 열릴 때까지 읽기가 끝나지 않는다.
        # `fail_reads` 만큼의 읽기는 값을 읽은 뒤 실패한다.
        self.reads = 0
        self.gate: asyncio.Event | None = None
        self.fail_reads = 0

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[_UnusedWork]:
        yield _UnusedWork(self)
