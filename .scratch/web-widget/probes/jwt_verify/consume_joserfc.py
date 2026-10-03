"""joserfc 로 위젯 토큰을 검증하고 `sub`를 `str`로 꺼내는 소비 지점.

`check_types.py`가 이 파일을 `tests/` 아래로 복사해 저장소의 pyright strict 설정으로 검사하고,
`cases.py`가 실제로 서명한 토큰으로 돌린다. 키는 형식이 있는 객체(`OctKey`·`OKPKey`·`RSAKey`)라
`load_key`가 설정의 바이트를 알고리즘에 맞는 형식으로 읽는다.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Literal

from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import OctKey, OKPKey, RSAKey

# "EdDSA"는 RFC 9864 가 폐기한 이름이고 "Ed25519"가 그 자리를 잇는다. 둘 다 같은 서명이다.
type Algorithm = Literal["HS256", "EdDSA", "Ed25519", "RS256"]
type VerifyKey = OctKey | OKPKey | RSAKey


class InvalidToken(Exception):
    """검증 실패는 이 예외 하나로 모은다. 라이브러리의 원인은 `__cause__`에 남는다."""


def load_key(algorithm: Algorithm, material: bytes) -> VerifyKey:
    """HS256 이면 공유 비밀, 나머지는 PEM 공개 키."""
    match algorithm:
        case "HS256":
            return OctKey.import_key(material)
        case "EdDSA" | "Ed25519":
            return OKPKey.import_key(material)
        case "RS256":
            return RSAKey.import_key(material)


def verified_subject(
    token: str, key: VerifyKey, *, algorithm: Algorithm, audience: str, issuer: str
) -> str:
    # 클레임은 있을 때만 검사된다(`value`를 줘도 없으면 통과). essential 로 있어야 함을 명시한다.
    registry = jwt.JWTClaimsRegistry(
        exp={"essential": True},
        aud={"essential": True, "value": audience},
        iss={"essential": True, "value": issuer},
        sub={"essential": True},
    )
    try:
        decoded = jwt.decode(token, key, algorithms=[algorithm])
        registry.validate(decoded.claims)
    except JoseError as error:
        raise InvalidToken(f"{type(error).__name__}: {error}") from error
    # `Token.claims`는 `dict[str, Any]`다. 주해만 달면 대입에서 `dict[str, Any]`로
    # 되좁혀지므로(control_joserfc.py) `dict(...)`로 감싸 값 타입을 `object`로 만든다.
    claims: Mapping[str, object] = dict(decoded.claims)
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise InvalidToken("sub 가 비지 않은 문자열이 아니다")
    return subject
