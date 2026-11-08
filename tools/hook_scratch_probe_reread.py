"""PreToolUse 훅(Write|Edit). 막는 훅이다. 세션 스크래치패드의 실행 스크립트를 이미 쓴 세션이
`.claude/rules/probes.md` 를 Read 로 열지 않은 채 스크래치 스크립트를 또 쓰려 하면 그 호출을 거부해,
이유를 쓰기 전에 읽힌다(대기열 426). 첫 알림은 PostToolUse 의 `hook_scratch_probe_rule` 이 낸다.

막는 대상은 실수다. 알림을 받고도 규칙 파일을 열지 않은 채 측정 스크립트를 이어 짓는 것이다.
일부러 하는 우회는 막지 않는다. 거부는 세션마다 두 번까지(`DENY_LIMIT`)고 그 뒤의 시도는
지나간다. 읽지 않고 같은 호출을 되풀이해 두 번 막힌 뒤 지나가는 것과 Bash heredoc 으로 쓰는
길이 그 우회의 대표다(아래 못 보는 것).

내력. 알림만 하던 훅(대기열 336)이 알린 세션이 규칙 파일 대신 `docs/agents/issue-tracker.md` 를
열었고, 그 세션의 측정 설계가 규칙의 사전 등록 항목(판정 정의 전부를 해시 절 안에)을 어겨 셀프 리뷰
표준 축이 Major 로 잡았다(일지 2026-10-22-08, 2026-11-05-10. 대기열 426 의 3회차). 알림은 모델에게
닿았는데 따르지 않았다. 거부 이유는 도구 결과로 모델에게 가므로(`.claude/rules/tools.md` 의
PreToolUse 항목) 알림보다 읽히는 때가 앞선다.

왜 따로 있는가. 알림 훅과 한 파일에 두려 했으나 `tools/run_hooks.py` 의 `registered_hooks` 가 훅
하나를 이벤트 둘에 등록하는 것을 거부하고(훅은 `hookEventName` 하나를 낸다), `coverage_gaps` 가
발동 사례가 없는 훅을 받지 않는다. 그래서 읽음 표지만 쓰는 PostToolUse `Read` 훅도 둘 수 없었다.
이 훅은 대신 표지 파일 없이 대화 기록(`transcript_path`)에서 상태를 읽는다. 기록에는 지금까지의
도구 호출이 모두 있다.

판정. 도구가 Write·Edit 이고 `tool_input.file_path` 가 스크래치패드의 실행
스크립트(`hook_scratch_probe_rule` 의 `is_scratch_script` 와 같은 판정이고 복사해 둔다. 훅끼리
import 하지 않는다)이며, 호출에 `agent_id` 가 없고 `transcript_path` 와 `tool_use_id` 가 있고,
기록을 읽을 수 있을 때만 센다. 기록의 줄마다(서브에이전트 쪽 줄 `isSidechain` 은 뺀다) 도구 호출
블록을 훑어, 이 호출의 `tool_use_id` 가 아닌 것 가운데 스크래치패드의 Write·Edit 의 수 `earlier` 와
`file_path` 가 `.claude/rules/probes.md` 로 끝나는 Read 의 유무를 본다. 읽음이 없고
`1 <= earlier <= DENY_LIMIT` 이면 거부한다. 첫 시도는 지나가고 알림이 나간다. 거부된 시도도 기록에
호출로 남고(이 PC의 앱 세션 기록 한 개에서 훅이 거부한 Bash·AskUserQuestion 호출마다 `tool_use`
줄이 남고 뒤에 `is_error` 도구 결과가 붙은 것을 손으로 봤다, 2026-11-08) `earlier` 를 키우므로, 읽지
않고 다시 부르면 두 번 막고 그다음에 지나간다. `earlier` 는 도구 결과(`tool_result`)가 기록에 이미
있는 시도만 센다. 같은 메시지에서 병렬로 내는 형제 호출은 결과가 아직 없어 서로를 앞선 시도로
세지 않는다. 이 호출의 기록이 PreToolUse 시점에 이미 있을 수도 없을 수도 있어(`hook_midturn_korean`)
자기 id 를 뺀다. 같은 호출이 기록에 두 줄로 나뉘어 와도 id 로 한 번만 센다.

못 보는 것:
- 측정인지. 측정이 아닌 도우미 스크립트도 둘째 시도부터 막는다(거짓 양성). 상한 두 번이 값이고,
  이유는 측정이 아니면 같은 호출을 다시 부르라고 적는다.
- 실패한 시도. old_string 이 맞지 않아 실패한 Edit 이나 사용자가 거절한 Write 도 도구 결과가 있어
  앞선 시도로 센다. 그 시도는 PostToolUse 알림이 나가지 않았어도 다음 시도를 막을 수 있다
  (거짓 양성).
- 앞선 시도가 상한을 넘게 쌓인 기록. 스크래치 스크립트 시도가 셋 이상 이어진 기록(긴 세션,
  앞 세션의 기록을 이은 재개)은 규칙 파일을 읽지 않았어도 지나간다. 거부는 첫 알림 직후의 두
  번뿐이다.
- 사전 등록 문서. 스크래치 스크립트를 한 번만 쓰고 설계 문서를 쓰는 세션은 이 훅이 한 번도
  막지 않는다. 막는 것은 둘째 스크립트부터다.
- 도구 결과가 기록에 아직 없는 시도. 병렬 형제와 결과가 쓰이기 전의 직전 호출은 센 수에 들지
  않아 거부가 늦어진다(거짓 음성). 형제의 `tool_use` 줄이 PreToolUse 보다 먼저 기록에 오는지는
  재지 않았고, 와도 센 수에 들지 않게 한 것이다.
- Bash heredoc·`>`·`sed -i` 로 쓴 스크래치 파일. 이 훅은 편집 도구에만 붙고, 센 수에도 들지 않는다.
- 서브에이전트. `agent_id` 가 있는 호출은 막지 않는다. 서브에이전트의 기록은 따로라 이 훅이 센 것이
  그쪽 호출을 보지 못한다. 서브에이전트가 연 probes.md 도 이 세션의 읽음으로 세지 않는다. 재지
  않았다.
- 저장소 프로브를 Read 할 때 `paths` 규칙이 자동으로 싣는 probes.md. 기록에 `Read` 호출로 남지
  않아 읽음이 아니다. 그 세션은 한 번 더 열라는 이유를 받는다(거짓 양성).
- 읽었는데 기록에 없는 경우. 같은 메시지의 병렬 호출 안에서 Read 와 Write 가 함께 가면 Write 의
  PreToolUse 가 Read 의 기록보다 먼저 돌 수 있다. 재지 않았다.
- 컨텍스트 압축 뒤. 읽음은 기록에 남아 압축 뒤에도 거부하지 않는다. 규칙의 내용이 컨텍스트에서
  사라졌는지는 보지 못한다.
- 기록을 읽지 못하는 호출. 기록 경로나 `tool_use_id` 가 없거나 파일을 열 수 없으면 막지 않는다.
  막으면 다시 불러도 또 막혀 끝나지 않는다. 기록의 줄 모양이 바뀌면 센 수가 0 이 되어 조용히 문이
  열린다(막는 훅의 버그는 조용히 문을 연다, `.claude/rules/tools.md`).
- 기록 전체를 훑는 값. 스크래치 스크립트를 쓸 때만 호출마다 기록 파일을 앞에서 읽는다. 규칙 파일
  Read 를 만나면 거기서 멈추고 못 만나면 끝까지 읽는다. 시간은 재지 않았다.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TypedDict

TOOLS = ("Write", "Edit")
SCRIPT_SUFFIXES = frozenset({".py", ".sh", ".bash", ".ps1", ".js", ".mjs", ".cjs", ".ts"})
DENY_LIMIT = 2
# 거부 이유의 첫 문장. 모델이 이 문장을 옮겼는지 잴 때 볼 문구다.
LEAD = "스크래치 스크립트를 또 쓰기 전에 규칙 파일을 연다"
_REASON = (
    "{lead}. 이 세션은 이미 세션 스크래치패드의 실행 스크립트를 썼고 `.claude/rules/probes.md` 를"
    " Read 로 열지 않았다. 이 호출은 아직 실행되지 않았다. 이 스크립트가 측정 스크립트(그 결과를"
    " 보고·명세·ADR·대기열의 근거로 쓸 것)라면 지금 `.claude/rules/probes.md` 를 Read 로 열어"
    " 따른 뒤 같은 호출을 다시 한다. 재려는 상황이 났다는 표지의 단언, 표지 없는 회차를 측정으로"
    " 세지 않기, 사전 등록은 판정 정의 전부를 해시 절 안에 두기가 그 파일에 있다."
    " `docs/agents/issue-tracker.md` 가 아니라 그 파일이다. 측정이 아니면 같은 호출을 다시"
    " 부른다. 읽지 않고 다시 부르면 이 훅이 한 번 더 막고, 세션마다 두 번까지만 막은 뒤 지나간다."
)
_SPLIT = re.compile(r"[\\/]+")
# 줄을 JSON 으로 풀기 전에 거르는 낱말. 스크래치패드 경로나 규칙 파일 이름이 없는 줄은 어느 쪽도
# 아니다.
_HINT = re.compile(rb"scratchpad|probes\.md", re.IGNORECASE)
# 도구 결과 줄. 풀지 않고 `tool_use_id` 만 건진다. 이스케이프된 본문 안의 글은 닫는 따옴표
# 앞에 역슬래시가 있어 맞지 않는다.
_RESULT_MARK = b'"tool_result"'
_RESULT_ID = re.compile(rb'"tool_use_id"\s*:\s*"([^"]+)"')
_RULE_TAIL = (".claude", "rules", "probes.md")


class ToolInput(TypedDict, total=False):
    file_path: object


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분. `tool_input` 은 객체가 아닌 값이
    와도 `reason_for` 가 런타임에 다시 본다."""

    tool_name: str
    tool_input: ToolInput
    transcript_path: str
    tool_use_id: str
    agent_id: str


class ToolUseBlock(TypedDict, total=False):
    type: object
    id: object
    name: object
    input: ToolInput | None


class Message(TypedDict, total=False):
    content: list[ToolUseBlock | None] | None


class Record(TypedDict, total=False):
    """대화 기록 한 줄 중 이 훅이 읽는 부분. 어느 칸이든 다른 꼴이 올 수 있어 `count_history` 가
    런타임에 다시 본다."""

    isSidechain: object
    message: Message | None


@dataclass(frozen=True)
class History:
    """대화 기록에서 센 것. `earlier` 는 앞선 스크래치 스크립트 쓰기·고치기의 수, `read` 는
    `.claude/rules/probes.md` 를 Read 로 열었는지."""

    earlier: int
    read: bool


def is_scratch_script(path: str) -> bool:
    """세션 스크래치패드(`…/claude/<프로젝트>/<세션>/scratchpad/` 아래)의 실행 스크립트인가.
    `hook_scratch_probe_rule` 의 같은 이름 함수와 같은 판정이다."""
    parts = [part.casefold() for part in _SPLIT.split(path) if part]
    if Path(parts[-1] if parts else "").suffix not in SCRIPT_SUFFIXES:
        return False
    return any(
        parts[index] == "claude" and parts[index + 3] == "scratchpad"
        for index in range(len(parts) - 4)
    )


def is_probes_rule(path: str) -> bool:
    """경로가 `.claude/rules/probes.md` 로 끝나는가(대소문자를 가리지 않고, 워크트리 안의 사본도
    같다)."""
    parts = tuple(part.casefold() for part in _SPLIT.split(path) if part)
    return parts[-len(_RULE_TAIL) :] == _RULE_TAIL


def count_history(lines: Iterable[bytes], *, own_id: str) -> History:
    """기록의 줄들에서 앞선 스크래치 스크립트 쓰기·고치기의 수와 규칙 파일 Read 의 유무를 센다.
    `own_id` 는 이 호출의 `tool_use_id` 로 세지 않는다. 같은 id 는 한 번만 센다. 도구 결과가
    기록에 아직 없는 호출(같은 메시지의 병렬 형제)은 앞선 시도로 세지 않는다. 읽음을 만나면
    더 훑지 않는다. 그때의 `earlier` 는 모은 시도의 수일 뿐 도구 결과를 따지지 않는다."""
    attempts: dict[str, None] = {}
    answered: set[str] = set()
    for line in lines:
        if _RESULT_MARK in line:
            for found in _RESULT_ID.findall(line):
                answered.add(found.decode("ascii", "replace"))
            continue
        if not _HINT.search(line):
            continue
        try:
            record: Record | None = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict) or record.get("isSidechain") is True:
            continue
        message = record.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            tool_id = block.get("id")
            if tool_id == own_id:
                continue
            tool_input = block.get("input")
            path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
            if not isinstance(path, str):
                continue
            name = block.get("name")
            if name == "Read" and is_probes_rule(path):
                return History(earlier=len(attempts), read=True)
            if name in TOOLS and is_scratch_script(path) and isinstance(tool_id, str):
                attempts[tool_id] = None
    return History(earlier=sum(tool_id in answered for tool_id in attempts), read=False)


def reason_for(payload: HookPayload) -> str | None:
    """거부할 호출이면 이유, 아니면 None. 막을 수 있는지 알 수 없으면 None 이다."""
    if payload.get("tool_name") not in TOOLS:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    path = tool_input.get("file_path")
    if not isinstance(path, str) or not is_scratch_script(path):
        return None
    if payload.get("agent_id"):
        return None
    transcript = payload.get("transcript_path")
    own_id = payload.get("tool_use_id")
    if (
        not isinstance(transcript, str)
        or not transcript
        or not isinstance(own_id, str)
        or not own_id
    ):
        return None
    try:
        with open(transcript, "rb") as handle:
            history = count_history(handle, own_id=own_id)
    except OSError:
        return None
    if history.read or not 1 <= history.earlier <= DENY_LIMIT:
        return None
    return _REASON.format(lead=LEAD)


def main() -> int:
    payload: HookPayload = json.load(sys.stdin.buffer)
    reason = reason_for(payload)
    if reason is None:
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
