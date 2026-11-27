"""운영자 계정의 이름 규칙과 계정 저장소의 포트(ADR 0062 결정 "계정"과 "경로와 층").

포트(바깥 저장소에 닿는 자리를 타입으로 적은 약속)는 `Database` 포트(`agent_os.http.database`) 옆에
선언한다. PostgreSQL 구현은 `agent_os.adapters`가 들고, 어댑터는 이 모듈을 가져오지 않고
시그니처(메서드의 이름과 인자와 돌려주는 타입)로 만족한다. 그래서 포트가 주고받는 줄은 여기서 읽기
전용 Protocol로 적고 어댑터는 자기 타입으로 낸다. 두 쪽이 어긋나면 둘을 함께 가져오는 자리(조립하는
`main`, 포트 타입을 적은 시험 픽스처)의 타입 검사가 잡는다.

**포트의 메서드는 지금 쓰는 것만 있다.** 첫 쓰는 곳은 서버 명령
`agent-os operator system-admin`이고, 로그인 경로가 둘째, 갱신과 서명 키 바꾸기가 셋째다. 계정
경로가 쓰는 메서드는 그 일을 들이는 티켓이 더한다.

**이름 충돌은 예외가 아니라 돌려주는 값으로 가른다.** 계정을 넣는 메서드(`AccountWork.add`)는 넣은
줄이나 글자 값 `"taken"`을 돌려준다. 예외로 알리는 길은 두 층이 함께 가져올 예외 타입이 없고(core에
계정의 개념을 넣지 않는다), 타입 검사가 유일 제약 위반을 옮기지 않은 어댑터를 잡지 못한다.

**한 트랜잭션에 묶을 일은 `transaction()`이 연다.** 블록을 정상으로 나오면 적고 예외로 나오면
되돌린다. 판정의 규칙(잠그는 시간, 만료)은 `http`의 함수가 갖고 어댑터는 줄을 잠그고 읽고 적는 일만
한다. 어댑터가 적는 시각은 모두 부르는 쪽이 주입된 시계에서 읽어 넘긴 값이다. 어댑터와
마이그레이션은 SQL의 `now()`나 칸의 기본값으로 시각을 짓지 않는다. 그래야 시험의 가짜 시계가 그 칸을
움직인다.
"""

from __future__ import annotations

import re
from contextlib import AbstractAsyncContextManager
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

type Tier = Literal["system_admin", "admin"]
type Taken = Literal["taken"]
# 로그인 기록에 남기는 일의 종류. 닫힌 목록이고, 열넷 가운데 지금 쓰는 것만 있다(명세 "로그인
# 기록"). 나머지는 그 일을 들이는 티켓이 더한다.
type RecordKind = Literal[
    "system_admin_set",
    "login_succeeded",
    "login_failed",
    "locked",
    "logged_out",
    "refresh_reused",
    "signing_key_rotated",
]

ACCOUNT_NAME_RULE_TEXT = (
    "계정 이름은 영문 소문자, 숫자, `.`, `_`, `-`로 3~32자이고 영문자나 숫자로 시작해야 합니다."
)
_ACCOUNT_NAME = re.compile(r"[a-z0-9][a-z0-9._-]{2,31}")
_UPPER_TO_LOWER = {code: code + 32 for code in range(ord("A"), ord("Z") + 1)}


def fold_account_name(text: str) -> str:
    """들어온 이름에서 영문 대문자(A~Z)만 소문자로 바꾼다.

    전각 대문자나 다른 문자 체계의 대문자는 바꾸지 않는다. 바꾸면 규칙에 맞는 이름이 늘어 한 사람을
    두 이름으로 부르게 된다. 바꾼 뒤의 글을 `is_account_name`으로 규칙에 댄다.
    """
    return text.translate(_UPPER_TO_LOWER)


def is_account_name(name: str) -> bool:
    """이름 규칙(영문 소문자, 숫자, `.`, `_`, `-`로 3~32자, 영문자나 숫자로 시작)에 맞는가."""
    return _ACCOUNT_NAME.fullmatch(name) is not None


class AccountRow(Protocol):
    """포트가 돌려주는 계정 한 줄. 읽기만 한다."""

    @property
    def name(self) -> str: ...

    @property
    def tier(self) -> Tier: ...

    @property
    def password_hash(self) -> str | None: ...

    @property
    def disabled_at(self) -> datetime | None: ...

    @property
    def failures(self) -> int: ...

    @property
    def locked_until(self) -> datetime | None: ...

    @property
    def created_at(self) -> datetime: ...


class NewAccount(Protocol):
    """포트가 받는 새 계정. 비밀번호를 정한 계정만 만든다."""

    @property
    def name(self) -> str: ...

    @property
    def tier(self) -> Tier: ...

    @property
    def password_hash(self) -> str: ...

    @property
    def created_at(self) -> datetime: ...


class RefreshRow(Protocol):
    """갱신용 번호 한 줄과 그 번호가 속한 로그인 한 건. 읽기만 한다."""

    @property
    def login_id(self) -> UUID: ...

    @property
    def account(self) -> str: ...

    @property
    def logged_in_at(self) -> datetime: ...

    @property
    def refreshed_at(self) -> datetime: ...

    @property
    def ended_at(self) -> datetime | None: ...

    @property
    def used_at(self) -> datetime | None: ...


class AccountWork(Protocol):
    """트랜잭션 하나 안의 읽기와 쓰기."""

    async def lock_system_admin(self) -> AccountRow | None:
        """시스템 관리자의 줄을 잠가 읽는다. 없으면 `None`. 시스템 관리자는 하나뿐이다."""
        ...

    async def lock(self, name: str) -> AccountRow | None:
        """그 이름의 줄을 잠가 읽는다. 없으면 `None`."""
        ...

    async def add(self, account: NewAccount) -> AccountRow | Taken:
        """계정을 넣는다. 같은 이름이 이미 있거나 시스템 관리자가 이미 있으면 `"taken"`이다."""
        ...

    async def reset_password(self, name: str, *, password_hash: str) -> None:
        """비밀번호 해시를 적고 틀린 횟수와 잠금을 지운다."""
        ...

    async def end_logins(self, name: str, *, at: datetime) -> None:
        """그 계정에서 아직 끊기지 않은 로그인을 한 건도 남기지 않고 끊는다."""
        ...

    async def record(
        self,
        kind: RecordKind,
        *,
        at: datetime,
        account: str | None,
        address: str | None = None,
    ) -> None:
        """로그인 기록에 한 줄을 더한다. 비밀번호와 해시는 어느 줄에도 싣지 않는다(원칙 V).

        대상 계정(`account`)은 없는 이름으로 온 로그인 실패에서 비운다. 접속한 주소(`address`)는
        부르는 쪽이 읽어 넘기고 읽지 못했으면 비운다.
        """
        ...

    async def any_account(self) -> bool:
        """운영자 계정이 하나라도 있는가. 첫 계정 확인이 쓴다."""
        ...

    async def set_failures(
        self, name: str, *, failures: int, locked_until: datetime | None
    ) -> None:
        """연속 틀린 횟수와 잠겨 풀리는 시각을 적는다. 둘 다 부르는 쪽이 규칙으로 정한 값이다."""
        ...

    async def clear_failures(self, name: str) -> None:
        """연속 틀린 횟수와 잠금을 지운다. 해시는 건드리지 않는다."""
        ...

    async def delete_ended_logins(
        self, name: str, *, idle_before: datetime, total_before: datetime
    ) -> None:
        """그 계정의 끝난 로그인을 지운다. 갱신용 번호는 로그인과 함께 지워진다.

        끝난 로그인은 끊긴 것(`ended_at` 이 있다), 마지막 갱신이 `idle_before` 이전인 것(쉬는 시간이
        지났다), 로그인한 때가 `total_before` 이전인 것(총 시간이 지났다)이다. 기준 시각은 부르는
        쪽이 유지 시간 규칙으로 계산해 넘긴다.
        """
        ...

    async def open_login(self, login_id: UUID, name: str, *, at: datetime) -> None:
        """로그인 한 건을 연다. 마지막으로 갱신한 시각은 로그인한 시각과 같다."""
        ...

    async def add_refresh_token(self, token_hash: str, login_id: UUID, *, at: datetime) -> None:
        """갱신용 번호의 해시를 그 로그인 한 건에 더한다. 번호 자체는 서버에 두지 않는다."""
        ...

    async def end_login(self, login_id: UUID, *, at: datetime) -> None:
        """로그인 한 건을 끊는다. 이미 끊겼거나 없으면 아무것도 하지 않는다."""
        ...

    async def ensure_signing_key(self, key: bytes, *, at: datetime) -> None:
        """서명 키의 줄이 없으면 넣는다. 이미 있으면 아무것도 하지 않는다(줄은 하나뿐이다)."""
        ...

    async def read_signing_key(self) -> bytes | None:
        """서명 키. 줄이 없으면 `None`."""
        ...

    async def replace_signing_key(self, key: bytes, *, at: datetime) -> None:
        """서명 키의 줄을 새 키로 바꾼다. 줄이 없으면 넣는다. 옛 키는 남기지 않는다."""
        ...

    async def lock_refresh(self, token_hash: str) -> RefreshRow | None:
        """그 해시의 갱신용 번호와 속한 로그인 한 건의 줄을 함께 잠가 읽는다. 없으면 `None`.

        로그인 줄을 먼저, 번호 줄을 그다음에 잠근다. 로그인 줄을 지우며 번호 줄을 따라 지우는
        쪽(`delete_ended_logins`)과 같은 순서다. 계정의 줄은 잠그지 않는다. 계정을 잠그고 로그인
        줄을 지우는 쪽과 순서가 엇갈려 서로 기다리는 일(교착)을 피하기 위해서다.
        """
        ...

    async def read_account(self, name: str) -> AccountRow | None:
        """그 이름의 줄을 잠그지 않고 읽는다. 없으면 `None`."""
        ...

    async def use_refresh_token(self, token_hash: str, *, at: datetime) -> None:
        """그 번호를 쓴 것으로 적는다. 이미 쓴 것으로 적혀 있으면 처음 쓴 시각을 그대로 둔다."""
        ...

    async def touch_login(self, login_id: UUID, *, at: datetime) -> None:
        """로그인 한 건의 마지막으로 갱신한 시각을 적는다."""
        ...


class AccountStore(Protocol):
    """계정을 읽고 쓰는 포트. 어댑터는 상속하지 않고 시그니처로 만족한다."""

    def transaction(self) -> AbstractAsyncContextManager[AccountWork]:
        """트랜잭션 하나를 연다. 블록을 정상으로 나오면 적고, 예외로 나오면 되돌린다."""
        ...
