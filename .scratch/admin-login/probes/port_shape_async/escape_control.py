"""양성 대조. 이 파일은 일부러 타입 우회 검사에 걸린다. 임시 사본에 넣지 않는다.

타입 우회 검사(`tools/check_type_escapes.py` 의 `escapes_in`)가 듣는다는 표지는 금지된 이름 둘과
억제 주석 하나가 그 목록에 모두 드는 것이다. 선례는 `../port_shape/control_checks.py` 다.
"""

from typing import Any, cast


def escape(value: Any) -> int:
    return cast(int, value)


number: int = "text"  # type: ignore[assignment]
