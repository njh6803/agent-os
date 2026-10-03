"""소비 지점(`consume_<후보>.py`)이 실제로 서명한 토큰을 받아들이고 거부하는지 돌린다.

토큰은 후보 라이브러리와 무관하게 표준 라이브러리와 `cryptography`로 직접 만든다. 같은 라이브러리가
서명과 검증을 둘 다 맡으면 서로의 버릇을 맞춰 줄 수 있고, 위젯을 임베드한 사이트의 백엔드는 다른
언어·라이브러리로 서명한다. `alg: none`과 알고리즘 혼동 토큰도 같은 길로 만든다.

뒤쪽 "고정하지 않으면" 절은 소비 지점을 거치지 않고 라이브러리를 직접 부른다. 허용 알고리즘을
고정하지 않거나 대칭·비대칭을 섞어 허용했을 때 라이브러리 스스로 무엇을 막는지 본다.

후보 환경의 인터프리터로 돈다. 인자는 후보 이름(pyjwt, joserfc, jwcrypto)이다.

    <환경 루트>/<후보>/.venv/Scripts/python .scratch/web-widget/probes/jwt_verify/cases.py <후보>
    PYTHONUTF8=1 uv run python .scratch/web-widget/probes/jwt_verify/cases.py pyjwt  # 저장소 .venv
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import importlib
import importlib.metadata
import json
import secrets
import sys
import time
import warnings
from collections.abc import Callable
from dataclasses import dataclass

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa

AUDIENCE = "agent-os-widget"
ISSUER = "https://embedder.example"
SUBJECT = "user-123"

DIST = {"pyjwt": "pyjwt", "joserfc": "joserfc", "jwcrypto": "jwcrypto"}

# 토큰 헤더의 alg → 소비 지점에 고정하는 알고리즘. PyJWT 는 RFC 9864 의 "Ed25519" 이름을 모르므로
# 그 행의 검증자는 자기 이름("EdDSA")으로 고정된다. 사이트가 새 이름으로 서명하는 경우를 본다.
PINNED: dict[str, dict[str, str]] = {
    "pyjwt": {"HS256": "HS256", "EdDSA": "EdDSA", "Ed25519": "EdDSA", "RS256": "RS256"},
    "joserfc": {"HS256": "HS256", "EdDSA": "EdDSA", "Ed25519": "Ed25519", "RS256": "RS256"},
    "jwcrypto": {"HS256": "HS256", "EdDSA": "EdDSA", "Ed25519": "Ed25519", "RS256": "RS256"},
}


type Signer = Callable[[bytes], bytes]


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def compact(header: dict[str, object], claims: dict[str, object], sign: Signer) -> str:
    head = b64(json.dumps(header, separators=(",", ":")).encode())
    body = b64(json.dumps(claims, separators=(",", ":")).encode())
    signing_input = f"{head}.{body}"
    return f"{signing_input}.{b64(sign(signing_input.encode()))}"


@dataclass(frozen=True)
class Material:
    """검증자가 설정으로 받는 바이트(공유 비밀 또는 PEM 공개 키)와 서명 함수."""

    verify: bytes
    sign: Signer
    asymmetric: bool


def hmac_material() -> Material:
    secret = secrets.token_bytes(32)
    return Material(secret, lambda m: hmac.new(secret, m, hashlib.sha256).digest(), False)


def pem(public: ed25519.Ed25519PublicKey | rsa.RSAPublicKey) -> bytes:
    return public.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )


def ed25519_material() -> Material:
    private = ed25519.Ed25519PrivateKey.generate()
    return Material(pem(private.public_key()), private.sign, True)


def rsa_material() -> Material:
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return Material(
        pem(private.public_key()),
        lambda m: private.sign(m, padding.PKCS1v15(), hashes.SHA256()),
        True,
    )


FAMILY: dict[str, Callable[[], Material]] = {
    "HS256": hmac_material,
    "EdDSA": ed25519_material,
    "Ed25519": ed25519_material,
    "RS256": rsa_material,
}


def claims(**override: object) -> dict[str, object]:
    now = int(time.time())
    base: dict[str, object] = {
        "sub": SUBJECT,
        "aud": AUDIENCE,
        "iss": ISSUER,
        "iat": now,
        "exp": now + 300,
    }
    for name, value in override.items():
        if value is None:
            base.pop(name, None)
        else:
            base[name] = value
    return base


def tokens(alg: str, material: Material) -> list[tuple[str, bool, str]]:
    """(사례, 수락이 기대인가, 토큰). 기대는 보안 쪽 기대다. 정상만 수락이다."""
    header: dict[str, object] = {"alg": alg, "typ": "JWT"}
    now = int(time.time())
    other = FAMILY[alg]()
    found = [
        ("정상", True, compact(header, claims(), material.sign)),
        ("만료(1시간 전)", False, compact(header, claims(exp=now - 3600), material.sign)),
        ("만료(30초 전)", False, compact(header, claims(exp=now - 30), material.sign)),
        ("exp 없음", False, compact(header, claims(exp=None), material.sign)),
        ("다른 키로 서명", False, compact(header, claims(), other.sign)),
        ("aud 다름", False, compact(header, claims(aud="someone-else"), material.sign)),
        ("aud 없음", False, compact(header, claims(aud=None), material.sign)),
        ("iss 다름", False, compact(header, claims(iss="https://evil.example"), material.sign)),
        ("sub 가 숫자", False, compact(header, claims(sub=123), material.sign)),
        ("sub 없음", False, compact(header, claims(sub=None), material.sign)),
        ("alg none", False, compact({"alg": "none", "typ": "JWT"}, claims(), lambda _: b"")),
        ("형식 깨짐", False, "a.b.c"),
    ]
    if material.asymmetric:
        confused = compact(
            {"alg": "HS256", "typ": "JWT"},
            claims(),
            lambda m: hmac.new(material.verify, m, hashlib.sha256).digest(),
        )
        found.append(("혼동(HS256, 공개 키 PEM 을 비밀로)", False, confused))
    return found


def describe(error: BaseException) -> str:
    text = str(error).replace("\n", " ")
    return f"{type(error).__name__}: {text}"[:140]


def outcome(call: Callable[[], str], invalid: type[Exception]) -> tuple[bool | None, str]:
    """(수락했나, 설명). 소비 지점의 예외가 아닌 것이 새어 나오면 수락 여부를 None 으로 둔다."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            subject = call()
        except invalid as error:
            cause = error.__cause__
            accepted, text = False, describe(cause) if cause is not None else str(error)
        except Exception as error:  # 새어 나온 예외를 그대로 적는다
            accepted, text = None, f"새어 나옴 {describe(error)}"
        else:
            accepted, text = True, f"sub={subject!r}"
    names = sorted({w.category.__name__ for w in caught})
    return accepted, text + (f" [경고: {', '.join(names)}]" if names else "")


def mark(accepted: bool | None) -> str:
    return {True: "수락", False: "거부", None: "새어 나옴"}[accepted]


# ---- "고정하지 않으면": 라이브러리를 직접 부른다 ----


def unpinned(lib: str, alg: str, token: str, material: Material, allowed: list[str] | None) -> str:
    """서명만 본다. 허용 목록을 주지 않거나(None) 대칭·비대칭을 섞어 준다."""
    if lib == "pyjwt":
        import jwt

        if allowed is None:
            return str(jwt.decode(token, material.verify, audience=AUDIENCE, issuer=ISSUER))
        return str(
            jwt.decode(token, material.verify, algorithms=allowed, audience=AUDIENCE, issuer=ISSUER)
        )
    if lib == "joserfc":
        from joserfc import jwt as jose_jwt
        from joserfc.jwk import OKPKey, RSAKey

        key = (
            RSAKey.import_key(material.verify)
            if alg == "RS256"
            else OKPKey.import_key(material.verify)
        )
        return str(jose_jwt.decode(token, key, algorithms=allowed).claims)
    from jwcrypto import jwk
    from jwcrypto import jwt as jwc_jwt

    key = jwk.JWK.from_pem(material.verify)
    return str(jwc_jwt.JWT(jwt=token, key=key, algs=allowed).claims)


def unpinned_outcome(call: Callable[[], str]) -> tuple[bool | None, str]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            call()
        except Exception as error:  # 라이브러리가 낸 예외를 그대로 적는다
            accepted, text = False, describe(error)
        else:
            accepted, text = True, "서명 통과"
    names = sorted({w.category.__name__ for w in caught})
    return accepted, text + (f" [경고: {', '.join(names)}]" if names else "")


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in DIST:
        print(f"인자: {' | '.join(DIST)}", file=sys.stderr)
        return 2
    lib = sys.argv[1]
    consumer = importlib.import_module(f"consume_{lib}")
    invalid: type[Exception] = consumer.InvalidToken
    print(
        f"{lib} {importlib.metadata.version(DIST[lib])},"
        f" cryptography {importlib.metadata.version('cryptography')},"
        f" python {sys.version.split()[0]}"
    )
    print("\n| 토큰 alg | 고정한 alg | 사례 | 기대 | 결과 | 원인·값 |")
    print("|---|---|---|---|---|---|")
    surprises: list[str] = []
    for alg, pinned in PINNED[lib].items():
        material = FAMILY[alg]()
        for case, want, token in tokens(alg, material):

            def call(
                token: str = token, material: Material = material, pinned: str = pinned
            ) -> str:
                key = (
                    material.verify
                    if lib == "pyjwt"
                    else consumer.load_key(pinned, material.verify)
                )
                return consumer.verified_subject(
                    token, key, algorithm=pinned, audience=AUDIENCE, issuer=ISSUER
                )

            accepted, text = outcome(call, invalid)
            if accepted is not want:
                surprises.append(f"{alg}/{case}")
            print(f"| {alg} | {pinned} | {case} | {mark(want)} | {mark(accepted)} | {text} |")

    print("\n고정하지 않으면(라이브러리 직접 호출, 서명만)")
    print("\n| 토큰 alg | 허용 목록 | 사례 | 결과 | 원인 |")
    print("|---|---|---|---|---|")
    for alg in ("EdDSA", "Ed25519", "RS256"):
        material = FAMILY[alg]()
        pinned = PINNED[lib][alg]
        valid = compact({"alg": alg, "typ": "JWT"}, claims(), material.sign)
        confused = compact(
            {"alg": "HS256", "typ": "JWT"},
            claims(),
            lambda m, secret=material.verify: hmac.new(secret, m, hashlib.sha256).digest(),
        )
        none = compact({"alg": "none", "typ": "JWT"}, claims(), lambda _: b"")
        rows: list[tuple[str, list[str] | None, str]] = [
            ("정상", None, valid),
            ("혼동", None, confused),
            ("혼동", [pinned, "HS256"], confused),
            ("alg none", None, none),
            ("alg none", [pinned, "none"], none),
        ]
        for case, allowed, token in rows:
            accepted, text = unpinned_outcome(
                lambda token=token, material=material, allowed=allowed, alg=alg: unpinned(
                    lib, alg, token, material, allowed
                )
            )
            shown = "기본값" if allowed is None else str(allowed)
            print(f"| {alg} | {shown} | {case} | {mark(accepted)} | {text} |")

    print(f"\n기대와 다른 사례: {surprises if surprises else '없음'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
