"""tools/mutate.py 의 변이 도구.

러너는 가짜다. 가짜 러너가 불리는 순간의 파일 바이트를 기록해, 변이가 든 동안과 끝난 뒤를 따로 본다.
pytest 를 하위 프로세스로 부르는 실제 러너는 실제 실행으로 확인한다(`.claude/rules/tests.md`).
"""

from __future__ import annotations

import stat
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest
from tools.mutate import (
    PytestResult,
    RestoreError,
    SpecError,
    load_spec,
    main,
    measure,
    select,
)

_초록 = PytestResult(0, "1 passed in 0.01s\n")
_빨강 = PytestResult(1, "FAILED tests/test_x.py::test_x - AssertionError\n1 failed in 0.01s\n")


def _파일을_둔다(root: Path, 상대_경로: str, 내용: bytes) -> Path:
    path = root / 상대_경로
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(내용)
    return path


def _변이_파일(*, old: str, new: str, expect: str = "red", file: str = "src/m.py") -> str:
    return f"""
[[mutation]]
name = "하나"
tests = ["tests/test_x.py"]
expect = "{expect}"

[[mutation.edit]]
file = "{file}"
old = '''{old}'''
new = '''{new}'''
"""


def test_변이가_든_동안_러너는_바뀐_바이트를_보고_끝나면_원래_바이트로_돌아온다(
    tmp_path: Path,
) -> None:
    """CRLF 와 UTF-8 이 아닌 바이트까지 그대로다.

    텍스트로 되돌린 변이 스크립트가 줄 끝을 CRLF 로 바꿔 두 번 남겼다(대기열 29).
    """
    원래 = b"def f():\r\n    return 1\r\n# \xff\n"
    path = _파일을_둔다(tmp_path, "src/m.py", 원래)
    본_것: list[bytes] = []

    def 러너(args: Sequence[str]) -> PytestResult:
        본_것.append(path.read_bytes())
        return _빨강 if b"return 2" in path.read_bytes() else _초록

    code = measure(
        load_spec(_변이_파일(old="return 1", new="return 2")),
        root=tmp_path,
        runner=러너,
        out=lambda _: None,
    )

    assert 본_것 == [원래, b"def f():\r\n    return 2\r\n# \xff\n"]
    assert path.read_bytes() == 원래
    assert code == 0


def test_변이한_소스의_바이트코드_캐시는_변이_동안과_되돌린_뒤에_없다(tmp_path: Path) -> None:
    """캐시는 소스의 수정 시각(초)과 크기로만 맞춰 본다. 같은 크기의 변이가 같은 초에 쓰이면 원래
    바이트코드가 그대로 돌고, 거꾸로 변이 동안 생긴 캐시가 남으면 되돌린 원본이 변이된 바이트코드로
    돈다. pytest 의 assertion rewrite 캐시도 같은 자리에 같은 방식으로 산다. 이웃 소스의 캐시는
    건드리지 않는다(PR #89 CodeRabbit)."""
    path = _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    캐시 = [
        _파일을_둔다(tmp_path, "src/__pycache__/m.cpython-312.pyc", b"old"),
        _파일을_둔다(tmp_path, "src/__pycache__/m.cpython-312-pytest-9.1.1.pyc", b"old"),
    ]
    이웃 = _파일을_둔다(tmp_path, "src/__pycache__/mm.cpython-312.pyc", b"old")
    변이_동안: list[bool] = []

    def 러너(args: Sequence[str]) -> PytestResult:
        if b"x = 2" not in path.read_bytes():
            return _초록
        변이_동안.extend(pyc.exists() for pyc in 캐시)
        for pyc in 캐시:  # 변이된 소스의 캐시를 누군가 남겼다
            pyc.write_bytes(b"mutated")
        return _빨강

    measure(
        load_spec(_변이_파일(old="x = 1", new="x = 2")),
        root=tmp_path,
        runner=러너,
        out=lambda _: None,
    )

    assert 변이_동안 == [False, False]
    assert [pyc.exists() for pyc in 캐시] == [False, False]
    assert 이웃.exists()


def test_러너가_예외를_던져도_원래_바이트로_돌아온다(tmp_path: Path) -> None:
    원래 = b"x = 1\r\n"
    path = _파일을_둔다(tmp_path, "src/m.py", 원래)

    def 러너(args: Sequence[str]) -> PytestResult:
        if b"x = 2" in path.read_bytes():
            raise KeyboardInterrupt
        return _초록

    with pytest.raises(KeyboardInterrupt):
        measure(
            load_spec(_변이_파일(old="x = 1", new="x = 2")),
            root=tmp_path,
            runner=러너,
            out=lambda _: None,
        )

    assert path.read_bytes() == 원래


def _변이면(path: Path, 표지: bytes, 변이: PytestResult) -> Callable[[Sequence[str]], PytestResult]:
    """파일에 표지가 있으면(변이가 들었으면) `변이`, 아니면 초록을 내는 러너."""

    def 러너(args: Sequence[str]) -> PytestResult:
        return 변이 if 표지 in path.read_bytes() else _초록

    return 러너


@pytest.mark.parametrize(
    ("expect", "변이_결과", "기대_코드"),
    [("red", _빨강, 0), ("red", _초록, 1), ("green", _초록, 0), ("green", _빨강, 1)],
)
def test_기대와_결과가_어긋나면_알리고_1을_돌려준다(
    tmp_path: Path, expect: str, 변이_결과: PytestResult, 기대_코드: int
) -> None:
    """빨강을 기대한 변이가 초록으로 지나간 것을 아무도 몰랐다(대기열 29의 5회차)."""
    path = _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    줄: list[str] = []

    code = measure(
        load_spec(_변이_파일(old="x = 1", new="x = 2", expect=expect)),
        root=tmp_path,
        runner=_변이면(path, b"x = 2", 변이_결과),
        out=줄.append,
    )

    assert code == 기대_코드
    assert any("어긋" in 한줄 for 한줄 in 줄) == (기대_코드 == 1)


def test_수집_오류는_빨강이_아니라_오류라서_빨강을_기대해도_어긋난다(tmp_path: Path) -> None:
    """문법 오류로 모든 것이 빨간 변이는 테스트의 이빨을 재지 않는다."""
    path = _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    줄: list[str] = []
    수집_오류 = PytestResult(2, "ERROR tests/test_x.py\nInterrupted: 1 error during collection\n")

    code = measure(
        load_spec(_변이_파일(old="x = 1", new="x = (")),
        root=tmp_path,
        runner=_변이면(path, b"x = (", 수집_오류),
        out=줄.append,
    )

    assert code == 1
    assert any("오류" in 한줄 for 한줄 in 줄)


def test_반복하면_매번_기대와_같아야_한다(tmp_path: Path) -> None:
    path = _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    결과들 = iter([_빨강, _초록, _빨강])
    불린_횟수 = 0

    def 러너(args: Sequence[str]) -> PytestResult:
        nonlocal 불린_횟수
        if b"x = 2" not in path.read_bytes():
            return _초록
        불린_횟수 += 1
        return next(결과들)

    변이 = _변이_파일(old="x = 1", new="x = 2").replace(
        'expect = "red"', 'expect = "red"\nrepeat = 3'
    )

    code = measure(load_spec(변이), root=tmp_path, runner=러너, out=lambda _: None)

    assert 불린_횟수 == 3
    assert code == 1


def test_기준선이_초록이_아니면_변이를_넣지_않는다(tmp_path: Path) -> None:
    """기준선이 빨간데 변이가 빨가면 그 빨강은 아무것도 말하지 않는다."""
    원래 = b"x = 1\n"
    path = _파일을_둔다(tmp_path, "src/m.py", 원래)
    본_것: list[bytes] = []

    def 러너(args: Sequence[str]) -> PytestResult:
        본_것.append(path.read_bytes())
        return _빨강

    줄: list[str] = []
    code = measure(
        load_spec(_변이_파일(old="x = 1", new="x = 2")),
        root=tmp_path,
        runner=러너,
        out=줄.append,
    )

    assert code == 1
    assert 본_것 == [원래]
    assert any("기준선" in 한줄 for 한줄 in 줄)


def _부르면_안_되는_러너(args: Sequence[str]) -> PytestResult:
    raise AssertionError("변이 파일 오류인데 테스트를 돌렸다")


@pytest.mark.parametrize("내용", [b"y = 1\n", b"x = 1\nx = 1\n"], ids=["없다", "두_번"])
def test_원문이_정확히_한_번이_아니면_아무_파일도_쓰지_않고_변이_파일_오류다(
    tmp_path: Path, 내용: bytes
) -> None:
    """앞의 변이가 맞아도 뒤의 변이가 틀리면 기준선도 돌지 않는다."""
    맞는_파일 = _파일을_둔다(tmp_path, "src/a.py", b"a = 1\n")
    _파일을_둔다(tmp_path, "src/m.py", 내용)
    변이 = _변이_파일(old="a = 1", new="a = 2", file="src/a.py") + _변이_파일(
        old="x = 1", new="x = 2"
    )

    with pytest.raises(SpecError, match="src/m.py"):
        measure(
            load_spec(변이.replace('name = "하나"', 'name = "둘"', 1)),
            root=tmp_path,
            runner=_부르면_안_되는_러너,
            out=lambda _: None,
        )

    assert 맞는_파일.read_bytes() == b"a = 1\n"


def test_한_변이의_편집_여럿은_앞_편집의_결과_위에_차례로_들어간다(tmp_path: Path) -> None:
    path = _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    본_것: list[bytes] = []

    def 러너(args: Sequence[str]) -> PytestResult:
        본_것.append(path.read_bytes())
        return _초록 if len(본_것) == 1 else _빨강

    변이 = _변이_파일(old="x = 1", new="x = 2") + "\n".join(
        ["[[mutation.edit]]", 'file = "src/m.py"', "old = 'x = 2'", "new = 'x = 3'", ""]
    )

    measure(load_spec(변이), root=tmp_path, runner=러너, out=lambda _: None)

    assert 본_것[1] == b"x = 3\n"
    assert path.read_bytes() == b"x = 1\n"


def test_저장소_밖을_가리키는_파일은_변이_파일_오류다(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    바깥 = _파일을_둔다(tmp_path, "outside.py", b"x = 1\n")

    with pytest.raises(SpecError, match="저장소 밖"):
        measure(
            load_spec(_변이_파일(old="x = 1", new="x = 2", file="../outside.py")),
            root=root,
            runner=_부르면_안_되는_러너,
            out=lambda _: None,
        )

    assert 바깥.read_bytes() == b"x = 1\n"


@pytest.mark.parametrize(
    ("바꿀_것", "바꾼_것"),
    [
        ('expect = "red"', 'expect = "빨강"'),
        ('expect = "red"', 'expect = "red"\nrepaet = 3'),
        ('tests = ["tests/test_x.py"]', 'tests = "tests/test_x.py"'),
        ('expect = "red"', 'expect = "red"\nrepeat = 0'),
    ],
    ids=["기대는_red_나_green", "모르는_키", "tests_는_목록", "반복은_1_이상"],
)
def test_변이_파일의_모양이_틀리면_오류다(바꿀_것: str, 바꾼_것: str) -> None:
    with pytest.raises(SpecError):
        load_spec(_변이_파일(old="x = 1", new="x = 2").replace(바꿀_것, 바꾼_것))


def test_이름이_겹치면_변이_파일_오류다() -> None:
    """이름으로 골라 다시 돌리므로 이름이 변이 하나를 가리켜야 한다."""
    with pytest.raises(SpecError, match="하나"):
        load_spec(_변이_파일(old="x = 1", new="x = 2") * 2)


def test_이름으로_고른다() -> None:
    변이 = load_spec(
        _변이_파일(old="x = 1", new="x = 2")
        + _변이_파일(old="x = 1", new="x = 3").replace("하나", "둘")
    )

    assert [m.name for m in select(변이, ["둘"]).mutation] == ["둘"]
    assert select(변이, []) == 변이
    with pytest.raises(SpecError, match="셋"):
        select(변이, ["셋"])


@pytest.mark.parametrize(
    ("결과", "판정"),
    [
        (PytestResult(0, "3 passed in 0.10s\n"), "green"),
        (PytestResult(1, "1 failed, 2 passed in 0.10s\n"), "red"),
        (PytestResult(2, "Interrupted: 1 error during collection\n"), "error"),
        (PytestResult(4, "ERROR: file or directory not found: tests/x.py\n"), "error"),
        (PytestResult(5, "no tests ran in 0.01s\n"), "error"),
        (PytestResult(0, "2 passed, 1 skipped in 0.10s\n"), "error"),
    ],
    ids=["통과", "실패", "수집_오류", "없는_경로", "선택된_테스트_없음", "skip_이_섞였다"],
)
def test_pytest_의_종료_코드와_요약으로_판정한다(결과: PytestResult, 판정: str) -> None:
    """skip 이 섞인 초록은 초록이 아니다(원칙 II). 재지 않은 테스트가 있다."""
    assert 결과.outcome == 판정


def test_빨간_테스트의_노드_아이디를_짧은_요약에서_읽는다() -> None:
    결과 = PytestResult(
        1,
        "..F\n"
        "FAILED tests/a.py::test_x[1] - assert 0\n"
        "ERROR tests/b.py::test_y - fixture 'z' not found\n"
        "1 failed, 1 error in 0.10s\n",
    )

    assert 결과.failed == ["tests/a.py::test_x[1]", "tests/b.py::test_y"]


def _잠그는_러너(잠글_파일: Path, 표지: bytes) -> Callable[[Sequence[str]], PytestResult]:
    """변이가 든 동안 파일을 읽기 전용으로 바꿔, 되돌리는 쓰기가 `PermissionError` 가 되게 한다."""

    def 러너(args: Sequence[str]) -> PytestResult:
        if 표지 not in 잠글_파일.read_bytes():
            return _초록
        잠글_파일.chmod(stat.S_IREAD)
        return _빨강

    return 러너


def _두_파일_변이(tmp_path: Path) -> tuple[Path, Path, str]:
    m = _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    a = _파일을_둔다(tmp_path, "src/a.py", b"a = 1\n")
    변이 = _변이_파일(old="x = 1", new="x = 2") + "\n".join(
        ["[[mutation.edit]]", 'file = "src/a.py"', "old = 'a = 1'", "new = 'a = 2'", ""]
    )
    return m, a, 변이


def test_되돌리지_못한_파일이_있으면_RestoreError_이고_나머지는_되돌린다(tmp_path: Path) -> None:
    """되돌림 실패를 명세 오류로 알리면 변이된 채 남은 파일을 아무도 모른다(셀프 리뷰 Major)."""
    m, a, 변이 = _두_파일_변이(tmp_path)
    try:
        with pytest.raises(RestoreError, match="src/m.py"):
            measure(
                load_spec(변이),
                root=tmp_path,
                runner=_잠그는_러너(m, b"x = 2"),
                out=lambda _: None,
            )

        assert a.read_bytes() == b"a = 1\n"
        assert m.read_bytes() == b"x = 2\n"
    finally:
        m.chmod(stat.S_IREAD | stat.S_IWRITE)


def _변이_파일을_쓴다(tmp_path: Path, 내용: str) -> str:
    path = tmp_path / "mutations.toml"
    path.write_text(내용, encoding="utf-8")
    return str(path)


def test_main_은_변이_파일을_읽지_못하면_아무것도_돌리지_않고_2다(tmp_path: Path) -> None:
    """UTF-8 이 아닌 변이 파일이 트레이스백의 1 이 되면 어긋남의 1 과 구별되지 않는다."""
    깨진_파일 = tmp_path / "broken.toml"
    깨진_파일.write_bytes(b'name = "\xff"\n')
    _파일을_둔다(tmp_path, "src/m.py", b"y = 1\n")
    원문_없음 = _변이_파일을_쓴다(tmp_path, _변이_파일(old="x = 1", new="x = 2"))

    for argv in ([], [str(tmp_path / "없다.toml")], [str(깨진_파일)], [원문_없음]):
        code = main(argv, root=tmp_path, runner=_부르면_안_되는_러너, out=lambda _: None)
        assert code == 2, argv


def test_main_은_기대대로면_0_어긋나면_1이다(tmp_path: Path) -> None:
    path = _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    변이 = _변이_파일을_쓴다(tmp_path, _변이_파일(old="x = 1", new="x = 2"))

    assert main([변이], root=tmp_path, runner=_변이면(path, b"x = 2", _빨강), out=print) == 0
    assert main([변이], root=tmp_path, runner=_변이면(path, b"x = 2", _초록), out=print) == 1


def test_main_은_되돌리지_못하면_3이고_git_diff_를_가리킨다(tmp_path: Path) -> None:
    m, _, 변이 = _두_파일_변이(tmp_path)
    줄: list[str] = []
    try:
        code = main(
            [_변이_파일을_쓴다(tmp_path, 변이)],
            root=tmp_path,
            runner=_잠그는_러너(m, b"x = 2"),
            out=줄.append,
        )
    finally:
        m.chmod(stat.S_IREAD | stat.S_IWRITE)

    assert code == 3
    assert any("git diff" in 한줄 and "src/m.py" in 한줄 for 한줄 in 줄)


def test_main_은_테스트를_돌리지_못하면_3이고_변이는_되돌렸다(tmp_path: Path) -> None:
    path = _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")

    def 러너(args: Sequence[str]) -> PytestResult:
        if b"x = 2" in path.read_bytes():
            raise FileNotFoundError("python 이 없다")
        return _초록

    code = main(
        [_변이_파일을_쓴다(tmp_path, _변이_파일(old="x = 1", new="x = 2"))],
        root=tmp_path,
        runner=러너,
        out=lambda _: None,
    )

    assert code == 3
    assert path.read_bytes() == b"x = 1\n"
