"""`git commit` 의 훅이 도는 동안 그 체크아웃의 git 디렉터리에 무엇이 잠겨 있는지 잰다(대기열 293).

대기열 293 은 고치는 파일이 든 체크아웃에 커밋이 도는 중이면(그 git 디렉터리의 `index.lock`) 편집이
도는 커밋의 검사와 겹친다고 알리는 계기 훅이다. 훅을 짓기 전에 pre-commit 이 도는 동안 `index.lock`
이 있는지와, 워크트리의 git 디렉터리 자리를 잰다.

임시 폴더에 저장소 하나와 연결된 워크트리 하나를 만들고, `pre-commit`·`commit-msg` 훅을 심는다. 훅은
이 파이썬을 다시 불러(`--hook <단계>`) 그 순간의 git 디렉터리(`git rev-parse --absolute-git-dir`)와
공통 디렉터리, 두 디렉터리 바로 아래의 `*.lock`, 환경의 `GIT_DIR`·`GIT_INDEX_FILE` 을 한 줄 JSON
으로 남긴다. 갈래는 커밋의 모양 셋(`git add` 뒤의 보통 커밋, `-a`, 경로를 준 `--only`)과 자리
둘(주 체크아웃, 연결된 워크트리)을 곱한 여섯이다.

표지. 갈래마다 두 훅의 기록이 모두 남고 커밋이 HEAD 를 옮겼을 때만 측정으로 센다. 하나라도 빠진
갈래는 따로 적고 종료 코드를 1 로 둔다.

윈도 전용이 아니다. 이 저장소는 건드리지 않는다(임시 폴더에서만 git 을 부르고, 저장소를 가리키는
`GIT_*` 를 자식 환경에서 벗긴다. `.claude/rules/tools.md`). 돌리는 법(저장소 루트에서):
`PYTHONUTF8=1 uv run python .scratch/harness/probes/commit_lock/probe.py`
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_LOCATION_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_PREFIX",
)
LOG_VAR = "COMMIT_LOCK_PROBE_LOG"
CASE_VAR = "COMMIT_LOCK_PROBE_CASE"


def clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in REPO_LOCATION_VARS}


def git(cwd: Path, *args: str, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=env if env is not None else clean_env(),
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 실패: {result.stderr.strip()}")
    return result.stdout.strip()


def locks(directory: Path) -> list[str]:
    return sorted(p.name for p in directory.glob("*.lock"))


def hook(stage: str) -> int:
    """훅으로 불렸을 때. 그 순간의 잠금을 한 줄로 남긴다. 판정은 하지 않는다."""
    git_dir = Path(git(Path.cwd(), "rev-parse", "--absolute-git-dir", env=dict(os.environ)))
    common = Path(git_dir, git(Path.cwd(), "rev-parse", "--git-common-dir", env=dict(os.environ)))
    record = {
        "case": os.environ.get(CASE_VAR, "?"),
        "stage": stage,
        "git_dir": git_dir.as_posix(),
        "common_dir": common.resolve().as_posix(),
        "git_dir_locks": locks(git_dir),
        "common_dir_locks": locks(common),
        "index_lock_in_git_dir": (git_dir / "index.lock").exists(),
        "env_GIT_DIR": os.environ.get("GIT_DIR"),
        "env_GIT_INDEX_FILE": os.environ.get("GIT_INDEX_FILE"),
    }
    with open(os.environ[LOG_VAR], "a", encoding="utf-8") as log:
        log.write(json.dumps(record, ensure_ascii=False) + "\n")
    return 0


def install_hooks(common_dir: Path) -> None:
    hooks = common_dir / "hooks"
    hooks.mkdir(exist_ok=True)
    python = Path(sys.executable).as_posix()
    me = Path(__file__).resolve().as_posix()
    for stage in ("pre-commit", "commit-msg"):
        script = hooks / stage
        script.write_text(f'#!/bin/sh\nexec "{python}" "{me}" --hook {stage}\n', encoding="utf-8")
        script.chmod(0o755)


def run_case(name: str, checkout: Path, style: str, log: Path) -> dict[str, object]:
    env = clean_env()
    env[LOG_VAR] = str(log)
    env[CASE_VAR] = name
    target = checkout / f"{name}.txt"
    before = git(checkout, "rev-parse", "HEAD")
    if style == "as-is":
        target.write_text(name, encoding="utf-8")
        git(checkout, "add", target.name)
        git(checkout, "commit", "-q", "-m", name, env=env)
    elif style == "all":
        tracked = checkout / "tracked.txt"
        tracked.write_text(tracked.read_text(encoding="utf-8") + name + "\n", encoding="utf-8")
        git(checkout, "commit", "-q", "-a", "-m", name, env=env)
    else:  # only
        target.write_text(name, encoding="utf-8")
        git(checkout, "add", target.name)
        target.write_text(name + " again", encoding="utf-8")
        git(checkout, "commit", "-q", "-m", name, "--", target.name, env=env)
    after = git(checkout, "rev-parse", "HEAD")
    return {"moved": before != after}


def main() -> int:
    if len(sys.argv) == 3 and sys.argv[1] == "--hook":
        return hook(sys.argv[2])
    with tempfile.TemporaryDirectory(prefix="commit-lock-") as temp:
        root = Path(temp)
        main_checkout = root / "main"
        main_checkout.mkdir()
        git(main_checkout, "init", "-q", "-b", "main")
        git(main_checkout, "config", "user.name", "probe")
        git(main_checkout, "config", "user.email", "probe@example.invalid")
        (main_checkout / "tracked.txt").write_text("start\n", encoding="utf-8")
        git(main_checkout, "add", "tracked.txt")
        git(main_checkout, "commit", "-q", "-m", "start")
        worktree = root / "wt"
        git(main_checkout, "worktree", "add", "-q", "-b", "side", str(worktree))
        install_hooks(main_checkout / ".git")
        log = root / "hook.log"
        outcomes: dict[str, dict[str, object]] = {}
        for place, checkout in (("main", main_checkout), ("worktree", worktree)):
            for style in ("as-is", "all", "only"):
                name = f"{place}-{style}"
                outcomes[name] = run_case(name, checkout, style, log)
        records = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
        print(f"git {git(root, 'version')}")
        measured = 0
        for name, outcome in outcomes.items():
            stages = {r["stage"]: r for r in records if r["case"] == name}
            if not outcome["moved"] or set(stages) != {"pre-commit", "commit-msg"}:
                print(f"{name}: 측정 아님(커밋 이동 {outcome['moved']}, 훅 {sorted(stages)})")
                continue
            measured += 1
            for stage in ("pre-commit", "commit-msg"):
                r = stages[stage]
                print(
                    f"{name} {stage}: index.lock={r['index_lock_in_git_dir']} "
                    f"git_dir_locks={r['git_dir_locks']} common_locks={r['common_dir_locks']} "
                    f"GIT_DIR={r['env_GIT_DIR']} GIT_INDEX_FILE={r['env_GIT_INDEX_FILE']} "
                    f"git_dir={r['git_dir'].removeprefix(root.as_posix())}"
                )
        print(f"측정 {measured}/{len(outcomes)}")
        return 0 if measured == len(outcomes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
