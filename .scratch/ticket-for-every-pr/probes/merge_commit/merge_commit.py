"""병합을 마무리하는 커밋에서 pre-commit 훅이 보는 merge-base와 색인 차이를 잰다(명세 "커밋 검사").

커밋 검사는 바뀐 파일(C)을 `origin/main`과 HEAD의 merge-base에서 지금 색인까지로 본다. 브랜치가
`origin/main`을 합치다 충돌을 풀고 `git commit`을 치면, 그 커밋의 pre-commit에서 HEAD는 아직 병합
전이고 색인에는 main이 들여온 파일이 있다. 그러면 C에 main의 변경이 섞여 면제 브랜치가 거짓으로 막힐
수 있다. 이 프로브는 그 자리에서 두 merge-base(HEAD 하나, HEAD와 `MERGE_HEAD`)가 내는 C를 견준다.

갈래 넷을 임시 저장소(맨 원격 하나와 그 클론)에서 돈다.

1. 충돌 병합. 브랜치와 main이 같은 파일(`queue.md`)을 고치고 main만 `tools/x.py`를 더한다.
   `git merge origin/main`이 충돌로 멈춘 뒤 풀고 `git commit --no-edit`를 친다. 기대는 셋이다. 훅이
   돌았고 `MERGE_HEAD`가 있었다. HEAD만으로 구한 C에 `tools/x.py`가 든다.
   `git merge-base origin/main HEAD <MERGE_HEAD>`(둘째 인자 뒤의 커밋들을 합친 가상의 커밋과 첫
   인자의 merge-base)로 구한 C에는 `tools/x.py`가 없고 `queue.md`만 든다. 훅은 `MERGE_HEAD`를
   git 디렉터리의 파일로도, ref 이름(`git rev-parse -q --verify MERGE_HEAD`)으로도 찾는다.
4. 링크드 워크트리의 충돌 병합. 1과 같은 병합을 `git worktree add`로 만든 워크트리에서 친다. 그
   워크트리의 `.git`은 파일이고 git 디렉터리는 클론의 `.git/worktrees/<이름>`이라, 작업 트리 루트의
   `.git/MERGE_HEAD`를 경로로 읽으면 병합 중인 것을 놓친다. 기대는 넷이다. 루트 경로로는
   `MERGE_HEAD`가 없고, git 디렉터리의 파일과 ref 이름으로는 있다. ref 이름으로 구한 C에는
   `queue.md`만 든다. 표지는 워크트리의 `.git`이 파일이고 훅이 본 git 디렉터리에 `worktrees`가 든
   것이다(이 저장소의 커밋 대부분이 링크드 워크트리에서 난다, PR 직전 `bug-perf-review`가 짚었다).
2. 충돌 없는 병합. main만 `tools/x.py`를 더하고 `git merge origin/main --no-edit`를 친다. 이
   저장소는 pre-commit과 commit-msg만 깐다(`.pre-commit-config.yaml`의
   `default_install_hook_types`). 그래서 pre-commit 훅만 둔 이 갈래에서는 훅이 돌지 않아야 한다.
   병합 커밋이 생겼다(부모 둘)는 것이 병합이 일어났다는 표지다.
3. 양성 대조. 같은 훅으로 보통 커밋을 쳐서 훅이 돌고 `MERGE_HEAD`가 없었다는 것을 본다. 2에서 훅이
   돌지 않은 것이 훅을 실행하지 못해서가 아니라는 것을 가른다.

측정인 회차는 표지(1과 4의 `CONFLICT` 출력과 훅 기록, 2의 부모 둘, 3의 훅 기록, 4의 워크트리
표지)를 모두 갖춘 회차다.
측정이 아니거나 기대와 다르면 1로 끝난다. 결과는 JSON 한 줄로 찍는다. 표준 라이브러리만 쓰고 git을
부를 때마다 시간 제한을 둔다. 저장소 밖 임시 폴더에서 돌도록 git의 저장소 위치 변수를 벗긴다.

    uv run --no-project python .scratch/ticket-for-every-pr/probes/merge_commit/merge_commit.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

TIMEOUT = 30
LOCATION_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_INDEX_FILE",
    "GIT_COMMON_DIR",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_PREFIX",
)

HOOK = """#!/bin/sh
gd=$(git rev-parse --git-dir)
top=$(git rev-parse --show-toplevel)
{
  echo "ran"
  echo "git_dir=$gd"
  if [ -f "$gd/MERGE_HEAD" ]; then echo "merge_head=yes"; else echo "merge_head=no"; fi
  if [ -f "$top/.git/MERGE_HEAD" ]; then
    echo "top_merge_head=yes"
  else
    echo "top_merge_head=no"
  fi
  if git rev-parse -q --verify MERGE_HEAD >/dev/null; then
    echo "ref_merge_head=yes"
  else
    echo "ref_merge_head=no"
  fi
  old=$(git merge-base origin/main HEAD)
  echo "plain=$(git diff --cached --name-only --no-renames "$old" | tr '\\n' ' ')"
  if [ -f "$gd/MERGE_HEAD" ]; then
    new=$(git merge-base origin/main HEAD $(cat "$gd/MERGE_HEAD"))
    echo "with_merge_head=$(git diff --cached --name-only --no-renames "$new" | tr '\\n' ' ')"
  fi
  if git rev-parse -q --verify MERGE_HEAD >/dev/null; then
    ref=$(git merge-base origin/main HEAD MERGE_HEAD)
    echo "with_ref=$(git diff --cached --name-only --no-renames "$ref" | tr '\\n' ' ')"
  fi
} >> "$PROBE_HOOK_LOG"
exit 0
"""


def _env(log: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in LOCATION_VARS}
    env["PROBE_HOOK_LOG"] = str(log)
    env["GIT_AUTHOR_NAME"] = env["GIT_COMMITTER_NAME"] = "probe"
    env["GIT_AUTHOR_EMAIL"] = env["GIT_COMMITTER_EMAIL"] = "probe@example.invalid"
    return env


def _git(cwd: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=TIMEOUT,
        check=False,
    )


def _setup(root: Path, env: dict[str, str], *, conflict: bool) -> Path:
    """맨 원격과 클론을 만들고, 브랜치 `docs/x`와 앞서 나간 main을 둔다. 클론 경로를 돌려준다."""
    remote = root / "remote.git"
    work = root / "work"
    _git(root, env, "init", "-q", "--bare", str(remote))
    _git(root, env, "clone", "-q", str(remote), str(work))
    _git(work, env, "checkout", "-q", "-b", "main")
    (work / "queue.md").write_text("a\n", encoding="utf-8")
    _git(work, env, "add", "queue.md")
    _git(work, env, "commit", "-q", "-m", "base")
    _git(work, env, "push", "-q", "origin", "main")
    _git(work, env, "checkout", "-q", "-b", "docs/x")
    (work / "queue.md").write_text("branch\n", encoding="utf-8")
    _git(work, env, "commit", "-q", "-am", "branch edits queue")
    _git(work, env, "checkout", "-q", "main")
    if conflict:
        (work / "queue.md").write_text("main\n", encoding="utf-8")
    (work / "tools").mkdir()
    (work / "tools" / "x.py").write_text("code\n", encoding="utf-8")
    _git(work, env, "add", "-A")
    _git(work, env, "commit", "-q", "-m", "main advances")
    _git(work, env, "push", "-q", "origin", "main")
    _git(work, env, "checkout", "-q", "docs/x")
    _git(work, env, "fetch", "-q", "origin")
    hook = work / ".git" / "hooks" / "pre-commit"
    hook.write_text(HOOK, encoding="utf-8", newline="\n")
    hook.chmod(0o755)
    return work


def _read_log(log: Path) -> dict[str, str]:
    """훅 기록을 `키=값` 사전으로. 훅이 돌지 않았으면 빈 사전."""
    if not log.exists():
        return {}
    found: dict[str, str] = {}
    for line in log.read_text(encoding="utf-8").splitlines():
        if line == "ran":
            found["ran"] = "yes"
        elif "=" in line:
            key, value = line.split("=", 1)
            found[key] = value.strip()
    return found


def _resolve_and_commit(work: Path, env: dict[str, str], log: Path) -> dict[str, object]:
    """`work`에서 `origin/main`을 합쳐 충돌을 내고, 풀어 커밋한 뒤 훅 기록을 돌려준다."""
    merge = _git(work, env, "merge", "origin/main")
    conflict_seen = "CONFLICT" in merge.stdout + merge.stderr
    (work / "queue.md").write_text("resolved\n", encoding="utf-8")
    _git(work, env, "add", "queue.md")
    commit = _git(work, env, "commit", "-q", "--no-edit")
    found = _read_log(log)
    return {
        "conflict_seen": conflict_seen,
        "commit_returncode": commit.returncode,
        "hook_ran": found.get("ran") == "yes",
        "git_dir": found.get("git_dir", ""),
        "merge_head_present": found.get("merge_head") == "yes",
        "top_merge_head_present": found.get("top_merge_head") == "yes",
        "ref_merge_head_present": found.get("ref_merge_head") == "yes",
        "plain_c": found.get("plain", "").split(),
        "with_merge_head_c": found.get("with_merge_head", "").split(),
        "with_ref_c": found.get("with_ref", "").split(),
    }


def conflict_case(root: Path) -> dict[str, object]:
    log = root / "hook.log"
    env = _env(log)
    work = _setup(root, env, conflict=True)
    return _resolve_and_commit(work, env, log)


def worktree_case(root: Path) -> dict[str, object]:
    """1과 같은 충돌 병합을 클론의 링크드 워크트리에서 친다. 훅은 공유되는 클론의 것이다."""
    log = root / "hook.log"
    env = _env(log)
    work = _setup(root, env, conflict=True)
    _git(work, env, "checkout", "-q", "main")
    linked = root / "linked"
    added = _git(work, env, "worktree", "add", "-q", str(linked), "docs/x")
    result = _resolve_and_commit(linked, env, log)
    result["worktree_add_returncode"] = added.returncode
    result["dot_git_is_file"] = (linked / ".git").is_file()
    return result


def clean_case(root: Path) -> dict[str, object]:
    log = root / "hook.log"
    env = _env(log)
    work = _setup(root, env, conflict=False)
    merge = _git(work, env, "merge", "origin/main", "--no-edit")
    parents = _git(work, env, "rev-list", "--parents", "-n", "1", "HEAD").stdout.split()
    found = _read_log(log)
    return {
        "merge_returncode": merge.returncode,
        "merge_commit_parents": len(parents) - 1,
        "hook_ran": found.get("ran") == "yes",
    }


def control_case(root: Path) -> dict[str, object]:
    log = root / "hook.log"
    env = _env(log)
    work = _setup(root, env, conflict=False)
    (work / "note.md").write_text("n\n", encoding="utf-8")
    _git(work, env, "add", "note.md")
    commit = _git(work, env, "commit", "-q", "-m", "plain commit")
    found = _read_log(log)
    return {
        "commit_returncode": commit.returncode,
        "hook_ran": found.get("ran") == "yes",
        "merge_head_present": found.get("merge_head") == "yes",
        "ref_merge_head_present": found.get("ref_merge_head") == "yes",
    }


def main() -> int:
    version = subprocess.run(
        ["git", "--version"], capture_output=True, text=True, timeout=TIMEOUT, check=False
    ).stdout.strip()
    with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
        with tempfile.TemporaryDirectory() as c, tempfile.TemporaryDirectory() as d:
            conflict = conflict_case(Path(a))
            clean = clean_case(Path(b))
            control = control_case(Path(c))
            worktree = worktree_case(Path(d))
    git_dir = worktree["git_dir"]
    measured = (
        conflict["conflict_seen"] is True
        and conflict["hook_ran"] is True
        and clean["merge_commit_parents"] == 2
        and control["hook_ran"] is True
        and worktree["conflict_seen"] is True
        and worktree["hook_ran"] is True
        and worktree["dot_git_is_file"] is True
        and isinstance(git_dir, str)
        and "worktrees" in git_dir
    )
    expected = (
        measured
        and _merge_head_found(conflict)
        and conflict["top_merge_head_present"] is True
        and _merge_head_found(worktree)
        and worktree["top_merge_head_present"] is False
        and clean["hook_ran"] is False
        and control["merge_head_present"] is False
        and control["ref_merge_head_present"] is False
    )
    print(
        json.dumps(
            {
                "git": version,
                "measured": measured,
                "expected": expected,
                "conflict": conflict,
                "clean": clean,
                "control": control,
                "worktree": worktree,
            },
            ensure_ascii=False,
        )
    )
    return 0 if expected else 1


def _merge_head_found(case: dict[str, object]) -> bool:
    """git 디렉터리의 파일과 ref 이름으로 `MERGE_HEAD`를 찾았고, 두 길의 C가 `queue.md`뿐이며
    HEAD만으로 구한 C에는 main이 들여온 `tools/x.py`가 든다."""
    plain_c = case["plain_c"]
    return (
        case["merge_head_present"] is True
        and case["ref_merge_head_present"] is True
        and isinstance(plain_c, list)
        and "tools/x.py" in plain_c
        and case["with_merge_head_c"] == ["queue.md"]
        and case["with_ref_c"] == ["queue.md"]
    )


if __name__ == "__main__":
    sys.exit(main())
