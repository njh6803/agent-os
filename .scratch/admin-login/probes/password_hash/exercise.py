"""후보 모듈 둘의 세 동작을 한 바퀴 돌고 `RESULT <json>` 줄로 낸다. 셈은 `run.py` 가 한다.

후보마다 한 줄이다. 지금 설정으로 만든 문자열, 더 약한 설정으로 만든 문자열, 더 센 설정으로 만든
문자열에 견줌과 다시 해시 판정을 걸고, 깨진 저장 문자열 몇 개에 두 함수가 무엇을 돌려주는지(예외가
새면 그 이름)를 적는다. 끝의 `raw` 줄은 모듈을 거치지 않고 `hashlib.scrypt` 를 터무니없는 매개변수로
바로 불러 그것이 던지는 예외의 종류를 적는다. `store_scrypt.py` 가 잡는 예외 셋의 근거다.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass

import store_argon2
import store_scrypt
from argon2 import PasswordHasher
from rows import PASSWORD, WRONG
from store_scrypt import ScryptParams

SALT = "c2FsdC1vZi0xNi1ieXRlcw"
KEY = "a2V5LW9mLTMyLWJ5dGVzLWtleS1vZi0zMi1ieXRlcyE"


@dataclass(frozen=True)
class Candidate:
    name: str
    prefixes: tuple[str, str, str]
    makers: tuple[Callable[[], str], Callable[[], str], Callable[[], str]]
    verify: Callable[[str, str], bool]
    needs_rehash: Callable[[str], bool]
    broken: dict[str, str]


def scrypt_candidate() -> Candidate:
    current = store_scrypt.CURRENT
    weaker = ScryptParams(log_n=14, r=8, p=1)
    stronger = ScryptParams(log_n=18, r=8, p=1)
    return Candidate(
        "scrypt",
        (current.prefix, weaker.prefix, stronger.prefix),
        (
            lambda: store_scrypt.hash_password(PASSWORD),
            lambda: store_scrypt.hash_password(PASSWORD, weaker),
            lambda: store_scrypt.hash_password(PASSWORD, stronger),
        ),
        store_scrypt.verify_password,
        store_scrypt.needs_rehash,
        {
            "빈 문자열": "",
            "꼴이 아닌 글": "plain-text",
            "다른 알고리즘의 문자열": f"$argon2id$v=19$m=19456,t=2,p=1${SALT}${KEY}",
            "칸이 모자란 문자열": f"$scrypt$ln=17,r=8,p=1${SALT}",
            "ASCII 가 아닌 글자": "$scrypt$ln=17,r=8,p=1$한글$한글",
            "수가 아닌 매개변수": f"$scrypt$ln=x,r=8,p=1${SALT}${KEY}",
            "0 인 매개변수": f"$scrypt$ln=17,r=0,p=1${SALT}${KEY}",
            "터무니없이 큰 매개변수": f"$scrypt$ln=100,r=8,p=1${SALT}${KEY}",
            "메모리 한도를 넘는 매개변수": f"$scrypt$ln=21,r=8,p=1${SALT}${KEY}",
        },
    )


def argon2_candidate() -> Candidate:
    current = store_argon2.CURRENT
    weaker = PasswordHasher(time_cost=1, memory_cost=7168, parallelism=1)
    stronger = PasswordHasher(time_cost=3, memory_cost=47104, parallelism=1)
    return Candidate(
        "argon2",
        (
            store_argon2.prefix_of(current),
            store_argon2.prefix_of(weaker),
            store_argon2.prefix_of(stronger),
        ),
        (
            lambda: store_argon2.hash_password(PASSWORD),
            lambda: store_argon2.hash_password(PASSWORD, weaker),
            lambda: store_argon2.hash_password(PASSWORD, stronger),
        ),
        store_argon2.verify_password,
        store_argon2.needs_rehash,
        {
            "빈 문자열": "",
            "꼴이 아닌 글": "plain-text",
            "다른 알고리즘의 문자열": f"$scrypt$ln=17,r=8,p=1${SALT}${KEY}",
            "칸이 모자란 문자열": f"$argon2id$v=19$m=19456,t=2,p=1${SALT}",
            "ASCII 가 아닌 글자": "$argon2id$v=19$m=19456,t=2,p=1$한글$한글",
            "수가 아닌 매개변수": f"$argon2id$v=19$m=x,t=2,p=1${SALT}${KEY}",
            "0 인 매개변수": f"$argon2id$v=19$m=0,t=2,p=1${SALT}${KEY}",
            "터무니없이 큰 매개변수": f"$argon2id$v=19$m={2**40},t=2,p=1${SALT}${KEY}",
        },
    )


def outcome(call: Callable[[], bool]) -> str:
    try:
        return str(call())
    except Exception as error:  # 새는 예외의 이름이 결과다
        return f"예외 {type(error).__name__}"


def describe(candidate: Candidate) -> dict[str, object]:
    current, weaker, stronger = (make() for make in candidate.makers)
    verify, needs_rehash = candidate.verify, candidate.needs_rehash
    prefixes_ok = [
        text.startswith(prefix)
        for text, prefix in zip((current, weaker, stronger), candidate.prefixes, strict=True)
    ]
    return {
        "candidate": candidate.name,
        "prefixes": list(candidate.prefixes),
        "prefixes_ok": prefixes_ok,
        "stored_len": len(current),
        "salts_differ": current != candidate.makers[0](),
        "current": [verify(current, PASSWORD), verify(current, WRONG), needs_rehash(current)],
        "weaker": [verify(weaker, PASSWORD), verify(weaker, WRONG), needs_rehash(weaker)],
        "stronger": [verify(stronger, PASSWORD), verify(stronger, WRONG), needs_rehash(stronger)],
        "broken": {
            label: [
                outcome(lambda text=text: verify(text, PASSWORD)),
                outcome(lambda text=text: needs_rehash(text)),
            ]
            for label, text in candidate.broken.items()
        },
    }


def raw_scrypt() -> dict[str, object]:
    cases = {
        "n=2^100": {"n": 1 << 100, "r": 8, "p": 1},
        "r=0": {"n": 1 << 17, "r": 0, "p": 1, "maxmem": 1 << 28},
        "n=2^21,maxmem=128·r·(N+p+2)": {"n": 1 << 21, "r": 8, "p": 1, "maxmem": 1024 * (2**21 + 3)},
        "n=3": {"n": 3, "r": 8, "p": 1},
    }
    raised: dict[str, str] = {}
    for label, kwargs in cases.items():
        try:
            hashlib.scrypt(b"sample", salt=b"salt-of-16-bytes", dklen=32, **kwargs)
        except Exception as error:  # 던지는 예외의 종류와 문구가 결과다
            raised[label] = f"{type(error).__name__}: {error}"
        else:
            raised[label] = "예외 없음"
    return {"raw": "hashlib.scrypt", "raised": raised}


def main() -> int:
    for candidate in (scrypt_candidate(), argon2_candidate()):
        print(f"RESULT {json.dumps(describe(candidate), ensure_ascii=False)}", flush=True)
    print(f"RESULT {json.dumps(raw_scrypt(), ensure_ascii=False)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
