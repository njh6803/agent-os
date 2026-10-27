"""다시 풀기 회차의 게이트와 숨은 시험. 결과 커밋을 클론에서 새 작업 트리로 꺼내 준비한 뒤 게이트를
돌고, 같은 작업 트리에 M의 숨은 시험 파일과 시험 지원 파일을 덮어 숨은 시험의 노드만 돌린다.

명세는 `.scratch/model-rerun/spec.md`의 "게이트와 숨은 시험"과 "클론과 설정 폴더"의 회차 폴더
2026-10-22 주석이고, 티켓은 `.scratch/model-rerun/issues/07-gates-and-official-cost.md`다. 회차의
차례(10)가 끝남인 회차에서 `check_result`를 부르고, 그 결과를 회차 기록(`tools/rerun_files.py`)의
결과 칸에 옮긴다.

차례.
1. 원본 저장소에서 M의 숨은 시험 파일(`hidden_test_files`)과 시험 지원 파일을 `git cat-file`로 먼저
   읽는다. 클론은 B까지라 M이 없다.
2. 회차 폴더의 `gate`에 결과 커밋을 클론의 분리 HEAD 작업 트리(`git worktree add --detach`)로
   꺼낸다. 세션이 일한 클론의 작업 폴더는 쓰지 않아, 커밋하지 않은 변경과 세션이 남긴 파일이 판정에
   들지 않는다(스토리 34).
3. 그 작업 트리에서 04의 준비(`tools/rerun_round.py`의 `run_setup`)를 돈다. 실패하면 게이트와 숨은
   시험을 돌지 않고, 실패한 명령과 끝난 꼴을 `SetupFailure`로 옮긴다(`setup_failure_of`).
4. 받은 게이트를 차례로 돈다. 앞 게이트가 실패해도 다 돈다. 게이트는 대개 셋(`GATE_ARGV`)이고,
   러너는 B 에 게이트 러너가 없는 과제(`has_gate_file`)에 옛 여섯(`OLD_GATE_ARGV`)을 준다. 모두가
   함께 쓰는 몫(`Limits.gates`) 하나를 두고 게이트마다 남은 몫을 시간 제한으로 준다. 넘긴 게이트는
   프로세스 트리째 끄고 시간 넘김으로 적는다. 몫이 남지 않아 돌지 않은 게이트, 찾지 못했거나 띄우지
   못한 게이트, 작업 트리 자리가 링크로 바뀌어 띄우지 않은 게이트는 종료 코드도 시간 넘김도 없다.
   링크인 자리에서 띄우면 결과 커밋이 아니라 그 링크가 가리키는 바깥에서 돈다.
5. 게이트가 모두 0으로 끝났을 때만 숨은 시험을 돈다. 판정(`tools/rerun_judge.py`의 `solved`)이
   게이트 초록을 먼저 요구해, 게이트가 초록이 아닌 회차의 숨은 시험은 판정에 쓰이지 않는다. 노드가
   없는 과제면 돌지 않고 0개로 센다. 노드 없이 띄운 pytest는 결과 커밋의 시험 전체를 돈다. 1에서
   읽은 파일을 작업 트리에 덮는다. 작업 트리 자리나 덮을 자리의 상위 폴더나 그 자리가 링크면
   (`tools/rerun_hidden.py`의 `overlay_target`) 덮지 않고 모든 노드를 실패로 센다. 쓰지 못해도
   같다. 까닭은 숨은 시험 로그에 적는다.
6. 숨은 시험의 노드 ID만 pytest로 돌려 junit xml을 회차 폴더에 남기고 센다(`count_hidden`). 앞선
   xml은 먼저 지운다. 시간을 넘기면 프로세스 트리째 끄고 모든 노드가 실패다.
7. 어느 길에서도(예외 포함) 작업 트리를 걷는다. 작업 트리와 클론의 관리 폴더(`.git/worktrees/`)
   안의 링크(심볼릭 링크, junction)를 먼저 링크만 끊는다(`tools/tidy_checkouts.py`의 `cut_links`).
   git 2.32의 `git worktree remove --force`가 junction을 따라가 바깥 파일까지 지웠고(일지
   2026-10-15-19), 관리 폴더를 지울 때도 그 안의 junction을 따라갔다(이 티켓의 커밋 전 반박 검증에서
   서브에이전트가 임시 저장소로 재현했고, 바깥 파일과 원본 저장소의 `.git`이 지워졌다. 그 스크립트는
   커밋하지 않았고, 이 모듈의 시험이 그 길을 고정한다). 작업 트리 자리나 클론의 `.git`이나 관리
   폴더 자체가 링크이거나 링크를 끊지 못하면, 따라가지 않고 걷지 않은 채 `out`으로 알린다. 그 뒤
   `git worktree remove --force --force`로 걷고, 폴더나 등록이 남으면 알린다. 클론과 원본은 남긴다.
   출력은 회차 폴더의 로그(`gate-git.log`, `gate-setup.log`, `gate.log`, `hidden.log`)에 덧붙인다.

junit의 셈. 노드 ID를 pytest가 junit에 쓰는 꼴(pytest의 `mangle_test_address`)로 옮겨 `classname`과
`name`으로 찾는다. 노드마다 그 `testcase`가 하나라도 있고 모두 통과일 때만 통과다. `failure`·
`error`·`skipped`가 든 것, XML에 없는 것(모음 오류로 그 파일의 `error`만 남은 때), XML이 없거나
UTF-8로 읽히지 않거나 풀리지 않는 것은 실패다. XML은 세션의 코드가 고쳐 쓸 수도 있는 파일이지만
표준 라이브러리 파서로 푼다. 파이썬 문서의 XML 취약점 표(https://docs.python.org/3.12/library/xml.html.
이 티켓은 웹 요약으로 읽었다)는 `ElementTree`가 바깥 엔터티를 풀지 않고 expat 2.4.1부터 엔터티
증폭(billion laughs)이 막힌다고 적는다. 이 PC의 파이썬 3.12.10(expat 2.7.1)에서 그 둘을 이 모듈의
시험이 고정한다.

자식 환경. 준비·게이트·pytest·git은 부르는 쪽이 넘긴 환경(`env`)으로 띄우고, 거기서
`tools.run_hooks.REPO_LOCATION_VARS`와 `VIRTUAL_ENV`를 벗긴다. git에는 `GIT_TERMINAL_PROMPT=0`을
더한다. 결과 커밋과 클론의 `.git`은 세션이 쓴 것이라 그 안의 코드(게이트 스크립트, git 훅과 필터,
`conftest.py`)가 이 환경으로 돈다. 그래서 러너의 전체 환경이 아니라 세션과 같은 허용 목록의 환경
(`tools/rerun_round.py`의 `session_env`)을 넘기는 것이 부르는 쪽의 몫이다. 그 위에 B 설정의
`env`(`settings_env`)를 얹는다. 원래 세션의 pre-commit 은 Claude Code 가 그 값을 넣은 Bash 에서
돌았고, 얹지 않은 파일럿 첫 실행의 게이트는 `PYTHONUTF8` 없이 돌아 빨갰다(일지 2026-10-27-08).
하위 프로세스마다 시간 제한이 있다.

못 보는 것.
- 노드 ID로 돌린 pytest는 한 파일을 모으지 못하면 실행 전체를 종료 4로 멈추고 junit에 그 파일의
  `error`만 남긴다. `--continue-on-collection-errors`를 줘도 같았다(이 PC의 pytest에서 스크래치로
  손으로 봤다. 기본 인자로 돌린 그 동작은 이 모듈의 시험이 고정한다). 그래서 다른 파일의 노드도
  실패로 세어 통과 수가 낮게 나온다. 모두 통과인지의 판정은 같다.
- 결과 커밋의 코드가 판정을 바꾸는 길(게이트 스크립트를 0으로 끝나게 고치기, 모든 시험을 통과시키는
  `conftest.py`나 pytest 설정, junit xml을 고쳐 쓰기)은 막지 않는다. 덮는 것은 M이 바꾼 시험 파일과
  지원 파일뿐이다.
- 작업 트리 자리나 덮을 자리를 본 뒤 명령을 띄우거나 쓰기 전에 다른 프로세스가 그 자리를 링크로
  바꾸는 일은 막지 않는다. 덮기는 준비와 게이트가 끝난 뒤라 이 도구가 띄운 프로세스는 없지만, 그
  프로세스가 떼어 낸 손자는 남을 수 있다. 준비 명령 사이에 자리가 바뀌는 일도 막지 않는다. 04의
  `run_setup`은 명령마다 그 자리를 보지 않는다.
- 걷기의 링크 확인은 결과 커밋의 코드가 일부러 심은 링크까지 막는다(원본 저장소의 `.git`을 지울 수
  있었다). 다만 링크를 끊은 뒤 `git worktree remove`가 지우기 전에, 떼어 낸 손자가 새 링크를 심는
  일은 막지 않는다.
- 프로세스 트리를 끄는 길은 그 트리를 떠난 손자(새 세션이나 그룹으로 떼어 낸 것)를 끄지 못한다.
  준비 명령이 시간을 넘기면 그 명령의 프로세스만 끈다(04의 `run_setup`). 남은 프로세스가 작업
  트리를 쥐면 걷지 못하고 알린다.
- 결과 커밋을 꺼내지 못한 것(`git worktree add`의 실패)은 세션의 커밋 때문일 수도 있다(윈도에서 쓸
  수 없는 이름, 세션이 바꾼 필터). 이 도구는 가르지 않고 `GateError`로 올린다.
"""

from __future__ import annotations

import enum
import json
import os
import re
import shutil
import subprocess
import time
import xml.etree.ElementTree as ElementTree
from collections.abc import Callable, Generator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import IO

from tools.rerun_files import (
    GATE_COMMANDS,
    GATE_FILE,
    OLD_GATE_COMMANDS,
    Gate,
    Hidden,
    SetupFailure,
    Task,
    hidden_test_files,
)
from tools.rerun_hidden import kill_tree, overlay_target
from tools.rerun_round import (
    GIT_TIMEOUT,
    SETUP_ARGV,
    SETUP_TIMEOUT,
    RoundDir,
    SetupEnd,
    SetupFailed,
    run_setup,
)
from tools.run_hooks import REPO_LOCATION_VARS
from tools.tidy_checkouts import cut_links

# 게이트의 인자 목록. 명세 "게이트와 숨은 시험"의 셋이고 글은 `tools/rerun_files.py`의
# `GATE_COMMANDS`다.
GATE_ARGV: tuple[tuple[str, ...], ...] = tuple(tuple(c.split(" ")) for c in GATE_COMMANDS)
# B 에 게이트 러너(`GATE_FILE`)가 없는 과제의 게이트. 글은 `OLD_GATE_COMMANDS`다.
OLD_GATE_ARGV: tuple[tuple[str, ...], ...] = tuple(tuple(c.split(" ")) for c in OLD_GATE_COMMANDS)
# 숨은 시험의 pytest. 러너 체크아웃의 `.venv`는 `agent_os`를 러너의 `src/`에 묶어, 그 파이썬으로
# 돌면 덮은 시험이 러너의 코드로 돈다(`tools/rerun_hidden.py`의 모듈 독스트링).
PYTEST_ARGV = ("uv", "run", "pytest")

_COMMIT = re.compile(r"[0-9a-f]{40}")
type Json = dict[str, Json] | list[Json] | str | int | float | bool | None
_DROPPED_ENV = frozenset({*REPO_LOCATION_VARS, "VIRTUAL_ENV"})
_BAD_CHILDREN = frozenset({"failure", "error", "skipped"})

_WORKTREE = "gate"
_GIT_LOG = "gate-git.log"
_SETUP_LOG = "gate-setup.log"
_GATE_LOG = "gate.log"
_HIDDEN_LOG = "hidden.log"
_HIDDEN_XML = "hidden.xml"


@dataclass(frozen=True)
class Limits:
    """시간 제한(초)."""

    setup: float = SETUP_TIMEOUT  # 준비 명령 하나
    gates: float = 1800.0  # 게이트가 모두 함께 쓰는 몫(명세 "게이트와 숨은 시험")
    hidden: float = 600.0  # 숨은 시험의 pytest(같은 절)
    git: float = GIT_TIMEOUT  # git 하나


class GateError(RuntimeError):
    """결과 작업 트리를 짓지 못했다(원본에서 M의 파일을 읽지 못함, 결과 커밋을 꺼내지 못함 등)."""


@dataclass(frozen=True)
class Checked:
    """회차 기록의 결과 칸 셋. 준비가 실패하면 게이트와 숨은 시험은 빈 값이다."""

    setup_failure: SetupFailure | None
    gates: tuple[Gate, ...] | None
    hidden: Hidden | None


def setup_failure_of(failed: SetupFailed) -> SetupFailure:
    """04의 준비 실패를 회차 기록의 꼴로 옮긴다. 끝난 꼴 셋을 종료 코드와 시간 넘김 두 칸으로
    가른다. 종료 코드는 끝까지 돈 명령에만 있다(`SetupFailed`가 지킨다)."""
    return SetupFailure(
        command=failed.command,
        exit_code=failed.exit_code,
        timed_out=failed.end is SetupEnd.TIMED_OUT,
    )


# --- junit 셈 ---


def _junit_key(node: str) -> tuple[str, str]:
    """노드 ID를 pytest junit의 (`classname`, `name`)으로 옮긴다. pytest의 `mangle_test_address`와
    같다. `[` 앞에서 먼저 잘라, 매개변수에 든 `::`·`/`·`.`는 건드리지 않는다."""
    path, bracket, params = node.partition("[")
    names = path.split("::")
    names[0] = re.sub(r"\.py$", "", names[0].replace("/", "."))
    names[-1] += bracket + params
    return ".".join(names[:-1]), names[-1]


def count_hidden(text: str | None, nodes: Sequence[str]) -> Hidden:
    """junit xml `text`에서 숨은 시험의 노드 `nodes`를 센다. 실패한 노드는 `nodes`의 차례다.

    노드의 `testcase`가 하나라도 있고 모두 통과일 때만 통과다. 같은 노드의 `testcase`가
    둘이면(통과한 뒤 정리에서 난 오류) 나쁜 쪽을 든다. `text`가 빈 값이거나 풀리지 않으면 모든
    노드가 실패다. `nodes`에 겹친 노드는 한 번만 센다. 회차 기록 읽기가 겹친 실패 노드를 거부한다.
    """
    nodes = tuple(dict.fromkeys(nodes))
    passed_keys: dict[tuple[str, str], bool] = {}
    root = None
    if text:
        try:
            root = ElementTree.fromstring(text)
        except ElementTree.ParseError:
            root = None
    if root is not None:
        for case in root.iter("testcase"):
            key = (case.get("classname", ""), case.get("name", ""))
            clean = not any(child.tag in _BAD_CHILDREN for child in case)
            passed_keys[key] = passed_keys.get(key, True) and clean
    failed = tuple(n for n in nodes if not passed_keys.get(_junit_key(n), False))
    return Hidden(passed=len(nodes) - len(failed), total=len(nodes), failed=failed)


# --- 하위 프로세스 ---


def _clean_env(env: Mapping[str, str]) -> dict[str, str]:
    return {k: v for k, v in env.items() if k not in _DROPPED_ENV}


def _last_line(data: bytes) -> str:
    lines = [line.strip() for line in data.decode("utf-8", "replace").splitlines() if line.strip()]
    return lines[-1][:300] if lines else "출력 없음"


def _is_link(path: Path) -> bool:
    return os.path.islink(path) or os.path.isjunction(path)


def _not_started(exe: str | None, cwd: Path, timeout: float) -> str | None:
    """띄우지 않을 까닭. 없으면 빈 값이다."""
    if exe is None:
        return "찾지 못했다"
    if timeout <= 0:
        return "남은 시간이 없어 돌지 않았다"
    if _is_link(cwd):
        return f"작업 트리 자리가 링크라 돌지 않았다: {cwd}"
    return None


def _run(
    argv: Sequence[str], cwd: Path, env: Mapping[str, str], log: Path, timeout: float
) -> tuple[int | None, bool]:
    """`argv`를 `cwd`에서 띄우고 출력을 `log`에 덧붙인다. (종료 코드, 시간 넘김)을 준다.

    찾지 못했거나 띄우지 못했거나 남은 시간이 없거나 `cwd`가 링크면 (빈 값, 거짓)이다. 링크인
    `cwd`에서 띄우면 결과 커밋이 아닌 바깥에서 돈다. 시간을 넘기면 프로세스 트리째 끄고 (빈 값,
    참)이다. 파이프를 쓰지 않아 손자가 출력을 쥐어도 기다림이 시간 제한을 넘기지 않는다
    (`.claude/rules/tools.md`의 시간 제한 항목).
    """
    with log.open("ab") as sink:
        sink.write(f"$ {' '.join(argv)}\n".encode())
        sink.flush()
        exe = shutil.which(argv[0], path=env.get("PATH"))
        why = _not_started(exe, cwd, timeout)
        if exe is None or why is not None:
            sink.write(f"({why})\n".encode())
            return None, False
        try:
            process = subprocess.Popen(
                [exe, *argv[1:]],
                cwd=cwd,
                env=dict(env),
                stdin=subprocess.DEVNULL,
                stdout=sink,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )
        except (OSError, ValueError) as error:
            sink.write(f"(띄우지 못했다: {error})\n".encode())
            return None, False
        try:
            return process.wait(timeout=timeout), False
        except subprocess.TimeoutExpired:
            kill_tree(process)
            sink.write(f"(시간 제한 {timeout:g}초를 넘겨 껐다)\n".encode())
            return None, True


class Registration(enum.Enum):
    """게이트 작업 트리 자리가 클론의 작업 트리 목록에 있는지."""

    LISTED = "listed"
    ABSENT = "absent"
    UNKNOWN = "unknown"  # 목록을 읽지 못했다


@dataclass(frozen=True)
class _Git:
    """git 하나를 띄우는 자리. 실행 파일과 환경과 시간 제한을 묶는다."""

    exe: str
    env: Mapping[str, str]
    timeout: float

    def read(self, repo: Path, args: Sequence[str]) -> bytes:
        """출력이 필요한 git 하나. 손자를 띄우지 않는 명령(`cat-file`, `worktree list`)만 쓴다.
        0이 아니게 끝나거나 띄우지 못하거나 시간을 넘기면 `GateError`다."""
        what = f"git {' '.join(args)}"
        done = self._call(repo, args, what, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if done.returncode != 0:
            raise GateError(f"{what} 가 {done.returncode}로 끝났다: {_last_line(done.stderr)}")
        return done.stdout

    def logged(self, repo: Path, args: Sequence[str], what: str, log: Path) -> None:
        """출력이 필요 없는 git 하나. 출력은 `log`에 덧붙인다. 0이 아니게 끝나거나 띄우지 못하거나
        시간을 넘기면 `GateError`다. 훅과 필터가 띄운 손자가 파이프를 쥐는 일이 없게 파이프를 쓰지
        않는다."""
        with log.open("ab") as sink:
            sink.write(f"$ git {' '.join(args)}\n".encode())
            sink.flush()
            done = self._call(repo, args, what, stdout=sink, stderr=subprocess.STDOUT)
        if done.returncode != 0:
            raise GateError(f"{what} 가 {done.returncode}로 끝났다(출력은 {log})")

    def _call(
        self, repo: Path, args: Sequence[str], what: str, *, stdout: int | IO[bytes], stderr: int
    ) -> subprocess.CompletedProcess[bytes]:
        """git 하나를 띄워 끝나기를 기다린다. 띄우지 못하거나 시간을 넘기면 `GateError`다."""
        try:
            return subprocess.run(
                [self.exe, "-C", str(repo), *args],
                env=dict(self.env),
                stdin=subprocess.DEVNULL,
                stdout=stdout,
                stderr=stderr,
                check=False,
                timeout=self.timeout,
            )
        except subprocess.TimeoutExpired as error:
            raise GateError(f"{what} 가 시간 제한({self.timeout:g}초)을 넘겼다") from error
        except (OSError, ValueError) as error:
            raise GateError(f"{what} 를 띄우지 못했다: {error}") from error

    def registration(self, clone: Path, place: Path) -> Registration:
        """`place`가 `clone`의 작업 트리로 등록돼 있는지."""
        try:
            out = self.read(clone, ["worktree", "list", "--porcelain"])
        except GateError:
            return Registration.UNKNOWN
        key = os.path.normcase(os.path.realpath(place))
        for line in out.decode("utf-8", "replace").splitlines():
            if line.startswith("worktree "):
                path = line.removeprefix("worktree ")
                if os.path.normcase(os.path.realpath(path)) == key:
                    return Registration.LISTED
        return Registration.ABSENT


def _git_of(env: Mapping[str, str], timeout: float) -> tuple[dict[str, str], _Git]:
    """넘긴 환경에서 저장소 변수를 벗긴 환경과 그 PATH 의 git. git 이 없으면 `GateError`다."""
    clean = _clean_env(env)
    exe = shutil.which("git", path=clean.get("PATH"))
    if exe is None:
        raise GateError("넘긴 환경의 PATH 에서 git 을 찾지 못했다")
    return clean, _Git(exe, {**clean, "GIT_TERMINAL_PROMPT": "0"}, timeout)


def _is_blob_at(line: str, rel: str) -> bool:
    """`git ls-tree`의 한 줄(`<모드> <형> <해시>\\t<경로>`)이 `rel`의 blob 인지. 폴더는 tree 다."""
    head, _, path = line.partition("\t")
    return head.split(" ")[1:2] == ["blob"] and path == rel


SETTINGS_FILE = ".claude/settings.json"


def settings_env(
    source: Path, base: str, env: Mapping[str, str], *, timeout: float = GIT_TIMEOUT
) -> dict[str, str]:
    """원본 저장소 `source`의 커밋 `base`(과제의 B)에 든 `SETTINGS_FILE`의 `env` 가운데 값이 글인
    것.

    원래 세션의 pre-commit 은 Claude Code 가 이 값을 넣은 Bash 에서 돌았으므로 게이트도 이 값으로
    돈다. 결과 커밋이 아니라 B 에서 읽어 세션이 설정을 고쳐도 같다. 파일이 없거나 `env`가 객체가
    아니면 빈 값이다. `base`가 40자 커밋 해시가 아니거나 git 이 실패하거나 JSON 으로 풀리지 않으면
    `GateError`다.
    """
    git, found_file = _blob_in_base(source, base, SETTINGS_FILE, env, timeout)
    if not found_file:
        return {}
    raw = git.read(source, ["cat-file", "blob", f"{base}:{SETTINGS_FILE}"])
    try:
        data = _parse_json(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError) as e:
        raise GateError(f"B 의 {SETTINGS_FILE} 를 풀지 못했다: {e}") from e
    found = data.get("env") if isinstance(data, dict) else None
    if not isinstance(found, dict):
        return {}
    return {k: v for k, v in found.items() if isinstance(v, str)}


def _parse_json(text: str) -> Json:
    # `json.loads`의 반환형은 Any라 `Json`으로 받아 뒤의 좁히기가 타입 검사를 지나게 한다.
    return json.loads(text)


def has_gate_file(
    source: Path, base: str, env: Mapping[str, str], *, timeout: float = GIT_TIMEOUT
) -> bool:
    """원본 저장소 `source`의 커밋 `base`(과제의 B)에 게이트 러너(`GATE_FILE`) 파일이 있는지.

    러너가 어느 게이트 묶음을 돌지 가른다. 결과 커밋이 아니라 B 로 가르므로, 세션이 그 파일을
    지우거나 더해도 묶음은 바뀌지 않는다. 같은 이름의 폴더는 파일이 아니다. 같은 이름의 심볼릭
    링크는 형이 blob 이라 파일로 센다. `base`가 40자 커밋 해시가 아니거나 git 이 실패하면
    `GateError`다.
    """
    return _blob_in_base(source, base, GATE_FILE, env, timeout)[1]


def _blob_in_base(
    source: Path, base: str, rel: str, env: Mapping[str, str], timeout: float
) -> tuple[_Git, bool]:
    """넘긴 환경의 git 과, 원본 저장소 `source`의 커밋 `base`에 `rel`의 blob 이 있는지.
    `base`가 40자 커밋 해시가 아니거나 git 이 실패하면 `GateError`다."""
    if not _COMMIT.fullmatch(base):
        raise GateError(f"B 가 40자 커밋 해시가 아니다: {base!r}")
    _, git = _git_of(env, timeout)
    out = git.read(source, ["ls-tree", base, "--", rel]).decode("utf-8", "replace")
    return git, any(_is_blob_at(line, rel) for line in out.splitlines())


# --- 한 회차 ---


def _gates(
    worktree: Path, gates: Sequence[Sequence[str]], env: Mapping[str, str], log: Path, budget: float
) -> tuple[Gate, ...]:
    """게이트를 차례로 돈다. 모두가 몫 `budget` 하나를 함께 쓰고, 게이트마다 남은 몫을 받는다."""
    deadline = time.monotonic() + budget
    done: list[Gate] = []
    for argv in gates:
        code, timed_out = _run(argv, worktree, env, log, deadline - time.monotonic())
        done.append(Gate(command=" ".join(argv), exit_code=code, timed_out=timed_out))
    return tuple(done)


class _NotOverlaid(Exception):
    """M의 파일을 덮지 않았다. 덮지 않은 파일과 까닭을 든다."""


def _overlay(worktree: Path, blobs: Mapping[str, bytes]) -> None:
    """M의 파일을 작업 트리에 덮는다. 작업 트리 자리나 덮을 자리의 상위나 그 자리가 링크거나 쓰지
    못하면 `_NotOverlaid`다."""
    for rel, data in blobs.items():
        target = overlay_target(worktree, rel)
        if target is None:
            raise _NotOverlaid(f"{rel}. 작업 트리 자리나 그 아래의 상위나 그 자리가 링크다")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        except OSError as error:
            raise _NotOverlaid(f"{rel}. 쓰지 못했다: {error}") from error


def _hidden(
    worktree: Path,
    nodes: Sequence[str],
    blobs: Mapping[str, bytes],
    *,
    folder: Path,
    pytest: Sequence[str],
    env: Mapping[str, str],
    timeout: float,
) -> Hidden:
    log = folder / _HIDDEN_LOG
    if not nodes:
        # 노드 없이 띄우면 결과 커밋의 시험 전체를 돈다
        with log.open("ab") as sink:
            sink.write("(숨은 시험의 노드가 없어 돌지 않았다)\n".encode())
        return count_hidden(None, nodes)
    try:
        _overlay(worktree, blobs)
    except _NotOverlaid as refused:
        with log.open("ab") as sink:
            sink.write(f"(덮지 않았다: {refused})\n".encode())
        return count_hidden(None, nodes)
    xml = folder / _HIDDEN_XML
    try:
        xml.unlink(missing_ok=True)
    except OSError as error:
        raise GateError(f"앞선 junit xml 을 지우지 못했다: {xml}: {error}") from error
    args = [
        *pytest,
        "--rootdir=.",
        "-p",
        "no:cacheprovider",
        "-o",
        "junit_family=xunit2",
        f"--junitxml={xml}",
        "-q",
        *nodes,
    ]
    _, timed_out = _run(args, worktree, env, log, timeout)
    if timed_out:
        return count_hidden(None, nodes)
    try:
        text = xml.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        # 세션의 코드가 고쳐 쓸 수 있는 파일이라 풀지 못해도 예외가 아니라 실패다
        text = None
    return count_hidden(text, nodes)


def _remove(git: _Git, clone: Path, worktree: Path, log: Path, out: Callable[[str], None]) -> None:
    """게이트 작업 트리를 걷는다. 폴더도 등록도 없으면 할 일이 없다. 그 자리와 클론의 관리
    폴더(`.git/worktrees/`) 안의 링크를 먼저 끊는다. 그 자리나 클론의 git 폴더가 링크이거나 링크를
    끊지 못하면 걷지 않고 알린다."""
    if not os.path.lexists(worktree) and git.registration(clone, worktree) is Registration.ABSENT:
        return
    admin = clone / ".git" / "worktrees"
    linked = [str(p) for p in (worktree, clone / ".git", admin) if _is_link(p)]
    if linked:
        out(
            f"게이트 작업 트리를 걷지 않았다: {worktree}. 그 자리나 클론의 git 폴더가 링크다: "
            f"{', '.join(linked)}. 따라가면 바깥을 지울 수 있다. 그 링크를 링크만 지운 뒤 걷는다"
        )
        return
    left = cut_links(worktree) if os.path.lexists(worktree) else []
    if os.path.lexists(admin):
        left += cut_links(admin)
    if left:
        out(
            f"게이트 작업 트리를 걷지 않았다: {worktree}. 안의 링크를 끊지 못해 git 이 "
            f"그 링크를 따라가 바깥을 지울 수 있다: {', '.join(left[:3])}. "
            "그 링크를 링크만 지운 뒤 "
            f"git -C {clone} worktree remove --force {worktree} 로 걷는다"
        )
        return
    # 시간을 넘겨 죽은 꺼내기는 잠금을 남겼을 수 있어 --force 를 두 번 준다
    args = ["-c", "core.longpaths=true", "worktree", "remove", "--force", "--force", str(worktree)]
    reason = None
    try:
        git.logged(clone, args, "git worktree remove", log)
    except GateError as error:
        reason = str(error)
    if os.path.lexists(worktree) or git.registration(clone, worktree) is not Registration.ABSENT:
        why = reason or "git 은 걷었다고 했지만 남았다"
        out(
            f"게이트 작업 트리를 다 걷지 못했다: {worktree}({why}). "
            "그 자리를 쥔 프로세스가 끝난 뒤 "
            f"git -C {clone} worktree remove --force {worktree} 로 걷는다"
            "(등록이 없으면 폴더만 지운다)"
        )


@contextmanager
def _gate_worktree(
    git: _Git, clone: Path, worktree: Path, commit: str, log: Path, out: Callable[[str], None]
) -> Generator[None]:
    """결과 커밋 `commit`을 `worktree`에 분리 HEAD 작업 트리로 꺼내고, 끝나면 어느 길에서도(예외
    포함) 걷는다."""
    add = ["-c", "core.longpaths=true", "worktree", "add", "--detach", str(worktree), commit]
    try:
        git.logged(clone, add, "git worktree add", log)
        yield
    finally:
        _remove(git, clone, worktree, log, out)


def check_result(
    place: RoundDir,
    *,
    source: Path,
    commit: str,
    task: Task,
    env: Mapping[str, str],
    out: Callable[[str], None],
    setup: Sequence[Sequence[str]] = SETUP_ARGV,
    gates: Sequence[Sequence[str]] = GATE_ARGV,
    pytest: Sequence[str] = PYTEST_ARGV,
    limits: Limits = Limits(),  # noqa: B008  # 얼린 데이터클래스라 공유해도 바뀌지 않는다
) -> Checked:
    """회차 `place`의 결과 커밋 `commit`으로 게이트 `gates`와 `task`의 숨은 시험을 돈다.

    `source`는 M을 담은 원본 저장소다. 작업 트리를 걷지 못하는 등 결과와 별개로 사람이 알아야 할
    일은 `out`으로 알린다. 결과 작업 트리를 짓지 못하거나 B 의 설정을 풀지 못하면(`settings_env`)
    `GateError`다. B 설정의 `env`는 거르지 않고 얹으므로, 거기 `PATH`가 있으면 넘긴 환경의 `PATH`를
    덮는다(못 보는 것. 2026-10-27 에 `git log --all -S'"PATH"' -- .claude/settings.json`이 빈
    것을 손으로 봤다). 회차 폴더에 로그를 쓰지
    못하면 `OSError`가 그대로 오른다.
    """
    if not _COMMIT.fullmatch(commit):
        raise GateError(f"결과 커밋이 40자 커밋 해시가 아니다: {commit!r}")
    env = {**env, **settings_env(source, task.base, env, timeout=limits.git)}
    clean, git = _git_of(env, limits.git)
    files = dict.fromkeys((*hidden_test_files(task), *task.support_files))
    blobs = {rel: git.read(source, ["cat-file", "blob", f"{task.merge}:{rel}"]) for rel in files}
    worktree = place.path / _WORKTREE
    if os.path.lexists(worktree):
        raise GateError(f"게이트 작업 트리 자리가 이미 있다: {worktree}")
    with _gate_worktree(git, place.clone, worktree, commit, place.path / _GIT_LOG, out):
        done = run_setup(
            worktree, setup, env=clean, log=place.path / _SETUP_LOG, timeout=limits.setup
        )
        gate_results = None
        if done.failed is None:
            gate_results = _gates(worktree, gates, clean, place.path / _GATE_LOG, limits.gates)
        hidden = None
        # 판정(`tools/rerun_judge.py`의 `solved`)이 게이트 초록을 먼저 요구해, 게이트가 초록이
        # 아닌 회차의 숨은 시험은 판정에 쓰이지 않는다
        if gate_results is not None and all(g.exit_code == 0 for g in gate_results):
            hidden = _hidden(
                worktree,
                task.hidden_tests,
                blobs,
                folder=place.path,
                pytest=pytest,
                env=clean,
                timeout=limits.hidden,
            )
    setup_failure = None if done.failed is None else setup_failure_of(done.failed)
    return Checked(setup_failure=setup_failure, gates=gate_results, hidden=hidden)
