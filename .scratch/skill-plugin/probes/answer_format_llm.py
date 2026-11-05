"""예시 스킬 `answer-format` 의 본문을 calc 프롬프트에 엮으면 실제 모델의 답과 도구 호출이
달라지는지 재는 탐침. 명세의 "예시 스킬" 절이 근거로 든다. 네트워크와 `ANTHROPIC_API_KEY` 가
필요하다.

재는 것(티켓 05 뒤에도 같다. 그 티켓이 calc 에 `{skills}` 를 더하고 매니페스트에 `skills` 를 적어,
`_prepare` 가 모든 갈래에서 그 줄을 지우고 글로 넣는 갈래는 `{skills}` 가 빠진 줄로 바꾼다).
스킬 경로가 아직 없으므로 저장소 `plugins/` 를 임시 폴더에 복사하고, 블록 갈래에서는 그
사본의 calc `PROMPT` 에 `지침 answer-format: <본문>` 블록을 글로 넣어 명세가 정한 자리(머리 문장 뒤,
앞 대화 블록 앞)에 둔다. 대조 갈래는 사본을 고치지 않는다. 두 갈래를 실제
CLI(`python -m agent_os.main run calc`) 와 실제 stdio 서버와 실제 모델로 돌려 `tests/test_main.py`
의 `-m llm` 시험이 보는 것을 같은 입력으로 본다.

- 새 실행: `2 더하기 2는?` 의 표준 출력에 `4` 가 있는지, 트레이스에 `tool_called` 가 있는지
  (`test_calc_에이전트가_실제_모델로_답하고_트레이스에_모델_호출이_남는다`).
- 이어 가기: `2 더하기 3은?` 뒤 `거기에 4를 곱하면?` 의 출력에 `20` 이 있는지
  (`test_실제_CLI_로_calc_를_이어_가면_앞_대화를_알고_답한다`).

표지. 프로세스가 0 으로 끝나고 트레이스의 끝이 `run_finished` 이며, 첫 `llm_called.prompt` 에 본문이
블록 갈래에서는 있고 대조 갈래에서는 없을 때만 측정이다. 답과 도구 호출은 결과이지 표지가 아니다.

판정(돌리기 전에 적었다). 블록 갈래의 측정 회차가 모두 값과 도구 호출을 갖추면 이 본문이 그
회차들에서 시험의 단언을 깨지 않았다고 읽는다. 블록 갈래에서만 값이나 도구 호출이 빠지면 본문이 답을
바꾼 것으로 읽어 본문을 다시 쓰거나 예시 스킬의 갈래를 다시 묻는다. 대조 갈래에서도 빠지면 본문이
아니라 시험의 단언 자체가 흔들리는 것으로 읽는다. 대조 갈래가 앞의 둘을 가른다.

양성 대조. 도구금지 갈래는 같은 자리에 도구를 쓰지 말라는 본문을 넣는다. 그 회차에 `도구=False` 가
나야 이 자리의 글이 모델의 도구 호출을 바꿀 수 있고 탐침이 그 변화를 알아본다는 것이 선다. 결과를 본
뒤 더했다. 첫 실행은 대조와 블록 두 갈래였고 값과 도구 호출이 모두 그대로라, "블록이 답을 바꾸지
않는다" 와 "이 자리의 글은 무엇이든 답을 바꾸지 못한다" 를 가르지 못했다. 앞의 판정 기준은 바꾸지
않았다. 인자로 갈래 이름을 주면 그 갈래만 돈다(토큰을 아끼려고 도구금지만 따로 돌렸다).

못 보는 것. 회차 수가 적어 드문 흔들림은 잡지 못한다. calc 코드가 스킬을 엮는 실제 경로는 지나지
않고 글로 넣은 프롬프트만 잰다. 요약을 지나는 `-m llm` 시험(`test_한도를_작게_적은_…`)은 넣지
않았다. 본문을 바꾸면 이 결과는 그 본문의 것이 아니다. 이어 가기 회차의 표지는 두 실행이 0 으로
끝나고 둘째가 첫째의 식별자를 `--continuation` 으로 받은 것까지이고, 둘째 프롬프트에 앞 대화 블록이
든 것은 보지 않는다. 앞 값 없이는 `20` 이 나오기 어렵다는 것은 어림이다.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds  # noqa: E402

from agent_os.adapters.jsonl import JsonlTrace  # noqa: E402
from agent_os.sdk import LlmCalled, RunFinished, RunId, ToolCalled  # noqa: E402

BODY = (
    "답은 값 하나만 쓴다. 단위·설명·계산 과정을 붙이지 않는다. "
    "계산할 수 없으면 왜 할 수 없는지 한 문장으로 답한다."
)
NO_TOOL_BODY = "도구를 쓰지 말고 암산으로 바로 답한다."
PROMPT_TAIL = '"{skills}{previous}요청: {request}"'
SKILLS_LINE = 'skills = ["answer-format"]\n'
MODEL = "claude-opus-5"
CALL_TIMEOUT = 300
# 갈래 이름, 넣을 본문(없으면 고치지 않는다), 새 실행 회차, 이어 가기 회차.
ARMS = (
    ("대조", None, 5, 3),
    ("블록", BODY, 5, 3),
    ("도구금지", NO_TOOL_BODY, 2, 0),
)


def _prepare(root: Path, body: str | None) -> None:
    shutil.copytree(
        ROOT / "plugins", root / "plugins", ignore=shutil.ignore_patterns("__pycache__")
    )
    # 티켓 05 뒤 저장소 calc 는 매니페스트의 `skills` 로 진짜 블록을 엮는다. 모든 갈래에서 그 줄을
    # 지워 대조 갈래에 본문이 없고 블록 갈래에는 글로 넣은 블록 하나만 있게 한다(재던 것 그대로).
    manifest = root / "plugins" / "agents" / "calc" / "plugin.toml"
    text = manifest.read_text(encoding="utf-8")
    assert text.count(SKILLS_LINE) == 1, "calc 의 매니페스트 모양이 바뀌었다"
    manifest.write_text(text.replace(SKILLS_LINE, ""), encoding="utf-8")
    if body is None:
        return
    agent = root / "plugins" / "agents" / "calc" / "agent.py"
    source = agent.read_text(encoding="utf-8")
    assert source.count(PROMPT_TAIL) == 1, "calc 의 PROMPT 모양이 바뀌었다"
    woven = f'"지침 answer-format: {body}\\n\\n{{previous}}요청: {{request}}"'
    agent.write_text(source.replace(PROMPT_TAIL, woven), encoding="utf-8")


def _run(
    request: str, root: Path, traces: Path, previous: str | None = None
) -> tuple[subprocess.CompletedProcess[str], str | None]:
    before = {path.stem for path in traces.iterdir()} if traces.is_dir() else set[str]()
    continuation = [] if previous is None else ["--continuation", previous]
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_os.main",
            "run",
            "calc",
            request,
            "--traces",
            str(traces),
            "--plugins-root",
            str(root / "plugins"),
            "--model",
            MODEL,
            *continuation,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
        check=False,
        timeout=CALL_TIMEOUT,
    )
    created = {path.stem for path in traces.iterdir()} - before if traces.is_dir() else set[str]()
    return result, next(iter(created)) if len(created) == 1 else None


def _observe(traces: Path, run_id: str | None, body: str | None):
    """(표지를 봤는가, 출력, 도구 호출이 있는가, 토큰 합)."""
    if run_id is None:
        return False, "", False, 0
    trace = JsonlTrace(traces).read(RunId(run_id))
    assert trace is not None
    events = trace.events
    calls = [event for event in events if isinstance(event, LlmCalled)]
    prompts = [call.prompt for call in calls if call.prompt]
    woven = bool(prompts) and (BODY not in prompts[0] if body is None else body in prompts[0])
    marked = woven and isinstance(events[-1], RunFinished)
    output = events[-1].output if isinstance(events[-1], RunFinished) else ""
    tool = any(isinstance(event, ToolCalled) for event in events)
    tokens = sum(call.input_tokens + call.output_tokens for call in calls)
    return marked, output, tool, tokens


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    if "ANTHROPIC_API_KEY" not in os.environ:
        print("ANTHROPIC_API_KEY 가 없다. --env-file 을 확인한다")
        return 2
    chosen = sys.argv[1:]
    rounds = Rounds()
    total_tokens = 0
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temp:
        base = Path(temp)
        for arm, body, fresh_rounds, chain_rounds in ARMS:
            if chosen and arm not in chosen:
                continue
            root = base / arm
            _prepare(root, body)
            for index in range(fresh_rounds):
                label = f"{arm} 새 실행 {index + 1}"
                with rounds.round(label) as slot:
                    traces = root / "traces" / f"fresh-{index}"
                    result, run_id = _run("2 더하기 2는?", root, traces)
                    marked, output, tool, tokens = _observe(traces, run_id, body)
                    total_tokens += tokens
                    print(f"{label}: 출력={result.stdout.strip()!r} 도구={tool} 토큰={tokens}")
                    slot.mark(
                        measured=result.returncode == 0 and marked,
                        result=f"{arm} 새 실행 값={'4' in output} 도구={tool}",
                    )
            for index in range(chain_rounds):
                label = f"{arm} 이어 가기 {index + 1}"
                with rounds.round(label) as slot:
                    traces = root / "traces" / f"chain-{index}"
                    first, first_id = _run("2 더하기 3은?", root, traces)
                    second, second_id = _run("거기에 4를 곱하면?", root, traces, first_id)
                    first_marked, _, _, first_tokens = _observe(traces, first_id, body)
                    marked, output, _, tokens = _observe(traces, second_id, body)
                    total_tokens += first_tokens + tokens
                    print(f"{label}: 출력={second.stdout.strip()!r} 토큰={first_tokens + tokens}")
                    slot.mark(
                        measured=first.returncode == 0
                        and second.returncode == 0
                        and first_marked
                        and marked,
                        result=f"{arm} 이어 가기 값={'20' in output}",
                    )
    print(rounds.summary())
    print(f"토큰 합계 {total_tokens}")
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
