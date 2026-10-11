"""pytest 설정의 매개변수 id. 한국어 id 가 `\\uXXXX` 로 이스케이프되면 실패 출력에서 어느 사례인지
읽지 못하고, 매개변수 id 로 고른 `-k` 선택이 비어 변이 도구가 기준선 오류로 멈춘다(대기열 56).
이스케이프를 끄는 옵션은 줄바꿈 같은 인쇄되지 않는 문자도 그대로 두어, 그런 값의 id 가 출력 줄을
가른다. 그 문자만 `tests/conftest.py` 의 `pytest_make_parametrize_id` 가 되돌린다.

node id 는 pytest 가 도는 테스트마다 채우는 `PYTEST_CURRENT_TEST` 에서 읽는다. `request.node` 는
pytest 쪽에 반환 타입이 없어 pyright strict 에서 Unknown 이다. 그 값의 끝 모양(`(call)`)에는 기대지
않는다. 형식이 바뀌어 id 가 빠지면 이 테스트는 조용히 초록이 아니라 빨개진다."""

import os

import pytest


@pytest.mark.parametrize("사례", ["다른_자리"])
def test_한국어_매개변수_id_를_이스케이프하지_않는다(사례: str) -> None:
    assert f"[{사례}]" in os.environ["PYTEST_CURRENT_TEST"]


@pytest.mark.parametrize("사례", ["첫_줄\n둘째_줄\t끝"])
def test_인쇄되지_않는_문자만_이스케이프한다(사례: str) -> None:
    assert "[첫_줄\\n둘째_줄\\t끝]" in os.environ["PYTEST_CURRENT_TEST"]
    assert 사례 not in os.environ["PYTEST_CURRENT_TEST"]
