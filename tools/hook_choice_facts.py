"""PreToolUse 훅(AskUserQuestion). 선택 화면의 질문과 선택지 설명에 든 사실을 지금 코드와 판정자에
대 보았는지, 못 대 본 것은 어림이라고 적었는지 확인하라는 계기를 컨텍스트에 넣는다(대기열 308).

`grilling`의 "올리기 전"(대기열 101)이 지침으로 선 뒤에도 설명에 대 보지 않은 사실이 다시
들어갔다. 설계 인터뷰 2라운드의 "실패 기록 글이 ExceptionGroup 모양이 된다"는 지금 코드에 대 보지
않은 채 올렸고(다음 라운드 전에 재 보니 그대로였다), "최악 약 4.5초"는 Windows 의 값이라 Linux 는
약 6.5초였는데 확인받은 합의 요약에까지 들어갔다(일지 2026-10-16-36). 교정 루프의 "지침으로 적은
뒤에도 어겨지면 훅"을 따라 선택 화면 호출에 계기를 붙인다. 인터뷰 밖의 선택 화면(승인, 고르기)도
같은 도구라 함께 받는다. 101 의 2회차가 인터뷰 밖의 선택지 설명이었다(글로 낸 선택지였다면 이 훅은
보지 못한다, 아래 못 보는 것).

**알림이 닿는 때.** 훅은 화면이 뜨기 직전에 돌지만 모델은 사용자가 답한 뒤에야 이 문장을 읽는다.
원천은 `.claude/rules/tools.md` 의 PreToolUse 계기 훅 항목이고, 그 근거는 이 도구에서 잰 SDK 제어
모드 탐침(`.scratch/harness/probes/choice_facts/probe.py`)이다. 그래서 알림은 두 일을 시킨다. 방금
답을 받은 설명의 사실을 답을 쓰기 전에(다른 자리로 옮기거나 고른 대로 실행하기 전에) 대 보는 것과,
다음 화면의 설명을 쓰기 전에 대 보는 것이다. 사건에서 틀린 사실이 남은 자리도 옮긴 자리(합의
요약)였다.

화면보다 먼저 읽히는 길(사용자 프롬프트의 훅, 앞선 호출의 계기, 막는 훅의 거부 이유)도 같은 항목이
적는다. 앞의 둘은 이 화면의 설명을 보지 못한다(모델이 Skill 도구로 부른 인터뷰라면
`hook_grill_design_check` 가 첫 화면보다 먼저 닿는다. 사람이 슬래시 명령으로 시작한 인터뷰에는 그
훅이 돌지 않는다고 그 독스트링이 적는다, 어림). 거부 이유가 도구 결과로 가는 것은 AskUserQuestion
에서 재지 않았다. 막지 않는 까닭은 아래 문단이다. 이 계기를 받은 뒤에도
어겨지면 retro 가 다음 꼴을 고른다. 모든 화면을 막는 꼴은 후보가 아니다. 후보는 화면마다 처음 한
번만 거부해 이유(이 알림)를 먼저 읽히고 같은 입력을 다시 부르면 지나가게 하는 막는 훅이다(어림.
짓지도 재지도 않았다).

막지 않고 알린다. 훅은 대화를 읽지 못해 사실을 대 보았는지 가를 수 없다. 가르는 것은 모델이다.
그래서 막으면 모든 선택 화면을 막게 되고, 그것은 거짓 양성이 많은 하드 게이트다(`CLAUDE.md` 교정
루프). 알림에는 머리(`header`)·질문·라벨·설명에서 숫자(`\\d`)가 든 문장(수, 시간)을 `QUOTE_LIMIT`
개까지 옮긴다. 대 볼 자리를 짚어 주기 위해서다. 머리는 `머리:`, 질문은 `질문:`, 라벨은 `라벨:`,
설명은 그 선택지의 라벨을 앞에 붙인다. 문장은 `.`·`!`·`?` 뒤의 공백, 그 뒤에 닫는 따옴표나 괄호가
하나 붙은 자리 뒤의 공백, 줄바꿈으로 가른다(`4.5`, `v2.3.0` 은 가르지 않는다). 질문 차례로 옮기고,
질문 안에서는 머리, 질문, 선택지 차례(선택지마다 라벨, 설명)로 옮긴다. 넘친 것은 수만 적는다. 긴
문장은 `QUOTE_WIDTH` 글자에서 자른다. 입력 모양이 달라도 선택 화면은 떴으므로 알리고, 가를 수 없는
조각만 건너뛴다.

못 보는 것:
- 사실을 실제로 대 보았는지. 어림이라고 적은 문장도, 대 본 뒤의 화면도 같은 알림을 받는다.
- 숫자가 없는 사실. 지금 코드의 동작이나 바뀌는지 그대로인지("ExceptionGroup 모양이 된다")는
  옮기지 않고 알림의 일반 문장만 짚는다. 한글 수사("두 배", "세 번")도 옮기지 않는다. 숫자는
  유니코드 십진 숫자라 전각 숫자(`４`)도 센다.
- 선택지의 `preview`. 코드·화면 조각이라 옮기지 않는다.
- 문장 가르기의 빈틈. 번호 목록("1. 첫째")은 번호의 점 뒤에서 갈라, 숫자가 사실이 아닌 조각도
  옮기고 한도를 먹는다. 긴 문장은 앞에서 자르므로 숫자가 자른 자리 뒤에 있으면 옮긴 조각에 숫자가
  없다(라벨과 문장 머리로 자리만 짚는다).
- 선택 화면 도구를 거치지 않고 글로 낸 선택지. 101 의 2회차가 그 꼴이었을 수 있다(어림. 일지
  2026-10-06-10 이 사용자의 답을 `"A"` 로 적었다).
- 세션의 첫 선택 화면(압축이나 새 세션 뒤도 같다). 앞선 알림이 없어 화면 전의 상기 없이 뜬다. 이
  알림은 그 화면의 답을 쓰기 전부터 돕는다.
- 이 문장이 모델에게 닿는지는 탐침의 C 갈래가 이 훅을 등록 모양으로 붙이고 모델이 첫 문장을
  옮기게 해서 본다(스트림에는 additionalContext 가 실리지 않는다, `hook_webfetch_summary` 의
  독스트링). 사용자가 화면을 거절하거나 답 대신 다른 메시지를 보낼 때 닿는지는 재지 않았다. 탐침은
  답한 길만 본다.
"""

from __future__ import annotations

import json
import re
import sys
from typing import TypedDict

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

TOOL = "AskUserQuestion"
# 알림의 첫 문장. 세션 확인이 모델이 이 문장을 옮겼는지 본다.
LEAD = "선택 화면의 설명에 든 사실을 대 보았는지 확인한다"
QUOTES_LEAD = "이 화면에서 수가 든 문장"
QUOTE_LIMIT = 5
QUOTE_WIDTH = 100
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+|(?<=[.!?][\"'”’)\]」』])\s+|\n+")
_DIGIT = re.compile(r"\d")
_BODY = (
    f"{LEAD}. 이 문장은 화면을 띄우기 직전에 훅이 냈지만 사용자가 답한 뒤에야 읽힌다."
    " 질문과 선택지 설명에 적은 사실(수, 시간, 지금 코드의 동작, 바뀌는지 그대로인지)을"
    " 지금 코드와 판정자(린터, 타입 검사, 훅)에 대 보지 않았으면, 답을 쓰기 전에"
    "(다음 라운드, 합의 요약, 일지 인용, 명세, ADR 로 옮기거나 고른 대로 실행하기 전에) 대 본다."
    " 대 본 사실이 그 화면의 설명과 다르면 그 질문을 다시 묻거나 글(합의 요약 등)로 바로잡아"
    " 확인받고, 대 보지 못한 것은 옮기는 자리에 어림이라고 적는다."
    " 다음 선택 화면은 설명을 쓰기 전에 대 보고, 못 대 본 것은 설명에 어림이라고 적는다"
    "(grilling 의 '올리기 전'·'옮길 때')."
)


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분. `tool_input` 은 JSON 값 그대로
    두고 `digit_sentences` 가 칸마다 형을 본다."""

    tool_name: str
    tool_input: Json


def context_for(payload: HookPayload) -> str | None:
    """AskUserQuestion 호출이면 컨텍스트 문장, 아니면 None."""
    if payload.get("tool_name") != TOOL:
        return None
    quotes = digit_sentences(payload.get("tool_input"))
    if not quotes:
        return _BODY
    shown = " / ".join(quotes[:QUOTE_LIMIT])
    rest = len(quotes) - QUOTE_LIMIT
    more = f" 외 {rest}개" if rest > 0 else ""
    return f"{_BODY} {QUOTES_LEAD}: {shown}{more}"


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
