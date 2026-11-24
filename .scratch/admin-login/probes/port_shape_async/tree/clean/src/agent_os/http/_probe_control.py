"""양성 대조(port_shape_async). 임시 사본에만 두고 아무도 가져오지 않는다.

`untyped` 의 `reportMissingParameterType` 은 strict 에서만 오류다. 그래서 그 오류가 나면 이 사본을
strict 로 봤다는 표지다. `reveal_type` 의 정보 한 줄은 임시 사본에만 있는 포트를 pyright 가 풀었다는
표지다(저장소의 `src` 로 풀렸다면 이 가져오기가 `reportMissingImports` 다).
"""

from __future__ import annotations

from typing import reveal_type

from agent_os.http.account_work import AccountTransactions
from agent_os.http.accounts import AccountStore


def untyped(value):
    return value


reveal_type(AccountStore.find)
reveal_type(AccountTransactions.transaction)
