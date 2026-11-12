"""요청의 모양(질문 1)과 환경 변수(질문 2)의 사례. `openai_compat.py`가 모아 돌린다.

표지는 사례마다 "요청이 가짜 서버에 닿았다"다. 닿은 요청의 경로, 헤더, 본문이 결과다. 환경 변수
사례는 명시한 키로 간 요청이 닿았다는 것까지 보고, 환경을 읽는다는 해석의 양성 대조(키나 주소를
넘기지 않으면 환경의 값이 간다)를 따로 둔다. LangSmith 게이트웨이 변수도 같은 짝으로 본다.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Sequence
from functools import partial

import openai
from fake_server import FakeServer, Received, Reply, completion
from langchain_core.messages import HumanMessage, SystemMessage
from support import (
    KEY,
    KEY_VARIABLE,
    MODEL_ID,
    PROMPT,
    PROMPT_MARK,
    QUERY_SECRET,
    Case,
    Outcome,
    Report,
    authorizations,
    bodies,
    call,
    candidate,
    chat,
    describe,
    environment,
    said,
    targets,
)

CHAT_TARGET = "POST /v1/chat/completions"
WATCHED = (
    "tool_choice",
    "parallel_tool_calls",
    "max_tokens",
    "max_completion_tokens",
    "temperature",
    "stream",
    "stream_options",
    "n",
)
DECOY_KEY = "env-decoy-key-6a1f"
GATEWAY_KEY = "gateway-decoy-key-9c2e"
# 환경 변수 이름 → (넣는 값, 요청에서 찾을 글자)
DECOYS = {
    "OPENAI_ORG_ID": ("org-decoy-11aa", "org-decoy-11aa"),
    "OPENAI_ORGANIZATION": ("org-decoy-66ff", "org-decoy-66ff"),
    "OPENAI_PROJECT_ID": ("proj-decoy-22bb", "proj-decoy-22bb"),
    "OPENAI_ADMIN_KEY": ("admin-decoy-33cc", "admin-decoy-33cc"),
    "OPENAI_WEBHOOK_SECRET": ("whsec-decoy-44dd", "whsec-decoy-44dd"),
    "OPENAI_CUSTOM_HEADERS": ("X-Probe-Decoy: custom-decoy-55ee", "custom-decoy-55ee"),
}
QUIRK_NAMES = (
    "local-model",
    "o1-local",
    "o3-local",
    "gpt-5-local",
    "gpt-5-pro-local",
    "my-codex-model",
)


def _anywhere(_request: Received) -> Reply:
    """경로를 가리지 않고 글 응답을 준다. 요청이 어느 경로로 왔는지만 보려는 사례가 쓴다."""
    return completion()


def _mentions(servers: Sequence[FakeServer], needle: str) -> list[str]:
    return sorted(
        {
            place
            for server in servers
            for request in server.requests
            for place in request.mentions(needle)
        }
    )


async def _path(suffix: str, *, v1: bool = True, query: bool = False) -> Report:
    with FakeServer(_anywhere) if query else FakeServer() as server:
        base = (server.base_url if v1 else server.origin) + suffix
        outcome = await call(chat(base), tools=False)
    seen = targets(server)
    return Report(
        measured=len(seen) >= 1,
        result=" | ".join(seen),
        data={
            "base_url": base.replace(server.origin, "http://127.0.0.1:<port>"),
            "requests": seen,
            "text": said(outcome),
            "error": describe(outcome.error, query=QUERY_SECRET),
        },
    )


def _body_view(body: dict[str, object]) -> dict[str, object]:
    return {
        "keys": sorted(body),
        "absent": [name for name in WATCHED if name not in body],
        "body": body,
    }


async def body_with_tools() -> Report:
    with FakeServer() as server:
        await call(chat(server.base_url))
    seen = bodies(server)
    body = seen[0] if seen else {}
    tools = body.get("tools")
    marked = PROMPT_MARK in json.dumps(body, ensure_ascii=False)
    return Report(
        measured=len(seen) == 1 and isinstance(tools, list) and len(tools) == 1 and marked,
        result="본문의 키: " + " ".join(sorted(body)),
        data=_body_view(body),
    )


async def body_without_tools() -> Report:
    with FakeServer() as server:
        await call(chat(server.base_url), tools=False)
    seen = bodies(server)
    body = seen[0] if seen else {}
    return Report(
        measured=len(seen) == 1 and PROMPT_MARK in json.dumps(body, ensure_ascii=False),
        result="본문의 키: " + " ".join(sorted(body)),
        data=_body_view(body),
    )


async def body_with_options() -> Report:
    """`max_completion_tokens`(별칭)로 준 것과 `max_tokens`(칸 이름)로 준 것이 어느 키로 가는지."""
    with FakeServer() as server:
        await call(chat(server.base_url, max_completion_tokens=256, temperature=0.2), tools=False)
        await call(chat(server.base_url, max_tokens=256, temperature=0.2), tools=False)
    seen = bodies(server)
    names = [sorted(key for key, value in body.items() if value in (256, 0.2)) for body in seen]
    return Report(
        measured=len(seen) == 2 and all(len(found) == 2 for found in names),
        result=" / ".join(" ".join(found) for found in names),
        data={"given": ["max_completion_tokens=256", "max_tokens=256"], "bodies": seen},
    )


async def authorization_header() -> Report:
    with FakeServer() as server:
        outcome = await call(chat(server.base_url), tools=False)
    sent = authorizations(server)
    headers = [list(pair) for request in server.requests for pair in request.headers]
    return Report(
        measured=len(sent) == 1 and said(outcome) == "pong",
        result=" | ".join(sent),
        data={"authorization": sent, "headers": headers},
    )


async def _route(model_id: str, *, version: str | None = None, **options: object) -> Report:
    """요청이 Chat Completions 로 가는지 Responses 로 가는지. `version`은 환경의 출력 판이다."""
    with FakeServer() as server, environment(LC_OUTPUT_VERSION=version):
        outcome = await call(chat(server.base_url, model=model_id, **options), tools=False)
    return _route_report(server, outcome, {"model": model_id, "LC_OUTPUT_VERSION": version})


async def route_candidate_env_version() -> Report:
    with FakeServer() as server, environment(LC_OUTPUT_VERSION="responses/v1"):
        outcome = await call(candidate(server.base_url), tools=False)
    return _route_report(server, outcome, {"model": MODEL_ID, "LC_OUTPUT_VERSION": "responses/v1"})


def _route_report(server: FakeServer, outcome: Outcome, given: dict[str, object]) -> Report:
    seen = targets(server)
    content = None if outcome.message is None else outcome.message.content
    return Report(
        measured=len(seen) >= 1,
        result=" | ".join(sorted(set(seen))),
        data={**given, "requests": seen, "content": content, "error": describe(outcome.error)},
    )


async def model_name_quirks() -> Report:
    """모델 이름의 머리에 따라 라이브러리가 요청을 바꾸는지. `use_responses_api=False`는 준 채다."""
    rows: list[dict[str, object]] = []
    messages = [SystemMessage("지시"), HumanMessage(PROMPT)]
    with FakeServer() as server:
        for name in QUIRK_NAMES:
            for temperature in (None, 0.2):
                before = len(server.requests)
                model = chat(
                    server.base_url, model=name, temperature=temperature, use_responses_api=False
                )
                outcome = await call(model, tools=False, messages=messages)
                rows.append(_quirk_row(name, temperature, server.requests[before:], outcome))
    odd = [row for row in rows if row["odd"]]
    return Report(
        measured=all(row["requests"] == 1 for row in rows),
        result="; ".join(f"{row['model']}({row['given']}): {row['odd']}" for row in odd)
        or "이름에 따라 달라지지 않았다",
        data={"rows": rows},
    )


def _quirk_row(
    name: str, given: float | None, requests: Sequence[Received], outcome: Outcome
) -> dict[str, object]:
    body = (requests[0].json() or {}) if requests else {}
    sent = body.get("temperature", "(없음)")
    messages = body.get("messages")
    first = messages[0] if isinstance(messages, list) and messages else {}
    role = first.get("role") if isinstance(first, dict) else None
    target = f"{requests[0].method} {requests[0].target}" if requests else None
    odd: list[str] = []
    if sent != (given if given is not None else "(없음)"):
        odd.append(f"temperature={sent}")
    if role != "system":
        odd.append(f"role={role}")
    if target != CHAT_TARGET:
        odd.append(f"target={target}")
    return {
        "model": name,
        "given": given,
        "requests": len(requests),
        "target": target,
        "temperature": sent,
        "first_role": role,
        "odd": " ".join(odd),
        "error": describe(outcome.error),
    }


async def env_explicit_wins() -> Report:
    """환경에 키와 주소가 있어도 명시한 키와 주소로만 간다."""
    with FakeServer() as server, FakeServer() as decoy:
        env = {
            "OPENAI_API_KEY": DECOY_KEY,
            "OPENAI_BASE_URL": decoy.base_url,
            "OPENAI_API_BASE": decoy.base_url,
        }
        with environment(**env):
            await call(chat(server.base_url), tools=False)
    sent = authorizations(server)
    found = _mentions([server, decoy], DECOY_KEY)
    return Report(
        measured=sent == [f"Bearer {KEY}"],
        result="환경의 값이 갔다" if found or decoy.requests else "환경의 값이 가지 않았다",
        data={
            "authorization": sent,
            "decoy_key_in": found,
            "decoy_server_requests": targets(decoy),
            "header_names": sorted(
                name for request in server.requests for name, _ in request.headers
            ),
        },
    )


async def env_key_used_when_omitted() -> Report:
    """양성 대조. 키를 넘기지 않으면 환경의 `OPENAI_API_KEY`가 간다."""
    with FakeServer() as server, environment(OPENAI_API_KEY=DECOY_KEY):
        await call(chat(server.base_url, api_key=None), tools=False)
    sent = authorizations(server)
    return Report(
        measured=len(sent) == 1,
        result="환경의 키가 갔다" if sent == [f"Bearer {DECOY_KEY}"] else f"다른 값이 갔다 {sent}",
        data={"authorization": sent},
    )


async def _env_url(variable: str) -> Report:
    """양성 대조. 주소를 넘기지 않으면 환경의 주소로 간다.

    만든 클라이언트의 주소가 가짜 서버가 아니면 부르지 않는다. 실제 서버로 요청이 나가지 않게 한다.
    """
    with FakeServer() as decoy, environment(**{variable: decoy.base_url}):
        model = chat(None)
        aimed = str(model.root_async_client.base_url)
        if not aimed.startswith(decoy.origin):
            shown = {"variable": variable, "aimed": aimed}
            return Report(measured=False, result="요청을 보내지 않았다", data=shown)
        await call(model, tools=False)
    return Report(
        measured=len(decoy.requests) >= 1,
        result="환경의 주소로 갔다 " + " | ".join(targets(decoy)),
        data={"variable": variable, "requests": targets(decoy)},
    )


async def env_gateway_explicit_wins() -> Report:
    """환경에 LangSmith 게이트웨이의 주소와 키가 있어도 명시한 키와 주소로만 간다."""
    with FakeServer() as server, FakeServer(_anywhere) as decoy:
        env = {"LANGSMITH_GATEWAY": decoy.origin, "LANGSMITH_GATEWAY_API_KEY": GATEWAY_KEY}
        with environment(**env):
            await call(chat(server.base_url), tools=False)
    sent = authorizations(server)
    found = _mentions([server, decoy], GATEWAY_KEY)
    return Report(
        measured=sent == [f"Bearer {KEY}"],
        result="환경의 값이 갔다" if found or decoy.requests else "환경의 값이 가지 않았다",
        data={
            "authorization": sent,
            "gateway_key_in": found,
            "gateway_requests": targets(decoy),
        },
    )


async def env_gateway_used_when_omitted() -> Report:
    """양성 대조. 키와 주소를 넘기지 않으면 게이트웨이 변수의 주소와 키로 간다.

    만든 클라이언트의 주소가 가짜 서버가 아니면 부르지 않는다. 실제 게이트웨이로 요청이 나가지 않게
    한다.
    """
    with FakeServer(_anywhere) as decoy:
        env = {"LANGSMITH_GATEWAY": decoy.origin, "LANGSMITH_GATEWAY_API_KEY": GATEWAY_KEY}
        with environment(**env):
            model = chat(None, api_key=None)
            aimed = str(model.root_async_client.base_url)
            if not aimed.startswith(decoy.origin):
                return Report(measured=False, result="요청을 보내지 않았다", data={"aimed": aimed})
            await call(model, tools=False)
    sent = authorizations(decoy)
    return Report(
        measured=len(decoy.requests) >= 1,
        result="게이트웨이 변수의 주소로 갔다 " + " | ".join(targets(decoy)),
        data={"requests": targets(decoy), "authorization": sent},
    )


async def _env_identity(*, guarded: bool, names: Sequence[str] = tuple(DECOYS)) -> Report:
    """명시한 키와 주소로 부를 때 환경의 다른 OpenAI 변수가 요청에 실리는지.

    `names`를 주면 그 변수만 심는다. `OPENAI_ORGANIZATION`은 `OPENAI_ORG_ID`와 함께 심으면 가려져
    따로 본다.
    """
    values = {name: DECOYS[name][0] for name in names}
    with FakeServer() as server, environment(**values):
        model = candidate(server.base_url) if guarded else chat(server.base_url)
        await call(model, tools=False)
    found = {name: _mentions([server], DECOYS[name][1]) for name in names}
    carried = [f"{name}→{','.join(places)}" for name, places in found.items() if places]
    return Report(
        measured=authorizations(server) == [f"Bearer {KEY}"],
        result="실린 변수: " + (" ".join(carried) or "없음"),
        data={"found": found, "authorization": authorizations(server)},
    )


async def _proxy(variable: str, *, guarded: bool = False) -> Report:
    """프록시 환경 변수를 가짜 서버로 두고 요청이 어디로 가는지."""
    with FakeServer() as server, FakeServer() as proxy:
        with environment(**{variable: proxy.origin}):
            model = candidate(server.base_url) if guarded else chat(server.base_url)
            outcome = await call(model, tools=False)
    return Report(
        measured=len(server.requests) + len(proxy.requests) >= 1,
        result="프록시로 갔다" if proxy.requests else "곧바로 갔다",
        data={
            "variable": variable,
            "server": targets(server),
            "proxy": [t.replace(server.origin, "http://127.0.0.1:<port>") for t in targets(proxy)],
            "proxy_saw_key": bool(_mentions([proxy], KEY)),
            "error": describe(outcome.error),
        },
    )


def _client_view(model: object) -> dict[str, object]:
    client = getattr(model, "root_async_client", None)
    return {
        "sdk_max_retries": getattr(client, "max_retries", "(없음)"),
        "sdk_timeout": repr(getattr(client, "timeout", "(없음)")),
        "max_retries": getattr(model, "max_retries", "(없음)"),
        "request_timeout": repr(getattr(model, "request_timeout", "(없음)")),
        "streaming": getattr(model, "streaming", "(없음)"),
        "disable_streaming": getattr(model, "disable_streaming", "(없음)"),
        "use_responses_api": getattr(model, "use_responses_api", "(없음)"),
        "output_version": getattr(model, "output_version", "(없음)"),
        "openai_proxy": getattr(model, "openai_proxy", "(없음)"),
    }


async def client_defaults() -> Report:
    """키도 서버도 없이 만들 수 있는지와, 만든 클라이언트의 재시도 횟수와 타임아웃 기본값."""
    unused = "http://127.0.0.1:9/v1"
    with environment(OPENAI_PROXY="http://127.0.0.1:9", LC_OUTPUT_VERSION="responses/v1"):
        views = {
            "plain": _client_view(chat(unused)),
            "candidate": _client_view(candidate(unused, key=None)),
        }
    plain = views["plain"]
    return Report(
        measured=plain["sdk_max_retries"] != "(없음)" and plain["sdk_timeout"] != "'(없음)'",
        result=f"max_retries={plain['sdk_max_retries']} timeout={plain['sdk_timeout']}",
        data={"variable": KEY_VARIABLE, **views},
    )


async def _two_loops(kind: str) -> Report:
    """같은 주소로 이벤트 루프 둘에서 차례로 부른다. 모델은 core 처럼 부를 때마다 새로 만든다.

    `shared`는 손대지 않은 `ChatOpenAI`(주소별로 캐시한 httpx 클라이언트를 나눠 쓴다), `own`은
    모델마다 httpx 클라이언트를 따로 준 것, `candidate`는 후보다. `own`이 되면 `shared`의 실패는
    나눠 쓰는 클라이언트 때문이라는 갈래다. 같은 루프 안의 두 번째 호출이 되는 것은
    `key_function_per_request`가 보인다.
    """
    with FakeServer() as server:
        rows = await asyncio.to_thread(_twice, server.base_url, kind)
        seen = targets(server)
    first, second = rows
    return Report(
        measured=first["text"] == "pong" and len(seen) >= 1,
        result="둘째 루프도 됐다" if second["text"] == "pong" else "둘째 루프가 실패했다",
        data={"kind": kind, "rows": rows, "requests": seen},
    )


def _twice(base_url: str, kind: str) -> list[dict[str, object]]:
    return [asyncio.run(_once(base_url, kind)) for _ in range(2)]


async def _once(base_url: str, kind: str) -> dict[str, object]:
    if kind == "candidate":
        model = candidate(base_url)
    elif kind == "own":
        model = chat(base_url, http_async_client=openai.DefaultAsyncHttpxClient())
    else:
        model = chat(base_url)
    outcome = await call(model, tools=False)
    return {"text": said(outcome), "error": describe(outcome.error), "seconds": outcome.seconds}


CASES: dict[str, Case] = {
    "path_plain": partial(_path, ""),
    "path_trailing_slash": partial(_path, "/"),
    "path_without_v1": partial(_path, "", v1=False),
    "path_with_query": partial(_path, f"?probe_token={QUERY_SECRET}", query=True),
    "path_with_fragment": partial(_path, "#probe-fragment", query=True),
    "body_with_tools": body_with_tools,
    "body_without_tools": body_without_tools,
    "body_with_options": body_with_options,
    "authorization_header": authorization_header,
    "route_plain": partial(_route, MODEL_ID),
    "route_off": partial(_route, MODEL_ID, use_responses_api=False),
    "route_pro_name_auto": partial(_route, "gpt-5-pro-local"),
    "route_pro_name_off": partial(_route, "gpt-5-pro-local", use_responses_api=False),
    "route_codex_name_auto": partial(_route, "my-codex-model"),
    "route_codex_name_off": partial(_route, "my-codex-model", use_responses_api=False),
    "route_env_version_auto": partial(_route, MODEL_ID, version="responses/v1"),
    "route_env_version_off": partial(
        _route, MODEL_ID, version="responses/v1", use_responses_api=False
    ),
    "route_candidate_env_version": route_candidate_env_version,
    "model_name_quirks": model_name_quirks,
    "env_explicit_wins": env_explicit_wins,
    "env_key_used_when_omitted": env_key_used_when_omitted,
    "env_base_url_used_when_omitted": partial(_env_url, "OPENAI_BASE_URL"),
    "env_api_base_used_when_omitted": partial(_env_url, "OPENAI_API_BASE"),
    "env_identity_headers": partial(_env_identity, guarded=False),
    "env_identity_headers_candidate": partial(_env_identity, guarded=True),
    "env_legacy_org_alone": partial(_env_identity, guarded=False, names=("OPENAI_ORGANIZATION",)),
    "env_gateway_explicit_wins": env_gateway_explicit_wins,
    "env_gateway_used_when_omitted": env_gateway_used_when_omitted,
    "env_openai_proxy": partial(_proxy, "OPENAI_PROXY"),
    "env_openai_proxy_candidate": partial(_proxy, "OPENAI_PROXY", guarded=True),
    "env_http_proxy": partial(_proxy, "HTTP_PROXY"),
    "env_http_proxy_candidate": partial(_proxy, "HTTP_PROXY", guarded=True),
    "client_defaults": client_defaults,
    "two_loops_same_url": partial(_two_loops, "shared"),
    "two_loops_own_client": partial(_two_loops, "own"),
    "two_loops_candidate": partial(_two_loops, "candidate"),
}
