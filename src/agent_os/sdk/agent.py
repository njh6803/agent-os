"""BaseAgent 프로토콜. 플러그인이 구현하고 런타임이 호출하는 계약.

결정(2026-09-19):
- 입력은 문자열 하나. 구조화된 요청은 필요가 증명될 때 ADR로 바꾼다.
- 반환은 AsyncIterator[Event]. async generator로 구현한다(원칙 V).
- LLM과 도구는 run()의 ctx 인자로 받는다. 플러그인은 sdk의 프로토콜만 본다(원칙 IV).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol

from agent_os.sdk.events import Event


class AgentContext(Protocol):
    """런타임이 run()에 넘기는 것. 플러그인은 이것으로만 LLM과 도구를 쓴다."""

    async def llm(self, prompt: str) -> str: ...

    async def tool(self, name: str, **args: object) -> str: ...


class BaseAgent(Protocol):
    def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]: ...
