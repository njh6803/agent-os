"""NULL 을 받는 칸을 `Column` 의 타입 인자 없이 적은 읽기(port_shape_async 대조군). 임시 사본의
대조군 나무에만 둔다.

`accounts.py` 는 NULL 을 받는 칸을 `Column[str | None]` 으로 적는다. 여기는 같은 칸을 타입 인자
없이 `nullable=True` 로만 적고, `select` 가 그 칸을 어떤 타입으로 푸는지 `reveal_type` 으로
드러낸다.
"""

from __future__ import annotations

from typing import reveal_type

from sqlalchemy import Column, MetaData, Table, Text, select

_metadata = MetaData()
LOOSE_HASH = Column("password_hash", Text, nullable=True)
loose_accounts = Table("accounts", _metadata, LOOSE_HASH)


def loose_query() -> None:
    reveal_type(select(LOOSE_HASH))
