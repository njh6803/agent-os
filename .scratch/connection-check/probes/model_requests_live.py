"""실제 Anthropic Models API가 접속 확인의 요청에 어떻게 답하는지.

ADR 0067의 결정 "모델을 확인하는 법"이 프로브로 보라고 남긴 것 가운데 실제 제공사가 있어야 보이는
것을 잰다. 모델 파일의 `model_id`를 하나만 묻는 요청이 그 id를 받는지, 날짜를 뗀 이름도 받는지, 없는
id와 틀린 키가 어떤 상태로 갈리는지, 목록이 한 쪽에 다 오는지와 날짜를 뗀 이름이 목록에 실리는지,
응답 본문에 쓴 양(`usage`)이 실리는지를 본다.

바깥에 닿는다. `https://api.anthropic.com`에 GET 요청만 보내고 모델은 부르지 않는다(토큰을 쓰는
요청이 없다). 키는 SDK가 환경 변수 `ANTHROPIC_API_KEY`에서 읽고, 이 프로브는 그 값을 찍지 않는다.
이 프로브가 그 값을 읽는 자리는 하나다. 출력에 싣는 예외의 글에 그 값이 들어 있으면 `<가린 키>`로
바꾼다(서버가 받은 키를 오류 글에 되울리는 경우를 막는다). 주소는 환경의 `ANTHROPIC_BASE_URL`을
따르지 않게 인자로 못박는다. 틀린 키 회차는 지어낸 글자(`sk-ant-probe-…`)를 보낸다. 모델
서버(`openai-compatible`)는 띄워야 해서 여기서 보지 않는다.

회차와 표지:
- `retrieve_plugin_id`: `plugins/models/claude-opus-5/plugin.toml`의 `model_id`를 묻는다. 표지는
  응답 상태가 200이고 돌려받은 id가 비지 않은 것이다.
- `list_default`, `list_1000`: 목록의 첫 쪽. 표지는 한 개 이상이 온 것이다.
- `retrieve_alias`: 목록에서 고른 날짜 붙은 id에서 날짜를 뗀 이름을 묻는다. 표지는 그런 id가
  목록에 있어 물었고, 날짜를 뗀 그 이름은 목록에 없으며, 답이 200이거나 404인 것이다.
- `retrieve_unknown`: 없는 id. 표지는 `anthropic.NotFoundError`로 끝난 것이다.
- `bad_key`: 지어낸 키. 표지는 `anthropic.AuthenticationError`로 끝난 것이다.

표지가 없는 회차가 하나라도 있으면 1로 끝난다(`tools/probe_kit.py`의 `Rounds`). 키가 없으면 아무
요청도 보내지 않고 2로 끝난다.

    uv run --env-file ../../../.env python .scratch/connection-check/probes/model_requests_live.py
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import time
import tomllib
from importlib.metadata import version
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.probe_kit import Rounds  # noqa: E402

API = "https://api.anthropic.com"
KEY_VARIABLE = "ANTHROPIC_API_KEY"
PLUGIN_FILE = ROOT / "plugins" / "models" / "claude-opus-5" / "plugin.toml"
UNKNOWN = "agent-os-probe-no-such-model"
NOT_A_KEY = "sk-ant-probe-not-a-real-key"
KEY_HIDDEN = "<가린 키>"
DATED = re.compile(r"-\d{8}$")
CALL_TIMEOUT = 30.0
SHOWN_HEADERS = ("anthropic-", "retry-after", "request-id", "x-ratelimit")


def plugin_model_id() -> str:
    value = tomllib.loads(PLUGIN_FILE.read_text(encoding="utf-8")).get("model_id")
    if not isinstance(value, str):
        raise TypeError(f"{PLUGIN_FILE} 에 model_id 가 없다")
    return value


def emit(case: str, **data: object) -> None:
    print(json.dumps({"case": case, **data}, ensure_ascii=False, default=repr), flush=True)


def client_for(key: str | None) -> anthropic.AsyncAnthropic:
    """재시도 없는 클라이언트. 키가 없으면 SDK가 환경에서 읽게 둔다."""
    if key is None:
        return anthropic.AsyncAnthropic(base_url=API, max_retries=0, timeout=CALL_TIMEOUT)
    return anthropic.AsyncAnthropic(api_key=key, base_url=API, max_retries=0, timeout=CALL_TIMEOUT)


def without_key(text: str) -> str:
    """글에서 환경의 키 값을 가린다. 서버가 받은 키를 글에 되울려도 출력에 남지 않게 한다."""
    key = os.environ.get(KEY_VARIABLE)
    return text.replace(key, KEY_HIDDEN) if key else text


async def failure(client: anthropic.AsyncAnthropic, model_id: str) -> dict[str, object]:
    """그 id를 물어 끝난 모양. 예외의 글은 서버의 글이라 키를 가린 뒤 앞부분만 싣는다."""
    started = time.perf_counter()
    try:
        found = await client.models.retrieve(model_id)
    except anthropic.APIStatusError as error:
        return {
            "error": type(error).__name__,
            "status": error.status_code,
            "text": without_key(str(error))[:200],
            "seconds": round(time.perf_counter() - started, 2),
        }
    return {"error": None, "returned": found.id}


async def measure(rounds: Rounds) -> None:
    plugin_id = plugin_model_id()
    emit(
        "setup",
        api=API,
        plugin_id=plugin_id,
        sdk=version("anthropic"),
        base_url_variable_set="ANTHROPIC_BASE_URL" in os.environ,
    )
    alias: str | None = None
    dated: str | None = None
    more_pages = True  # 목록의 첫 쪽이 끝이라고 알기 전에는 부재를 확정하지 않는다
    async with client_for(None) as client:
        with rounds.round("retrieve_plugin_id") as current:
            started = time.perf_counter()
            raw = await client.models.with_raw_response.retrieve(plugin_id)
            seconds = round(time.perf_counter() - started, 2)
            found = await raw.parse()
            body = raw.http_response.json()
            emit(
                "retrieve_plugin_id",
                status=raw.status_code,
                asked=plugin_id,
                returned=found.id,
                display_name=found.display_name,
                body_keys=sorted(body) if isinstance(body, dict) else None,
                headers=sorted(name for name in raw.headers if name.startswith(SHOWN_HEADERS)),
                seconds=seconds,
            )
            usage = "있음" if isinstance(body, dict) and "usage" in body else "없음"
            current.mark(
                measured=raw.status_code == 200 and bool(found.id),
                result=f"{plugin_id} → {found.id}, 본문에 usage {usage}, {seconds}초",
            )

        with rounds.round("list_default") as current:
            page = await client.models.list()
            emit("list_default", count=len(page.data), has_more=page.has_more)
            current.mark(
                measured=len(page.data) >= 1,
                result=f"기본 한 쪽에 {len(page.data)}개, has_more {page.has_more}",
            )

        with rounds.round("list_1000") as current:
            page = await client.models.list(limit=1000)
            ids = [model.id for model in page.data]
            more_pages = page.has_more
            dated = next((one for one in ids if DATED.search(one)), None)
            alias = DATED.sub("", dated) if dated else None
            emit(
                "list_1000",
                count=len(ids),
                has_more=page.has_more,
                ids=ids,
                plugin_id_listed=plugin_id in ids,
                dated=dated,
                alias=alias,
                alias_listed=alias in ids if alias else None,
            )
            listed = "있음" if plugin_id in ids else "없음"
            current.mark(
                measured=len(ids) >= 1,
                result=f"limit=1000 한 쪽에 {len(ids)}개, has_more {page.has_more}, "
                f"모델 파일의 id는 목록에 {listed}",
            )

        with rounds.round("retrieve_alias") as current:
            if alias is None:
                emit("retrieve_alias", skipped="목록에 날짜 붙은 id가 없다")
            else:
                outcome = await failure(client, alias)
                emit(
                    "retrieve_alias", asked=alias, dated=dated, alias_listed=alias in ids, **outcome
                )
                answer = outcome.get("returned") or outcome.get("status")
                current.mark(
                    measured=not more_pages
                    and alias not in ids
                    and (outcome["error"] is None or outcome.get("status") == 404),
                    result=f"{alias} → {answer}, 그 이름은 목록에 "
                    f"{'있음' if alias in ids else '없음'}",
                )

        with rounds.round("retrieve_unknown") as current:
            outcome = await failure(client, UNKNOWN)
            emit("retrieve_unknown", asked=UNKNOWN, **outcome)
            current.mark(
                measured=outcome["error"] == "NotFoundError",
                result=f"없는 id는 {outcome.get('status')} {outcome['error']}",
            )

    with rounds.round("bad_key") as current:
        async with client_for(NOT_A_KEY) as wrong:
            outcome = await failure(wrong, plugin_id)
        emit("bad_key", **outcome)
        current.mark(
            measured=outcome["error"] == "AuthenticationError",
            result=f"틀린 키는 {outcome.get('status')} {outcome['error']}",
        )


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    if not os.environ.get(KEY_VARIABLE):
        print(f"환경 변수 {KEY_VARIABLE} 가 없다. 요청을 보내지 않았다.", file=sys.stderr)
        return 2
    rounds = Rounds()
    asyncio.run(measure(rounds))
    print(without_key(rounds.summary()))
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
