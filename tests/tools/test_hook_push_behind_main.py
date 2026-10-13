"""tools/hook_push_behind_main.py 의 판정. 뒤처짐 수는 tmp_path 의 임시 저장소로 잰다.

stdin 을 읽는 main 은 tools/run_hooks.py(pre-commit)가 등록 모양으로 띄워 확인한다.
"""

from __future__ import annotations

import subprocess
import time
from collections.abc import Callable
from pathlib import Path

import pytest
from tools.hook_push_behind_main import (
    FETCH_TIMEOUT,
    GIT_TIMEOUT,
    behind_count,
    checks_push,
    quiet_git,
    reason_for,
    reason_text,
    run_git,
)

IDENTITY = ("-c", "user.name=test", "-c", "user.email=test@localhost")


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True, timeout=30)


def behind_repository(
    root: Path, *, ahead_on_main: int = 1, remote: str = "origin", base: str = "main"
) -> Path:
    """origin 의 `base` 가 작업 브랜치보다 `ahead_on_main` 커밋 앞선 저장소. 원격은 같은 tmp 의 bare
    다."""
    origin = root / "origin.git"
    repo = root / "work"
    git("init", "-q", "--bare", "-b", base, str(origin))
    git("init", "-q", "-b", base, str(repo))
    git("-C", str(repo), *IDENTITY, "commit", "-q", "--allow-empty", "-m", "first")
    git("-C", str(repo), "remote", "add", remote, str(origin))
    git("-C", str(repo), "push", "-q", remote, base)
    git("-C", str(repo), "switch", "-q", "-c", "chore/x")
    git("-C", str(repo), *IDENTITY, "commit", "-q", "--allow-empty", "-m", "work")
    git("-C", str(repo), "switch", "-q", base)
    for index in range(ahead_on_main):
        git("-C", str(repo), *IDENTITY, "commit", "-q", "--allow-empty", "-m", f"ahead {index}")
    git("-C", str(repo), "push", "-q", remote, base)
    git("-C", str(repo), "switch", "-q", "chore/x")
    return repo


@pytest.mark.parametrize(
    "command",
    [
        "git push",
        "git push -u origin chore/push-behind-notice",  # 이 세션이 첫 푸시에 친 모양
        "git -C C:/project/agent/.claude/worktrees/x push",
        'git -c "credential.helper=" push',
        "git --no-pager push",
        "git add -A && git commit -m x && git push",
    ],
)
def test_명령_위치의_git_push는_잰다(command: str) -> None:
    assert checks_push(command)


@pytest.mark.parametrize(
    "command",
    [
        "echo 'git push 는 나중에'",
        "echo git push 는 CI 가 끝난 뒤에",  # 인용 없이 다른 명령의 인자로 든 문구
        "git push origin --delete chore/ci-wait-background",  # 이 세션이 병합 뒤에 친 명령
        "git push -d origin chore/x",
        "git push origin :chore/x",
        'git push origin ":chore/x"',  # 인용한 지우기 refspec
        "git push -fd origin chore/x",  # 합친 짧은 옵션의 -d
        "PUSH_BEHIND_OK=1 git push",
        "$env:PUSH_BEHIND_OK = '1'; git push",  # PowerShell 의 탈출구
        "git log --oneline -1",
        "cat <<'EOF' > note.txt\ngit push\nEOF",
    ],
)
def test_지우는_푸시와_탈출구와_데이터로_든_문구는_재지_않는다(command: str) -> None:
    assert not checks_push(command)


def test_래퍼_뒤의_푸시와_큰따옴표_안의_치환은_놓친다() -> None:
    # 못 보는 것: 인용 안은 자리표시자로 바뀌어 명령 위치가 되지 않는다.
    assert not checks_push('bash -c "git push"')
    assert not checks_push('result="$(git push 2>&1)"')


def test_PowerShell의_제어_블록과_접두_명령_뒤의_푸시는_놓친다() -> None:
    # 못 보는 것: 조각 앞을 벗기는 규칙이 `if (…) {`·`time` 을 모른다. 막지 않고 지나간다.
    assert not checks_push("if ($?) { git push }")
    assert not checks_push("time git push")


def test_태그만_올리는_푸시도_잰다() -> None:
    # 못 보는 것: 브랜치를 올리지 않아 CI 를 다시 돌리지 않는데도 막는다. 탈출구로 지나간다.
    assert checks_push("git push --tags")
    assert not checks_push("PUSH_BEHIND_OK=1 git push --tags")


def test_멈춘_fetch는_손자_프로세스가_살아_있어도_시간_제한에서_끊는다(tmp_path: Path) -> None:
    # 출력을 붙잡으면 kill 뒤에도 손자가 쥔 파이프를 기다려, 2초 제한이 손자가 끝날 때(12초)까지
    # 늦어졌다(PR 직전 버그 리뷰가 윈도에서 ext:: 전송으로 재현했다).
    git("init", "-q", str(tmp_path))
    started = time.monotonic()
    fetched = quiet_git(
        str(tmp_path), 2, "-c", "protocol.ext.allow=always", "fetch", "-q", "ext::sleep 12", "main"
    )
    assert not fetched
    assert time.monotonic() - started < 8


def test_원격의_main이_앞서면_뒤처진_수를_낸다(tmp_path: Path) -> None:
    repo = behind_repository(tmp_path, ahead_on_main=2)
    assert behind_count(str(repo)) == 2


def test_main을_합친_뒤에는_0이다(tmp_path: Path) -> None:
    repo = behind_repository(tmp_path)
    git("-C", str(repo), *IDENTITY, "merge", "-q", "--no-edit", "origin/main")
    assert behind_count(str(repo)) == 0


def test_main_위에서는_재지_않는다(tmp_path: Path) -> None:
    repo = behind_repository(tmp_path)
    git("-C", str(repo), "switch", "-q", "main")
    git("-C", str(repo), "reset", "-q", "--hard", "HEAD~1")
    assert behind_count(str(repo)) is None


def test_detached_HEAD에서는_재지_않는다(tmp_path: Path) -> None:
    repo = behind_repository(tmp_path)
    git("-C", str(repo), "switch", "-q", "--detach", "HEAD")
    assert behind_count(str(repo)) is None


def test_원격_이름이_origin이_아니면_재지_않는다(tmp_path: Path) -> None:
    # 못 보는 것: 원격 이름과 기본 브랜치를 origin·main 으로 고정했다.
    repo = behind_repository(tmp_path, remote="upstream")
    assert behind_count(str(repo)) is None


def test_기본_브랜치가_main이_아니면_재지_않는다(tmp_path: Path) -> None:
    repo = behind_repository(tmp_path, base="trunk")
    assert behind_count(str(repo)) is None


def test_fetch가_실패하면_재지_않는다(tmp_path: Path) -> None:
    # 못 보는 것: 오프라인이나 지워진 원격. 막지 않고 지나간다(fail-open).
    repo = behind_repository(tmp_path)
    git("-C", str(repo), "remote", "set-url", "origin", str(tmp_path / "gone.git"))
    assert behind_count(str(repo)) is None


def test_git이_시간을_넘기면_실패로_센다(monkeypatch: pytest.MonkeyPatch) -> None:
    # 못 보는 것: 시간을 넘긴 fetch 는 실패와 같이 지나간다. 호출마다 시간 제한을 넘기는지 본다.
    seen: list[object] = []

    def stuck(args: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        seen.append(kwargs.get("timeout"))
        raise subprocess.TimeoutExpired(args, 8)

    monkeypatch.setattr(subprocess, "run", stuck)
    assert run_git("C:/this", FETCH_TIMEOUT, "fetch", "-q", "origin", "main") is None
    assert seen == [FETCH_TIMEOUT]


@pytest.mark.parametrize("call", [run_git, quiet_git])
def test_git은_저장소를_가리키는_환경을_벗기고_자격_증명을_묻지_않는다(
    call: Callable[..., object], monkeypatch: pytest.MonkeyPatch
) -> None:
    # 워크트리의 pre-commit 아래에서는 GIT_DIR 이 남아 다른 저장소를 잰다. 프롬프트는 fetch 를 시간
    # 제한까지 붙잡는다.
    monkeypatch.setenv("GIT_DIR", "C:/elsewhere/.git")
    seen: list[dict[str, str]] = []

    def recorded(
        args: list[str], *, env: dict[str, str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        seen.append(env)
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(subprocess, "run", recorded)
    call("C:/this", GIT_TIMEOUT, "fetch", "-q", "origin", "main")
    [environment] = seen
    assert "GIT_DIR" not in environment
    assert environment.get("GIT_TERMINAL_PROMPT") == "0"


def test_저장소_밖에서는_재지_않는다(tmp_path: Path) -> None:
    assert behind_count(str(tmp_path)) is None


def recording(count: int | None) -> tuple[Callable[[str], int | None], list[str]]:
    seen: list[str] = []

    def behind(cwd: str) -> int | None:
        seen.append(cwd)
        return count

    return behind, seen


def test_뒤처진_푸시는_합치는_길과_탈출구를_든_이유로_막는다() -> None:
    behind, seen = recording(3)
    assert reason_for("git push", "C:/this", behind) == reason_text(3)
    assert seen == ["C:/this"]
    text = reason_text(3)
    assert "3커밋" in text
    assert "git merge origin/main" in text
    assert "sibling_overlap.py" in text
    assert "PUSH_BEHIND_OK=1 git push" in text
    assert "$env:PUSH_BEHIND_OK='1'; git push" in text  # PowerShell 도구에도 등록돼 있다


@pytest.mark.parametrize("count", [0, None])
def test_뒤처지지_않았거나_재지_못하면_지나간다(count: int | None) -> None:
    behind, _ = recording(count)
    assert reason_for("git push", "C:/this", behind) is None


def test_푸시가_아니면_git을_부르지_않는다() -> None:
    behind, seen = recording(3)
    assert reason_for("git commit -m x", "C:/this", behind) is None
    assert seen == []


def test_다른_저장소로_cd한_푸시도_페이로드의_cwd로_잰다() -> None:
    # 못 보는 것: `cd <다른 저장소> && git push` 와 `git -C <다른 저장소> push` 는 cwd 로 판정한다.
    behind, seen = recording(1)
    reason_for("cd C:/other && git push", "C:/this", behind)
    reason_for("git -C C:/other push", "C:/this", behind)
    assert seen == ["C:/this", "C:/this"]
