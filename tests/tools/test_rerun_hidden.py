"""`tools/rerun_hidden.py`: 숨은 시험 가르기.

티켓은 `.scratch/model-rerun/issues/02-hidden-test-filter.md`다.

값만 받는 함수는 지은 입력으로, 바깥 층은 B와 M 커밋이 있는 임시 저장소와 작은 pytest 시험으로
본다(명세 Testing Decisions "과제 고르기와 숨은 시험 가르기").
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest
from tools.rerun_hidden import (
    ERROR,
    FAILED,
    NAME,
    PASSED,
    PYTEST_COMMAND,
    SETUP_COMMANDS,
    SKIPPED,
    STRING,
    CandidateError,
    ChangedTest,
    Dropped,
    Failure,
    Hidden,
    Limits,
    NodeFacts,
    Outcome,
    Term,
    changed_tests,
    node_facts,
    overlay_target,
    read_junit,
    sort_candidate,
    sort_nodes,
    term_in,
)
from tools.run_hooks import REPO_LOCATION_VARS

_IDENTITY = ("-c", "user.name=t", "-c", "user.email=t@example.com")
_TIMEOUT = 60


def _src(text: str) -> str:
    return textwrap.dedent(text).lstrip("\n")


# --- 바뀐 시험 ---


def _이름들(tests: tuple[ChangedTest, ...]) -> list[str]:
    return [t.selector for t in tests]


def test_새로_생긴_시험과_본문이_바뀐_시험을_찾고_그대로인_시험은_뺀다() -> None:
    b = _src("""
        def test_same():
            assert 1

        def test_body():
            assert 1 == 1
        """)
    m = _src("""
        import pytest

        def test_same():
            assert 1

        def test_body():
            assert 1 == 2

        def test_new():
            assert True

        def helper_not_a_test():
            return 1
        """)
    got = changed_tests({"tests/test_a.py": b}, {"tests/test_a.py": m})
    assert _이름들(got) == ["tests/test_a.py::test_body", "tests/test_a.py::test_new"]


def test_데코레이터만_바뀐_시험도_바뀐_시험이다() -> None:
    b = _src("""
        import pytest

        @pytest.mark.parametrize("x", [1])
        def test_p(x):
            assert x
        """)
    m = _src("""
        import pytest

        @pytest.mark.parametrize("x", [1, 2])
        def test_p(x):
            assert x
        """)
    got = changed_tests({"tests/test_a.py": b}, {"tests/test_a.py": m})
    assert _이름들(got) == ["tests/test_a.py::test_p"]


def test_줄만_옮긴_시험은_바뀌지_않았다() -> None:
    b = "def test_a():\n    assert 1\n"
    m = "\n\n# 주석\n\ndef test_a():\n    assert 1\n"
    assert changed_tests({"tests/test_a.py": b}, {"tests/test_a.py": m}) == ()


def test_Test_클래스의_test_메서드만_본다() -> None:
    b = _src("""
        class TestC:
            def test_m(self):
                assert 1
        """)
    m = _src("""
        class TestC:
            def test_m(self):
                assert 2

            def helper(self):
                return 1

            def test_n(self):
                assert 1

        class Other:
            def test_x(self):
                assert 1
        """)
    got = changed_tests({"tests/test_a.py": b}, {"tests/test_a.py": m})
    assert _이름들(got) == ["tests/test_a.py::TestC::test_m", "tests/test_a.py::TestC::test_n"]


def test_B_에_없거나_풀리지_않는_시험_파일의_시험은_모두_새것이다() -> None:
    m = "def test_a():\n    assert 1\n"
    assert _이름들(changed_tests({}, {"tests/test_a.py": m})) == ["tests/test_a.py::test_a"]
    got = changed_tests({"tests/test_a.py": "def (:\n"}, {"tests/test_a.py": m})
    assert _이름들(got) == ["tests/test_a.py::test_a"]


def test_M_의_시험_파일이_풀리지_않으면_CandidateError_다() -> None:
    with pytest.raises(CandidateError, match="tests/test_a.py"):
        changed_tests({}, {"tests/test_a.py": "def (:\n"})


def test_BOM_으로_시작하는_시험_파일의_시험도_본다() -> None:
    m = chr(0xFEFF) + "def test_a():\n    assert 1\n"
    assert _이름들(changed_tests({}, {"tests/test_a.py": m})) == ["tests/test_a.py::test_a"]


def test_비동기_시험도_본다() -> None:
    m = "async def test_a():\n    assert 1\n"
    assert _이름들(changed_tests({}, {"tests/test_a.py": m})) == ["tests/test_a.py::test_a"]


def test_본문의_이름과_두_글자_이상의_문자열을_모은다() -> None:
    m = _src("""
        import pytest

        @pytest.mark.parametrize("decorated_string", [1])
        def test_a(decorated_string):
            value = module.new_attr(other_name)
            assert value == "ok", "x"
            assert f"pre{value}" != "--resume"
        """)
    (got,) = changed_tests({}, {"tests/test_a.py": m})
    assert got.names == ("module", "new_attr", "other_name", "value")
    assert got.strings == ("--resume", "ok", "pre")


def test_줄바꿈이_든_문자열은_두_글자_이상인_줄마다_센다() -> None:
    m = 'def test_a():\n    assert x == "ab-old\\nc\\ncd-new\\n"\n'
    (got,) = changed_tests({}, {"tests/test_a.py": m})
    assert got.strings == ("ab-old", "cd-new")


def test_NUL_이_든_문자열은_그_자리에서도_나눠_두_글자_이상인_조각마다_센다() -> None:
    m = 'def test_a():\n    assert x == "ab-old\\x00c\\ncd\\x00ef-new"\n'
    (got,) = changed_tests({}, {"tests/test_a.py": m})
    assert got.strings == ("ab-old", "cd", "ef-new")


def test_못_보는_것_인자_기본값의_이름은_모으지_않고_docstring_은_문자열로_센다() -> None:
    m = _src('''
        def test_a(x=DEFAULT_NAME):
            """새 문서"""
            assert x
        ''')
    (got,) = changed_tests({}, {"tests/test_a.py": m})
    assert got.names == ("x",)
    assert got.strings == ("새 문서",)


def test_못_보는_것_중첩_클래스와_test_밑줄_없는_함수와_문_안의_정의는_보지_않는다() -> None:
    m = _src("""
        class TestOuter:
            class TestInner:
                def test_nested(self):
                    assert 1

        def testfoo():
            assert 1

        if True:
            def test_in_if():
                assert 1
        """)
    assert changed_tests({}, {"tests/test_a.py": m}) == ()


# --- junit ---

_JUNIT = """<?xml version="1.0" encoding="utf-8"?>
<testsuites><testsuite name="pytest" errors="1" failures="2" skipped="1" tests="8">
<testcase classname="tests.test_a" name="test_pass" time="0.001" />
<testcase classname="tests.test_a" name="test_assert" time="0.001">
  <failure message="assert 1 == 2">긴 설명</failure></testcase>
<testcase classname="tests.test_a" name="test_attr" time="0.001">
  <failure message="AttributeError: module 'calc' has no attribute 'x'">긴 설명</failure>
</testcase>
<testcase classname="tests.test_a" name="test_setup" time="0.001">
  <error message="failed on setup with &quot;boom&quot;">긴 설명</error></testcase>
<testcase classname="tests.test_a" name="test_skip" time="0.001">
  <skipped type="pytest.skip" message="나중에">긴 설명</skipped></testcase>
<testcase classname="tests.test_a" name="test_p[1]" time="0.001" />
<testcase classname="tests.test_a" name="test_p[a::b]" time="0.001" />
<testcase classname="tests.test_a.TestC" name="test_m" time="0.001" />
<testcase classname="tests.test_a" name="test_pass_then_teardown" time="0.001" />
<testcase classname="tests.test_a" name="test_pass_then_teardown" time="0.001">
  <error message="failed on teardown with &quot;boom&quot;">긴 설명</error></testcase>
<testcase classname="" name="tests.test_b" time="0.001">
  <error message="collection failure">긴 설명</error></testcase>
<testcase classname="tests.test_a" name="test_not_changed" time="0.001" />
</testsuite></testsuites>
"""


def _바뀐(file: str, name: str) -> ChangedTest:
    return ChangedTest(file=file, name=name, names=(), strings=())


def test_junit_을_바뀐_시험의_노드_ID_로_푼다() -> None:
    tests = [
        _바뀐("tests/test_a.py", n)
        for n in (
            "test_pass",
            "test_assert",
            "test_attr",
            "test_setup",
            "test_skip",
            "test_p",
            "TestC::test_m",
            "test_pass_then_teardown",
        )
    ] + [_바뀐("tests/test_b.py", "test_import")]
    got = read_junit(_JUNIT, tests)
    assert got == {
        "tests/test_a.py::test_pass": Outcome(PASSED, ""),
        "tests/test_a.py::test_assert": Outcome(FAILED, "assert 1 == 2"),
        "tests/test_a.py::test_attr": Outcome(
            FAILED, "AttributeError: module 'calc' has no attribute 'x'"
        ),
        "tests/test_a.py::test_setup": Outcome(ERROR, 'failed on setup with "boom"'),
        "tests/test_a.py::test_skip": Outcome(SKIPPED, "나중에"),
        "tests/test_a.py::test_p[1]": Outcome(PASSED, ""),
        "tests/test_a.py::test_p[a::b]": Outcome(PASSED, ""),
        "tests/test_a.py::TestC::test_m": Outcome(PASSED, ""),
        "tests/test_a.py::test_pass_then_teardown": Outcome(
            ERROR, 'failed on teardown with "boom"'
        ),
    }


def test_시험_이름의_앞자리만_같은_다른_시험은_가르지_않는다() -> None:
    xml = (
        '<testsuites><testsuite name="pytest">'
        '<testcase classname="tests.test_a" name="test_p_other" />'
        '<testcase classname="tests.test_a" name="test_p[1]" />'
        "</testsuite></testsuites>"
    )
    got = read_junit(xml, [_바뀐("tests/test_a.py", "test_p")])
    assert list(got) == ["tests/test_a.py::test_p[1]"]


def test_풀리지_않는_junit_은_CandidateError_다() -> None:
    with pytest.raises(CandidateError, match="junit"):
        read_junit("<testsuites><testcase", [_바뀐("tests/test_a.py", "test_a")])


# --- 세 조건 ---

_P = Outcome(PASSED, "")
_단언_실패 = Outcome(FAILED, "assert 1 == 2")


def _노드(
    node_id: str = "tests/test_a.py::test_a",
    merge_runs: tuple[Outcome | None, Outcome | None] = (_P, _P),
    base_run: Outcome | None = _단언_실패,
    terms: tuple[Term, ...] = (),
) -> NodeFacts:
    return NodeFacts(node_id=node_id, merge_runs=merge_runs, base_run=base_run, terms=terms)


def test_세_조건을_모두_지난_노드만_남는다() -> None:
    got = sort_nodes([_노드()])
    assert got.kept == ("tests/test_a.py::test_a",)
    assert got.dropped == ()


def test_노드는_M_결과에서_짓고_M_에서_돌지_않은_바뀐_시험도_넣는다() -> None:
    term = Term(kind=NAME, text="calc", in_merge=True, in_base=True)
    terms = {
        "tests/test_a.py::test_p": (term,),
        "tests/test_a.py::test_llm": (),
    }
    first = {"tests/test_a.py::test_p[1]": _P}
    second = {"tests/test_a.py::test_p[1]": _P, "tests/test_a.py::test_p[2]": _P}
    base = {"tests/test_a.py::test_p[1]": _단언_실패}
    got = node_facts(terms, (first, second), base)
    assert got == [
        NodeFacts("tests/test_a.py::test_p[1]", (_P, _P), _단언_실패, (term,)),
        NodeFacts("tests/test_a.py::test_p[2]", (None, _P), None, (term,)),
        NodeFacts("tests/test_a.py::test_llm", (None, None), None, ()),
    ]
    assert sort_nodes(got).dropped[-1] == Dropped(
        "tests/test_a.py::test_llm", 1, "M 첫째 실행: 결과 없음"
    )


@pytest.mark.parametrize(
    ("runs", "까닭"),
    [
        ((_P, Outcome(FAILED, "assert 0")), "M 둘째 실행: 실패"),
        ((Outcome(ERROR, "boom"), _P), "M 첫째 실행: 오류"),
        ((_P, Outcome(SKIPPED, "")), "M 둘째 실행: 건너뜀"),
        ((None, _P), "M 첫째 실행: 결과 없음"),
    ],
)
def test_조건_1_은_M_에서_두_번_다_통과한_노드만_남긴다(
    runs: tuple[Outcome | None, Outcome | None], 까닭: str
) -> None:
    got = sort_nodes([_노드(merge_runs=runs)])
    assert got.kept == ()
    assert got.dropped == (Dropped("tests/test_a.py::test_a", 1, 까닭),)


@pytest.mark.parametrize(
    ("base", "까닭"),
    [
        (_P, "통과"),
        (Outcome(SKIPPED, "나중에"), "건너뜀"),
        (Outcome(ERROR, "failed on setup"), "오류"),
        (Outcome(FAILED, "AttributeError: no attribute"), "AttributeError"),
        (Outcome(FAILED, "NameError: name 'x' is not defined"), "NameError"),
        (Outcome(FAILED, "TypeError: f() takes 1 positional argument"), "TypeError"),
        (None, "결과 없음(모음 실패)"),
    ],
)
def test_조건_2_는_B_에서_단언으로_실패하지_않은_노드를_뺀다(
    base: Outcome | None, 까닭: str
) -> None:
    got = sort_nodes([_노드(base_run=base)])
    assert got.kept == ()
    assert got.dropped == (Dropped("tests/test_a.py::test_a", 2, 까닭),)


@pytest.mark.parametrize(
    "message",
    ["assert 1 == 2", "AssertionError: 다르다", "ValueError: 나쁜 값", "ImportError: 없다"],
)
def test_조건_2_는_단언과_다른_예외의_실패를_남긴다(message: str) -> None:
    got = sort_nodes([_노드(base_run=Outcome(FAILED, message))])
    assert got.kept == ("tests/test_a.py::test_a",)


@pytest.mark.parametrize(
    "있는_자리",
    [(True, False, False), (True, True, True), (False, False, True), (False, True, True)],
)
def test_조건_3_은_M_의_tests_밖에_있고_B_에_없는_이름이면_뺀다(
    있는_자리: tuple[bool, bool, bool],
) -> None:
    in_merge, in_base, 남는다 = 있는_자리
    term = Term(kind=NAME, text="new_name", in_merge=in_merge, in_base=in_base)
    got = sort_nodes([_노드(terms=(term,))])
    if 남는다:
        assert got.kept == ("tests/test_a.py::test_a",)
    else:
        assert got.dropped == (Dropped("tests/test_a.py::test_a", 3, "이름 'new_name'"),)


def test_조건_3_은_문자열도_본다() -> None:
    terms = (
        Term(kind=NAME, text="calc", in_merge=False, in_base=True),
        Term(kind=STRING, text="cd-new", in_merge=True, in_base=False),
    )
    got = sort_nodes([_노드(terms=terms)])
    assert got.dropped == (Dropped("tests/test_a.py::test_a", 3, "문자열 'cd-new'"),)


def test_앞선_조건에서_빠진_노드는_그_조건의_이유를_든다() -> None:
    term = Term(kind=NAME, text="new_name", in_merge=True, in_base=False)
    got = sort_nodes([_노드(base_run=_P, terms=(term,))])
    assert got.dropped == (Dropped("tests/test_a.py::test_a", 2, "통과"),)


# --- 바깥 층의 상수 ---


def test_실제_준비는_uv_sync_이고_pytest_는_uv_run_으로_띄운다() -> None:
    assert SETUP_COMMANDS == (("uv", "sync"),)
    assert PYTEST_COMMAND == ("uv", "run", "pytest")


# --- 바깥 층: 임시 저장소 ---


def _env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in REPO_LOCATION_VARS}


def _git(repo: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-C", str(repo), *_IDENTITY, *args],
        capture_output=True,
        check=True,
        env=_env(),
        timeout=_TIMEOUT,
    )
    return done.stdout.decode("utf-8").strip()


def _쓰기(repo: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")


_B_FILES = {
    "pytest.ini": "[pytest]\npythonpath = .\n",
    "calc.py": _src("""
        OPTION = "--resume"
        OLD = "ab-old"

        def double(x):
            return x + x

        def triple(x):
            return x * 2
        """),
    "tests/conftest.py": "# B\n",
    "tests/test_calc.py": _src("""
        import calc

        def test_unchanged():
            assert calc.double(2) == 4
        """),
}

_M_FILES = {
    "calc.py": _src("""
        OPTION = "--resume"
        OLD = "ab-old"
        NEW = "cd-new"
        LABEL = "triple-fixed"

        def double(x):
            return x + x

        def triple(x):
            return x * 3

        def quadruple(x):
            return x * 4
        """),
    "tests/conftest.py": "# M\n",
    "tests/helpers.py": "SAMPLE = 1\n",
    "tests/test_calc.py": _src("""
        import pytest
        import calc

        def test_unchanged():
            assert calc.double(2) == 4

        def test_triple():
            assert calc.triple(2) == 6, "--resume"

        @pytest.mark.parametrize("x", [1, 2])
        def test_triple_cases(x):
            assert calc.triple(x) == 3 * x

        def test_quadruple():
            assert calc.quadruple(2) == 8

        def test_skipped():
            pytest.skip("나중에")

        def test_label():
            assert getattr(calc, "LABEL", "") == "triple-fixed"

        def test_multiline():
            assert calc.triple(1) == 3, "ab-old\\ncd-new"

        class TestCalc:
            def test_method(self):
                assert calc.triple(3) == 9
        """),
    "tests/test_new.py": _src("""
        from calc import quadruple

        def test_new_import():
            assert quadruple(1) == 4
        """),
}


def _저장소(tmp_path: Path) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _쓰기(repo, _B_FILES)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "B")
    base = _git(repo, "rev-parse", "HEAD")
    _쓰기(repo, _M_FILES)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "M")
    merge = _git(repo, "rev-parse", "HEAD")
    return repo, base, merge


def _워크트리들(repo: Path) -> list[str]:
    listed = _git(repo, "worktree", "list", "--porcelain")
    return [line for line in listed.splitlines() if line.startswith("worktree ")]


_PYTEST = (sys.executable, "-m", "pytest")
_NO_SETUP: tuple[tuple[str, ...], ...] = ()


def test_후보_하나의_숨은_시험과_지원_파일과_빠진_이유가_끝까지_나온다(tmp_path: Path) -> None:
    repo, base, merge = _저장소(tmp_path)
    (repo / "커밋하지_않은.txt").write_text("남는다\n", encoding="utf-8")
    전 = _워크트리들(repo)
    임시 = tmp_path / "임시"
    임시.mkdir()
    notes: list[str] = []

    got = sort_candidate(
        repo, base, merge, setup=_NO_SETUP, pytest=_PYTEST, temp_root=임시, out=notes.append
    )

    assert isinstance(got, Hidden), got
    assert set(got.hidden_tests) == {
        "tests/test_calc.py::test_triple",
        "tests/test_calc.py::test_triple_cases[1]",
        "tests/test_calc.py::test_triple_cases[2]",
        "tests/test_calc.py::TestCalc::test_method",
    }
    assert got.support_files == ("tests/conftest.py", "tests/helpers.py")
    빠진 = {d.node_id: (d.condition, d.cause) for d in got.dropped}
    assert 빠진 == {
        "tests/test_calc.py::test_quadruple": (2, "AttributeError"),
        "tests/test_calc.py::test_skipped": (1, "M 첫째 실행: 건너뜀"),
        "tests/test_calc.py::test_label": (3, "문자열 'LABEL'"),
        "tests/test_calc.py::test_multiline": (3, "문자열 'cd-new'"),
        "tests/test_new.py::test_new_import": (2, "결과 없음(모음 실패)"),
    }
    assert notes == []
    assert _워크트리들(repo) == 전
    assert list(임시.iterdir()) == []
    assert (repo / "커밋하지_않은.txt").read_text(encoding="utf-8") == "남는다\n"
    상태 = _git(repo, "-c", "core.quotepath=false", "status", "--porcelain")
    assert 상태 == "?? 커밋하지_않은.txt"


def _기록하는_명령(log: Path, *rest: str) -> tuple[str, ...]:
    """작업 폴더를 `log` 에 한 줄 덧붙이고, `rest` 가 있으면 그 파이썬 모듈 명령으로 이어 간다."""
    code = (
        "import os, sys, runpy\n"
        f"open({str(log)!r}, 'a', encoding='utf-8').write(os.getcwd() + '\\n')\n"
        "if len(sys.argv) > 1:\n"
        "    sys.argv = sys.argv[1:]\n"
        "    runpy.run_module(sys.argv[0], run_name='__main__')\n"
    )
    return (sys.executable, "-c", code, *rest)


def test_준비와_pytest_는_꺼낸_작업_트리를_작업_폴더로_돈다(tmp_path: Path) -> None:
    repo, base, merge = _저장소(tmp_path)
    준비_기록 = tmp_path / "setup.log"
    시험_기록 = tmp_path / "pytest.log"
    임시 = tmp_path / "임시"
    임시.mkdir()

    got = sort_candidate(
        repo,
        base,
        merge,
        setup=(_기록하는_명령(준비_기록),),
        pytest=_기록하는_명령(시험_기록, "pytest"),
        temp_root=임시,
        out=lambda _: None,
    )

    assert isinstance(got, Hidden), got
    준비 = 준비_기록.read_text(encoding="utf-8").splitlines()
    시험 = 시험_기록.read_text(encoding="utf-8").splitlines()
    assert len(준비) == 2  # M 과 B 의 작업 트리마다 한 번
    assert len(시험) == 3  # M 두 번, B 한 번
    assert 준비[0] == 시험[0] == 시험[1]
    assert 준비[1] == 시험[2]
    assert 준비[0] != 준비[1]
    for 폴더 in 준비:
        assert Path(폴더).resolve().is_relative_to(임시.resolve())
        assert Path(폴더).resolve() != repo.resolve()


def test_자식_환경에서_저장소_변수와_VIRTUAL_ENV_를_벗긴다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """워크트리에서 커밋할 때 pre-commit 아래의 git 이 `GIT_DIR` 을
    내보낸다(`.claude/rules/tools.md` 의 pre-commit 항목). 남기면 git 이 그 저장소를 보고,
    `VIRTUAL_ENV` 를 남기면 `uv run` 이 러너의 가상 환경을 가리킬 수 있다."""
    repo, base, merge = _저장소(tmp_path)
    엉뚱한 = tmp_path / "엉뚱한"
    엉뚱한.mkdir()
    _git(엉뚱한, "init", "-q")
    for name in REPO_LOCATION_VARS:
        monkeypatch.setenv(name, str(엉뚱한 / ".git" / name))
    monkeypatch.setenv("GIT_DIR", str(엉뚱한 / ".git"))
    monkeypatch.setenv("VIRTUAL_ENV", str(tmp_path / "러너의-venv"))
    기록 = tmp_path / "env.log"
    환경_기록 = (
        sys.executable,
        "-c",
        "import os\n"
        f"open({str(기록)!r}, 'a', encoding='utf-8').write("
        "repr(sorted(k for k in os.environ if k.startswith('GIT_') or k == 'VIRTUAL_ENV'))"
        " + '\\n')\n",
    )
    임시 = tmp_path / "임시"
    임시.mkdir()

    got = sort_candidate(
        repo, base, merge, setup=(환경_기록,), pytest=_PYTEST, temp_root=임시, out=print
    )

    assert isinstance(got, Hidden), got
    assert len(got.hidden_tests) == 4
    줄들 = 기록.read_text(encoding="utf-8").splitlines()
    assert len(줄들) == 2
    for 줄 in 줄들:
        assert "VIRTUAL_ENV" not in 줄
        assert not any(f"'{name}'" in 줄 for name in REPO_LOCATION_VARS)


def test_pytest_가_시간을_넘기면_실패_갈래이고_작업_트리를_걷는다(tmp_path: Path) -> None:
    repo, base, merge = _저장소(tmp_path)
    전 = _워크트리들(repo)
    임시 = tmp_path / "임시"
    임시.mkdir()

    got = sort_candidate(
        repo,
        base,
        merge,
        setup=_NO_SETUP,
        pytest=(sys.executable, "-c", "import time; time.sleep(60)"),
        temp_root=임시,
        out=lambda _: None,
        limits=Limits(pytest=2.0),
    )

    assert isinstance(got, Failure)
    assert "시간" in got.reason
    assert "pytest" in got.reason
    assert _워크트리들(repo) == 전
    assert list(임시.iterdir()) == []


def test_준비가_실패하면_실패_갈래다(tmp_path: Path) -> None:
    repo, base, merge = _저장소(tmp_path)
    전 = _워크트리들(repo)
    임시 = tmp_path / "임시"
    임시.mkdir()

    got = sort_candidate(
        repo,
        base,
        merge,
        setup=((sys.executable, "-c", "import sys; print('망가짐'); sys.exit(3)"),),
        pytest=_PYTEST,
        temp_root=임시,
        out=lambda _: None,
    )

    assert isinstance(got, Failure)
    assert "준비" in got.reason
    assert "3" in got.reason
    assert _워크트리들(repo) == 전
    assert list(임시.iterdir()) == []


def test_임시_폴더에_남은_것은_지우지_않고_그_이름을_알린다(tmp_path: Path) -> None:
    repo, base, merge = _저장소(tmp_path)
    임시 = tmp_path / "임시"
    임시.mkdir()
    notes: list[str] = []

    sort_candidate(
        repo,
        base,
        merge,
        setup=((sys.executable, "-c", "open('../낯선.txt', 'w').close()"),),
        pytest=_PYTEST,
        temp_root=임시,
        out=notes.append,
    )

    (parent,) = 임시.iterdir()
    assert [p.name for p in parent.iterdir()] == ["낯선.txt"]
    assert any("낯선.txt" in note and str(parent) in note for note in notes), notes


def test_임시_폴더에_남은_이름은_정렬해_다섯까지_보이고_모두의_수를_적는다(tmp_path: Path) -> None:
    repo, base, merge = _저장소(tmp_path)
    임시 = tmp_path / "임시"
    임시.mkdir()
    notes: list[str] = []
    make = "for n in 'gfedcba': open(f'../낯선{n}.txt', 'w').close()"

    sort_candidate(
        repo,
        base,
        merge,
        setup=((sys.executable, "-c", make),),
        pytest=_PYTEST,
        temp_root=임시,
        out=notes.append,
    )

    (note,) = [note for note in notes if "임시 폴더" in note]
    assert "남은 것 7개: 낯선a.txt, 낯선b.txt, 낯선c.txt, 낯선d.txt, 낯선e.txt …" in note, note
    assert "낯선f.txt" not in note, note


def test_M_의_시험_파일이_풀리지_않으면_후보의_실패_갈래이고_작업_트리가_남지_않는다(
    tmp_path: Path,
) -> None:
    repo, base, _ = _저장소(tmp_path)
    _쓰기(repo, {"tests/test_new.py": "def test_x(:\n"})
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "M 깨짐")
    merge = _git(repo, "rev-parse", "HEAD")
    전 = _워크트리들(repo)
    임시 = tmp_path / "임시"
    임시.mkdir()

    got = sort_candidate(
        repo, base, merge, setup=_NO_SETUP, pytest=_PYTEST, temp_root=임시, out=print
    )

    assert isinstance(got, Failure), got
    assert "M 의 시험 파일을 풀지 못했다: tests/test_new.py" in got.reason, got.reason
    assert _워크트리들(repo) == 전
    assert list(임시.iterdir()) == []


def test_없는_커밋은_실패_갈래다(tmp_path: Path) -> None:
    repo, base, _ = _저장소(tmp_path)
    got = sort_candidate(
        repo, base, "0" * 40, setup=_NO_SETUP, pytest=_PYTEST, temp_root=tmp_path, out=print
    )
    assert isinstance(got, Failure)
    assert "0" * 40 in got.reason


def test_덮을_자리를_쓰지_못하면_실패_갈래이고_작업_트리를_걷는다(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _쓰기(repo, {"tests/sub": "B 에서는 파일이다\n"})
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "B")
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "rm", "-q", "tests/sub")
    _쓰기(repo, {"tests/sub/test_a.py": "def test_a():\n    assert True\n"})
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "M")
    merge = _git(repo, "rev-parse", "HEAD")
    전 = _워크트리들(repo)
    임시 = tmp_path / "임시"
    임시.mkdir()

    got = sort_candidate(
        repo, base, merge, setup=_NO_SETUP, pytest=_PYTEST, temp_root=임시, out=lambda _: None
    )

    assert isinstance(got, Failure)
    assert "덮지 못했다: tests/sub/test_a.py" in got.reason
    assert _워크트리들(repo) == 전
    assert list(임시.iterdir()) == []


def _바깥_링크(링크: Path, 대상: Path) -> None:
    """`링크` 에 `대상` 폴더를 가리키는 링크를 만든다. 윈도는 권한 없이 만들 수 있는 junction
    이다(`tests/tools/test_canary.py` 의 같은 이름 도우미)."""
    링크.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(링크), str(대상)],
            check=True,
            capture_output=True,
            timeout=_TIMEOUT,
        )
    else:
        링크.symlink_to(대상, target_is_directory=True)


def test_작업_트리_안의_링크는_링크만_끊고_바깥_파일은_남긴다(tmp_path: Path) -> None:
    """지우는 길의 반박(`.claude/rules/tools.md` 의 지우는 도구 항목). git 2.32 의
    `git worktree remove --force` 는 꺼낸 자리 안의 junction 을 따라가 바깥을 지웠다."""
    repo, base, merge = _저장소(tmp_path)
    전 = _워크트리들(repo)
    바깥 = tmp_path / "바깥"
    (바깥 / "sub").mkdir(parents=True)
    (바깥 / "precious.txt").write_text("남는다\n", encoding="utf-8")
    (바깥 / "sub" / "deep.txt").write_text("남는다\n", encoding="utf-8")
    링크_만들기 = (
        sys.executable,
        "-c",
        "import subprocess, sys, os\n"
        f"target = {str(바깥)!r}\n"
        "for rel in ('.venv', os.path.join('tests', 'deep', 'link')):\n"
        "    os.makedirs(os.path.dirname(os.path.abspath(rel)), exist_ok=True)\n"
        "    if sys.platform == 'win32':\n"
        "        subprocess.run(['cmd', '/c', 'mklink', '/J', rel, target], check=True,"
        " capture_output=True, timeout=60)\n"
        "    else:\n"
        "        os.symlink(target, rel, target_is_directory=True)\n",
    )
    임시 = tmp_path / "임시"
    임시.mkdir()

    got = sort_candidate(
        repo,
        base,
        merge,
        setup=(링크_만들기,),
        pytest=_PYTEST,
        temp_root=임시,
        out=lambda _: None,
    )

    assert isinstance(got, Hidden), got
    assert (바깥 / "precious.txt").read_text(encoding="utf-8") == "남는다\n"
    assert (바깥 / "sub" / "deep.txt").read_text(encoding="utf-8") == "남는다\n"
    assert _워크트리들(repo) == 전
    assert list(임시.iterdir()) == []


def test_덮을_자리의_상위가_링크면_덮지_않는다(tmp_path: Path) -> None:
    """B 에 커밋된 링크 폴더를 지나 덮으면 작업 트리 바깥에 쓴다."""
    root = tmp_path / "root"
    (root / "tests").mkdir(parents=True)
    바깥 = tmp_path / "바깥"
    바깥.mkdir()
    _바깥_링크(root / "tests" / "sub", 바깥)
    assert overlay_target(root, "tests/sub/test_a.py") is None, "링크를 지나 덮을 자리를 냈다"
    assert overlay_target(root, "tests/other/test_a.py") == root / "tests" / "other" / "test_a.py"
    assert overlay_target(root, "tests/test_a.py") == root / "tests" / "test_a.py"


def test_작업_트리_자리_자체가_링크면_덮지_않는다(tmp_path: Path) -> None:
    """게이트(`tools/rerun_gates.py`)는 결과 커밋의 코드가 돈 뒤에 덮는다. 그 사이 작업 트리 자리가
    바깥을 가리키는 링크로 바뀌면, 그 아래 조각만 봐서는 바깥에 쓴다(티켓 07의 셀프 리뷰)."""
    바깥 = tmp_path / "바깥"
    (바깥 / "tests").mkdir(parents=True)
    root = tmp_path / "root"
    _바깥_링크(root, 바깥)
    assert overlay_target(root, "tests/test_a.py") is None, "링크인 작업 트리 자리 아래를 냈다"


def test_git_grep_은_대시로_시작하는_문자열과_낱말_경계를_가린다(tmp_path: Path) -> None:
    repo, base, merge = _저장소(tmp_path)
    limits = Limits()
    assert term_in(repo, base, STRING, "--resume", outside_tests=False, limits=limits)
    assert term_in(repo, merge, STRING, "cd-new", outside_tests=True, limits=limits)
    assert not term_in(repo, base, STRING, "cd-new", outside_tests=False, limits=limits)
    # 낱말 경계: `triple` 은 B 에 있지만 `tripl` 은 낱말로 없다
    assert term_in(repo, base, NAME, "triple", outside_tests=False, limits=limits)
    tripl = term_in(repo, base, NAME, "tripl", outside_tests=False, limits=limits)
    assert not tripl, "이름을 낱말 경계 없이 찾았다"
    # 문자열은 고정 문자열이라 낱말 안의 조각도 찾는다
    assert term_in(repo, base, STRING, "tripl", outside_tests=False, limits=limits)
    # tests/ 밖만 본다: `test_unchanged` 는 tests/ 안에만 있다
    inside = term_in(repo, merge, NAME, "test_unchanged", outside_tests=True, limits=limits)
    assert not inside, "tests/ 안을 찾았다"
    assert term_in(repo, merge, NAME, "test_unchanged", outside_tests=False, limits=limits)


def test_못_보는_것_명령_줄에_넘기지_못할_만큼_긴_문자열은_git_grep_을_띄우지_못해_실패_갈래다(
    tmp_path: Path,
) -> None:
    repo, base, _ = _저장소(tmp_path)
    # 대조: 같은 호출이 짧은 문자열이면 띄워져 답한다. 그래서 아래의 실패는 길이 때문이다
    assert term_in(repo, base, STRING, "a" * 10, outside_tests=False, limits=Limits()) is False
    # 윈도는 명령 줄 전체가 32767자(CreateProcess 의 한도), 리눅스는 인자 하나가 128KiB
    # (MAX_ARG_STRLEN)를 넘으면 띄우지 못한다. 둘 다 문서의 상수이고 재지 않았다. 이 PC 에서는
    # 셀프 리뷰가 2만 자는 띄워지고 4만 자는 WinError 206 인 것을 손으로 봤다(일지 2026-10-23-43)
    with pytest.raises(CandidateError, match="띄우지 못했다"):
        term_in(repo, base, STRING, "a" * 300_000, outside_tests=False, limits=Limits())


def test_NUL_이_든_문자열이_있어도_후보가_실패하지_않고_조각으로_조건_3_을_본다(
    tmp_path: Path,
) -> None:
    # 02 의 시험이 NUL 이 든 문자열을 들어, 실제 후보 표에서 02 가 git grep 을 띄우지 못하고
    # 통째로 실패 갈래였다(일지 2026-10-23-43)
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _쓰기(repo, _B_FILES)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "B")
    base = _git(repo, "rev-parse", "HEAD")
    _쓰기(
        repo,
        {
            "calc.py": _M_FILES["calc.py"],
            "tests/test_calc.py": _src("""
                import calc

                def test_unchanged():
                    assert calc.double(2) == 4

                def test_nul_new():
                    assert calc.triple(1) == 3, "ab\\x00cd-new"

                def test_nul_short():
                    assert calc.triple(2) == 6, "x\\x00y"
                """),
        },
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "M")
    merge = _git(repo, "rev-parse", "HEAD")
    임시 = tmp_path / "임시"
    임시.mkdir()

    got = sort_candidate(
        repo, base, merge, setup=_NO_SETUP, pytest=_PYTEST, temp_root=임시, out=print
    )

    assert isinstance(got, Hidden), got
    assert got.hidden_tests == ("tests/test_calc.py::test_nul_short",)
    빠진 = {d.node_id: (d.condition, d.cause) for d in got.dropped}
    assert 빠진 == {"tests/test_calc.py::test_nul_new": (3, "문자열 'cd-new'")}


def test_못_보는_것_이어_붙이거나_이스케이프가_든_문자열은_소스에서_찾지_못한다(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _쓰기(repo, {"calc.py": 'MSG = ("long-" "message")\nTAB = "a\\tb"\n'})
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "M")
    merge = _git(repo, "rev-parse", "HEAD")
    m = 'def test_a():\n    assert x == ("long-" "message"), "a\\tb"\n'
    (got,) = changed_tests({}, {"tests/test_a.py": m})
    assert got.strings == ("a\tb", "long-message")
    limits = Limits()
    for text in got.strings:
        found = term_in(repo, merge, STRING, text, outside_tests=True, limits=limits)
        assert not found, f"소스 글자와 다른 값을 찾았다: {text!r}"


def test_못_보는_것_B_에서_불러오지_못하는_conftest_는_후보_전체의_실패_갈래다(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _쓰기(repo, {"pytest.ini": "[pytest]\npythonpath = .\n", "calc.py": "OLD = 1\n"})
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "B")
    base = _git(repo, "rev-parse", "HEAD")
    _쓰기(
        repo,
        {
            "calc.py": "OLD = 1\nNEW = 2\n",
            "tests/conftest.py": "from calc import NEW\n",
            "tests/test_a.py": "def test_a():\n    assert 1 == 2\n",
        },
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "M")
    merge = _git(repo, "rev-parse", "HEAD")
    임시 = tmp_path / "임시"
    임시.mkdir()

    got = sort_candidate(
        repo, base, merge, setup=_NO_SETUP, pytest=_PYTEST, temp_root=임시, out=lambda _: None
    )

    assert isinstance(got, Failure)
    assert "junit xml 을 남기지 않았다(종료 4" in got.reason


def test_git_grep_이_0_과_1_밖으로_끝나면_실패_갈래다(tmp_path: Path) -> None:
    repo, _, _ = _저장소(tmp_path)
    with pytest.raises(CandidateError, match="git grep"):
        term_in(repo, "0" * 40, NAME, "triple", outside_tests=False, limits=Limits())
