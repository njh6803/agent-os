"""운영자 계정의 이름 규칙과 비밀번호 규칙(`agent_os.http.accounts`, `agent_os.http.passwords`).

명세 admin-login "계정 이름과 비밀번호"의 사례를 함수 단위로 본다. 뒤 티켓의 로그인과 계정 경로가
같은 함수를 쓰므로, 사례의 값이 곧 그 경로들이 받는 값의 경계다.
"""

from __future__ import annotations

import pytest
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from agent_os.http.accounts import fold_account_name, is_account_name
from agent_os.http.passwords import (
    PASSWORD_RULE_TEXT,
    PasswordProblem,
    hash_password,
    needs_rehash,
    normalize_password,
    password_matches,
    password_problem,
)

# --- 계정 이름 -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name",
    ["abc", "a" * 32, "ab1", "0ab", "a.b", "a_b", "a-b", "kim.min-su_01", "1" * 3],
    ids=lambda name: name if len(name) < 10 else f"{len(name)}자",
)
def test_이름_규칙을_맞춘_이름은_받는다(name: str) -> None:
    assert is_account_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "ab",
        "a" * 33,
        "",
        ".abc",
        "_abc",
        "-abc",
        "Abc",
        "ab c",
        "ab\n",
        "abc\n",
        "김민수",
        "abc!",
        "ａｂｃ",
        "abc\x00",
    ],
    ids=[
        "두_자",
        "서른셋",
        "빈_이름",
        "점으로_시작",
        "밑줄로_시작",
        "붙임표로_시작",
        "대문자",
        "공백",
        "개행이_끝에",
        "개행이_끝에_셋",
        "한글",
        "느낌표",
        "전각",
        "널",
    ],
)
def test_이름_규칙을_어긴_이름은_받지_않는다(name: str) -> None:
    assert not is_account_name(name)


@pytest.mark.parametrize(
    ("raw", "folded"),
    [
        ("Kim.Min-Su", "kim.min-su"),
        ("ADMIN", "admin"),
        ("abc", "abc"),
        # 영문 대문자만 소문자로 바꾼다. 전각 대문자와 터키어 İ 는 그대로 둔다
        ("ＡＢＣ", "ＡＢＣ"),
        ("İstanbul", "İstanbul"),
        ("KİM", "kİm"),
    ],
)
def test_들어온_이름은_영문_대문자만_소문자로_바꾼다(raw: str, folded: str) -> None:
    assert fold_account_name(raw) == folded


def test_대문자를_소문자로_바꾼_이름이_규칙에_맞으면_받는다() -> None:
    assert is_account_name(fold_account_name("Password1."))
    assert not is_account_name(fold_account_name("ＡＢＣ"))


# --- 비밀번호 규칙 -------------------------------------------------------------------------------


def test_규칙_문구는_네_조건을_모두_적는다() -> None:
    for part in ("8자 이상", "128자 이하", "대문자", "숫자", "특수문자"):
        assert part in PASSWORD_RULE_TEXT


@pytest.mark.parametrize(
    "password",
    [
        "Abcdef1!",
        "A1" + "a" * 124 + "!!",  # 128자
        "Abcdefg1 ",  # 공백도 특수문자다
        "Abcdefg1한",  # 한글은 특수문자로 센다
        "한글비밀번호A1",  # 한글 여덟 자와 대문자와 숫자: 특수문자는 한글이 맡는다
    ],
    ids=["최소", "백스물여덟", "공백이_특수문자", "한글이_특수문자", "한글_특수문자"],
)
def test_규칙을_맞춘_비밀번호는_문제가_없다(password: str) -> None:
    assert password_problem(password) is None


@pytest.mark.parametrize(
    ("password", "problem"),
    [
        ("Abcde1!", PasswordProblem.LENGTH),  # 7자
        ("A1!" + "a" * 126, PasswordProblem.LENGTH),  # 129자
        ("", PasswordProblem.LENGTH),
        ("abcdefg1!", PasswordProblem.UPPERCASE),
        ("Abcdefgh!", PasswordProblem.DIGIT),
        ("Abcdefg12", PasswordProblem.SPECIAL),
        ("Abcdef1\x00!", PasswordProblem.FORBIDDEN_CHARACTER),  # 널
        ("Abcdef1\t!", PasswordProblem.FORBIDDEN_CHARACTER),  # 탭
        ("Abcdef1\n!", PasswordProblem.FORBIDDEN_CHARACTER),  # 줄바꿈
        ("Abcdef1\x7f!", PasswordProblem.FORBIDDEN_CHARACTER),  # 삭제 문자
        ("Abcdef1\ud800!", PasswordProblem.FORBIDDEN_CHARACTER),  # 짝 없는 서로게이트
    ],
    ids=[
        "일곱_자",
        "백스물아홉",
        "빈_글",
        "대문자_없음",
        "숫자_없음",
        "특수문자_없음",
        "널",
        "탭",
        "줄바꿈",
        "삭제_문자",
        "짝_없는_서로게이트",
    ],
)
def test_규칙을_어긴_비밀번호는_어긴_까닭을_말한다(password: str, problem: PasswordProblem) -> None:
    assert password_problem(password) is problem


def test_자모로_적은_한글은_정규화한_글자_수로_센다() -> None:
    # 자모 셋으로 적은 한글 한 글자는 NFKC 로 한 글자가 된다. 자모 열두 개를 센 글자 수가 아니라
    # 정규화한 글자 수가 길이다
    jamo = "각" * 4  # 정규화하면 "각" 넷
    assert normalize_password(jamo) == "각각각각"
    assert password_problem(jamo + "A") == PasswordProblem.LENGTH
    eight = "각" * 6 + "A1"  # 정규화하면 각 여섯 + A1 = 여덟 자
    assert password_problem(eight) is None
    seven = "각" * 5 + "A1"  # 정규화하면 일곱 자
    assert password_problem(seven) == PasswordProblem.LENGTH


def test_그림_문자_128자는_지나고_129자는_길이에_걸린다() -> None:
    emoji = "😀"  # UTF-8 로 4바이트, UTF-16 으로 두 단위, 코드 포인트는 하나
    assert password_problem("A1" + emoji * 126) is None  # 128자
    assert password_problem("A1" + emoji * 127) == PasswordProblem.LENGTH  # 129자


def test_전각_대문자와_위_첨자_숫자는_정규화한_뒤_대문자와_숫자로_센다() -> None:
    assert normalize_password("Ａ²") == "A2"
    # 전각 Ａ 는 대문자, 위 첨자 ² 는 숫자, 한글은 특수문자
    assert password_problem("Ａbcdef²한") is None
    assert password_problem("abcdefg²한") == PasswordProblem.UPPERCASE
    assert password_problem("Ａbcdefgh한") == PasswordProblem.DIGIT


# --- 해시 ----------------------------------------------------------------------------------------


def test_해시는_Argon2id이고_매개변수가_고정이다() -> None:
    hashed = hash_password("Abcdef1!")
    assert hashed.startswith("$argon2id$v=19$m=19456,t=2,p=1$")


def test_해시는_정규화한_글로_만들어_져_정규화한_글로_견줘진다() -> None:
    hashed = hash_password("Ａbcdef1!")
    PasswordHasher().verify(hashed, "Abcdef1!")
    with pytest.raises(VerifyMismatchError):
        PasswordHasher().verify(hashed, "Ａbcdef1!")


def test_같은_비밀번호도_해시는_매번_다르다() -> None:
    assert hash_password("Abcdef1!") != hash_password("Abcdef1!")


def test_맞는_비밀번호만_저장_값과_맞고_정규화한_글로_견준다() -> None:
    hashed = hash_password("Ａbcdef1!")

    assert password_matches(hashed, "Abcdef1!") is True
    assert password_matches(hashed, "Ａbcdef1!") is True
    assert password_matches(hashed, "Abcdef1?") is False


@pytest.mark.parametrize(
    "stored",
    ["", "not-a-hash", "$argon2id$v=19$m=19456,t=2,p=1$c2FsdA$aGFzaA", "$2b$12$abcdefgh"],
    ids=["빈 값", "해시가 아닌 글", "깨진 Argon2", "다른 해시 형식"],
)
def test_저장_값이_깨졌으면_예외가_아니라_틀림이다(stored: str) -> None:
    assert password_matches(stored, "Abcdef1!") is False


def test_해시가_인코딩하지_못하는_글자가_든_비밀번호는_틀림이다() -> None:
    assert password_matches(hash_password("Abcdef1!"), "Abcdef1!\ud800") is False


def test_고정한_매개변수와_다른_저장_값만_다시_해시가_필요하다() -> None:
    assert needs_rehash(hash_password("Abcdef1!")) is False
    weaker = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1).hash("Abcdef1!")
    assert needs_rehash(weaker) is True
