"""출력 상한(기본 16,000토큰) 안에서 모델이 낼 수 있는 깊게 겹친 글이 몇 겹인지(명세 "깊이 가드").

깊이 가드는 파싱이 끝난 나무를 보고 물러서므로 파싱에 드는 시간을 줄이지 않는다. 브라우저
프로브(`markdown_render/probe/browser.mjs` 의 `guard`)에서 들여쓴 목록 1,000겹(약 100만 자)은
가드를 켜도 원문을 보이기까지 약 22초, 500겹(약 25만 자)은 약 2.5~2.9초 걸렸다. 그 글이 출력
상한 안에서 나올 수 있는지는 글자 수가 아니라 토큰 수가 정한다. 공백이 길게 이어지면 토큰
하나가 여러 글자일 수 있다. 이 프로브는 Anthropic 의 토큰 세기 API(`count_tokens`. 모델을
부르지 않는다)로 같은 꼴의 글이 몇 토큰인지 세고, 들여쓴 목록이 상한 안에 드는 가장 깊은
깊이를 이분 탐색으로 찾는다.

글을 만드는 식은 `markdown_render/probe/inputs.mjs` 의 `DEPTH_KINDS` 와 같다(그 파일을 읽고
옮겼다). 토큰 수에서 마침표 하나뿐인 메시지의 토큰 수를 빼 메시지 틀의 몫을 덜어 낸다. 세는
것은 입력 토큰이다. 모델이 같은 글을 출력으로 낼 때의 토큰 수와 같다고 보는 것은 같은
토크나이저를 쓴다는 데 기댄 어림이다. 모델이 실제로 그런 글을 내는지는 보지 않는다.

    uv run --env-file ../../../.env python -X utf8 \
        .scratch/answer-markdown/probes/output_tokens.py claude-opus-5

`.env` 의 경로는 워크트리에서 주 체크아웃의 것을 읽는 꼴이다(`docs/constitution/operations.md`
LLM 테스트). `ANTHROPIC_API_KEY` 가 있어야 한다. 첫 인자는 API 의 모델 id, 둘째 인자(선택)는
상한이다(기본 16,000. `src/agent_os/adapters/anthropic.py` 의 `MAX_TOKENS` 와 모델 플러그인의
`max_tokens` 를 읽었다).

회차마다 표지를 본다(`.claude/rules/probes.md` 첫 항목, `tools/probe_kit.py` 의 `Rounds`).
- 세는 회차: API 가 틀의 몫보다 큰 정수를 돌려줬다. 글이 문맥 창을 넘어 세지 못하면 그 오류
  문구("prompt is too long")를 표지로 삼아 "상한 밖"으로 센다.
- 양성 대조 둘: 공백만 두 배로 늘린 글의 토큰 수가 는다(API 가 공백을 접어 세지 않는다),
  들여쓴 목록의 깊이를 두 배로 하면 토큰 수가 두 배보다 더 는다(들여쓰기가 토큰으로 세어진다.
  접어 센다면 줄 수만큼만 는다).
표지가 없는 회차가 하나라도 있으면 종료 코드가 1 이다.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import anthropic  # noqa: E402
from tools.probe_kit import Rounds  # noqa: E402

DEFAULT_CAP = 16_000
CALL_TIMEOUT = 120.0

KINDS: dict[str, Callable[[int], str]] = {
    "quote": lambda depth: ">" * depth + " a",
    "list-inline": lambda depth: "- " * depth + "a",
    "list-indent": lambda depth: "\n".join(" " * (2 * index) + "- a" for index in range(depth)),
}

# 브라우저 프로브가 본 깊이. 인용과 한 줄 목록은 가드 없이 탭이 죽거나 던지던 깊이다.
FIXED = (
    ("quote", 200),
    ("quote", 3_000),
    ("list-inline", 200),
    ("list-inline", 3_000),
    ("list-indent", 100),
    ("list-indent", 200),
    ("list-indent", 500),
    ("list-indent", 1_000),
)


class Counter:
    """토큰 세기 호출 하나. 틀의 몫을 뺀 수를 돌려주고, 문맥 창을 넘는 글은 None 이다."""

    def __init__(self, client: anthropic.Anthropic, model: str) -> None:
        self._client = client
        self._model = model
        self.frame = self._raw(".")

    def _raw(self, text: str) -> int:
        counted = self._client.messages.count_tokens(
            model=self._model,
            messages=[{"role": "user", "content": text}],
            timeout=CALL_TIMEOUT,
        )
        return counted.input_tokens

    def tokens(self, text: str) -> int | None:
        try:
            return self._raw(text) - self.frame
        except anthropic.BadRequestError as error:
            if "prompt is too long" in str(error):
                return None
            raise


def within(tokens: int | None, cap: int) -> bool:
    return tokens is not None and tokens <= cap


def describe(text: str, tokens: int | None, cap: int) -> str:
    if tokens is None:
        return f"{len(text):>9,}자 · 문맥 창을 넘어 세지 못했다 · 상한 밖"
    per_token = len(text) / tokens
    side = "상한 안" if tokens <= cap else "상한 밖"
    return f"{len(text):>9,}자 · {tokens:>7,}토큰 · 토큰당 {per_token:.1f}자 · {side}"


def main() -> int:
    if len(sys.argv) < 2:
        print("모델 id 를 인자로 준다. 예: claude-opus-5")
        return 2
    model = sys.argv[1]
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_CAP
    counter = Counter(anthropic.Anthropic(), model)
    rounds = Rounds()
    print(f"모델 {model}, 상한 {cap:,}토큰, 틀의 몫 {counter.frame}토큰(마침표 하나의 메시지)")

    with rounds.round("대조: 공백만 두 배로 늘리면 토큰이 는다") as slot:
        short = counter.tokens("a" + " " * 2_000 + "a")
        long = counter.tokens("a" + " " * 4_000 + "a")
        print(f"  대조 공백 2,000칸 {short}토큰 · 4,000칸 {long}토큰")
        if short is not None and long is not None and short > 0:
            slot.mark(measured=long > short, result="대조" if long > short else "")

    counted: dict[tuple[str, int], int | None] = {}
    for kind, depth in FIXED:
        label = f"{kind}:{depth}"
        with rounds.round(label) as slot:
            text = KINDS[kind](depth)
            tokens = counter.tokens(text)
            counted[(kind, depth)] = tokens
            print(f"  {label:<18} {describe(text, tokens, cap)}")
            if tokens is None or tokens > 0:
                slot.mark(measured=True, result="상한 안" if within(tokens, cap) else "상한 밖")

    with rounds.round("대조: 들여쓴 목록의 깊이를 두 배로 하면 토큰이 두 배보다 더 는다") as slot:
        shallow = counted.get(("list-indent", 100))
        deep = counted.get(("list-indent", 200))
        if shallow is not None and deep is not None and shallow > 0:
            ratio = deep / shallow
            print(f"  대조 들여쓴 목록 100겹 {shallow}토큰 · 200겹 {deep}토큰 · 비 {ratio:.2f}")
            slot.mark(measured=ratio > 2, result="대조" if ratio > 2 else "")

    inside = [
        depth
        for (kind, depth), tokens in counted.items()
        if kind == "list-indent" and within(tokens, cap)
    ]
    outside = [
        depth
        for (kind, depth), tokens in counted.items()
        if kind == "list-indent" and not within(tokens, cap)
    ]
    if inside and outside:
        low, high = max(inside), min(outside)
        with rounds.round("들여쓴 목록이 상한 안에 드는 가장 깊은 깊이") as slot:
            steps = 0
            while high - low > 1:
                middle = (low + high) // 2
                steps += 1
                if within(counter.tokens(KINDS["list-indent"](middle)), cap):
                    low = middle
                else:
                    high = middle
            text = KINDS["list-indent"](low)
            tokens = counter.tokens(text)
            over = counter.tokens(KINDS["list-indent"](high))
            print(
                f"  가장 깊은 깊이 {low}겹: {describe(text, tokens, cap)} (이분 탐색 {steps}걸음)"
            )
            print(f"  그 다음 깊이 {high}겹: {'세지 못했다' if over is None else f'{over:,}토큰'}")
            # 표지: 찾은 깊이는 상한 안이고 바로 다음 깊이는 상한 밖이다(경계를 실제로 봤다).
            slot.mark(
                measured=within(tokens, cap) and not within(over, cap),
                result=f"경계 {low}겹",
            )
    else:
        # 경계가 본 깊이 밖이다. 깊이마다의 회차가 이미 표지를 봤으므로 이 줄은 결과로 센다.
        where = "모두 상한 안" if inside else "모두 상한 밖"
        print(f"  들여쓴 목록의 본 깊이가 {where}이라 경계를 찾지 않았다")
        rounds.record("들여쓴 목록이 상한 안에 드는 가장 깊은 깊이", measured=True, result=where)

    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    sys.exit(main())
