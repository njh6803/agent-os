"""계정을 다루는 판정: 목록, 만들기, 링크 만들기, 활성과 비활성, 잠금 풀기(ADR 0062, 명세
admin-login "계정을 다루는 경로").

판정은 모두 짧은 트랜잭션 하나다. 해시를 만들거나 견주는 일이 없어 해시 전용 스레드를 쓰지 않는다.
계정의 줄을 먼저 잠그고 그다음에 링크를 바꾼다. 링크로 비밀번호를 정하는 쪽(`lock_link`)이 같은
순서로 잠가 서로 기다리지 않는다.

**한 일이 있을 때만 로그인 기록을 남긴다.** 이미 그 상태인 활성 바꾸기와 잠긴 적이 없는 계정의 잠금
풀기는 아무것도 바꾸지 않으므로 줄을 남기지 않는다. 기록에는 비밀번호도 링크 토큰도 싣지 않는다(원칙
V). 링크 토큰은 이 모듈이 만들어 호출한 쪽에 한 번 돌려줄 뿐 서버에는 해시만 남는다.
"""

from __future__ import annotations

import hashlib
import secrets
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

from agent_os.core.ports import Clock
from agent_os.http.accounts import AccountRow, AccountStore, AccountWork, Taken

# 비밀번호 링크의 기한. 만든 때부터 센다(명세 "비밀번호 링크")
LINK_LIFETIME = timedelta(hours=24)
LINK_TOKEN_BYTES = 32

type Missing = Literal["absent"]
# 시스템 관리자는 서버 명령으로 비밀번호를 다시 정하고, 이 경로로는 링크도 활성 바꾸기도 받지 않는다
type Protected = Literal["system_admin"]
type LinkRefusal = Missing | Protected | Literal["disabled"]


@dataclass(frozen=True)
class IssuedLink:
    """만든 링크. 토큰은 이때 한 번만 보이고 서버에는 해시만 남는다."""

    token: str
    expires_at: datetime


@dataclass(frozen=True)
class CreatedAccount:
    """만든 계정과 그 계정의 첫 링크."""

    name: str
    link: IssuedLink


def token_digest(token: str) -> str:
    """링크 토큰이나 갱신용 번호의 SHA-256 해시(16진수). 서버에는 이것만 둔다."""
    return hashlib.sha256(token.encode("ascii")).hexdigest()


@dataclass(frozen=True)
class _NewAccount:
    name: str
    tier: Literal["admin"]
    password_hash: None
    created_at: datetime


class AccountAdmin:
    """계정을 다루는 일. 계정을 다룰 권한은 라우터가 먼저 가렸다."""

    def __init__(self, *, accounts: AccountStore, clock: Clock) -> None:
        self._accounts = accounts
        self._clock = clock

    def now(self) -> datetime:
        """목록이 잠금을 풀린 것으로 셀 때 쓰는 지금. 시계는 주입된 하나만 쓴다."""
        return self._clock.now()

    async def list_accounts(self) -> Sequence[AccountRow]:
        async with self._accounts.transaction() as work:
            return await work.list_accounts()

    async def create(self, name: str, *, actor: str, address: str | None) -> CreatedAccount | Taken:
        """관리자 단계의 새 계정을 비밀번호 없이 만들고 첫 링크를 낸다. 같은 이름이 있으면
        `taken`."""
        async with self._accounts.transaction() as work:
            now = self._clock.now()
            added = await work.add(_NewAccount(name, "admin", None, now))
            if added == "taken":
                return "taken"
            link = await self._issue(work, name, now)
            await work.record("account_created", at=now, account=name, address=address, actor=actor)
            await work.record("link_created", at=now, account=name, address=address, actor=actor)
            return CreatedAccount(name=name, link=link)

    async def create_link(
        self, name: str, *, actor: str, address: str | None
    ) -> IssuedLink | LinkRefusal:
        """그 계정의 앞 링크를 못 쓰게 하고 새 링크를 낸다."""
        async with self._accounts.transaction() as work:
            now = self._clock.now()
            row = await work.lock(name)
            if row is None:
                return "absent"
            if row.tier == "system_admin":
                return "system_admin"
            if row.disabled_at is not None:
                return "disabled"
            await work.void_links(name, at=now)
            link = await self._issue(work, name, now)
            await work.record("link_created", at=now, account=name, address=address, actor=actor)
            return link

    async def enable(
        self, name: str, *, actor: str, address: str | None
    ) -> Missing | Protected | None:
        """비활성인 계정을 활성으로 되돌린다. 이미 활성이면 아무것도 바꾸지 않는다. 문제 없으면
        `None`."""
        async with self._accounts.transaction() as work:
            now = self._clock.now()
            row = await work.lock(name)
            if row is None:
                return "absent"
            if row.tier == "system_admin":
                return "system_admin"
            if row.disabled_at is None:
                return None
            await work.set_disabled(name, at=None)
            await work.record("account_enabled", at=now, account=name, address=address, actor=actor)
            return None

    async def disable(
        self, name: str, *, actor: str, address: str | None
    ) -> Missing | Protected | None:
        """계정을 비활성으로 바꾸고 그 계정의 로그인을 모두 끊고 쓰지 않은 링크를 못 쓰게 한다.
        이미 비활성이면 아무것도 바꾸지 않는다. 문제 없으면 `None`."""
        async with self._accounts.transaction() as work:
            now = self._clock.now()
            row = await work.lock(name)
            if row is None:
                return "absent"
            if row.tier == "system_admin":
                return "system_admin"
            if row.disabled_at is not None:
                return None
            await work.set_disabled(name, at=now)
            await work.end_logins(name, at=now)
            await work.void_links(name, at=now)
            await work.record(
                "account_disabled", at=now, account=name, address=address, actor=actor
            )
            return None

    async def unlock(self, name: str, *, actor: str, address: str | None) -> Missing | None:
        """잠금과 틀린 횟수를 지운다. 풀 것이 있었을 때만 기록한다."""
        async with self._accounts.transaction() as work:
            now = self._clock.now()
            row = await work.lock(name)
            if row is None:
                return "absent"
            if row.failures == 0 and row.locked_until is None:
                return None
            await work.clear_failures(name)
            await work.record("unlocked", at=now, account=name, address=address, actor=actor)
            return None

    async def _issue(self, work: AccountWork, name: str, now: datetime) -> IssuedLink:
        token = secrets.token_urlsafe(LINK_TOKEN_BYTES)
        expires_at = now + LINK_LIFETIME
        await work.add_link(token_digest(token), name, at=now, expires_at=expires_at)
        return IssuedLink(token=token, expires_at=expires_at)
