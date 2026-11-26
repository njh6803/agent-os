"""운영자 로그인의 값 모양: 유지 시간, 잠그는 시간, 짧은 JWT, 쿠키 줄, 접속 주소(ADR 0062).

이 모듈은 규칙만 갖고 데이터베이스도 시계도 모른다. 시각은 부르는 쪽이 주입된 시계에서 읽어
넘긴다. 그래서 시험이 가짜 시계로 만료와 잠금 시간을 움직인다.

**짧은 JWT.** 서명은 HS256 하나이고 칸 다섯(`sub`, `sid`, `tier`, `iat`, `exp`)이 모두 있어야
한다. 사이트가 서명한 토큰(`agent_os.http.sites`, RS256 하나)과 같은 라이브러리를 쓰되 알고리즘
목록이 서로 달라 한쪽의 토큰이 다른 쪽을 지나지 않는다. 시간은 라이브러리가 아니라 이 모듈이
넘겨받은 시각으로 센다(PyJWT 의 `decode` 에는 시각을 넣을 자리가 없다). 만료에 여유를 두지
않는다. 검증은 데이터베이스를 읽지 않는다. 로그인을 끊어도 이미 받은 짧은 JWT 는 수명이 끝날
때까지 통하는 것이 이 선택의 값이다(명세 admin-login "로그인을 끊는 일").

**쿠키 줄.** 속성은 심을 때와 지울 때가 같고(`HttpOnly; Secure; SameSite=Strict; Path=/`), 이름이
`__Host-` 로 시작해 브라우저가 `Secure` 와 `Path=/` 와 `Domain` 없음을 강제한다.
"""

from __future__ import annotations

import ipaddress
import re
import uuid
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta

import jwt

from agent_os.http.accounts import Tier

ACCESS_COOKIE = "__Host-aos_at"
REFRESH_COOKIE = "__Host-aos_rt"

TOKEN_MINUTES_ENV = "AGENT_OS_LOGIN_TOKEN_MINUTES"
IDLE_MINUTES_ENV = "AGENT_OS_LOGIN_IDLE_MINUTES"
TOTAL_MINUTES_ENV = "AGENT_OS_LOGIN_TOTAL_MINUTES"

# 유지 시간의 범위와 기본값(분). 표는 명세 admin-login "유지 시간"이다.
TOKEN_MINUTES_RANGE = (1, 15)
IDLE_MINUTES_RANGE = (5, 1440)
TOTAL_MINUTES_MAX = 43200
DEFAULT_TOKEN_MINUTES = 5
DEFAULT_IDLE_MINUTES = 30
DEFAULT_TOTAL_MINUTES = 480

# 틀린 횟수가 이 수에 닿는 시도가 계정을 잠근다
LOCK_AFTER_FAILURES = 5
LOCK_MINUTES_CAP = 60
# 서명 키를 메모리에 두고 다시 읽기까지의 시간
SIGNING_KEY_REREAD = timedelta(seconds=10)

ALGORITHM = "HS256"
_REQUIRED_CLAIMS = ("sub", "sid", "tier", "iat", "exp")
_ATTRIBUTES = "HttpOnly; Secure; SameSite=Strict; Path=/"
_DIGITS = re.compile(r"[0-9]{1,9}")


@dataclass(frozen=True)
class LoginDurations:
    """로그인이 유지되는 시간 셋(분). 짧은 JWT 의 수명, 쉬는 시간, 총 시간이다."""

    token_minutes: int = DEFAULT_TOKEN_MINUTES
    idle_minutes: int = DEFAULT_IDLE_MINUTES
    total_minutes: int = DEFAULT_TOTAL_MINUTES


def read_login_durations(env: Mapping[str, str]) -> LoginDurations | str:
    """환경 변수 셋을 읽는다. 맞으면 값이고 어기면 변수 이름과 받은 값과 범위를 적은 문구다.

    빈 값은 변수가 없는 것과 같이 기본값이고 기본값도 같은 범위를 지난다(compose 의 `${…:-}` 꼴이
    빈 값을 넘긴다). 값은
    앞뒤에 공백이 없는 십진 정수만 받는다. 받은 값은 비밀이 아니라 문구에 싣는다. 짧은 JWT 의 수명은
    쉬는 시간보다 짧아야 한다 — 화면은 요청이 401 을 받은 뒤에야 갱신하므로 수명이 쉬는 시간
    이상이면 쉬지 않고 쓰는 사람도 처음 갱신하려는 때 이미 쉬는 시간이 지나 로그인이 끝난다.
    """
    problems: list[str] = []
    token = _read(env, TOKEN_MINUTES_ENV, DEFAULT_TOKEN_MINUTES, TOKEN_MINUTES_RANGE, problems)
    idle = _read(env, IDLE_MINUTES_ENV, DEFAULT_IDLE_MINUTES, IDLE_MINUTES_RANGE, problems)
    # 쉬는 시간이 틀렸으면 총 시간의 아래 한계는 쉬는 시간의 최솟값으로 본다
    floor = idle if idle is not None else IDLE_MINUTES_RANGE[0]
    total = _read(
        env, TOTAL_MINUTES_ENV, DEFAULT_TOTAL_MINUTES, (floor, TOTAL_MINUTES_MAX), problems
    )
    if token is not None and idle is not None and token >= idle:
        problems.append(
            f"{TOKEN_MINUTES_ENV} 의 값({token}분)은 {IDLE_MINUTES_ENV} 의 값({idle}분)보다"
            " 작아야 합니다. 짧은 로그인 증표의 수명이 쉬는 시간 이상이면 쉬지 않고 쓰는 사람도"
            " 로그인이 끝납니다."
        )
    if problems or token is None or idle is None or total is None:
        return "\n".join(problems)
    return LoginDurations(token_minutes=token, idle_minutes=idle, total_minutes=total)


def _read(
    env: Mapping[str, str],
    name: str,
    default: int,
    allowed: tuple[int, int],
    problems: list[str],
) -> int | None:
    raw = env.get(name, "")
    low, high = allowed
    # 비운 값은 기본값을 쓰되 기본값도 같은 범위를 지난다. 쉬는 시간을 늘리면 총 시간의 아래 한계가
    # 기본값을 넘어설 수 있고, 그때 기본값을 그대로 받으면 로그인이 쉬는 시간보다 먼저 끝난다
    if raw == "":
        value: int | None = default
    else:
        value = int(raw) if _DIGITS.fullmatch(raw) else None
    if value is None or not low <= value <= high:
        problems.append(
            f"{name} 의 값은 {low}분 이상 {high}분 이하의 정수여야 합니다. 받은 값: {raw!r}"
        )
        return None
    return value


def lock_duration(failures: int) -> timedelta | None:
    """연속 틀린 횟수에 걸리는 잠금의 길이. 다섯째에 1분이고 하나 늘 때마다 두 배, 1시간에서 멈춘다.

    다섯 번째 전이면 잠그지 않는다. 지수를 6에서 자르는 것은 큰 횟수가 거대한 정수를 만들지
    않게 하려는 것이다(2의 6제곱은 이미 상한을 넘는다).
    """
    if failures < LOCK_AFTER_FAILURES:
        return None
    minutes = min(LOCK_MINUTES_CAP, 2 ** min(failures - LOCK_AFTER_FAILURES, 6))
    return timedelta(minutes=minutes)


@dataclass(frozen=True)
class LoginClaims:
    """짧은 JWT 가 실은 것. 계정 이름과 로그인 한 건과 단계와 만료 시각이다."""

    name: str
    login_id: uuid.UUID
    tier: Tier
    expires_at: int


def issue_token(
    key: bytes, *, name: str, login_id: uuid.UUID, tier: Tier, now: datetime, token_minutes: int
) -> str:
    """짧은 JWT 하나를 서명해 낸다. 만든 시각과 만료는 정수 초다."""
    issued = int(now.timestamp())
    claims = {
        "sub": name,
        "sid": str(login_id),
        "tier": tier,
        "iat": issued,
        "exp": issued + token_minutes * 60,
    }
    return jwt.encode(claims, key, algorithm=ALGORITHM)


def verify_token(token: str, key: bytes, now: datetime) -> LoginClaims | None:
    """짧은 JWT 를 검증한다. 어느 단계든 실패는 `None` 하나다(원인은 부르는 쪽이 모른다).

    서명과 칸 다섯은 라이브러리가, 만료는 넘겨받은 시각이 본다. 만료에 여유를 두지 않아 `exp` 와
    같은 초부터 만료다.
    """
    try:
        decoded = jwt.decode(
            token,
            key,
            algorithms=[ALGORITHM],
            options={
                "require": list(_REQUIRED_CLAIMS),
                "verify_exp": False,
                "verify_iat": False,
                "verify_nbf": False,
            },
        )
    except jwt.PyJWTError:
        return None
    name = decoded.get("sub")
    sid = decoded.get("sid")
    tier = decoded.get("tier")
    issued = decoded.get("iat")
    expires = decoded.get("exp")
    if not isinstance(name, str) or not name or not isinstance(sid, str):
        return None
    if isinstance(issued, bool) or not isinstance(issued, int):
        return None
    if isinstance(expires, bool) or not isinstance(expires, int):
        return None
    if expires <= now.timestamp():
        return None
    try:
        login_id = uuid.UUID(sid)
    except ValueError:
        return None
    if tier == "system_admin":
        return LoginClaims(name, login_id, "system_admin", expires)
    if tier == "admin":
        return LoginClaims(name, login_id, "admin", expires)
    return None


def cookie_line(name: str, value: str, *, max_age: int | None = None) -> str:
    """`Set-Cookie` 머리 하나의 값. 속성은 심을 때와 지울 때가 같다."""
    suffix = "" if max_age is None else f"; Max-Age={max_age}"
    return f"{name}={value}; {_ATTRIBUTES}{suffix}"


def login_cookie_lines(access_token: str, refresh_token: str, *, refresh_max_age: int) -> list[str]:
    """로그인이 심는 쿠키 줄 둘. 짧은 JWT 에는 `Max-Age` 가 없다(브라우저를 닫으면 사라진다)."""
    return [
        cookie_line(ACCESS_COOKIE, access_token),
        cookie_line(REFRESH_COOKIE, refresh_token, max_age=refresh_max_age),
    ]


def clearing_cookie_lines() -> list[str]:
    """쿠키를 지우는 줄 둘. 같은 이름에 빈 값과 `Max-Age=0` 을 붙이고 나머지 속성은 그대로다."""
    return [
        cookie_line(ACCESS_COOKIE, "", max_age=0),
        cookie_line(REFRESH_COOKIE, "", max_age=0),
    ]


def refresh_max_age(durations: LoginDurations, *, logged_in_at: datetime, now: datetime) -> int:
    """갱신용 번호 쿠키의 `Max-Age`(초). 쉬는 시간과 총 시간의 남은 몫 가운데 짧은 것이다."""
    total_left = durations.total_minutes * 60 - (now - logged_in_at).total_seconds()
    return max(0, int(min(durations.idle_minutes * 60, total_left)))


def forwarded_address(values: Sequence[str]) -> str | None:
    """`X-Forwarded-For` 머리에서 남길 접속 주소. 값이 꼭 하나이고 IP 주소로 읽힐 때만 그 주소다.

    머리가 여럿이거나 한 머리에 쉼표로 이은 값이 둘 이상이면 비운다. 앞에 선 nginx 가 받은 값을
    덮어쓴 하나의 주소만 믿을 수 있기 때문이다(명세 "로그인 기록"의 "접속한 주소").
    """
    if len(values) != 1:
        return None
    text = values[0].strip()
    if not text or "," in text:
        return None
    try:
        return str(ipaddress.ip_address(text))
    except ValueError:
        return None
