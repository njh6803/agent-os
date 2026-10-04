"""jwcrypto 로 위젯 토큰을 검증하고 `sub`를 `str`로 꺼내는 소비 지점.

`check_types.py`가 이 파일을 `tests/` 아래로 복사해 저장소의 pyright strict 설정으로 검사하고,
`cases.py`가 실제로 서명한 토큰으로 돌린다. jwcrypto 는 클레임을 JSON 문자열로 돌려주므로
`json.loads`의 결과를 패턴 매칭으로 좁힌다.
"""

from __future__ import annotations

import json
from typing import Literal

from jwcrypto import jwk, jwt
from jwcrypto.common import JWException, base64url_encode

type Algorithm = Literal["HS256", "EdDSA", "Ed25519", "RS256"]


class InvalidToken(Exception):
    """검증 실패는 이 예외 하나로 모은다. 라이브러리의 원인은 `__cause__`에 남는다."""


def load_key(algorithm: Algorithm, material: bytes) -> jwk.JWK:
    """HS256 이면 공유 비밀, 나머지는 PEM 공개 키."""
    if algorithm == "HS256":
        return jwk.JWK(kty="oct", k=base64url_encode(material))
    return jwk.JWK.from_pem(material)


def verified_subject(
    token: str, key: jwk.JWK, *, algorithm: Algorithm, audience: str, issuer: str
) -> str:
    try:
        decoded = jwt.JWT(
            jwt=token,
            key=key,
            algs=[algorithm],
            # 값이 None 이면 있어야 한다는 뜻이고, 값이 있으면 같아야 한다.
            check_claims={"exp": None, "aud": audience, "iss": issuer, "sub": None},
            expected_type="JWS",
        )
        payload: object = json.loads(decoded.claims)
    except (JWException, ValueError) as error:
        raise InvalidToken(f"{type(error).__name__}: {error}") from error
    match payload:
        case {"sub": str() as subject} if subject:
            return subject
        case _:
            raise InvalidToken("sub 가 비지 않은 문자열이 아니다")
