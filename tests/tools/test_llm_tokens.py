"""tools/llm_tokens.py 의 트레이스 토큰 합계.

`-m llm` 실행의 끝 줄은 `tests/conftest.py` 가 이것으로 찍는다.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import pytest
from tools.llm_tokens import Tokens, count, summary

HEADER = {"schema_version": "3", "run_id": "r1"}


def _line(event: Mapping[str, object]) -> str:
    return json.dumps(event, ensure_ascii=False) + "\n"


def _llm(input_tokens: int, output_tokens: int) -> dict[str, object]:
    return {
        "type": "llm_called",
        "run_id": "r1",
        "ts": "2026-10-07T00:00:00Z",
        "model": "m",
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


def _write(path: Path, *lines: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(lines), encoding="utf-8")


def test_아래_디렉터리까지_내려가_모델_호출과_요약의_토큰을_더한다(tmp_path: Path) -> None:
    """LLM 테스트는 트레이스를 `tmp_path / "t"` 처럼 한 단 아래에도 둔다.

    요약 이벤트도 모델 호출이다."""
    tool = {"type": "tool_called", "run_id": "r1", "ts": "2026-10-07T00:00:00Z", "tool": "add"}
    summarized = {
        "type": "conversation_summarized",
        "run_id": "r2",
        "ts": "2026-10-07T00:00:00Z",
        "summary": "2+3 묻자 5 답.",
        "last_covered_run": "r1",
        "model": "m",
        "input_tokens": 7,
        "output_tokens": 3,
    }
    _write(tmp_path / "r1.jsonl", _line(HEADER), _line(_llm(10, 2)), _line(tool), _line(_llm(5, 1)))
    _write(tmp_path / "t" / "r2.jsonl", _line(HEADER), _line(summarized), _line(_llm(1, 1)))

    assert count(tmp_path) == Tokens(traces=2, calls=4, input_tokens=23, output_tokens=7)


def test_토큰을_들지_않은_줄과_커밋되지_않은_줄은_세지_않는다(tmp_path: Path) -> None:
    """개행으로 끝나지 않은 마지막 줄은 어댑터도 쓰이지 않은 것으로 본다.

    ADR 0012 의 2026-09-23 이력 둘째다."""
    stringly = {**_llm(5, 5), "input_tokens": "5"}
    _write(
        tmp_path / "r1.jsonl",
        _line(HEADER),
        _line({"type": "run_started", "run_id": "r1", "ts": "2026-10-07T00:00:00Z"}),
        _line(stringly),
        "[1, 2]\n",
        "\n",
        json.dumps(_llm(9, 9)),
    )

    assert count(tmp_path) == Tokens(traces=1)


def test_응답에_줄_구분_문자가_든_호출도_한_줄로_센다(tmp_path: Path) -> None:
    """pydantic 의 `model_dump_json()` 은 U+2028 을 이스케이프하지 않는다. 문자열의 `splitlines` 는
    거기서도 갈라 이 호출을 놓친다. 어댑터처럼 바이트의 개행으로 가른다."""
    text = "a" + chr(0x2028) + "b" + chr(0x2029) + "c"  # 날것으로 쓰면 줄 구분 문자 검사가 막는다
    _write(tmp_path / "r1.jsonl", _line(HEADER), _line({**_llm(3, 4), "text": text}))

    assert count(tmp_path) == Tokens(traces=1, calls=1, input_tokens=3, output_tokens=4)


def test_UTF8_이_아닌_줄은_건너뛰고_나머지를_센다(tmp_path: Path) -> None:
    """teardown 훅에서 디코딩 오류가 나면 LLM 테스트가 에러가 된다."""
    broken = b'{"input_tokens": 100, "output_tokens": 100, "text": "\xff"}\n'
    (tmp_path / "r1.jsonl").write_bytes(broken + _line(_llm(2, 1)).encode("utf-8"))

    assert count(tmp_path) == Tokens(traces=1, calls=1, input_tokens=2, output_tokens=1)


def test_트레이스가_아닌_파일은_세지_않는다(tmp_path: Path) -> None:
    _write(tmp_path / "notes.txt", _line(_llm(100, 100)))

    assert count(tmp_path) == Tokens()


def test_jsonl_이름의_디렉터리와_읽지_못한_파일은_건너뛴다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """tryfirst teardown 훅에서 예외가 나면 pluggy 가 픽스처 정리(`teardown_exact`)를 건너뛰어
    다음 테스트의 setup 까지 깨진다(PR 직전 버그·성능 리뷰가 재현했다)."""
    (tmp_path / "x.jsonl").mkdir()
    _write(tmp_path / "locked.jsonl", _line(_llm(100, 100)))
    _write(tmp_path / "r1.jsonl", _line(_llm(2, 1)))
    read_bytes = Path.read_bytes

    def locked(path: Path) -> bytes:
        if path.name == "locked.jsonl":
            raise PermissionError("다른 프로세스가 쥐었다")
        return read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", locked)

    assert count(tmp_path) == Tokens(traces=1, calls=1, input_tokens=2, output_tokens=1)


def test_없는_디렉터리는_0이다(tmp_path: Path) -> None:
    assert count(tmp_path / "없다") == Tokens()


def test_합계_줄은_천_단위로_끊고_입력과_출력과_범위를_적는다() -> None:
    line = summary(Tokens(traces=9, calls=20, input_tokens=40190, output_tokens=1153))

    assert "LLM 토큰 합계 41,343(입력 40,190, 출력 1,153)" in line
    assert "트레이스 9개" in line
    assert "모델 호출 20건" in line
    assert "세지 못했다" not in line


def test_트레이스를_남기지_않은_LLM_테스트가_있으면_합계_줄이_그_수를_적는다() -> None:
    """모델을 바로 부르는 테스트만 돌면 0 만 찍혀 호출이 없었다고 읽힌다."""
    line = summary(Tokens(untraced_tests=1))

    assert "트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다" in line
