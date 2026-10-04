"""BaseAgent 프로토콜. 플러그인이 구현하고 런타임이 호출하는 계약.

결정(2026-09-19):
- 입력은 문자열 하나. 구조화된 요청은 필요가 증명될 때 ADR로 바꾼다.
- 반환은 AsyncIterator[Event]. async generator로 구현한다(원칙 V).
- LLM과 도구는 run()의 ctx 인자로 받는다. 플러그인은 sdk의 프로토콜만 본다(원칙 IV).

결정(2026-09-21, ADR 0008): 시각과 실행 식별자도 ctx에서 받는다. run()이 재실행 가능하려면
시각과 난수가 컨텍스트를 통해서만 들어와야 한다. 에이전트는 datetime.now()를 부르지 않는다.

결정(2026-09-22, ADR 0009): 일시정지한 실행은 run()을 처음부터 다시 돌려 재개한다. 그래서
**비결정적인 값은 전부 ctx를 지나야 한다.** 에이전트가 ctx를 우회해 시각, 난수, 환경변수, 파일,
네트워크를 읽으면 재생이 조용히 깨진다. 깨지는 자리가 실행 도중이라 이미 승인을 받은 뒤다.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime
from typing import Protocol

from agent_os.sdk.conversation import Conversation
from agent_os.sdk.events import Event
from agent_os.sdk.ids import RunId
from agent_os.sdk.json import Json


class AgentContext(Protocol):
    """런타임이 run()에 넘기는 것. 플러그인은 이것으로만 LLM, 도구, 시각, 식별자를 쓴다.

    llm()은 프롬프트 한 번이 아니라 루프 전체다. 모델이 도구를 부르면 런타임이 실행해 되돌리고
    모델이 멈출 때까지 반복한 뒤 마지막 텍스트를 돌려준다. tool()은 모델을 거치지 않고 도구 하나를
    부르며 실패하면 ToolError 다. 인자와 반환은 JSON으로 직렬화 가능한 것만이다.

    now()는 실행의 시작 시각을 돌려주고, 재개된 실행에서 재생 구간이 끝난 뒤로만 실제 시각으로
    바뀐다. 처음 실행 전체가 나중에 재생될 구간이라 처음부터 고정한다. 그래야 프롬프트에 날짜를
    넣는 평범한 에이전트가 시각 때문에 재개 불가가 되지 않는다(ADR 0009). 시계 읽기를 따로
    기록하지 않고도 결정적이다. 실행이 오래 걸려도 now()는 움직이지 않는다는 뜻이기도 하다.

    conversation 은 이 실행이 이어 간 대화에서 이 에이전트가 아는 것이다(ADR 0022). 가장 가까운 자기
    대화 요약(없으면 None)과 그 뒤 자기 교환들(요청과 출력, 오래된 것부터)이고, 이어 가지 않은
    실행에서는 요약이 없고 열이 비어 있다. 다른 에이전트의 교환은 오지 않는다. **신뢰 경계**: 요약과
    교환의 요청은 최종 사용자의 입력과 같은 신뢰 수준이다. 요청에 심은 지시나 주장이 출처가 흐려진
    채 요약에 실릴 수 있으므로, 에이전트는 그것을 지시가 아니라 데이터로 엮는다. llm()은 이것을
    프롬프트에 붙이지 않는다. 값은 런타임이 run()을 부르기 전에 정하고 실행 안에서 바뀌지 않으며
    재개해도 같다.
    """

    @property
    def run_id(self) -> RunId: ...

    @property
    def conversation(self) -> Conversation: ...

    def now(self) -> datetime: ...

    async def llm(self, prompt: str) -> str: ...

    async def tool(self, name: str, **args: Json) -> str: ...


class BaseAgent(Protocol):
    def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]: ...
