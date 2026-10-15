"""거슬러 읽기의 비용과 그동안 이벤트 루프가 막히는 시간(ADR 0022 의 둘째 2026-10-15 이력).

설계 인터뷰(일지 2026-10-15-17)가 커밋하지 않은 스크래치 스크립트로 손으로 본 수를 이 프로브가 다시
잰다. 명세가 교환 수의 기준과 읽기 상한의 값을 정하는 입력이다.

지금의 거슬러 읽기(`agent_os.core.continuation.gather_continued`)를 실제 JSONL 어댑터
(`JsonlTrace`) 위에서 돌린다. 고리는 임시 디렉터리에 끝난 실행 N개를 시작 이벤트의 앞 실행 필드로
이어 쓴 것이다. 경우는 둘이다.

- 한 에이전트: 같은 에이전트로 N번 이어 간 고리. 요약이 없어 처음까지 N개를 읽는다. 바로가기가 생긴
  뒤에도 한 에이전트의 실행만 따라가므로 읽는 트레이스는 이것과 같다(교환 수 기준의 예산).
- 바꿔 씀: 에이전트 A로 한 번, B로 N-1번 이어 간 고리에서 A로 돌아온다. 지금의 읽기는 B의 실행을
  모두 지나간다(바로가기가 없는 옛 고리의 상한 예산).

자리는 둘이다. 루프는 코루틴 안에서 동기로 부른다(지금 재개가 하는 모양). 스레드는
`anyio.to_thread.run_sync` 로 보낸다(이어 가기를 시작할 때의 새 모양). 자리마다 새 디렉터리에 고리를
써서 첫 읽기가 언제나 방금 쓴 트레이스를 읽게 하고, 같은 자리에서 한 번 더 읽어 둘째 읽기를 잰다.
첫 읽기가 왜 느린지(백신의 검사, 캐시)는 가르지 않는다. 예산에 쓰는 것은 그 값이다.

루프가 막히는 시간은 1ms 간격으로 잠드는 박동 태스크의 가장 긴 공백이다. 박동은 읽기를 시작하기 전에
뛰고 있어야 하고(표지), 읽는 창 앞의 마지막 박동부터 창 뒤의 첫 박동까지를 본다. 박동은 읽지 않아도
1ms보다 긴 공백을 내므로 아무것도 읽지 않고 잠들기만 한 대조군의 공백을 함께 적는다. 최장 공백은
창이 길수록 길게 나올 수 있어 대조군의 창을 1초와 10초 둘로 두어 측정 창(최대 약 10초)과 견준다.
루프 위의 읽기는 양성 대조다 — 막으면 공백이 읽은 시간과 같고 창 안의 박동이 0이어야 한다. 스레드의
공백이 대조군과 같은 크기면 막지 않은 것이고, 대조군의 공백이 왜 그 크기인지(타이머의 눈금 등)는
가르지 않는다.

측정의 표지는 셋이다. 거슬러 읽기가 모은 교환 수가 그 경우의 기대값과 같다. 박동이 창 앞에서
뛰었다. 루프 자리에서는 읽는 창 안에 박동이 없다(양성 대조가 섰다). 표지가 없는 회차는 측정이 아니라
따로 세고, 하나라도 있으면 종료 코드가 1이다.

    PYTHONUTF8=1 uv run python .scratch/end-user-continuation/probes/walk_budget.py

시각은 `time.perf_counter` 이고 회차마다 새 고리를 쓴다. 표는 회차 셋의 가장 짧은 값과 가장 긴
값이다.
"""

from __future__ import annotations

import sys
import tempfile
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import anyio

from agent_os.adapters.jsonl import JsonlTrace
from agent_os.core.continuation import Gathered, gather_continued
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

ROUNDS = 3
BEAT_SECONDS = 0.001
IDLE_WINDOWS = (1.0, 10.0)

ALPHA = AgentName("alpha")
BRAVO = AgentName("bravo")
PRINCIPAL = Principal("probe")

# 한글 한 글자. UTF-8 로 3바이트다.
KO = "가"
REQUEST_CHARS = 100
OUTPUT_CHARS = 300


@dataclass(frozen=True)
class Case:
    """고리 하나의 모양. 실행마다의 에이전트와 거슬러 읽기가 모을 교환 수."""

    name: str
    runs: int
    prompt_chars: int
    switched: bool

    def agent_at(self, index: int) -> AgentName:
        """바꿔 쓴 고리는 첫 실행만 A 이고 나머지가 B 다."""
        return ALPHA if not self.switched or index == 0 else BRAVO

    @property
    def expected_exchanges(self) -> int:
        """A 로 돌아와 모으는 교환 수. 바꿔 쓴 고리는 처음 하나뿐이다."""
        return 1 if self.switched else self.runs


CASES = (
    Case("한 에이전트", 52, 2_000, switched=False),
    Case("한 에이전트", 52, 20_000, switched=False),
    Case("한 에이전트", 201, 2_000, switched=False),
    Case("한 에이전트", 201, 20_000, switched=False),
    Case("한 에이전트", 1_001, 2_000, switched=False),
    Case("바꿔 씀", 201, 2_000, switched=True),
    Case("바꿔 씀", 1_001, 2_000, switched=True),
)


@dataclass(frozen=True)
class Walk:
    """한 번의 거슬러 읽기. 걸린 시간, 그동안 루프의 가장 긴 공백, 창 안의 박동 수, 표지."""

    seconds: float
    longest_gap: float
    beats_inside: int
    measured: bool


@dataclass
class Heartbeat:
    """1ms 간격으로 잠들며 깬 시각을 적는 태스크. 루프가 막히면 공백이 벌어진다."""

    beats: list[float]

    async def run(self) -> None:
        while True:
            self.beats.append(time.perf_counter())
            await anyio.sleep(BEAT_SECONDS)

    def gap_around(self, began: float, ended: float) -> tuple[float, int, bool]:
        """창 앞의 마지막 박동부터 창 뒤의 첫 박동까지 가장 긴 공백, 창 안의 박동 수, 창 앞 박동의
        유무."""
        before = [beat for beat in self.beats if beat < began]
        inside = [beat for beat in self.beats if began <= beat <= ended]
        after = [beat for beat in self.beats if beat > ended]
        if not before or not after:
            return 0.0, len(inside), False
        points = [before[-1], *inside, after[0]]
        longest = max(later - earlier for earlier, later in zip(points, points[1:], strict=False))
        return longest, len(inside), True


def _text(chars: int) -> str:
    return KO * chars


def _write_chain(trace: JsonlTrace, case: Case) -> RunId:
    """끝난 실행 N개를 앞 실행 필드로 이어 쓰고 마지막 실행을 돌려준다."""
    start = datetime(2026, 10, 16, tzinfo=UTC)
    previous: RunId | None = None
    for index in range(case.runs):
        run_id = RunId(f"run-{index:05d}")
        at = start + timedelta(seconds=index)
        trace.write(
            RunStarted(
                run_id=run_id,
                ts=at,
                agent=case.agent_at(index),
                request=_text(REQUEST_CHARS),
                principal=PRINCIPAL,
                previous_run=previous,
            )
        )
        trace.write(
            LlmCalled(
                run_id=run_id,
                ts=at,
                model="probe",
                input_tokens=1,
                output_tokens=1,
                prompt=_text(case.prompt_chars),
                tool_calls=(ToolCall(id="t1", name="add", args={"a": 1, "b": 2}),),
            )
        )
        trace.write(
            ToolCalled(
                run_id=run_id, ts=at, tool="add", ok=True, args={"a": 1, "b": 2}, content="3"
            )
        )
        trace.write(
            LlmCalled(
                run_id=run_id,
                ts=at,
                model="probe",
                input_tokens=1,
                output_tokens=1,
                text=_text(OUTPUT_CHARS),
            )
        )
        trace.write(RunFinished(run_id=run_id, ts=at, output=_text(OUTPUT_CHARS)))
        previous = run_id
    assert previous is not None
    return previous


async def _settle(heartbeat: Heartbeat) -> None:
    """박동이 몇 번 뛴 뒤에 잰다. 창 앞의 박동이 표지다."""
    seen = len(heartbeat.beats)
    while len(heartbeat.beats) < seen + 3:
        await anyio.sleep(BEAT_SECONDS)


type Gather = Callable[[], Gathered]


async def _on_loop(gather: Gather) -> Gathered:
    """지금 재개의 모양. 코루틴 안에서 동기로 부른다."""
    return gather()


async def _on_thread(gather: Gather) -> Gathered:
    """이어 가기를 시작할 때의 새 모양. 별도 스레드로 보낸다."""
    return await anyio.to_thread.run_sync(gather)


@dataclass(frozen=True)
class Place:
    """거슬러 읽기를 부르는 자리. 양성 대조인 자리는 읽는 동안 박동이 없어야 측정이다."""

    name: str
    call: Callable[[Gather], Awaitable[Gathered]]
    positive_control: bool


PLACES = (
    Place("루프", _on_loop, positive_control=True),
    Place("스레드", _on_thread, positive_control=False),
)


async def _walk(heartbeat: Heartbeat, place: Place, gather: Gather, case: Case) -> Walk:
    """거슬러 읽기 한 번을 그 자리에서 돌려 잰다."""
    await _settle(heartbeat)
    began = time.perf_counter()
    gathered = await place.call(gather)
    ended = time.perf_counter()
    await _settle(heartbeat)
    longest, inside, beat_before = heartbeat.gap_around(began, ended)
    control_held = not place.positive_control or inside == 0
    measured = beat_before and control_held and len(gathered.runs) == case.expected_exchanges
    return Walk(ended - began, longest, inside, measured)


async def _idle(heartbeat: Heartbeat, seconds: float) -> float:
    """대조군. 아무것도 읽지 않고 잠들기만 하는 창의 가장 긴 공백."""
    await _settle(heartbeat)
    began = time.perf_counter()
    await anyio.sleep(seconds)
    ended = time.perf_counter()
    await _settle(heartbeat)
    longest, _, _ = heartbeat.gap_around(began, ended)
    return longest


def _span(values: list[float]) -> str:
    low, high = min(values), max(values)
    return f"{low:,.1f}" if f"{low:,.1f}" == f"{high:,.1f}" else f"{low:,.1f}~{high:,.1f}"


async def main() -> int:
    heartbeat = Heartbeat(beats=[])
    unmeasured = 0
    async with anyio.create_task_group() as group:
        group.start_soon(heartbeat.run)
        for seconds in IDLE_WINDOWS:
            idle_gaps = [await _idle(heartbeat, seconds) * 1000 for _ in range(ROUNDS)]
            print(f"대조군(잠들기만 {seconds:g}초): 가장 긴 공백 {_span(idle_gaps)}ms")
        print()
        print(
            "| 경우 | 고리(실행) | 프롬프트(자) | 자리 | 회차 | 걸린 시간(ms) "
            "| 트레이스 하나(ms) | 루프의 가장 긴 공백(ms) | 창 안 박동 |"
        )
        print("|---|---|---|---|---|---|---|---|---|")
        for case in CASES:
            for place in PLACES:
                first: list[Walk] = []
                second: list[Walk] = []
                for _ in range(ROUNDS):
                    with tempfile.TemporaryDirectory() as root:
                        trace = JsonlTrace(Path(root))
                        last = _write_chain(trace, case)

                        def gather(trace: JsonlTrace = trace, last: RunId = last) -> Gathered:
                            return gather_continued(trace, last, ALPHA, PRINCIPAL)

                        first.append(await _walk(heartbeat, place, gather, case))
                        second.append(await _walk(heartbeat, place, gather, case))
                for label, walks in (("첫 읽기", first), ("둘째 읽기", second)):
                    unmeasured += sum(1 for walk in walks if not walk.measured)
                    good = [walk for walk in walks if walk.measured]
                    if not good:
                        continue
                    print(
                        f"| {case.name} | {case.runs:,} | {case.prompt_chars:,} "
                        f"| {place.name} | {label} "
                        f"| {_span([w.seconds * 1000 for w in good])} "
                        f"| {_span([w.seconds * 1000 / case.runs for w in good])} "
                        f"| {_span([w.longest_gap * 1000 for w in good])} "
                        f"| {_span([float(w.beats_inside) for w in good])} |"
                    )
        group.cancel_scope.cancel()
    print()
    print(f"측정이 아닌 회차: {unmeasured}")
    return 1 if unmeasured else 0


if __name__ == "__main__":
    sys.exit(anyio.run(main))
