"""식별자 넷. 경계에서 한 번만 감싸고 JSON 형식은 문자열 그대로다(ADR 0008).

NewType이라 런타임 비용이 없고, 실행 식별자 자리에 에이전트 이름을 넣는 실수를 pyright가 잡는다.
"""

from __future__ import annotations

from typing import NewType

RunId = NewType("RunId", str)
AgentName = NewType("AgentName", str)
PluginName = NewType("PluginName", str)
Principal = NewType("Principal", str)
