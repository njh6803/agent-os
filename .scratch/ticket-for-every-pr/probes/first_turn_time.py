"""`tools/hook_prompt_directive.py` 의 첫 턴 티켓 알림(티켓 05) 한 번의 시간을 등록 모양으로 잰다.

`.claude/rules/tools.md` 의 훅별 시간 문단에 적을 값이다. 알림이 생기며 이 훅은 지시문이 아닌
프롬프트에서도 트랜스크립트를 연다(그 독스트링의 "비용"). 그래서 이 PC 의 가장 큰 트랜스크립트로
잰다(인자로 다른 파일을 줄 수 있다).

`tools/run_hooks.py` 의 `launch_argv`(등록 모양, 래퍼 `tools/launch_hook.py` 를 거친다)로 자식을
띄우고 stdin 에 보통 프롬프트 `끝났어?` 의 페이로드를 넣어 끝날 때까지의 시간을 갈래마다 다섯 번씩
잰다. 환경은 `hook_environment()` 라 러너를 띄운 세션의 헤드리스 변수가 벗겨진다. 갈래는 넷이다.
- 첫 턴, 새 트랜스크립트: 아직 없는 경로. 새 세션의 첫 프롬프트와 같다. 알림이어야 측정이다.
- 첫 턴, 큰 트랜스크립트: 가장 큰 트랜스크립트에서 assistant 기록을 뺀 사본. 훅이 파일을 끝까지
  읽는 최악이다(실제 첫 턴의 트랜스크립트는 첫 assistant 기록 앞의 줄뿐이고, 그 줄 수를 결과에
  찍는다). 알림이어야 측정이다.
- 첫 턴 아님: 가장 큰 트랜스크립트 그대로. 첫 assistant 기록에서 멈춘다. 침묵이어야 측정이고, 같은
  프롬프트가 앞 갈래에서 알림이었다는 것이 그 침묵이 첫 턴 판정에서 왔다는 대조다.
- 헤드리스: 앞의 사본에 `CLAUDE_CODE_SESSION_ATTENDED=0`. 침묵이어야 측정이다. 같은 사본이 둘째
  갈래에서 알림이었다는 것이 그 침묵이 헤드리스 가름에서 왔다는 대조다.
사본을 짓기 전에 원본에 assistant 기록이 있고 사본에 없는지 훅의 `has_assistant_turn` 으로 본다.
아니면 아무것도 재지 않고 2로 끝난다. 측정이 아닌 회차가 있으면 1이다(`tools/probe_kit.py`).
끝에 결과 한 줄(JSON)을 찍는다.

쓰임: 저장소 루트에서
`uv run python .scratch/ticket-for-every-pr/probes/first_turn_time.py [트랜스크립트]`
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.hook_prompt_directive import TICKET_NOTICE, has_assistant_turn  # noqa: E402
from tools.probe_kit import Rounds  # noqa: E402
from tools.run_hooks import hook_environment, launch_argv, message_of, outcome_of  # noqa: E402

RUNS = 5
HOOK = "hook_prompt_directive.py"
EVENT = "UserPromptSubmit"


def largest_transcript() -> Path:
    candidates = (Path.home() / ".claude" / "projects").glob("*/*.jsonl")
    return max(candidates, key=lambda path: path.stat().st_size)


def strip_assistant(source: Path, target: Path) -> None:
    """assistant 기록을 뺀 사본. 훅과 같이 줄마다 최상위 `type` 을 본다."""
    with (
        source.open(encoding="utf-8", errors="replace") as reader,
        target.open("w", encoding="utf-8", newline="") as writer,
    ):
        for line in reader:
            if not has_assistant_turn([line]):
                writer.write(line)


def has_assistant(path: Path) -> bool:
    with path.open(encoding="utf-8", errors="replace") as transcript:
        return has_assistant_turn(transcript)


def lines_before_assistant(path: Path) -> int:
    """첫 assistant 기록 앞의 줄 수. 첫 턴에 훅이 보는 트랜스크립트의 크기다."""
    with path.open(encoding="utf-8", errors="replace") as transcript:
        for index, line in enumerate(transcript):
            if has_assistant_turn([line]):
                return index
    return -1


def run_once(transcript: Path, extra_env: dict[str, str]) -> tuple[float, str, str]:
    """(밀리초, 판정, 훅이 낸 문장)."""
    payload = {
        "hook_event_name": EVENT,
        "prompt": "끝났어?",
        "cwd": str(ROOT),
        "transcript_path": str(transcript),
    }
    started = time.perf_counter()
    completed = subprocess.run(
        launch_argv(HOOK),
        input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
        env={**hook_environment(), **extra_env},
        cwd=ROOT,
        timeout=120,
        check=False,
    )
    elapsed = (time.perf_counter() - started) * 1000
    stdout = completed.stdout.decode("utf-8", "replace")
    stderr = completed.stderr.decode("utf-8", "replace")
    return (
        elapsed,
        outcome_of(completed.returncode, stdout, EVENT),
        message_of(completed.returncode, stdout, stderr),
    )


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else largest_transcript()
    size = source.stat().st_size
    head = lines_before_assistant(source)
    print(f"트랜스크립트: {source.name}, {size:,} 바이트, 첫 assistant 기록 앞 {head}줄")
    rounds = Rounds()
    ranges: dict[str, list[int] | None] = {}
    with tempfile.TemporaryDirectory() as scratch:
        stripped = Path(scratch) / "stripped.jsonl"
        strip_assistant(source, stripped)
        if not has_assistant(source) or has_assistant(stripped):
            print("원본에 assistant 기록이 없거나 사본에 남았다. 재지 않는다.")
            return 2
        print(f"assistant 를 뺀 사본: {stripped.stat().st_size:,} 바이트")
        cases = [
            ("첫 턴, 새 트랜스크립트", Path(scratch) / "없음.jsonl", {}, "context"),
            ("첫 턴, 큰 트랜스크립트", stripped, {}, "context"),
            ("첫 턴 아님", source, {}, "silent"),
            ("헤드리스", stripped, {"CLAUDE_CODE_SESSION_ATTENDED": "0"}, "silent"),
        ]
        for name, transcript, extra_env, expect in cases:
            # 표지를 본 회차의 시간만 모은다. 결론은 측정인 회차만으로
            # 낸다(.claude/rules/probes.md).
            times: list[float] = []
            for index in range(RUNS):
                with rounds.round(f"{name} {index + 1}") as current:
                    elapsed, outcome, message = run_once(transcript, extra_env)
                    noticed = message.startswith(TICKET_NOTICE[:40])
                    marked = outcome == expect and (noticed if expect == "context" else True)
                    if marked:
                        times.append(elapsed)
                    current.mark(
                        measured=marked,
                        result=f"{outcome}" if marked else f"기대 {expect}, 실제 {outcome}",
                    )
            if not times:
                ranges[name] = None
                print(f"{name}: 측정값 없음({RUNS}번 모두 측정 아님, 기대 {expect})")
                continue
            ranges[name] = [round(min(times)), round(max(times))]
            print(
                f"{name}: {min(times):.0f}~{max(times):.0f}ms"
                f" (측정 {len(times)}/{RUNS}번, 기대 {expect})"
            )
    print(rounds.summary())
    result = {
        "transcript_bytes": size,
        "lines_before_assistant": head,
        "runs": RUNS,
        "ranges_ms": ranges,
        "measured": rounds.exit_code() == 0,
    }
    print(json.dumps(result, ensure_ascii=False))
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
