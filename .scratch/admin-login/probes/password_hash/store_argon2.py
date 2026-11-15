"""후보 2. `argon2-cffi` 의 Argon2id 로 비밀번호를 저장하는 작은 모듈.

재는 대상이다(pyright strict 와 타입 우회 검사, `run.py` 의 `types`). 제품 코드가 아니다. 하는 일은
`store_scrypt.py` 와 같은 셋이고, 셋 다 `argon2.PasswordHasher` 의 메서드를 그대로 부른다. 저장 꼴
(`$argon2id$v=19$m=19456,t=2,p=1$<소금>$<해시>`)은 라이브러리가 만들고 읽는다.

`verify` 는 맞으면 `True` 를 돌려주고 틀리면 예외를 던진다. 여기서는 그 문서가 적은 예외 셋
(`VerifyMismatchError` 와 그 부모 `VerificationError`, `InvalidHashError`)만 잡는다. 그 밖의 예외가
새는 입력이 있는지는 `exercise.py` 가 본다. `check_needs_rehash` 는 약한지가 아니라 지금 설정과
다른지를 본다(`exercise.py` 가 더 센 매개변수의 문자열로 그 갈래를 본다).
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

# OWASP Password Storage Cheat Sheet 의 요약 줄(19 MiB, 반복 2, 병렬 1).
CURRENT = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)


def prefix_of(hasher: PasswordHasher) -> str:
    cost = f"m={hasher.memory_cost},t={hasher.time_cost},p={hasher.parallelism}"
    return f"$argon2id$v=19${cost}$"


def hash_password(password: str, hasher: PasswordHasher = CURRENT) -> str:
    return hasher.hash(password)


def verify_password(stored: str, password: str, hasher: PasswordHasher = CURRENT) -> bool:
    try:
        return hasher.verify(stored, password)
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(stored: str, hasher: PasswordHasher = CURRENT) -> bool:
    try:
        return hasher.check_needs_rehash(stored)
    except InvalidHashError:
        return True
