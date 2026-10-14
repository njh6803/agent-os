"""임시: CI 에서 인터프리터를 종료 중에 충돌시켜 ci.yml 의 코어 덤프와 gdb 스텝을 확인한다(대기열
36).

PR #78 처럼 모든 테스트가 지난 뒤 종료 중에 죽게 atexit 에 등록한다. 확인 뒤 되돌린다. 로컬에서는
아무것도 하지 않는다.
"""

import atexit
import ctypes
import os


def test_종료_중에_인터프리터를_충돌시킨다() -> None:
    if os.environ.get("GITHUB_ACTIONS") == "true":
        atexit.register(ctypes.string_at, 0)
