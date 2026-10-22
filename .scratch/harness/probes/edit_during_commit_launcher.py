"""대기열 368. `hook_edit_during_commit` 이 다른 저장소에 친 `git -C <임시> commit` 을 띄운 폴더(이
체크아웃)의 커밋으로 잘못 세는 순간이 있는지, 있으면 어느 프로세스의 어느 순간인지 잰다.

회차. 임시 저장소에 `git -C <임시> commit --allow-empty` 하나를 친다. 띄운 폴더(작업 디렉터리)는 이
체크아웃이다. 그동안 훑는 스레드가 훅의 `scan_processes` 를 쉬지 않고 돌아, 훑기마다 판정 둘을 낸다.
- 지금 판: 훅의 `running_commits`.
- 옛 판: 대기열 368 전의 `running_commits` 를 이 파일에 옮긴 `old_running_commits`(자식 git 을 띄운
  git 만 거르고 작업 디렉터리로 체크아웃을 찾는다).
두 판 모두 그 회차의 꼬리표(`-m` 의 값)가 든 프로세스를 이 체크아웃의 커밋으로 세면 거짓 알림이다.

갈래. 실행 파일 셋(런처 `cmd\\git.exe`, 런처 `bin\\git.exe`, 실제 git `mingw64\\bin\\git.exe`) ×
`-C` 의 꼴 둘(절대 경로, 이 체크아웃에서 본 상대 경로) × 부하 둘(없음, CPU 수만큼 도는 파이썬).

표지. 훑기가 그 회차의 꼬리표가 든 git 프로세스를 한 번이라도 봤고 커밋이 0 으로 끝났다. 아니면 그
회차는 측정이 아니다(`tools/probe_kit.py` 의 `Rounds`). 옛 판이 거짓 알림을 낸 회차가 지금 판의
고친 길을 지난 회차다(`.claude/rules/probes.md` 첫 항목, 대기열 367).

거짓 알림의 순간. 옛 판이 센 프로세스가 띄운 프로세스(pid 가 같다)면, 그 회차의 앞선 훑기에서
그것을 부모로 둔 git 을 봤는지로 "자식 전"과 "자식 뒤"를 가른다. 띄운 프로세스의 자식이면 "자식
git" 이다. 실제 git 을 바로 띄운 갈래의 "자식 전"은 그 git 이 `-C` 를 풀어 작업 디렉터리를 옮기기
전의 순간이다.

쓰임: 저장소 루트에서
`PYTHONUTF8=1 uv run python .scratch/harness/probes/edit_during_commit_launcher.py [회차]`
(기본 60). 윈도에서만 잰다. 임시 폴더에서만 커밋한다. 부하 프로세스는 이 탐침이 띄운 `Popen` 으로만
끈다.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.hook_edit_during_commit import (  # noqa: E402
    Process,
    RunningCommit,
    checkout_of,
    git_subcommand,
    is_git,
    running_commits,
    scan_processes,
)
from tools.probe_kit import Rounds  # noqa: E402
from tools.run_hooks import REPO_LOCATION_VARS  # noqa: E402

TAG = "probe368"


def old_running_commits(processes: list[Process]) -> list[RunningCommit]:
    """대기열 368 전의 판정. 자식 git 을 띄운 git 만 거르고 작업 디렉터리로 체크아웃을 찾는다."""
    gits = [process for process in processes if is_git(process.image)]
    launchers = {process.parent for process in gits} & {process.pid for process in gits}
    found: list[RunningCommit] = []
    for process in gits:
        if process.pid in launchers or git_subcommand(process.argv) != "commit":
            continue
        checkout = checkout_of(process.cwd)
        if checkout is not None:
            found.append(RunningCommit(process.pid, checkout))
    return found


@dataclass
class Scan:
    """훑기 하나에서 꼬리표가 든 프로세스(pid → 부모 pid)와 두 판이 이 체크아웃으로 센 pid."""

    tagged: dict[int, int]
    old_false: set[int]
    new_false: set[int]


@dataclass
class Scanner:
    """쉬지 않고 훑어 꼬리표마다 훑기를 모은다."""

    checkout: str
    scans: dict[str, list[Scan]] = field(default_factory=dict[str, list[Scan]])
    stop: threading.Event = field(default_factory=threading.Event)
    errors: list[str] = field(default_factory=list[str])

    def run(self) -> None:
        while not self.stop.is_set():
            try:
                self.scan_once()
            except Exception as error:  # 훑기 하나의 실패가 측정 전체를 멈추지 않게
                self.errors.append(repr(error))

    def scan_once(self) -> None:
        processes = scan_processes() or []
        old = {c.pid for c in old_running_commits(processes) if self._same(c.checkout)}
        new = {c.pid for c in running_commits(processes) if self._same(c.checkout)}
        by_tag: dict[str, dict[int, int]] = {}
        for process in processes:
            for word in process.argv:
                if word.startswith(TAG):
                    by_tag.setdefault(word, {})[process.pid] = process.parent
        for tag, tagged in by_tag.items():
            pids = set(tagged)
            scan = Scan(tagged, old & pids, new & pids)
            self.scans.setdefault(tag, []).append(scan)

    def _same(self, checkout: str) -> bool:
        return os.path.normcase(checkout) == os.path.normcase(self.checkout)


def moment(scans: list[Scan], index: int, pid: int, launched: int) -> str:
    """옛 판이 센 pid 의 순간."""
    if pid != launched:
        return "자식 git"
    child_before = any(parent == pid for scan in scans[:index] for parent in scan.tagged.values())
    return "띄운 프로세스, 자식 뒤" if child_before else "띄운 프로세스, 자식 전"


def git_executables() -> dict[str, Path]:
    completed = subprocess.run(
        ["git", "--exec-path"], capture_output=True, text=True, check=True, timeout=30
    )
    mingw = Path(completed.stdout.strip()).parents[1]  # <루트>/mingw64/libexec/git-core
    root = mingw.parent
    return {
        "런처 cmd": root / "cmd" / "git.exe",
        "런처 bin": root / "bin" / "git.exe",
        "실제 git": mingw / "bin" / "git.exe",
    }


def clean_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if key not in REPO_LOCATION_VARS}


def init_repo(repo: Path, env: dict[str, str]) -> None:
    repo.mkdir(parents=True)
    for args in (
        ["init", "-q"],
        ["config", "user.email", "probe@example.invalid"],
        ["config", "user.name", "probe"],
        ["config", "gc.auto", "0"],
        ["config", "maintenance.auto", "false"],
    ):
        subprocess.run(["git", *args], cwd=repo, env=env, check=True, timeout=30)


def start_load() -> list[subprocess.Popen[bytes]]:
    return [
        subprocess.Popen(
            [sys.executable, "-c", "while True: pass"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(os.cpu_count() or 4)
    ]


def stop_load(load: list[subprocess.Popen[bytes]]) -> None:
    for process in load:
        process.kill()
    for process in load:
        process.wait(timeout=30)


def run_branch(
    name: str, executable: Path, target: str, repo: Path, runs: int, *, loaded: bool
) -> tuple[int, str]:
    env = clean_env()
    scanner = Scanner(str(ROOT))
    thread = threading.Thread(target=scanner.run, daemon=True)
    load = start_load() if loaded else []
    thread.start()
    rounds = Rounds()
    old_moments: Counter[str] = Counter()
    new_moments: Counter[str] = Counter()
    fixed_path_rounds = 0
    try:
        for index in range(runs):
            tag = f"{TAG}-{name.replace(' ', '_')}-{index}"
            with rounds.round(f"{index + 1}회차") as current:
                process = subprocess.Popen(
                    [str(executable), "-C", target, "commit", "--allow-empty", "-q", "-m", tag],
                    cwd=ROOT,
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
                _, stderr = process.communicate(timeout=120)
                time.sleep(0.05)  # 끝난 뒤의 훑기 하나까지 기다린다
                scans = scanner.scans.pop(tag, [])
                if process.returncode != 0:
                    current.mark(measured=False, result=f"커밋 실패 {stderr!r}")
                    continue
                if not scans:
                    current.mark(measured=False, result="꼬리표가 든 프로세스를 훑지 못했다")
                    continue
                old_hits = [
                    moment(scans, i, pid, process.pid)
                    for i, scan in enumerate(scans)
                    for pid in scan.old_false
                ]
                new_hits = [
                    moment(scans, i, pid, process.pid)
                    for i, scan in enumerate(scans)
                    for pid in scan.new_false
                ]
                old_moments.update(old_hits)
                new_moments.update(new_hits)
                fixed_path_rounds += bool(old_hits)
                if new_hits:
                    result = "지금 판 거짓 알림"
                elif old_hits:
                    result = "옛 판만 거짓 알림"
                else:
                    result = "둘 다 침묵"
                current.mark(measured=True, result=result)
    finally:
        scanner.stop.set()
        thread.join(timeout=30)
        stop_load(load)
    lines = [
        f"## {name}",
        rounds.summary(),
        f"옛 판이 거짓 알림을 낸 회차(고친 길을 지난 회차): {fixed_path_rounds}",
        f"옛 판 거짓 알림의 순간(훑기 수): {dict(old_moments)}",
        f"지금 판 거짓 알림의 순간(훑기 수): {dict(new_moments)}",
    ]
    if scanner.errors:
        lines.append(f"훑기 오류 {len(scanner.errors)}건, 첫 것: {scanner.errors[0]}")
    return rounds.exit_code() | bool(scanner.errors), "\n".join(lines)


def main(argv: list[str]) -> int:
    if sys.platform != "win32":
        print("윈도에서만 잰다")
        return 2
    runs = int(argv[1]) if len(argv) > 1 else 60
    executables = git_executables()
    scratch = Path(tempfile.mkdtemp(prefix="edit-commit-launcher-"))
    exit_code = 0
    try:
        repo = scratch / "repo"
        init_repo(repo, clean_env())
        targets = {"절대": str(repo), "상대": os.path.relpath(repo, ROOT)}
        print(f"git: {executables}, 상대 -C: {targets['상대']}")
        for executable_name, executable in executables.items():
            for target_name, target in targets.items():
                for loaded in (False, True):
                    name = f"{executable_name} {target_name} {'부하' if loaded else '맨'}"
                    code, report = run_branch(name, executable, target, repo, runs, loaded=loaded)
                    print(report, flush=True)
                    exit_code |= code
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
