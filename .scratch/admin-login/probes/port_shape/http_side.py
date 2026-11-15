"""`agent_os.http` 의 자리를 흉내 낸 모듈. 계정 포트와 그 포트가 주고받는 값의 모양을 선언한다.

재는 대상이다(`run.py`). 제품 코드가 아니다. 어댑터 쪽(`adapter_side.py`)은 이 모듈을 가져오지
않는다. 포트가 돌려주는 줄과 받는 값을 Protocol 로 둔 것은, 어댑터가 이 모듈의 클래스를 가져다 쓸
수 없는 조건에서 타입 검사가 두 쪽의 모양을 맞대게 하려는 것이다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

type Tier = Literal["system_admin", "admin"]


class AccountRow(Protocol):
    """포트가 돌려주는 계정 한 줄. 읽기만 한다."""

    @property
    def name(self) -> str: ...

    @property
    def tier(self) -> Tier: ...

    @property
    def password_hash(self) -> str | None: ...

    @property
    def locked_until(self) -> datetime | None: ...


class NewAccount(Protocol):
    """포트가 받는 새 계정."""

    @property
    def name(self) -> str: ...

    @property
    def tier(self) -> Tier: ...


class AccountStore(Protocol):
    """계정을 읽고 쓰는 포트. 어댑터는 이 클래스를 상속하지 않고 시그니처로 만족한다."""

    def find(self, name: str) -> AccountRow | None: ...

    def add(self, account: NewAccount) -> AccountRow: ...

    def record_failure(self, name: str, *, at: datetime) -> int: ...


@dataclass(frozen=True)
class Draft:
    """이 층이 포트에 넘기는 새 계정."""

    name: str
    tier: Tier


def tier_after_adding(store: AccountStore, name: str, *, at: datetime) -> tuple[Tier, int]:
    """포트를 쓰는 쪽(로그인 검사와 관리 라우터의 자리)."""
    added = store.add(Draft(name=name, tier="admin"))
    found = store.find(added.name)
    if found is None:
        raise LookupError(name)
    return found.tier, store.record_failure(found.name, at=at)
