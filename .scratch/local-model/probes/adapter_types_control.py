"""`check_adapter_types.py`의 양성 대조(측정이 아니다). 일부러 넣은 타입 오류만 있다.

`# 기대: <규칙>`이 달린 줄에 그 규칙의 오류가 나야 pyright 가 이 파일의 사본을 저장소의 strict
설정으로, 임시 환경에 깔린 langchain-openai 의 형식을 읽어 가며 봤다고 본다. 표시가 없는 줄에는
오류가 없어야 한다. 후보(`adapter_candidate.py`)를 가져오지 않는다. 저장소 밖에 둔 사본에서는 옆
파일의 가져오기가 풀리지 않았다(첫 판이 `reportMissingImports`로 걸렸다).
"""

from __future__ import annotations

from typing import override

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_openai import ChatOpenAI


def untyped(value):  # 기대: reportMissingParameterType, reportUnknownParameterType
    """strict 에서만 오류다. 설정이 basic 이면 이 줄이 조용하다."""
    return value  # 기대: reportUnknownVariableType


def built() -> BaseChatModel:
    return ChatOpenAI(model="m", api_key=lambda: "k")


# `ChatOpenAI`의 형식을 읽지 못하면 조용하다.
narrowed: ChatOpenAI = built()  # 기대: reportAssignmentType
# 생성자의 인자 형식. 후보가 넘기는 인자도 같은 검사를 받았다는 대조다.
ChatOpenAI(model="m", max_completion_tokens="256")  # 기대: reportArgumentType
ChatOpenAI(model="m", disable_streaming="yes")  # 기대: reportArgumentType
ChatOpenAI(model="m", api_key=3)  # 기대: reportArgumentType


class WrongOverride(ChatOpenAI):
    """재정의의 서명을 부모와 맞대 본다. 후보의 `_agenerate` 재정의도 같은 검사를 받았다."""

    @override
    async def _agenerate(  # 기대: reportIncompatibleMethodOverride
        self, messages: list[BaseMessage], stop: int = 0
    ) -> ChatResult:
        raise NotImplementedError
