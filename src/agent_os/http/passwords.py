"""운영자 계정의 비밀번호 규칙과 해시(ADR 0062 결정 "비밀번호 규칙"과 "비밀번호 저장").

규칙을 유니코드 글에 대는 법은 명세 admin-login "계정 이름과 비밀번호"가 정한다.

- 받은 비밀번호를 NFKC로 정규화한 뒤 규칙에 대고 해시를 만든다. 로그인도 같은 정규화를 한 글로
  견주므로, 한쪽에서만 하면 같은 글을 친 사람이 걸린다.
- 글자 수는 정규화한 뒤의 코드 포인트로 센다. 자모 셋으로 적은 한글 한 글자는 정규화로 한 글자가
  된다.
- 글자 종류는 ASCII로 읽는다. 영문자도 숫자도 아닌 글자(한글, 공백 포함)는 특수문자다.
- 제어 문자(유니코드 범주 Cc)와 짝 없는 서로게이트(범주 Cs)가 든 글은 받지 않는다.

몸통의 상한(정규화하기 전 1~1024자)은 비밀번호를 받는 경로의 몫이고 여기서 보지 않는다.

해시는 `argon2-cffi`의 Argon2id이고 매개변수 m=19456, t=2, p=1을 코드에 고정한다. 매개변수가 다르게
만든 가짜 저장 값은 견줌 시간이 +274ms 달랐다(프로브 `.scratch/admin-login/probes/hash_load/`의 결과
6이 쟀다). 그래서 저장 값은 모두 이 한 벌의 매개변수로 만든다.
이 모듈은 이벤트 루프를 막지 않으려는 스레드 넘기기를 하지 않는다. 부르는 쪽이 정한다.
"""

from __future__ import annotations

import enum
import unicodedata

from argon2 import PasswordHasher

MIN_LENGTH = 8
MAX_LENGTH = 128

# 사람이 읽는 규칙 문구. 서버 명령과 뒤 티켓의 422 문구가 같은 글을 쓴다.
PASSWORD_RULE_TEXT = (
    f"비밀번호는 {MIN_LENGTH}자 이상 {MAX_LENGTH}자 이하이고 영문 대문자, 숫자, 특수문자"
    "(영문자와 숫자가 아닌 글자)가 각각 1자 이상이어야 합니다. 제어 문자는 쓸 수 없습니다."
)

# OWASP Password Storage Cheat Sheet 의 권고 줄(ADR 0062). 코드에 고정하고 설정으로 받지 않는다.
_HASHER = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)


class PasswordProblem(enum.Enum):
    """비밀번호가 규칙을 어긴 까닭. 어긴 것이 여럿이면 아래 차례의 첫째다."""

    FORBIDDEN_CHARACTER = "forbidden_character"
    LENGTH = "length"
    UPPERCASE = "uppercase"
    DIGIT = "digit"
    SPECIAL = "special"


def normalize_password(password: str) -> str:
    """규칙과 해시가 보는 글. 모양이 다르게 적힌 같은 글자를 한 모양으로 맞춘다."""
    return unicodedata.normalize("NFKC", password)


def password_problem(password: str) -> PasswordProblem | None:
    """비밀번호가 규칙을 어긴 까닭. 맞으면 `None`. 받은 글을 정규화한 뒤에 본다."""
    normalized = normalize_password(password)
    if any(unicodedata.category(char) in ("Cc", "Cs") for char in normalized):
        return PasswordProblem.FORBIDDEN_CHARACTER
    if not MIN_LENGTH <= len(normalized) <= MAX_LENGTH:
        return PasswordProblem.LENGTH
    if not any("A" <= char <= "Z" for char in normalized):
        return PasswordProblem.UPPERCASE
    if not any("0" <= char <= "9" for char in normalized):
        return PasswordProblem.DIGIT
    if all(_is_ascii_alphanumeric(char) for char in normalized):
        return PasswordProblem.SPECIAL
    return None


def hash_password(password: str) -> str:
    """정규화한 글로 만든 Argon2id 저장 값. 규칙은 부르는 쪽이 먼저 `password_problem`으로 본다.

    짝 없는 서로게이트가 든 글은 해시에서 `UnicodeEncodeError`로 끝나므로 규칙이 먼저 걸러야 한다.
    """
    return _HASHER.hash(normalize_password(password))


def _is_ascii_alphanumeric(char: str) -> bool:
    return "A" <= char <= "Z" or "a" <= char <= "z" or "0" <= char <= "9"
