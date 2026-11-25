"""운영자 계정의 이름 규칙과 계정 저장소의 포트(ADR 0062 결정 "계정"과 "경로와 층").

포트(바깥 저장소에 닿는 자리를 타입으로 적은 약속)는 `Database` 포트(`agent_os.http.database`) 옆에
선언한다. PostgreSQL 구현은 `agent_os.adapters`가 들고, 어댑터는 이 모듈을 가져오지 않고
시그니처(메서드의 이름과 인자와 돌려주는 타입)로 만족한다. 그래서 포트가 주고받는 줄은 여기서 읽기
전용 Protocol로 적고 어댑터는 자기 타입으로 낸다. 두 쪽이 어긋나면 둘을 함께 가져오는 자리(조립하는
`main`, 포트 타입을 적은 시험 픽스처)의 타입 검사가 잡는다.

**포트의 메서드는 지금 쓰는 것만 있다.** 첫 쓰는 곳은 서버 명령
`agent-os operator system-admin`이다. 로그인과 계정 경로가 쓰는 메서드는 그 일을 들이는 티켓이
더한다.

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

type Tier = Literal["system_admin", "admin"]
type Taken = Literal["taken"]
# 로그인 기록에 남기는 일의 종류. 닫힌 목록이고, 열넷 가운데 지금 쓰는 하나만 있다(명세 "로그인
# 기록").
type RecordKind = Literal["system_admin_set"]

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

    async def record(self, kind: RecordKind, *, at: datetime, account: str) -> None:
        """로그인 기록에 한 줄을 더한다. 비밀번호와 해시는 어느 줄에도 싣지 않는다(원칙 V)."""
        ...


class AccountStore(Protocol):
    """계정을 읽고 쓰는 포트. 어댑터는 상속하지 않고 시그니처로 만족한다."""

    def transaction(self) -> AbstractAsyncContextManager[AccountWork]:
        """트랜잭션 하나를 연다. 블록을 정상으로 나오면 적고, 예외로 나오면 되돌린다."""
        ...
