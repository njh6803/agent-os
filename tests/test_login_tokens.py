"""운영자 로그인의 값 규칙(`agent_os.http.login_tokens`).

잠그는 시간, 유지 시간의 범위와 문구, 짧은 JWT, 쿠키 줄, 접속 주소를 함수 단위로 본다. 이 모듈은
시계도 데이터베이스도 모르므로 시각은 시험이 값으로 넘긴다.
"""

from __future__ import annotations

import base64
import json
import uuid
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from agent_os.http.login_tokens import (
    ACCESS_COOKIE,
    IDLE_MINUTES_ENV,
    REFRESH_COOKIE,
    TOKEN_MINUTES_ENV,
    TOTAL_MINUTES_ENV,
    LoginDurations,
    clearing_cookie_lines,
    cookie_line,
    forwarded_address,
    issue_token,
    lock_duration,
    login_cookie_lines,
    read_login_durations,
    refresh_max_age,
    verify_token,
)

NOW = datetime(2026, 11, 26, 9, 0, tzinfo=UTC)
KEY = b"k" * 32
LOGIN_ID = uuid.UUID("12345678-1234-5678-1234-567812345678")


# --- 잠그는 시간 ---------------------------------------------------------------------------------


@pytest.mark.parametrize("failures", [0, 1, 4])
def test_다섯_번_틀리기_전에는_잠그지_않는다(failures: int) -> None:
    assert lock_duration(failures) is None


@pytest.mark.parametrize(
    ("failures", "minutes"),
    [(5, 1), (6, 2), (7, 4), (8, 8), (9, 16), (10, 32), (11, 60), (12, 60), (500, 60)],
)
def test_다섯째에_1분이고_하나_늘_때마다_두_배이며_한_시간에서_멈춘다(
    failures: int, minutes: int
) -> None:
    assert lock_duration(failures) == timedelta(minutes=minutes)


# --- 유지 시간 -----------------------------------------------------------------------------------


def test_환경_변수가_없거나_비면_기본값이다() -> None:
    expected = LoginDurations(token_minutes=5, idle_minutes=30, total_minutes=480)

    assert read_login_durations({}) == expected
    assert (
        read_login_durations({TOKEN_MINUTES_ENV: "", IDLE_MINUTES_ENV: "", TOTAL_MINUTES_ENV: ""})
        == expected
    )


def test_범위_안의_값은_그대로_받는다() -> None:
    env = {TOKEN_MINUTES_ENV: "15", IDLE_MINUTES_ENV: "1440", TOTAL_MINUTES_ENV: "43200"}

    assert read_login_durations(env) == LoginDurations(15, 1440, 43200)


@pytest.mark.parametrize(
    ("name", "value"),
    [
        (TOKEN_MINUTES_ENV, "0"),
        (TOKEN_MINUTES_ENV, "16"),
        (IDLE_MINUTES_ENV, "4"),
        (IDLE_MINUTES_ENV, "1441"),
        (TOTAL_MINUTES_ENV, "43201"),
        (TOKEN_MINUTES_ENV, "5분"),
        (TOKEN_MINUTES_ENV, " 5"),
        (TOKEN_MINUTES_ENV, "-3"),
        (TOKEN_MINUTES_ENV, "+3"),
        (TOKEN_MINUTES_ENV, "3.5"),
        (TOKEN_MINUTES_ENV, "1" * 40),
    ],
)
def test_범위를_벗어나거나_정수가_아닌_값은_이름과_받은_값을_적은_문구다(
    name: str, value: str
) -> None:
    result = read_login_durations({name: value})

    assert isinstance(result, str)
    assert name in result
    assert repr(value) in result


def test_총_시간은_쉬는_시간_이상이어야_한다() -> None:
    result = read_login_durations({IDLE_MINUTES_ENV: "600", TOTAL_MINUTES_ENV: "599"})

    assert isinstance(result, str)
    assert TOTAL_MINUTES_ENV in result


def test_총_시간이_쉬는_시간과_같으면_받는다() -> None:
    result = read_login_durations({IDLE_MINUTES_ENV: "600", TOTAL_MINUTES_ENV: "600"})

    assert result == LoginDurations(5, 600, 600)


def test_짧은_로그인_증표의_수명이_쉬는_시간_이상이면_둘의_값을_적은_문구다() -> None:
    result = read_login_durations({TOKEN_MINUTES_ENV: "10", IDLE_MINUTES_ENV: "10"})

    assert isinstance(result, str)
    assert TOKEN_MINUTES_ENV in result
    assert IDLE_MINUTES_ENV in result
    assert "10분" in result


def test_틀린_값이_여럿이면_한_번에_모두_알린다() -> None:
    result = read_login_durations({TOKEN_MINUTES_ENV: "99", IDLE_MINUTES_ENV: "1"})

    assert isinstance(result, str)
    assert TOKEN_MINUTES_ENV in result
    assert IDLE_MINUTES_ENV in result


# --- 짧은 JWT ------------------------------------------------------------------------------------


def _issue(*, tier: str = "admin", minutes: int = 5, key: bytes = KEY, at: datetime = NOW) -> str:
    assert tier in ("admin", "system_admin")
    return issue_token(
        key,
        name="kim.min",
        login_id=LOGIN_ID,
        tier="admin" if tier == "admin" else "system_admin",
        now=at,
        token_minutes=minutes,
    )


def test_발급한_증표는_같은_키로_검증되고_칸_다섯이_그대로_돌아온다() -> None:
    claims = verify_token(_issue(), KEY, NOW)

    assert claims is not None
    assert (claims.name, claims.login_id, claims.tier) == ("kim.min", LOGIN_ID, "admin")
    assert claims.expires_at == int(NOW.timestamp()) + 300


def test_시스템_관리자_단계도_그대로_돌아온다() -> None:
    claims = verify_token(_issue(tier="system_admin"), KEY, NOW)

    assert claims is not None
    assert claims.tier == "system_admin"


def test_만료_한_초_전까지는_통하고_만료와_같은_초부터는_통하지_않는다() -> None:
    token = _issue(minutes=5)
    expires = NOW + timedelta(minutes=5)

    assert verify_token(token, KEY, expires - timedelta(seconds=1)) is not None
    assert verify_token(token, KEY, expires) is None
    assert verify_token(token, KEY, expires + timedelta(seconds=1)) is None


def test_다른_키로_서명한_증표는_통하지_않는다() -> None:
    assert verify_token(_issue(key=b"x" * 32), KEY, NOW) is None


def test_서명을_바꾼_증표는_통하지_않는다() -> None:
    token = _issue()
    head, body, signature = token.split(".")
    flipped = signature[:-2] + ("AA" if signature[-2:] != "AA" else "BB")

    assert verify_token(f"{head}.{body}.{flipped}", KEY, NOW) is None


def test_서명하지_않은_증표는_통하지_않는다() -> None:
    def part(value: Mapping[str, object]) -> str:
        raw = json.dumps(value).encode()
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    claims = {"sub": "kim.min", "sid": str(LOGIN_ID), "tier": "admin", "iat": 1, "exp": 2**40}
    token = f"{part({'alg': 'none', 'typ': 'JWT'})}.{part(claims)}."

    assert verify_token(token, KEY, NOW) is None


def test_사이트가_쓰는_RS256_증표는_통하지_않는다() -> None:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    issued = int(NOW.timestamp())
    claims = {
        "sub": "kim.min",
        "sid": str(LOGIN_ID),
        "tier": "admin",
        "iat": issued,
        "exp": issued + 300,
    }
    token = jwt.encode(claims, private, algorithm="RS256")

    assert verify_token(token, KEY, NOW) is None


@pytest.mark.parametrize("missing", ["sub", "sid", "tier", "iat", "exp"])
def test_칸_다섯_가운데_하나라도_없으면_통하지_않는다(missing: str) -> None:
    issued = int(NOW.timestamp())
    claims: dict[str, object] = {
        "sub": "kim.min",
        "sid": str(LOGIN_ID),
        "tier": "admin",
        "iat": issued,
        "exp": issued + 300,
    }
    del claims[missing]

    assert verify_token(jwt.encode(claims, KEY, algorithm="HS256"), KEY, NOW) is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sub", ""),
        ("sub", 7),
        ("sid", "not-a-uuid"),
        ("sid", 7),
        ("tier", "owner"),
        ("tier", None),
        ("iat", "1"),
        ("iat", True),
        ("exp", True),
        ("exp", "9999999999"),
    ],
)
def test_칸의_값이_모양에_맞지_않으면_통하지_않는다(field: str, value: object) -> None:
    issued = int(NOW.timestamp())
    claims: dict[str, object] = {
        "sub": "kim.min",
        "sid": str(LOGIN_ID),
        "tier": "admin",
        "iat": issued,
        "exp": issued + 300,
    }
    claims[field] = value

    assert verify_token(jwt.encode(claims, KEY, algorithm="HS256"), KEY, NOW) is None


@pytest.mark.parametrize("garbage", ["", "abc", "a.b.c", "....", "한글.한글.한글"])
def test_증표가_아닌_글은_예외가_아니라_통하지_않음이다(garbage: str) -> None:
    assert verify_token(garbage, KEY, NOW) is None


# --- 쿠키 줄 -------------------------------------------------------------------------------------


def test_로그인이_심는_쿠키는_이름이_Host_접두이고_속성이_같다() -> None:
    access, refresh = login_cookie_lines("AAA", "RRR", refresh_max_age=1800)

    assert access == f"{ACCESS_COOKIE}=AAA; HttpOnly; Secure; SameSite=Strict; Path=/"
    expected_refresh = f"{REFRESH_COOKIE}=RRR; HttpOnly; Secure; SameSite=Strict; Path=/"
    assert refresh == f"{expected_refresh}; Max-Age=1800"
    assert access.startswith("__Host-")
    assert refresh.startswith("__Host-")
    assert "Domain" not in access + refresh


def test_짧은_증표_쿠키에는_Max_Age가_없다() -> None:
    access, _ = login_cookie_lines("AAA", "RRR", refresh_max_age=60)

    assert "Max-Age" not in access


def test_지우는_줄은_빈_값과_Max_Age_0이고_나머지_속성은_심을_때와_같다() -> None:
    access, refresh = clearing_cookie_lines()

    assert access == f"{ACCESS_COOKIE}=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0"
    assert refresh == f"{REFRESH_COOKIE}=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0"


def test_쿠키_줄_하나는_값과_Max_Age를_속성_앞뒤에_붙인다() -> None:
    assert cookie_line("a", "b") == "a=b; HttpOnly; Secure; SameSite=Strict; Path=/"
    assert cookie_line("a", "b", max_age=3).endswith("; Max-Age=3")


def test_갱신용_쿠키의_Max_Age는_쉬는_시간과_총_시간의_남은_몫_가운데_짧은_것이다() -> None:
    durations = LoginDurations(token_minutes=5, idle_minutes=30, total_minutes=60)

    fresh = refresh_max_age(durations, logged_in_at=NOW, now=NOW)
    late = refresh_max_age(durations, logged_in_at=NOW, now=NOW + timedelta(minutes=50))
    over = refresh_max_age(durations, logged_in_at=NOW, now=NOW + timedelta(minutes=70))

    assert fresh == 30 * 60
    assert late == 10 * 60
    assert over == 0


# --- 접속 주소 -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("values", "expected"),
    [
        (["203.0.113.7"], "203.0.113.7"),
        ([" 203.0.113.7 "], "203.0.113.7"),
        (["2001:db8::1"], "2001:db8::1"),
        ([], None),
        (["203.0.113.7", "198.51.100.1"], None),
        (["203.0.113.7, 198.51.100.1"], None),
        (["not-an-ip"], None),
        ([""], None),
        (["203.0.113.7:8080"], None),
    ],
    ids=["IPv4", "공백", "IPv6", "머리 없음", "머리 둘", "쉼표", "IP 아님", "빈 값", "포트"],
)
def test_접속_주소는_머리가_하나이고_IP로_읽힐_때만_남긴다(
    values: list[str], expected: str | None
) -> None:
    assert forwarded_address(values) == expected
