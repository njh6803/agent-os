"""최종 사용자 면의 서명 토큰. 사이트 목록의 타입과 토큰 하나의 검증이 여기 있다(ADR 0023).

사이트는 위젯을 넣은 바깥 서비스이고, 그 백엔드가 RS256 으로 서명한 짧은 JWT 가 최종 사용자의
신원을 보증한다. 서버는 공개 키만 들어 토큰을 만들 수 없다. 사이트 목록은 운영자가 사이트 파일에
적은 것이고 `main.py` 가 TOML 을 읽어 이 타입으로 만든다 — 이 층은 TOML 을 모르고, 파일의 키
이름과 손상 판정은 그쪽이 소유한다. 인증 미들웨어(`auth`)가 이것으로 토큰을 검증하고, 채널이 열
에이전트와 상한을 본다.

**검증 순서는 토큰 형식 → 발급자로 사이트 항목 → `kid` 로 키 → 서명·필수 클레임·`aud`·`iss`
(라이브러리) → `exp`·`iat`·`nbf`·수명(여기) → `sub` 다.** 발급자와 `kid` 는 서명을 검증하기 전에
서명 없이 읽어 항목 하나와 키를 고른다. 그래서 한 사이트가 다른 사이트의 발급자를 주장해도 그
항목의 키로만 검증되고, 모르는 발급자와 모르는 `kid` 는 키를 보기 전에 끝난다. 어느 단계든 실패는
같은 401 이고 밖으로는 고정 문구 하나다 — 만료인지 서명인지 말하면 토큰을 다듬어 가며 단계를
알아낼 수 있다. 원인(`Refusal.reason`)은 서버 기록에만 가고 토큰 값은 싣지 않는다(원칙 V).

**시간 클레임은 여기서 `Clock` 포트의 지금으로 센다.** 라이브러리의 `decode` 에는 시각을 넣을
자리가 없어(PyJWT 2.14.0) 그대로 쓰면 가짜 시계로 만료를 잴 수 없다. 그래서 라이브러리의 시간
검증을 끄고 그 비교식을 옮긴다 — 만료는 `exp <= 지금 - 여유`, 미래의 `iat` 와 `nbf` 는
`> 지금 + 여유`이고 여유는 셋에 같이 걸린다. 비교식은 PyJWT 2.14.0 의 `api_jwt.py`
(`_validate_exp`·`_validate_iat`·`_validate_nbf`)를 읽은 것이고, 라이브러리가 미래의 `iat` 를
거절하는 것은 `.scratch/end-user-channel/probes/jwt_claims.py` 가 실제 시간으로 쟀다. 다른 점은
값의 타입 하나다 — 라이브러리는 `int()` 로 받아 숫자 글자와 불린도 지나가게 두지만 여기서는 수만
받는다. 수명(`exp - iat`)은 라이브러리가 보지 않는 것이라 처음부터 여기 몫이고, 600초 경계는 명세가
정했다. 토큰은 요청 하나를 여는 것이고 연결은 그 요청이다 — 열린 스트림은 토큰이 만료돼도 끊기지
않는다.

클레임은 라이브러리가 값 타입이 느슨한 사전으로 돌려주므로 `dict(...)` 로 감싸
`Mapping[str, object]` 로 받는다. 그래야 pyright strict 가 `sub` 를 좁히라고 강제하고 타입
우회가 들지 않는다(ADR 0023).
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import jwt
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey

from agent_os.core.ports import Clock
from agent_os.sdk import AgentName, Principal

# 허용 알고리즘은 하나다(ADR 0023). `none` 과 HS256(공개 키를 비밀로 쓰는 혼동)은 라이브러리가 이
# 목록 밖이라 거절한다.
ALGORITHM = "RS256"
REQUIRED_CLAIMS = ("iss", "sub", "aud", "exp", "iat")
# `exp - iat` 의 상한(초)과 시계 여유(초). 값은 명세가 정했다. 꼭 600 인 토큰은 받는다.
MAX_LIFETIME_SECONDS = 600
LEEWAY_SECONDS = 30
# 주체 이름 `<발급자>|<sub>` 의 구분자. 사이트 파일이 발급자에 이것을 금지하므로 첫 `|` 에서 가르면
# 짝이 하나로 정해지고, OS 사용자 이름에도 금지하므로(`main.py`) 이것이 든 주체는 언제나 최종
# 사용자다. 관리 화면이 이 모양으로 최종 사용자의 실행을 알아본다.
PRINCIPAL_SEPARATOR = "|"


@dataclass(frozen=True)
class SiteKey:
    """사이트의 공개 키 하나. 토큰 헤더의 `kid` 가 이것을 고른다. `kid` 없는 키는 사이트에 많아야
    하나다(사이트 파일의 규칙)."""

    kid: str | None
    key: RSAPublicKey


@dataclass(frozen=True)
class SiteLimits:
    """사이트 파일의 상한 표. 값마다 선택이고 없음은 채널의 기본값이다.

    요청 글자 수, 주체별 동시 실행, 주체별 시간당 실행, 사이트별 동시 실행, 사이트별 시간당 실행,
    주체별 구독의 여섯이다(ADR 0023). 값은 1 이상의 정수다 — 사이트 파일을 읽는 쪽이 판정하고 이
    타입은 그것을 믿는다. 기본값을 여기 두지 않는 이유는 기본값 일곱이 채널의 한 곳
    (`agent_os.channel.http.limits`)에 있어야 하기 때문이다. 이 층은 채널을 import 할 수 없고,
    여기도 숫자를 두면 같은 값이 두 곳에 선다. 전역 동시 실행은 사이트의 것이 아니라 `serve` 의
    인자다.
    """

    request_chars: int | None = None
    concurrent_runs_per_principal: int | None = None
    hourly_runs_per_principal: int | None = None
    concurrent_runs_per_site: int | None = None
    hourly_runs_per_site: int | None = None
    subscriptions_per_principal: int | None = None


@dataclass(frozen=True)
class Site:
    """받아들이는 사이트 하나. 발급자, 대상, 공개 키, 허용 출처, 열 에이전트, 상한 표를 든다.

    발급자는 비지 않았고 사이트끼리 겹치지 않으며 `|` 를 품지 않는다 — 사이트 파일을 읽는 쪽이
    판정하고 이 타입은 그것을 믿는다. 허용 출처는 CORS 의 입력이고 사이트 목록이 모든 사이트의 것을
    합쳐 넘긴다(`Sites.origins`). 열 에이전트는 이 사이트의 최종 사용자가 볼 수 있는 에이전트의
    집합이고 core 가 판정한다(ADR 0023 의 2026-10-05 이력). 상한 표는 채널이 센다.
    """

    issuer: str
    audience: str
    keys: tuple[SiteKey, ...]
    allowed_origins: tuple[str, ...]
    agents: frozenset[AgentName]
    limits: SiteLimits = SiteLimits()


@dataclass(frozen=True)
class Sites:
    """사이트 목록. 비면 받아들일 사이트가 없어 최종 사용자 면의 모든 토큰이 401 이다(ADR 0023)."""

    entries: tuple[Site, ...] = ()

    def of(self, issuer: str) -> Site | None:
        """발급자의 사이트 항목(질의). 발급자는 겹치지 않으므로 많아야 하나다."""
        return next((site for site in self.entries if site.issuer == issuer), None)

    def origins(self) -> tuple[str, ...]:
        """모든 사이트의 허용 출처를 합친 것(질의). 처음 나온 순서이고 겹친 것은 하나다.

        CORS 가 이것 하나를 받는다. 사이트별로 가르지 않는 이유는 preflight 에 토큰이 없어
        미들웨어가 출처의 사이트를 토큰보다 먼저 가를 수 없기 때문이다(end-user-channel 명세
        "CORS"). 그래서 한 사이트의 페이지에서 다른 사이트의 토큰으로 보낸 요청도 읽힌다 — 둘 다
        운영자가 사이트 파일에 올린 사이트라 믿는 범위 안이고, 가르려면 토큰과 출처를 묶는 규칙이
        하나 더 든다.
        """
        return tuple(dict.fromkeys(o for site in self.entries for o in site.allowed_origins))


@dataclass(frozen=True)
class EndUser:
    """서명 토큰을 지난 요청의 신원. 주체(`발급자|sub`)와 그 토큰을 서명한 사이트 항목이다."""

    principal: Principal
    site: Site


@dataclass(frozen=True)
class Refusal:
    """서명 토큰을 받아들이지 않은 이유. 서버 기록에만 간다."""

    reason: str


class _Refused(Exception):
    """검증의 단계 하나가 끝냈다. 밖으로는 `Refusal` 로 나간다."""


def verify_signed(token: str | None, sites: Sites, clock: Clock) -> EndUser | Refusal:
    """서명 토큰 하나를 검증한다(질의). 순서와 이유는 모듈 독스트링.

    시계는 시간 클레임에 닿을 때만 읽는다. 그 앞의 단계에서 끝나는 토큰은 시계를 부르지 않는다.
    """
    if token is None:
        return Refusal("토큰이 없다")
    try:
        return _verified(token, sites, clock)
    except _Refused as refused:
        return Refusal(str(refused))


def _verified(token: str, sites: Sites, clock: Clock) -> EndUser:
    header, unverified = _unverified(token)
    issuer = unverified.get("iss")
    if not isinstance(issuer, str):
        raise _Refused("발급자(iss)가 없다")
    site = sites.of(issuer)
    if site is None:
        raise _Refused("모르는 발급자다")
    claims = _signed_claims(token, site, _candidate_keys(site, header))
    _check_times(claims, clock)
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise _Refused("sub 가 비지 않은 문자열이 아니다")
    return EndUser(principal=Principal(f"{site.issuer}{PRINCIPAL_SEPARATOR}{subject}"), site=site)


def _unverified(token: str) -> tuple[Mapping[str, object], Mapping[str, object]]:
    """서명을 보기 전에 읽는 헤더와 클레임. 사이트 항목과 키를 고르는 데만 쓴다."""
    try:
        header: Mapping[str, object] = dict(jwt.get_unverified_header(token))
        claims: Mapping[str, object] = dict(jwt.decode(token, options={"verify_signature": False}))
    except jwt.PyJWTError as error:
        raise _Refused(f"토큰의 형식이 깨졌다: {type(error).__name__}") from error
    return header, claims


def _candidate_keys(site: Site, header: Mapping[str, object]) -> Sequence[SiteKey]:
    """헤더의 `kid` 가 고른 키. 헤더에 `kid` 가 없으면 사이트의 키 전부를 차례로 시도한다.

    `kid` 가 문자열이 아닌 헤더는 라이브러리가 서명 없는 읽기에서 이미 거절한다.
    """
    kid = header.get("kid")
    if kid is None:
        return site.keys
    chosen = [key for key in site.keys if key.kid == kid]
    if not chosen:
        raise _Refused("사이트에 그 kid 의 키가 없다")
    return chosen


def _signed_claims(token: str, site: Site, keys: Sequence[SiteKey]) -> Mapping[str, object]:
    """서명과 필수 클레임과 대상과 발급자를 라이브러리가 본 클레임. 시간 클레임은 보지 않는다.

    서명이 틀린 것만 다음 키로 넘어간다. 그 밖의 거절(알고리즘, 클레임, 대상)은 키와 무관하다.
    """
    for candidate in keys:
        try:
            return dict(
                jwt.decode(
                    token,
                    candidate.key,
                    algorithms=[ALGORITHM],
                    audience=site.audience,
                    issuer=site.issuer,
                    options={
                        "require": list(REQUIRED_CLAIMS),
                        "verify_exp": False,
                        "verify_iat": False,
                        "verify_nbf": False,
                    },
                )
            )
        except jwt.InvalidSignatureError:
            continue
        except jwt.PyJWTError as error:
            raise _Refused(f"라이브러리가 거절했다: {type(error).__name__}") from error
    raise _Refused("어느 키로도 서명이 맞지 않는다")


def _check_times(claims: Mapping[str, object], clock: Clock) -> None:
    """만료, 미래의 `iat`·`nbf`, 수명. 라이브러리의 비교식을 `Clock` 의 지금으로 센다.

    만료와 미래는 라이브러리처럼 정수로 자른 값으로 견준다. 수명은 자르지 않은 값으로 센다 —
    자르면 600.9초 같은 수명이 600초로 읽혀 경계를 넘은 토큰이 지나간다.
    """
    now = clock.now().timestamp()
    expires = _numeric_date(claims, "exp")
    issued = _numeric_date(claims, "iat")
    if int(expires) <= now - LEEWAY_SECONDS:
        raise _Refused("만료됐다(exp)")
    if int(issued) > now + LEEWAY_SECONDS:
        raise _Refused("발급 시각(iat)이 미래다")
    if "nbf" in claims and int(_numeric_date(claims, "nbf")) > now + LEEWAY_SECONDS:
        raise _Refused("아직 쓸 수 없다(nbf)")
    lifetime = expires - issued
    if lifetime > MAX_LIFETIME_SECONDS:
        raise _Refused(f"수명 {lifetime:g}초가 최대 {MAX_LIFETIME_SECONDS}초를 넘는다")


def _numeric_date(claims: Mapping[str, object], name: str) -> float:
    """시간 클레임 하나(NumericDate)의 값. 불린과 무한대는 수가 아니다."""
    value = claims.get(name)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise _Refused(f"{name} 가 수가 아니다")
    if not math.isfinite(value):
        raise _Refused(f"{name} 가 유한한 수가 아니다")
    return float(value)
