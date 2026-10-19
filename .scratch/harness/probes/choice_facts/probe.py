"""선택 화면 도구(AskUserQuestion)에 PreToolUse 훅이 도는지, 그 훅의 additionalContext 를 모델이
언제 읽는지 잰다(대기열 308).

`claude -p` 의 보통 모드에는 AskUserQuestion 이 없다. 2.1.300 에서 `--tools AskUserQuestion` 을 줘도
init 이벤트의 `tools` 가 비었고, 모델이 부르자 `No such tool available: AskUserQuestion` 이 났다(이
탐침의 첫 판인 셸 스크립트의 원본 출력을 손으로 봤다. 그 스크립트와 출력은 커밋하지 않고 이 판으로
바꿨다). 사람에게 묻는 자리가 없는 모드라서다. 그래서 이 탐침은 SDK 의 제어 프로토콜로 띄운다.
`--permission-prompt-tool stdio` 를 주면 도구를 쓰기 전의 허락을 stdout 의
`control_request`(`subtype: can_use_tool`)로 묻고, stdin 의 `control_response` 로 답을 받는다.
AskUserQuestion 의 답은 허락 응답의 `updatedInput.answers` 에 질문 문장을 열쇠로 넣는다(Agent SDK
문서의 사용자 입력 처리 절의 모양을 따랐다. 판은 대지 않았다). 이 허락 요청을 앱이 선택 화면을
띄우는 자리로 본다. 앱 세션에서는 재지 않았다.

갈래:
- `A_hooked` — `hooked.json` 이 `log_hook.py` 를 AskUserQuestion 에 등록한다. 훅은 받은 입력을 받은
  시각과 함께 남기고 표지 문장(`log_hook.MARK`)을 낸 뒤 끝 시각을 남긴다. 모델에게 도구 결과가
  돌아온 뒤 그 호출에 붙어 온 알림의 첫 문장을 옮기게 한다.
- `B_control` — 등록 없이 같은 프롬프트. 모델이 표지를 지어내지 않는다는 대조군이다.
- `C_real` — `real.json` 이 실제 훅(`tools/hook_choice_facts.py`)을 `.claude/settings.json` 과 같은
  모양(래퍼 `tools/launch_hook.py`)으로 등록한다. 모델이 옮긴 첫 문장에 그 훅의 `LEAD` 가 있으면
  닿은 것이다(`.claude/rules/tools.md` 의 새 훅 넷). 훅 파일을 못 찾으면 래퍼의 알림을 옮겨 표지가
  없다.
- `D_slow` — A 와 같은 등록에 `PROBE_HOOK_DELAY` 로 표지 훅이 `DELAY` 초를 기다린 뒤 출력하게 한다.
  A 에서 허락 요청이 훅의 끝 기록 뒤에 온 것은 허락 요청이 훅을 기다린다는 해석과, 둘이 나란히
  돌았는데 훅이 더 빨랐다는 해석이 모두 설명한다. 훅이 느려도 허락 요청이 끝 기록 뒤에 오면 앞의
  해석이 선다.

측정의 표지(`.claude/rules/probes.md`): 모든 갈래에서 모델이 AskUserQuestion 을 불렀고(assistant 의
`tool_use`) 그 호출의 허락 요청과 도구 결과(그 `tool_use` 의 id 를 가리키는 것)가 왔어야 측정이다.
A·D 는 훅 기록에 AskUserQuestion 입력과 끝 시각이 남아야 측정이다. 측정이 아니거나 아래 기대와 다른
갈래가 하나라도 있으면 1로 끝난다. 갈래 이름을 주면 그 갈래만 돌리고 보고한다.

기대(모두 단언한다):
- 표지: A·C·D 의 답에 표지가 있고 B 의 답에 없다. 답은 도구 결과 뒤의 모델 글만 본다.
- 차례: 허락 요청이 도구 결과보다 앞이고, 모델의 `tool_use` 와 도구 결과 사이에 모델의 글이 없다.
  없으면 모델이 훅의 문장을 읽을 수 있는 첫 추론은 도구 결과(사람의 답)가 돌아온 뒤다. A·D 는 훅의
  끝 기록이 허락 요청(앱의 선택 화면)보다 앞이다. C 는 훅의 시각을 남기지 않아 이 단언이 없다.

돌리는 법: 저장소 루트에서
`uv run python .scratch/harness/probes/choice_facts/probe.py <출력 디렉터리> [갈래 이름]`. `claude`
CLI와 인증이 든다(갈래마다 haiku 세션 하나). `--setting-sources local` 이 사용자 설정과 프로젝트
설정의 훅을 빼서, A·D 에 붙는 훅은 `--settings` 의 것 하나다. 갈래마다 `<갈래>.tsv`(줄마다
`<epoch>\\t<in|out>\\t<줄>`)와 `<갈래>.hook.jsonl` 을 남긴다.
"""

from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
from log_hook import MARK  # noqa: E402
from tools.hook_choice_facts import LEAD  # noqa: E402

QUESTION = "어느 쪽으로 할까요?"
ANSWER = "빨강"
PROMPT = (
    "AskUserQuestion 도구를 한 번만 부른다. 질문은 '어느 쪽으로 할까요?' 하나이고"
    " header 는 '탐침', multiSelect 는 false 다. 선택지는 둘이다."
    " 첫째는 라벨 '빨강', 설명 '서버 하나에 약 4.5초가 든다.'"
    " 둘째는 라벨 '파랑', 설명 '지금 코드는 그대로 둔다.'"
    " 도구 결과가 돌아오면, 그 호출에 붙어 온 훅 알림이나 시스템 리마인더가 있으면"
    " 그 첫 문장을 그대로 옮기고, 없으면 '알림 없음' 이라고 한국어 한 줄로 답한다."
    " 다른 도구는 부르지 않는다."
)
COMMAND = [
    "claude",
    "-p",
    "--setting-sources",
    "local",
    "--strict-mcp-config",
    "--model",
    "haiku",
    "--tools",
    "AskUserQuestion",
    "--permission-prompt-tool",
    "stdio",
    "--input-format",
    "stream-json",
    "--output-format",
    "stream-json",
    "--verbose",
]
TIMEOUT = 300
DELAY = "1.5"


@dataclass(frozen=True, kw_only=True)
class Branch:
    """갈래 하나. `marker` 는 답에서 찾는 표지이고, `expect_marked` 는 그 표지가 있어야
    기대대로인지, `logged` 는 훅 기록이 있어야 측정인지, `env` 는 claude 에 더 주는 환경이다."""

    args: tuple[str, ...]
    marker: str
    expect_marked: bool
    logged: bool
    env: tuple[tuple[str, str], ...] = ()


BRANCHES = {
    "A_hooked": Branch(
        args=("--settings", str(HERE / "hooked.json")),
        marker=MARK,
        expect_marked=True,
        logged=True,
    ),
    "B_control": Branch(args=(), marker=MARK, expect_marked=False, logged=False),
    "C_real": Branch(
        args=("--settings", str(HERE / "real.json")),
        marker=LEAD,
        expect_marked=True,
        logged=False,
    ),
    "D_slow": Branch(
        args=("--settings", str(HERE / "hooked.json")),
        marker=MARK,
        expect_marked=True,
        logged=True,
        env=(("PROBE_HOOK_DELAY", DELAY),),
    ),
}


def event_of(line: str) -> dict[str, object] | None:
    """줄을 풀어 이벤트로. 풀지 못한 줄(끊겨 잘린 마지막 줄)은 이벤트가 아니다."""
    if not line.lstrip().startswith("{"):
        return None
    try:
        event = json.loads(line)
    except ValueError:
        return None
    return event if isinstance(event, dict) else None


def control(request_id: str, response: dict[str, object]) -> dict[str, object]:
    return {
        "type": "control_response",
        "response": {"subtype": "success", "request_id": request_id, "response": response},
    }


def answer_for(request: dict[str, object]) -> dict[str, object]:
    """허락 요청에 대한 답. AskUserQuestion 이면 고른 답을 넣어 허락하고, 그 밖은 거절한다."""
    tool_input = request.get("input")
    if request.get("tool_name") != "AskUserQuestion" or not isinstance(tool_input, dict):
        return {"behavior": "deny", "message": "이 탐침은 AskUserQuestion 만 허락한다."}
    updated = {**tool_input, "answers": {QUESTION: ANSWER}}
    return {"behavior": "allow", "updatedInput": updated}


def drive(branch: str, out: Path) -> None:
    """갈래 하나를 돌려 원본을 `<갈래>.tsv` 에 남긴다. 결과 이벤트가 오거나 제한 시간이 지나면
    끝낸다."""
    hook_log = out / f"{branch}.hook.jsonl"
    hook_log.unlink(missing_ok=True)
    executable = shutil.which(COMMAND[0]) or COMMAND[0]
    process = subprocess.Popen(
        [executable, *COMMAND[1:], *BRANCHES[branch].args],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env={**os.environ, **dict(BRANCHES[branch].env), "PROBE_LOG": str(hook_log)},
    )
    stdin, stdout = process.stdin, process.stdout
    assert stdin is not None and stdout is not None
    pending: queue.Queue[str | None] = queue.Queue()

    def pump() -> None:
        for raw in iter(stdout.readline, b""):
            pending.put(raw.decode("utf-8", errors="replace"))
        pending.put(None)

    threading.Thread(target=pump, daemon=True).start()
    rows: list[str] = []

    def send(message: dict[str, object]) -> bool:
        line = json.dumps(message, ensure_ascii=False)
        rows.append(f"{time.time()}\tout\t{line}\n")
        try:
            stdin.write((line + "\n").encode("utf-8"))
            stdin.flush()
        except OSError:  # 끝난 claude 는 파이프를 닫는다
            return False
        return True

    init = {
        "type": "control_request",
        "request_id": "req_init",
        "request": {"subtype": "initialize"},
    }
    user = {"type": "user", "message": {"role": "user", "content": PROMPT}}
    deadline = time.monotonic() + TIMEOUT
    try:
        if send(init) and send(user):
            while (left := deadline - time.monotonic()) > 0:
                try:
                    line = pending.get(timeout=min(left, 5))
                except queue.Empty:
                    continue
                if line is None:
                    pending.put(None)  # 끝의 배출이 같은 표지를 기다린다
                    break
                rows.append(f"{time.time()}\tin\t{line}")
                event = event_of(line)
                if event is None:
                    continue
                if event.get("type") == "result":
                    break
                request = event.get("request")
                if event.get("type") == "control_request" and isinstance(request, dict):
                    if request.get("subtype") == "can_use_tool":
                        send(control(str(event.get("request_id")), answer_for(request)))
    finally:
        try:
            stdin.close()
        except OSError:
            pass
        try:
            process.wait(timeout=60)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    # 손자가 stdout 을 쥐고 남으면 EOF 가 오지 않으므로 배출에도 제한 시간을 둔다.
    while True:
        try:
            line = pending.get(timeout=10)
        except queue.Empty:
            break
        if line is None:
            break
        rows.append(f"{time.time()}\tin\t{line}")
    (out / f"{branch}.tsv").write_text("".join(rows), encoding="utf-8")


@dataclass
class Seen:
    """원본에서 찾은 시각(epoch)과 글. 찾지 못한 것은 None 이다."""

    tool_use: float | None = None
    tool_use_id: str | None = None
    permission: float | None = None
    tool_result: float | None = None
    result_text: str = ""
    texts_between: list[str] = field(default_factory=list)
    answers_after: list[tuple[float, str]] = field(default_factory=list)
    hook_at: list[float] = field(default_factory=list)
    hook_end: list[float] = field(default_factory=list)
    hook_inputs: list[object] = field(default_factory=list)


def blocks(event: dict[str, object], role: str) -> list[dict[str, object]]:
    message = event.get("message")
    if event.get("type") != role or not isinstance(message, dict):
        return []
    content = message.get("content")
    if not isinstance(content, list):
        return []
    return [block for block in content if isinstance(block, dict)]


def text_of(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(part.get("text", "")) for part in content if isinstance(part, dict))
    return str(content)


def lines_of(path: Path) -> list[str]:
    """`\\n` 으로만 가른 비지 않은 줄. `splitlines` 는 JSON 문자열 안의 U+2028·U+0085 에서도
    가른다."""
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    return [line for line in text.split("\n") if line]


def read_branch(out: Path, branch: str) -> Seen:
    seen = Seen()
    for row in lines_of(out / f"{branch}.tsv"):
        at_text, direction, line = row.split("\t", 2)
        at = float(at_text)
        event = event_of(line)
        if direction != "in" or event is None:
            continue
        request = event.get("request")
        if (
            event.get("type") == "control_request"
            and isinstance(request, dict)
            and request.get("tool_name") == "AskUserQuestion"
            and seen.permission is None
        ):
            seen.permission = at
        for block in blocks(event, "assistant"):
            if (
                block.get("type") == "tool_use"
                and block.get("name") == "AskUserQuestion"
                and seen.tool_use is None
            ):
                seen.tool_use = at
                seen.tool_use_id = str(block.get("id"))
            elif block.get("type") == "text":
                text = " ".join(str(block.get("text")).split())
                if seen.tool_use is not None and seen.tool_result is None:
                    seen.texts_between.append(text)
                elif seen.tool_result is not None:
                    seen.answers_after.append((at, text))
        for block in blocks(event, "user"):
            if (
                block.get("type") == "tool_result"
                and seen.tool_use_id is not None
                and block.get("tool_use_id") == seen.tool_use_id
                and seen.tool_result is None
            ):
                seen.tool_result = at
                seen.result_text = " ".join(text_of(block.get("content")).split())
    for raw in lines_of(out / f"{branch}.hook.jsonl"):
        record = json.loads(raw)
        if "end" in record:
            seen.hook_end.append(float(record["end"]))
            continue
        payload = record.get("payload", {})
        if payload.get("tool_name") == "AskUserQuestion":
            seen.hook_at.append(float(record["at"]))
            seen.hook_inputs.append(payload.get("tool_input"))
    return seen


def in_order(branch: Branch, seen: Seen) -> bool:
    """기대한 차례인지. 허락 요청이 도구 결과보다 앞이고 그 사이에 모델의 글이 없으며, 훅 기록을
    보는 갈래는 첫 훅의 끝 기록이 허락 요청보다 앞이다."""
    if seen.permission is None or seen.tool_result is None or seen.texts_between:
        return False
    if seen.permission > seen.tool_result:
        return False
    if branch.logged:
        return bool(seen.hook_end) and seen.hook_end[0] < seen.permission
    return True


def report(name: str, seen: Seen) -> bool:
    """갈래의 결과를 찍고, 측정이면서 기대대로인지 돌려준다."""
    branch = BRANCHES[name]
    measured = all(at is not None for at in (seen.tool_use, seen.permission, seen.tool_result))
    if branch.logged:
        measured = measured and bool(seen.hook_at) and bool(seen.hook_end)
    print(f"{name}: {'측정' if measured else '측정 아님'}")
    base = seen.tool_use

    def rel(at: float | None) -> str:
        return "없음" if at is None or base is None else f"{at - base:+.2f}초"

    print(f"  tool_use 0초, 허락 요청 {rel(seen.permission)}, 도구 결과 {rel(seen.tool_result)}")
    print(f"  훅이 돈 시각: {[rel(at) for at in seen.hook_at] or '없음'}")
    print(f"  훅의 끝 기록: {[rel(at) for at in seen.hook_end] or '없음'}")
    for tool_input in seen.hook_inputs:
        print(f"  훅이 받은 tool_input: {json.dumps(tool_input, ensure_ascii=False)[:400]}")
    print(f"  도구 결과: {seen.result_text[:300]}")
    print(f"  tool_use 와 도구 결과 사이의 모델 글: {seen.texts_between or '없음'}")
    for at, text in seen.answers_after:
        print(f"  결과 뒤 답 {rel(at)}: {text[:240]}")
    marked = any(branch.marker in text for _, text in seen.answers_after)
    expected = marked == branch.expect_marked
    found = "있음" if marked else "없음"
    verdict = "기대대로" if expected else "기대와 다르다"
    print(f"  표지({branch.marker}) {found}, {verdict}")
    ordered = in_order(branch, seen)
    print(f"  차례: {'기대대로' if ordered else '기대와 다르다'}")
    return measured and expected and ordered


def main() -> int:
    out = Path(sys.argv[1]).resolve()
    names = sys.argv[2:3] or list(BRANCHES)
    if any(name not in BRANCHES for name in names):
        print(f"갈래 이름은 {', '.join(BRANCHES)} 가운데 하나다.", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    for name in names:
        drive(name, out)
    results = [report(name, read_branch(out, name)) for name in names]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
