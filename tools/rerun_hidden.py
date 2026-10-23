"""다시 풀기의 숨은 시험 가르기. 후보 하나(B와 M)의 원래 PR 시험 가운데 숨은 시험으로 쓸 노드를
고른다.

근거는 `.scratch/model-rerun/spec.md`의 "숨은 시험 가르기"와 티켓
`.scratch/model-rerun/issues/02-hidden-test-filter.md`다. 과제 고르기(05)가 후보마다
`sort_candidate`를 부르고, 그 결과의 숨은 시험 ID와 지원 파일을 과제 목록(`tools/rerun_files.py`)의
칸에 옮긴다.

두 층이다.
- 값만 받는 함수(`changed_tests`, `read_junit`, `node_facts`, `sort_nodes`)는 git·pytest를 부르지
  않는다.
  - 바뀐 시험은 M과 B의 시험 파일에서 AST로 견준 시험 함수다. 모듈 수준의 `test_*`와 `Test*`
    클래스의 `test_*` 메서드 가운데 M에 새로 생겼거나 함수 정의(데코레이터 포함)의 AST 덤프가 다른
    것이다. 줄 번호는 덤프에 들지 않아 줄만 옮긴 시험은 바뀌지 않았다. B에서 풀리지 않는 파일의
    시험은 모두 새것이고, M에서 풀리지 않는 파일은 바뀐 시험을 셀 수 없어 그 후보의 실패 갈래다.
  - 시험의 단위는 pytest의 노드 ID다. 매개변수화한 시험은 경우마다 따로 센다.
  - 조건 1. M에서 두 번 다 통과한 노드만 남는다.
  - 조건 2. B에 M의 시험 파일과 지원 파일을 덮고 돌린 junit xml에서, `error` 요소인 노드,
    `failure`의 `message`가 `AttributeError`·`NameError`·`TypeError`로 시작하는 노드, 통과하거나
    건너뛴 노드, 결과가 없는 노드(모음 오류로 파일이 통째로 실패했다)는 빠진다.
  - 조건 3. 함수 본문의 이름(`Name`의 id, `Attribute`의 attr)과 길이가 둘 이상인 문자열 상수
    가운데 하나라도 M의 `tests/` 밖 추적 파일에 있고 B의 추적 파일 어디에도 없으면 그 함수의
    노드가 모두 빠진다. 줄바꿈이 든 문자열은 줄마다 나눠 길이가 둘 이상인 줄 하나를 문자열 하나로
    센다. `git grep`이 줄바꿈이 든 패턴을 줄마다 따로 찾아 한 줄만 있어도 있다고 답하기 때문이다.
    NUL도 그 자리에서 나눈다. NUL이 든 패턴은 명령 줄에 넘길 수 없어, 나누지 않으면 그 후보 전체가
    실패 갈래였다(05의 실제 후보 표에서 02 자신이 그랬다, 일지 2026-10-23-38).
  - 빠진 노드에는 처음 걸린 조건과 그 까닭(실패 종류, 이름)을 든다. M 두 실행 어디에도 결과가
    없는 바뀐 시험(마커로 빠졌거나 M에서 모으지 못했다)은 함수 노드 ID 하나로 조건 1에서 빠진다.
- 바깥 층(`sort_candidate`, `term_in`)이 git과 pytest를 부른다. B와 M을 시스템 임시 폴더(또는
  `temp_root`) 아래 `git worktree add --detach`로 꺼내고, 작업 트리마다 준비 명령(실제는
  `uv sync`)을 그 작업 트리를 작업 폴더로 돌린 뒤 같은 자리에서 pytest(실제는 `uv run pytest`)를
  띄운다. 러너 체크아웃의 `.venv`는 `agent_os`를 편집 설치로 러너의 `src/`에 묶어, 그 파이썬으로
  돌면 B에 덮은 시험이 러너의 새 코드로 돌기 때문이다(명세 같은 절의 2026-10-23 주석). M에서는
  바뀐 시험이 든 파일을 두 번, B에서는 덮고 한 번 돌리고, junit xml에서 바뀐 시험의 노드만 읽는다.
  junit xml은 pytest가 이 도구의 임시 폴더에 쓴 파일이라 표준 라이브러리 파서로 푼다. 조건 3의
  찾기는 작업 트리 없이 커밋에 대고
  `git grep -q -F`로 하고, 이름은 `-w`를 더한다. 패턴은 `-e`로 넘겨 `-`로 시작하는 문자열을
  옵션으로 읽지 않게 한다. 종료 0은 있음, 1은 없음이고 그 밖은 그 후보의 실패 갈래다.
- 하위 프로세스마다 시간 제한(`Limits`)을 두고, 넘김과 준비의 실패와 junit이 없는 것, B의 작업
  트리에 덮지 못한 것(B에서 상위 자리가 파일이다 등)은 그 후보의 실패 갈래(`Failure`)다. 시간을 넘긴
  준비와 pytest는 프로세스 트리째 끈다(윈도는 `taskkill /T`, 그 밖은 프로세스 그룹). 자식 환경에서
  `tools.run_hooks.REPO_LOCATION_VARS`와 `VIRTUAL_ENV`를 벗긴다.
- 꺼낸 작업 트리는 성공·실패·시간 넘김 어느 길에서도 걷는다. 걷기 전에 그 안의 링크(심볼릭 링크,
  junction)를 링크만 끊는다. git 2.32의 `git worktree remove --force`가 junction을 따라가 바깥
  파일까지 지웠다(선례 `tools/canary.py`의 `_cut_links`). 링크를 끊지 못하면 걷지 않고 알린다.
  임시 폴더에는 이 도구가 지은 이름(작업 트리 둘, junit xml과 로그)만 지운다.
- 덮을 자리의 상위 폴더나 그 파일이 B의 링크면 작업 트리 바깥에 쓸 수 있어 덮지 않고 실패 갈래로
  센다(`overlay_target`).

못 보는 것.
- 조건 3은 시험 함수 본문만 본다. 본문이 부르는 모듈 수준 상수와 도우미 안의 이름, 데코레이터와
  인자 기본값의 이름은 보지 않아, M이 새로 지은 모듈 수준 이름에 기대는 시험이 조건 3을
  지난다(명세 조건 3의 2026-10-22 주석이 한계로 두었다). 본문의 docstring도 문자열 상수로 세어,
  M이 새로 쓴 문서에 같은 글이 있으면 그 시험이 빠진다.
- 조건 3은 문자열 상수의 값을 소스 글자에서 찾는다. 이어 붙인 문자열(`"ab" "cd"`)과 이스케이프가
  든 문자열(`"a\\tb"`)은 값과 소스 글자가 달라 M에 있어도 없다고 나와, 그 문자열에 기대는 시험이
  조건 3을 지난다.
- 조건 3의 문자열이 명령 줄에 넘기지 못할 만큼 길면 `git grep`을 띄우지 못해, 그 노드가 아니라
  후보 전체가 실패 갈래다.
- 시험 파일과 지원 파일은 `tools/rerun_files.py`의 허용 꼴(`is_test_file`, `is_support_file`)에
  드는 경로만 본다. 그 꼴 밖의 이름(한글이 든 경로 등)으로 바뀐 시험은 숨은 시험 후보가 되지 않는다.
  pytest 설정이 `python_files`로 더 모으는 `tests/` 아래 `*_test.py`는 시험 파일이 아니라 지원
  파일로 덮인다.
- 중첩한 `Test*` 클래스의 메서드, pytest가 모으지만 `test_`로 시작하지 않는 `test*` 함수, `if`
  같은 문 안에서 정의한 시험은 보지 않는다.
- 조건 2는 실패 메시지의 머리만 본다. `ImportError`·`ModuleNotFoundError`처럼 새 이름에서 나는
  다른 예외는 남는다(명세가 정한 세 종류뿐이다).
- B에 덮은 `conftest.py`가 B에 없는 이름을 불러오면 pytest가 모으기 전에 종료 4로 멈추고 junit
  xml을 남기지 않아, 노드마다 조건 2로 빠지지 않고 후보 전체가 실패 갈래다.
- 프로세스 트리를 끄는 길은 그 트리를 떠난 손자(새 세션이나 그룹으로 떼어 낸 것)를 끄지 못한다. 그
  손자가 작업 트리를 쥐면 걷지 못하고, 남은 자리와 걷는 법을 `out`으로 알린다.
"""

from __future__ import annotations

import ast
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ElementTree
from collections.abc import Callable, Generator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from tools.rerun_files import is_support_file, is_test_file
from tools.run_hooks import REPO_LOCATION_VARS

# 실제 준비와 pytest 명령(티켓 "바깥 층"). 시험은 작은 명령을 인자로 넘긴다.
SETUP_COMMANDS: tuple[tuple[str, ...], ...] = (("uv", "sync"),)
PYTEST_COMMAND: tuple[str, ...] = ("uv", "run", "pytest")

PASSED = "통과"
FAILED = "실패"
ERROR = "오류"
SKIPPED = "건너뜀"
_SEVERITY = {PASSED: 0, SKIPPED: 1, FAILED: 2, ERROR: 3}

NAME = "이름"
STRING = "문자열"

_NAME_ERRORS = ("AttributeError", "NameError", "TypeError")
_ORDINALS = ("첫째", "둘째")
_NO_RESULT = "결과 없음"


class CandidateError(Exception):
    """후보 하나를 가르지 못했다. 그 후보의 실패 갈래다."""


# --- 바뀐 시험 ---


@dataclass(frozen=True)
class ChangedTest:
    """M이 바꾼 시험 함수 하나와 그 본문의 이름과 문자열."""

    file: str
    name: str  # `test_a` 또는 `TestC::test_m`
    names: tuple[str, ...]
    strings: tuple[str, ...]

    @property
    def selector(self) -> str:
        """pytest에 넘기는 함수의 노드 ID. 매개변수화한 경우를 모두 고른다."""
        return f"{self.file}::{self.name}"


type _Def = ast.FunctionDef | ast.AsyncFunctionDef


def _is_test_def(node: _Def) -> bool:
    return node.name.startswith("test_")


def _test_defs(tree: ast.Module) -> dict[str, _Def]:
    """모듈의 시험 함수."""
    out: dict[str, _Def] = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and _is_test_def(node):
            out[node.name] = node
        elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
            for item in node.body:
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef) and _is_test_def(item):
                    out[f"{node.name}::{item.name}"] = item
    return out


def _parse(source: str) -> ast.Module | None:
    """앞의 BOM은 벗기고 푼다. 풀리지 않으면 `None`이다."""
    try:
        return ast.parse(source.removeprefix(chr(0xFEFF)))
    except (SyntaxError, ValueError):
        return None


def _body_terms(node: _Def) -> tuple[tuple[str, ...], tuple[str, ...]]:
    names: set[str] = set()
    strings: set[str] = set()
    for statement in node.body:
        for sub in ast.walk(statement):
            if isinstance(sub, ast.Name):
                names.add(sub.id)
            elif isinstance(sub, ast.Attribute):
                names.add(sub.attr)
            elif isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                lines = sub.value.split("\n")
                pieces = (piece for line in lines for piece in line.split("\0"))
                strings.update(piece for piece in pieces if len(piece) >= 2)
    return tuple(sorted(names)), tuple(sorted(strings))


def changed_tests(base: Mapping[str, str], merge: Mapping[str, str]) -> tuple[ChangedTest, ...]:
    """M의 시험 파일(`merge`, 경로 → 소스) 가운데 B(`base`)에 없거나 정의가 다른 시험 함수.

    파일은 경로 차례, 함수는 정의 차례다. B에 없거나 B에서 풀리지 않는 파일의 시험은 모두
    새것이다. M에서 풀리지 않는 파일은 그 안의 바뀐 시험을 셀 수 없어 `CandidateError`다.
    """
    out: list[ChangedTest] = []
    for file in sorted(merge):
        tree = _parse(merge[file])
        if tree is None:
            raise CandidateError(f"M 의 시험 파일을 풀지 못했다: {file}")
        before_tree = _parse(base.get(file, ""))
        old = {} if before_tree is None else _test_defs(before_tree)
        for name, node in _test_defs(tree).items():
            before = old.get(name)
            if before is not None and ast.dump(before) == ast.dump(node):
                continue
            names, strings = _body_terms(node)
            out.append(ChangedTest(file=file, name=name, names=names, strings=strings))
    return tuple(out)


# --- junit ---


@dataclass(frozen=True)
class Outcome:
    """노드 하나의 결과. `message`는 실패·오류·건너뜀 요소의 `message` 속성이다."""

    kind: str  # PASSED, FAILED, ERROR, SKIPPED
    message: str


def _classname(test: ChangedTest) -> str:
    """pytest junit의 `classname`. 노드 ID의 파일 부분에서 `/`를 `.`로, 끝의 `.py`를 뺀 것이다."""
    module = test.file.removesuffix(".py").replace("/", ".")
    owner, sep, _ = test.name.rpartition("::")
    return f"{module}.{owner}" if sep else module


def _case_outcome(case: ElementTree.Element) -> Outcome:
    worst = Outcome(PASSED, "")
    for child in case:
        kind = {"error": ERROR, "failure": FAILED, "skipped": SKIPPED}.get(child.tag)
        if kind is not None and _SEVERITY[kind] > _SEVERITY[worst.kind]:
            worst = Outcome(kind, child.get("message", ""))
    return worst


def read_junit(text: str, tests: Sequence[ChangedTest]) -> dict[str, Outcome]:
    """junit xml을 바뀐 시험의 노드 ID마다의 결과로 푼다. 바뀐 시험이 아닌 `testcase`는 버린다.

    같은 노드의 `testcase`가 둘이면(통과한 뒤 정리에서 난 오류) 나쁜 쪽을 든다.
    """
    try:
        root = ElementTree.fromstring(text)
    except ElementTree.ParseError as error:
        raise CandidateError(f"junit xml 을 풀지 못했다: {error}") from error
    by_class: dict[str, list[ChangedTest]] = {}
    for test in tests:
        by_class.setdefault(_classname(test), []).append(test)
    out: dict[str, Outcome] = {}
    for case in root.iter("testcase"):
        name = case.get("name", "")
        function = name.partition("[")[0]
        for test in by_class.get(case.get("classname", ""), []):
            if test.name.rpartition("::")[2] != function:
                continue
            node = f"{test.selector}{name[len(function) :]}"
            got = _case_outcome(case)
            before = out.get(node)
            if before is None or _SEVERITY[got.kind] > _SEVERITY[before.kind]:
                out[node] = got
            break
    return out


# --- 세 조건 ---


@dataclass(frozen=True)
class Term:
    """시험 본문의 이름이나 문자열 하나. `in_merge`는 M의 `tests/` 밖 추적 파일에 있는지,
    `in_base`는 B의 추적 파일 어디에 있는지다."""

    kind: str  # NAME, STRING
    text: str
    in_merge: bool
    in_base: bool


@dataclass(frozen=True)
class NodeFacts:
    """노드 하나를 가르는 데 드는 값. 결과가 없으면(모으지 못했다) None이다."""

    node_id: str
    merge_runs: tuple[Outcome | None, Outcome | None]
    base_run: Outcome | None
    terms: tuple[Term, ...]  # 그 노드의 함수 본문의 이름과 문자열


@dataclass(frozen=True)
class Dropped:
    node_id: str
    condition: int  # 1, 2, 3
    cause: str  # 실패 종류나 이름


@dataclass(frozen=True)
class Sorted:
    kept: tuple[str, ...]
    dropped: tuple[Dropped, ...]


def _why(node: NodeFacts) -> tuple[int, str] | None:
    for ordinal, run in zip(_ORDINALS, node.merge_runs, strict=True):
        if run is None or run.kind != PASSED:
            return 1, f"M {ordinal} 실행: {_NO_RESULT if run is None else run.kind}"
    base = node.base_run
    if base is None:
        return 2, f"{_NO_RESULT}(모음 실패)"
    if base.kind != FAILED:
        return 2, base.kind
    for prefix in _NAME_ERRORS:
        if base.message.startswith(prefix):
            return 2, prefix
    for term in node.terms:
        if term.in_merge and not term.in_base:
            return 3, f"{term.kind} {term.text!r}"
    return None


type Runs = Mapping[str, Outcome]


def node_facts(
    terms: Mapping[str, tuple[Term, ...]], merge_runs: tuple[Runs, Runs], base_run: Runs
) -> list[NodeFacts]:
    """세 실행의 결과(노드 ID → 결과)에서 가를 노드를 짓는다. `terms`는 바뀐 시험의 함수 노드
    ID마다의 이름과 문자열이다.

    노드는 M 두 실행에 나온 차례다. M 어디에도 결과가 없는 바뀐 시험(마커로 빠졌거나 M에서 모으지
    못했다)은 그 함수 노드 ID로 넣어, 조건 1의 "결과 없음"으로 빠진 까닭이 남게 한다.
    """
    nodes = list(dict.fromkeys([*merge_runs[0], *merge_runs[1]]))
    seen = {node.partition("[")[0] for node in nodes}
    nodes += [selector for selector in terms if selector not in seen]
    return [
        NodeFacts(
            node_id=node,
            merge_runs=(merge_runs[0].get(node), merge_runs[1].get(node)),
            base_run=base_run.get(node),
            terms=terms[node.partition("[")[0]],
        )
        for node in nodes
    ]


def sort_nodes(nodes: Sequence[NodeFacts]) -> Sorted:
    """세 조건을 차례로 본다. 남은 노드와 빠진 노드는 받은 차례다."""
    kept: list[str] = []
    dropped: list[Dropped] = []
    for node in nodes:
        why = _why(node)
        if why is None:
            kept.append(node.node_id)
        else:
            dropped.append(Dropped(node.node_id, *why))
    return Sorted(kept=tuple(kept), dropped=tuple(dropped))


# --- 바깥 층 ---


@dataclass(frozen=True)
class Limits:
    """하위 프로세스 하나의 시간 제한(초)."""

    git: float = 60.0
    worktree: float = 300.0  # 작업 트리 하나를 꺼내거나 걷기
    setup: float = 900.0  # 준비 명령 하나(`uv sync`는 `.venv`를 복사로 채워 2분을 넘길 수 있다)
    pytest: float = 900.0


@dataclass(frozen=True)
class Hidden:
    """후보 하나를 가른 결과."""

    hidden_tests: tuple[str, ...]
    support_files: tuple[str, ...]
    dropped: tuple[Dropped, ...]


@dataclass(frozen=True)
class Failure:
    """후보 하나를 가르지 못했다(시간 넘김, 준비 실패, git 실패 등)."""

    reason: str


_GIT = shutil.which("git") or "git"


def _env() -> dict[str, str]:
    """자식 환경. 저장소를 가리키는 변수와, 러너의 가상 환경을 가리키는 `VIRTUAL_ENV`를 벗긴다."""
    drop = {*REPO_LOCATION_VARS, "VIRTUAL_ENV"}
    return {key: value for key, value in os.environ.items() if key not in drop}


def _text(data: bytes) -> str:
    return data.decode("utf-8", errors="replace")


def _last_line(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[-1][:300] if lines else "출력 없음"


def _git_name(args: Sequence[str]) -> str:
    """알림에 쓰는 git 명령 이름. 앞의 `-c <설정>`을 건너뛰고 하위 명령과 그 다음 낱말을 든다."""
    rest = list(args)
    while rest[:1] == ["-c"]:
        rest = rest[2:]
    return " ".join(["git", *rest[:2]])


def _git(repo: Path, args: Sequence[str], timeout: float) -> subprocess.CompletedProcess[bytes]:
    what = _git_name(args)
    try:
        return subprocess.run(
            [_GIT, "-C", str(repo), *args],
            capture_output=True,
            check=False,
            timeout=timeout,
            env=_env(),
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired as error:
        raise CandidateError(f"{what} 가 시간 제한({timeout:g}초)을 넘겼다") from error
    except (OSError, ValueError) as error:
        raise CandidateError(f"{what} 를 띄우지 못했다: {error}") from error


def _git_ok(repo: Path, args: Sequence[str], timeout: float) -> bytes:
    done = _git(repo, args, timeout)
    if done.returncode != 0:
        stderr = _last_line(_text(done.stderr))
        raise CandidateError(f"{_git_name(args)} 가 {done.returncode}로 끝났다: {stderr}")
    return done.stdout


def term_in(
    repo: Path, rev: str, kind: str, text: str, *, outside_tests: bool, limits: Limits
) -> bool:
    """`rev`의 추적 파일에 `text`가 있는지. 이름은 낱말 경계로, 문자열은 고정 문자열로 찾는다.

    `outside_tests`면 저장소 뿌리의 `tests/` 아래는 보지 않는다. `git grep`이 0과 1 밖으로 끝나면
    `CandidateError`다.
    """
    args = ["grep", "-q", "-F", *(["-w"] if kind == NAME else []), "-e", text, rev]
    if outside_tests:
        args += ["--", ":(top,exclude)tests"]
    done = _git(repo, args, limits.git)
    if done.returncode in (0, 1):
        return done.returncode == 0
    raise CandidateError(
        f"git grep 이 {done.returncode}로 끝났다({kind} {text!r}, {rev}): "
        f"{_last_line(_text(done.stderr))}"
    )


def overlay_target(root: Path, rel: str) -> Path | None:
    """작업 트리 `root`에 덮을 `rel`(`/`로 가른 상대 경로)의 자리. 상위 폴더나 그 자리가 링크면
    None이다. 링크를 지나 쓰면 작업 트리 바깥에 쓸 수 있다."""
    current = root
    for part in rel.split("/"):
        current = current / part
        if current.is_symlink() or current.is_junction():
            return None
    return current


def _kill_tree(process: subprocess.Popen[bytes]) -> None:
    """시간을 넘긴 자식과 그 아래 프로세스를 끈다. 아직 거두지 않은 자식이라 pid가 다른 프로세스에
    넘어가지 않았다."""
    if sys.platform == "win32":
        with suppress(OSError, subprocess.TimeoutExpired):
            subprocess.run(
                ["taskkill", "/T", "/F", "/PID", str(process.pid)],
                capture_output=True,
                check=False,
                timeout=30,
            )
    else:
        with suppress(OSError):
            os.killpg(process.pid, signal.SIGKILL)
    with suppress(OSError):
        process.kill()
    with suppress(subprocess.TimeoutExpired):
        process.wait(timeout=30)


def _run(args: Sequence[str], cwd: Path, log: Path, timeout: float, what: str) -> int:
    """`args`를 `cwd`에서 띄우고 출력을 `log`에 덧붙인다. 파이프를 쓰지 않아, 손자가 출력을 쥐어도
    기다림이 시간 제한을 넘기지 않는다."""
    with log.open("ab") as sink:
        try:
            process = subprocess.Popen(
                list(args),
                cwd=cwd,
                env=_env(),
                stdin=subprocess.DEVNULL,
                stdout=sink,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except (OSError, ValueError) as error:
            raise CandidateError(f"{what} 를 띄우지 못했다: {error}") from error
        try:
            return process.wait(timeout=timeout)
        except subprocess.TimeoutExpired as error:
            _kill_tree(process)
            raise CandidateError(f"{what} 가 시간 제한({timeout:g}초)을 넘겼다") from error


def _log_tail(log: Path) -> str:
    try:
        return _last_line(_text(log.read_bytes()))
    except OSError:
        return "로그를 읽지 못했다"


def _cut_links(folder: Path) -> list[str]:
    """`folder` 아래의 링크를 링크만 끊는다. 끊지 못한 링크와 읽지 못한 폴더를 준다.

    `tools/canary.py`의 `_cut_links`와 같은 길이다. 윈도의 junction도 `os.unlink`가 링크만 지운다.
    """
    left: list[str] = []
    pending = [folder]
    while pending:
        current = pending.pop()
        try:
            entries = list(os.scandir(current))
        except OSError:
            left.append(str(current))
            continue
        for entry in entries:
            if entry.is_symlink() or entry.is_junction():
                try:
                    os.unlink(entry.path)
                except OSError:
                    left.append(entry.path)
            elif entry.is_dir(follow_symlinks=False):
                pending.append(Path(entry.path))
    return left


class _Registration(Enum):
    """작업 트리 자리의 git 등록. 목록을 읽지 못하면 `UNKNOWN`이다."""

    LISTED = "listed"
    GONE = "gone"
    UNKNOWN = "unknown"


def _registration(repo: Path, place: Path, limits: Limits) -> _Registration:
    """`place`가 아직 git 작업 트리로 등록돼 있는지."""
    try:
        done = _git(repo, ["worktree", "list", "--porcelain"], limits.worktree)
    except CandidateError:
        return _Registration.UNKNOWN
    if done.returncode != 0:
        return _Registration.UNKNOWN
    key = os.path.normcase(os.path.realpath(place))
    for line in _text(done.stdout).splitlines():
        if line.startswith("worktree "):
            listed = os.path.normcase(os.path.realpath(line.removeprefix("worktree ")))
            if listed == key:
                return _Registration.LISTED
    return _Registration.GONE


def _remove_checkout(repo: Path, place: Path, limits: Limits, out: Callable[[str], None]) -> None:
    """꺼낸 작업 트리를 걷는다. 링크를 먼저 끊고, 끊지 못하면 걷지 않고 알린다."""
    if place.exists():
        left = _cut_links(place)
        if left:
            out(
                f"작업 트리를 걷지 않았다: {place}. 안의 링크를 끊지 못해 git 이 그 링크를 따라가 "
                f"바깥을 지울 수 있다: {', '.join(left[:3])}. 그 링크를 링크만 지운 뒤 "
                f"git worktree remove --force {place} 로 걷는다"
            )
            return
    reason = ""
    # 시간을 넘겨 죽은 꺼내기는 잠금을 남겼을 수 있어 --force 를 두 번 준다
    args = ["-c", "core.longpaths=true", "worktree", "remove", "--force", "--force", str(place)]
    try:
        done = _git(repo, args, limits.worktree)
        if done.returncode != 0:
            reason = _last_line(_text(done.stderr))
    except CandidateError as error:
        reason = str(error)
    if place.exists() or _registration(repo, place, limits) is not _Registration.GONE:
        why = reason or "git 은 걷었다고 했지만 남았다"
        out(
            f"작업 트리를 다 걷지 못했다: {place}({why}). 그 자리를 쥔 프로세스가 끝난 뒤 "
            f"git worktree remove --force {place} 로 걷는다(등록이 없으면 폴더만 지운다)"
        )


@contextmanager
def _checkout(
    repo: Path, sha: str, place: Path, limits: Limits, out: Callable[[str], None]
) -> Generator[Path]:
    """`sha`를 `place`에 분리 HEAD 작업 트리로 꺼내고, 끝나면 어느 길에서도 걷는다."""
    try:
        args = ["-c", "core.longpaths=true", "worktree", "add", "--detach", str(place), sha]
        _git_ok(repo, args, limits.worktree)
        yield place
    finally:
        if place.exists() or _registration(repo, place, limits) is not _Registration.GONE:
            _remove_checkout(repo, place, limits, out)


def _commit(repo: Path, rev: str, limits: Limits) -> str:
    done = _git(repo, ["rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}"], limits.git)
    if done.returncode != 0:
        raise CandidateError(f"커밋 {rev} 을 {repo} 의 저장소에서 찾지 못했다")
    return _text(done.stdout).strip()


def _blob(repo: Path, sha: str, path: str, limits: Limits) -> bytes:
    return _git_ok(repo, ["cat-file", "blob", f"{sha}:{path}"], limits.git)


def _terms(
    repo: Path, base: str, merge: str, test: ChangedTest, limits: Limits, cache: dict[str, Term]
) -> tuple[Term, ...]:
    """시험 본문의 이름과 문자열마다 M의 `tests/` 밖과 B에 있는지. M에 없으면 B는 찾지 않는다."""
    out: list[Term] = []
    for kind, texts in ((NAME, test.names), (STRING, test.strings)):
        for text in texts:
            key = f"{kind}\0{text}"
            if key not in cache:
                in_merge = term_in(repo, merge, kind, text, outside_tests=True, limits=limits)
                in_base = in_merge and term_in(
                    repo, base, kind, text, outside_tests=False, limits=limits
                )
                cache[key] = Term(kind=kind, text=text, in_merge=in_merge, in_base=in_base)
            out.append(cache[key])
    return tuple(out)


@dataclass(frozen=True)
class _Plan:
    tests: tuple[ChangedTest, ...]
    test_files: tuple[str, ...]
    support_files: tuple[str, ...]


def _plan(repo: Path, base: str, merge: str, limits: Limits) -> _Plan:
    """M이 바꾼 시험 파일과 지원 파일, 바뀐 시험 함수."""
    diff = _git_ok(
        repo,
        ["diff", "--no-renames", "--no-ext-diff", "--name-only", "-z", "--diff-filter=d"]
        + [base, merge],
        limits.git,
    )
    paths = [p for p in _text(diff).split("\0") if p]
    test_files = tuple(p for p in paths if is_test_file(p))
    support = tuple(p for p in paths if is_support_file(p))
    merge_sources = {f: _text(_blob(repo, merge, f, limits)) for f in test_files}
    base_sources: dict[str, str] = {}
    if test_files:
        listed = _git_ok(
            repo, ["ls-tree", "-r", "-z", "--name-only", base, "--", *test_files], limits.git
        )
        for f in _text(listed).split("\0"):
            if f in merge_sources:
                base_sources[f] = _text(_blob(repo, base, f, limits))
    tests = changed_tests(base_sources, merge_sources)
    return _Plan(tests=tests, test_files=test_files, support_files=support)


def _setup(worktree: Path, setup: Sequence[Sequence[str]], log: Path, limits: Limits) -> None:
    for command in setup:
        shown = " ".join(command)
        code = _run(command, worktree, log, limits.setup, f"준비 `{shown}`")
        if code != 0:
            raise CandidateError(f"준비 `{shown}` 가 {code}로 끝났다({worktree}): {_log_tail(log)}")


def _pytest(
    worktree: Path,
    pytest: Sequence[str],
    tests: Sequence[ChangedTest],
    xml: Path,
    log: Path,
    limits: Limits,
) -> dict[str, Outcome]:
    args = [
        *pytest,
        "--rootdir=.",
        "-p",
        "no:cacheprovider",
        "-o",
        "junit_family=xunit2",
        f"--junitxml={xml}",
        # 모음 오류가 난 파일이 있어도 다른 파일의 시험은 돈다(조건 2의 그 파일만 빠진다)
        "--continue-on-collection-errors",
        "-q",
        # 노드 ID 가 아니라 파일을 넘긴다. 모으지 못한 파일의 노드 ID 를 받은 pytest 는
        # `found no collectors` 로 실행 전체를 멈췄다(이 모듈의 시험이 B 의 모음 오류로 재현한다).
        # 바뀌지 않은 시험도 돌지만 `read_junit` 이 버린다
        *dict.fromkeys(t.file for t in tests),
    ]
    code = _run(args, worktree, log, limits.pytest, "pytest")
    try:
        text = xml.read_text(encoding="utf-8")
    except OSError as error:
        raise CandidateError(
            f"pytest 가 junit xml 을 남기지 않았다(종료 {code}, {worktree}): {_log_tail(log)}"
        ) from error
    return read_junit(text, tests)


def _overlay(repo: Path, merge: str, worktree: Path, files: Sequence[str], limits: Limits) -> None:
    for rel in files:
        target = overlay_target(worktree, rel)
        if target is None:
            raise CandidateError(f"덮을 자리 {rel} 의 상위나 그 자리가 B 에서 링크다")
        data = _blob(repo, merge, rel, limits)
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        except OSError as error:
            # B 에서 상위 자리가 파일인 경우, 윈도의 긴 경로 등
            raise CandidateError(f"B 의 작업 트리에 덮지 못했다: {rel}: {error}") from error


_M_RUNS = ("m1.xml", "m2.xml")
_B_RUN = "b.xml"
_LOGS = ("m.log", "b.log")


def _sort(
    repo: Path,
    base: str,
    merge: str,
    *,
    setup: Sequence[Sequence[str]],
    pytest: Sequence[str],
    parent: Path,
    limits: Limits,
    out: Callable[[str], None],
) -> Hidden:
    b = _commit(repo, base, limits)
    m = _commit(repo, merge, limits)
    plan = _plan(repo, b, m, limits)
    if not plan.tests:
        return Hidden(hidden_tests=(), support_files=plan.support_files, dropped=())
    cache: dict[str, Term] = {}
    terms = {t.selector: _terms(repo, b, m, t, limits, cache) for t in plan.tests}

    with _checkout(repo, m, parent / "m", limits, out) as worktree:
        _setup(worktree, setup, parent / "m.log", limits)
        merge_runs = [
            _pytest(worktree, pytest, plan.tests, parent / xml, parent / "m.log", limits)
            for xml in _M_RUNS
        ]
    with _checkout(repo, b, parent / "b", limits, out) as worktree:
        _overlay(repo, m, worktree, [*plan.test_files, *plan.support_files], limits)
        _setup(worktree, setup, parent / "b.log", limits)
        base_run = _pytest(worktree, pytest, plan.tests, parent / _B_RUN, parent / "b.log", limits)

    result = sort_nodes(node_facts(terms, (merge_runs[0], merge_runs[1]), base_run))
    return Hidden(
        hidden_tests=result.kept, support_files=plan.support_files, dropped=result.dropped
    )


def _remove_parent(parent: Path, out: Callable[[str], None]) -> None:
    """이 도구가 지은 이름만 지우고 임시 폴더를 걷는다. 다른 것이 남으면 지우지 않고 알린다."""
    for name in (*_M_RUNS, _B_RUN, *_LOGS):
        with suppress(OSError):
            (parent / name).unlink(missing_ok=True)
    try:
        parent.rmdir()
    except OSError:
        out(f"임시 폴더 {parent} 가 남았다{_leftover_names(parent)}. 남은 것을 확인한 뒤 지운다")


def _leftover_names(parent: Path) -> str:
    """남은 이름을 정렬해 다섯까지 보이는 괄호 글. 모두의 수를 앞에 둔다. 읽지 못하면 빈 글이다."""
    left: list[str] = []
    with suppress(OSError):
        left = sorted(p.name for p in parent.iterdir())
    if not left:
        return ""
    more = " …" if len(left) > 5 else ""
    return f"(남은 것 {len(left)}개: {', '.join(left[:5])}{more})"


def sort_candidate(
    repo: Path,
    base: str,
    merge: str,
    *,
    out: Callable[[str], None],
    setup: Sequence[Sequence[str]] = SETUP_COMMANDS,
    pytest: Sequence[str] = PYTEST_COMMAND,
    temp_root: Path | None = None,
    limits: Limits = Limits(),  # noqa: B008  # 얼린 데이터클래스라 공유해도 바뀌지 않는다
) -> Hidden | Failure:
    """후보 하나(B `base`, M `merge`)의 숨은 시험 ID, 시험 지원 파일, 빠진 노드와 그 까닭.

    `repo`는 두 커밋을 담은 저장소다. 작업 트리를 걷지 못하는 등 결과와 별개로 사람이 알아야 할
    일은 `out`으로 알린다. 가르지 못하면 `Failure`다.
    """
    try:
        parent = Path(tempfile.mkdtemp(prefix="rerun-hidden-", dir=temp_root))
    except OSError as error:
        return Failure(f"임시 폴더를 만들지 못했다: {error}")
    try:
        return _sort(
            repo,
            base,
            merge,
            setup=setup,
            pytest=pytest,
            parent=parent,
            limits=limits,
            out=out,
        )
    except CandidateError as error:
        return Failure(str(error))
    finally:
        _remove_parent(parent, out)
