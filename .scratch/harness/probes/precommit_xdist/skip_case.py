"""`skip_under_xdist.py` 가 pytest 에 넘기는 사례 모음. 저장소 테스트가 아니다.

파일 이름이 `test_` 로 시작하지 않아 `pytest .scratch` 같은 수집에 걸리지 않고, 명령줄에 파일로
줄 때만 모인다. 건너뛰는 사례 하나와 통과하는 사례 둘이다.
"""

import pytest


@pytest.mark.skip(reason="탐침: 일부러 건너뛴다")
def test_건너뛴다() -> None:
    raise AssertionError("돌지 않는다")


def test_통과한다() -> None:
    assert True


def test_하나_더_통과한다() -> None:
    assert True
