"""다시 풀기 회차의 자리. 회차 하나를 열기 전에 짓는 것과, 회차가 끝난 뒤 사람이 부르는 지우기.

명세는 `.scratch/model-rerun/spec.md`의 "클론과 설정 폴더"·"명령과 막는 규칙"·"자리와 모듈"이고
티켓은 `.scratch/model-rerun/issues/04-round-clone.md`다. 같은 일을 프로브 크기로 한 것은
`.scratch/model-rerun/probes/headless_flags/headless_flags.py`의 `layout`·`allowed_env`·
`ancestors_with_claude_dir`·`remove_tree`다. 세션을 띄우는 것(06), 게이트(07), 과제와 회차의
차례(10)는 이 모듈의 함수를 가져다 쓴다.

짓는 차례.
1. `checked_root`: 사람이 명령 줄로 준 뿌리가 절대 경로이고, 주 체크아웃(`git worktree list`의 첫
   줄)과 사용자의 `~/.claude`를 경로 조각 단위로 머리로 갖지 않고, 그 아래 회차 폴더의 상위에
   `.claude/`(홈의 것은 뺀다)와 `CLAUDE.md`·`CLAUDE.local.md`가 없는지 본다. 머리 견줌은 링크를 풀지
   않은 꼴(`abspath`)과 링크를 푼 꼴(`realpath`)을 둘 다 본다. 윈도의 `abspath`는 윈도가 그 경로를
   열 때처럼 마지막 조각에서는 끝의 점과 공백을 모두 떼고, 가운데 조각에서는 끝에 점이 꼭 하나일
   때만 그 점을 뗀다. 그래서 `agent.\\x`는 `agent` 아래로 읽는다. `realpath`의 꼴은
   장치 접두(`\\\\?\\`)를 떼고 견준다. 전용 설정 폴더는 `checked_place`로 앞의 둘만 본다.
2. `create_round_dir`: 뿌리 아래 `<과제 id>-<갈래>-<회차 번호>-<짧은 난수>`(이름은
   `tools/rerun_files.py`의 `round_dir_name`)를 만들고 곧바로 표지 파일을 심는다. 폴더가 이미 있으면
   덮지 않고 `FileExistsError`다. 부르는 쪽(10)은 회차 번호를 잡자마자 이 함수만 차례로 부르고,
   아래 3은 회차마다 따로 돈다.
3. `prepare_round`: 원본 저장소에서 B를 bare 저장소의 `main`으로만 밀고(태그와 다른 ref는 밀지
   않는다) 그것을 클론한 뒤, 클론과 bare의 모든 ref가 B이고 M이 닿지도 들지도 않는지 대 본다
   (`build_clone`, `check_clone`). 클론의 `.claude/settings.local.json`에 막는 규칙을 쓰고
   (`write_deny_rules`, 규칙은 `deny_rules`), 준비 명령을 클론에서 차례로 돌린다(`run_setup`).
4. `session_env`: 세션에 넘길 환경을 허용 목록으로 짓는다.

준비의 시간은 회차의 벽시계에 들지 않는다. `run_setup`이 내는 `wall_clock_from`은 마지막 준비
명령이 끝난 뒤의 단조 시계 값이고, 회차의 벽시계는 거기서 잰다. 준비 명령 하나라도 0이 아니게
끝나면 남은 명령을 돌리지 않고 어느 명령이 몇으로 끝났는지를 낸다. 러너를 멈추는 것은 10이다.

지우기(`remove_round_dirs`, 명령 줄 `remove`)는 사람이 부른다. 뿌리 바로 아래에서 링크가 아닌
폴더이고, 이름이 회차 폴더 꼴이며, 표지가 그 폴더 이름을 담은 보통 파일이고, `records/`에 그 회차의
기록이 있어 그 기록의 회차 폴더 이름이 이 폴더인 것만 지운다. 기록이 없는 회차 폴더는 비용이 아직
원본에만 있어 남긴다(명세 "차례, 동시성, 예산"의 2026-10-23 주석). 지울 때는 먼저 안의 링크
(심볼릭 링크, junction)를 링크만 끊고(선례 `tools/canary.py`의 `_cut_links`), 표지를 뺀 항목을
지운 뒤 표지를 맨 끝에 지운다(`tools/tidy_checkouts.py`의 `delete_path`). 그래서 지우다 막혀도
표지가 남아 다시 부르면 마저 지운다. 안을 다 지운 뒤 빈 폴더만 지우지 못하면(다른 프로세스가 작업
디렉터리로 쥐었다) 표지를 다시 심고, 윈도에서 폴더의 읽기 전용 특성에 막히면 특성을 풀고 한 번 더
지운다. 표지는 글자 그대로의 이름으로 찾는다. 이름은 디스크에서 읽은 글자 그대로 `\\\\?\\` 꼴로
다뤄, 윈도가 끝의 점과 공백을 떼어 다른 폴더를 가리키는 일이 없다. 이 판정들은 커밋 전에 임시 폴더의
반박 검증(링크와 junction, 커밋하지 않은 파일, 윈도가 바꾸는 이름, 표지의 꼴, 홈 같은 뿌리, 긴 경로,
명령 줄의 경로 꼴)을 거쳤다(일지 2026-10-23-32).

git을 띄우는 자리는 `tools.run_hooks.REPO_LOCATION_VARS`를 자식 환경에서 벗긴다(`.claude/rules/
tools.md`의 pre-commit 항목). 하위 프로세스마다 시간 제한이 있다.

못 보는 것.
- 회차 폴더의 상위에서 찾는 것은 `.claude/` 폴더와 `CLAUDE.md`·`CLAUDE.local.md`다. 홈의
  `.claude/`는 기본 설정 폴더라 늘 있어 세지 않는다(프로브와 같다). 그 폴더에 든 `CLAUDE.md`가
  세션에 실리는지는 재지 않았고, 파일럿(11)이 시작 컨텍스트로 본다. 뿌리의 상위를 고친 때(회차를 연
  뒤 `.claude/`를 만든 때)는 다시 보지 않는다.
- 막는 규칙의 경로 꼴(`Read(//c/…/**)`)은 프로브가 읽기에서 막는 것을 본 꼴이고, 쓰기·편집 규칙과
  도구 이름만 쓴 규칙은 재지 않았다(파일럿이 본다). 같은 뿌리 아래 다른 회차 폴더와 전용 설정
  폴더의 세션 기록은 막지 않는다. 함께 도는 갈래나 앞선 갈래의 풀이를 읽는 길이고, 명세의 목록에
  없다.
- 준비 명령이 시간을 넘기면 그 명령의 프로세스만 끈다(`subprocess.run`의 시간 제한). 그 명령이 띄운
  자식(node 등)은 남을 수 있고, 그것이 클론의 파일을 쥐면 지우기가 그 회차 폴더를 지우지 못했다고
  보고한다. 찾지 못한 준비 명령은 `SetupEnd.NOT_STARTED`(종료 코드는 빈 값)로 실패다.
- 원본 저장소의 `init.templateDir` 같은 사용자 전역 git 설정이 bare와 클론에 들이는 것은 보지
  않는다.
- 뿌리 바로 아래의 링크는 따라가지도 끊지도 않고 회차 폴더가 아니라고 보고한다. 지우기 직전에 그
  이름이 링크인지 한 번 더 보지만, 그 뒤에 같은 사용자의 다른 프로세스가 그 폴더를 링크로 바꾸는
  일은 막지 않는다. 뿌리 자체나 `records/`가 링크면 따라간다(뿌리는 링크를 푼 꼴도 머리 견줌을
  거친다). 대상을 잃은 링크인 뿌리는 없는 뿌리로 읽는다.
- 윈도에서 회차 폴더 안의 읽기 전용 파일이 바깥 파일의 하드 링크면(uv·pnpm 캐시가 하드 링크로 채울
  수 있다), 지우려고 푼 읽기 전용 특성이 바깥 파일에도 남는다. 내용은 남는다. 리눅스는 읽기 전용
  파일도 특성을 풀지 않고 지운다. 캐시의 파일이 읽기 전용인지는
  재지 않았다(커밋 전 반박 검증이 일부러 만든 하드 링크로 봤다).
- 회차 폴더 안의 링크를 먼저 끊는 것은 두 번째 지킴이다. 이 PC(파이썬 3.12)의 `shutil.rmtree`는
  junction을 따라가지 않아, 끊지 않아도 바깥 파일이 남았다(`.scratch/model-rerun/probes/
  rerun_round_mutations.toml`의 대조군). 끊지 못한 링크나 읽지 못한 폴더가 있으면, 끊을 수 있던
  링크는 이미 끊은 채 파일과 폴더는 하나도 지우지 않고 멈춘다.
- 경로 견줌은 리눅스에서도 `\\`를 구분자로 읽는다. 이름에 `\\`가 든 폴더는 다른 경로와 같게 읽혀
  거부될 수 있다(막는 쪽으로 틀린다).
- 윈도에서 `agent \\x`·`agent..\\x`는 가운데 조각의 끝을 떼지 않아 이름이 다른 폴더를 열고, 그
  경로가 있으면 받는다. 그 경로가 없으면 `realpath`가 부모 쪽으로 풀며 그 조각을 마지막 조각처럼
  열어 끝을 떼므로 `agent` 아래로 읽어 거부한다(막는 쪽으로 틀린다). `agent` 아래에 같은 이름의
  자식(`agent\\x`)이 있든 없든 같다.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import secrets
import shutil
import stat
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path, PurePath, PureWindowsPath
from typing import BinaryIO

from tools.rerun_files import (
    SETUP_COMMANDS,
    ShapeError,
    parse_round_dir_name,
    read_record,
    record_file_name,
    round_dir_name,
)
from tools.run_hooks import REPO_LOCATION_VARS
from tools.tidy_checkouts import delete_path, long_path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / ".scratch" / "model-rerun" / "probes" / "records"

# 회차 폴더의 표지. 이 도구만 쓰는 이름이고 내용은 그 회차 폴더의 이름이다.
MARKER = ".agent-os-rerun-round"
_MARKER_MAX_BYTES = 256
# 회차 폴더 안에서 띄우기 전에 그 호출의 세션 id를 한 줄씩 덧붙이는 파일. 다시 뜬 러너(10)가 죽은
# 러너가 남긴 회차에서 init 전에 죽은 호출까지 세션 id를 찾는다(명세 "차례, 동시성, 예산"의
# 2026-10-23 주석).
SESSION_IDS = "session-ids.txt"

GIT_TIMEOUT = 300  # git 호출 하나(원본에서 bare로 밀기와 클론이 가장 길다)
# 준비 명령 하나. `uv sync`가 `.venv`를 복사로 채우면 2분을 넘길 수 있다(`docs/constitution/
# operations.md`, 복사 105~148초).
SETUP_TIMEOUT = 1800

# 준비 명령의 인자 목록. 명세 "준비"의 셋이고 글은 `tools/rerun_files.py`의 `SETUP_COMMANDS`다.
SETUP_ARGV: tuple[tuple[str, ...], ...] = tuple(tuple(c.split(" ")) for c in SETUP_COMMANDS)

# --- 막는 규칙(명세 "명령과 막는 규칙") ---

# 경로가 들지 않는 규칙. 꼴은 프로브가 막는 것을 본 꼴(`Bash(<접두>:*)`, `Bash(*<글>*)`,
# `Skill(<이름>)`)이다.
FIXED_DENY_RULES = (
    "Bash(gh:*)",
    "Bash(git push:*)",
    "Skill(open-session)",
    "Bash(*open_session.ps1*)",
    "Bash(*claude://*)",
)
# 통째로 막는 도구. 웹 도구 둘과 바깥 상태를 바꾸는 도구다.
BLOCKED_TOOLS = (
    "WebFetch",
    "WebSearch",
    "SendMessage",
    "ListAgents",
    "RemoteTrigger",
    "PushNotification",
    "DesignSync",
    "CronCreate",
    "ScheduleWakeup",
)
# 주 체크아웃과 사용자의 `~/.claude`에 거는 도구.
PATH_TOOLS = ("Read", "Edit", "Write")

# --- 세션 환경(설계 5절 환경 변수와 명세의 윈도 기본값·캐시 변수) ---

CONFIG_DIR_VAR = "CLAUDE_CONFIG_DIR"
AUTOUPDATER_VAR = "DISABLE_AUTOUPDATER"
GH_CONFIG_VAR = "GH_CONFIG_DIR"
# 허용 목록. 러너가 값을 짓는 둘(설정 폴더, 자동 업데이트 끔)을 빼면 부모 환경에 있는 것만 넘긴다.
ALLOWED_ENV = (
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "SystemDrive",
    "WINDIR",
    "COMSPEC",
    "USERPROFILE",
    "HOME",
    "HOMEDRIVE",
    "HOMEPATH",
    "APPDATA",
    "LOCALAPPDATA",
    "PROGRAMDATA",
    "ProgramFiles",
    "ProgramFiles(x86)",
    "TEMP",
    "TMP",
    "UV_CACHE_DIR",
    "UV_PYTHON_INSTALL_DIR",
    "PNPM_HOME",
    "XDG_CACHE_HOME",
    CONFIG_DIR_VAR,
    AUTOUPDATER_VAR,
)
# 러너가 값을 지어 넣는 이름. 셋째는 허용 목록 밖에서 더하는 회차 폴더의 빈 gh 설정 폴더다.
RUNNER_SET_ENV = (CONFIG_DIR_VAR, AUTOUPDATER_VAR, GH_CONFIG_VAR)


class PlaceError(ValueError):
    """뿌리나 설정 폴더로 쓸 수 없는 경로."""


class CloneError(RuntimeError):
    """git 호출이 실패했거나(bare와 클론 짓기, 주 체크아웃 찾기), 지은 클론에 B 뒤의 것이 있다."""


# --- 뿌리와 설정 폴더 ---


def _without_device_prefix(text: str) -> str:
    """윈도 `realpath`가 남긴 장치 접두(`\\\\?\\`, `\\\\?\\UNC\\`)를 뗀다. 없는 경로를 풀면 처음
    오류와 접두를 뗀 경로의 오류가 다를 때 접두를 남겨, 그 꼴이 머리와 맞지 않았다(PR 직전 리뷰)."""
    if text.startswith("\\\\?\\UNC\\"):
        return "\\\\" + text[len("\\\\?\\UNC\\") :]
    if text.startswith("\\\\?\\"):
        return text[len("\\\\?\\") :]
    return text


def _forms(path: str | os.PathLike[str]) -> set[tuple[str, ...]]:
    """경로를 조각으로 나눈 꼴들. 윈도가 실제로 쓸 경로(`abspath`. 마지막 조각은 끝의 점과 공백을
    모두 떼고, 가운데 조각은 끝에 점이 꼭 하나일 때만 그 점을 뗀다)와 링크를 푼 경로(`realpath`.
    장치 접두를 뗀다)를 둘 다 낸다. 조각은 대소문자를 접고 `/`·`\\`를 가리지 않는다."""
    texts = {os.path.abspath(path), _without_device_prefix(os.path.realpath(path))}
    return {tuple(s for s in t.replace("\\", "/").casefold().split("/") if s) for t in texts}


def _under(path: str | os.PathLike[str], head: Path) -> bool:
    """`path`가 `head`이거나 그 아래인지. 두 꼴 가운데 하나라도 그러면 그렇다."""
    heads = _forms(head)
    return any(p[: len(h)] == h for p in _forms(path) for h in heads)


def checked_place(text: str, what: str, *, main_checkout: Path, user_claude: Path) -> Path:
    """절대 경로이고 주 체크아웃과 `~/.claude`를 머리로 갖지 않으면 그 경로. 아니면 `PlaceError`.

    구분자 둘로 시작하는 경로(`\\\\?\\`·`\\\\.\\` 장치 경로와 그 섞인 꼴, `\\\\localhost\\C$` 같은
    UNC)는 받지 않는다. `realpath`를 거쳐도 드라이브 문자 경로와 같은 조각으로 풀리지 않아 머리
    견줌을 비켜 갔다(커밋 전 반박 검증)."""
    if text[:2].replace("\\", "/") == "//" or not Path(text).is_absolute():
        raise PlaceError(f"{what}는 구분자 둘로 시작하지 않는 절대 경로여야 한다: {text!r}")
    if _under(text, main_checkout):
        raise PlaceError(f"{what}가 주 체크아웃 {main_checkout} 아래다: {text!r}")
    if _under(text, user_claude):
        raise PlaceError(f"{what}가 사용자의 ~/.claude({user_claude}) 아래다: {text!r}")
    return Path(text)


def _same(a: Path, b: Path) -> bool:
    return bool(_forms(a) & _forms(b))


def claude_files_above(path: Path, *, home: Path) -> list[Path]:
    """`path`의 상위 폴더(그 자신은 뺀다)에 있는 `.claude/` 폴더와 `CLAUDE.md`·`CLAUDE.local.md`.
    홈의 `.claude/`는 뺀다. 링크를 푼 경로의 상위도 본다."""
    parents: list[Path] = []
    for text in (os.path.abspath(path), os.path.realpath(path)):
        parents += [p for p in Path(text).parents if p not in parents]
    found: list[Path] = []
    for parent in parents:
        if (parent / ".claude").is_dir() and not _same(parent, home):
            found.append(parent / ".claude")
        found += [parent / n for n in ("CLAUDE.md", "CLAUDE.local.md") if (parent / n).exists()]
    return found


def checked_root(text: str, *, main_checkout: Path, home: Path) -> Path:
    """회차 폴더의 뿌리. `checked_place`에 더해 그 아래 회차 폴더의 상위(뿌리와 그 상위)에서
    `claude_files_above`가 찾는 것이 있으면 `PlaceError`다."""
    root = checked_place(text, "뿌리", main_checkout=main_checkout, user_claude=home / ".claude")
    found = claude_files_above(root / "회차 폴더", home=home)
    if found:
        listed = ", ".join(str(p) for p in found)
        raise PlaceError(f"회차 폴더의 상위에 .claude/ 나 CLAUDE.md 가 있다: {listed}")
    return root


def main_checkout(repo: Path) -> Path:
    """`repo`가 든 저장소의 주 체크아웃(`git worktree list`의 첫 줄)."""
    out = _git(repo, "worktree", "list", "--porcelain")
    for line in out.splitlines():
        if line.startswith("worktree "):
            return Path(line.removeprefix("worktree "))
    raise CloneError(f"git worktree list 에 체크아웃이 없다: {repo}")


# --- 회차 폴더 ---


@dataclass(frozen=True)
class RoundDir:
    """회차 폴더 하나와 그 안의 자리."""

    path: Path

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def bare(self) -> Path:
        return self.path / "bare.git"

    @property
    def clone(self) -> Path:
        return self.path / "clone"

    @property
    def stream(self) -> Path:
        """원본 stream-json의 자리."""
        return self.path / "stream"

    @property
    def gh_config(self) -> Path:
        """세션의 `GH_CONFIG_DIR`. 빈 폴더다."""
        return self.path / "gh"

    @property
    def setup_log(self) -> Path:
        return self.path / "setup.log"

    @property
    def session_ids(self) -> Path:
        """띄우기 전에 세션 id를 덧붙여 적는 파일(`SESSION_IDS`)."""
        return self.path / SESSION_IDS


def _plant_marker(folder: str | os.PathLike[str]) -> None:
    """`folder`에 표지를 심는다. 내용은 그 폴더의 이름이다. 이미 있으면 `FileExistsError`다."""
    with open(os.path.join(folder, MARKER), "x", encoding="utf-8", newline="") as f:
        f.write(os.path.basename(folder))


def create_round_dir(
    root: Path, task_id: str, arm: str, round_no: int, *, token: str | None = None
) -> RoundDir:
    """뿌리 아래 회차 폴더를 만들고 곧바로 표지를 심는다. 이미 있으면 `FileExistsError`다.
    `token`을 주지 않으면 짧은 난수를 짓는다. 뿌리는 `checked_root`가 본 것이어야 한다."""
    name = round_dir_name(task_id, arm, round_no, token or secrets.token_hex(4))
    root.mkdir(parents=True, exist_ok=True)
    place = RoundDir(root / name)
    place.path.mkdir()
    _plant_marker(place.path)
    place.gh_config.mkdir()
    place.stream.mkdir()
    return place


# --- bare와 클론 ---


def _git_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in REPO_LOCATION_VARS}
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _git(cwd: Path, *args: str, stdin: str | None = None) -> str:
    """git 하나의 표준 출력. 실패하거나 시간을 넘기면 `CloneError`다."""
    try:
        done = subprocess.run(
            ["git", *args],
            cwd=cwd,
            env=_git_env(),
            input=stdin,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
            timeout=GIT_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired) as e:
        raise CloneError(f"git {' '.join(args)}: {e}") from e
    if done.returncode != 0:
        raise CloneError(f"git {' '.join(args)} 이 {done.returncode}: {done.stderr.strip()}")
    return done.stdout.strip()


def _git_logged(cwd: Path, log: Path, *args: str) -> None:
    """출력이 필요 없는 git 하나. 출력은 `log`에 덧붙인다. 손자 프로세스가 파이프를 쥐어 시간
    제한 뒤에도 돌아오지 않는 일이 없게 파이프를 쓰지 않는다(`.claude/rules/tools.md`)."""
    with open(log, "ab") as out:
        out.write(f"$ git {' '.join(args)}\n".encode())
        out.flush()
        try:
            done = subprocess.run(
                ["git", *args],
                cwd=cwd,
                env=_git_env(),
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=GIT_TIMEOUT,
            )
        except (OSError, subprocess.TimeoutExpired) as e:
            raise CloneError(f"git {' '.join(args)}: {e}") from e
    if done.returncode != 0:
        raise CloneError(f"git {' '.join(args)} 이 {done.returncode}(출력은 {log})")


def build_clone(source: Path, base: str, merge: str, place: RoundDir) -> None:
    """`source`에서 B를 bare의 `main`으로만 밀고 그것을 클론한 뒤 `check_clone`으로 대 본다.

    태그는 사용자 설정(`push.followTags`)이 켜도 밀지 않는다. 원본의 pre-push 훅은 돌리지 않는다.
    클론의 원격 이름은 사용자 설정(`clone.defaultRemoteName`)과 상관없이 `origin`이다.
    """
    log = place.path / "git.log"
    _git_logged(place.path, log, "init", "-q", "--bare", "-b", "main", str(place.bare))
    _git_logged(
        source,
        log,
        "-c",
        "push.followTags=false",
        "push",
        "-q",
        "--no-verify",
        "--no-follow-tags",
        str(place.bare),
        f"{base}:refs/heads/main",
    )
    _git_logged(
        place.path, log, "clone", "-q", "--origin", "origin", str(place.bare), str(place.clone)
    )
    check_clone(place, base, merge)


_REFS = ("for-each-ref", "--format=%(objectname) %(refname)")


def check_clone(place: RoundDir, base: str, merge: str) -> None:
    """클론과 bare에서 모든 ref와 HEAD가 B이고, M이 `rev-list --all`에 없고 개체로도 없는지 본다.
    하나라도 아니면 `CloneError`다. 세션은 bare를 `../bare.git`으로 읽을 수 있어 bare도 본다."""
    for where in (place.clone, place.bare):
        refs = [line.split(" ", 1) for line in _git(where, *_REFS).splitlines()]
        if not refs:
            raise CloneError(f"{where.name} 에 ref 가 없다")
        wrong = [ref for sha, ref in refs if sha != base]
        if wrong:
            raise CloneError(f"{where.name} 의 ref 가 B 가 아니다: {', '.join(wrong)}")
        if _git(where, "rev-parse", "HEAD") != base:
            raise CloneError(f"{where.name} 의 HEAD 가 B 가 아니다")
        if merge in _git(where, "rev-list", "--all").split():
            raise CloneError(f"{where.name} 의 ref 에서 M 이 닿는다")
        if not _git(where, "cat-file", "--batch-check", stdin=merge + "\n").endswith(" missing"):
            raise CloneError(f"{where.name} 에 M 개체가 있다")


# --- 막는 규칙 ---


def _rule_path(path: PurePath) -> str:
    """권한 규칙의 절대 경로 꼴. 윈도의 `C:\\a\\b`는 `//c/a/b`, POSIX의 `/a/b`는 `//a/b`다."""
    posix = path.as_posix()
    drive = path.drive
    if isinstance(path, PureWindowsPath) or drive:
        if len(drive) != 2 or drive[1] != ":":
            raise PlaceError(f"드라이브 문자가 없는 경로는 규칙으로 쓰지 않는다: {path}")
        return f"//{drive[0].lower()}{posix[2:]}"
    if not posix.startswith("/"):
        raise PlaceError(f"절대 경로가 아니다: {path}")
    return f"/{posix}"


def deny_heads(main_checkout: Path, *, home: Path) -> tuple[Path, ...]:
    """막는 규칙을 걸 경로. 주 체크아웃과 사용자의 `~/.claude`이고, 링크를 푼 꼴이 다르면 그것도
    든다."""
    heads: list[Path] = []
    for head in (main_checkout, home / ".claude"):
        for text in (os.path.abspath(head), os.path.realpath(head)):
            if Path(text) not in heads:
                heads.append(Path(text))
    return tuple(heads)


def deny_rules(heads: Sequence[PurePath]) -> list[str]:
    """클론의 `permissions.deny`. 고정 규칙, 경로마다 읽기·편집·쓰기, 막는 도구의 차례다."""
    rules: list[str] = list(FIXED_DENY_RULES)
    for head in heads:
        where = _rule_path(head)
        rules.extend(f"{tool}({where}/**)" for tool in PATH_TOOLS)
    rules.extend(BLOCKED_TOOLS)
    return list(dict.fromkeys(rules))


def write_deny_rules(clone: Path, rules: Sequence[str]) -> None:
    """클론의 `.claude/settings.local.json`에 막는 규칙을 쓴다. B의 `.claude/settings.json`은 고치지
    않는다. 이미 있으면 덮지 않고 `CloneError`다. 그 파일이 세션의 `git status`에 보여 커밋되지
    않게 클론의 `.git/info/exclude`에 더한다."""
    local = clone / ".claude" / "settings.local.json"
    if os.path.lexists(local):
        raise CloneError(f"클론에 이미 settings.local.json 이 있다: {local}")
    local.parent.mkdir(exist_ok=True)
    text = json.dumps({"permissions": {"deny": list(rules)}}, ensure_ascii=False, indent=2)
    with open(local, "x", encoding="utf-8", newline="\n") as f:
        f.write(text + "\n")
    exclude = clone / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with open(exclude, "a", encoding="utf-8", newline="\n") as f:
        f.write("\n/.claude/settings.local.json\n")


# --- 준비 ---


class SetupEnd(Enum):
    """실패한 준비 명령이 끝난 꼴."""

    EXITED = "exited"  # 0이 아닌 종료 코드로 끝났다
    TIMED_OUT = "timed_out"  # 시간을 넘겨 껐다
    NOT_STARTED = "not_started"  # 명령을 찾지 못했거나 띄우지 못했다


@dataclass(frozen=True)
class SetupFailed:
    """0이 아니게 끝난 준비 명령."""

    index: int  # 준비 명령의 차례(0부터)
    command: str  # 인자를 공백으로 이은 글. 실제 준비면 `SETUP_COMMANDS`의 하나다
    end: SetupEnd
    exit_code: int | None  # `SetupEnd.EXITED`일 때만 값이 있다


@dataclass(frozen=True)
class Setup:
    failed: SetupFailed | None
    wall_clock_from: float  # 회차의 벽시계를 재기 시작할 단조 시계 값(준비가 끝난 뒤)


def run_setup(
    cwd: Path,
    commands: Sequence[Sequence[str]],
    *,
    env: Mapping[str, str],
    log: Path,
    timeout: float,
) -> Setup:
    """준비 명령을 `cwd`에서 차례로 돌린다. 하나라도 0이 아니면 남은 것을 돌리지 않는다.

    명령은 넘긴 환경의 `PATH`로 찾는다(윈도의 `pnpm.cmd` 같은 것도 찾는다). 출력은 `log`에 덧붙인다.
    """
    clean = {k: v for k, v in env.items() if k not in REPO_LOCATION_VARS}
    with open(log, "ab") as out:
        for index, argv in enumerate(commands):
            command = " ".join(argv)
            out.write(f"$ {command}\n".encode())
            out.flush()
            failed = _setup_one(cwd, argv, clean, out, timeout)
            if failed is not None:
                end, exit_code = failed
                return Setup(SetupFailed(index, command, end, exit_code), time.monotonic())
    return Setup(None, time.monotonic())


def _setup_one(
    cwd: Path,
    argv: Sequence[str],
    env: dict[str, str],
    out: BinaryIO,
    timeout: float,
) -> tuple[SetupEnd, int | None] | None:
    """준비 명령 하나. 성공이면 빈 값, 실패면 (끝난 꼴, 종료 코드)."""
    exe = shutil.which(argv[0], path=env.get("PATH"))
    if exe is None:
        return SetupEnd.NOT_STARTED, None
    try:
        done = subprocess.run(
            [exe, *argv[1:]],
            cwd=cwd,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return SetupEnd.TIMED_OUT, None
    except OSError:
        return SetupEnd.NOT_STARTED, None
    return None if done.returncode == 0 else (SetupEnd.EXITED, done.returncode)


def prepare_round(
    place: RoundDir,
    *,
    source: Path,
    base: str,
    merge: str,
    rules: Sequence[str],
    setup: Sequence[Sequence[str]],
    env: Mapping[str, str],
    timeout: float,
) -> Setup:
    """회차 하나의 bare·클론·막는 규칙·준비. 클론이 B까지가 아니면 `CloneError`다."""
    build_clone(source, base, merge, place)
    write_deny_rules(place.clone, rules)
    return run_setup(place.clone, setup, env=env, log=place.setup_log, timeout=timeout)


# --- 세션 환경 ---


def without_venv_dirs(path: str) -> str:
    """`PATH` 값에서 가상 환경의 실행 폴더(부모 폴더에 `pyvenv.cfg`가 있는 폴더)를 뺀다.

    러너를 주 체크아웃에서 `uv run`으로 띄우면 그 `.venv`의 실행 폴더가 맨 앞에 와서, 세션이 친 맨
    `pytest` 같은 명령이 클론이 아니라 주 체크아웃의 환경과 코드로 돈다(04의 PR 직전
    `/security-review`가 측정의 정확성으로 짚었다). 클론의 `uv run`은 클론의 `.venv`를 쓰므로 빼도
    준비와 게이트는 그대로다. 빈 조각, 상대 경로 조각, 루트(`/`, `C:\\`)는 그대로 둔다. 상대 조각의
    부모는 러너의 작업 폴더라 견주지 않는다. 폴더가 있는지는 보지 않아, 부모 폴더에 `pyvenv.cfg`가
    있으면 없는 실행 폴더도 뺀다. 가상 환경이 아닌 곳(전역 파이썬, `~/.local/bin`)에 깔린 명령은
    거르지 않는다.
    """

    def in_venv(part: str) -> bool:
        folder = part.rstrip("\\/")
        if not folder or not os.path.isabs(folder):
            return False
        parent = os.path.dirname(folder)
        return parent != folder and os.path.isfile(os.path.join(parent, "pyvenv.cfg"))

    return os.pathsep.join(p for p in path.split(os.pathsep) if not in_venv(p))


def session_env(
    parent: Mapping[str, str], *, config_dir: str, round_dir: RoundDir
) -> dict[str, str]:
    """세션에 넘길 환경. 허용 목록 가운데 부모에 있는 것과 러너가 짓는 셋이다.

    `parent`에 `os.environ`을 주면 윈도에서 이름의 대소문자를 가리지 않고 찾는다. 설정 폴더는 넘긴
    글 그대로다(`claude auth status`의 `configDirectory`가 그 글을 그대로 돌려준다, 명세 "계정").
    """
    env = {n: parent[n] for n in ALLOWED_ENV if n not in RUNNER_SET_ENV and n in parent}
    if "PATH" in env:
        env["PATH"] = without_venv_dirs(env["PATH"])
    env[CONFIG_DIR_VAR] = config_dir
    env[AUTOUPDATER_VAR] = "1"
    env[GH_CONFIG_VAR] = str(round_dir.gh_config)
    return env


# --- 지우기 ---


@dataclass
class Removal:
    removed: list[str] = field(default_factory=list[str])
    no_record: list[str] = field(default_factory=list[str])
    not_round: list[str] = field(default_factory=list[str])
    failed: list[tuple[str, str]] = field(default_factory=list[tuple[str, str]])


def _is_round_dir(entry: os.DirEntry[str]) -> bool:
    """링크가 아닌 폴더이고 이름이 회차 폴더 꼴이며 표지가 그 이름을 담은 보통 파일인지.

    표지는 글자 그대로의 이름으로 찾는다. 윈도는 대소문자만 다른 이름도 같은 파일로 열지만, 지울 때
    맨 끝에 남길 표지는 글자 그대로 견주므로 둘이 어긋나면 표지를 먼저 지운다."""
    if entry.is_symlink() or entry.is_junction() or not entry.is_dir(follow_symlinks=False):
        return False
    if parse_round_dir_name(entry.name) is None:
        return False
    marker = os.path.join(entry.path, MARKER)
    try:
        if MARKER not in os.listdir(entry.path) or not stat.S_ISREG(os.lstat(marker).st_mode):
            return False
        with open(marker, "rb") as f:
            return f.read(_MARKER_MAX_BYTES) == entry.name.encode("utf-8")
    except OSError:
        return False


def _recorded(records: Path, name: str) -> bool:
    """`records/`에 이 회차 폴더를 가리키는 기록이 있는지."""
    parsed = parse_round_dir_name(name)
    if parsed is None:
        return False
    path = records / record_file_name(parsed.task_id, parsed.arm, parsed.round_no)
    try:
        return read_record(path).round_dir_name == name
    except (OSError, ShapeError):
        return False


def _cut_links(folder: str) -> list[str]:
    """`folder` 아래의 심볼릭 링크와 junction을 링크만 끊는다. 끊지 못한 링크와 읽지 못한 폴더."""
    left: list[str] = []
    pending = [folder]
    while pending:
        current = pending.pop()
        try:
            entries = list(os.scandir(current))
        except OSError:
            left.append(current)
            continue
        for entry in entries:
            if entry.is_symlink() or entry.is_junction():
                try:
                    os.unlink(entry.path)
                except OSError:
                    left.append(entry.path)
            elif entry.is_dir(follow_symlinks=False):
                pending.append(entry.path)
    return left


class _RemoveError(Exception):
    """회차 폴더 하나를 지우지 못했다. 메시지가 그 까닭이다."""


def _rmdir(folder: str) -> None:
    """빈 회차 폴더를 지운다. 윈도에서 폴더의 읽기 전용 특성에 막히면 특성을 풀고 한 번 더
    지운다."""
    try:
        os.rmdir(folder)
    except PermissionError:
        if sys.platform != "win32":
            raise
        os.chmod(folder, stat.S_IWRITE)
        os.rmdir(folder)


def _remove(folder: str) -> None:
    """회차 폴더 하나를 지운다. 링크를 먼저 끊고 표지를 맨 끝에 지운다. OS가 막아(`OSError`)
    지우지 못하면 그 까닭을 든 `_RemoveError`다.

    판정한 뒤 그 이름이 링크로 바뀌었으면 지우지 않는다. 안을 다 지운 뒤 빈 폴더만 지우지 못하면
    (다른 프로세스가 작업 디렉터리로 쥐었다) 표지를 다시 심는다. 항목은 `delete_path`로 지운다.
    링크는 링크만, 폴더는 통째로 지우고, 읽기 전용 파일에 지우기가 막히면(윈도) 쓰기를 켜고 다시
    지운다."""
    if os.path.islink(folder) or os.path.isjunction(folder):
        raise _RemoveError("판정한 뒤 링크로 바뀌어 지우지 않았다")
    try:
        left = _cut_links(folder)
    except OSError as e:
        raise _RemoveError(f"링크를 찾다 막혔다. {type(e).__name__}: {e}") from e
    if left:
        raise _RemoveError(f"끊지 못한 링크나 읽지 못한 폴더 {len(left)}개(첫째 {left[0]})")
    try:
        for entry in sorted(os.scandir(folder), key=lambda e: e.name):
            if entry.name != MARKER:
                delete_path(Path(entry.path))
        delete_path(Path(folder) / MARKER)
    except OSError as e:
        raise _RemoveError(f"{type(e).__name__}: {e}") from e
    try:
        _rmdir(folder)
    except OSError as e:
        # 다시 부르면 마저 지우게 표지를 다시 심는다.
        try:
            _plant_marker(folder)
        except OSError as replant:
            raise _RemoveError(
                f"빈 폴더를 지우지 못했고 표지도 다시 심지 못했다. {e}; {replant}"
            ) from replant
        raise _RemoveError(
            f"빈 폴더를 지우지 못했다(표지를 다시 심었다). {type(e).__name__}: {e}"
        ) from e


def remove_round_dirs(root: Path, records: Path) -> Removal | None:
    """뿌리 바로 아래에서 표지와 기록이 있는 회차 폴더만 지운다. 나머지는 이름을 보고한다. 뿌리를
    읽으려는데 없다고 하면(대상을 잃은 링크 포함) 아무것도 하지 않고 `None`이다."""
    report = Removal()
    base = long_path(os.path.abspath(root))
    try:
        entries = sorted(os.scandir(base), key=lambda e: e.name)
    except FileNotFoundError:
        return None
    except NotADirectoryError as e:
        raise PlaceError(f"뿌리가 폴더가 아니다: {root}") from e
    except OSError as e:
        raise PlaceError(f"뿌리를 읽지 못했다: {root} ({type(e).__name__}: {e})") from e
    for entry in entries:
        if not _is_round_dir(entry):
            report.not_round.append(entry.name)
        elif not _recorded(records, entry.name):
            report.no_record.append(entry.name)
        else:
            try:
                _remove(entry.path)
            except _RemoveError as e:
                report.failed.append((entry.name, str(e)))
            else:
                report.removed.append(entry.name)
    return report


# --- 명령 줄 ---


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.rerun_round", description="다시 풀기 회차의 자리."
    )
    sub = parser.add_subparsers(dest="command", required=True)
    remove = sub.add_parser("remove", help="뿌리 아래에서 표지와 기록이 있는 회차 폴더만 지운다")
    remove.add_argument("root", help="회차 폴더의 뿌리(절대 경로)")
    remove.add_argument("--records", default=str(RECORDS), help="회차 기록 폴더")
    return parser


def main(argv: list[str] | None = None) -> int:
    """종료 코드: 0 지울 것을 다 지웠다(뿌리가 없으면 stderr에 한 줄을 남긴다), 1 지우지 못한
    폴더가 있다, 2 아무것도 지우지 않고 멈췄다(뿌리를 쓸 수 없거나 읽지 못했다, 주 체크아웃을 찾지
    못했다)."""
    args = _parser().parse_args(argv)
    root_text: str = args.root
    records_text: str = args.records
    try:
        checkout = main_checkout(ROOT)
        root = checked_place(
            root_text, "뿌리", main_checkout=checkout, user_claude=Path.home() / ".claude"
        )
        report = remove_round_dirs(root, Path(records_text))
    except (PlaceError, CloneError) as e:
        print(f"끝: {e}", file=sys.stderr)
        return 2
    if report is None:
        print(f"뿌리가 없어 지울 것이 없다: {root}", file=sys.stderr)
        return 0
    for name in report.removed:
        print(f"지웠다: {name}")
    for name in report.no_record:
        print(f"기록이 없어 남겼다: {name}")
    for name in report.not_round:
        print(f"회차 폴더가 아니라 남겼다: {name}")
    for name, why in report.failed:
        print(f"지우지 못했다: {name} ({why})")
    return 1 if report.failed else 0


if __name__ == "__main__":
    # 윈도의 파이프는 PYTHONUTF8·PYTHONIOENCODING 이 없으면 로캘의 인코딩(이 PC 는 cp949)이라, 그
    # 밖의 글자(이모지 등)가 든 이름을 찍다 `UnicodeEncodeError`로 지운 뒤의 보고를 잃는다(PR 직전
    # 리뷰. 이 PC 에서 `print`와 `sys.stdout.encoding`으로 손으로 봤다). 선례는 `tools/canary.py`의
    # 같은 자리다.
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())
