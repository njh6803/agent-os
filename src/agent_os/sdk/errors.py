"""에이전트가 잡을 수 있는 예외. sdk 만 import 하는 플러그인이 이름으로 구분하기 위해 여기 둔다."""

from __future__ import annotations


class ToolError(Exception):
    """ctx.tool() 로 직접 부른 도구가 실패했다. 메시지는 도구가 돌려준 에러 내용이다."""
