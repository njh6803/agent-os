"""JSON 으로 직렬화 가능한 값. AgentContext 의 메서드는 이것만 주고받는다.

나중에 에이전트가 다른 프로세스나 원격에서 돌 때 계약이 그대로 유지되게 하기 위해서다.
"""

from __future__ import annotations

type Json = str | int | float | bool | None | list[Json] | dict[str, Json]
