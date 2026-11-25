"""PostgreSQL 어댑터가 데이터베이스의 예외를 읽는 두 함수.

연결 어댑터(`database.py`)와 계정 어댑터(`accounts.py`)가 함께 쓴다. 둘이 서로를 가져오면 순환이라
(연결 어댑터가 계정 어댑터를 만든다) 예외를 읽는 일을 이 모듈로 뺐다. 드라이버(asyncpg)를 가져오지
않고 예외의 클래스가 아니라 PostgreSQL 의 오류 번호(SQLSTATE) 속성으로 읽는다.
"""

from __future__ import annotations


def error_chain(error: BaseException) -> list[BaseException]:
    """예외와 그 원인들. SQLAlchemy 가 감싼 경우에도 드라이버의 예외를 찾으려고 따라간다."""
    seen: list[BaseException] = []
    current: BaseException | None = error
    while current is not None and all(current is not item for item in seen):
        seen.append(current)
        current = current.__cause__ or current.__context__
    return seen


def sqlstate_of(error: BaseException) -> str | None:
    """예외 사슬에서 찾은 PostgreSQL 의 오류 번호. 없으면 `None`."""
    for item in error_chain(error):
        state = getattr(item, "sqlstate", None)
        if isinstance(state, str):
            return state
    return None
