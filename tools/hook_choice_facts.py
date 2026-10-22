"""PreToolUse 훅(AskUserQuestion). 막는 훅이다. 세션·에이전트마다 처음 보는 선택 화면을 한 번
거부해, 질문과 선택지 설명에 든 사실을 지금 코드와 판정자에 대 보라는 이유를 화면이 뜨기 전에
읽힌다(대기열 394). 같은 화면을 다시 부르면 지나가게 하고, 받은 답과 확인받은 요약을 이 턴에 일지에
옮기라는 계기를 낸다(대기열 395).

막는 대상은 실수다. 대 보지 않은 사실을 설명에 넣은 채 화면을 올리는 것이다. 일부러 하는 우회는
막지 않는다. 대 보지 않고 같은 화면을 다시 부르면 지나간다(아래 못 보는 것).

내력. 처음 판(대기열 308)은 막지 않고 알렸다. `grilling` 의 "올리기 전"(대기열 101)이 지침으로 선
뒤에도 설명에 대 보지 않은 사실이 들어갔기 때문이다. 설계 인터뷰 2라운드의 "실패 기록 글이
ExceptionGroup 모양이 된다"는 지금 코드에 대 보지 않은 채 올렸고, "최악 약 4.5초"는 Windows 의
값이라 Linux 는 약 6.5초였는데 확인받은 합의 요약에까지 들어갔다(일지 2026-10-16-36). 그런데 이
도구에서 PreToolUse 계기는 사용자가 답한 뒤에야 읽힌다(`.claude/rules/tools.md` 의 PreToolUse 계기
훅 항목). 알림을 세 번 받은 뒤의 화면에도 대 보지 않은 사실이 다시 들어가, 101 의 7회차에서 이 꼴로
바꿨다(대기열 394). 같은 가족을 `grilling` 의 "올리기 전" 문장으로 고치는 행은 324 이고, PR 직전
리뷰 보고를 받은 턴에 옮기는 계기는 250 이다.

**이유가 닿는 때.** 거부 이유는 도구 결과(`PreToolUse:AskUserQuestion hook error: <이유>`)로
모델에게 가고, 그 호출의 허락 요청(앱이 선택 화면을 띄우는 자리)은 오지 않는다. 모델이 같은 화면을
다시 부르면 그때 화면이 뜬다. SDK 제어 모드 탐침(`.scratch/harness/probes/choice_facts/probe.py` 의
E, claude 2.1.302, haiku, 다섯 번)에서 다섯 번 모두 그랬고, 모델은 다섯 번 모두 같은 질문을 다시
불렀으며 첫 결과 뒤의 글에 이유의 표지를 옮겼다. 한 번은 둘째 호출 뒤의 마지막 답에서 옮겼고, 표지를
보는 자리(첫 결과 뒤의 글)는 결과를 본 뒤 정했다(탐침 README). 다시 부른 호출은 첫 호출 뒤
4.1~5.4초에 왔다. 화면마다 모델의 한 바퀴가 이 값이다(haiku 의 값이고 다른 모델은 재지 않았다).

**모든 화면을 막지 않는 까닭.** 훅은 대화를 읽지 못해 사실을 대 보았는지 가를 수 없다. 가르는 것은
모델이다. 그래서 다시 부른 화면까지 막으면 모든 선택 화면을 막게 되고, 그것은 거짓 양성이 많은
하드 게이트다(`CLAUDE.md` 교정 루프). 처음 한 번만 막아 이유를 먼저 읽히는 값은 화면마다 한 바퀴다.

같은 화면. 질문마다 질문 문장과 라벨의 차례가 같으면 같은 화면이다(`screen_key`). 설명·머리·미리보기
·multiSelect 는 넣지 않는다. 대 본 뒤 설명만 고쳐 다시 부른 화면을 또 막지 않기 위해서다. 표지는
임시 폴더(`tempfile.gettempdir()`) 아래 `STATE_DIR` 에 세션 ID 와 `agent_id`(서브에이전트는
컨텍스트가 따로다)와 그 열쇠의 해시로 빈 파일을 `O_EXCL` 로 만든다(`tools/launch_hook.py` 의 모양).
세션을 모르거나 표지를 쓰지 못하면 막지 않고 옛 알림을 낸다. 막으면 다시 불러도 또 막혀 끝나지 않기
때문이다. 그 알림은 답한 뒤에야 읽히므로 답을 쓰기 전에 대 보라고 시킨다.

막는 이유와 옛 알림에는 머리(`header`)·질문·라벨·설명에서 숫자(`\\d`)가 든 문장(수, 시간)을
`QUOTE_LIMIT` 개까지 옮긴다. 대 볼 자리를 짚어 주기 위해서다. 머리는 `머리:`, 질문은 `질문:`, 라벨은
`라벨:`, 설명은 그 선택지의 라벨을 앞에 붙인다. 문장은 `.`·`!`·`?` 뒤의 공백, 그 뒤에 닫는 따옴표나
괄호가 하나 붙은 자리 뒤의 공백, 줄바꿈으로 가른다(`4.5`, `v2.3.0` 은 가르지 않는다). 질문 차례로
옮기고, 질문 안에서는 머리, 질문, 선택지 차례(선택지마다 라벨, 설명)로 옮긴다. 넘친 것은 수만
적는다. 긴 문장은 `QUOTE_WIDTH` 글자에서 자른다. 입력 모양이 달라도 선택 화면은 뜨므로 막고, 가를
수 없는 조각만 건너뛴다.

못 보는 것:
- 사실을 실제로 대 보았는지. 어림이라고 적은 문장도, 대 본 뒤의 화면도 처음이면 막힌다. 대 보지
  않고 같은 화면을 다시 부르면 지나간다(일부러 하는 우회).
- 질문 문장과 라벨이 앞 화면과 같고 설명만 다른 뒤 화면. 같은 화면으로 보아 막지 않는다(거짓
  음성). 표지는 세션 동안 남아, 컨텍스트 압축 뒤에 같은 화면을 다시 올려도 막지 않는다.
- 막힌 뒤 모델이 다시 부르지 않고 글로 묻는 길. 탐침의 다섯 번에는 없었다. 앱 세션과 다른 모델에서는
  재지 않았다. 사용자가 둘째 화면을 거절하거나 답 대신 다른 메시지를 보낼 때 답 뒤 계기가 닿는지도
  재지 않았다(탐침은 답한 길만 본다).
- 숫자가 없는 사실. 지금 코드의 동작이나 바뀌는지 그대로인지("ExceptionGroup 모양이 된다")는
  옮기지 않고 이유의 일반 문장만 짚는다. 한글 수사("두 배", "세 번")도 옮기지 않는다. 숫자는
  유니코드 십진 숫자라 전각 숫자(`４`)도 센다.
- 선택지의 `preview`. 코드·화면 조각이라 옮기지 않는다.
- 문장 가르기의 빈틈. 번호 목록("1. 첫째")은 번호의 점 뒤에서 갈라, 숫자가 사실이 아닌 조각도
  옮기고 한도를 먹는다. 긴 문장은 앞에서 자르므로 숫자가 자른 자리 뒤에 있으면 옮긴 조각에 숫자가
  없다(라벨과 문장 머리로 자리만 짚는다).
- 선택 화면 도구를 거치지 않고 글로 낸 선택지. 101 의 2회차가 그 꼴이었을 수 있다(어림. 일지
  2026-10-06-10 이 사용자의 답을 `"A"` 로 적었다).
- 표지는 지우지 않아 임시 폴더에 빈 파일로 쌓인다.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from enum import Enum
from pathlib import Path
from typing import TypedDict

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

TOOL = "AskUserQuestion"
STATE_DIR = "agent-os-choice-facts"
# 막는 이유와 옛 알림의 첫 문장. 탐침의 C 갈래가 모델이 이 문장을 옮겼는지 본다.
LEAD = "선택 화면의 설명에 든 사실을 대 보았는지 확인한다"
# 같은 화면을 다시 불러 지나갈 때 내는 계기의 첫 문장.
ANSWERED_LEAD = "선택 화면의 답을 받았다"
QUOTES_LEAD = "이 화면에서 수가 든 문장"
QUOTE_LIMIT = 5
QUOTE_WIDTH = 100
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+|(?<=[.!?][\"'”’)\]」』])\s+|\n+")
_DIGIT = re.compile(r"\d")
_FACTS = (
    "질문과 선택지 설명에 적은 사실(수, 시간, 지금 코드의 동작, 바뀌는지 그대로인지)을"
    " 지금 코드와 판정자(린터, 타입 검사, 훅)에 대 보지 않았으면"
)
_JOURNAL = (
    "결정을 받은 화면(설계 인터뷰의 라운드, 승인)이면 받은 답(고른 라벨과 그 설명을 글자 그대로)과"
    " 이 화면으로 확인받은 요약을 이 턴에 일지에 옮긴다(grilling 의 '옮길 때')."
    " 일지 파일이 아직 없으면 `uv run python tools/sibling_overlap.py` 의 `다음 빈 번호` 줄에서"
    " 번호를 받아 머리 한 줄 파일을 먼저 만든다(code-review 6단계 끝과 같은 길)."
    " 미루면 컨텍스트 압축 뒤 요지만 남는다."
)
_DENY_BODY = (
    f"{LEAD}. 이 화면은 아직 사용자에게 뜨지 않았다."
    " 이 세션에서 질문 문장과 라벨이 처음인 선택 화면은"
    f" 훅이 한 번 막는다. {_FACTS} 지금 대 본다. 다르면 설명을 고치고, 대 보지 못한 것은 설명에"
    " 어림이라고 적는다(grilling 의 '올리기 전'). 그런 다음 AskUserQuestion 을 다시 부른다."
    " 질문 문장과 라벨이 같으면 설명을 고쳐도 다시 막지 않는다."
)
_ANSWERED_BODY = f"{ANSWERED_LEAD}. {_JOURNAL}"
_FALLBACK_BODY = (
    f"{LEAD}. 이 화면은 막지 못했다(세션을 모르거나 표지를 쓰지 못했다). 이 문장은 화면을 띄우기"
    f" 직전에 훅이 냈지만 사용자가 답한 뒤에야 읽힌다. {_FACTS}, 답을 쓰기 전에"
    "(다음 라운드, 합의 요약, 일지 인용, 명세, ADR 로 옮기거나 고른 대로 실행하기 전에) 대 본다."
    " 대 본 사실이 그 화면의 설명과 다르면 그 질문을 다시 묻거나 글(합의 요약 등)로 바로잡아"
    f" 확인받고, 대 보지 못한 것은 옮기는 자리에 어림이라고 적는다. {_JOURNAL}"
)


class Seen(Enum):
    """이 화면을 이 세션·에이전트에서 본 적이 있는지. 표지 파일 하나로 가르고, 갈래마다 낼 JSON 이
    다르다(`output_for`)."""

    FIRST = "처음"
    AGAIN = "다시"
    # 세션을 모르거나 표지를 쓰지 못했다.
    UNKNOWN = "모름"


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분. `tool_input` 은 JSON 값 그대로
    두고 `digit_sentences`·`screen_key` 가 칸마다 형을 본다."""

    tool_name: str
    tool_input: Json
    session_id: str
    agent_id: str


def reason_for(payload: HookPayload) -> str | None:
    """AskUserQuestion 호출이면 처음 보는 화면을 막는 이유, 아니면 None."""
    if payload.get("tool_name") != TOOL:
        return None
    return _with_quotes(_DENY_BODY, payload.get("tool_input"))


def output_for(payload: HookPayload, *, seen: Seen) -> dict[str, Json] | None:
    """훅이 낼 JSON. 처음 보는 화면이면 막고, 다시 부른 화면이면 답 뒤 계기를, 가를 수 없으면 옛
    알림을 낸다."""
    if payload.get("tool_name") != TOOL:
        return None
    specific: dict[str, Json] = {"hookEventName": "PreToolUse"}
    if seen is Seen.FIRST:
        specific["permissionDecision"] = "deny"
        specific["permissionDecisionReason"] = reason_for(payload)
    elif seen is Seen.AGAIN:
        specific["additionalContext"] = _ANSWERED_BODY
    else:
        specific["additionalContext"] = _with_quotes(_FALLBACK_BODY, payload.get("tool_input"))
    return {"hookSpecificOutput": specific}


def _with_quotes(body: str, tool_input: Json) -> str:
    quotes = digit_sentences(tool_input)
    if not quotes:
        return body
    shown = " / ".join(quotes[:QUOTE_LIMIT])
    rest = len(quotes) - QUOTE_LIMIT
    more = f" 외 {rest}개" if rest > 0 else ""
    return f"{body} {QUOTES_LEAD}: {shown}{more}"


def digit_sentences(tool_input: Json) -> list[str]:
    """머리·질문·라벨·설명에서 숫자가 든 문장을 `머리: …`·`질문: …`·`라벨: …`·`<라벨>: …` 꼴로,
    질문 차례대로."""
    if not isinstance(tool_input, dict):
        return []
    questions = tool_input.get("questions")
    if not isinstance(questions, list):
        return []
    quotes: list[str] = []
    for question in questions:
        if not isinstance(question, dict):
            continue
        quotes.extend(_quoted("머리", question.get("header")))
        quotes.extend(_quoted("질문", question.get("question")))
        options = question.get("options")
        if not isinstance(options, list):
            continue
        for option in options:
            if not isinstance(option, dict):
                continue
            label = option.get("label")
            quotes.extend(_quoted("라벨", label))
            source = label if isinstance(label, str) else "선택지"
            quotes.extend(_quoted(source, option.get("description")))
    return quotes


def _quoted(source: str, text: Json) -> list[str]:
    if not isinstance(text, str):
        return []
    quotes: list[str] = []
    for piece in _SENTENCE_BREAK.split(text):
        sentence = " ".join(piece.split())
        if not _DIGIT.search(sentence):
            continue
        if len(sentence) > QUOTE_WIDTH:
            sentence = sentence[:QUOTE_WIDTH] + "…"
        quotes.append(f"{source}: {sentence}")
    return quotes


def screen_key(tool_input: Json) -> str:
    """같은 화면인지 가르는 열쇠. 질문마다 질문 문장과 라벨의 차례다. 꼴이 다른 조각은 그대로
    넣어, 꼴이 달라도 같은 입력이면 같은 열쇠다."""
    questions = tool_input.get("questions") if isinstance(tool_input, dict) else None
    if not isinstance(questions, list):
        return json.dumps(tool_input, ensure_ascii=False, sort_keys=True)
    screens: list[Json] = []
    for question in questions:
        if not isinstance(question, dict):
            screens.append(question)
            continue
        options = question.get("options")
        labels: Json = (
            [option.get("label") if isinstance(option, dict) else option for option in options]
            if isinstance(options, list)
            else options
        )
        screens.append([question.get("question"), labels])
    return json.dumps(screens, ensure_ascii=False, sort_keys=True)


def marker_name(session_id: str, agent_id: str, key: str) -> str:
    """세션·에이전트·화면 하나의 표지 파일 이름. 셋의 해시다."""
    joined = f"{session_id}\0{agent_id}\0{key}"
    return hashlib.sha256(joined.encode("utf-8", "surrogatepass")).hexdigest()


def claim_first(name: str, directory: Path) -> Seen:
    """`directory` 에 표지 `name` 을 이 호출이 처음 만들었으면 `FIRST`, 이미 있으면 `AGAIN`, 만들지
    못하면 `UNKNOWN`. `O_EXCL` 생성 하나가 묻기와 기록을 겸해, 병렬 호출 둘이 함께 처음이라고 보지
    않는다. 폴더 자리의 파일은 makedirs 가 FileExistsError 로 알리므로 표지가 이미 있는 것과
    따로 잡는다(`tools/hook_scratch_probe_rule.py` 의 `claim_first` 와 같은 길이고, 만들지 못한
    값만 다르다)."""
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError:
        return Seen.UNKNOWN
    try:
        os.close(os.open(directory / name, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        return Seen.AGAIN
    except OSError:
        return Seen.UNKNOWN
    return Seen.FIRST


def screen_seen(payload: HookPayload) -> Seen:
    """이 화면을 이 세션·에이전트에서 본 적이 있는지. 세션을 모르거나 표지를 쓰지 못하면
    `UNKNOWN`."""
    session = payload.get("session_id")
    if not isinstance(session, str) or not session:
        return Seen.UNKNOWN
    agent = payload.get("agent_id")
    key = screen_key(payload.get("tool_input"))
    name = marker_name(session, agent if isinstance(agent, str) else "", key)
    try:
        directory = Path(tempfile.gettempdir()) / STATE_DIR
    except OSError:
        # 쓸 수 있는 임시 폴더가 없다. 표지를 쓰지 못한 것과 같다.
        return Seen.UNKNOWN
    return claim_first(name, directory)


def main() -> int:
    payload: HookPayload = json.load(sys.stdin.buffer)
    if payload.get("tool_name") != TOOL:
        return 0
    output = output_for(payload, seen=screen_seen(payload))
    if output is not None:
        print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
