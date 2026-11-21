"""HTTP 쪽이 선언할 포트의 시제품. 어댑터는 이 모듈을 import 하지 않고 시그니처로 만족한다."""

from __future__ import annotations

from typing import Protocol


class Database(Protocol):
    """앱이 뜰 때 데이터베이스를 확인하고 꺼질 때 닫는 데 쓰는 것 둘."""

    async def startup_problem(self) -> str | None:
        """문제가 없으면 None, 있으면 운영자에게 보일 한 줄."""
        ...

    async def close(self) -> None:
        """연결 묶음을 닫는다."""
        ...
