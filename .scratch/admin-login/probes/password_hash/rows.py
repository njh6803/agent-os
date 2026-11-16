"""재는 매개변수의 줄과, 줄 하나로 후보 모듈을 부르는 도우미. 측정 스크립트들이 함께 쓴다.

줄은 OWASP Password Storage Cheat Sheet 의 사본에서 읽어 옮겼다. 사본은
`https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html` 을 2026-11-14 에
내려받아 글자만 남긴 것(`pwstore.html.txt`)이고, `source` 의 줄 번호는 그 사본의 줄이다. 요약 줄
(210·211 줄)이 든 조합이 `headline` 이다. Argon2 의 마지막 줄은 권고가 아니라 `argon2-cffi` 가 인자
없이 쓰는 기본값(`argon2/profiles.py` 의 `RFC_9106_LOW_MEMORY`)이다.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import store_argon2
import store_scrypt
from argon2 import PasswordHasher
from store_scrypt import ScryptParams

PASSWORD = "correct horse battery staple"
WRONG = "correct horse battery stapler"
MIB = 1024 * 1024


@dataclass(frozen=True)
class Row:
    candidate: str
    label: str
    source: str
    numbers: tuple[int, int, int]
    headline: bool = False

    @property
    def key(self) -> str:
        return f"{self.candidate} {self.label}"

    @property
    def nominal_bytes(self) -> int:
        """그 줄이 적은 메모리. scrypt 는 128·r·N 바이트, Argon2 는 m KiB 다."""
        first, second, _ = self.numbers
        return 128 * second * (1 << first) if self.candidate == "scrypt" else first * 1024


# scrypt 의 numbers 는 (log2 N, r, p), Argon2 의 numbers 는 (m KiB, t, p) 다.
ROWS = (
    Row("scrypt", "N=2^17,r=8,p=1", "사본 211·276 줄", (17, 8, 1), headline=True),
    Row("scrypt", "N=2^16,r=8,p=2", "사본 277 줄", (16, 8, 2)),
    Row("scrypt", "N=2^15,r=8,p=3", "사본 278 줄", (15, 8, 3)),
    Row("scrypt", "N=2^14,r=8,p=5", "사본 279 줄", (14, 8, 5)),
    Row("scrypt", "N=2^13,r=8,p=10", "사본 280 줄", (13, 8, 10)),
    Row("argon2", "m=19456,t=2,p=1", "사본 210·268 줄", (19456, 2, 1), headline=True),
    Row("argon2", "m=47104,t=1,p=1", "사본 267 줄", (47104, 1, 1)),
    Row("argon2", "m=12288,t=3,p=1", "사본 269 줄", (12288, 3, 1)),
    Row("argon2", "m=9216,t=4,p=1", "사본 270 줄", (9216, 4, 1)),
    Row("argon2", "m=7168,t=5,p=1", "사본 271 줄", (7168, 5, 1)),
    Row("argon2", "m=65536,t=3,p=4", "argon2-cffi 기본값", (65536, 3, 4)),
)


@dataclass(frozen=True)
class Bound:
    """줄 하나에 묶은 후보 모듈의 두 동작과, 그 줄로 만든 문자열이 가져야 하는 머리."""

    row: Row
    prefix: str
    hash_password: Callable[[str], str]
    verify_password: Callable[[str, str], bool]

    def round_trip(self) -> tuple[str, bool]:
        """한 번 해시하고 맞는 비밀번호와 틀린 비밀번호로 견준다. (문자열, 표지)를 돌려준다."""
        stored = self.hash_password(PASSWORD)
        return stored, self.genuine(stored)

    def genuine(self, stored: str) -> bool:
        """이 줄의 매개변수로 실제로 해시했다는 표지. 머리가 맞고 견줌이 맞는 쪽만 통과한다."""
        right = self.verify_password(stored, PASSWORD)
        wrong = self.verify_password(stored, WRONG)
        return stored.startswith(self.prefix) and right and not wrong


def bind(row: Row) -> Bound:
    first, second, third = row.numbers
    if row.candidate == "scrypt":
        params = ScryptParams(log_n=first, r=second, p=third)
        return Bound(
            row,
            params.prefix,
            lambda password: store_scrypt.hash_password(password, params),
            store_scrypt.verify_password,
        )
    hasher = PasswordHasher(memory_cost=first, time_cost=second, parallelism=third)
    return Bound(
        row,
        store_argon2.prefix_of(hasher),
        lambda password: store_argon2.hash_password(password, hasher),
        lambda stored, password: store_argon2.verify_password(stored, password, hasher),
    )


def headline(candidate: str) -> Row:
    return next(row for row in ROWS if row.candidate == candidate and row.headline)


def find(key: str) -> Row:
    return next(row for row in ROWS if row.key == key)
