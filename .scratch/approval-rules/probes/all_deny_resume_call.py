"""모두 deny 인 재개의 모델 호출을 Anthropic API 가 받는지 재는 탐침. 명세의 "모두 deny 인 재개"
절이 근거로 든다. 네트워크와 `ANTHROPIC_API_KEY` 가 필요하다. 워크트리에서
`uv run --env-file ../../../.env python .scratch/approval-rules/probes/all_deny_resume_call.py` 로
돈다.

재는 것. 멈춘 사이 운영자가 에이전트의 도구를 모두 deny 로 돌리면, 재개는 멈춘 호출을 거부로 기록한
뒤 도구 호출 블록(tool_use·tool_result)이 이미 든 대화를 도구 정의 없이 모델에 보낸다(`core/loop.py`
의 `_bind` 가 빈 목록이면 도구를 붙이지 않는다. 코드를 읽었다). ADR 0044 는 API 가 그런 요청을
거부하면 원인 `model_call` 의 `run_failed` 라고 어림했고 재지 않았다. 이 탐침은 저장소의 모델
플러그인(`plugins/models/claude-opus-5`)을 실제 어댑터(`AnthropicModels.build`)로 만들고 루프와 같은
`model_caller` 로 묶어, 손으로 지은 같은 대화를 세 갈래로 보낸다.

- 도구없음: 도구 목록이 비어 `_bind` 가 맨 모델을 돌려준다. 재려는 길이다.
- 도구있음(양성 대조): 거부된 도구 `add` 의 정의를 붙인다. 같은 대화가 도구 정의와 함께는
  받아들여져야 도구없음 갈래의 거부를 대화의 모양이 아니라 도구 정의의 없음 때문이라고 읽을 수 있다.
- 선택없음: 같은 정의를 붙이되 `tool_choice` 를 `{"type": "none"}` 으로 준다. 모델이 도구를 보되
  부르지 못하게 하는 처리 후보가 API 에서 서는지 본다. langchain-anthropic 1.7.2 의 `bind_tools` 는
  문자열 `tool_choice` 로 `any`·`auto`·도구 이름만 알고 dict 는 그대로 넘긴다(`chat_models.py`
  2475~2486행. 코드를 읽었다). 그래서 dict 로 준다.

표지. 요청이 API 에 닿았을 때만 측정이다. 응답이 왔으면 `response_metadata` 에 모델 이름이 있고,
거부면 예외에 `status_code` 400 이 있다(anthropic SDK 의 `BadRequestError`). 다른 예외(키 없음,
네트워크)는 측정이 아니다. 결과의 갈래는 `수락`(응답. 도구 호출이 있었는지 덧붙인다)과 `거부`(400.
본문 앞 300자를 출력에 찍는다)다.

판정(돌리기 전에 적었다). 도구없음이 모두 거부이고 도구있음이 모두 수락이면 "도구 호출 블록이 든
대화는 도구 정의가 없으면 API 가 거부한다"가 선다. 도구없음도 수락이면 ADR 의 어림이 틀린 것이고
처리를 따로 두지 않는다. 도구있음이 거부이면 대화의 모양이 틀린 것이라 둘을 가르지 못한다.
선택없음의 수락은 그 처리 후보가 API 에서 선다는 것까지이고, 모델이 도구를 부르지 않는 것은 결과로
적되 표지가 아니다.

못 보는 것. 실제 재개 길(재생 뒤 게이트의 거부 기록)은 지나지 않고 그 길이 만드는 메시지 열을
`run_loop` 의 모양대로 손으로 지었다. 모델 하나(claude-opus-5)와 한 날의 API 만 재고, 회차가 둘이라
드문 흔들림은 잡지 못한다.
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Sequence
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage  # noqa: E402
from tools.probe_kit import Rounds  # noqa: E402

from agent_os.adapters.anthropic import AnthropicModels  # noqa: E402
from agent_os.adapters.filesystem import FilesystemPlugins  # noqa: E402
from agent_os.core.loop import ModelCaller, model_caller  # noqa: E402
from agent_os.core.ports import ChatModel, ToolSpec  # noqa: E402
from agent_os.sdk import PluginKind, PluginName  # noqa: E402

MODEL = PluginName("claude-opus-5")
ROUNDS = 2
CALL_ID = "toolu_probe_01"
ADD = ToolSpec(
    name="add",
    description="두 수를 더한다.",
    input_schema={
        "type": "object",
        "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
        "required": ["a", "b"],
    },
)
DENIED = "운영자 규칙이 거부했다: add"


def conversation() -> list[BaseMessage]:
    """멈춘 호출을 거부로 기록한 직후의 메시지 열. `run_loop` 의 모양을 손으로 지었다."""
    return [
        HumanMessage("2 더하기 3은? 도구 결과를 그대로 답한다."),
        AIMessage(
            content="",
            tool_calls=[
                {"id": CALL_ID, "name": "add", "args": {"a": 2, "b": 3}, "type": "tool_call"}
            ],
        ),
        ToolMessage(content=DENIED, tool_call_id=CALL_ID, status="error"),
    ]


def build_model() -> ChatModel:
    manifest = FilesystemPlugins(ROOT / "plugins").read_manifest(PluginKind.MODEL, MODEL)
    if manifest is None:
        raise SystemExit(f"모델 플러그인이 없다: {MODEL}")
    return AnthropicModels().build(manifest)


async def send(call: ModelCaller, label: str, rounds: Rounds, totals: dict[str, int]) -> None:
    for i in range(1, ROUNDS + 1):
        with rounds.round(f"{label} {i}") as slot:
            try:
                reply = await call(conversation())
            except Exception as error:
                if getattr(error, "status_code", None) != 400:
                    raise
                body = str(error).replace("\n", " ")[:300]
                print(f"[{label} {i}] 거부 400: {body}")
                slot.mark(measured=True, result="거부")
                continue
            model_name = reply.response_metadata.get("model")
            if not model_name:
                slot.mark(measured=False, result="응답에 모델 이름이 없다")
                continue
            usage = reply.usage_metadata or {}
            totals["input"] += int(usage.get("input_tokens", 0))
            totals["output"] += int(usage.get("output_tokens", 0))
            called = [tool_call["name"] for tool_call in reply.tool_calls]
            print(
                f"[{label} {i}] 수락 model={model_name} 도구호출={called} "
                f"글={reply.text[:80]!r} 토큰={dict(usage)}"
            )
            slot.mark(measured=True, result=f"수락(도구호출 {'있음' if called else '없음'})")


def none_caller(model: ChatModel) -> ModelCaller:
    """같은 정의를 붙이되 `tool_choice` 를 none 으로 준 호출. dict 는 그대로 넘어간다."""
    spec = {
        "name": ADD.name,
        "description": ADD.description,
        "input_schema": dict(ADD.input_schema),
    }
    bound = model.bind_tools([spec], tool_choice={"type": "none"})

    async def invoke(messages: Sequence[BaseMessage]) -> AIMessage:
        return await bound.ainvoke(messages)

    return invoke


async def main() -> int:
    model = build_model()
    rounds = Rounds()
    totals = {"input": 0, "output": 0}
    await send(model_caller(model, []), "도구없음", rounds, totals)
    await send(model_caller(model, [ADD]), "도구있음", rounds, totals)
    await send(none_caller(model), "선택없음", rounds, totals)
    print(rounds.summary())
    print(f"LLM 토큰 합계: 입력 {totals['input']} 출력 {totals['output']}")
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
