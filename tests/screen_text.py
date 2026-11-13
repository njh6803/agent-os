"""실제 모델 e2e(`-m llm_widget`, `-m llm_portal`)가 화면의 출력과 트레이스의 출력을 견주는 규칙.

화면은 마크다운 부품이 그린 글이라(ADR 0053) 원문과 글자 그대로 같지 않다. 부품은 기호(별표, 대괄호,
세로줄)를 떼고 글자를 보태지 않으므로, 화면의 글자는 원문의 글자를 차례대로 골라낸 것이다. 그래서
글자 그대로의 비교는 모델이 굵게 하나만 써도 깨지고, 규칙은 부분열이다.

- 화면 글에서 머리의 숨긴 "출력: " 을 뗀다.
- 부품이 스스로 쓰는 문구(`HIDDEN_PHRASES`)를 화면 글의 어디서든 글자 그대로 지운다. 원문에 같은
  말이 있어도 화면 글에서 글자를 지우는 것은 부분열을 깨지 않아(남은 글자의 차례가 그대로다) 판정을
  느슨하게 할 뿐이다. 다만 원문이 그 문구뿐인 출력(`이미지`만 쓴 출력)은 지운 뒤 화면 글이 비어
  걸린다.
- 유니코드 글자와 숫자만 남긴 화면 글이, 원문에서 같은 것만 남긴 것의 부분열이다. 화면 글이 비면
  걸린다.

느슨해지는 것: 화면이 원문의 일부만 보여도 지난다. 출력이 통째로 그려지는지는 부품의 단위 시험이
본다. 문자 참조(`&#44032;`) 처럼 부품이 글자를 풀어 쓰는 입력은 원문에 없는 글자가 생겨 걸린다.

지우는 말은 부품의 쓰임 문서(`web/packages/ui/src/components/molecules/Markdown.md`)가 적은 화면
문구와 같은 글자다. 문구를 바꾸면 여기도 고친다.
"""

OUTPUT_PREFIX = "출력: "
# 링크마다 숨겨 붙는 문구와 이미지 자리의 "이미지: " 에서 콜론을 뺀 말. 콜론은 글자와 숫자만 남길 때
# 떨어진다.
HIDDEN_PHRASES = ("(새 탭에서 열림)", "이미지")


def _letters_and_digits(text: str) -> str:
    return "".join(char for char in text if char.isalnum())


def _is_subsequence(part: str, whole: str) -> bool:
    remaining = iter(whole)
    return all(char in remaining for char in part)


def screen_matches_output(screen: str, output: str) -> bool:
    """화면에 선 글(`screen`)이 트레이스의 출력(`output`)에서 온 것으로 볼 수 있는가."""
    text = screen.removeprefix(OUTPUT_PREFIX)
    for phrase in HIDDEN_PHRASES:
        text = text.replace(phrase, "")
    shown = _letters_and_digits(text)
    return shown != "" and _is_subsequence(shown, _letters_and_digits(output))
