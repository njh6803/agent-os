"""포트가 줄 여럿을 `list` 로 적은 모양(port_shape_async 대조군). 임시 사본의 대조군 나무에만 둔다.

`agent_os.http.accounts` 의 포트는 `Sequence[AccountRow]` 다. 여기는 같은 메서드를
`list[AccountRow]` 로 적는다. `list` 는 원소의 타입에서 불변이라 어댑터의 `list[Row]` 가 맞지
않는지를 본다.
"""

from __future__ import annotations

from typing import Protocol

from agent_os.http.accounts import AccountRow


class ListPort(Protocol):
    async def list_all(self) -> list[AccountRow]: ...


async def list_names(store: ListPort) -> list[str]:
    return [row.name for row in await store.list_all()]
