"""DEBUG 로그에 키와 프롬프트가 실리는지(질문 8)의 사례.

루트 로거를 DEBUG 로 두고 모든 레코드를 모은 채 키가 든 모델을 한 번 부른다. 레코드마다 로그에
찍힐 글(예외 정보의 트레이스백까지)에서 키 값, `Bearer `, 프롬프트, 서버 주소를 찾는다.

표지 셋. 찾는 방법이 듣는다(같은 수집기에 키와 프롬프트가 든 레코드를 일부러 하나 내고 그것을
찾는다). 서버가 그 키가 든 인증 헤더를 받았다. 서버가 받은 본문에 프롬프트가 있다. 셋이 다 있어야
"로그에 없다"가 "애초에 보내지 않았다"나 "찾지 못했다"와 갈린다.

사례가 고른 갈래가 실제로 났다는 표지 둘을 더 본다. 호출이 그 갈래대로 끝났다(성공 갈래는 메시지가
돌아왔고, 상태 코드 갈래는 예외의 글이 그 코드를 든다. 다른 까닭으로 끝난 호출의 로그를 그 갈래의
로그로 세지 않는다). 쿼리 갈래는 서버가 받은 요청 줄에 그 쿼리가 있다(쿼리가 가지 않았으면 "로그에
쿼리가 없다"가 "애초에 보내지 않았다"와 갈리지 않는다).
"""

from __future__ import annotations

import json
import logging
from functools import partial

from fake_server import FakeServer, default_responder
from support import (
    KEY,
    PROMPT_MARK,
    QUERY_SECRET,
    Case,
    Report,
    authorizations,
    bodies,
    call,
    candidate,
    chat,
    clip,
    debug_logs,
    describe,
    echo,
    rendered,
    targets,
)

SELF_TEST = "probe.selftest"
SHOWN_LINES = 14


async def _logged(*, guarded: bool, status: int | None, query: bool = False) -> Report:
    """`query`면 주소에 쿼리 문자열을 붙인다. 그 주소가 로그에 실리는지를 본다."""
    responder = default_responder if status is None else echo(status)
    with FakeServer(responder) as server, debug_logs() as logs:
        logging.getLogger(SELF_TEST).debug("Authorization: Bearer %s %s", KEY, PROMPT_MARK)
        base = server.base_url + (f"?probe_token={QUERY_SECRET}" if query else "")
        model = candidate(base) if guarded else chat(base)
        outcome = await call(model)
    lines = [(record.name, rendered(record)) for record in logs.records]
    planted = " ".join(text for name, text in lines if name == SELF_TEST)
    library = [(name, text) for name, text in lines if name != SELF_TEST]
    needles = {
        "key": KEY,
        "bearer": "Bearer ",
        "prompt": PROMPT_MARK,
        "origin": server.origin.removeprefix("http://"),
        "query": QUERY_SECRET,
    }
    hits = {
        label: sorted({name for name, text in library if needle in text})
        for label, needle in needles.items()
    }
    loggers: dict[str, list[str]] = {}
    for name, text in library:
        loggers.setdefault(name, []).append(clip(text, 260))
    sent_prompt = any(
        PROMPT_MARK in json.dumps(body, ensure_ascii=False) for body in bodies(server)
    )
    found = {label: "있음" if names else "없음" for label, names in hits.items()}
    if status is None:
        ended_as_chosen = outcome.message is not None
    else:
        ended_as_chosen = f"Error code: {status}" in str(outcome.error)
    sent_query = any(QUERY_SECRET in target for target in targets(server))
    return Report(
        measured=KEY in planted
        and PROMPT_MARK in planted
        and f"Bearer {KEY}" in authorizations(server)
        and sent_prompt
        and ended_as_chosen
        and (sent_query or not query),
        result=(
            f"로그 {len(library)}줄, 키 {found['key']}, Bearer {found['bearer']}, "
            f"프롬프트 {found['prompt']}, 주소 {found['origin']}"
            + (f", 쿼리 {found['query']}" if query else "")
        ),
        data={
            "hits": hits,
            "loggers": {
                name: {"count": len(texts), "lines": texts[:SHOWN_LINES]}
                for name, texts in loggers.items()
            },
            "error": describe(outcome.error, key=KEY),
            "requests": len(server.requests),
        },
    )


CASES: dict[str, Case] = {
    "logs_success_candidate": partial(_logged, guarded=True, status=None),
    "logs_success_plain": partial(_logged, guarded=False, status=None),
    "logs_401_candidate": partial(_logged, guarded=True, status=401),
    "logs_401_plain": partial(_logged, guarded=False, status=401),
    "logs_401_query_url": partial(_logged, guarded=True, status=401, query=True),
}
