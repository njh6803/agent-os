"""PreToolUse 훅(Skill). 모델이 내장 `/security-review`를 부르면, 그 보고를 다 쓴 턴에 일지로
옮기라는 계기를 컨텍스트에 넣는다(대기열 250).

PR 직전 리뷰의 보고는 받은 턴에 일지로 옮긴다(`code-review` 6단계 끝, 대기열 244). 그 문장은 셀프
리뷰 때 실리는 스킬과 PR 뒤에 여는 `next-session` 의 `merge.md` 3(일지)에 있어, 컨텍스트 압축 뒤 PR
직전 리뷰를 받는 턴에는 맥락에 없을 수 있다. 서브에이전트 보고(`bug-perf-review`,
`coderabbit-review`)는 정의가 보고 끝에 그 한 줄을 글자 그대로 적게 해서 덮는다. 내장
`/security-review`는 고칠 수 없는 명령이고, 본 세션이 그 명령의 지시를 따라 보고를 스스로 쓴다.
그래서 그 명령을 부르는 이 순간에 문장을 넣는다. 본 세션은 CodeRabbit 좌석을
`coderabbit auth status` 한 줄로 보고(PR 템플릿의 PR 직전 리뷰 줄) 좌석이 없으면
`coderabbit-review`를 거치지 않고 대체 둘로 가므로, `coderabbit-review` 정의에 둔 문장은 흔한 길에서
읽히지 않는다(셀프 리뷰 명세 축, 일지 2026-10-28-08).

가르는 것은 입력의 `tool_input.skill` 하나다. 앞의 `/`를 벗긴 이름이 `security-review`와 같을 때만
알린다. 이 PC의 트랜스크립트에서 그 호출의 입력은 `{"skill": "security-review"}`가 136번,
`args`가 붙은 것이 한 번이었고 접두가 붙은 이름은 없었다(2026-10-19 PR 직전 `bug-perf-review`가
Skill `tool_use`를 id로 중복을 걷어 셌다. 이어 연 세션의 기록이 앞 대화를 복사해 줄로 세면
154번이다). 내장 명령이라 이 저장소의 스킬처럼 `.claude/worktrees/<이름>:` 접두로 부르지 않는다고
본다. 접두가 붙은 이름은 지나간다.

막지 않고 알린다. 계기만 주는 PreToolUse 훅은 호출을 그대로 돌린다(`.claude/rules/tools.md`). 일지를
쓰는 세션인지는 훅이 가를 수 없어 문장이 조건으로 말한다.

못 보는 것:
- 사람이 슬래시 명령(`/security-review`)으로 시작한 리뷰. Skill 도구 호출이 아니면 이 훅에 오지
  않는다고 본다(어림이고 재지 않았다).
- 일지를 쓰는 세션인지. 쓰지 않는 세션에도 같은 문장을 낸다.
- 접두가 붙은 이름(`플러그인:security-review`, `.claude/worktrees/<이름>:security-review`). 그런
  이름의 호출은 기록에 없고, 내장 명령이 아니라 다른 스킬일 수 있어 지나간다.
- 서브에이전트가 부른 호출. 입력의 `agent_id`로 가르지 않고 같은 문장을 낸다.
- 이 문장이 모델에게 닿는지는 등록 모양의 `claude -p` 세션에서 모델이 첫 문장을 옮기게 해서
  본다(`.scratch/harness/probes/security_review_hook/run.py`).
"""

from __future__ import annotations

import json
import sys
from typing import TypedDict

TOOL = "Skill"
SKILL = "security-review"
# 알림의 첫 문장. 세션 확인이 모델이 이 문장을 옮겼는지 본다.
LEAD = "일지를 쓰는 세션이면 이 /security-review의 보고를 다 쓴 그 턴에 일지로 옮긴다"
_BODY = (
    "{lead}. 고친 것과 남긴 것은 지적마다 판정한 턴에 옮긴다(code-review 6단계 끝)."
    " 컨텍스트가 압축되면 옮기지 않은 보고는 요약에 요지만 남는다(대기열 244)."
)


class ToolInput(TypedDict, total=False):
    skill: object
    args: object


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분. `tool_input` 은 객체가 아닌 값이
    와도 `context_for` 가 런타임에 다시 본다."""

    tool_name: str
    tool_input: ToolInput


def context_for(payload: HookPayload) -> str | None:
    """내장 `/security-review` 호출이면 컨텍스트 문장, 아니면 None."""
    if payload.get("tool_name") != TOOL:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    skill = tool_input.get("skill")
    if not isinstance(skill, str) or skill.lstrip("/") != SKILL:
        return None
    return _BODY.format(lead=LEAD)


def main() -> int:
    payload: HookPayload = json.load(sys.stdin.buffer)
    context = context_for(payload)
    if context is None:
        return 0
    print(
        json.dumps(
            {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": context}}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
