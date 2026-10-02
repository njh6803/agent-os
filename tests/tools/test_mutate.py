"""tools/mutate.py 의 변이 도구.

러너는 가짜다. 가짜 러너가 불리는 순간의 파일 바이트를 기록해, 변이가 든 동안과 끝난 뒤를 따로
본다. 명령을 하위 프로세스로 부르는 실제 러너는 실제 실행으로 확인한다(`.claude/rules/tests.md`).
판정의 입력은 2026-10-01 에 본 실제 출력의 모양을 따른다(pytest 9, Vitest 5.0.2, tsc 5.9.3,
Playwright 의 `list` 리포터, 일지 2026-10-01-01). 색 코드를 넣거나 문구를 바꾼 사례는 그 모양을
비튼 것이다.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

import pytest
from tools.mutate import (
    ROOT,
    CommandResult,
    JudgeName,
    RestoreError,
    SpecError,
    judge,
    load_spec,
    main,
    measure,
    read_spec,
    select,
)
from tools.run_hooks import hook_environment

_초록 = CommandResult(0, "1 passed in 0.01s\n")
_빨강 = CommandResult(1, "FAILED tests/test_x.py::test_x - AssertionError\n1 failed in 0.01s\n")

type 러너 = Callable[[Sequence[str], Path], CommandResult]


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


_VITEST_러너 = """
[runner.vitest]
command = ["pnpm", "exec", "vitest", "run"]
cwd = "web"
judge = "vitest"
"""


def _vitest_변이(*, name: str = "하나", tests: str = '["a.test.ts"]', 줄: str = "") -> str:
    return f"""
[[mutation]]
name = "{name}"
runner = "vitest"
tests = {tests}
expect = "red"
{줄}
[[mutation.edit]]
file = "web/m.ts"
old = 'x = 1'
new = 'x = 2'
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

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
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

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
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

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
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


def _변이면(path: Path, 표지: bytes, 변이: CommandResult) -> 러너:
    """파일에 표지가 있으면(변이가 들었으면) `변이`, 아니면 초록을 내는 러너."""

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
        return 변이 if 표지 in path.read_bytes() else _초록

    return 러너


@pytest.mark.parametrize(
    ("expect", "변이_결과", "기대_코드"),
    [("red", _빨강, 0), ("red", _초록, 1), ("green", _초록, 0), ("green", _빨강, 1)],
)
def test_기대와_결과가_어긋나면_알리고_1을_돌려준다(
    tmp_path: Path, expect: str, 변이_결과: CommandResult, 기대_코드: int
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
    수집_오류 = CommandResult(2, "ERROR tests/test_x.py\nInterrupted: 1 error during collection\n")

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

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
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

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
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


def _부르면_안_되는_러너(argv: Sequence[str], cwd: Path) -> CommandResult:
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

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
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
    ids=["기대는_red_green_unhandled", "모르는_키", "tests_는_목록", "반복은_1_이상"],
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


def test_이름으로_고른_변이는_제_러너의_명령으로_돈다(tmp_path: Path) -> None:
    """고른 뒤에도 변이가 가리키는 러너를 찾을 수 있어야 한다."""
    _파일을_둔다(tmp_path, "web/m.ts", b"x = 1\n")
    _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    변이 = load_spec(_VITEST_러너 + _vitest_변이(name="둘") + _변이_파일(old="x = 1", new="x = 2"))
    불린_것: list[tuple[str, ...]] = []

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
        불린_것.append(tuple(argv))
        return CommandResult(0, "      Tests  1 passed (1)\n")

    measure(select(변이, ["둘"]), root=tmp_path, runner=러너, out=lambda _: None)

    assert 불린_것[0] == ("pnpm", "exec", "vitest", "run", "a.test.ts")


@pytest.mark.parametrize(
    ("결과", "판정"),
    [
        (CommandResult(0, "3 passed in 0.10s\n"), "green"),
        (CommandResult(1, "1 failed, 2 passed in 0.10s\n"), "red"),
        (CommandResult(2, "Interrupted: 1 error during collection\n"), "error"),
        (CommandResult(4, "ERROR: file or directory not found: tests/x.py\n"), "error"),
        (CommandResult(5, "no tests ran in 0.01s\n"), "error"),
        (CommandResult(0, "2 passed, 1 skipped in 0.10s\n"), "error"),
    ],
    ids=["통과", "실패", "수집_오류", "없는_경로", "선택된_테스트_없음", "skip_이_섞였다"],
)
def test_pytest_의_종료_코드와_요약으로_판정한다(결과: CommandResult, 판정: str) -> None:
    """skip 이 섞인 초록은 초록이 아니다(원칙 II). 재지 않은 테스트가 있다."""
    assert judge("pytest", 결과).outcome == 판정


def test_빨간_테스트의_노드_아이디를_짧은_요약에서_읽는다() -> None:
    결과 = CommandResult(
        1,
        "..F\n"
        "FAILED tests/a.py::test_x[1] - assert 0\n"
        "ERROR tests/b.py::test_y - fixture 'z' not found\n"
        "1 failed, 1 error in 0.10s\n",
    )

    assert judge("pytest", 결과).failed == ("tests/a.py::test_x[1]", "tests/b.py::test_y")


_VITEST_실패 = """
 ❯ |node| packages/api-client/src/p.test.ts (3 tests | 1 failed) 8ms
   × 실패 한다 5ms

 Test Files  1 failed (1)
      Tests  1 failed | 2 passed (3)
   Duration  680ms

⎯⎯⎯⎯⎯⎯⎯ Failed Tests 1 ⎯⎯⎯⎯⎯⎯⎯

 FAIL  |node| packages/api-client/src/p.test.ts > 실패 한다
AssertionError: expected 'yes' to be 'no' // Object.is equality
"""

_VITEST_수집_오류 = """
 ❯ |node| packages/api-client/src/broken.test.ts (0 test)

 Test Files  1 failed | 1 passed (2)
      Tests  3 passed (3)

 FAIL  |node| packages/api-client/src/broken.test.ts [ packages/api-client/src/broken.test.ts ]
Error: Transform failed with 1 error:
\x1b[31m[PARSE_ERROR] \x1b[0mExpected `,` or `)` but found `;`
"""


@pytest.mark.parametrize(
    ("결과", "판정"),
    [
        (CommandResult(0, " Test Files  1 passed (1)\n      Tests  3 passed (3)\n"), "green"),
        (
            CommandResult(0, " Test Files  1 passed (1)\n      Tests  1 passed | 2 skipped (3)\n"),
            "green",
        ),
        (CommandResult(1, _VITEST_실패), "red"),
        (
            CommandResult(
                1,
                _VITEST_실패.replace("[", "\x1b[33m[\x1b[39m").replace(
                    "Tests", "\x1b[2mTests\x1b[22m"
                ),
            ),
            "red",
        ),
        (
            CommandResult(1, "      Tests  3 passed (3)\n     Errors  1 error\n"),
            "unhandled",
        ),
        (
            CommandResult(1, "      Tests  1 failed | 2 passed (3)\n     Errors  1 error\n"),
            "red",
        ),
        (CommandResult(1, _VITEST_수집_오류), "error"),
        (
            CommandResult(
                1, _VITEST_수집_오류.replace("Tests  3 passed", "Tests  1 failed | 2 passed")
            ),
            "error",
        ),
        (CommandResult(1, "No test files found, exiting with code 1\n"), "error"),
        (CommandResult(0, "      Tests  3 skipped (3)\n"), "error"),
    ],
    ids=[
        "통과",
        "이름으로_좁혀_나머지가_skip",
        "실패",
        "색이_섞인_실패",
        "처리하지_않은_에러만",
        "실패와_처리하지_않은_에러",
        "수집_오류",
        "수집_오류와_실패",
        "테스트_파일_없음",
        "통과한_테스트_없음",
    ],
)
def test_vitest_는_실패한_테스트가_셀_때만_빨강이다(결과: CommandResult, 판정: str) -> None:
    """종료 코드는 실패와 수집 오류와 처리하지 않은 에러가 모두 1 이다. 수집 오류(파일 단위의
    FAIL)가 하나라도 있으면 다른 파일의 실패가 있어도 오류다 — 깨진 파일이 재지 않은 테스트를
    남겼다. `-t` 로 좁히면 나머지가 skipped 로 세어지므로 skip 은 오류가 아니다(못 보는 것)."""
    assert judge("vitest", 결과).outcome == 판정


def test_vitest_의_빨간_테스트는_FAIL_줄에서_읽는다() -> None:
    assert judge("vitest", CommandResult(1, _VITEST_실패)).failed == (
        "|node| packages/api-client/src/p.test.ts > 실패 한다",
    )


_TSC_진단 = (
    "packages/api-client/src/clients.test-d.ts(12,3): error TS2578: Unused '@ts-expect-error'.\n"
    "packages/api-client/src/stream.ts(40,1): error TS1360: Type does not satisfy.\n"
)


@pytest.mark.parametrize(
    ("결과", "자리", "판정"),
    [
        (CommandResult(0, ""), "clients.test-d.ts", "green"),
        (CommandResult(2, _TSC_진단), "clients.test-d.ts", "red"),
        (CommandResult(2, _TSC_진단), "packages/api-client/src/stream.ts", "red"),
        (CommandResult(2, _TSC_진단), "clients.ts", "error"),
        (CommandResult(2, _TSC_진단), "test-d.ts", "error"),
        (
            CommandResult(1, "src/clients.ts(3,1): error TS2322: Type 'string'.\nundefined\n"),
            "clients.ts",
            "red",
        ),
        (
            CommandResult(1, "[ELIFECYCLE] Command failed with exit code 1.\n"),
            "clients.ts",
            "error",
        ),
        (CommandResult(2, "other/index.ts(1,1): error TS2322: x.\n"), "index.ts", "red"),
        (CommandResult(2, "other/index.ts(1,1): error TS2322: x.\n"), "src/index.ts", "error"),
    ],
    ids=[
        "진단_없음",
        "적은_파일의_진단",
        "경로로_적은_파일",
        "다른_파일만",
        "파일_이름의_끝만_같다",
        "pnpm_r_의_패키지_기준_경로",
        "진단_없이_실패",
        "못_보는_것_다른_디렉터리의_같은_이름",
        "디렉터리까지_적으면_가른다",
    ],
)
def test_tsc_는_적은_파일에서_진단이_날_때만_빨강이다(
    결과: CommandResult, 자리: str, 판정: str
) -> None:
    """tsc 의 종료 코드는 문법 오류와 타입 에러가 같고(2), 오류 번호로도 가를 수 없다(`satisfies` 의
    어긋남이 TS1360 이다). 그래서 빨강은 변이가 적은 파일의 진단이다(대기열 59의 첫 판정)."""
    assert judge("tsc", 결과, 자리).outcome == 판정


def test_tsc_의_진단은_빨간_목록에_든다() -> None:
    assert judge("tsc", CommandResult(2, _TSC_진단), "stream.ts").failed == (
        "packages/api-client/src/clients.test-d.ts(12,3): error TS2578",
        "packages/api-client/src/stream.ts(40,1): error TS1360",
    )


_PLAYWRIGHT_실패 = """
  1) [chromium] › e2e/decision.spec.ts:10:5 › 결정 › 꺼짐이 버튼을 막는다

    Error: expect(locator).toBeDisabled() failed

  1 failed
    [chromium] › e2e/decision.spec.ts:10:5 › 결정 › 꺼짐이 버튼을 막는다
  6 passed (41.2s)
"""


@pytest.mark.parametrize(
    ("결과", "판정"),
    [
        (CommandResult(0, "Running 7 tests using 1 worker\n\n  7 passed (40.1s)\n"), "green"),
        (CommandResult(1, _PLAYWRIGHT_실패), "red"),
        (CommandResult(1, "Error: No tests found\n"), "error"),
        (CommandResult(1, "Error: Timed out waiting 120000ms from config.webServer.\n"), "error"),
        (CommandResult(0, "  1 skipped\n  6 passed (40.1s)\n"), "error"),
        (CommandResult(0, "  7 ok (40.1s)\n"), "error"),
    ],
    ids=["통과", "실패", "테스트_없음", "서버가_뜨지_않음", "skip_이_섞였다", "요약을_읽지_못함"],
)
def test_playwright_는_실패한_테스트가_셀_때만_빨강이다(결과: CommandResult, 판정: str) -> None:
    """`--grep` 은 고르지 않은 테스트를 skip 으로 세지 않으므로 skip 은 pytest 처럼 오류다."""
    assert judge("playwright", 결과).outcome == 판정


def test_playwright_의_빨간_테스트는_실패_요약_아래에서_읽는다() -> None:
    assert judge("playwright", CommandResult(1, _PLAYWRIGHT_실패)).failed == (
        "[chromium] › e2e/decision.spec.ts:10:5 › 결정 › 꺼짐이 버튼을 막는다",
    )


@pytest.mark.parametrize(
    ("판정자", "결과", "판정"),
    [
        ("vitest", CommandResult(1, "      Tests  1 failure | 2 passes (3)\n"), "error"),
        ("playwright", CommandResult(1, "  1 failure\n  6 passes (41.2s)\n"), "error"),
        ("tsc", CommandResult(2, "src/clients.test-d.ts:12:3 - error TS2578: Unused.\n"), "error"),
        (
            "vitest",
            CommandResult(
                1, "      Tests  1 failed | 2 passed (3)\n FAIL  broken.test.ts (수집 실패)\n"
            ),
            "red",
        ),
        ("playwright", CommandResult(0, "  1 skip\n  6 passed (40.1s)\n"), "green"),
        ("pytest", CommandResult(0, "2 passed, 1 skip in 0.10s\n"), "green"),
    ],
    ids=[
        "vitest_실패_문구",
        "playwright_실패_문구",
        "tsc_pretty_형식",
        "못_보는_것_vitest_파일_단위_표지",
        "못_보는_것_playwright_skip_문구",
        "못_보는_것_pytest_skip_문구",
    ],
)
def test_요약_문구가_바뀌면_읽는_문구는_오류로_기울고_거르는_표지는_못_보고_지나간다(
    판정자: JudgeName, 결과: CommandResult, 판정: str
) -> None:
    """도구의 판이 문구를 바꾼 모양을 흉내 낸다. 독스트링의 못 보는 것이 이 여섯이다(셀프 리뷰가
    "빨강으로 기울지는 않는다"의 반례 둘을 찾았다)."""
    assert judge(판정자, 결과, "clients.test-d.ts").outcome == 판정


def test_러너를_적은_변이는_그_명령에_tests_를_붙여_그_자리에서_돈다(tmp_path: Path) -> None:
    """기준선은 러너와 인자의 짝마다 한 번이다. 변이마다 테스트 이름으로 좁히면(`-t`) 좁힌 선택이
    초록인지를 그 짝의 기준선이 본다."""
    _파일을_둔다(tmp_path, "web/m.ts", b"x = 1\n")
    불린_것: list[tuple[tuple[str, ...], Path]] = []

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
        불린_것.append((tuple(argv), cwd))
        return CommandResult(0, "      Tests  1 passed (1)\n")

    변이 = (
        _VITEST_러너
        + _vitest_변이(name="하나", tests='["a.test.ts", "-t", "이름 하나"]')
        + _vitest_변이(name="둘", tests='["a.test.ts", "-t", "이름 하나"]')
        + _vitest_변이(name="셋", tests='["b.test.ts"]')
    )

    measure(load_spec(변이), root=tmp_path, runner=러너, out=lambda _: None)

    기본 = ("pnpm", "exec", "vitest", "run")
    assert 불린_것[:2] == [
        ((*기본, "a.test.ts", "-t", "이름 하나"), tmp_path / "web"),
        ((*기본, "b.test.ts"), tmp_path / "web"),
    ]
    assert len(불린_것) == 5


def test_러너를_적지_않은_변이는_내장_pytest_로_저장소_루트에서_돈다(tmp_path: Path) -> None:
    _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    불린_것: list[tuple[tuple[str, ...], Path]] = []

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
        불린_것.append((tuple(argv), cwd))
        return _초록

    measure(
        load_spec(_변이_파일(old="x = 1", new="x = 2", expect="green")),
        root=tmp_path,
        runner=러너,
        out=lambda _: None,
    )

    argv, cwd = 불린_것[0]
    assert argv[1:] == ("-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_x.py")
    assert cwd == tmp_path


def test_처리하지_않은_에러를_기대한_변이는_그것만으로_기대대로다(tmp_path: Path) -> None:
    """가드가 막는 것이 처리하지 않은 에러뿐이면 그 변이는 빨강도 오류도 아니다. 오류와 갈라 셀 수
    있어야 한다(대기열 59의 5회차, 셀 수 없던 가드 변이)."""
    path = _파일을_둔다(tmp_path, "web/m.ts", b"x = 1\n")
    줄: list[str] = []
    처리하지_않은 = CommandResult(1, "      Tests  3 passed (3)\n     Errors  1 error\n")
    변이 = _VITEST_러너 + _vitest_변이().replace('expect = "red"', 'expect = "unhandled"')

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
        if b"x = 2" in path.read_bytes():
            return 처리하지_않은
        return CommandResult(0, "      Tests  3 passed (3)\n")

    code = measure(load_spec(변이), root=tmp_path, runner=러너, out=줄.append)

    assert code == 0
    assert any("처리하지 않은 에러" in 한줄 for 한줄 in 줄)
    assert any(한줄.startswith("   |") and "Errors  1 error" in 한줄 for 한줄 in 줄)


@pytest.mark.parametrize(
    ("변이", "문구"),
    [
        (_vitest_변이(), "vitest"),
        (
            _VITEST_러너.replace("[runner.vitest]", "[runner.pytest]")
            + _변이_파일(old="x", new="y"),
            "내장",
        ),
        (
            _VITEST_러너.replace('judge = "vitest"', 'judge = "tsc"') + _vitest_변이(),
            "diagnostic_in",
        ),
        (_VITEST_러너 + _vitest_변이(줄='diagnostic_in = "a.ts"'), "diagnostic_in"),
        (_변이_파일(old="x", new="y", expect="unhandled"), "unhandled"),
        (_VITEST_러너.replace('judge = "vitest"', 'judge = "jest"') + _vitest_변이(), "judge"),
        (
            _VITEST_러너.replace('["pnpm", "exec", "vitest", "run"]', "[]") + _vitest_변이(),
            "command",
        ),
    ],
    ids=[
        "없는_러너",
        "pytest_는_내장이다",
        "tsc_는_진단_자리가_있어야",
        "진단_자리는_tsc_만",
        "처리하지_않은_에러는_vitest_만",
        "모르는_판정",
        "빈_명령",
    ],
)
def test_러너와_판정이_맞지_않으면_변이_파일_오류다(변이: str, 문구: str) -> None:
    with pytest.raises(SpecError, match=문구):
        load_spec(변이)


def test_러너의_자리가_저장소_밖이거나_없으면_변이_파일_오류다(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    _파일을_둔다(root, "web/m.ts", b"x = 1\n")

    for 자리 in ("../elsewhere", "없는_자리"):
        (tmp_path / "elsewhere").mkdir(exist_ok=True)
        변이 = _VITEST_러너.replace('cwd = "web"', f'cwd = "{자리}"') + _vitest_변이()
        with pytest.raises(SpecError, match=자리.lstrip("./")):
            measure(load_spec(변이), root=root, runner=_부르면_안_되는_러너, out=lambda _: None)


def test_되돌릴_파일은_편집하지_않아도_돌린_뒤에_원래_바이트로_돌아온다(tmp_path: Path) -> None:
    """변이가 명령에게 파일을 고쳐 쓰게 하면(최신성 검사가 생성물을 덮어쓰는 변이) 그 파일도
    쥔다."""
    path = _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    생성물 = _파일을_둔다(tmp_path, "gen/out.ts", b"generated\r\n")
    쓰기_전: list[bytes] = []

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
        if b"x = 2" not in path.read_bytes():
            return _초록
        쓰기_전.append(생성물.read_bytes())
        생성물.write_bytes(b"overwritten")
        return _빨강

    변이 = _변이_파일(old="x = 1", new="x = 2").replace(
        'expect = "red"', 'expect = "red"\nrestore = ["gen/out.ts"]'
    )

    code = measure(load_spec(변이), root=tmp_path, runner=러너, out=lambda _: None)

    assert code == 0
    assert 쓰기_전 == [b"generated\r\n"]
    assert 생성물.read_bytes() == b"generated\r\n"
    assert path.read_bytes() == b"x = 1\n"


@pytest.mark.parametrize("자리", ["gen/없다.ts", "../outside.ts"], ids=["없다", "저장소_밖"])
def test_되돌릴_파일이_없거나_저장소_밖이면_변이_파일_오류다(tmp_path: Path, 자리: str) -> None:
    root = tmp_path / "repo"
    _파일을_둔다(root, "src/m.py", b"x = 1\n")
    _파일을_둔다(tmp_path, "outside.ts", b"x\n")
    변이 = _변이_파일(old="x = 1", new="x = 2").replace(
        'expect = "red"', f'expect = "red"\nrestore = ["{자리}"]'
    )

    with pytest.raises(SpecError, match="되돌릴"):
        measure(load_spec(변이), root=root, runner=_부르면_안_되는_러너, out=lambda _: None)


def _쓰기를_막는다(
    monkeypatch: pytest.MonkeyPatch,
    막을_파일: Path,
    막을_때: Callable[[bytes], bool],
    *,
    남는_앞부분: int = 0,
) -> None:
    """그 파일에 `막을_때` 가 참인 바이트를 쓰면 앞의 `남는_앞부분` 바이트만 쓰고(0 이면 아무것도
    쓰지 않고) `PermissionError` 를 낸다.

    권한(`chmod` 읽기 전용)으로 막으면 root(uid 0)는 쓰기가 통해, 클라우드 컨테이너에서 되돌림 실패
    테스트 셋이 빨갰다(대기열 80, `.scratch/harness/probes/mutate_as_root.sh`).
    """
    원래_쓰기 = Path.write_bytes

    def 막힌_쓰기(self: Path, data: bytes) -> int:
        if self.resolve() == 막을_파일.resolve() and 막을_때(data):
            if 남는_앞부분:
                원래_쓰기(self, data[:남는_앞부분])
            raise PermissionError(13, "쓰기를 막았다", str(self))
        return 원래_쓰기(self, data)

    monkeypatch.setattr(Path, "write_bytes", 막힌_쓰기)


def _잠그는_러너(잠글_파일: Path, 표지: bytes, monkeypatch: pytest.MonkeyPatch) -> 러너:
    """변이가 든 동안 그 파일의 쓰기를 막아, 되돌리는 쓰기가 `PermissionError` 가 되게 한다."""

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
        if 표지 not in 잠글_파일.read_bytes():
            return _초록
        _쓰기를_막는다(monkeypatch, 잠글_파일, lambda _: True)
        return _빨강

    return 러너


def _두_파일_변이(tmp_path: Path) -> tuple[Path, Path, str]:
    m = _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    a = _파일을_둔다(tmp_path, "src/a.py", b"a = 1\n")
    변이 = _변이_파일(old="x = 1", new="x = 2") + "\n".join(
        ["[[mutation.edit]]", 'file = "src/a.py"', "old = 'a = 1'", "new = 'a = 2'", ""]
    )
    return m, a, 변이


def test_되돌리지_못한_파일이_있으면_RestoreError_이고_나머지는_되돌린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """되돌림 실패를 명세 오류로 알리면 변이된 채 남은 파일을 아무도 모른다(셀프 리뷰 Major)."""
    m, a, 변이 = _두_파일_변이(tmp_path)

    with pytest.raises(RestoreError, match="src/m.py.*쓰기를 막았다"):
        measure(
            load_spec(변이),
            root=tmp_path,
            runner=_잠그는_러너(m, b"x = 2", monkeypatch),
            out=lambda _: None,
        )

    assert a.read_bytes() == b"a = 1\n"
    assert m.read_bytes() == b"x = 2\n"


def test_변이가_든_동안_다른_쓰기가_들어온_파일은_덮지_않고_알린다(tmp_path: Path) -> None:
    """되돌림이 변이 전 바이트를 그대로 쓰면 도는 동안 고친 것이 조용히 사라진다. 변이가 도는 동안
    더한 훅 독스트링 한 문장이 그렇게 사라졌다(대기열 77). 나머지 파일은 되돌린다."""
    m, a, 변이 = _두_파일_변이(tmp_path)

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
        if b"x = 2" not in m.read_bytes():
            return _초록
        m.write_bytes(m.read_bytes() + b"# doc\n")  # 도는 동안 편집기가 저장했다
        return _빨강

    with pytest.raises(RestoreError, match="src/m.py.*다른 쓰기"):
        measure(load_spec(변이), root=tmp_path, runner=러너, out=lambda _: None)

    assert m.read_bytes() == b"x = 2\n# doc\n"
    assert a.read_bytes() == b"a = 1\n"


def test_되돌릴_파일로_적은_편집_파일은_명령이_고쳐_써도_되돌린다(tmp_path: Path) -> None:
    """`restore` 는 명령이 고쳐 쓰는 파일이다. 그 쓰기는 다른 쓰기와 가를 수 없어 보지 않는다."""
    path = _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
        if b"x = 2" not in path.read_bytes():
            return _초록
        path.write_bytes(b"x = 2\n# generated\n")
        return _빨강

    변이 = _변이_파일(old="x = 1", new="x = 2").replace(
        'expect = "red"', 'expect = "red"\nrestore = ["src/m.py"]'
    )

    code = measure(load_spec(변이), root=tmp_path, runner=러너, out=lambda _: None)

    assert code == 0
    assert path.read_bytes() == b"x = 1\n"


def test_변이를_쓰지_못한_파일은_다른_쓰기로_보지_않고_되돌린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """변이 바이트를 쓰다 실패한 파일은 쓰다 만 앞부분이 남아도 도구가 마지막으로 쓴 것이다. 그것을
    다른 쓰기로 알리면 쓰지 못한 원인이 가려지고 그 파일이 쓰다 만 채로 남는다."""
    m, a, 변이 = _두_파일_변이(tmp_path)
    _쓰기를_막는다(monkeypatch, a, lambda data: data == b"a = 2\n", 남는_앞부분=3)

    with pytest.raises(PermissionError):
        measure(
            load_spec(변이),
            root=tmp_path,
            runner=_변이면(m, b"x = 2", _빨강),
            out=lambda _: None,
        )

    assert m.read_bytes() == b"x = 1\n"
    assert a.read_bytes() == b"a = 1\n"


def test_못_보는_것_앞_파일의_변이_쓰기가_실패하면_아직_쓰지_않은_파일에_든_쓰기는_덮는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """변이를 쓰지 못한 파일은 쓴 변이 바이트가 없어 보지 않고 되돌린다. 처음 읽은 뒤 되돌리기까지의
    틈에 든 쓰기는 사라진다. 앞 파일의 쓰기가 실패하면 곧바로 되돌리므로 그 틈은 짧다(독스트링의 못
    보는 것, PR #115 claude-review)."""
    m, a, 변이 = _두_파일_변이(tmp_path)
    끼운_뒤: list[bytes] = []

    def 다른_쓰기를_끼우고_막는다(data: bytes) -> bool:
        if data != b"x = 2\n":
            return False
        with a.open("ab") as f:  # m 의 변이를 쓰는 사이 a 에 다른 쓰기가 든다
            f.write(b"# doc\n")
        끼운_뒤.append(a.read_bytes())
        return True

    _쓰기를_막는다(monkeypatch, m, 다른_쓰기를_끼우고_막는다)

    with pytest.raises(PermissionError):
        measure(
            load_spec(변이),
            root=tmp_path,
            runner=_변이면(m, b"x = 2", _빨강),
            out=lambda _: None,
        )

    assert 끼운_뒤 == [b"a = 1\n# doc\n"]
    assert a.read_bytes() == b"a = 1\n"


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

    for argv in ([], ["--check"], [str(tmp_path / "없다.toml")], [str(깨진_파일)], [원문_없음]):
        code = main(argv, root=tmp_path, runner=_부르면_안_되는_러너, out=lambda _: None)
        assert code == 2, argv


def test_main_은_모르는_선택을_변이_이름으로_읽지_않고_알린다(tmp_path: Path) -> None:
    """`--chek` 이 변이 이름이 되면 "없는 이름" 으로 끝나 무엇을 잘못 쳤는지 가려진다."""
    _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    경로 = _변이_파일을_쓴다(tmp_path, _변이_파일(old="x = 1", new="x = 2"))
    줄: list[str] = []

    code = main([경로, "--chek"], root=tmp_path, runner=_부르면_안_되는_러너, out=줄.append)

    assert code == 2
    assert any("모르는 선택: --chek" in 한줄 for 한줄 in 줄)


def test_main_은_기대대로면_0_어긋나면_1이다(tmp_path: Path) -> None:
    path = _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    변이 = _변이_파일을_쓴다(tmp_path, _변이_파일(old="x = 1", new="x = 2"))

    assert main([변이], root=tmp_path, runner=_변이면(path, b"x = 2", _빨강), out=print) == 0
    assert main([변이], root=tmp_path, runner=_변이면(path, b"x = 2", _초록), out=print) == 1


def test_원문만_보면_명령을_돌리지_않고_틀린_원문을_모두_알린다(tmp_path: Path) -> None:
    """리팩터 한 번에 다른 러너의 원문 19가 조용히 옮겨 갔고, 돌리기 전에는 아무도 몰랐다(대기열
    59의 4회차). 첫 틀림에서 멈추면 열아홉을 한 번에 고칠 수 없다."""
    _파일을_둔다(tmp_path, "src/m.py", b"x = 1\ny = 1\ny = 1\n")
    변이 = (
        _변이_파일(old="x = 1", new="x = 2")
        + _변이_파일(old="z = 1", new="z = 2").replace("하나", "둘")
        + _변이_파일(old="y = 1", new="y = 2").replace("하나", "셋")
    )
    경로 = _변이_파일을_쓴다(tmp_path, 변이)
    줄: list[str] = []

    code = main(["--check", 경로], root=tmp_path, runner=_부르면_안_되는_러너, out=줄.append)

    assert code == 2
    assert any("둘:" in 한줄 and "0번" in 한줄 for 한줄 in 줄)
    assert any("셋:" in 한줄 and "2번" in 한줄 for 한줄 in 줄)
    assert not any("하나:" in 한줄 for 한줄 in 줄)
    # pre-commit 이 표 하나만 넘겨도 어느 표가 틀렸는지 보인다
    assert all(한줄.startswith(f"{경로}: ") for 한줄 in 줄)


def test_원문만_보아_모두_맞으면_0이고_파일을_건드리지_않는다(tmp_path: Path) -> None:
    path = _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    경로 = _변이_파일을_쓴다(tmp_path, _변이_파일(old="x = 1", new="x = 2"))
    줄: list[str] = []

    code = main(
        [경로, "--check", "하나"], root=tmp_path, runner=_부르면_안_되는_러너, out=줄.append
    )

    assert code == 0
    assert path.read_bytes() == b"x = 1\n"
    assert any("1" in 한줄 and "한 번" in 한줄 for 한줄 in 줄)


_이_도구 = "tools/mutate.py"


def _표를_쓴다(tmp_path: Path, 이름: str, 내용: str) -> str:
    path = tmp_path / 이름
    path.write_text(내용, encoding="utf-8")
    return str(path)


def test_원문만_볼_때는_변이_파일_여럿을_받아_틀린_파일을_가리킨다(tmp_path: Path) -> None:
    """pre-commit 이 커밋에 든 변이 표를 한 번에 넘긴다(대기열 92). 앞 파일에서 멈추면 뒤 파일을
    못 본다."""
    _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    맞는 = _표를_쓴다(tmp_path, "a_mutations.toml", _변이_파일(old="x = 1", new="x = 2"))
    틀린 = _표를_쓴다(tmp_path, "b_mutations.toml", _변이_파일(old="z = 1", new="z = 2"))
    줄: list[str] = []

    code = main(["--check", 틀린, 맞는], root=tmp_path, runner=_부르면_안_되는_러너, out=줄.append)

    assert code == 2
    assert any(틀린 in 한줄 and "0번" in 한줄 for 한줄 in 줄)
    assert any(맞는 in 한줄 and "한 번" in 한줄 for 한줄 in 줄)
    assert not any(맞는 in 한줄 and "!!" in 한줄 for 한줄 in 줄)


def test_원문만_볼_때_읽지_못한_변이_파일이_있어도_나머지_파일을_본다(tmp_path: Path) -> None:
    깨진 = tmp_path / "broken_mutations.toml"
    깨진.write_bytes(b'name = "\xff"\n')
    _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")
    틀린 = _표를_쓴다(tmp_path, "b_mutations.toml", _변이_파일(old="z = 1", new="z = 2"))
    줄: list[str] = []

    code = main(
        ["--check", str(깨진), 틀린], root=tmp_path, runner=_부르면_안_되는_러너, out=줄.append
    )

    assert code == 2
    assert any(str(깨진) in 한줄 for 한줄 in 줄)
    assert any(틀린 in 한줄 and "0번" in 한줄 for 한줄 in 줄)


def test_원문만_볼_때_변이_파일_여럿이_모두_맞으면_0이다(tmp_path: Path) -> None:
    _파일을_둔다(tmp_path, "src/m.py", b"x = 1\ny = 1\n")
    가 = _표를_쓴다(tmp_path, "a_mutations.toml", _변이_파일(old="x = 1", new="x = 2"))
    나 = _표를_쓴다(tmp_path, "b_mutations.toml", _변이_파일(old="y = 1", new="y = 2"))

    code = main(["--check", 가, 나], root=tmp_path, runner=_부르면_안_되는_러너, out=print)

    assert code == 0


def test_변이_파일_여럿은_원문_확인에서만_받고_이름과_섞지_않는다(tmp_path: Path) -> None:
    """변이를 돌리는 것은 표 하나씩이다. 이름은 어느 표의 것인지 가를 수 없다."""
    _파일을_둔다(tmp_path, "src/m.py", b"x = 1\ny = 1\n")
    가 = _표를_쓴다(tmp_path, "a_mutations.toml", _변이_파일(old="x = 1", new="x = 2"))
    나 = _표를_쓴다(tmp_path, "b_mutations.toml", _변이_파일(old="y = 1", new="y = 2"))

    for argv in ([가, 나], ["--check", 가, 나, "하나"]):
        줄: list[str] = []
        code = main(argv, root=tmp_path, runner=_부르면_안_되는_러너, out=줄.append)
        assert code == 2, argv
        assert any("변이 파일 여럿" in 한줄 for 한줄 in 줄), argv


def test_pre_commit_처럼_띄우면_틀린_표의_경로를_UTF_8_로_알린다(tmp_path: Path) -> None:
    """pre-commit 은 표 경로를 인자 끝에 붙여 띄운다. 훅 환경에 `PYTHONUTF8` 이 있다고 가정하지
    않는다 — 없으면 윈도우의 파이프는 cp949 라 한국어 출력이 깨지거나 인코딩 오류로 끝난다."""
    맞는 = _표를_쓴다(
        tmp_path,
        "a_mutations.toml",
        _변이_파일(
            old="ROOT = Path(__file__).resolve().parent.parent", new="ROOT = Path()", file=_이_도구
        ),
    )
    틀린 = _표를_쓴다(
        tmp_path,
        "b_mutations.toml",
        _변이_파일(old="없는 원문 — 대기열 92", new="x", file=_이_도구).replace(
            "하나", "틀린 — 표"
        ),
    )

    done = subprocess.run(
        [sys.executable, "tools/mutate.py", "--check", 맞는, 틀린],
        cwd=ROOT,
        capture_output=True,
        env=hook_environment(),
        check=False,
        timeout=60,
    )
    stdout = done.stdout.decode("utf-8")

    assert done.returncode == 2, done.stderr.decode("utf-8", "replace")
    assert "틀린 — 표" in stdout
    assert 틀린 in stdout


def test_main_은_되돌리지_못하면_3이고_git_diff_를_가리킨다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    m, _, 변이 = _두_파일_변이(tmp_path)
    줄: list[str] = []

    code = main(
        [_변이_파일을_쓴다(tmp_path, 변이)],
        root=tmp_path,
        runner=_잠그는_러너(m, b"x = 2", monkeypatch),
        out=줄.append,
    )

    assert code == 3
    assert any("git diff" in 한줄 and "src/m.py" in 한줄 for 한줄 in 줄)


def test_main_은_되돌리지_못했을_때_그_전에_난_예외도_알린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """되돌림 실패가 원인 예외(명령을 돌리지 못했다)를 가리면 왜 멈췄는지 아무도 모른다(PR #110
    claude-review)."""
    m, _, 변이 = _두_파일_변이(tmp_path)
    잠그는 = _잠그는_러너(m, b"x = 2", monkeypatch)

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
        잠그는(argv, cwd)
        if b"x = 2" in m.read_bytes():
            raise FileNotFoundError("pnpm 이 없다")
        return _초록

    줄: list[str] = []
    code = main([_변이_파일을_쓴다(tmp_path, 변이)], root=tmp_path, runner=러너, out=줄.append)

    assert code == 3
    assert any("git diff" in 한줄 for 한줄 in 줄)
    assert any("pnpm 이 없다" in 한줄 for 한줄 in 줄)


def test_main_은_테스트를_돌리지_못하면_3이고_변이는_되돌렸다(tmp_path: Path) -> None:
    path = _파일을_둔다(tmp_path, "src/m.py", b"x = 1\n")

    def 러너(argv: Sequence[str], cwd: Path) -> CommandResult:
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


# 커밋된 변이 파일. 도구의 형식이 바뀌면 옛 파일이 조용히 깨진다 — 2026-10-01 에 형식을
# 넓히며 일곱을 손으로 `--check` 했다(대기열 73). 원문은 보지 않는다. 옛 프로브의 원문은
# 코드가 바뀌면 썩어도 되고, 다시 돌 때 `--check` 가 알린다.


def test_이_저장소의_변이_파일은_지금의_도구로_모두_읽힌다() -> None:
    경로들 = sorted(ROOT.glob(".scratch/**/*_mutations.toml"))
    문제: list[str] = []
    for 경로 in 경로들:
        try:
            read_spec(경로)
        except SpecError as error:
            문제.append(f"{경로.relative_to(ROOT).as_posix()}: {error}")

    assert 경로들, "변이 파일을 하나도 찾지 못했다. glob 이 아무것도 재지 않는다"
    assert 문제 == []
