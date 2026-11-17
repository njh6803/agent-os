"""위젯 관리 서버 대역(스텁). 같은 폴더의 probe.mjs 가 띄운다.

    uv run python .scratch/portal-admin/probes/login_relay/widget_admin_stub.py --port <포트> \
        --agent-os http://127.0.0.1:<Agent OS 대역의 포트>

위젯 관리 서버는 아직 없다(widget-admin-server 가 짓는다). 이 대역은 ADR 0064 결정 "로그인"이 적은
흐름만 흉내 낸다. 받은 쿠키를 Agent OS 의 "지금 누구인지"와 "갱신" 경로에 전하고, 갱신 때 Agent OS
가 내는 `Set-Cookie` 줄을 응답에 그대로 싣는다. Agent OS 를 부르는 HTTP 클라이언트는 셋이고 셋 다
서버가 사는 동안 함께 쓴다. 경로의 첫 마디가 고른다.
- 마디 없음   httpx 의 `AsyncClient`(dev 전용 의존성).
- `/x2/...`   httpx2 의 `AsyncClient`(런타임 의존성. 명세가 위젯 관리 서버의 클라이언트로 보는 것).
- `/x2n/...`  쿠키를 받지 않는 통을 준 httpx2 의 `AsyncClient`. 쿠키 통의 대조다.

경로(관리 화면 앱의 Next rewrites 가 브라우저의 `/api/<경로>` 를 여기 `/<경로>` 로 넘긴다)
- `/page`            포트 B 의 빈 문서.
- `/d1/data`         설계 1. 중계가 스스로 갱신한다. "지금 누구인지"가 401 이면 그 자리에서 "갱신"을
  부르고,
                     받은 `Set-Cookie` 줄을 응답에 싣는다.
- `/d2/data`         설계 2. "지금 누구인지"의 답을 그대로 돌려준다. 갱신하지 않는다. 주소에
  `delay_ms` 가 있으면 Agent OS 에 물은 뒤 답만 그만큼 늦춘다(프로브만 쓴다).
- `/d2/refresh`      설계 2. 화면이 부르는 갱신 경로. 쿠키를 "갱신"에 전하고 답과 `Set-Cookie` 줄을
  돌려준다.
- `/raw/data`, `/raw/refresh`   대조. 브라우저가 보낸 머리를 그대로 Agent OS 에 전한다.
- `/naive/refresh`   대조. `Set-Cookie` 를 줄마다 옮기지 않고 `headers["set-cookie"]` 한 값으로
  옮긴다.
- `/plain-cookie`    대조. `Secure` 없는 쿠키를 내는 Agent OS 대역의 경로를 함께 쓰는 클라이언트로
  부른다.

위 대조 둘을 뺀 경로가 Agent OS 에 보내는 요청에는 이 대역이 `Cookie` 머리 하나만 더한다. 나머지
머리는 httpx 가 스스로 붙인 것이다. 요청을 서로 맞대려고 주소에 `probe=<태그>.<길>` 을 붙인다(머리가
아니다).

프로브만 쓰는 것(`/__probe/` 아래): log 는 브라우저에게서 받은 머리와 Agent OS 에 한 호출을, state
는 함께 쓰는 클라이언트의 쿠키 통에 든 쿠키의 이름과 속성을 돌려준다. 쿠키 값은 무작위이고 비밀이
아니다.
"""

from __future__ import annotations

import argparse
import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from http.cookiejar import CookieJar, DefaultCookiePolicy

import httpx
import httpx2
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.routing import APIRoute

Entry = dict[str, object]
Client = httpx.AsyncClient | httpx2.AsyncClient
Answer = httpx.Response | httpx2.Response

# 브라우저의 머리를 그대로 전하는 대조에서도 빼는 것. 홉마다 다시 지어지는 머리다.
NOT_FORWARDED = {"host", "connection", "keep-alive", "transfer-encoding", "content-length"}

# 경로의 첫 마디가 Agent OS 를 부를 클라이언트를 고른다. 마디가 없으면 httpx 다.
PREFIXES = {"/x2": "httpx2", "/x2n": "httpx2-nojar"}


class Relay:
    agent_os: str = ""
    clients: dict[str, Client] = {}


RELAY = Relay()
LOG: list[Entry] = []


def refusing_jar() -> CookieJar:
    """어느 도메인의 쿠키도 받지 않고 싣지 않는 통. httpx2 2.13.0 의 `AsyncClient` 에는 쿠키 저장을
    끄는 인자가 없고 응답마다 `self.cookies.extract_cookies(response)` 를 부른다(`_client.py`).
    `cookies` 인자에 `CookieJar` 를 주면 `Cookies` 가 그 통을 그대로 쓰므로(`_models.py`), 받는
    도메인이 하나도 없는 정책의 통을 준다."""
    return CookieJar(policy=DefaultCookiePolicy(allowed_domains=[]))


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    async with (
        httpx.AsyncClient(timeout=30) as old,
        httpx2.AsyncClient(timeout=30) as new,
        httpx2.AsyncClient(timeout=30, cookies=refusing_jar()) as bare,
    ):
        RELAY.clients = {"httpx": old, "httpx2": new, "httpx2-nojar": bare}
        yield


app = FastAPI(lifespan=lifespan)


def client_key(path: str) -> str:
    for prefix, key in PREFIXES.items():
        if path.startswith(f"{prefix}/"):
            return key
    return "httpx"


def begin(request: Request) -> Entry:
    headers: list[tuple[bytes, bytes]] = request.scope["headers"]
    calls: list[Entry] = []
    entry: Entry = {
        "seq": len(LOG),
        "method": request.method,
        "path": request.url.path,
        "client": client_key(request.url.path),
        "tag": request.query_params.get("tag"),
        "headers": [[name.decode("latin-1"), value.decode("latin-1")] for name, value in headers],
        "calls": calls,
    }
    LOG.append(entry)
    return entry


async def call(
    entry: Entry,
    method: str,
    path: str,
    headers: list[tuple[str, str]],
    suffix: str = "",
) -> Answer:
    """Agent OS 를 한 번 부른다. headers 는 이 대역이 더하는 머리 전부다. 주소의 probe 에 붙는 길은
    클라이언트의 이름에 suffix 를 붙인 것이다(`httpx`, `httpx2`, `httpx-raw` …)."""
    client = RELAY.clients.get(str(entry["client"]))
    if client is None:
        raise RuntimeError("클라이언트가 아직 없다")
    answer = await client.request(
        method,
        f"{RELAY.agent_os}{path}",
        params={"probe": f"{entry['tag']}.{entry['client']}{suffix}"},
        headers=headers,
    )
    calls = entry["calls"]
    if isinstance(calls, list):
        calls.append(
            {
                "method": method,
                "path": path,
                "status": answer.status_code,
                "setCookie": answer.headers.get_list("set-cookie"),
            }
        )
    return answer


def cookie_only(cookie: str | None) -> list[tuple[str, str]]:
    return [] if cookie is None else [("cookie", cookie)]


def reason_of(answer: Answer) -> object:
    body = answer.json()
    return body.get("reason") if isinstance(body, dict) else None


def reply(entry: Entry, status: int, body: dict[str, object], lines: list[str]) -> JSONResponse:
    """응답을 짓고 Agent OS 가 낸 `Set-Cookie` 줄을 줄마다 그대로 싣는다."""
    response = JSONResponse(body, status_code=status)
    for line in lines:
        response.raw_headers.append((b"set-cookie", line.encode("latin-1")))
    entry["replied"] = {"status": status, "setCookie": lines}
    return response


def merged(cookie: str | None, lines: list[str]) -> str | None:
    """받은 `Cookie` 머리에 `Set-Cookie` 줄들의 이름과 값을 덮어, 같은 요청 안의 다음 호출에 쓸
    머리를 짓는다."""
    jar: dict[str, str] = {}
    for part in (cookie or "").split("; "):
        name, found, value = part.partition("=")
        if found:
            jar[name] = value
    for line in lines:
        name, _, value = line.split(";", 1)[0].partition("=")
        jar[name] = value
    return "; ".join(f"{name}={value}" for name, value in jar.items()) or None


@app.get("/page")
async def page() -> HTMLResponse:
    return HTMLResponse("<!doctype html><title>login_relay B</title><p>widget admin origin</p>")


@app.get("/d1/data")
async def d1_data(request: Request) -> Response:
    entry = begin(request)
    cookie = request.headers.get("cookie")
    who = await call(entry, "GET", "/auth/me", cookie_only(cookie))
    lines: list[str] = []
    if who.status_code == 401:
        refreshed = await call(entry, "POST", "/auth/refresh", cookie_only(cookie))
        lines = refreshed.headers.get_list("set-cookie")
        if refreshed.status_code != 200:
            body = {"stage": "refresh", "reason": reason_of(refreshed)}
            return reply(entry, refreshed.status_code, body, lines)
        who = await call(entry, "GET", "/auth/me", cookie_only(merged(cookie, lines)))
    if who.status_code != 200:
        return reply(entry, who.status_code, {"stage": "me", "reason": reason_of(who)}, lines)
    return reply(entry, 200, {"account": who.json()["account"], "refreshed": bool(lines)}, lines)


@app.get("/d2/data")
async def d2_data(request: Request) -> Response:
    entry = begin(request)
    who = await call(entry, "GET", "/auth/me", cookie_only(request.headers.get("cookie")))
    # 프로브만 쓴다. Agent OS 에 물은 뒤 답만 늦춘다. 화면의 갱신이 끝난 뒤에 닿는 401 을 만든다.
    late = request.query_params.get("delay_ms")
    if late is not None:
        await asyncio.sleep(float(late) / 1000)
    if who.status_code != 200:
        return reply(entry, who.status_code, {"stage": "me", "reason": reason_of(who)}, [])
    return reply(entry, 200, {"account": who.json()["account"]}, [])


@app.post("/d2/refresh")
async def d2_refresh(request: Request) -> Response:
    entry = begin(request)
    refreshed = await call(
        entry, "POST", "/auth/refresh", cookie_only(request.headers.get("cookie"))
    )
    lines = refreshed.headers.get_list("set-cookie")
    body: dict[str, object] = {"stage": "refresh"}
    if refreshed.status_code != 200:
        body["reason"] = reason_of(refreshed)
    return reply(entry, refreshed.status_code, body, lines)


def verbatim(request: Request) -> list[tuple[str, str]]:
    return [(name, value) for name, value in request.headers.items() if name not in NOT_FORWARDED]


@app.get("/raw/data")
async def raw_data(request: Request) -> Response:
    entry = begin(request)
    who = await call(entry, "GET", "/auth/me", verbatim(request), suffix="-raw")
    if who.status_code != 200:
        return reply(entry, who.status_code, {"stage": "me", "reason": reason_of(who)}, [])
    return reply(entry, 200, {"account": who.json()["account"]}, [])


@app.post("/raw/refresh")
async def raw_refresh(request: Request) -> Response:
    entry = begin(request)
    refreshed = await call(entry, "POST", "/auth/refresh", verbatim(request), suffix="-raw")
    lines = refreshed.headers.get_list("set-cookie")
    body: dict[str, object] = {"stage": "refresh"}
    if refreshed.status_code != 200:
        body["reason"] = reason_of(refreshed)
    return reply(entry, refreshed.status_code, body, lines)


@app.post("/naive/refresh")
async def naive_refresh(request: Request) -> Response:
    """대조. httpx 의 `headers["set-cookie"]` 는 여러 줄을 쉼표로 이은 한 값이다. 그것을 한 머리로
    옮긴다."""
    entry = begin(request)
    refreshed = await call(
        entry,
        "POST",
        "/auth/refresh",
        cookie_only(request.headers.get("cookie")),
        suffix="-naive",
    )
    response = JSONResponse({"stage": "refresh"}, status_code=refreshed.status_code)
    joined = refreshed.headers.get("set-cookie")
    if joined is not None:
        response.headers["set-cookie"] = joined
    entry["replied"] = {"status": refreshed.status_code, "setCookie": [joined]}
    return response


@app.get("/plain-cookie")
async def plain_cookie(request: Request) -> Response:
    entry = begin(request)
    answer = await call(entry, "GET", "/__probe/plain-cookie", [], suffix="-plain")
    return reply(entry, answer.status_code, {"stage": "plain-cookie"}, [])


# 위의 경로를 클라이언트마다 한 벌씩 더 둔다. `/x2/<경로>` 는 httpx2 로, `/x2n/<경로>` 는 쿠키를
# 받지 않는 통을 준 httpx2 로 Agent OS 를 부른다. 처리기는 같다.
for _route in list(app.routes):
    if isinstance(_route, APIRoute):
        for _prefix in PREFIXES:
            app.add_api_route(
                f"{_prefix}{_route.path}", _route.endpoint, methods=sorted(_route.methods)
            )


@app.get("/__probe/health")
async def health() -> dict[str, str]:
    return {
        "role": "widget_admin_stub",
        "httpx": httpx.__version__,
        "httpx2": httpx2.__version__,
    }


@app.get("/__probe/log")
async def log(since: int = 0) -> list[Entry]:
    return LOG[since:]


@app.get("/__probe/state")
async def state() -> dict[str, object]:
    """클라이언트마다 쿠키 통에 든 쿠키의 이름과 속성."""
    return {
        "jars": {
            key: [
                {
                    "name": cookie.name,
                    "domain": cookie.domain,
                    "path": cookie.path,
                    "secure": cookie.secure,
                }
                for cookie in client.cookies.jar
            ]
            for key, client in RELAY.clients.items()
        }
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--agent-os", required=True)
    # 쉬는 연결을 닫기까지의 초. uvicorn 의 기본값은 5 다. 프로브는 길게 준다(까닭은 README).
    parser.add_argument("--keep-alive", type=int, default=5)
    args = parser.parse_args()
    RELAY.agent_os = args.agent_os
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=args.port,
        log_level="warning",
        timeout_keep_alive=args.keep_alive,
    )


if __name__ == "__main__":
    main()
