"""Agent OS 의 로그인 경로 대역(스텁). 같은 폴더의 probe.mjs 가 띄운다.

    uv run python .scratch/portal-admin/probes/login_relay/agentos_stub.py --port <포트>

실제 Agent OS 의 로그인 경로는 아직 없다(admin-login 이 짓는다). 이 대역은 ADR 0062 결정 "로그인
상태"와 "요청 출처 검사"가 적은 것만 흉내 낸다. 그 ADR 이 정하지 않은 것은 이 대역이 골랐고 README
가 적는다.

ADR 0062 에서 옮긴 것
- 로그인 상태는 쿠키 둘이다. 수명이 짧은 JWT(HS256)와 서버가 기억하는 갱신용 번호. 둘 다 `__Host-`
  접두사에 `HttpOnly; Secure; SameSite=Strict; Path=/` 다.
- 갱신용 번호는 쓸 때마다 새 번호로 바뀌고, 이미 바꾼 옛 번호가 다시 오면 그 로그인을 끊는다.
- JWT 는 서버 상태를 보지 않는다. 끊긴 로그인의 JWT 도 만료 전까지는 "지금 누구인지"가 받는다.
- 요청 출처 검사. `/auth/` 아래의 모든 경로에서 `Sec-Fetch-Site` 가 있으면 `same-origin` 만 받고, 그
  머리가 없으면 `Origin` 도 없을 때만 받는다.

이 대역이 고른 것(ADR 이 정하지 않았다)
- 경로 이름(`/auth/login`, `/auth/me`, `/auth/refresh`, `/auth/logout`)과 쿠키 이름(`__Host-aos_at`,
  `__Host-aos_rt`), 응답의 모양, 갱신용 번호 쿠키의 `Max-Age`, JWT 쿠키가 세션 쿠키라는 것.
- 갱신이 거절되면 401 에 쿠키 둘을 지우는 줄(`Max-Age=0`)을 싣는다. "지금 누구인지"의 401 에는 싣지
  않는다.
- 짧은 유예의 뜻. `grace_seconds` 가 0 이면 유예가 없다. 0 보다 크면, 이미 바꾼 옛 번호가 바뀐
  때부터 그 초 안에 다시 오면 끊지 않고 새 JWT 와 새 번호를 낸다. 그때 앞서 낸 번호를 어떻게
  두는지가 `grace_kind` 다.
    chain   앞서 낸 번호를 그 순간 옛 번호로 돌린다. 통하는 번호는 언제나 마지막에 낸 하나다.
    family  앞서 낸 번호도 그대로 통한다. 통하는 번호가 여럿이 된다.
  유예가 지난 옛 번호가 오면 두 뜻 모두 그 로그인을 끊는다.
- 비밀번호를 보지 않는다. 로그인은 정해진 계정 이름 하나만 받는다.

프로브만 쓰는 것(`/__probe/` 아래, 요청 출처 검사 밖)
- reset 은 로그인과 이름표를 지우고 설정을 바꾼다. log 는 받은 요청을 머리 그대로(uvicorn 이 이름을
  소문자로 준다) 돌려주고, state 는 로그인마다 통하는 번호와 끊긴 까닭을, labels 는 낸 쿠키 값의
  이름표를 돌려준다. revoke 는 모든 로그인을 끊는다(다른 자리에서 계정이 '쓰지 않음'이 된 경우의
  자리).
- 갱신 응답의 지연. `refresh_delays_ms` 의 i 번째 값은 reset 뒤 i 번째로 닿은 갱신의 응답을 그만큼
  늦춘다. 목록을 넘은 갱신은 `hold_ms` 만큼 늦춘다. 번호를 바꾸는 일은 닿은 차례대로 바로 하고
  응답만 늦춘다.
- 쿠키 값은 무작위이고 비밀이 아니다. 이름표를 붙이려고 값을 그대로 들고 있다(실제 서버는 해시만
  둔다).
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import hmac
import json
import platform
import secrets
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

import fastapi
import starlette
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

ACCESS_COOKIE = "__Host-aos_at"
REFRESH_COOKIE = "__Host-aos_rt"
REFRESH_MAX_AGE = 1800
ACCOUNT = "probe-operator"
KEY = secrets.token_bytes(32)

Entry = dict[str, object]


@dataclass
class Config:
    access_ttl: float = 2.0
    grace_seconds: float = 0.0
    grace_kind: str = "chain"
    refresh_delays_ms: list[float] = field(default_factory=list[float])
    hold_ms: float = 0.0


@dataclass
class Login:
    """로그인 하나. valid 는 지금 통하는 번호, rotated 는 이미 바꾼 옛 번호와 바꾼 시각이다."""

    ident: str
    account: str
    valid: dict[str, str] = field(default_factory=dict[str, str])
    rotated: dict[str, tuple[str, float]] = field(default_factory=dict[str, tuple[str, float]])
    revoked: str | None = None
    last_issued: str = ""


@dataclass
class State:
    """issued 는 reset 뒤 낸 쿠키 쌍의 수이고 이름표(at0·rt0, at1·rt1 …)의 번호다."""

    config: Config = field(default_factory=Config)
    logins: dict[str, Login] = field(default_factory=dict[str, Login])
    owner: dict[str, str] = field(default_factory=dict[str, str])
    labels: dict[str, str] = field(default_factory=dict[str, str])
    refresh_seen: int = 0
    issued: int = 0


STATE = State()
LOG: list[Entry] = []
app = FastAPI()


def b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def sign(claims: dict[str, object]) -> str:
    head = b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    body = b64(json.dumps(claims, separators=(",", ":")).encode())
    mac = hmac.new(KEY, f"{head}.{body}".encode(), hashlib.sha256).digest()
    return f"{head}.{body}.{b64(mac)}"


def verify(token: str) -> tuple[dict[str, object] | None, str]:
    """(주장, 까닭). 서명이 맞고 만료 전이면 주장을, 아니면 None 과 까닭을 낸다."""
    parts = token.split(".")
    if len(parts) != 3:
        return None, "access_invalid"
    head, body, mac = parts
    expected = b64(hmac.new(KEY, f"{head}.{body}".encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(expected, mac):
        return None, "access_invalid"
    claims: dict[str, object] = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    expires = claims.get("exp")
    if not isinstance(expires, int | float) or time.time() >= expires:
        return None, "access_expired"
    return claims, ""


def entry_of(request: Request) -> Entry:
    entry: Entry = request.state.entry
    return entry


def issue(login: Login, response: Response) -> dict[str, str]:
    """새 JWT 와 새 갱신용 번호를 지어 응답에 싣는다. 쿠키 줄은 Starlette 의 set_cookie 가
    짓는다."""
    now = time.time()
    token = sign(
        {
            "sub": login.account,
            "sid": login.ident,
            "iat": now,
            "exp": now + STATE.config.access_ttl,
            "jti": secrets.token_hex(4),
        }
    )
    number = secrets.token_urlsafe(24)
    access_label = f"at{STATE.issued}"
    refresh_label = f"rt{STATE.issued}"
    STATE.issued += 1
    login.last_issued = refresh_label
    login.valid[number] = refresh_label
    STATE.owner[number] = login.ident
    STATE.labels[token] = access_label
    STATE.labels[number] = refresh_label
    response.set_cookie(
        ACCESS_COOKIE, token, path="/", secure=True, httponly=True, samesite="strict"
    )
    response.set_cookie(
        REFRESH_COOKIE,
        number,
        max_age=REFRESH_MAX_AGE,
        path="/",
        secure=True,
        httponly=True,
        samesite="strict",
    )
    return {"at": access_label, "rt": refresh_label}


def clear(response: Response) -> None:
    for name in (ACCESS_COOKIE, REFRESH_COOKIE):
        response.delete_cookie(name, path="/", secure=True, httponly=True, samesite="strict")


def refused(entry: Entry, reason: str) -> JSONResponse:
    """갱신과 로그인의 거절. 401 에 쿠키 둘을 지우는 줄을 싣는다."""
    entry["reason"] = reason
    response = JSONResponse({"reason": reason}, status_code=401)
    clear(response)
    return response


def retire(login: Login, number: str, now: float) -> None:
    login.rotated[number] = (login.valid.pop(number), now)


def origin_problem(request: Request) -> str | None:
    """ADR 0062 결정 "요청 출처 검사". 받으면 None, 거절이면 까닭이다."""
    site = request.headers.get("sec-fetch-site")
    if site is not None:
        return None if site == "same-origin" else f"sec-fetch-site={site}"
    if request.headers.get("origin") is not None:
        return "origin without sec-fetch-site"
    return None


@app.middleware("http")
async def record(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    path = request.url.path
    if path.startswith("/__probe/"):
        return await call_next(request)
    headers: list[tuple[bytes, bytes]] = request.scope["headers"]
    entry: Entry = {
        "seq": len(LOG),
        "method": request.method,
        "path": path,
        "probe": request.query_params.get("probe"),
        "headers": [[name.decode("latin-1"), value.decode("latin-1")] for name, value in headers],
        "check": "exempt",
        "reason": None,
        "outcome": None,
        "presented": {},
        "issued": None,
    }
    LOG.append(entry)
    request.state.entry = entry
    problem = origin_problem(request) if path.startswith("/auth/") else None
    if problem is None:
        if path.startswith("/auth/"):
            entry["check"] = "pass"
        response = await call_next(request)
    else:
        entry["check"] = f"reject: {problem}"
        entry["reason"] = "origin_check"
        response = JSONResponse({"reason": "origin_check", "detail": problem}, status_code=403)
    entry["status"] = response.status_code
    entry["setCookie"] = response.headers.getlist("set-cookie")
    return response


@app.get("/page")
async def page() -> HTMLResponse:
    """포트 A 의 빈 문서. 실제로는 관리 화면(Next)이 내는 자리라 요청 출처 검사 밖이다."""
    return HTMLResponse("<!doctype html><title>login_relay A</title><p>agent os origin</p>")


@app.post("/auth/login")
async def login(request: Request) -> Response:
    entry = entry_of(request)
    body: dict[str, object] = await request.json()
    if body.get("account") != ACCOUNT:
        return refused(entry, "login_failed")
    made = Login(ident=f"login{len(STATE.logins)}", account=ACCOUNT)
    STATE.logins[made.ident] = made
    response = JSONResponse({"account": made.account, "login": made.ident})
    entry["issued"] = issue(made, response)
    entry["outcome"] = "logged_in"
    return response


@app.get("/auth/me")
async def me(request: Request) -> Response:
    entry = entry_of(request)
    token = request.cookies.get(ACCESS_COOKIE)
    if token is None:
        entry["reason"] = "access_missing"
        return JSONResponse({"reason": "access_missing"}, status_code=401)
    entry["presented"] = {"at": STATE.labels.get(token, "unknown")}
    claims, reason = verify(token)
    if claims is None:
        entry["reason"] = reason
        return JSONResponse({"reason": reason}, status_code=401)
    return JSONResponse({"account": claims["sub"], "login": claims["sid"]})


@app.post("/auth/refresh")
async def refresh(request: Request) -> Response:
    entry = entry_of(request)
    index = STATE.refresh_seen
    STATE.refresh_seen += 1
    delays = STATE.config.refresh_delays_ms
    delay = delays[index] if index < len(delays) else STATE.config.hold_ms
    entry["delayMs"] = delay
    response = rotate(entry, request.cookies.get(REFRESH_COOKIE))
    # 번호를 바꾸는 일은 위에서 끝났다. 응답만 늦춘다.
    if delay > 0:
        await asyncio.sleep(delay / 1000)
    return response


def rotate(entry: Entry, number: str | None) -> Response:
    if number is None:
        return refused(entry, "refresh_missing")
    entry["presented"] = {"rt": STATE.labels.get(number, "unknown")}
    found = STATE.logins.get(STATE.owner.get(number, ""))
    if found is None:
        return refused(entry, "refresh_unknown")
    if found.revoked is not None:
        entry["outcome"] = "session_revoked"
        return refused(entry, "session_revoked")
    now = time.monotonic()
    if number in found.valid:
        entry["outcome"] = "rotated"
        retire(found, number, now)
    else:
        age = now - found.rotated[number][1]
        entry["reuseAgeMs"] = round(age * 1000)
        grace = STATE.config.grace_seconds
        if grace <= 0 or age > grace:
            found.revoked = "refresh_reuse"
            entry["outcome"] = "reuse_revoked"
            return refused(entry, "refresh_reuse")
        entry["outcome"] = "grace"
        if STATE.config.grace_kind == "chain":
            for other in list(found.valid):
                retire(found, other, now)
    response = JSONResponse({"account": found.account, "login": found.ident})
    entry["issued"] = issue(found, response)
    return response


@app.post("/auth/logout")
async def logout(request: Request) -> Response:
    entry = entry_of(request)
    number = request.cookies.get(REFRESH_COOKIE)
    found = STATE.logins.get(STATE.owner.get(number or "", ""))
    if found is not None and found.revoked is None:
        found.revoked = "logout"
    entry["outcome"] = "logged_out"
    response = Response(status_code=204)
    clear(response)
    return response


@app.get("/__probe/health")
async def health() -> dict[str, str]:
    return {
        "role": "agentos_stub",
        "python": platform.python_version(),
        "fastapi": fastapi.__version__,
        "starlette": starlette.__version__,
        "uvicorn": uvicorn.__version__,
    }


@app.post("/__probe/reset")
async def reset(request: Request) -> dict[str, object]:
    body: dict[str, object] = await request.json()
    known = Config()
    for name, value in body.items():
        if not hasattr(known, name):
            return {"problem": f"모르는 설정: {name}"}
        setattr(known, name, value)
    if known.grace_kind not in ("chain", "family"):
        return {"problem": f"모르는 grace_kind: {known.grace_kind}"}
    STATE.config = known
    STATE.logins.clear()
    STATE.owner.clear()
    STATE.labels.clear()
    STATE.refresh_seen = 0
    STATE.issued = 0
    return {"seq": len(LOG)}


@app.get("/__probe/log")
async def log(since: int = 0) -> list[Entry]:
    return LOG[since:]


@app.get("/__probe/state")
async def state() -> dict[str, object]:
    now = time.monotonic()
    return {
        "logins": [
            {
                "login": found.ident,
                "revoked": found.revoked,
                "valid": sorted(found.valid.values()),
                "rotated": {
                    label: round((now - since) * 1000) for label, since in found.rotated.values()
                },
                "lastIssued": found.last_issued,
            }
            for found in STATE.logins.values()
        ]
    }


@app.get("/__probe/labels")
async def labels() -> dict[str, str]:
    return STATE.labels


@app.post("/__probe/revoke")
async def revoke() -> dict[str, int]:
    for found in STATE.logins.values():
        found.revoked = found.revoked or "probe_revoke"
    return {"revoked": len(STATE.logins)}


@app.get("/__probe/plain-cookie")
async def plain_cookie() -> Response:
    """대조. `Secure` 가 없는 쿠키 하나를 싣는다. httpx 의 쿠키 통이 그것을 다음 요청에 싣는지 볼 때
    쓴다."""
    response = JSONResponse({"set": "probe_plain"})
    response.set_cookie("probe_plain", "kept-by-client", path="/")
    return response


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    # 쉬는 연결을 닫기까지의 초. uvicorn 의 기본값은 5 다. 프로브는 길게 준다(까닭은 README).
    parser.add_argument("--keep-alive", type=int, default=5)
    args = parser.parse_args()
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=args.port,
        log_level="warning",
        timeout_keep_alive=args.keep_alive,
    )


if __name__ == "__main__":
    main()
