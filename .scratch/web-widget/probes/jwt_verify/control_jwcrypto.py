"""대조군. pyright 가 이 파일을 실제로 읽었는지와, strict 가 `sub` 좁히기를 강제하는 조건을 본다.

`# 기대:` 주석이 줄마다의 기대다. `check_types.py`가 실제 진단과 대조한다. jwcrypto 는 클레임을
JSON 문자열로 주므로 `json.loads`의 `Any`가 출발점이다. 통째로 `Any`인 값은 `object`로 선언하면
대입에서 되좁혀지지 않는다.
"""

from __future__ import annotations

import json

from jwcrypto import jwk, jwt


def declared(token: str, key: jwk.JWK) -> str:
    payload: object = json.loads(jwt.JWT(jwt=token, key=key, algs=["EdDSA"]).claims)
    return payload["sub"]  # 기대: reportIndexIssue, reportUnknownVariableType


def bare(token: str, key: jwk.JWK) -> str:
    payload = json.loads(jwt.JWT(jwt=token, key=key, algs=["EdDSA"]).claims)
    return payload["sub"]  # 기대: 오류 없음
