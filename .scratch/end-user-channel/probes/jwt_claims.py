"""설치된 PyJWT 로 명세가 정할 클레임 규칙이 서는지. 필수 클레임, `iat`, 최대 수명, `kid` 로
키 고르기, 발급자로 사이트 고르기, 검증 한 번의 비용.

web-widget 의 `jwt_verify/` 프로브는 라이브러리와 알고리즘을 골랐고(서명·만료·`aud`·`iss`·
`alg: none`·혼동), 명세가 정할 것은 거기서 재지 않았다. 여기서 저장소 `.venv` 의 PyJWT 로
여섯을 본다.

1. `options={"require": [...]}` 가 `iat` 와 `sub` 가 빠진 토큰을 거부한다(`exp`·`aud`·`iss`
   는 앞 프로브).
2. `iat` 가 미래(여유 밖)이면 거부한다. 라이브러리가 하는 것인지 본다.
3. 최대 수명(`exp - iat`)은 라이브러리가 보지 않는다. 소비 지점이 직접 센다.
4. `kid` 는 `get_unverified_header` 로 서명 검증 전에 읽히고, 사이트의 키 목록에서 하나를
   고른다. 없는 `kid` 는 거부, 헤더에 `kid` 가 없으면 목록을 차례로 시도한다. 두 키로 교체
   중인 사이트의 토큰이 둘 다 받아들여진다.
5. 발급자 선택: 서명 검증 전에 `iss` 를 읽어 사이트 항목을 고른다. 모르는 발급자는 키를
   보기 전에 거부된다.
6. RS256 검증 한 번의 비용(2048 비트). 상한의 셈이 붙기 전에 서명 검증 자체가 요청마다
   얼마인지.

    PYTHONUTF8=1 uv run python .scratch/end-user-channel/probes/jwt_claims.py
"""

from __future__ import annotations

import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

AUDIENCE = "agent-os"
ISSUER = "https://site.example"
MAX_LIFETIME = timedelta(minutes=10)
REQUIRED = ("iss", "sub", "aud", "exp", "iat")


@dataclass(frozen=True)
class Site:
    issuer: str
    keys: Mapping[str | None, bytes]  # kid → PEM 공개 키. kid 없는 키는 None 키 하나만.


class InvalidToken(Exception):
    pass


def new_key() -> tuple[rsa.RSAPrivateKey, bytes]:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return private, pem


def sign(private: rsa.RSAPrivateKey, claims: Mapping[str, object], kid: str | None) -> str:
    headers = {"kid": kid} if kid is not None else None
    return jwt.encode(dict(claims), private, algorithm="RS256", headers=headers)


def candidate_keys(site: Site, header: Mapping[str, object]) -> Sequence[bytes]:
    kid = header.get("kid")
    if kid is None:
        return list(site.keys.values())
    if not isinstance(kid, str) or kid not in site.keys:
        raise InvalidToken("모르는 kid")
    return [site.keys[kid]]


def verified_subject(token: str, sites: Mapping[str, Site]) -> str:
    try:
        unverified: Mapping[str, object] = dict(
            jwt.decode(token, options={"verify_signature": False})
        )
        header: Mapping[str, object] = dict(jwt.get_unverified_header(token))
    except jwt.PyJWTError as error:
        raise InvalidToken(f"형식: {type(error).__name__}") from error
    issuer = unverified.get("iss")
    if not isinstance(issuer, str) or issuer not in sites:
        raise InvalidToken("모르는 발급자")
    site = sites[issuer]
    last: Exception | None = None
    for key in candidate_keys(site, header):
        try:
            claims: Mapping[str, object] = dict(
                jwt.decode(
                    token,
                    key,
                    algorithms=["RS256"],
                    audience=AUDIENCE,
                    issuer=site.issuer,
                    options={"require": list(REQUIRED)},
                )
            )
            break
        except jwt.PyJWTError as error:
            last = error
    else:
        raise InvalidToken(f"서명·클레임: {type(last).__name__}: {last}") from last
    exp, iat = claims.get("exp"), claims.get("iat")
    if not isinstance(exp, int) or not isinstance(iat, int):
        raise InvalidToken("exp·iat 가 정수가 아니다")
    lifetime = exp - iat
    if lifetime > MAX_LIFETIME.total_seconds():
        limit = MAX_LIFETIME.total_seconds()
        raise InvalidToken(f"수명 {lifetime}초가 최대 {limit:.0f}초를 넘는다")
    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject:
        raise InvalidToken("sub 가 비지 않은 문자열이 아니다")
    return subject


def main() -> None:
    now = int(datetime.now(UTC).timestamp())
    old_private, old_pem = new_key()
    new_private, new_pem = new_key()
    other_private, _ = new_key()
    nokid = "https://nokid.example"
    sites = {
        ISSUER: Site(ISSUER, {"k1": old_pem, "k2": new_pem}),
        nokid: Site(nokid, {None: old_pem}),
    }
    base = {"iss": ISSUER, "sub": "user-1", "aud": AUDIENCE, "iat": now, "exp": now + 300}
    without_iat = {k: v for k, v in base.items() if k != "iat"}
    without_sub = {k: v for k, v in base.items() if k != "sub"}
    future_iat = {**base, "iat": now + 300, "exp": now + 600}
    aud_list = {**base, "aud": [AUDIENCE, "x"]}

    cases: list[tuple[str, str, str]] = [
        ("정상(k1)", sign(old_private, base, "k1"), "수락"),
        ("정상(k2, 교체 중 새 키)", sign(new_private, base, "k2"), "수락"),
        ("iat 없음", sign(old_private, without_iat, "k1"), "거부"),
        ("sub 없음", sign(old_private, without_sub, "k1"), "거부"),
        ("iat 가 5분 뒤", sign(old_private, future_iat, "k1"), "거부"),
        ("수명 11분", sign(old_private, {**base, "exp": now + 660}, "k1"), "거부"),
        ("수명 10분 꼭", sign(old_private, {**base, "exp": now + 600}, "k1"), "수락"),
        ("모르는 kid", sign(old_private, base, "k9"), "거부"),
        ("kid 없음, 키 둘인 사이트", sign(new_private, base, None), "수락(차례로 시도)"),
        ("kid 없음, 키 하나인 사이트", sign(old_private, {**base, "iss": nokid}, None), "수락"),
        ("모르는 발급자", sign(old_private, {**base, "iss": "https://who.example"}, "k1"), "거부"),
        ("남의 키로 서명하고 kid 는 k1", sign(other_private, base, "k1"), "거부"),
        ("sub 가 숫자", sign(old_private, {**base, "sub": 7}, "k1"), "거부"),
        ("aud 가 배열이고 우리 포함", sign(old_private, aud_list, "k1"), "수락"),
    ]
    mismatches = 0
    for title, token, expected in cases:
        try:
            got = f"수락 sub={verified_subject(token, sites)}"
        except InvalidToken as error:
            got = f"거부 ({error})"
        ok = got.startswith(expected[:2])
        mismatches += 0 if ok else 1
        print(f"{'  ' if ok else '!!'} {title}: 기대 {expected} → {got}")
    print(f"기대와 다른 사례: {mismatches}")

    token = sign(old_private, base, "k1")
    rounds = 1000
    started = time.perf_counter()
    for _ in range(rounds):
        verified_subject(token, sites)
    elapsed = time.perf_counter() - started
    print(f"검증 {rounds}회 {elapsed * 1000:.0f}ms, 한 번 {elapsed / rounds * 1000:.3f}ms")
    print(f"pyjwt {jwt.__version__}")


if __name__ == "__main__":
    main()
