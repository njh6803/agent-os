"""실패가 호출한 쪽에 닿는 모양(질문 6)의 사례. 손대지 않은 `ChatOpenAI`를 루프와 같은 길로 부른다.

표지: 상태 코드 사례는 요청이 닿았고 올라온 예외가 그 상태 코드를 들었다. 닫힌 포트 사례는 예외의
원인 사슬에 전송 층의 접속 오류(`ConnectError`)가 있다. 200 인데 본문이 이상한 사례는 요청이 닿았다.
가짜 서버는 받은 키를 오류 글에 되울린다. 그래서 글에 키가 있는지가 곧 서버가 되울린 글이 예외에
실리는지다.
"""

from __future__ import annotations

from functools import partial

from fake_server import FakeServer, Responder, closed_port
from support import (
    KEY,
    QUERY_SECRET,
    USER_BASIC,
    USER_PASSWORD,
    Case,
    Collector,
    CountingKey,
    Report,
    authorizations,
    call,
    chat,
    debug_logs,
    describe,
    echo,
    leaked,
    links,
    ok_error_body,
    ok_not_json,
    ok_null_choices,
    qualified,
    targets,
    with_userinfo,
)

QUERY = f"?probe_token={QUERY_SECRET}"


def _retry_lines(logs: Collector) -> int:
    """openai SDK 가 다시 시도한다고 남긴 로그 줄의 수."""
    return sum("Retrying request" in record.getMessage() for record in logs.records)


async def _status(status: int, *, function: bool = False, query: bool = False) -> Report:
    key = CountingKey(value=KEY)
    with FakeServer(echo(status)) as server, debug_logs() as logs:
        base = server.base_url + (QUERY if query else "")
        outcome = await call(chat(base, api_key=key if function else KEY))
    error = outcome.error
    origin = server.origin.removeprefix("http://")
    code = getattr(error, "status_code", None)
    kind = "예외 없음" if error is None else qualified(type(error))
    return Report(
        measured=len(server.requests) >= 1 and code == status,
        result=f"{kind} 요청 {len(server.requests)}건 키 {leaked(error, KEY)}",
        data={
            "status": status,
            "error": describe(error, key=KEY, origin=origin, query=QUERY_SECRET),
            "requests": [t.replace(QUERY_SECRET, "<쿼리>") for t in targets(server)],
            "query_reached_server": any(QUERY_SECRET in t for t in targets(server)),
            "retry_log_lines": _retry_lines(logs),
            "key_function_calls": key.calls,
            "seconds": outcome.seconds,
        },
    )


async def _closed(*, query: bool = False) -> Report:
    origin = f"127.0.0.1:{closed_port()}"
    with debug_logs() as logs:
        outcome = await call(chat(f"http://{origin}/v1" + (QUERY if query else "")))
    error = outcome.error
    kinds = [] if error is None else [qualified(type(found)) for _, found in links(error)]
    kind = "예외 없음" if error is None else qualified(type(error))
    return Report(
        measured=any("ConnectError" in name for name in kinds),
        result=f"{kind} 주소 {leaked(error, origin)} 쿼리 {leaked(error, QUERY_SECRET)}",
        data={
            "error": describe(error, key=KEY, origin=origin, query=QUERY_SECRET),
            "retry_log_lines": _retry_lines(logs),
            "seconds": outcome.seconds,
        },
    )


async def userinfo_url_401() -> Report:
    """주소에 사용자 정보(`user:암호@`)가 있을 때 서버가 받는 인증 헤더와 예외 글."""
    with FakeServer(echo(401)) as server:
        outcome = await call(chat(with_userinfo(server.base_url)))
    error = outcome.error
    sent = authorizations(server)
    return Report(
        measured=len(sent) >= 1 and error is not None,
        result=f"받은 인증 헤더의 머리 {[value.split(' ')[0] for value in sent]}, "
        f"예외의 암호 {leaked(error, USER_PASSWORD)}, base64 꼴 {leaked(error, USER_BASIC)}",
        data={
            "authorization": sent,
            "error": describe(error, key=KEY, password=USER_PASSWORD, basic=USER_BASIC),
        },
    )


async def _odd_body(responder: Responder) -> Report:
    """상태는 200 인데 본문이 Chat Completions 응답이 아닐 때."""
    with FakeServer(responder) as server:
        outcome = await call(chat(server.base_url))
    error = outcome.error
    kind = "예외 없음" if error is None else qualified(type(error))
    return Report(
        measured=len(server.requests) >= 1,
        result=f"{kind} 요청 {len(server.requests)}건 키 {leaked(error, KEY)}",
        data={
            "error": describe(error, key=KEY),
            "requests": len(server.requests),
            "seconds": outcome.seconds,
        },
    )


CASES: dict[str, Case] = {
    "fail_401_echo_string": partial(_status, 401),
    "fail_401_echo_function": partial(_status, 401, function=True),
    "fail_400": partial(_status, 400),
    "fail_404": partial(_status, 404),
    "fail_429": partial(_status, 429),
    "fail_500": partial(_status, 500),
    "fail_closed_port": _closed,
    "query_url_401": partial(_status, 401, query=True),
    "query_url_closed_port": partial(_closed, query=True),
    "userinfo_url_401": userinfo_url_401,
    "ok_status_error_body": partial(_odd_body, ok_error_body),
    "ok_status_not_json": partial(_odd_body, ok_not_json),
    "ok_status_null_choices": partial(_odd_body, ok_null_choices),
}
