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
  모양(래퍼 `tools/launch_hook.py`)으로 등록한다(`.claude/rules/tools.md` 의 새 훅 넷). 대기열 394
  뒤로 그 훅은 처음 보는 화면을 막으므로 E 와 같은 다시 부르는 갈래로 돈다. 첫 도구 결과에 그 훅의
  `LEAD`(거부 이유의 첫 문장)가 있고, 답 뒤 모델이 옮긴 첫 문장에 `ANSWERED_LEAD`(다시 부른 화면의
  계기)가 있으면 닿은 것이다. 거부 이유는 표지를 옮기라고 시키지 않아, 모델 글의 거부 표지는 보지
  않는다(읽는지는 E 가 본다). 훅 파일을 못 찾으면 래퍼가 막지 않고 알려 첫 결과에 `LEAD` 가 없다.
- `D_slow` — A 와 같은 등록에 `PROBE_HOOK_DELAY` 로 표지 훅이 `DELAY` 초를 기다린 뒤 출력하게 한다.
  A 에서 허락 요청이 훅의 끝 기록 뒤에 온 것은 허락 요청이 훅을 기다린다는 해석과, 둘이 나란히
  돌았는데 훅이 더 빨랐다는 해석이 모두 설명한다. 훅이 느려도 허락 요청이 끝 기록 뒤에 오면 앞의
  해석이 선다.
- `E_deny` — `denied.json` 이 `deny_hook.py` 를 등록한다(대기열 394). 같은 질문의 첫 호출은 거부하고
  이유에 표지(`deny_hook.DENY_MARK`)와 "표지를 옮기고 같은 입력으로 다시 부르라" 는 지시를 싣는다.
  같은 질문의 둘째 호출은 지나가게 하고 A 의 표지를 낸다. 프롬프트(`PROMPT_RETRY`)는 막힌 뒤 무엇을
  할지 말하지 않는다. 다시 부른 것이 거부 이유의 지시 때문인지, 막힌 도구를 모델이 스스로 다시 부른
  것인지는 가르지 않는다(실제 훅의 거부 이유도 다시 부르라고 적으므로 설계에는 둘 다 같다).

측정의 표지(`.claude/rules/probes.md`): 모든 갈래에서 모델이 AskUserQuestion 을 불렀고(assistant 의
`tool_use`) 그 호출의 허락 요청과 도구 결과(그 `tool_use` 의 id 를 가리키는 것)가 왔어야 측정이다.
A·D 는 훅 기록에 AskUserQuestion 입력과 끝 시각이 남아야 측정이다. C·E 는 이 셋 대신
AskUserQuestion `tool_use` 둘과 그 둘의 도구 결과가 있어야 측정이고, E 는 훅 기록의 판정 거부·통과와
끝 시각 둘도 있어야 한다. 측정이
아니거나 아래 기대와 다른 갈래가 하나라도 있으면 1로 끝난다. 갈래 이름을 주면 그 갈래만 돌리고
보고한다.

기대(모두 단언한다):
- 표지: A·D 의 답에 표지가 있고 B 의 답에 없다. 답은 도구 결과 뒤의 모델 글만 본다.
- 차례: 허락 요청이 도구 결과보다 앞이고, 모델의 `tool_use` 와 도구 결과 사이에 모델의 글이 없다.
  없으면 모델이 훅의 문장을 읽을 수 있는 첫 추론은 도구 결과(사람의 답)가 돌아온 뒤다. A·D 는 훅의
  끝 기록이 허락 요청(앱의 선택 화면)보다 앞이다.
- C·E(`report_retry`): 첫 도구 결과에 거부 표지가 있고, 첫 호출과 그 결과 사이에 허락 요청(선택
  화면)이 없고, E 는 첫 결과 뒤의 모델 글에 거부 표지가 있고(둘째 호출 앞에 옮겼는지는 찍기만 한다.
  둘째 호출은 첫 결과 뒤에 생성되어 이유가 이미 문맥에 있고, 추측할 수 없는 표지를 옮긴 것이 읽은
  표지다. 첫 판은 둘째 호출 앞의 글만 봤고, 셋째 회차가 표지를 마지막 답에서야 옮겨 결과를 본
  뒤 고쳤다), 둘째 호출이 같은 질문이고, 둘째 호출 뒤·둘째 결과 앞에 허락 요청이 있고(E
  는 둘째 훅의 끝 기록 뒤), 둘째 결과에 고른 답이 있고, 그 뒤의 모델 글에 표지(C 는
  `ANSWERED_LEAD`, E 는 A 의 표지)가 있다.

돌리는 법: 저장소 루트에서
`uv run python .scratch/harness/probes/choice_facts/probe.py <출력 디렉터리> [갈래 이름] [--saved]`.
`--saved` 를 주면 띄우지 않고 그 디렉터리에 저장한 원본을 다시 읽어 보고한다. `claude`
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
from deny_hook import DENY_MARK, key_of  # noqa: E402
from log_hook import MARK  # noqa: E402
from tools.hook_choice_facts import ANSWERED_LEAD, LEAD  # noqa: E402

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
# 다시 부르는 갈래(E)의 프롬프트. "한 번만" 을 빼고, 막힌 결과와 사용자의 답을 가르게 한다. 막힌 뒤
# 무엇을 할지는 말하지 않는다. 다시 부르는 것은 거부 이유의 지시만으로 일어나야 한다.
PROMPT_RETRY = (
    "AskUserQuestion 도구로 묻는다. 질문은 '어느 쪽으로 할까요?' 하나이고"
    " header 는 '탐침', multiSelect 는 false 다. 선택지는 둘이다."
    " 첫째는 라벨 '빨강', 설명 '서버 하나에 약 4.5초가 든다.'"
    " 둘째는 라벨 '파랑', 설명 '지금 코드는 그대로 둔다.'"
    " 사용자가 답하면(도구 결과에 고른 답이 오면), 그 호출에 붙어 온 훅 알림이나 시스템 리마인더가"
    " 있으면 그 첫 문장을 그대로 옮기고, 없으면 '알림 없음' 이라고 한국어 한 줄로 답한다."
    " AskUserQuestion 밖의 도구는 부르지 않는다."
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
    기대대로인지, `logged` 는 훅 기록이 있어야 측정인지, `env` 는 claude 에 더 주는 환경이다.
    `deny_marker` 가 있으면 다시 부르는 갈래다. 첫 호출의 거부 이유에서 그 표지를
    찾고(`report_retry`), 프롬프트는 `PROMPT_RETRY` 다. `copies_deny` 는 거부 이유가 표지를 옮기라고
    시켜 모델 글에서도 그 표지를 찾는지다."""

    args: tuple[str, ...]
    marker: str
    expect_marked: bool
    logged: bool
    env: tuple[tuple[str, str], ...] = ()
    deny_marker: str | None = None
    copies_deny: bool = False

    @property
    def prompt(self) -> str:
        return PROMPT if self.deny_marker is None else PROMPT_RETRY


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
        marker=ANSWERED_LEAD,
        expect_marked=True,
        logged=False,
        deny_marker=LEAD,
    ),
    "D_slow": Branch(
        args=("--settings", str(HERE / "hooked.json")),
        marker=MARK,
        expect_marked=True,
        logged=True,
        env=(("PROBE_HOOK_DELAY", DELAY),),
    ),
    "E_deny": Branch(
        args=("--settings", str(HERE / "denied.json")),
        marker=MARK,
        expect_marked=True,
        logged=True,
        deny_marker=DENY_MARK,
        copies_deny=True,
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
    state = out / f"{branch}.state.json"
    state.unlink(missing_ok=True)
    executable = shutil.which(COMMAND[0]) or COMMAND[0]
    extra = {"PROBE_LOG": str(hook_log), "PROBE_STATE": str(state)}
    process = subprocess.Popen(
        [executable, *COMMAND[1:], *BRANCHES[branch].args],
        cwd=ROOT,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env={**os.environ, **dict(BRANCHES[branch].env), **extra},
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
    user = {"type": "user", "message": {"role": "user", "content": BRANCHES[branch].prompt}}
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


@dataclass
class RetrySeen:
    """다시 부르는 갈래의 원본에서 찾은 것. 시각은 epoch 이다. `uses` 는 AskUserQuestion
    `tool_use` 마다 (시각, id, 질문 키), `results` 는 id 마다 첫 도구 결과의 (시각, 글),
    `decisions` 는 훅 기록마다 (받은 시각, 판정)이다."""

    uses: list[tuple[float, str, str]] = field(default_factory=list)
    results: dict[str, tuple[float, str]] = field(default_factory=dict)
    permissions: list[float] = field(default_factory=list)
    texts: list[tuple[float, str]] = field(default_factory=list)
    decisions: list[tuple[float, str]] = field(default_factory=list)
    hook_end: list[float] = field(default_factory=list)


def read_retry(out: Path, branch: str) -> RetrySeen:
    seen = RetrySeen()
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
        ):
            seen.permissions.append(at)
        for block in blocks(event, "assistant"):
            if block.get("type") == "tool_use" and block.get("name") == "AskUserQuestion":
                seen.uses.append((at, str(block.get("id")), key_of(block.get("input"))))
            elif block.get("type") == "text":
                seen.texts.append((at, " ".join(str(block.get("text")).split())))
        for block in blocks(event, "user"):
            use_id = str(block.get("tool_use_id"))
            if block.get("type") == "tool_result" and use_id not in seen.results:
                seen.results[use_id] = (at, " ".join(text_of(block.get("content")).split()))
    for raw in lines_of(out / f"{branch}.hook.jsonl"):
        record = json.loads(raw)
        if "end" in record:
            seen.hook_end.append(float(record["end"]))
        elif record.get("payload", {}).get("tool_name") == "AskUserQuestion":
            seen.decisions.append((float(record["at"]), str(record.get("decision"))))
    return seen


def retry_checks(branch: Branch, seen: RetrySeen) -> dict[str, bool]:
    """측정인 회차의 기대마다 맞았는지. 차례는 첫 호출과 둘째 호출의 시각으로 가른다. 훅 기록이
    없는 갈래는 둘째 훅의 끝 기록을, 거부 이유가 표지를 옮기라고 시키지 않는 갈래는 모델 글의 거부
    표지를 보지 않는다."""
    deny_marker = branch.deny_marker or ""
    (first, first_id, first_key), (second, second_id, second_key) = seen.uses[:2]
    first_result, first_text = seen.results[first_id]
    second_result, second_text = seen.results[second_id]
    asked = [at for at in seen.permissions if second <= at <= second_result]
    checks = {
        "첫 결과에 거부 표지": deny_marker in first_text,
        "첫 호출에 허락 요청 없음": not any(first <= at <= first_result for at in seen.permissions),
        "같은 질문을 다시 부름": first_key == second_key,
        "둘째 호출에 허락 요청": bool(asked) and (not branch.logged or seen.hook_end[1] < asked[0]),
        "둘째 결과에 고른 답": ANSWER in second_text,
        "답 뒤 모델 글에 훅 표지": any(
            at >= second_result and branch.marker in text for at, text in seen.texts
        ),
    }
    if branch.copies_deny:
        checks["첫 결과 뒤 모델 글에 거부 표지"] = any(
            at >= first_result and deny_marker in text for at, text in seen.texts
        )
    return checks


def report_retry(name: str, seen: RetrySeen) -> bool:
    """다시 부르는 갈래의 결과를 찍고, 측정이면서 기대대로인지 돌려준다."""
    branch = BRANCHES[name]
    measured = len(seen.uses) >= 2 and all(use_id in seen.results for _, use_id, _ in seen.uses[:2])
    if branch.logged:
        measured = (
            measured
            and [decision for _, decision in seen.decisions][:2] == ["deny", "pass"]
            and len(seen.hook_end) >= 2
        )
    print(f"{name}: {'측정' if measured else '측정 아님'}")
    base = seen.uses[0][0] if seen.uses else None

    def rel(at: float) -> str:
        return "없음" if base is None else f"{at - base:+.2f}초"

    for at, use_id, key in seen.uses:
        print(f"  tool_use {rel(at)} 질문 {key}")
        if (result := seen.results.get(use_id)) is not None:
            print(f"    도구 결과 {rel(result[0])}: {result[1][:300]}")
    print(f"  허락 요청: {[rel(at) for at in seen.permissions] or '없음'}")
    print(f"  훅 판정: {[(rel(at), decision) for at, decision in seen.decisions] or '없음'}")
    print(f"  훅의 끝 기록: {[rel(at) for at in seen.hook_end] or '없음'}")
    for at, text in seen.texts:
        print(f"  모델 글 {rel(at)}: {text[:240]}")
    if not measured:
        return False
    if branch.copies_deny:
        first_result, second = seen.results[seen.uses[0][1]][0], seen.uses[1][0]
        early = any(
            first_result <= at <= second and (branch.deny_marker or "") in text
            for at, text in seen.texts
        )
        print(f"  거부 표지를 둘째 호출 앞에 옮겼나(단언 밖): {'예' if early else '아니오'}")
    checks = retry_checks(branch, seen)
    for label, ok in checks.items():
        print(f"  {label}: {'기대대로' if ok else '기대와 다르다'}")
    return all(checks.values())


def main() -> int:
    args = [arg for arg in sys.argv[1:] if arg != "--saved"]
    saved = len(args) < len(sys.argv) - 1
    out = Path(args[0]).resolve()
    names = args[1:2] or list(BRANCHES)
    if any(name not in BRANCHES for name in names):
        print(f"갈래 이름은 {', '.join(BRANCHES)} 가운데 하나다.", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    for name in names if not saved else ():
        drive(name, out)
    results = [
        report(name, read_branch(out, name))
        if BRANCHES[name].deny_marker is None
        else report_retry(name, read_retry(out, name))
        for name in names
    ]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
