"""테스트가 사이트처럼 서명 토큰을 만든다. 최종 사용자 면을 미는 테스트 셋이 같이 쓴다.

키는 테스트가 `cryptography` 로 직접 만들고 RS256 으로 서명한다(end-user-channel 명세 "이음매").
서버는 공개 키만 받는다. 라이브러리가 만들어 주지 않는 토큰(서명 없는 `alg: none`, 공개 키 PEM 을
HMAC 비밀로 쓴 HS256)은 손으로 조립한다. 테스트 모듈이 아니라 수집되지 않는다. 저장소 루트가 pytest
의 `pythonpath` 라 `tests.signing` 으로 import 한다.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from agent_os.http.sites import SiteKey

AUDIENCE = "agent-os"


@dataclass(frozen=True)
class SigningKey:
    """사이트의 키 하나. 비밀 키로 서명하고 공개 키를 사이트 목록에 올린다."""

    private: rsa.RSAPrivateKey
    kid: str | None

    def site_key(self) -> SiteKey:
        """사이트 목록에 올리는 공개 키."""
        return SiteKey(kid=self.kid, key=self.private.public_key())

    def public_pem(self) -> str:
        """사이트 파일에 적는 공개 키(SubjectPublicKeyInfo PEM)."""
        return (
            self.private.public_key()
            .public_bytes(
                serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
            )
            .decode("ascii")
        )


def new_key(kid: str | None = None) -> SigningKey:
    """RSA 2048 비트 키 하나. 실행마다 새로 만든다."""
    return SigningKey(rsa.generate_private_key(public_exponent=65537, key_size=2048), kid)


def claims(
    issuer: str,
    subject: object,
    now: datetime,
    *,
    lifetime: int = 300,
    audience: object = AUDIENCE,
) -> dict[str, object]:
    """필수 클레임 다섯을 갖춘 클레임. 발급 시각이 지금이고 수명이 `lifetime` 초다."""
    issued = int(now.timestamp())
    return {
        "iss": issuer,
        "sub": subject,
        "aud": audience,
        "iat": issued,
        "exp": issued + lifetime,
    }


def sign(key: SigningKey, payload: Mapping[str, object], *, kid: str | None = None) -> str:
    """RS256 으로 서명한다. 헤더의 `kid` 는 주지 않으면 그 키의 것이다."""
    chosen = kid if kid is not None else key.kid
    headers = None if chosen is None else {"kid": chosen}
    return jwt.encode(dict(payload), key.private, algorithm="RS256", headers=headers)


def assembled(header: Mapping[str, object], payload: Mapping[str, object], signature: bytes) -> str:
    """헤더와 클레임과 서명을 손으로 이어 붙인 토큰. 라이브러리가 만들지 않는 모양을 만든다."""
    return f"{_signing_input(header, payload)}.{_part(signature)}"


def unsigned(payload: Mapping[str, object]) -> str:
    """`alg: none` 토큰. 서명이 비어 있다."""
    return assembled({"alg": "none", "typ": "JWT"}, payload, b"")


def hs256_with(secret: bytes, payload: Mapping[str, object]) -> str:
    """HS256 토큰. 공개 키 PEM 을 비밀로 쓰는 알고리즘 혼동 공격의 모양이다."""
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = _signing_input(header, payload).encode("ascii")
    return assembled(header, payload, hmac.new(secret, signing_input, hashlib.sha256).digest())


def bearer(token: str) -> dict[str, str]:
    """`Authorization` 헤더 하나."""
    return {"Authorization": f"Bearer {token}"}


def _signing_input(header: Mapping[str, object], payload: Mapping[str, object]) -> str:
    """서명이 덮는 앞의 두 조각."""
    return f"{_part(json.dumps(dict(header)).encode())}.{_part(json.dumps(dict(payload)).encode())}"


def _part(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")
