"""계정 저장소를 쓰지 않는 시험이 `create_app` 에 넘기는 대역.

로그인 쿠키로 도는 시험(관리 API, 운영자 채널, 최종 사용자 경로)은 계정을 읽고 쓰지 않는다.
다만 앱이 뜰 때 서명 키의 줄을 만들고(`LoginService.ready`) 로그인 쿠키가 든 요청을 검증하려면 키를
읽어야 하므로, 서명 키 둘만 메모리에서 받는다. 그 밖의 메서드는 불리면 시험이 계정을 쓰고 있다는
뜻이라 곧바로 터뜨린다. 계정을 읽고 쓰는 시험은 이 대역이 아니라 진짜 데이터베이스를 쓴다
(`.claude/rules/http.md` 의 테스트 항목).

대역은 포트를 상속하지 않고 시그니처로 만족하며, 시험이 `accounts: AccountStore = UnusedAccounts()`
처럼 포트 타입으로 annotate 한다.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import UUID

from agent_os.http.accounts import (
    AccountRow,
    LinkRow,
    NewAccount,
    RecordKind,
    RefreshRow,
    Taken,
    Tier,
)
from agent_os.http.login_tokens import ACCESS_COOKIE, issue_token

_UNUSED = "이 시험은 계정 저장소를 쓰지 않는다"

# 운영자 경로를 미는 시험이 짧은 JWT 를 직접 서명할 때 쓰는 키와 발급 시각. `UnusedAccounts` 의 기본
# 서명 키가 이것이라, 이 키로 서명한 쿠키를 앱이 맞는 로그인으로 읽는다. 만료는 발급 시각에서 아주
# 먼 뒤라 시험의 가짜 시계가 어느 때를 가리켜도 지나간다. 로그인 경로 자체를 재는 시험은 이것을 쓰지
# 않고 진짜 로그인 경로를 부른다(`tests/test_login_http.py`).
LOGIN_KEY = b"tests-only-signing-key-0123456789abcdef"
_LOGIN_ISSUED = datetime(2026, 1, 1, tzinfo=UTC)
_LOGIN_MINUTES = 60 * 24 * 365 * 100


def operator_cookie(tier: Tier = "admin", name: str = "kim.min") -> dict[str, str]:
    """운영자 로그인을 흉내 낸 `Cookie` 머리 하나. `UnusedAccounts` 의 키로 서명한 짧은 JWT 를
    싣는다.

    계정 저장소에 그 계정이 있는지는 보지 않는다. 짧은 JWT 의 검증은 서명과 만료만 본다.
    """
    token = issue_token(
        LOGIN_KEY,
        name=name,
        login_id=UUID(int=1),
        tier=tier,
        now=_LOGIN_ISSUED,
        token_minutes=_LOGIN_MINUTES,
    )
    return {"Cookie": f"{ACCESS_COOKIE}={token}"}


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
        actor: str | None = None,
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

    async def replace_signing_key(self, key: bytes, *, at: datetime) -> None:
        raise AssertionError(_UNUSED)

    async def lock_refresh(self, token_hash: str) -> RefreshRow | None:
        raise AssertionError(_UNUSED)

    async def read_account(self, name: str) -> AccountRow | None:
        raise AssertionError(_UNUSED)

    async def use_refresh_token(self, token_hash: str, *, at: datetime) -> None:
        raise AssertionError(_UNUSED)

    async def touch_login(self, login_id: UUID, *, at: datetime) -> None:
        raise AssertionError(_UNUSED)

    async def list_accounts(self) -> Sequence[AccountRow]:
        raise AssertionError(_UNUSED)

    async def set_disabled(self, name: str, *, at: datetime | None) -> None:
        raise AssertionError(_UNUSED)

    async def end_other_logins(self, name: str, *, keep: UUID, at: datetime) -> None:
        raise AssertionError(_UNUSED)

    async def add_link(
        self, token_hash: str, account: str, *, at: datetime, expires_at: datetime
    ) -> None:
        raise AssertionError(_UNUSED)

    async def void_links(self, account: str, *, at: datetime) -> None:
        raise AssertionError(_UNUSED)

    async def lock_link(self, token_hash: str) -> LinkRow | None:
        raise AssertionError(_UNUSED)

    async def use_link(self, token_hash: str, *, at: datetime) -> None:
        raise AssertionError(_UNUSED)


class UnusedAccounts:
    """계정을 쓰지 않는 시험의 계정 저장소. 서명 키 하나만 메모리에 둔다."""

    def __init__(self, key: bytes | None = LOGIN_KEY) -> None:
        self.key: bytes | None = key
        # 서명 키 읽기를 센다. `gate` 가 있으면 열릴 때까지 읽기가 끝나지 않는다.
        # `fail_reads` 만큼의 읽기는 값을 읽은 뒤 실패한다.
        self.reads = 0
        self.gate: asyncio.Event | None = None
        self.fail_reads = 0

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[_UnusedWork]:
        yield _UnusedWork(self)
