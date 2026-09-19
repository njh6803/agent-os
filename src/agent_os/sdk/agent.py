"""BaseAgent 프로토콜. 플러그인이 구현하고 런타임이 호출하는 계약.

TODO(사용자): run 시그니처를 정한다. 정할 것 셋.
1. 입력. 문자열 하나인가, 구조화된 요청 모델인가.
2. 반환. 원칙 V에 따라 이벤트의 열이다. AsyncIterator[Event]를 권한다.
   anthropic SDK와 mcp SDK가 async 기본이라 동기 Iterator는 어댑터가 하나 더 필요하다.
3. 의존성 전달. 에이전트가 LLM과 MCP 도구를 어떻게 받는가.
   생성자 주입이면 플러그인이 core 타입을 알아야 하고(원칙 IV 위반 위험),
   run()의 컨텍스트 인자로 받으면 sdk에 정의된 프로토콜만 보면 된다.

권장 형태:

    class BaseAgent(Protocol):
        def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]: ...
"""

from __future__ import annotations

from typing import Protocol


class BaseAgent(Protocol):
    """TODO(사용자): run 시그니처를 채운다."""
