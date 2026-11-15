"""조합 모듈이 함께 쓰는 값 모양과, 드라이버가 타입 없이 돌려준 값을 좁히는 도우미.

도우미는 `object` 를 받아 `isinstance` 로 좁힌다. 드라이버가 `Any` 로 돌려준 값을 금지된 이름 없이
타입 있는 값으로 바꾸는 길이 이것 하나라, 어느 조합이 이 도우미를 몇 번 부르는지가 곧 그 조합의
타입 마찰이다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Account:
    id: int
    name: str
    password_hash: str
    failed_attempts: int
    locked_until: datetime | None


def as_int(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"int 가 아니다: {type(value).__name__}")
    return value


def as_str(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError(f"str 이 아니다: {type(value).__name__}")
    return value


def as_datetime_or_none(value: object) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    raise TypeError(f"datetime 도 None 도 아니다: {type(value).__name__}")
