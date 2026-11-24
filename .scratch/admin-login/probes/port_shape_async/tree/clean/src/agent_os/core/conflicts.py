"""core 갈래의 예외. 프로브(`port_shape_async`)가 임시 사본의 `agent_os.core` 에만 둔다.

제품 코드가 아니다. http 와 어댑터가 둘 다 core 를 가져올 수 있으므로(층의 순서) 이 자리의 예외는
두 쪽이 같은 클래스를 쓴다. 대가는 core 가 '이름'이 겹치는 일을 알게 되는 것이다.
"""

from __future__ import annotations


class NameTaken(Exception):
    """이름이 이미 있다. 글에 이름을 싣지 않는다."""

    def __init__(self, name: str) -> None:
        super().__init__("이름이 이미 있다")
        self.name = name
