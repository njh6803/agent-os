"""병합된 워크트리와 로컬 브랜치를 판정하고, 후보 하나씩 지운다. `tidy-checkouts` 스킬 3이 부른다.

세션마다 판정과 삭제 스크립트를 스크래치에 새로 짓다가, 사용자가 끊은 호출이 지우는 도중에 죽어
지우다 만 폴더가 생겼다(대기열 132, 일지 2026-10-07-02). 그래서 판정은 이 도구가 한 번에 내고,
삭제는 후보 하나마다 따로 부른다. 끊긴 호출이 망가뜨리는 것은 많아야 하나다.

사용(주 체크아웃에서):
    uv run python tools/tidy_checkouts.py judge [--running "<세션 제목>" ...]
    uv run python tools/tidy_checkouts.py remove "<경로>" <브랜치> <HEAD>
    uv run python tools/tidy_checkouts.py remove-branch <브랜치> <커밋>

`--running` 은 `list_sessions` 에서 이 세션을 뺀 `isRunning` 세션의 제목이다. 도구는 앱의 세션을
보지 못해 부르는 쪽이 넘긴다. `judge` 는 줄마다 `지운다`·`남긴다`·`넘긴다`(사람에게)와 이유를 찍고,
지울 것에는 부를 `remove`·`remove-branch` 명령을 붙인다. 경로나 브랜치 이름에 셸이 풀 수 있는
글자가 들었으면 명령 없이 넘긴다. git 은 모두 `core.longpaths=true` 로 친다
(스킬 머리 문단).

판정. 워크트리마다 아래 순서로 보고 처음 어긋난 것을 이유로 찍는다. 모두 맞아야 지운다.
- 자리. 등록이 `prunable` 이거나 폴더가 없거나, 그 폴더에서 `git rev-parse --show-toplevel` 이 그
  경로가 아니면 사람에게 넘긴다. `.git` 파일이 없는 폴더에서 친 git 은 루트 저장소에 닿아, 그
  status 는 루트의 것이다(대기열 135, 일지 2026-10-07-03).
- 판정 1, 병합됐다. 분리 HEAD 면 넘긴다. 병합된 PR 중 머리 브랜치 이름이 같은 것의 `headRefOid` 가
  브랜치 끝(그 워크트리의 HEAD)과 같아야 한다. 이름이 같은 PR 이 없으면 남기고, 있는데 머리가 다르면
  넘긴다. 이름만 보면 포크의 같은 이름 브랜치를 잡으므로 머리를 견준다. squash 라 `git log` 로는
  가르지 못하고, 브랜치 끝이 `origin/main` 의 조상인 것으로도 판정하지 않는다. 막 따고 커밋하지 않은
  브랜치도 조상이다(일지 2026-10-05-05). 병합된 PR 은 `gh pr list` 한 번에 최근 1000개를 읽는다.
  그보다 오래된 것은 병합되지 않은 것으로 보여 남는다(안전한 쪽).
- 판정 2, 깨끗하다. `status --porcelain --untracked-files=all` 의 stdout 과 stderr 가 모두 비어야
  한다. stderr 의 경고는 git 이 그 아래를 보지 못했다는 뜻이다. `status --ignored` 의 `!!` 항목은
  다시 만들 수 있는 것(`RECREATABLE_*`, 루트와 바이트가 같은 `.claude/settings.local.json`)뿐이어야
  한다.
  `git worktree remove` 는 무시된 파일을 묻지 않고 지운다. `.env` 나 `traces/` 가 있으면 남긴다.
- 판정 3, 주인이 없다. 제목이 그 브랜치인 실행 중 세션이 있으면 남긴다. 잠금 사유는
  `claude session <이름> (pid <N>)` 모양이고 그 pid 가 살아 있으면 남긴다. 죽었으면 `remove` 가 풀고
  지운다. 사유가 다른 모양이면 넘긴다. 잠금이 없다고 주인이 없는 것은 아니다. `git worktree add` 로
  판 워크트리와 `EnterWorktree(path)` 로 들어간 워크트리는 잠기지 않는다(일지 2026-10-06-04).
  제목이 체크아웃된 어느 브랜치와도 맞지 않는 실행 중 세션이 있으면 지울 후보를 모두 넘긴다. 그
  세션이 어느 워크트리에 있는지 알 수 없다(일지 2026-10-06-03). 사람이 그 세션이 후보에 없다고
  답하면 부르는 쪽이 `remove` 를 부른다. `remove` 는 세션을 보지 않는다.
체크아웃되지 않은 로컬 브랜치는 판정 1만 본다. `.claude/worktrees/` 아래인데 등록이 없는 폴더는
넘긴다. 그 안에서 친 git 은 루트에 닿는다.

판정 4, 지운다(`remove`). 후보 하나를 다시 판정하고(세션은 빼고) 브랜치와 HEAD 가 인자와 같을 때만,
아래 순서로 지운다.
1. 점유 탐침. 워크트리 폴더를 옆 이름으로 바꿨다가 되돌린다. 윈도에서 그 아래를 작업 디렉터리로
   쥔 프로세스나 그 안의 파일을 연 프로세스가 있으면 이름 바꾸기가 막힌다. 그대로 지우면 git 은
   `Permission denied`·`Invalid argument` 로 지우다 만 폴더를 남긴다(`.scratch/harness/probes/
   worktree_occupancy.py` 의 B·C). 막히면 아무것도 바꾸지 않고 멈춘다.
2. 다시 거르기. 판정 1~3을 한 번 더 내고, 지울 무시된 항목도 그때 읽는다. 판정 뒤에 생긴 `.env` 나
   새 파일을 앞지우기가 지우지 않게 한다. 어긋나면 아무것도 바꾸지 않고 멈춘다.
3. 죽은 잠금을 푼다. 1·2가 막히면 잠금도 그대로 남도록 그 뒤다.
4. 앞지우기. 2가 읽은 무시된 항목을 이 도구가 git 보다 먼저 지운다. 막히면 멈춘다. 등록과
   `.git` 파일은 남는다(프로브의 F). 워크트리 밖의 하드링크 이름으로 같은 DLL 을 적재한 프로세스는
   이름 바꾸기를 지나는데 git 은 지우다 만 폴더를 남긴다(프로브의 E). uv 의 `.venv` 는 캐시에서
   하드링크로 채워져, 어느 체크아웃의 파이썬이 확장 모듈을 실으면 같은 캐시 파일에 걸린 다른
   워크트리의 `.pyd` 도 그 처지가 된다. 링크 수는 손으로 봤다
   (`pydantic_core` 의 `.pyd` 22, `yaml` 의 `.pyd` 19). 2026-10-07 에 `mutate-restore-guard` 가
   `Invalid argument` 로 그 `yaml` 의 `.pyd` 에서 멈췄다(손으로 봤다, 일지 2026-10-07-15). 같은
   까닭으로 이 도구는 표준 라이브러리만 쓴다. 링크(심볼릭 링크, 정션)는 따라가지 않고 링크 자체만
   지운다.
5. `git worktree remove <경로>`. git 2.32 는 지우다 실패해도 등록을 지우고(`.scratch/harness/probes/
   worktree_longpath.py`), 그 폴더의 `.git` 파일도 지운다(`worktree_occupancy.py` 의 B·C·E).
6. `git branch -D <브랜치>`. squash 병합이라 `-d` 는 병합을 알아보지 못한다.

못 보는 것.
- 앞지우기 뒤에 남은 추적 파일을 다른 프로세스가 워크트리 밖의 하드링크 이름으로 적재한 것.
  추적 파일은 하드링크가 아니라 드물다.
- 탐침과 git 사이에 새로 생긴 점유와 파일. 다시 거른 뒤 git 이 지울 때까지의 틈이다.
- 세션이 쓰던 워크트리인지. 제목과 잠금으로만 가린다(판정 3).
- 맥과 리눅스의 점유. 재지 않았다. 그 OS 는 열린 파일과 작업 디렉터리가 이름 바꾸기를 막지 않는
  것으로 알고 있어(어림) 탐침이 점유를 보지 못한다고 본다.

종료 코드. `judge`: 0 찍었다, 2 인자가 틀렸거나 주 체크아웃이 아니다, 3 git 이나 gh 가 실패했다.
`remove`·`remove-branch`: 0 지웠다. 1 망가뜨린 것 없이 멈췄다. 아무것도 바꾸지 않았거나(1·2에서
멈췄다), 죽은 잠금을 풀고 다시 만들 수 있는 것만 지웠거나(4에서 멈췄다. 등록과 `.git` 이 남는다),
워크트리는 지웠는데 브랜치가 남았다(6).
다음 후보로 가도 된다. 2 인자가 틀렸거나 주 체크아웃이 아니다. 3 멈추고 사람에게 넘긴다. 지우다 만
폴더나 옆 이름에 남은 폴더가 생겼을 수 있거나, git·gh 를 부르지 못했다.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Literal

type Action = Literal["delete", "keep", "human", "hold"]
type GitRunner = Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]]
type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

COMMAND = "uv run python tools/tidy_checkouts.py"
WORKTREES_DIR = ".claude/worktrees"
SETTINGS = ".claude/settings.local.json"
PROBE_SUFFIX = ".tidy-probe"
MERGED_LIMIT = 1000
RECREATABLE_DIRS = frozenset(
    {
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".import_linter_cache",
        ".grimp_cache",
        "node_modules",
        ".next",
        "test-results",
        "playwright-report",
        "blob-report",
        "coverage",
    }
)
RECREATABLE_FILES = frozenset({"next-env.d.ts"})
# 이름이 흔해 자리째로 본다. `.gitignore` 가 앵커를 붙인 디자인 시스템 패키지의 빌드다(ADR 0026)
RECREATABLE_PATHS = frozenset({"web/packages/ui/dist/", "web/packages/ui/storybook-static/"})

_LOCK_PID = re.compile(r"^claude session \S+ \(pid (\d+)\)$")
# 찍은 명령을 에이전트가 셸에 그대로 친다. git 은 브랜치 이름에 `$`·`;`·`(`·백틱을 허락해, 그런
# 이름이 든 명령은 찍지 않고 사람에게 넘긴다(셀프 보안 리뷰, 일지 2026-10-07-15)
_SHELL_UNSAFE = re.compile(r"[\s$`\"'\\;&|<>(){}*?\[\]!#~]")
_ACTIONS: dict[Action, str] = {
    "delete": "지운다",
    "keep": "남긴다",
    "human": "넘긴다",
    "hold": "넘긴다",
}


class ToolError(Exception):
    """git 이나 gh 를 부르지 못했다. 판정을 낼 수 없다."""


@dataclass(frozen=True)
class Worktree:
    """`git worktree list --porcelain` 의 한 항목. `locked` 는 잠금 사유다(사유가 없으면 "")."""

    path: str
    head: str | None = None
    branch: str | None = None
    locked: str | None = None
    prunable: bool = False
    bare: bool = False


@dataclass(frozen=True)
class Facts:
    """판정 2와 자리 판정의 재료. 자리가 어긋나면 status 를 읽지 않아 빈 값이다."""

    exists: bool
    toplevel: str | None
    status: str
    status_err: str
    ignored: tuple[str, ...]
    settings_same: bool


@dataclass(frozen=True)
class Verdict:
    """`hold` 는 지울 것이었는데 제목 모를 세션 때문에 넘긴 것이다. 사람이 승인하면 지운다.
    `human` 은 사람이 직접 본다. `unlock` 은 지우기 전에 죽은 잠금을 풀어야 한다는 뜻이다."""

    action: Action
    path: str
    reason: str
    branch: str | None = None
    head: str | None = None
    unlock: bool = False


# --- 바깥을 부르는 것 ---------------------------------------------------------------------------


def real_git(args: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """`GIT_OPTIONAL_LOCKS=0`: 남의 워크트리에서 친 `status` 가 색인을 고쳐 쓰며 잠그지 않는다."""
    return subprocess.run(
        ["git", "-c", "core.longpaths=true", *args],
        cwd=cwd,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def gh_merged_heads(root: Path) -> dict[str, frozenset[str]]:
    fields = "headRefName,headRefOid"
    command = ["gh", "pr", "list", "--state", "merged", "--limit", str(MERGED_LIMIT)]
    try:
        result = subprocess.run(
            [*command, "--json", fields],
            cwd=root,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as error:
        raise ToolError(f"gh 를 띄우지 못했다: {error}") from error
    if result.returncode != 0:
        raise ToolError(f"gh pr list 가 {result.returncode} 로 끝났다: {result.stderr.strip()}")
    try:
        return parse_merged(result.stdout)
    except ValueError as error:
        raise ToolError(f"gh pr list 의 출력을 읽지 못했다: {error}") from error


def process_alive(pid: int) -> bool:
    """그 pid 의 프로세스가 있는지. 알 수 없으면 있다고 본다(지우지 않는 쪽)."""
    if sys.platform == "win32":
        query = ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"]
        try:
            result = subprocess.run(query, capture_output=True, text=True, errors="replace")
        except OSError:
            return True
        return result.returncode != 0 or tasklist_has(result.stdout, pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _long(path: Path) -> str:
    """윈도에서 MAX_PATH 를 넘는 경로를 파이썬이 다루도록 `\\\\?\\` 를 붙인 절대 경로."""
    text = os.path.abspath(path)
    if sys.platform == "win32" and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def _writable_retry(function: Callable[[str], object], target: str, error: BaseException) -> None:
    """읽기 전용 파일이면 쓰기를 켜고 한 번 더 지운다. 그래도 막히면 그 예외로 멈춘다."""
    if not isinstance(error, PermissionError):
        raise error
    os.chmod(target, stat.S_IWRITE)
    function(target)


def delete_path(path: Path) -> None:
    """무시된 항목 하나를 지운다. 링크는 따라가지 않고 링크 자체만 지운다. 막히면 OSError."""
    target = _long(path)
    if os.path.islink(target) or os.path.isjunction(target):
        os.unlink(target)
    elif os.path.isdir(target):
        shutil.rmtree(target, onexc=_writable_retry)
    elif os.path.lexists(target):
        try:
            os.unlink(target)
        except PermissionError as error:
            _writable_retry(os.unlink, target, error)


@dataclass(frozen=True)
class Ops:
    """바깥을 부르는 자리. 테스트가 실패를 넣는다."""

    git: GitRunner = real_git
    merged: Callable[[Path], dict[str, frozenset[str]]] = gh_merged_heads
    pid_alive: Callable[[int], bool] = process_alive
    rename: Callable[[str, str], None] = os.rename
    delete: Callable[[Path], None] = delete_path


# --- 읽기 ---------------------------------------------------------------------------------------


def parse_worktrees(porcelain: str) -> list[Worktree]:
    worktrees: list[Worktree] = []
    fields: dict[str, str] = {}
    for line in [*porcelain.splitlines(), ""]:
        if line:
            key, _, value = line.partition(" ")
            fields[key] = value
            continue
        if "worktree" in fields:
            branch = fields.get("branch")
            worktrees.append(
                Worktree(
                    path=fields["worktree"],
                    head=fields.get("HEAD"),
                    branch=branch.removeprefix("refs/heads/") if branch is not None else None,
                    locked=fields.get("locked"),
                    prunable="prunable" in fields,
                    bare="bare" in fields,
                )
            )
        fields = {}
    return worktrees


def lock_pid(reason: str) -> int | None:
    match = _LOCK_PID.match(reason)
    return int(match.group(1)) if match else None


def parse_merged(text: str) -> dict[str, frozenset[str]]:
    """`gh pr list --json headRefName,headRefOid` 의 출력. 모양이 어긋나면 ValueError."""
    parsed: Json = json.loads(text)
    if not isinstance(parsed, list):
        raise ValueError("배열이 아니다")
    heads: dict[str, set[str]] = {}
    for row in parsed:
        if not isinstance(row, dict):
            raise ValueError("객체가 아닌 항목이 있다")
        name = row.get("headRefName")
        oid = row.get("headRefOid")
        if not isinstance(name, str) or not isinstance(oid, str):
            raise ValueError("headRefName 이나 headRefOid 가 문자열이 아니다")
        heads.setdefault(name, set()).add(oid)
    return {name: frozenset(oids) for name, oids in heads.items()}


def tasklist_has(output: str, pid: int) -> bool:
    """`tasklist /FO CSV /NH` 의 출력에 그 pid 의 줄이 있는지. 둘째 칸이 pid 다."""
    return any(len(row) >= 2 and row[1] == str(pid) for row in csv.reader(output.splitlines()))


def unrecreatable(ignored: Sequence[str], settings_same: bool) -> list[str]:
    """`status --ignored` 의 `!!` 항목 중 다시 만들 수 없는 것. 디렉터리는 `/` 로 끝난다."""
    kept: list[str] = []
    for entry in ignored:
        name = entry.rstrip("/").rsplit("/", 1)[-1]
        if entry.endswith("/"):
            if name in RECREATABLE_DIRS or entry in RECREATABLE_PATHS:
                continue
        elif name in RECREATABLE_FILES or (entry == SETTINGS and settings_same):
            continue
        kept.append(entry)
    return kept


def same_path(left: str, right: str) -> bool:
    return os.path.normcase(os.path.normpath(left)) == os.path.normcase(os.path.normpath(right))


# --- 판정 ---------------------------------------------------------------------------------------


def judge(
    wt: Worktree,
    facts: Facts,
    merged: Mapping[str, frozenset[str]],
    running: Sequence[str],
    alive: Callable[[int], bool],
) -> Verdict:
    """워크트리 하나의 판정. 순서와 근거는 모듈 독스트링."""

    def verdict(action: Action, reason: str) -> Verdict:
        return Verdict(action, wt.path, reason, wt.branch, wt.head)

    if wt.prunable:
        return verdict("human", "등록이 prunable 이다. 지우다 만 폴더일 수 있다")
    if not facts.exists:
        return verdict("human", "등록은 있는데 폴더가 없다")
    if facts.toplevel is None or not same_path(facts.toplevel, wt.path):
        return verdict("human", f"그 폴더의 git 이 다른 저장소({facts.toplevel})를 읽는다")
    if wt.branch is None or wt.head is None:
        return verdict("human", "분리 HEAD 다")
    heads = merged.get(wt.branch)
    if not heads:
        return verdict("keep", "병합된 PR 이 없다")
    if wt.head not in heads:
        return verdict("human", "병합된 PR 의 머리와 브랜치 끝이 다르다")
    if facts.status:
        return verdict("keep", "바뀐 파일이 있다")
    if facts.status_err:
        return verdict("keep", f"git status 가 경고를 냈다: {facts.status_err.strip()[:120]}")
    extra = unrecreatable(facts.ignored, facts.settings_same)
    if extra:
        return verdict("keep", f"다시 만들 수 없는 무시된 항목: {', '.join(extra[:5])}")
    if wt.branch in running:
        return verdict("keep", "그 브랜치가 제목인 세션이 돈다")
    if wt.locked is None:
        return verdict("delete", "")
    pid = lock_pid(wt.locked)
    if pid is None:
        return verdict("human", f"잠금 사유에 pid 가 없다: {wt.locked or '(사유 없음)'}")
    if alive(pid):
        return verdict("keep", f"잠금 pid {pid} 가 살아 있다. 그 세션: {wt.locked}")
    dead = f"잠금 pid {pid} 는 죽었다. remove 가 풀고 지운다"
    return Verdict("delete", wt.path, dead, wt.branch, wt.head, unlock=True)


def hold_for_strangers(
    verdicts: Sequence[Verdict], running: Sequence[str], checked_out: set[str]
) -> list[Verdict]:
    """제목이 체크아웃된 어느 브랜치와도 맞지 않는 실행 중 세션이 있으면 지울 것을 넘긴다."""
    strangers = [title for title in running if title not in checked_out]
    if not strangers:
        return list(verdicts)
    reason = f"제목이 체크아웃된 어느 브랜치와도 맞지 않는 세션이 돈다: {', '.join(strangers)}"
    return [
        replace(v, action="hold", reason=reason) if v.action == "delete" else v for v in verdicts
    ]


def judge_branch(branch: str, tip: str, merged: Mapping[str, frozenset[str]]) -> Verdict:
    """체크아웃되지 않은 로컬 브랜치의 판정 1."""
    heads = merged.get(branch)
    if not heads:
        return Verdict("keep", branch, "병합된 PR 이 없다", branch, tip)
    if tip not in heads:
        return Verdict("human", branch, "병합된 PR 의 머리와 브랜치 끝이 다르다", branch, tip)
    return Verdict("delete", branch, "", branch, tip)


# --- 배관 ---------------------------------------------------------------------------------------


def _checked(git: GitRunner, args: Sequence[str], cwd: Path) -> str:
    result = git(args, cwd)
    if result.returncode != 0:
        raise ToolError(f"git {' '.join(args)} 가 {result.returncode} 로 끝났다: {result.stderr}")
    return result.stdout


def _same_bytes(left: Path, right: Path) -> bool:
    try:
        return left.read_bytes() == right.read_bytes()
    except OSError:
        return False


def _misplaced(*, exists: bool, toplevel: str | None) -> Facts:
    """자리가 어긋나 status 를 읽지 않은 재료. 그 폴더의 git 은 루트에 닿을 수 있다."""
    return Facts(
        exists=exists, toplevel=toplevel, status="", status_err="", ignored=(), settings_same=False
    )


def gather(root: Path, wt: Worktree, git: GitRunner) -> Facts:
    path = Path(wt.path)
    if not path.is_dir():
        return _misplaced(exists=False, toplevel=None)
    top = git(["rev-parse", "--show-toplevel"], path)
    toplevel = top.stdout.strip() if top.returncode == 0 else None
    if toplevel is None or not same_path(toplevel, wt.path):
        return _misplaced(exists=True, toplevel=toplevel)
    status = git(["status", "--porcelain", "-z", "--untracked-files=all"], path)
    status_err = status.stderr or ("" if status.returncode == 0 else f"exit {status.returncode}")
    listed = git(["status", "--porcelain", "-z", "--ignored"], path)
    if listed.returncode != 0 and not status_err:
        status_err = listed.stderr or f"exit {listed.returncode}"
    ignored = tuple(item[3:] for item in listed.stdout.split("\0") if item.startswith("!! "))
    settings_same = _same_bytes(root / SETTINGS, path / SETTINGS)
    return Facts(
        exists=True,
        toplevel=toplevel,
        status=status.stdout,
        status_err=status_err,
        ignored=ignored,
        settings_same=settings_same,
    )


def _place(cwd: Path, git: GitRunner) -> tuple[Path, list[Worktree]]:
    """주 체크아웃의 루트와 워크트리 목록. 주 체크아웃이 아니면 ValueError."""
    top = git(["rev-parse", "--show-toplevel"], cwd)
    if top.returncode != 0:
        raise ValueError(f"git 저장소가 아니다: {top.stderr.strip()}")
    listing = parse_worktrees(_checked(git, ["worktree", "list", "--porcelain"], cwd))
    if not listing or not same_path(top.stdout.strip(), listing[0].path):
        raise ValueError("이 폴더는 워크트리다. 주 체크아웃 세션에서 돈다")
    prefix = _checked(git, ["rev-parse", "--show-prefix"], cwd).strip()
    if prefix.startswith(WORKTREES_DIR + "/"):
        raise ValueError(f"지우다 만 워크트리 폴더 안이다({prefix}). git 이 루트에 닿는다")
    return Path(listing[0].path), listing


def _render(verdict: Verdict, kind: Literal["worktree", "branch"]) -> str:
    label = (
        _ACTIONS[verdict.action] if kind == "worktree" else "브랜치를 " + _ACTIONS[verdict.action]
    )
    if kind == "worktree":
        command = f'{COMMAND} remove "{verdict.path}" {verdict.branch} {verdict.head}'
    else:
        command = f"{COMMAND} remove-branch {verdict.branch} {verdict.head}"
    names = (verdict.path, verdict.branch or "", verdict.head or "")
    if verdict.action in ("delete", "hold") and any(map(_SHELL_UNSAFE.search, names)):
        hand_off = "넘긴다" if kind == "worktree" else "브랜치를 넘긴다"
        return f"{hand_off} {verdict.path} — 셸이 풀 수 있는 글자가 든 이름이라 명령을 찍지 않는다"
    if verdict.action == "hold":
        return f"{label} {verdict.path} — {verdict.reason}. 승인하면 → {command}"
    if verdict.action != "delete":
        return f"{label} {verdict.path} — {verdict.reason}"
    note = f" ({verdict.reason})" if verdict.reason else ""
    return f"{label} {verdict.path}{note} → {command}"


def _judge_all(root: Path, listing: list[Worktree], running: Sequence[str], ops: Ops) -> int:
    merged = ops.merged(root)
    others = [wt for wt in listing[1:] if not wt.bare]
    verdicts = [
        judge(wt, gather(root, wt, ops.git), merged, running, ops.pid_alive) for wt in others
    ]
    checked_out = {wt.branch for wt in listing if wt.branch is not None}
    for verdict in hold_for_strangers(verdicts, running, checked_out):
        print(_render(verdict, "worktree"))
    registered = [wt.path for wt in listing]
    holder = root / WORKTREES_DIR
    strays = sorted(p for p in holder.iterdir() if p.is_dir()) if holder.is_dir() else []
    for stray in strays:
        if not any(same_path(str(stray), path) for path in registered):
            print(
                f"넘긴다 {stray.as_posix()} — 등록 없는 워크트리 폴더다. 안의 git 은 루트에 닿는다"
            )
    refs = _checked(
        ops.git, ["for-each-ref", "refs/heads", "--format=%(refname:short) %(objectname)"], root
    )
    for line in refs.splitlines():
        branch, _, tip = line.partition(" ")
        if branch and branch not in checked_out:
            print(_render(judge_branch(branch, tip, merged), "branch"))
    return 0


def _remove(
    root: Path, listing: list[Worktree], target: str, branch: str, head: str, ops: Ops
) -> int:
    """판정 4. 단계의 순서와 종료 코드는 모듈 독스트링."""
    wt = next((w for w in listing[1:] if same_path(w.path, target)), None)
    if wt is None:
        print(f"남겼다 {target} — 등록된 워크트리가 아니다")
        return 1
    if (wt.branch, wt.head) != (branch, head):
        print(f"남겼다 {target} — judge 뒤에 바뀌었다: 지금 {wt.branch} {wt.head}")
        return 1
    merged = ops.merged(root)
    if _still_candidate(root, wt, merged, ops, "지우기 전에") is None:
        return 1
    stop = _probe(Path(wt.path), ops.rename)
    if stop is not None:
        return stop
    # 판정 뒤에 생긴 것(`.env`, 새 파일)을 앞지우기가 지우지 않게, 지울 목록을 다시 판정해 읽는다
    again = _still_candidate(root, wt, merged, ops, "앞지우기 직전에")
    if again is None:
        return 1
    verdict, facts = again
    if verdict.unlock and not _unlock(root, wt, ops.git):
        return 1
    if not _pre_delete(Path(wt.path), facts.ignored, ops.delete):
        return 1
    return _git_remove(root, wt.path, branch, ops.git)


def _still_candidate(
    root: Path, wt: Worktree, merged: Mapping[str, frozenset[str]], ops: Ops, moment: str
) -> tuple[Verdict, Facts] | None:
    """판정 1~3(세션 빼고)을 다시 낸다. 지울 것이 아니면 이유를 찍고 None."""
    facts = gather(root, wt, ops.git)
    verdict = judge(wt, facts, merged, (), ops.pid_alive)
    if verdict.action != "delete":
        print(f"남겼다 {wt.path} — {moment} 다시 판정했다: {verdict.reason}")
        return None
    return verdict, facts


def _probe(path: Path, rename: Callable[[str, str], None]) -> int | None:
    """점유 탐침. 지나면 None, 막히면 1(바꾼 것 없음), 되돌리지 못하면 3."""
    aside = path.with_name(path.name + PROBE_SUFFIX)
    if os.path.lexists(aside):
        print(f"남겼다 {path.as_posix()} — 탐침 자리 {aside.as_posix()} 가 이미 있다")
        return 1
    try:
        rename(_long(path), _long(aside))
    except OSError as error:
        print(
            f"남겼다 {path.as_posix()} — 다른 프로세스가 쥐고 있다(이름 바꾸기가 막혔다: {error})"
        )
        return 1
    try:
        rename(_long(aside), _long(path))
    except OSError as error:
        print(
            f"멈췄다 {path.as_posix()} — 폴더가 {aside.as_posix()} 에 남았다. "
            f"되돌리지 못했다: {error}"
        )
        return 3
    return None


def _unlock(root: Path, wt: Worktree, git: GitRunner) -> bool:
    unlocked = git(["worktree", "unlock", wt.path], root)
    if unlocked.returncode != 0:
        print(f"남겼다 {wt.path} — 잠금을 풀지 못했다: {unlocked.stderr.strip()}")
        return False
    return True


def _pre_delete(path: Path, entries: Sequence[str], delete: Callable[[Path], None]) -> bool:
    """앞지우기. 막히면 그 자리에서 멈추고 False. 등록과 `.git` 은 남는다."""
    for entry in entries:
        try:
            delete(path / entry)
        except OSError as error:
            print(
                f"남겼다 {path.as_posix()} — 다시 만들 수 있는 {entry} 를 지우다 막혔다({error}). "
                "등록과 .git 은 남았다"
            )
            return False
    return True


def _git_remove(root: Path, path: str, branch: str, git: GitRunner) -> int:
    removed = git(["worktree", "remove", path], root)
    if removed.returncode != 0:
        print(
            f"멈췄다 {path} — git worktree remove 가 {removed.returncode} 로 끝났다: "
            f"{removed.stderr.strip()}. 등록과 .git 파일이 지워졌을 수 있다"
        )
        return 3
    deleted = git(["branch", "-D", branch], root)
    if deleted.returncode != 0:
        print(f"지웠다 {path}, 브랜치는 남았다 — git branch -D: {deleted.stderr.strip()}")
        return 1
    print(f"지웠다 {path} 와 브랜치 {branch}")
    return 0


def _remove_branch(root: Path, listing: list[Worktree], branch: str, tip: str, ops: Ops) -> int:
    if any(wt.branch == branch for wt in listing):
        print(f"남겼다 {branch} — 체크아웃돼 있다")
        return 1
    current = ops.git(["rev-parse", "--verify", "--quiet", f"refs/heads/{branch}"], root)
    if current.returncode != 0 or current.stdout.strip() != tip:
        print(f"남겼다 {branch} — judge 뒤에 바뀌었다: 지금 {current.stdout.strip() or '없음'}")
        return 1
    verdict = judge_branch(branch, tip, ops.merged(root))
    if verdict.action != "delete":
        print(f"남겼다 {branch} — 다시 판정했다: {verdict.reason}")
        return 1
    deleted = ops.git(["branch", "-D", branch], root)
    if deleted.returncode != 0:
        print(f"남겼다 {branch} — git branch -D: {deleted.stderr.strip()}")
        return 1
    print(f"지웠다 브랜치 {branch}")
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tidy_checkouts", description="병합된 워크트리와 로컬 브랜치를 판정하고 하나씩 지운다"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    judged = commands.add_parser("judge", help="워크트리와 로컬 브랜치를 판정해 찍는다")
    judged.add_argument("--running", action="append", default=[], help="실행 중 세션의 제목")
    removed = commands.add_parser("remove", help="워크트리 후보 하나를 지운다")
    removed.add_argument("path")
    removed.add_argument("branch")
    removed.add_argument("head")
    branch = commands.add_parser("remove-branch", help="체크아웃되지 않은 브랜치 하나를 지운다")
    branch.add_argument("branch")
    branch.add_argument("tip")
    return parser


def main(
    argv: Sequence[str] | None = None, *, cwd: Path | None = None, ops: Ops | None = None
) -> int:
    args = _parser().parse_args(argv)
    tools = ops if ops is not None else Ops()
    try:
        root, listing = _place(cwd if cwd is not None else Path.cwd(), tools.git)
    except ValueError as error:
        print(f"주 체크아웃 세션에서 돈다: {error}", file=sys.stderr)
        return 2
    except ToolError as error:
        print(error, file=sys.stderr)
        return 3
    command: str = args.command
    try:
        if command == "judge":
            running: list[str] = args.running
            return _judge_all(root, listing, running, tools)
        if command == "remove":
            return _remove(root, listing, args.path, args.branch, args.head, tools)
        return _remove_branch(root, listing, args.branch, args.tip, tools)
    except ToolError as error:
        print(error, file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
