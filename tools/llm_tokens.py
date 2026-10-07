"""`-m llm` 실행이 남긴 트레이스의 토큰 합계(대기열 113).

`docs/constitution/operations.md` LLM 테스트 절이 일지 검사 절에 토큰 합계를 적으라는데 세는 법이
없어, 세션마다 스크래치에 합계 스크립트를 새로 지었다(일지 2026-10-05-01·2026-10-06-06).
`--basetemp` 없이 돌린 세션은 같은 사용자의 다른 세션과 나눠 쓰는 `pytest-current` 에서 섞인 실행을
모델 이름으로 걸러 셌다(일지 2026-10-06-11). 그래서 `tests/conftest.py` 가 llm 마커 테스트마다 그
`tmp_path` 를 이것으로 세어, 실행 끝의 결과 요약(`short test summary info` 와 통과 수 줄) 바로 위에
찍는다. `tmp_path` 는 그 실행만의
basetemp(`pytest-N`) 아래에 테스트마다 따로 생겨 다른 세션의 실행이 섞이지 않는다.

토큰 이벤트는 종류 이름이 아니라 모양으로 고른다. 최상위에 정수 `input_tokens` 와 `output_tokens`
를 든 줄이면 모델 호출 하나다. 지금은 `llm_called` 와 `conversation_summarized` 이고, sdk 에 토큰을
든 종류가 늘어도 여기 목록이 낡지 않는다. 줄은 JSONL 어댑터와 같이 디코딩 전에 바이트의 개행으로
가르고, 개행으로 끝나지 않은 마지막 조각은 커밋되지 않은 줄이라 세지 않는다(ADR 0012 의
2026-09-23 이력 둘째). 문자열의 `splitlines` 로 가르면 U+2028 같은 줄 구분 문자에서도 갈라, 모델
응답에 그 문자가 든 호출이 합계에서 빠진다(셀프 리뷰가 손으로 봤다). UTF-8 이 아닌 줄은 건너뛴다.

못 보는 것: 트레이스를 남기지 않는 호출과 테스트의 `tmp_path` 밖에 쓴 트레이스. 모델을 바로 부르는
LLM 테스트(`tests/core/test_model.py`)의 토큰은 어디에도 기록되지 않고, `tmp_path_factory` 로 만든
디렉터리의 트레이스는 세지 않는다. 그런 테스트의 수는 합계 줄이 따로 적는다(`tests/test_conftest.py`
가 잰다). 한 테스트가 트레이스도 남기고 모델도 바로 부르면 뒤의 호출은 빠진 채 세지 못한 수에도
들지 않는다. 읽지 못한 파일도 빠진다.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


@dataclass(frozen=True)
class Tokens:
    traces: int = 0
    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    # 세지 못한 LLM 테스트의 수. 센 쪽(count)이 아니라 테스트마다 부르는 쪽(conftest)이 채운다.
    untraced_tests: int = 0

    def __add__(self, other: Tokens) -> Tokens:
        return Tokens(
            traces=self.traces + other.traces,
            calls=self.calls + other.calls,
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            untraced_tests=self.untraced_tests + other.untraced_tests,
        )


def count(root: Path) -> Tokens:
    """`root` 아래 모든 깊이의 `*.jsonl` 파일에서 토큰을 든 줄을 더한다. 없으면 0 이다.

    읽지 못한 파일은 건너뛴다. 이것을 부르는 tryfirst teardown 훅이 예외를 내면 pluggy 가 픽스처
    정리를 건너뛰어 다음 테스트의 setup 까지 깨진다(PR 직전 버그·성능 리뷰가 재현했다).
    """
    total = Tokens()
    for path in sorted(root.rglob("*.jsonl")):
        try:
            data = path.read_bytes()
        except OSError:  # 그 이름의 디렉터리도 여기 든다
            continue
        total += _trace(data)
    return total


def summary(tokens: Tokens) -> str:
    total = tokens.input_tokens + tokens.output_tokens
    untraced = (
        f" 트레이스를 남기지 않은 LLM 테스트 {tokens.untraced_tests}개는 세지 못했다."
        if tokens.untraced_tests
        else ""
    )
    return (
        f"LLM 토큰 합계 {total:,}(입력 {tokens.input_tokens:,}, 출력 {tokens.output_tokens:,})."
        f" 트레이스 {tokens.traces}개, 모델 호출 {tokens.calls}건.{untraced}"
        " 일지 검사 절에 옮긴다(operations.md LLM 테스트)"
    )


def _trace(data: bytes) -> Tokens:
    total = Tokens(traces=1)
    # 마지막 조각은 커밋되지 않은 줄이거나, 파일이 개행으로 끝났으면 빈 바이트다.
    for line in data.split(b"\n")[:-1]:
        call = _call(line)
        if call is not None:
            total += call
    return total


def _call(line: bytes) -> Tokens | None:
    try:
        value: Json = json.loads(line)
    except ValueError:  # UnicodeDecodeError 도 여기 든다
        return None
    if not isinstance(value, dict):
        return None
    input_tokens = value.get("input_tokens")
    output_tokens = value.get("output_tokens")
    if not isinstance(input_tokens, int) or not isinstance(output_tokens, int):
        return None
    return Tokens(calls=1, input_tokens=input_tokens, output_tokens=output_tokens)
