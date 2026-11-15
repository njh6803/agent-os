"""후보 1. 표준 라이브러리 `hashlib.scrypt` 로 비밀번호를 저장하는 작은 모듈.

재는 대상이다(pyright strict 와 타입 우회 검사, `run.py` 의 `types`). 제품 코드가 아니다. 하는 일은
셋이다. 비밀번호로 저장할 문자열을 만들고(`hash_password`), 저장된 문자열과 비밀번호를 견주고
(`verify_password`), 저장된 문자열의 매개변수가 지금 설정보다 약한지 판정한다(`needs_rehash`).

저장 꼴은 `$scrypt$ln=17,r=8,p=1$<소금>$<키>` 다. 소금과 키는 `=` 를 뗀 base64 이고 `ln` 은 N 의
밑이 2 인 로그다. 표준 라이브러리는 이 꼴을 만들거나 읽어 주지 않아 만들기·읽기·견주기·약한지
판정을 모두 여기서 한다. "약하다"는 `ln`, `r`, `p`, 소금 길이, 키 길이 가운데 하나라도 지금 설정보다
작은 것으로 정했다. 이 정의는 이 모듈이 고른 것이고 표준 라이브러리가 주는 것이 아니다.

`maxmem` 은 OpenSSL 이 이 매개변수에 요구하는 바이트 수로 준다. 주지 않으면 권고 매개변수에서
거부된다(`scrypt_maxmem.py` 가 그 문턱을 잰다).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from dataclasses import dataclass

NAME = "scrypt"


@dataclass(frozen=True)
class ScryptParams:
    log_n: int
    r: int
    p: int
    salt_len: int = 16
    key_len: int = 32

    @property
    def maxmem(self) -> int:
        return 128 * self.r * ((1 << self.log_n) + self.p + 2)

    @property
    def prefix(self) -> str:
        return f"${NAME}$ln={self.log_n},r={self.r},p={self.p}$"


# OWASP Password Storage Cheat Sheet 의 scrypt 첫 줄(N=2^17, r=8, p=1).
CURRENT = ScryptParams(log_n=17, r=8, p=1)


@dataclass(frozen=True)
class _Stored:
    params: ScryptParams
    salt: bytes
    key: bytes


def _encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii").rstrip("=")


def _decode(text: str) -> bytes:
    return base64.b64decode(text + "=" * (-len(text) % 4), validate=True)


def _derive(password: str, salt: bytes, params: ScryptParams) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=1 << params.log_n,
        r=params.r,
        p=params.p,
        maxmem=params.maxmem,
        dklen=params.key_len,
    )


def _parse(stored: str) -> _Stored | None:
    parts = stored.split("$")
    if len(parts) != 5 or parts[0] != "" or parts[1] != NAME:
        return None
    numbers: dict[str, int] = {}
    for item in parts[2].split(","):
        name, _, value = item.partition("=")
        if not (value.isascii() and value.isdigit()):
            return None
        numbers[name] = int(value)
    if sorted(numbers) != ["ln", "p", "r"]:
        return None
    try:
        salt, key = _decode(parts[3]), _decode(parts[4])
    except ValueError:
        return None
    params = ScryptParams(numbers["ln"], numbers["r"], numbers["p"], len(salt), len(key))
    return _Stored(params, salt, key)


def hash_password(password: str, params: ScryptParams = CURRENT) -> str:
    salt = secrets.token_bytes(params.salt_len)
    key = _derive(password, salt, params)
    return f"{params.prefix}{_encode(salt)}${_encode(key)}"


def verify_password(stored: str, password: str) -> bool:
    parsed = _parse(stored)
    if parsed is None:
        return False
    try:
        key = _derive(password, parsed.salt, parsed.params)
    except (ValueError, OverflowError, TypeError):
        # 저장된 매개변수가 터무니없을 때 `hashlib.scrypt` 가 던지는 셋이다(`exercise.py` 의 raw).
        return False
    return hmac.compare_digest(key, parsed.key)


def needs_rehash(stored: str, params: ScryptParams = CURRENT) -> bool:
    parsed = _parse(stored)
    if parsed is None:
        return True
    old = parsed.params
    return (
        old.log_n < params.log_n
        or old.r < params.r
        or old.p < params.p
        or old.salt_len < params.salt_len
        or old.key_len < params.key_len
    )
