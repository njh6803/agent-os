"""대화의 고리를 거슬러 읽는 비용(ADR 0022 "그 비용은 명세가 잰다").

실제 JSONL 어댑터(`JsonlTrace`)로 끝난 실행 N개의 트레이스를 임시 디렉터리에
쓰고, 고리를 끝에서 처음까지 `read` 로 하나씩 읽는 시간을 잰다. 대조군 둘은
포트에 없는 읽기다.

- 머리와 끝: 헤더, 첫 이벤트 줄(시작 이벤트), 마지막 줄(결말)만 JSON 으로
  읽는다. 마지막 줄을 찾으려 파일을 끝까지 흘려 읽는다. 목록의 요약 읽기와
  같은 모양이다.
- 머리만: 헤더와 첫 이벤트 줄만 읽고 파일을 닫는다. 흘려 읽기도 없다.

둘의 차이가 끝까지 흘려 읽는 몫이고, `read` 와 머리와 끝의 차이가 가운데 줄을
파싱하는 몫이다.

트레이스 하나의 모양은 도구를 한 번 부르고 끝난 실행이다. run_started,
llm_called(프롬프트와 도구 호출), tool_called, llm_called(텍스트),
run_finished. 에이전트가 앞 교환을 프롬프트에 엮으면 프롬프트가 대화 요약의
한도만큼 자라므로 프롬프트 길이(한글 글자 수)를 바꿔 가며 잰다. 한 실행 안의
루프는 둘째 턴부터 프롬프트를 싣지 않으므로(ADR 0009 이력) 트레이스마다 한
번이다. 도구 결과는 작다. 결과가 큰 트레이스는 재지 않았다.

`previous` 필드는 아직 없어서 고리는 메모리의 run_id 목록으로 흉내 낸다.
재는 것은 읽기의 비용이고, 시작 이벤트에서 다음 식별자를 꺼내는 비용은 그에
비해 무시할 만하다. 고리 1000개에 프롬프트 60,000자인 조합은 디스크를 약
180MB 써서 뺀다(`SKIP`).

    PYTHONUTF8=1 uv run python .scratch/conversation/probes/chain_walk.py

결과는 표 하나다. 시각은 `time.perf_counter` 이고 같은 측정을 세 번 해 가장
짧은 것을 적는다. 방금 쓴 파일이라 OS 캐시에 있으므로 하한이다.
"""

from __future__ import annotations

import json
import tempfile
import time
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from functools import partial
from pathlib import Path

from agent_os.adapters.jsonl import JsonlTrace
from agent_os.sdk import (
    AgentName,
    LlmCalled,
    Principal,
    RunFinished,
    RunId,
    RunStarted,
    ToolCall,
    ToolCalled,
)

# 고리 길이와 프롬프트 길이. 큰 조합은 디스크를 많이 쓰므로 빼는 쌍을 둔다.
CHAINS = (10, 100, 1000)
PROMPTS = (2_000, 20_000, 60_000)
SKIP = {(1000, 60_000)}
REPEAT = 3

# 파일 머리의 줄 수. 헤더와 첫 이벤트 줄(시작 이벤트)이다.
HEAD_LINES = 2

# 한글 한 글자. UTF-8 로 3바이트라 파일 크기가 글자 수의 약 세 배다.
KO = "가"

HEADER = (
    "| 고리 | 프롬프트(자) | 파일 하나(KB) | read 합계(ms) | read 하나(ms) "
    "| 머리와 끝 합계(ms) | 머리만 합계(ms) |"
)
RULE = "|---|---|---|---|---|---|---|"


def _text(chars: int) -> str:
    return KO * chars


def _write_run(trace: JsonlTrace, run_id: RunId, prompt_chars: int, at: datetime) -> None:
    trace.write(
        RunStarted(
            run_id=run_id,
            ts=at,
            agent=AgentName("calc"),
            request=_text(100),
            principal=Principal("probe"),
        )
    )
    trace.write(
        LlmCalled(
            run_id=run_id,
            ts=at,
            model="probe",
            input_tokens=1,
            output_tokens=1,
            prompt=_text(prompt_chars),
            text="",
            tool_calls=(ToolCall(id="t1", name="add", args={"a": 1, "b": 2}),),
        )
    )
    trace.write(
        ToolCalled(run_id=run_id, ts=at, tool="add", ok=True, args={"a": 1, "b": 2}, content="3")
    )
    trace.write(
        LlmCalled(
            run_id=run_id,
            ts=at,
            model="probe",
            input_tokens=1,
            output_tokens=1,
            prompt="",
            text=_text(300),
        )
    )
    trace.write(RunFinished(run_id=run_id, ts=at, output=_text(300)))


def _full_walk(trace: JsonlTrace, chain: list[RunId]) -> None:
    """고리를 끝에서 처음까지 포트의 `read` 로 읽는다."""
    for run_id in reversed(chain):
        assert trace.read(run_id) is not None


def _edges_walk(directory: Path, chain: list[RunId]) -> None:
    """머리와 마지막 줄만 JSON 으로 읽는다. 마지막 줄을 찾으려 끝까지 흘려 읽는다."""
    for run_id in reversed(chain):
        with (directory / f"{run_id}.jsonl").open("rb") as file:
            lines = iter(file)
            head = [next(lines) for _ in range(HEAD_LINES)]
            last = head[-1]
            for line in lines:
                last = line
        for line in (*head, last):
            json.loads(line)


def _head_walk(directory: Path, chain: list[RunId]) -> None:
    """머리만 JSON 으로 읽고 닫는다."""
    for run_id in reversed(chain):
        with (directory / f"{run_id}.jsonl").open("rb") as file:
            lines = iter(file)
            head = [next(lines) for _ in range(HEAD_LINES)]
        for line in head:
            json.loads(line)


def _best_ms(walk_once: Callable[[], None], repeat: int) -> float:
    """가장 짧은 한 번(ms)."""
    seconds: list[float] = []
    for _ in range(repeat):
        began = time.perf_counter()
        walk_once()
        seconds.append(time.perf_counter() - began)
    return min(seconds) * 1000


def main() -> None:
    print(HEADER)
    print(RULE)
    start = datetime(2026, 10, 4, tzinfo=UTC)
    for chain_length in CHAINS:
        for prompt_chars in PROMPTS:
            if (chain_length, prompt_chars) in SKIP:
                continue
            with tempfile.TemporaryDirectory() as root:
                directory = Path(root)
                trace = JsonlTrace(directory)
                chain = [RunId(f"run-{index:05d}") for index in range(chain_length)]
                for index, run_id in enumerate(chain):
                    _write_run(trace, run_id, prompt_chars, start + timedelta(seconds=index))
                size_kb = (directory / f"{chain[0]}.jsonl").stat().st_size / 1024
                full_ms = _best_ms(partial(_full_walk, trace, chain), REPEAT)
                edges_ms = _best_ms(partial(_edges_walk, directory, chain), REPEAT)
                head_ms = _best_ms(partial(_head_walk, directory, chain), REPEAT)
                print(
                    f"| {chain_length} | {prompt_chars:,} | {size_kb:,.1f} | {full_ms:,.1f} "
                    f"| {full_ms / chain_length:.2f} | {edges_ms:,.1f} | {head_ms:,.1f} |"
                )


if __name__ == "__main__":
    main()
