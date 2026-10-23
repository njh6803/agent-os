"""`tools/rerun_gates.py`. 결과 커밋을 새 작업 트리로 꺼내 게이트 셋과 숨은 시험을 돈다.

임시 원본 저장소(B와 M)에서 회차의 클론을 짓고, 그 클론에 세션의 결과 커밋을 더한 뒤 작은 파이썬
명령을 게이트·준비·pytest 자리에 넣어 돈다. 실제 명령은 상수로 따로 단언한다.
"""

from __future__ import annotations

import inspect
import os
import subprocess
import sys
import textwrap
import time
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path

import pytest
from tools.rerun_files import (
    GATE_COMMANDS,
    TIER_SMALL,
    Gate,
    Hidden,
    SetupFailure,
    Task,
)
from tools.rerun_gates import (
    GATE_ARGV,
    PYTEST_ARGV,
    GateError,
    Limits,
    check_result,
    count_hidden,
    setup_failure_of,
)
from tools.rerun_round import (
    SETUP_ARGV,
    RoundDir,
    Setup,
    SetupEnd,
    SetupFailed,
    build_clone,
    create_round_dir,
)

from tools import rerun_gates

_TIMEOUT = 60


def _src(text: str) -> str:
    return textwrap.dedent(text).lstrip("\n")


def _git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@invalid", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=_TIMEOUT,
    )
    assert done.returncode == 0, f"git {args}: {done.stderr}"
    return done.stdout.strip()


def _쓰기(repo: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")


def _커밋(repo: Path, files: dict[str, str], message: str) -> str:
    _쓰기(repo, files)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", message)
    return _git(repo, "rev-parse", "HEAD")


_B = {
    "pytest.ini": "[pytest]\npythonpath = .\n",
    "calc.py": "def add(a, b):\n    return a - b\n",
    "tests/test_calc.py": _src("""
        from calc import add


        def test_old():
            assert add(1, 1) is not None
        """),
}
_M_CALC = "def add(a, b):\n    return a + b\n\n\ndef sub(a, b):\n    return a - b\n"
_M = {
    "calc.py": _M_CALC,
    # 시험 지원 파일. 숨은 시험이 이 픽스처를 쓴다
    "tests/conftest.py": _src("""
        import pytest


        @pytest.fixture
        def three():
            return 3
        """),
    "tests/test_calc.py": _src("""
        import pytest
        from calc import add


        def test_old():
            assert add(1, 1) is not None


        def test_add(three):
            assert add(1, 2) == three


        @pytest.mark.parametrize(("a", "b"), [(1, 2), (2, 1)], ids=["a::b", "c.d"])
        def test_param(a, b, three):
            assert add(a, b) == three


        class TestAdd:
            def test_zero(self):
                assert add(0, 0) == 0
        """),
    "tests/test_more.py": _src("""
        from calc import sub


        def test_sub():
            assert sub(3, 1) == 2
        """),
}
_NODES = (
    "tests/test_calc.py::test_add",
    "tests/test_calc.py::test_param[a::b]",
    "tests/test_calc.py::test_param[c.d]",
    "tests/test_calc.py::TestAdd::test_zero",
    "tests/test_more.py::test_sub",
)
_SUPPORT = ("tests/conftest.py",)


def _과제(base: str, merge: str) -> Task:
    return Task(
        task_id="model-rerun-07",
        ticket=".scratch/model-rerun/issues/07-gates-and-official-cost.md",
        base=base,
        merge=merge,
        branch="feature/07-gates-and-official-cost",
        tier=TIER_SMALL,
        size=1,
        order=0,
        pilot=False,
        pr_cost_usd=1.0,
        round_cap_usd=3.0,
        hidden_tests=_NODES,
        support_files=_SUPPORT,
        original_model_effort=None,
        arm_plan=("A",),
    )


def _회차(tmp_path: Path, result: dict[str, str]) -> tuple[RoundDir, Path, Task, str]:
    """원본(B, M)과 회차 폴더의 클론을 짓고, 클론에 세션의 결과 커밋 `result`를 더한다."""
    source = tmp_path / "원본"
    source.mkdir()
    _git(source, "init", "-q", "-b", "main")
    base = _커밋(source, _B, "B")
    merge = _커밋(source, _M, "M")
    place = create_round_dir(tmp_path / "뿌리", "model-rerun-07", "A", 1, token="abcd1234")
    build_clone(source, base, merge, place)
    commit = _커밋(place.clone, result, "세션")
    return place, source, _과제(base, merge), commit


def _명령(code: str) -> tuple[str, ...]:
    return (sys.executable, "-c", code)


def _환경() -> dict[str, str]:
    return dict(os.environ)


_PYTEST = (sys.executable, "-m", "pytest")
_NO_SETUP: tuple[tuple[str, ...], ...] = ()
_OK = _명령("pass")
_GATES_OK = (_OK, _OK, _OK)
_FAST = Limits(setup=60, gates=120, hidden=120, git=60)


def _작업_트리들(repo: Path) -> list[str]:
    listed = _git(repo, "worktree", "list", "--porcelain")
    return [line for line in listed.splitlines() if line.startswith("worktree ")]


def _돌기(
    place: RoundDir,
    source: Path,
    task: Task,
    commit: str,
    *,
    setup: Sequence[Sequence[str]] = _NO_SETUP,
    gates: Sequence[Sequence[str]] = _GATES_OK,
    pytest_argv: Sequence[str] = _PYTEST,
    limits: Limits = _FAST,
    env: dict[str, str] | None = None,
) -> tuple[rerun_gates.Checked, list[str]]:
    notes: list[str] = []
    got = check_result(
        place,
        source=source,
        commit=commit,
        task=task,
        env=_환경() if env is None else env,
        out=notes.append,
        setup=setup,
        gates=gates,
        pytest=pytest_argv,
        limits=limits,
    )
    return got, notes


def _같은_자리(path: str | Path) -> str:
    return os.path.normcase(os.path.realpath(path))


def _걷혔다(place: RoundDir) -> None:
    """게이트 작업 트리가 폴더로도 클론의 등록으로도 남지 않았다."""
    assert not os.path.lexists(place.path / "gate"), "게이트 작업 트리 폴더가 남았다"
    listed = [_같은_자리(line.removeprefix("worktree ")) for line in _작업_트리들(place.clone)]
    assert listed == [_같은_자리(place.clone)], "게이트 작업 트리의 등록이 남았다"


# --- 실제 상수 ---


def test_실제_게이트는_명세의_셋이고_pytest는_uv_run이다() -> None:
    assert [" ".join(argv) for argv in GATE_ARGV] == [
        "uv run ruff check .",
        "uv run ruff format --check .",
        "uv run python tools/run_checks.py",
    ]
    assert tuple(" ".join(argv) for argv in GATE_ARGV) == GATE_COMMANDS
    assert PYTEST_ARGV == ("uv", "run", "pytest")
    assert Limits() == Limits(setup=1800, gates=1800, hidden=600, git=300)
    defaults = inspect.signature(check_result).parameters
    assert defaults["setup"].default is SETUP_ARGV
    assert defaults["gates"].default is GATE_ARGV
    assert defaults["pytest"].default is PYTEST_ARGV
    assert defaults["limits"].default == Limits()


# --- 끝까지 ---


def test_결과_커밋만_게이트와_숨은_시험에_들고_작업_트리는_걷힌다(tmp_path: Path) -> None:
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    # 세션이 커밋하지 않고 남긴 변경. 클론에서 돌면 게이트도 숨은 시험도 빨갛다
    (place.clone / "calc.py").write_text("def add(a, b):\n    return a * b\n", encoding="utf-8")
    (place.clone / "남긴.txt").write_text("x\n", encoding="utf-8")
    sees_commit = _명령(
        "import os, pathlib, sys; "
        "ok = 'a + b' in pathlib.Path('calc.py').read_text() and not os.path.exists('남긴.txt'); "
        "sys.exit(0 if ok else 1)"
    )
    # 게이트는 숨은 시험 파일을 덮기 전에 돈다
    before_overlay = _명령(
        "import os, sys; sys.exit(1 if os.path.exists('tests/conftest.py') else 0)"
    )

    got, notes = _돌기(place, source, task, commit, gates=(sees_commit, before_overlay, _OK))

    assert got.setup_failure is None
    assert got.gates == tuple(
        Gate(command=" ".join(g), exit_code=0, timed_out=False)
        for g in (sees_commit, before_overlay, _OK)
    )
    # 덮은 지원 파일의 픽스처(`three`)로 돌았다
    assert got.hidden == Hidden(passed=5, total=5, failed=())
    assert notes == []
    _걷혔다(place)
    # 클론과 그 안의 남긴 것은 그대로다
    assert "a * b" in (place.clone / "calc.py").read_text(encoding="utf-8")
    assert (place.clone / "남긴.txt").exists()
    assert (place.path / "gate.log").exists()


def _표지_명령(mark: Path) -> tuple[str, ...]:
    """돌면 `mark`를 남기는 명령. 숨은 시험의 pytest 자리에 넣어 돌았는지 본다."""
    return _명령(f"open({str(mark)!r}, 'w').write('x')")


def test_게이트_하나가_0이_아니어도_셋을_다_돌고_숨은_시험은_돌지_않는다(tmp_path: Path) -> None:
    """판정(`tools/rerun_judge.py`의 `solved`)은 게이트가 초록일 때만 숨은 시험을 읽는다."""
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    third = tmp_path / "셋째.txt"
    gates = (_OK, _명령("import sys; sys.exit(3)"), _명령(f"open({str(third)!r}, 'w').write('3')"))
    pytest_ran = tmp_path / "pytest.txt"

    got, notes = _돌기(place, source, task, commit, gates=gates, pytest_argv=_표지_명령(pytest_ran))

    assert got.gates is not None
    assert [(g.exit_code, g.timed_out) for g in got.gates] == [(0, False), (3, False), (0, False)]
    assert third.exists()
    assert got.hidden is None
    assert not pytest_ran.exists(), "게이트가 초록이 아닌데 숨은 시험이 돌았다"
    assert notes == []
    _걷혔다(place)


_SLEEP_WITH_GRANDCHILD = _명령(
    "import subprocess, sys, time; "
    "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)']); "
    "time.sleep(30)"
)


def test_게이트_몫의_시간을_넘기면_그_게이트는_시간_넘김이고_남은_게이트는_돌지_않는다(
    tmp_path: Path,
) -> None:
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    later = tmp_path / "뒤.txt"
    marks = _명령(f"open({str(later)!r}, 'a').write('x')")
    limits = Limits(setup=60, gates=1.0, hidden=120, git=60)

    started = time.monotonic()
    got, notes = _돌기(
        place, source, task, commit, gates=(_SLEEP_WITH_GRANDCHILD, marks, marks), limits=limits
    )

    assert time.monotonic() - started < 40
    assert got.gates == (
        Gate(command=" ".join(_SLEEP_WITH_GRANDCHILD), exit_code=None, timed_out=True),
        Gate(command=" ".join(marks), exit_code=None, timed_out=False),
        Gate(command=" ".join(marks), exit_code=None, timed_out=False),
    )
    assert not later.exists()
    assert got.hidden is None
    # 손자까지 꺼서 작업 트리를 쥔 프로세스가 남지 않는다
    assert notes == []
    _걷혔다(place)


def test_찾지_못한_게이트는_종료_코드도_시간_넘김도_없다(tmp_path: Path) -> None:
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    missing = ("없는-게이트-07",)

    got, _ = _돌기(place, source, task, commit, gates=(missing, _OK, _OK))

    assert got.gates is not None
    assert got.gates[0] == Gate(command="없는-게이트-07", exit_code=None, timed_out=False)
    assert [g.exit_code for g in got.gates[1:]] == [0, 0]
    assert got.hidden is None


# --- 숨은 시험 ---


def test_숨은_시험의_일부가_실패하면_그_노드만_실패로_든다(tmp_path: Path) -> None:
    calc = (
        "def add(a, b):\n    return a + b if a != 2 else 0\n\n\ndef sub(a, b):\n    return a - b\n"
    )
    place, source, task, commit = _회차(tmp_path, {"calc.py": calc})

    got, _ = _돌기(place, source, task, commit)

    assert got.hidden == Hidden(passed=4, total=5, failed=("tests/test_calc.py::test_param[c.d]",))
    _걷혔다(place)


def test_한_파일의_모음_오류는_실행_전체를_멈춰_모든_노드가_실패다(tmp_path: Path) -> None:
    """노드 ID로 돌린 pytest는 한 파일을 모으지 못하면 종료 4로 멈추고, junit에는 그 파일의
    `error`만 남는다(`--continue-on-collection-errors`를 줘도 같았다). 다른 파일의 노드도 결과가
    없어 실패로 센다(모듈 독스트링의 못 보는 것)."""
    place, source, task, commit = _회차(tmp_path, {"calc.py": "def add(a, b):\n    return a + b\n"})

    got, _ = _돌기(place, source, task, commit)

    assert got.hidden == Hidden(passed=0, total=5, failed=_NODES)
    _걷혔다(place)


def test_junit_xml이_없으면_모든_노드가_실패다(tmp_path: Path) -> None:
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})

    got, _ = _돌기(place, source, task, commit, pytest_argv=_명령("pass"))

    assert got.hidden == Hidden(passed=0, total=5, failed=_NODES)
    _걷혔다(place)


def test_숨은_시험이_시간을_넘기면_모든_노드가_실패이고_손자까지_끈다(tmp_path: Path) -> None:
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    limits = Limits(setup=60, gates=120, hidden=1.0, git=60)

    started = time.monotonic()
    got, notes = _돌기(
        place, source, task, commit, pytest_argv=_SLEEP_WITH_GRANDCHILD, limits=limits
    )

    assert time.monotonic() - started < 40
    assert got.hidden == Hidden(passed=0, total=5, failed=_NODES)
    assert notes == []
    _걷혔다(place)


def test_xml을_다_쓴_뒤에_시간을_넘겨도_모든_노드가_실패다(tmp_path: Path) -> None:
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    cases = "".join(
        f'<testcase classname="{c}" name="{n}"/>'
        for c, n in (
            ("tests.test_calc", "test_add"),
            ("tests.test_calc", "test_param[a::b]"),
            ("tests.test_calc", "test_param[c.d]"),
            ("tests.test_calc.TestAdd", "test_zero"),
            ("tests.test_more", "test_sub"),
        )
    )
    # 모든 노드가 통과한 xml 을 쓰고 끝나지 않는 pytest
    writes_then_hangs = _명령(
        "import sys, time\n"
        "xml = next(a for a in sys.argv if a.startswith('--junitxml=')).split('=', 1)[1]\n"
        f"open(xml, 'w', encoding='utf-8').write({_xml(cases)!r})\n"
        "time.sleep(30)\n"
    )
    limits = Limits(setup=60, gates=120, hidden=3.0, git=60)

    got, _ = _돌기(place, source, task, commit, pytest_argv=writes_then_hangs, limits=limits)

    assert (place.path / "hidden.xml").exists()
    assert got.hidden == Hidden(passed=0, total=5, failed=_NODES)


def test_UTF_8이_아닌_junit_xml은_모든_노드가_실패다(tmp_path: Path) -> None:
    """xml 은 결과 커밋의 코드가 고쳐 쓸 수 있다. 풀지 못하면 예외가 아니라 실패다."""
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    writes_bytes = _명령(
        "import sys\n"
        "xml = next(a for a in sys.argv if a.startswith('--junitxml=')).split('=', 1)[1]\n"
        "open(xml, 'wb').write(b'\\xff\\xfe<testsuites/>')\n"
    )

    got, notes = _돌기(place, source, task, commit, pytest_argv=writes_bytes)

    assert got.hidden == Hidden(passed=0, total=5, failed=_NODES)
    assert notes == []
    _걷혔다(place)


def test_앞선_junit_xml은_지우고_돈다(tmp_path: Path) -> None:
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    (place.path / "hidden.xml").write_text(
        '<testsuites><testsuite><testcase classname="tests.test_more" name="test_sub"/>'
        "</testsuite></testsuites>",
        encoding="utf-8",
    )

    got, _ = _돌기(place, source, task, commit, pytest_argv=_명령("pass"))

    assert got.hidden == Hidden(passed=0, total=5, failed=_NODES)


# --- 준비 ---


def test_준비가_실패하면_그_명령과_종료_코드를_적고_게이트와_숨은_시험을_돌지_않는다(
    tmp_path: Path,
) -> None:
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    ran = tmp_path / "돌았다.txt"
    marks = _명령(f"open({str(ran)!r}, 'a').write('x')")
    failing = _명령("import sys; sys.exit(5)")

    got, notes = _돌기(
        place, source, task, commit, setup=(_OK, failing, marks), gates=(marks, marks, marks)
    )

    assert got.setup_failure == SetupFailure(
        command=" ".join(failing), exit_code=5, timed_out=False
    )
    assert got.gates is None
    assert got.hidden is None
    assert not ran.exists()
    assert notes == []
    _걷혔다(place)


def test_준비는_결과_작업_트리에서_돈다(tmp_path: Path) -> None:
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    writes = _명령("open('준비.txt', 'w').write('x')")
    sees = _명령("import os, sys; sys.exit(0 if os.path.exists('준비.txt') else 1)")

    got, _ = _돌기(place, source, task, commit, setup=(writes,), gates=(sees, _OK, _OK))

    assert got.gates is not None
    assert got.gates[0].exit_code == 0
    assert not (place.clone / "준비.txt").exists()


@pytest.mark.parametrize(
    ("failed", "expected"),
    [
        (
            SetupFailed(1, "uv sync", SetupEnd.EXITED, 2),
            SetupFailure("uv sync", 2, timed_out=False),
        ),
        (
            SetupFailed(0, "uv sync", SetupEnd.TIMED_OUT, None),
            SetupFailure("uv sync", None, timed_out=True),
        ),
        (
            SetupFailed(0, "uv sync", SetupEnd.NOT_STARTED, None),
            SetupFailure("uv sync", None, timed_out=False),
        ),
    ],
    ids=["0이 아닌 종료", "시간 넘김", "띄우지 못함"],
)
def test_준비_실패는_끝난_꼴을_종료_코드와_시간_넘김_두_칸으로_옮긴다(
    failed: SetupFailed, expected: SetupFailure
) -> None:
    assert setup_failure_of(failed) == expected


# --- 환경 ---


def test_자식_환경에서_저장소를_가리키는_변수와_VIRTUAL_ENV를_벗긴다(tmp_path: Path) -> None:
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    전 = _작업_트리들(source)
    env = _환경()
    # 남으면 git 이 원본 저장소를 보고, 게이트가 러너의 가상 환경으로 돈다
    env["GIT_DIR"] = str(source / ".git")
    env["GIT_WORK_TREE"] = str(source)
    env["GIT_INDEX_FILE"] = str(source / ".git" / "index")
    env["VIRTUAL_ENV"] = str(tmp_path / "러너의-venv")
    clean = _명령(
        "import os, sys; "
        "bad = [k for k in ('GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'VIRTUAL_ENV') "
        "if k in os.environ]; "
        "sys.exit(1 if bad else 0)"
    )

    got, notes = _돌기(
        place, source, task, commit, setup=(clean,), gates=(clean, _OK, _OK), env=env
    )

    assert got.setup_failure is None
    assert got.gates is not None
    assert got.gates[0].exit_code == 0
    assert got.hidden == Hidden(passed=5, total=5, failed=())
    assert notes == []
    assert _작업_트리들(source) == 전
    _걷혔다(place)


# --- 링크와 걷기 ---


def _링크(link: Path, target: Path) -> None:
    """디렉터리 링크. 윈도는 권한 없이 만드는 junction, 나머지는 심볼릭 링크."""
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        link.symlink_to(target, target_is_directory=True)


def _링크인가(path: Path) -> bool:
    return os.path.islink(path) or os.path.isjunction(path)


def _링크_명령(link: str, target: Path) -> tuple[str, ...]:
    """작업 트리 안 `link`(상대 경로)에 `target`을 가리키는 링크를 만드는 준비 명령. 윈도는 권한
    없이 만드는 junction이다. 그 자리에 폴더가 있으면 먼저 지운다."""
    return _명령(
        "import os, shutil, sys\n"
        f"link = {link!r}\n"
        f"target = {str(target)!r}\n"
        "os.makedirs(os.path.dirname(link) or '.', exist_ok=True)\n"
        "shutil.rmtree(link, ignore_errors=True)\n"
        "if sys.platform == 'win32':\n"
        "    import _winapi\n"
        "    _winapi.CreateJunction(target, link)\n"
        "else:\n"
        "    os.symlink(target, link, target_is_directory=True)\n"
    )


def test_작업_트리_안의_링크는_링크만_끊고_바깥_파일은_남는다(tmp_path: Path) -> None:
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    outside = tmp_path / "바깥"
    outside.mkdir()
    (outside / "keep.txt").write_text("남는다", encoding="utf-8")
    setup = (
        _링크_명령(".venv", outside),
        _링크_명령("deep/er/link", outside),
        _명령("open('커밋하지_않은.txt', 'w').write('x')"),
    )

    got, notes = _돌기(place, source, task, commit, setup=setup)

    assert got.hidden == Hidden(passed=5, total=5, failed=())
    assert notes == []
    _걷혔다(place)
    assert (outside / "keep.txt").read_text(encoding="utf-8") == "남는다"


def test_덮을_자리가_링크를_지나면_덮지_않고_모든_노드가_실패다(tmp_path: Path) -> None:
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    outside = tmp_path / "바깥"
    outside.mkdir()
    (outside / "keep.txt").write_text("남는다", encoding="utf-8")

    got, notes = _돌기(place, source, task, commit, setup=(_링크_명령("tests", outside),))

    # 링크를 따라 바깥에 쓰지 않았다
    assert sorted(p.name for p in outside.iterdir()) == ["keep.txt"]
    assert got.hidden == Hidden(passed=0, total=5, failed=_NODES)
    assert notes == []
    _걷혔다(place)


def test_준비_뒤에_작업_트리_자리가_링크로_바뀌면_게이트도_숨은_시험도_돌지_않는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """결과 커밋의 코드가 도는 준비(의존성 설치의 빌드 스크립트 등)가 떼어 낸 손자가 작업 트리
    자리를 옮기고 거기에 바깥을 가리키는 링크를 두는 길을, 준비를 감싸 흉내 낸다. 따라가면 게이트와
    숨은 시험이 바깥에서 돈다(`uv run`은 그 자리의 가상 환경을 고친다). 윈도에서는 이 시험의 게이트
    명령이 스스로 자리를 옮기지 못했다(`WinError 32`). 가상 환경의 `python.exe`로 띄운 자식은 옮기지
    못했고 기반 인터프리터로 띄운 자식은 옮겼다(2026-10-23 스크래치로 손으로 봤다). 가상 환경의
    `python.exe`는 기반 인터프리터를 자식으로 띄우는 런처라, 그 런처가 자리를 쥔 것으로 본다."""
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    outside = tmp_path / "바깥"
    outside.mkdir()
    (outside / "keep.txt").write_text("남는다", encoding="utf-8")
    gate = place.path / "gate"
    real_setup = rerun_gates.run_setup

    def 자리를_바꾸는(
        cwd: Path,
        commands: Sequence[Sequence[str]],
        *,
        env: Mapping[str, str],
        log: Path,
        timeout: float,
    ) -> Setup:
        done = real_setup(cwd, commands, env=env, log=log, timeout=timeout)
        gate.rename(tmp_path / "옮긴_자리")
        _링크(gate, outside)
        return done

    monkeypatch.setattr(rerun_gates, "run_setup", 자리를_바꾸는)
    ran = tmp_path / "돌았다.txt"
    marks = _표지_명령(ran)

    got, notes = _돌기(place, source, task, commit, gates=(marks, marks, marks), pytest_argv=marks)

    assert got.gates == (Gate(command=" ".join(marks), exit_code=None, timed_out=False),) * 3
    assert got.hidden is None
    assert not ran.exists(), "링크로 바뀐 자리에서 게이트나 숨은 시험이 돌았다"
    assert sorted(p.name for p in outside.iterdir()) == ["keep.txt"]
    # 걷기도 그 링크를 따라가지 않고 알린다
    assert len(notes) == 1
    assert "링크다" in notes[0]
    assert _링크인가(gate)


def test_링크를_끊지_못하면_작업_트리를_걷지_않고_알린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    stuck = str(place.path / "gate" / "stuck")

    def 못_끊는(folder: str | os.PathLike[str]) -> list[str]:
        del folder
        return [stuck]

    monkeypatch.setattr(rerun_gates, "cut_links", 못_끊는)

    _, notes = _돌기(place, source, task, commit)

    assert len(notes) == 1
    assert "걷지 않았다" in notes[0] and stuck in notes[0]
    assert (place.path / "gate").exists()


def test_클론의_관리_폴더_안의_링크도_끊고_걷어_바깥과_원본이_남는다(tmp_path: Path) -> None:
    """`git worktree remove`는 클론의 `.git/worktrees/<이름>/`도 지우며 그 안의 junction 을
    따라갔다(이 PC의 git 2.32, 커밋 전 반박 검증). 게이트 명령이 거기에 바깥과 원본의 `.git`을
    가리키는 링크를 심는다."""
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    outside = tmp_path / "바깥"
    (outside / "sub").mkdir(parents=True)
    (outside / "sub" / "keep.txt").write_text("남는다", encoding="utf-8")
    plant = _명령(
        "import os, sys\n"
        "admin = os.path.abspath(open('.git', encoding='utf-8').read().split(':', 1)[1].strip())\n"
        f"pairs = (('바깥', {str(outside)!r}), ('원본', {str(source / '.git')!r}))\n"
        "for name, target in pairs:\n"
        "    link = os.path.join(admin, name)\n"
        "    if sys.platform == 'win32':\n"
        "        import _winapi\n"
        "        _winapi.CreateJunction(target, link)\n"
        "    else:\n"
        "        os.symlink(target, link, target_is_directory=True)\n"
    )

    got, notes = _돌기(place, source, task, commit, gates=(plant, _OK, _OK))

    assert got.gates is not None and got.gates[0].exit_code == 0
    assert (outside / "sub" / "keep.txt").read_text(encoding="utf-8") == "남는다"
    assert _git(source, "rev-parse", task.merge).strip() == task.merge
    assert notes == []
    _걷혔다(place)


@pytest.mark.parametrize("which", ["gate", "clone-git"])
def test_작업_트리_자리나_클론의_git_폴더가_링크로_바뀌면_따라가지_않고_걷지_않고_알린다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, which: str
) -> None:
    """게이트 명령이 떼어 낸 손자가 숨은 시험 뒤에 그 자리를 옮기고 거기에 바깥을 가리키는 링크를
    두는 길을, 숨은 시험의 셈을 감싸 흉내 낸다. 바깥 안의 링크는 끊기지 않는다."""
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    outside = tmp_path / "바깥"
    outside.mkdir()
    elsewhere = tmp_path / "다른_곳"
    elsewhere.mkdir()
    (elsewhere / "keep.txt").write_text("남는다", encoding="utf-8")
    _링크(outside / "안의_링크", elsewhere)
    bent = place.path / "gate" if which == "gate" else place.clone / ".git"

    def 자리를_바꾸는(text: str | None, nodes: Sequence[str]) -> Hidden:
        bent.rename(tmp_path / "옮긴_자리")
        _링크(bent, outside)
        return count_hidden(text, nodes)

    monkeypatch.setattr(rerun_gates, "count_hidden", 자리를_바꾸는)

    _, notes = _돌기(place, source, task, commit)

    assert len(notes) == 1
    assert "링크다" in notes[0] and str(bent) in notes[0]
    assert _링크인가(outside / "안의_링크")
    assert (elsewhere / "keep.txt").read_text(encoding="utf-8") == "남는다"
    assert _링크인가(bent)


# --- 짓지 못함 ---


def test_결과_커밋이_해시_꼴이_아니면_작업_트리를_짓지_않는다(tmp_path: Path) -> None:
    place, source, task, _ = _회차(tmp_path, {"calc.py": _M_CALC})

    with pytest.raises(GateError, match="결과 커밋"):
        _돌기(place, source, task, "--orphan")

    assert not (place.path / "gate").exists()


def test_클론에_없는_결과_커밋이면_GateError이고_남는_것이_없다(tmp_path: Path) -> None:
    place, source, task, _ = _회차(tmp_path, {"calc.py": _M_CALC})

    with pytest.raises(GateError, match="worktree add"):
        _돌기(place, source, task, "0" * 40)

    _걷혔다(place)


def test_원본에서_M의_파일을_읽지_못하면_작업_트리를_짓기_전에_GateError다(tmp_path: Path) -> None:
    place, source, task, commit = _회차(tmp_path, {"calc.py": _M_CALC})
    task = replace(task, support_files=("tests/없는_conftest.py",))

    with pytest.raises(GateError, match="tests/없는_conftest.py"):
        _돌기(place, source, task, commit)

    assert not (place.path / "gate").exists()


# --- junit 셈 ---


def _xml(*cases: str) -> str:
    return f"<testsuites><testsuite>{''.join(cases)}</testsuite></testsuites>"


def test_junit의_노드는_pytest의_classname과_name으로_찾는다() -> None:
    nodes = (
        "tests/test_a.py::test_x",
        "tests/sub/test_b.py::TestK::test_m",
        "tests/test_a.py::test_p[a::b]",
        "tests/test_a.py::test_p[c.d/e]",
    )
    text = _xml(
        '<testcase classname="tests.test_a" name="test_x"/>',
        '<testcase classname="tests.sub.test_b.TestK" name="test_m"/>',
        '<testcase classname="tests.test_a" name="test_p[a::b]"/>',
        '<testcase classname="tests.test_a" name="test_p[c.d/e]"/>',
    )
    assert count_hidden(text, nodes) == Hidden(passed=4, total=4, failed=())


@pytest.mark.parametrize(
    "child",
    ['<failure message="x"/>', '<error message="x"/>', '<skipped message="x"/>'],
    ids=["failure", "error", "건너뜀"],
)
def test_실패_오류_건너뜀은_실패다(child: str) -> None:
    nodes = ("tests/test_a.py::test_x", "tests/test_a.py::test_y")
    text = _xml(
        f'<testcase classname="tests.test_a" name="test_x">{child}</testcase>',
        '<testcase classname="tests.test_a" name="test_y"/>',
    )
    assert count_hidden(text, nodes) == Hidden(passed=1, total=2, failed=nodes[:1])


def test_같은_노드의_testcase가_둘이면_차례와_상관없이_나쁜_쪽을_든다() -> None:
    nodes = ("tests/test_a.py::test_x", "tests/test_a.py::test_y")
    text = _xml(
        '<testcase classname="tests.test_a" name="test_x"/>',
        '<testcase classname="tests.test_a" name="test_x"><error message="teardown"/></testcase>',
        '<testcase classname="tests.test_a" name="test_y"><error message="setup"/></testcase>',
        '<testcase classname="tests.test_a" name="test_y"/>',
    )
    assert count_hidden(text, nodes) == Hidden(passed=0, total=2, failed=nodes)


def test_xml에_없는_노드와_모음_오류만_남은_파일은_실패다() -> None:
    nodes = ("tests/test_a.py::test_x", "tests/test_b.py::test_y")
    text = _xml(
        '<testcase classname="tests.test_a" name="test_x"/>',
        '<testcase classname="" name="tests.test_b">'
        '<error message="collection failure"/></testcase>',
    )
    assert count_hidden(text, nodes) == Hidden(passed=1, total=2, failed=nodes[1:])


@pytest.mark.parametrize("text", [None, "", "<testsuites><testcase", "<a/>"])
def test_xml이_없거나_풀리지_않거나_비면_모든_노드가_실패다(text: str | None) -> None:
    nodes = ("tests/test_a.py::test_x",)
    assert count_hidden(text, nodes) == Hidden(passed=0, total=1, failed=nodes)


def _엔터티(declaration: str) -> str:
    """`test_x`의 이름을 엔터티 `name`으로 적은 junit xml."""
    return f'<?xml version="1.0"?><!DOCTYPE testsuites [{declaration}]>' + _xml(
        '<testcase classname="tests.test_a" name="&name;"/>'
    )


def test_안의_엔터티는_풀고_바깥_엔터티는_풀지_않는다(tmp_path: Path) -> None:
    """모듈 독스트링의 `ElementTree`가 바깥 엔터티를 풀지 않는다는 주장. 안의 엔터티로 같은 xml 이
    통과로 읽히는 것을 먼저 보여, 바깥 엔터티의 실패가 풀지 않아서임을 가른다."""
    nodes = ("tests/test_a.py::test_x",)
    name_file = tmp_path / "name.txt"
    name_file.write_text("test_x", encoding="utf-8")

    inner = _엔터티('<!ENTITY name "test_x">')
    outer = _엔터티(f'<!ENTITY name SYSTEM "{name_file.as_uri()}">')

    assert count_hidden(inner, nodes) == Hidden(passed=1, total=1, failed=())
    assert count_hidden(outer, nodes) == Hidden(passed=0, total=1, failed=nodes)


def test_엔터티_증폭은_풀리지_않아_모든_노드가_실패다() -> None:
    """모듈 독스트링의 expat 2.4.1부터 엔터티 증폭(billion laughs)이 막힌다는 주장."""
    nodes = ("tests/test_a.py::test_x",)
    levels = ['<!ENTITY lol0 "test_x">']
    levels += [f'<!ENTITY lol{i} "{f"&lol{i - 1};" * 10}">' for i in range(1, 10)]
    levels.append('<!ENTITY name "&lol9;">')

    started = time.monotonic()
    got = count_hidden(_엔터티("".join(levels)), nodes)

    assert got == Hidden(passed=0, total=1, failed=nodes)
    assert time.monotonic() - started < 10
