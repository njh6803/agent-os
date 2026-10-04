"""PyJWT 로 위젯 토큰을 검증하고 `sub`를 `str`로 꺼내는 소비 지점.

`check_types.py`가 이 파일을 `tests/` 아래로 복사해 저장소의 pyright strict 설정으로 검사하고,
`cases.py`가 실제로 서명한 토큰으로 돌린다. 키는 HS256 이면 공유 비밀 바이트, 비대칭이면 PEM
공개 키 바이트다. PyJWT 는 같은 `bytes`를 알고리즘에 따라 달리 읽으므로 `algorithms`를 고정한다.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

import jwt

type Algorithm = Literal["HS256", "EdDSA", "RS256"]


class InvalidToken(Exception):
    """검증 실패는 이 예외 하나로 모은다. 라이브러리의 원인은 `__cause__`에 남는다."""


def verified_subject(
    token: str, key: bytes, *, algorithm: Algorithm, audience: str, issuer: str
) -> str:
    try:
        # 라이브러리는 `dict[str, Any]`를 돌려준다. 주해만 달면 대입에서 `dict[str, Any]`로
        # 되좁혀지므로(control_pyjwt.py) `dict(...)`로 감싸 값 타입을 `object`로 만든다.
        # 그래야 아래 좁히기를 pyright 가 요구한다.
        claims: Mapping[str, object] = dict(
            jwt.decode(
                token,
                key,
                algorithms=[algorithm],
                audience=audience,
                issuer=issuer,
                # exp·sub 는 있을 때만 검사된다(aud·iss 는 값을 주면 없을 때도 거부된다).
                # 넷 다 여기 적어 있어야 하는 클레임을 한곳에 둔다.
                options={"require": ["exp", "aud", "iss", "sub"]},
            )
        )
    except jwt.PyJWTError as error:
        raise InvalidToken(f"{type(error).__name__}: {error}") from error
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise InvalidToken("sub 가 비지 않은 문자열이 아니다")
    return subject
