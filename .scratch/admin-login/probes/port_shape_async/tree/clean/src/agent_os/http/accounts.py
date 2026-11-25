"""계정 포트와 그 포트를 쓰는 쪽. 프로브(`port_shape_async`)가 임시 사본의 `agent_os.http`
에만 둔다.

제품 코드가 아니다. 포트는 비동기 메서드 넷이다. 줄 하나(`find`), 줄 여럿(`list_all`), 아무것도
돌려주지 않는 쓰기(`record_failure`), 이름이 이미 있으면 포트가 약속한 신호를 내는 쓰기(`add`)다.
줄과 받는 값은 읽기 전용 Protocol 이고 어댑터는 이 모듈을 가져오지 않는다.

`add` 의 '이름이 이미 있음'을 어떻게 알아보는지가 갈래 넷이다.

- core: 예외를 `agent_os.core.conflicts` 에 두고 http 와 어댑터가 함께 가져온다.
- 주입: 예외를 여기(`NameTaken`)에 두고, 조립하는 자리가 그 클래스를 어댑터에 넘긴다.
- 알아보기: 어댑터가 자기 예외를 던지고, 포트의 메서드(`is_name_taken`)가 그것을 알아본다.
- 값: 예외가 아니라 돌려주는 값(`Literal["taken"]`)으로 알린다.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from agent_os.core.conflicts import NameTaken as CoreNameTaken

type Tier = Literal["system_admin", "admin"]
type Taken = Literal["taken"]


class AccountRow(Protocol):
    """포트가 돌려주는 계정 한 줄. 읽기만 한다."""

    @property
    def name(self) -> str: ...

    @property
    def tier(self) -> Tier: ...

    @property
    def password_hash(self) -> str | None: ...

    @property
    def failures(self) -> int: ...

    @property
    def locked_until(self) -> datetime | None: ...


class NewAccount(Protocol):
    """포트가 받는 새 계정."""

    @property
    def name(self) -> str: ...

    @property
    def tier(self) -> Tier: ...


class NameTaken(Exception):
    """이름이 이미 있다(주입 갈래). 글에 이름을 싣지 않는다."""

    def __init__(self, name: str) -> None:
        super().__init__("이름이 이미 있다")
        self.name = name


class AccountStore(Protocol):
    """계정을 읽고 쓰는 포트. 어댑터는 상속하지 않고 시그니처로 만족한다."""

    async def find(self, name: str) -> AccountRow | None: ...

    async def list_all(self) -> Sequence[AccountRow]: ...

    async def record_failure(self, name: str, *, at: datetime) -> None: ...

    async def add(self, account: NewAccount) -> AccountRow: ...


class RecognizingStore(AccountStore, Protocol):
    """알아보기 갈래. 어댑터가 던진 예외가 '이름이 이미 있음'인지 어댑터가 답한다."""

    def is_name_taken(self, error: Exception) -> bool: ...


class ResultStore(Protocol):
    """값 갈래. 이름이 이미 있으면 줄 대신 `"taken"` 을 돌려준다."""

    async def add(self, account: NewAccount) -> AccountRow | Taken: ...


@dataclass(frozen=True)
class Draft:
    """이 층이 포트에 넘기는 새 계정."""

    name: str
    tier: Tier


@dataclass(frozen=True)
class Walk:
    """포트를 한 바퀴 돈 결과. 조립 자리가 이 값을 받아 쓴다."""

    added: str
    found_tier: Tier
    failures_after: int
    locked_until: datetime | None
    listed: tuple[str, ...]
    missing_is_none: bool


async def walk(store: AccountStore, name: str, *, at: datetime) -> Walk:
    """로그인 검사와 관리 라우터의 자리. 넣고, 실패를 두 번 적고, 읽고, 목록을 본다."""
    added = await store.add(Draft(name=name, tier="admin"))
    await store.record_failure(added.name, at=at)
    await store.record_failure(added.name, at=at)
    found = await store.find(added.name)
    if found is None:
        raise LookupError("넣은 계정을 찾지 못했다")
    rows = await store.list_all()
    missing = await store.find(f"{name}_missing")
    return Walk(
        added=added.name,
        found_tier=found.tier,
        failures_after=found.failures,
        locked_until=found.locked_until,
        listed=tuple(row.name for row in rows),
        missing_is_none=missing is None,
    )


async def add_twice_core(store: AccountStore, name: str) -> str:
    """core 갈래. 둘째 넣기가 core 의 예외로 오면 `"taken"`."""
    await store.add(Draft(name=name, tier="admin"))
    try:
        await store.add(Draft(name=name, tier="admin"))
    except CoreNameTaken:
        return "taken"
    return "added twice"


async def add_twice_injected(store: AccountStore, name: str) -> str:
    """주입 갈래. 둘째 넣기가 이 모듈의 예외로 오면 `"taken"`."""
    await store.add(Draft(name=name, tier="admin"))
    try:
        await store.add(Draft(name=name, tier="admin"))
    except NameTaken:
        return "taken"
    return "added twice"


async def add_twice_recognized(store: RecognizingStore, name: str) -> str:
    """알아보기 갈래. 둘째 넣기의 예외를 포트가 알아보면 `"taken"`, 아니면 그대로 올린다."""
    await store.add(Draft(name=name, tier="admin"))
    try:
        await store.add(Draft(name=name, tier="admin"))
    except Exception as error:
        if store.is_name_taken(error):
            return "taken"
        raise
    return "added twice"


async def add_twice_result(store: ResultStore, name: str) -> str:
    """값 갈래. 둘째 넣기가 `"taken"` 을 돌려주면 `"taken"`."""
    first = await store.add(Draft(name=name, tier="admin"))
    if first == "taken":
        return "taken on first"
    second = await store.add(Draft(name=name, tier="admin"))
    if second == "taken":
        return "taken"
    return f"added twice: {second.name}"
