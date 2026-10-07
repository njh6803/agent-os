"""tools/hook_session_web_deps.py — 클라우드 세션이 시작될 때 git 훅과 web 의존성을 깐다.

web 의존성은 대기열 138, git 훅(pre-commit)은 일지 2026-10-07-10의 회고다. 설치 명령은 인자로
받아 가짜(파이썬 한 줄)로 성공·실패·시간 초과·실행 실패를 만든다. 진짜 pnpm 과 uv 는 띄우지 않는다.
CLI 는 실제로 부른다. 로컬 세션이면 아무것도 하지 않고, 클라우드 세션인데 명령을 찾지 못하면
세션에 알린다. 모두 저장소 밖의 임시 루트를 가리켜 이 저장소를 건드리지 않는다.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest
from tools.hook_session_web_deps import (
    GIT_HOOKS_LABEL,
    PNPM_MISSING,
    TIMEOUT_SECONDS,
    UV_MISSING,
    WEB_DEPS_LABEL,
    Failure,
    Step,
    failure_output,
    install,
    install_pre_commit,
    manual_command,
    plan,
    pre_commit_command,
    pre_commit_root,
    project_root,
    run_steps,
    should_install,
    step_timeout,
    web_dir,
)
from tools.run_hooks import registered_hooks

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / "tools" / "hook_session_web_deps.py"


def _web(tmp_path: Path) -> Path:
    web = tmp_path / "web"
    web.mkdir()
    (web / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    return web


def _python(code: str) -> list[str]:
    return [sys.executable, "-c", code]


def test_클라우드에서_시작하거나_이어질_때만_깐다() -> None:
    assert should_install("true", "startup")
    assert should_install("true", "resume")
    assert not should_install("true", "compact")
    assert not should_install("true", "clear")
    assert not should_install(None, "startup")
    assert not should_install("", "startup")
    assert not should_install("false", "startup")
    assert not should_install("true", None)


def test_프로젝트_루트는_CLAUDE_PROJECT_DIR_이_먼저다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`cwd` 는 Claude 가 `cd` 하면 따라 움직이고, `CLAUDE_PROJECT_DIR` 은 세션이 시작된 루트에
    머문다(공식 hooks 문서)."""
    monkeypatch.chdir(tmp_path)

    assert project_root("/repo", "/repo/src") == "/repo"
    assert project_root(None, "/repo/src") == "/repo/src"
    assert project_root("", "/repo/src") == "/repo/src"
    assert project_root(None, None) == os.getcwd()


def test_web_잠금_파일이_있는_자리만_web_으로_본다(tmp_path: Path) -> None:
    assert web_dir(str(tmp_path)) is None
    web = _web(tmp_path)

    assert web_dir(str(tmp_path)) == web


def test_잠금_파일을_고정하고_web_에서_깐다(tmp_path: Path) -> None:
    web = _web(tmp_path)
    expected = ["-C", str(web), "install", "--frozen-lockfile"]
    code = f"import sys; sys.exit(0 if sys.argv[1:] == {expected!r} else 1)"

    assert install(_python(code), web, timeout=30) is None


def test_손으로_칠_명령은_web_의_절대_경로를_든다(tmp_path: Path) -> None:
    web = _web(tmp_path) / "공백 있는 곳"

    assert shlex.split(manual_command(web)) == [
        "pnpm",
        "-C",
        str(web),
        "install",
        "--frozen-lockfile",
    ]


def test_설치가_성공하면_까닭이_없다(tmp_path: Path) -> None:
    assert install(_python("import sys; sys.exit(0)"), _web(tmp_path), timeout=30) is None


def test_설치가_실패하면_출력의_끝을_까닭으로_준다(tmp_path: Path) -> None:
    code = "import sys; print('ERR_PNPM_OUTDATED_LOCKFILE'); sys.exit(1)"

    reason = install(_python(code), _web(tmp_path), timeout=30)

    assert reason is not None
    assert "ERR_PNPM_OUTDATED_LOCKFILE" in reason


def test_시간_안에_끝나지_않으면_까닭이다(tmp_path: Path) -> None:
    reason = install(_python("import time; time.sleep(5)"), _web(tmp_path), timeout=0.5)

    assert reason is not None
    assert "0.5" in reason


def test_띄우지_못한_명령도_까닭이다(tmp_path: Path) -> None:
    reason = install([str(tmp_path / "no-such-pnpm")], _web(tmp_path), timeout=30)

    assert reason is not None
    assert "no-such-pnpm" in reason


def _루트(tmp_path: Path) -> Path:
    (tmp_path / ".pre-commit-config.yaml").write_text("repos: []\n", encoding="utf-8")
    return tmp_path


def test_pre_commit_설정이_있는_루트만_git_훅을_깐다(tmp_path: Path) -> None:
    assert pre_commit_root(str(tmp_path)) is None

    assert pre_commit_root(str(_루트(tmp_path))) == tmp_path


def test_git_훅은_uv_가_루트로_옮겨_pre_commit_install_로_깐다(tmp_path: Path) -> None:
    root = _루트(tmp_path)
    expected = ["run", "--directory", str(root), "pre-commit", "install"]
    code = f"import sys; sys.exit(0 if sys.argv[1:] == {expected!r} else 1)"

    assert install_pre_commit(_python(code), root, timeout=30) is None


def test_git_훅이_실패하면_출력의_끝을_까닭으로_준다(tmp_path: Path) -> None:
    code = "import sys; print('An error has occurred: FatalError'); sys.exit(1)"

    reason = install_pre_commit(_python(code), _루트(tmp_path), timeout=30)

    assert reason is not None
    assert "FatalError" in reason


def test_git_훅을_손으로_칠_명령은_어디서_쳐도_루트에_깐다(tmp_path: Path) -> None:
    root = tmp_path / "공백 있는 곳"

    assert shlex.split(pre_commit_command(root)) == [
        "uv",
        "run",
        "--directory",
        str(root),
        "pre-commit",
        "install",
    ]


def test_두_설치는_훅의_시간_제한_하나를_나눠_쓴다() -> None:
    """먼저 끝난 설치가 쓴 만큼 뒤의 설치가 덜 받는다.

    다 썼어도 뒤의 설치는 1초를 받는다.
    """
    assert step_timeout(deadline=240.0, now=0.0) == 240.0
    assert step_timeout(deadline=240.0, now=200.0) == 40.0
    assert step_timeout(deadline=240.0, now=250.0) == 1.0


def test_계획은_git_훅을_먼저_web_의존성을_다음에_둔다(tmp_path: Path) -> None:
    """git 훅이 빠진 커밋은 조용하고, web 의존성이 빠진 검사는 시끄럽게 빨갛다."""
    assert plan(str(tmp_path)) == []
    _web(tmp_path)
    assert [step.what for step in plan(str(tmp_path))] == [WEB_DEPS_LABEL]

    _루트(tmp_path)
    steps = plan(str(tmp_path))

    assert [(step.what, step.program, step.missing) for step in steps] == [
        (GIT_HOOKS_LABEL, "uv", UV_MISSING),
        (WEB_DEPS_LABEL, "pnpm", PNPM_MISSING),
    ]
    assert [step.command for step in steps] == [
        pre_commit_command(tmp_path),
        manual_command(tmp_path / "web"),
    ]


def _가짜_단계(what: str, reason: str | None, seen: list[tuple[str, str, float]]) -> Step:
    def run(program: str, timeout: float) -> str | None:
        seen.append((what, program, timeout))
        return reason

    return Step(what, what + "-명령", what + " 없음", run, what + " 손으로")


def test_단계마다_남은_시간을_받고_실패를_모은다() -> None:
    seen: list[tuple[str, str, float]] = []
    steps = [_가짜_단계("앞", None, seen), _가짜_단계("뒤", "까닭", seen)]
    clock = iter([0.0, 0.0, 200.0])

    failures = run_steps(steps, lambda name: f"/bin/{name}", lambda: next(clock))

    assert seen == [("앞", "/bin/앞-명령", 240.0), ("뒤", "/bin/뒤-명령", 40.0)]
    assert failures == [("뒤", "까닭", "뒤 손으로")]


def test_프로그램을_찾지_못한_단계는_띄우지_않고_까닭을_남긴_뒤_다음_단계로_간다() -> None:
    seen: list[tuple[str, str, float]] = []
    steps = [_가짜_단계("앞", None, seen), _가짜_단계("뒤", None, seen)]

    def which(name: str) -> str | None:
        return None if name == "앞-명령" else f"/bin/{name}"

    failures = run_steps(steps, which, lambda: 0.0)

    assert [what for what, _, _ in seen] == ["뒤"]
    assert failures == [("앞", "앞 없음", "앞 손으로")]


def test_실패는_모델과_사용자에게_손으로_칠_명령과_함께_알린다(tmp_path: Path) -> None:
    web = _web(tmp_path)
    root = _루트(tmp_path)
    failures = [
        Failure(GIT_HOOKS_LABEL, "An error has occurred", pre_commit_command(root)),
        Failure(WEB_DEPS_LABEL, "ERR_PNPM_OUTDATED_LOCKFILE", manual_command(web)),
    ]

    output = failure_output(failures)

    specific = output["hookSpecificOutput"]
    assert specific["hookEventName"] == "SessionStart"
    for what, reason, command in failures:
        assert what in specific["additionalContext"]
        assert reason in specific["additionalContext"]
        assert command in specific["additionalContext"]
        assert command in output["systemMessage"]


def test_등록의_시간_제한이_훅_안의_것보다_길다() -> None:
    """훅 안의 시간 제한이 먼저 와야 훅이 스스로 알리고 끝난다. 등록의 것이 먼저 오면 Claude
    Code 가 훅을 끊어 아무것도 알리지 못한다."""
    registration = registered_hooks()["hook_session_web_deps.py"]

    assert registration.event == "SessionStart"
    assert registration.timeout > TIMEOUT_SECONDS


def _cli(tmp_path: Path, remote: str | None) -> subprocess.CompletedProcess[str]:
    """훅을 실제로 부른다. PATH 에는 없는 디렉터리만 두어 진짜 pnpm 과 uv 를 찾지 못하게 한다.

    페이로드의 `cwd` 는 루트 아래의 디렉터리다. Claude 가 `cd` 한 뒤의 세션처럼, 훅이
    `CLAUDE_PROJECT_DIR` 로 루트를 찾아야 web/ 을 본다.
    """
    env = {key: value for key, value in os.environ.items() if key != "CLAUDE_CODE_REMOTE"}
    system: list[str] = (
        [os.path.join(os.environ["SYSTEMROOT"], "System32")] if os.name == "nt" else []
    )
    env["PATH"] = os.pathsep.join([str(tmp_path / "bin"), *system])
    env["CLAUDE_PROJECT_DIR"] = str(tmp_path)
    if remote is not None:
        env["CLAUDE_CODE_REMOTE"] = remote
    web = _web(tmp_path)
    payload = {"hook_event_name": "SessionStart", "source": "startup", "cwd": str(web)}
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
        check=False,
    )


def test_CLI_는_로컬_세션에서_아무것도_하지_않는다(tmp_path: Path) -> None:
    _루트(tmp_path)

    process = _cli(tmp_path, remote=None)

    assert process.returncode == 0, process.stderr
    assert process.stdout == ""


def test_CLI_는_pnpm_을_찾지_못하면_세션에_알리고_0으로_끝난다(tmp_path: Path) -> None:
    process = _cli(tmp_path, remote="true")

    assert process.returncode == 0, process.stderr
    context = json.loads(process.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "pnpm 을 PATH 에서 찾지 못했다" in context
    assert manual_command(tmp_path / "web") in context
    assert GIT_HOOKS_LABEL not in context  # pre-commit 설정이 없는 루트다


def test_CLI_는_pre_commit_설정이_있으면_git_훅도_깔고_uv_가_없으면_알린다(tmp_path: Path) -> None:
    root = _루트(tmp_path)

    process = _cli(tmp_path, remote="true")

    assert process.returncode == 0, process.stderr
    output = json.loads(process.stdout)
    context = output["hookSpecificOutput"]["additionalContext"]
    assert "uv 를 PATH 에서 찾지 못했다" in context
    assert pre_commit_command(root) in context
    assert pre_commit_command(root) in output["systemMessage"]
    assert "pnpm 을 PATH 에서 찾지 못했다" in context
