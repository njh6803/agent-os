"""운영자 로그인의 판정: 로그인, 로그아웃, 첫 계정 확인, 서명 키, 해시 전용 스레드(ADR 0062).

**로그인의 차례**는 명세 admin-login "로그인"이 정한다. 틀린 횟수를 견주기 전에 짧은 트랜잭션에서
줄을 잠가 센다. 비밀번호는 연결을 쥐지 않은 채 해시 전용 스레드에서 견준다. 맞으면 둘째 트랜잭션에서
줄을 다시 잠가 해시가 그대로이고 계정이 활성인지 본 뒤에 횟수와 잠금을 지우고 로그인 한 건을 연다.
같은 계정의 시도를 줄 잠금으로 차례로 세우면 기다리는 시도마다 연결을 하나씩 쥐어 다른 운영자의
로그인이 연결을 기다리다 실패한다. 그래서 횟수를 먼저 세고 견줌은 트랜잭션 밖에서 한다.

**해시 전용 스레드 넷.** 해시 한 번은 19 MiB 를 쓰고, 일꾼 스레드가 정리된 뒤에도 그만큼이 상주로
남았다(남는 까닭은 어림이다). 해시가 기본 일꾼 스레드 묶음의 여러 스레드(36~43개)에 돌아가며 얹히면
685~818 MiB 가 남았고, 전용 넷에서는 76 MiB 였다(프로브 `.scratch/admin-login/probes/hash_load/`).
넷을 넘은 로그인은 거절하지 않고 차례를 기다린다.

**뜰 때 만드는 것.** 가짜 해시(없는 계정의 로그인도 같은 시간이 걸리게 견주는 해시), 해시 전용
스레드, 서명 키의 줄은 `serve` 가 뜰 때 만든다. `ASGITransport` 는 수명 주기를 돌리지 않으므로
수명 주기에만 두면 시험의 앱에는 없다. 그래서 `ready()` 가 처음 쓸 때도 같은 자리를 지나게 하고,
수명 주기도 같은 `ready()` 를 부른다. 두 길이 한 함수를 지나므로 둘 가운데 먼저 닿는 쪽이 만든다.

**기록.** 로그인 기록은 결과가 정해진 뒤에 적는다. 없는 이름으로 온 실패에는 입력한 이름을
남기지 않는다. 비밀번호와 갱신용 번호와 해시는 어느 줄에도 싣지 않는다(원칙 V).
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import secrets
import uuid
from collections.abc import AsyncGenerator
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta

from agent_os.core.ports import Clock
from agent_os.http.accounts import (
    AccountRow,
    AccountStore,
    fold_account_name,
    is_account_name,
)
from agent_os.http.login_tokens import (
    SIGNING_KEY_REREAD,
    LoginClaims,
    LoginDurations,
    clearing_cookie_lines,
    issue_token,
    lock_duration,
    login_cookie_lines,
    refresh_max_age,
    verify_token,
)
from agent_os.http.passwords import hash_password, needs_rehash, password_matches

HASH_THREADS = 4
SIGNING_KEY_BYTES = 32
# 가짜 해시를 만드는 글. 어떤 계정의 비밀번호도 아니다
_FAKE_PASSWORD = "Fake-password-for-timing-1!"


@dataclass(frozen=True)
class _Rejected:
    """틀린 횟수를 세지 않고 거절하는 시도. 없는 이름이거나 비활성이거나 잠겼거나 비밀번호가
    없다."""

    account: str | None


@dataclass(frozen=True)
class _Counted:
    """횟수를 하나 늘린 시도. 저장된 해시와 견줄 차례다."""

    name: str
    stored_hash: str
    locked: bool


class SigningKeys:
    """서명 키를 메모리에 두고, 마지막으로 읽은 뒤 10초가 지난 다음 쓸 때 다시 읽는다.

    10초는 주입된 시계로 센다. 프로세스의 단조 시계로 세면 시험이 키를 바꾼 뒤 10초를 실제로
    기다려야 한다. 줄이 없으면 넣고 읽는다. 넣기는 "없으면 넣는다" 한 문장이라 `serve` 둘이
    함께 떠도 키가 하나로 모인다.
    """

    def __init__(self, accounts: AccountStore, clock: Clock) -> None:
        self._accounts = accounts
        self._clock = clock
        self._key: bytes | None = None
        self._read_at: datetime | None = None
        # 읽기는 한 번에 하나다. 겹치면 먼저 시작한 읽기가 늦게 끝나 옛 키를 캐시에 되돌릴 수 있고,
        # 만료된 순간에 온 요청마다 읽어 10초에 한 번이라는 약속도 깨진다
        self._lock = asyncio.Lock()

    async def current(self) -> bytes:
        cached = self._cached(self._clock.now())
        if cached is not None:
            return cached
        async with self._lock:
            # 기다리는 사이 앞선 읽기가 끝났을 수 있다. 앞선 읽기가 실패했으면 캐시가 그대로라 다시
            # 읽는다
            now = self._clock.now()
            cached = self._cached(now)
            if cached is not None:
                return cached
            return await self._read(now)

    async def ensure(self) -> None:
        """줄이 없으면 넣고 지금 값을 읽어 둔다. 뜰 때 한 번 부른다."""
        async with self._lock:
            await self._read(self._clock.now())

    def _cached(self, now: datetime) -> bytes | None:
        """다시 읽을 때가 되지 않았으면 메모리의 키, 아니면 없음."""
        if self._key is None or self._read_at is None:
            return None
        return self._key if now - self._read_at < SIGNING_KEY_REREAD else None

    async def _read(self, now: datetime) -> bytes:
        async with self._accounts.transaction() as work:
            key = await work.read_signing_key()
            if key is None:
                await work.ensure_signing_key(os.urandom(SIGNING_KEY_BYTES), at=now)
                key = await work.read_signing_key()
        if key is None:
            raise RuntimeError("서명 키를 넣었는데 읽지 못했다")
        self._key = key
        self._read_at = now
        return key


class LoginService:
    """로그인과 로그아웃과 첫 계정 확인. 미들웨어가 짧은 JWT 를 검증하는 길(`verify`)도 겸한다."""

    def __init__(self, *, accounts: AccountStore, clock: Clock, durations: LoginDurations) -> None:
        self._accounts = accounts
        self._clock = clock
        self._durations = durations
        self._keys = SigningKeys(accounts, clock)
        self._pool: ThreadPoolExecutor | None = None
        self._fake_hash: str | None = None
        self._ready_lock = asyncio.Lock()

    async def ready(self) -> None:
        """가짜 해시와 해시 전용 스레드와 서명 키의 줄을 만든다. 여러 번 불러도 한 번만 만든다."""
        if self._pool is not None:
            return
        async with self._ready_lock:
            if self._pool is not None:
                return
            pool = ThreadPoolExecutor(max_workers=HASH_THREADS, thread_name_prefix="agent-os-hash")
            try:
                fake = await asyncio.get_running_loop().run_in_executor(
                    pool, hash_password, _FAKE_PASSWORD
                )
                await self._keys.ensure()
            except BaseException:
                pool.shutdown(wait=False, cancel_futures=True)
                raise
            self._fake_hash = fake
            self._pool = pool

    async def close(self) -> None:
        """해시 전용 스레드를 닫는다. 이미 시작한 견줌은 끝까지 돈다."""
        pool, self._pool = self._pool, None
        self._fake_hash = None
        if pool is not None:
            pool.shutdown(wait=False, cancel_futures=True)

    @asynccontextmanager
    async def lifespan(self) -> AsyncGenerator[None]:
        """서버가 뜰 때 `ready()` 를, 멈출 때 `close()` 를 부른다. 라우터의 수명에 건다."""
        await self.ready()
        try:
            yield
        finally:
            await self.close()

    async def verify(self, token: str | None) -> LoginClaims | None:
        """짧은 JWT 를 검증한다. 토큰이 없으면 데이터베이스도 읽지 않고 없음이다."""
        if token is None:
            return None
        key = await self._keys.current()
        return verify_token(token, key, self._clock.now())

    async def needs_first_account(self) -> bool:
        async with self._accounts.transaction() as work:
            return not await work.any_account()

    async def log_in(
        self, raw_name: str, password: str, *, address: str | None
    ) -> list[str] | None:
        """로그인한다. 성공이면 심을 쿠키 줄 둘, 실패이면 `None`(밖으로는 401 하나)."""
        await self.ready()
        name = fold_account_name(raw_name)
        counted = await self._take_attempt(name)
        if isinstance(counted, _Rejected):
            # 어느 갈래든 해시와 한 번 견주어 걸린 시간을 맞춘다. 결과는 버린다
            await self._compare(self._fake(), password)
            await self._record_failure(counted.account, locked=False, address=address)
            return None
        if not await self._compare(counted.stored_hash, password):
            await self._record_failure(counted.name, locked=counted.locked, address=address)
            return None
        # 파라미터가 달라진 저장 값은 맞은 지금 새로 해시한다
        new_hash = await self._hash(password) if needs_rehash(counted.stored_hash) else None
        key = await self._keys.current()
        opened = await self._open(counted, new_hash, address=address)
        if opened is None:
            # 비밀번호는 맞았다. 잠금은 틀린 비밀번호가 거는 것이라 `locked` 줄은 남기지 않는다
            await self._record_failure(counted.name, locked=False, address=address)
            return None
        row, login_id, refresh_token, now = opened
        access = issue_token(
            key,
            name=row.name,
            login_id=login_id,
            tier=row.tier,
            now=now,
            token_minutes=self._durations.token_minutes,
        )
        max_age = refresh_max_age(self._durations, logged_in_at=now, now=now)
        return login_cookie_lines(access, refresh_token, refresh_max_age=max_age)

    async def log_out(self, claims: LoginClaims, *, address: str | None) -> list[str]:
        """짧은 JWT 가 가리키는 로그인 한 건을 끊고 쿠키를 지우는 줄 둘을 낸다."""
        async with self._accounts.transaction() as work:
            now = self._clock.now()
            await work.end_login(claims.login_id, at=now)
            await work.record("logged_out", at=now, account=claims.name, address=address)
        return clearing_cookie_lines()

    async def _take_attempt(self, name: str) -> _Counted | _Rejected:
        """줄을 잠가 읽고 틀린 횟수를 미리 하나 늘린다. 거절하는 갈래는 줄을 바꾸지 않는다."""
        if not is_account_name(name):
            return _Rejected(None)
        async with self._accounts.transaction() as work:
            row = await work.lock(name)
            now = self._clock.now()
            if row is None:
                return _Rejected(None)
            stored = row.password_hash
            locked = row.locked_until is not None and row.locked_until > now
            if row.disabled_at is not None or stored is None or locked:
                return _Rejected(row.name)
            failures = row.failures + 1
            length = lock_duration(failures)
            until = None if length is None else now + length
            await work.set_failures(name, failures=failures, locked_until=until)
            return _Counted(row.name, stored, until is not None)

    async def _open(
        self, counted: _Counted, new_hash: str | None, *, address: str | None
    ) -> tuple[AccountRow, uuid.UUID, str, datetime] | None:
        """맞은 시도를 마무리하는 둘째 트랜잭션. 해시가 바뀌었거나 비활성이면 아무것도 바꾸지
        않는다."""
        async with self._accounts.transaction() as work:
            row = await work.lock(counted.name)
            now = self._clock.now()
            if (
                row is None
                or row.password_hash != counted.stored_hash
                or row.disabled_at is not None
            ):
                return None
            if new_hash is not None:
                await work.reset_password(row.name, password_hash=new_hash)
            else:
                await work.clear_failures(row.name)
            durations = self._durations
            await work.delete_ended_logins(
                row.name,
                idle_before=now - _minutes(durations.idle_minutes),
                total_before=now - _minutes(durations.total_minutes),
            )
            login_id = uuid.uuid4()
            refresh_token = secrets.token_urlsafe(32)
            await work.open_login(login_id, row.name, at=now)
            await work.add_refresh_token(_digest(refresh_token), login_id, at=now)
            await work.record("login_succeeded", at=now, account=row.name, address=address)
            return row, login_id, refresh_token, now

    async def _record_failure(
        self, account: str | None, *, locked: bool, address: str | None
    ) -> None:
        """실패의 기록. 이 시도가 잠금을 걸었으면 `locked` 한 줄이 더 든다."""
        async with self._accounts.transaction() as work:
            now = self._clock.now()
            await work.record("login_failed", at=now, account=account, address=address)
            if locked:
                await work.record("locked", at=now, account=account, address=address)

    async def _compare(self, stored_hash: str, password: str) -> bool:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._threads(), password_matches, stored_hash, password)

    async def _hash(self, password: str) -> str:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._threads(), hash_password, password)

    def _threads(self) -> ThreadPoolExecutor:
        if self._pool is None:
            raise RuntimeError("해시 전용 스레드가 없다. ready() 를 먼저 부른다")
        return self._pool

    def _fake(self) -> str:
        if self._fake_hash is None:
            raise RuntimeError("가짜 해시가 없다. ready() 를 먼저 부른다")
        return self._fake_hash


def _digest(token: str) -> str:
    """갱신용 번호의 SHA-256 해시(16진수). 서버에는 이것만 둔다."""
    return hashlib.sha256(token.encode("ascii")).hexdigest()


def _minutes(count: int) -> timedelta:
    return timedelta(minutes=count)
