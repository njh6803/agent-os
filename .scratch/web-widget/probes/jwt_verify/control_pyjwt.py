"""대조군. pyright 가 이 파일을 실제로 읽었는지와, strict 가 `sub` 좁히기를 강제하는 조건을 본다.

`# 기대:` 주석이 줄마다의 기대다. `check_types.py`가 실제 진단과 대조한다. 셋은 같은 일(좁히지
않고 `sub`를 `str`로 돌려준다)을 하고, 오류는 `dict(...)`로 감싼 하나에서만 나야 한다.
"""

from __future__ import annotations

from collections.abc import Mapping

import jwt


def copied(token: str, key: bytes) -> str:
    claims: Mapping[str, object] = dict(jwt.decode(token, key, algorithms=["EdDSA"]))
    return claims["sub"]  # 기대: reportReturnType


def annotated(token: str, key: bytes) -> str:
    # 선언 타입이 있어도 대입한 값의 타입(`dict[str, Any]`)으로 좁혀진다.
    claims: Mapping[str, object] = jwt.decode(token, key, algorithms=["EdDSA"])
    return claims["sub"]  # 기대: 오류 없음


def bare(token: str, key: bytes) -> str:
    claims = jwt.decode(token, key, algorithms=["EdDSA"])
    return claims["sub"]  # 기대: 오류 없음
