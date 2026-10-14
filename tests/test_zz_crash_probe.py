"""임시: CI 에서 인터프리터를 충돌시켜 ci.yml 의 코어 덤프와 gdb 스텝을 확인한다(대기열 36).

확인 뒤 되돌린다. 로컬에서는 아무것도 하지 않는다.
"""

import ctypes
import os


def test_인터프리터를_충돌시킨다() -> None:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        ctypes.string_at(0)
