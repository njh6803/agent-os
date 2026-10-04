"""대화 요약의 한도를 글자 수로 잴 때 그것이 토큰으로 얼마인지(ADR 0022, 기본 한도).

ADR 0022 는 한도를 토큰이 아니라 글자 수로 잰다. 토큰을 세려면 셀 때마다 모델 API 를
불러 그 값도 재생해야 하기 때문이다. 그래서 기본값을 고를 때 글자 수가 토큰으로 얼마인지
알아야 비용을 가늠한다. 이 프로브는 Anthropic 의 토큰 세기 API(`count_tokens`, 모델을
부르지 않는다)로 한국어와 영어 대화 표본의 글자당 토큰 수를 잰다.

표본은 이 프로브가 지은 짧은 대화(요청과 출력)를 이어 붙여 약 4,000자로 만든 것이다.
글자 수는 파이썬 `len`(코드 포인트)이고 런타임이 한도를 잴 때와 같다. 토큰 수에서
마침표 하나뿐인 메시지의 토큰 수를 빼 메시지 틀의 몫을 덜어 낸다. 마침표의 몫까지
빼므로 표본 4,000자에서 토큰 하나 남짓 적게 센다.

    PYTHONUTF8=1 uv run --env-file .env python .scratch/conversation/probes/token_ratio.py

`ANTHROPIC_API_KEY` 가 있어야 한다. 모델 이름은 인자로 줄 수 있고 기본은 런타임의 기본
모델(`adapters/anthropic.py` 의 `DEFAULT_MODEL`)이다.
"""

from __future__ import annotations

import sys

from anthropic import Anthropic

from agent_os.adapters.anthropic import DEFAULT_MODEL

KO = (
    "요청: 내일 서울 날씨 어때?\n"
    "출력: 내일 서울은 오전에 구름이 많고 오후부터 비가 올 가능성이 높습니다. "
    "최고 기온은 21도, 최저 기온은 14도로 예상됩니다.\n"
    "요청: 그럼 우산 챙겨야 해?\n"
    "출력: 네, 오후 강수 확률이 70퍼센트라 접이식 우산을 챙기시는 편이 좋습니다. "
    "저녁 퇴근길에는 바람도 조금 불 수 있습니다.\n"
    "요청: 지난번에 물어본 회의실 예약은 어떻게 됐어?\n"
    "출력: 3층 소회의실을 목요일 오후 두 시부터 한 시간 동안 예약해 두었습니다. "
    "참석자 다섯 명에게 초대 메일도 보냈습니다.\n"
)

EN = (
    "Request: What's the weather like in Seoul tomorrow?\n"
    "Output: Tomorrow Seoul will be cloudy in the morning with a high chance of rain "
    "in the afternoon. The high is expected to be 21 degrees and the low 14.\n"
    "Request: Should I bring an umbrella then?\n"
    "Output: Yes, the chance of rain in the afternoon is 70 percent, so a folding "
    "umbrella is a good idea. It may also be a little windy on the way home.\n"
    "Request: What happened with the meeting room booking I asked about?\n"
    "Output: I booked the small meeting room on the third floor for one hour from two "
    "o'clock on Thursday afternoon and sent invitations to the five attendees.\n"
)

TARGET_CHARS = 4_000


def _sample(unit: str) -> str:
    repeats = TARGET_CHARS // len(unit) + 1
    return (unit * repeats)[:TARGET_CHARS]


def _tokens(client: Anthropic, model: str, text: str) -> int:
    counted = client.messages.count_tokens(
        model=model, messages=[{"role": "user", "content": text}]
    )
    return counted.input_tokens


def main() -> None:
    model = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    client = Anthropic()
    frame = _tokens(client, model, ".")
    print(f"모델 {model}, 틀의 몫 {frame} 토큰(마침표 하나의 메시지)")
    print("| 표본 | 글자 | 토큰(틀 뺌) | 글자당 토큰 |")
    print("|---|---|---|---|")
    for name, unit in (("한국어", KO), ("영어", EN)):
        text = _sample(unit)
        tokens = _tokens(client, model, text) - frame
        print(f"| {name} | {len(text):,} | {tokens:,} | {tokens / len(text):.3f} |")


if __name__ == "__main__":
    main()
