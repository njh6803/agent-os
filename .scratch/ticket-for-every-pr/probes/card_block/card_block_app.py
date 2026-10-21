"""데스크톱 앱 세션에서 PreToolUse 훅이 세션 카드 도구(`start_session`)를 막는지 판정한다(ADR 0037).

앱 세션은 스크립트로 띄울 수 없어 절차는 사람과 그 세션이 손으로 하고, 이 프로브는 그 세션 기록과
훅 기록을 맞대 판정만 한다(선례는 `.scratch/harness/probes/worktree_overrides_app.py`).

절차.

1. 탐침할 워크트리의 `.claude/settings.local.json`(git이 추적하지 않는다)에 `log_hook.py` 를
   PreToolUse 로 등록한다. 매처는
   `mcp__ccd_session__start_session|mcp__ccd_session__list_start_targets` 이고 명령은
   `uv run --no-project python "<log_hook.py 절대 경로>" "<훅 기록 절대 경로>"` 다. 세션 도중에 더한
   등록은 그 세션에 실리지 않았다(2026-10-21, 앱 2.1.299, README). 그래서
2. 사람이 그 워크트리 폴더에서 앱의 새 세션을 열고, 그 세션에 세 호출을 차례로 시킨다.
   읽기만 하는 `list_start_targets` 한 번(등록이 실렸다는 표지), `start_session` 을
   `initiation: own_initiative` 로 한 번(막혀야 한다), `start_session` 을 없는 `proposal_id` 하나로
   한 번(훅이 지나보내 도구가 스스로 거절해야 한다). 둘째가 카드를 만들었으면 그 세션이
   `dismiss_task` 로 거둔다.
3. 이 스크립트에 그 세션의 기록 jsonl 과 훅 기록을 준다. 끝나면 등록을 지운다.

판정. 세션 기록에서 세 도구의 `tool_use` 를 찾아 같은 id 의 도구 결과와 훅 기록 줄을 맞댄다.
측정인 회차는 셋을 모두 갖춘 회차다. `list_start_targets` 의 `tool_use` 가 훅 기록에 같은 id 로
있다(등록이 실렸다). `own_initiative` 호출의 `tool_use` 가 있고 그 id 의 훅 기록 줄이 있다(훅이 그
호출을 받았다). 없는 `proposal_id` 호출의 `tool_use` 와 그 id 의 훅 기록 줄이 있다. 기대는 둘이다.
`own_initiative` 호출의 도구 결과에 `log_hook.MARK` 가 있고 카드 id(`task_id`)가 없다. 없는
`proposal_id` 호출의 도구 결과에는 `MARK` 가 없다(훅이 막지 않고 도구가 돌았다). 측정이 아니거나
기대와 다르면 1로 끝난다. 결과는 JSON 한 줄로 찍는다.

갈래. 결과에 `MARK` 가 있으면 훅이 막았다는 해석과, 같은 관찰을 낼 다른 해석(앱이 다른 까닭으로
거절했다)을 가르는 것이 표지 문구다. 그 문구는 이 탐침의 훅 이유에만 있다. 훅이 지나보낸 호출의
결과에 표지가 없다는 것이 양성 대조다. 표준 라이브러리만 쓴다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from log_hook import MARK  # noqa: E402

LIST = "mcp__ccd_session__list_start_targets"
START = "mcp__ccd_session__start_session"
TASK_ID = "task_id"
RECEIVER_REJECTION = "proposal_id must be the task_id"


def _text(content: object) -> str:
    """도구 결과의 `content`(문자열이나 블록 목록)를 한 글로."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, dict):
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return ""


def read_calls(transcript: Path) -> tuple[list[dict[str, object]], dict[str, str]]:
    """세션 기록의 두 도구 `tool_use` 와, id 마다의 도구 결과 글."""
    uses: list[dict[str, object]] = []
    results: dict[str, str] = {}
    for line in transcript.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if not isinstance(record, dict):
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "tool_use" and block.get("name") in (LIST, START):
                uses.append(block)
            if block.get("type") == "tool_result":
                use_id = block.get("tool_use_id")
                if isinstance(use_id, str):
                    results[use_id] = _text(block.get("content"))
    return uses, results


def read_log(log: Path) -> dict[str, dict[str, object]]:
    """훅 기록을 `tool_use_id` 로 묶는다."""
    by_id: dict[str, dict[str, object]] = {}
    for line in log.read_text(encoding="utf-8").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict) and isinstance(record.get("tool_use_id"), str):
            by_id[str(record["tool_use_id"])] = record
    return by_id


def judge(
    uses: list[dict[str, object]], results: dict[str, str], logged: dict[str, dict[str, object]]
) -> dict[str, object]:
    """세 호출을 맞대 측정인지와 기대를 낸다."""

    def first(name: str, pick: str) -> dict[str, object] | None:
        for use in uses:
            if use.get("name") != name:
                continue
            tool_input = use.get("input")
            if not isinstance(tool_input, dict):
                continue
            if pick == "list":
                return use
            if pick == "own" and tool_input.get("initiation") == "own_initiative":
                return use
            if (
                pick == "proposal"
                and "proposal_id" in tool_input
                and "initiation" not in tool_input
            ):
                return use
        return None

    listed = first(LIST, "list")
    own = first(START, "own")
    proposal = first(START, "proposal")
    found = {"list": listed, "own": own, "proposal": proposal}
    missing = [
        k
        for k, v in found.items()
        if v is None
        or str(v.get("id")) not in logged
        or logged[str(v.get("id"))].get("tool_name") != v.get("name")
    ]
    out: dict[str, object] = {"measured": not missing, "missing": missing}
    if own is not None:
        text = results.get(str(own.get("id")), "")
        out["own_result"] = text[:400]
        out["own_blocked"] = MARK in text and TASK_ID not in text
        record = logged.get(str(own.get("id"))) or {}
        out["own_logged_denied"] = record.get("denied")
        logged_input = record.get("tool_input")
        out["own_logged_input_keys"] = (
            sorted(logged_input) if isinstance(logged_input, dict) else None
        )
    if proposal is not None:
        text = results.get(str(proposal.get("id")), "")
        out["proposal_result"] = text[:400]
        out["proposal_passed"] = MARK not in text and RECEIVER_REJECTION in text
    out["as_expected"] = (
        bool(out.get("own_blocked"))
        and out.get("own_logged_denied") is True
        and bool(out.get("proposal_passed"))
    )
    return out


def main() -> int:
    if len(sys.argv) != 3:
        print("쓰는 법: card_block_app.py <세션 기록 jsonl> <훅 기록 jsonl>", file=sys.stderr)
        return 2
    uses, results = read_calls(Path(sys.argv[1]))
    logged = read_log(Path(sys.argv[2]))
    out = judge(uses, results, logged)
    print(json.dumps(out, ensure_ascii=False))
    return 0 if out["measured"] and out["as_expected"] else 1


if __name__ == "__main__":
    sys.exit(main())
