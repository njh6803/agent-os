"""양성 대조. 이 파일은 일부러 두 검사에 걸린다.

pyright 가 이 폴더를 strict 로 분석한다는 표지는 `untyped` 의 `reportMissingParameterType` 이다
(strict 에서만 오류다). 타입 우회 검사(`tools/check_type_escapes.py` 의 `escapes_in`)가 듣는다는
표지는 금지된 이름 둘과 억제 주석 하나가 그 목록에 모두 드는 것이다.
"""

from typing import Any, cast


def untyped(value):
    return value


def escape(value: Any) -> int:
    return cast(int, value)


number: int = "text"  # type: ignore[assignment]
