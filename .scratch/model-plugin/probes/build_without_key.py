"""모델 객체(`ChatAnthropic`)를 매니페스트의 설정으로 만드는 일이 API 키 없이, 네트워크를 타지 않고
되는지와 걸리는 시간을 잰다. ADR 0040 Consequences 의 "만드는 것이 네트워크를 타지 않는다는 것은
어림"이 구현 티켓에 넘긴 측정이다. 실행마다 모델 객체를 만들기로 했으므로 만들기가 느리거나
키·네트워크를 요구하면 결정이 달라진다. 갈래는 넷이다.

- `build_no_key`. 환경에서 `ANTHROPIC_API_KEY` 와 기본 주소 환경변수를 걷어낸 뒤 어댑터와 같은
  인자(`model_name`, `max_tokens_to_sample`, `timeout=None`, `stop=None`)에 `temperature` 를 더해
  만든다. 표지는 인스턴스의 `anthropic_api_key` 가 빈 `SecretStr`(1.7.2 의 기본값. 1136 줄을
  읽었다. 걷어낸 환경에서 채워지지 않았다는 뜻)이고 `model` 과 `max_tokens` 가 준 값인 것. 결과는
  `cached_property` 인 `_client`·`_async_client` 가 인스턴스 `__dict__` 에 있는지(만들며
  클라이언트를 만들었는지)와 걸린 밀리초다.
- `build_dead_base_url`. 같은 만들기에 아무도 듣지 않는 로컬 포트를 `base_url` 로 준다. 만들기가
  네트워크를 탄다면 여기서 실패하거나 느려진다. 표지는 위와 같고 `anthropic_api_url` 이 준 주소다.
- `invoke_dead_base_url`(양성 대조 둘). 자리 표시 키와 `max_retries=0` 으로 그 모델을 `ainvoke` 하면
  `anthropic.APIConnectionError` 로 끝나야 한다. 네트워크는 호출에서 타고 `base_url` 이 실제로
  쓰인다는 표지다. 이것이 없으면 "만들기가 네트워크를 안 탄다"를 "이 프로브는 네트워크를 보지
  못한다"와 가를 수 없다. 그리고 호출 뒤에는 `_async_client` 가 인스턴스 `__dict__` 에 있어야
  한다. 만들기 회차의 "클라이언트 안 만듦"을 읽는 `__dict__` 탐지가 만들어진 클라이언트를 실제로
  잡는다는 양성 대조다. 둘 중 하나라도 없으면 그 회차는 측정이 아니다.
- `invoke_no_key`. 키 없이 같은 모델을 `ainvoke` 하면 어떤 예외로 끝나는지. 키가 없는 것이 드러나는
  자리(만들기가 아니라 첫 호출)와 그 문구의 근거다. 표지는 예외 문구에 `api_key` 가 있는 것.

전제. langchain-anthropic 1.7.2 의 `_client`·`_async_client` 는 `functools.cached_property` 다
(`chat_models.py` 의 1465·1480 줄을 읽었다). 그래서 "만들지 않았다"를 `__dict__` 로 본다. 판이
바뀌어 속성 이름이 달라지면 그 회차는 예외로 측정 아님이 된다. 호출은 런타임과 같은 `ainvoke` 다
(`core/loop.py` 를 읽었다).

쓰임: 저장소 루트에서 `uv run python .scratch/model-plugin/probes/build_without_key.py`
"""

from __future__ import annotations

import asyncio
import os
import platform
import socket
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

for variable in ("ANTHROPIC_API_KEY", "ANTHROPIC_API_URL", "ANTHROPIC_BASE_URL"):
    os.environ.pop(variable, None)

import anthropic  # noqa: E402
import langchain_anthropic  # noqa: E402
from langchain_anthropic import ChatAnthropic  # noqa: E402
from tools.probe_kit import Rounds  # noqa: E402

NAME = "claude-opus-5"
MAX_TOKENS = 16000
TEMPERATURE = 0.5
BUILDS = 5
CALLS = 2
LAZY = ("_client", "_async_client")
PLACEHOLDER_KEY = "not-a-real-key"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def build(**extra: object) -> tuple[ChatAnthropic, float]:
    """(모델, 걸린 밀리초). 인자는 `adapters/anthropic.py` 의 factory 와 같고 `temperature` 를
    더했다."""
    started = time.perf_counter()
    model = ChatAnthropic(
        model_name=NAME,
        max_tokens_to_sample=MAX_TOKENS,
        timeout=None,
        stop=None,
        temperature=TEMPERATURE,
        **extra,
    )
    return model, (time.perf_counter() - started) * 1000


def configured(model: ChatAnthropic) -> bool:
    return (
        model.anthropic_api_key.get_secret_value() == ""
        and model.model == NAME
        and model.max_tokens == MAX_TOKENS
        and model.temperature == TEMPERATURE
    )


def client_state(model: ChatAnthropic) -> str:
    made = [name for name in LAZY if name in model.__dict__]
    return f"클라이언트 만듦 {made}" if made else "클라이언트 안 만듦"


def invoke(model: ChatAnthropic) -> tuple[BaseException | None, float]:
    started = time.perf_counter()
    try:
        asyncio.run(model.ainvoke("hi"))
    except Exception as error:  # 예외의 종류가 측정 대상이다
        return error, (time.perf_counter() - started) * 1000
    return None, (time.perf_counter() - started) * 1000


def main() -> int:
    rounds = Rounds()
    timings: dict[str, list[float]] = {}
    dead = f"http://127.0.0.1:{free_port()}"

    for index in range(BUILDS):
        with rounds.round(f"build_no_key#{index}") as current:
            model, ms = build()
            timings.setdefault("build_no_key", []).append(ms)
            current.mark(measured=configured(model), result=client_state(model))
        with rounds.round(f"build_dead_base_url#{index}") as current:
            model, ms = build(base_url=dead)
            timings.setdefault("build_dead_base_url", []).append(ms)
            current.mark(
                measured=configured(model) and model.anthropic_api_url == dead,
                result=client_state(model),
            )

    for index in range(CALLS):
        with rounds.round(f"invoke_dead_base_url#{index}") as current:
            model, _ = build(base_url=dead, api_key=PLACEHOLDER_KEY, max_retries=0)
            error, ms = invoke(model)
            timings.setdefault("invoke_dead_base_url", []).append(ms)
            state = client_state(model)
            if (
                isinstance(error, anthropic.APIConnectionError)
                and "_async_client" in model.__dict__
            ):
                current.mark(measured=True, result=f"APIConnectionError, 호출 뒤 {state}")
            elif isinstance(error, anthropic.APIConnectionError):
                current.mark(measured=False, result=f"APIConnectionError 이나 호출 뒤에도 {state}")
            elif error is None:
                current.mark(measured=False, result="응답이 왔다")
            else:
                current.mark(
                    measured=False, result=f"다른 예외 {type(error).__name__}: {str(error)[:120]}"
                )
        with rounds.round(f"invoke_no_key#{index}") as current:
            model, _ = build(base_url=dead, max_retries=0)
            error, ms = invoke(model)
            timings.setdefault("invoke_no_key", []).append(ms)
            text = "" if error is None else str(error)
            names_key = "api_key" in text or "ANTHROPIC_API_KEY" in text
            if error is None:
                current.mark(measured=False, result="응답이 왔다")
            elif names_key:
                current.mark(measured=True, result=f"{type(error).__name__}: {text[:160]}")
            else:
                current.mark(
                    measured=False,
                    result=f"키를 말하지 않는 예외 {type(error).__name__}: {text[:120]}",
                )

    for entry in rounds.entries:
        print(f"{entry.label}: {entry.result}")
    for label, values in timings.items():
        print(
            f"{label}: 최소 {min(values):.1f}ms 중앙 {statistics.median(values):.1f}ms "
            f"최대 {max(values):.1f}ms ({len(values)}회)"
        )
    print(
        f"판: python {platform.python_version()}, anthropic {anthropic.__version__}, "
        f"langchain-anthropic {langchain_anthropic.__version__}"
    )
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
