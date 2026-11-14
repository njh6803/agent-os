"""실제로 뜬 모델 서버 둘에 도구가 든 요청을 보내 `tool_calls`로 답하는지 본다(티켓 03 "띄워
확인하는 것").

`tools/llm_local.py run --yes -- uv run python .scratch/local-model/probes/live_tool_call.py`의 `--`
뒤에 넣는 자식 프로세스다. 모델 서버의 주소·모델 이름·키는 그 명령이 넘기는 환경 변수 여섯
(`AGENT_OS_LLM_LOCAL_<n>_BASE_URL`·`_MODEL_ID`·`_API_KEY`, n은 1과 2)에서 읽고, 키는 어디에도 찍지
않는다. 표준 라이브러리와 `tools/probe_kit.py`(`Rounds`)만 쓴다.

회차는 모델마다 하나다. 요청은 Chat Completions(`POST <주소>/chat/completions`)에 도구 하나
(`get_weather`)를 싣고 `tool_choice`는 `auto`다. 재려는 상황은 "서버가 200으로 JSON 답을 냈다"이고,
그 표지(`choices`가 배열로 든 200 응답)를 본 회차만 측정이다. 답이 `tool_calls`인지 글인지는 측정의
결과(`tool_calls`, `글로만 답함`)이지 표지가 아니다. 연결이 안 되거나 200이 아니거나 환경 변수가
없으면 측정이 아니라 세고 종료 코드가 1이다(`tools/probe_kit.py`의 `Rounds`).

찍는 것(JSON 한 줄씩): 모델 번호, 요청한 모델 이름, 응답이 낸 모델 이름, 종료 사유(`finish_reason`),
도구 호출 이름들, 인자가 JSON으로 풀리고 `city`가 든 호출의 수, 걸린 시간, 주소의 꼴(파드 번호를
가린 것).

못 보는 것: 서버가 `tool_calls`를 `content` 글에 섞어 내는 모양(그러면 `글로만 답함`으로 센다),
스트리밍 응답, 요청 한 번의 결과(모델이 비결정적이라 같은 요청도 갈릴 수 있다. `temperature`는 0으로
둔다).
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from typing import TypeGuard

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.probe_kit import Rounds  # noqa: E402

MODEL_NUMBERS = (1, 2)
TIMEOUT_SECONDS = 180.0
TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "도시의 지금 날씨를 돌려준다",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "도시 이름"}},
            "required": ["city"],
        },
    },
}
PROMPT = "서울의 지금 날씨를 알려 줘. 도구를 써서 확인해."


def names(number: int) -> tuple[str, str, str]:
    prefix = f"AGENT_OS_LLM_LOCAL_{number}"
    return f"{prefix}_BASE_URL", f"{prefix}_MODEL_ID", f"{prefix}_API_KEY"


def address_shape(base_url: str) -> str:
    """주소의 꼴. 파드 번호와 포트가 든 첫 마디를 가린다."""
    parts = urllib.parse.urlparse(base_url)
    host = re.sub(r"^[^.]+", "<파드번호>-<포트>", parts.hostname or "")
    return f"{parts.scheme}://{host}{parts.path}"


def ask(base_url: str, model_id: str, key: str) -> tuple[int, Mapping[str, object]]:
    body = json.dumps(
        {
            "model": model_id,
            "messages": [{"role": "user", "content": PROMPT}],
            "tools": [TOOL],
            "tool_choice": "auto",
            "temperature": 0,
            "max_tokens": 256,
        }
    ).encode()
    request = urllib.request.Request(
        base_url.rstrip("/") + "/chat/completions",
        data=body,
        # Runpod 프록시는 urllib 기본 User-Agent를 403(error code: 1010)으로 거절한다(2026-11-14
        # 파드 앞에서 손으로 봤다).
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "User-Agent": "agent-os-llm-local",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            status = response.status
            payload: object = json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, {}
    return status, payload if is_dict(payload) else {}


def is_dict(value: object) -> TypeGuard[dict[str, object]]:
    """JSON 객체. 키는 JSON 문법상 문자열이다."""
    return isinstance(value, dict)


def is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def calls_of(payload: Mapping[str, object]) -> tuple[str, list[str], int]:
    """(종료 사유, 도구 호출 이름들, 인자가 JSON으로 풀리고 city가 든 호출의 수)."""
    choices = payload.get("choices")
    choice = choices[0] if is_list(choices) and choices else None
    if not is_dict(choice):
        return "", [], 0
    finish = str(choice.get("finish_reason", ""))
    message = choice.get("message")
    raw = message.get("tool_calls") if is_dict(message) else None
    if not is_list(raw):
        return finish, [], 0
    called: list[str] = []
    good = 0
    for call in raw:
        function = call.get("function") if is_dict(call) else None
        if not is_dict(function):
            continue
        called.append(str(function.get("name", "")))
        try:
            arguments: object = json.loads(str(function.get("arguments", "")))
        except json.JSONDecodeError:
            continue
        if is_dict(arguments) and "city" in arguments:
            good += 1
    return finish, called, good


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    rounds = Rounds()
    for number in MODEL_NUMBERS:
        url_name, model_name, key_name = names(number)
        with rounds.round(f"모델 {number}") as current:
            missing = [n for n in (url_name, model_name, key_name) if not os.environ.get(n)]
            if missing:
                current.mark(measured=False, result=f"환경 변수가 없다: {' '.join(missing)}")
                continue
            base_url, model_id, key = (os.environ[n] for n in (url_name, model_name, key_name))
            started = time.monotonic()
            status, payload = ask(base_url, model_id, key)
            elapsed = round(time.monotonic() - started, 1)
            finish, called, good = calls_of(payload)
            answered = status == 200 and isinstance(payload.get("choices"), list)
            line = {
                "model_number": number,
                "requested_model": model_id,
                "response_model": payload.get("model"),
                "status": status,
                "finish_reason": finish,
                "tool_call_names": called,
                "calls_with_city": good,
                "elapsed_seconds": elapsed,
                "address_shape": address_shape(base_url),
            }
            print(json.dumps(line, ensure_ascii=False), flush=True)
            if not answered:
                current.mark(measured=False, result=f"200으로 답하지 않았다(상태 {status})")
            else:
                current.mark(measured=True, result="tool_calls" if called else "글로만 답함")
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
