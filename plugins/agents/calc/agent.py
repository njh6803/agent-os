"""calc. 계산 요청을 받아 답한다. 첫 에이전트.

모델도 도구도 직접 알지 못하고 런타임이 넘긴 ctx 로만 일한다. ctx.llm() 한 번이 루프 전체다.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from agent_os.sdk import AgentContext, Event, RunFinished

PROMPT = "계산 요청이다. 도구가 있으면 도구로 계산한다. 최종 답만 짧게 답한다.\n\n요청: {request}"


class Calc:
    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        output = await ctx.llm(PROMPT.format(request=request))
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=output)
