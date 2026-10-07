"""tools/hook_session_web_deps.py — 클라우드 세션이 시작될 때 web 의존성을 깐다(대기열 138).

설치 명령은 인자로 받아 가짜(파이썬 한 줄)로 성공·실패·시간 초과·실행 실패를 만든다. 진짜 pnpm 은
띄우지 않는다. CLI 는 두 번 실제로 부른다. 로컬 세션이면 아무것도 하지 않고, 클라우드 세션인데
pnpm 을 찾지 못하면 세션에 알린다. 둘 다 저장소 밖의 임시 web/ 을 가리켜 이 저장소를 건드리지
않는다.
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
    TIMEOUT_SECONDS,
    failure_output,
    install,
    manual_command,
    project_root,
    should_install,
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


def test_실패는_모델과_사용자에게_손으로_칠_명령과_함께_알린다(tmp_path: Path) -> None:
    web = _web(tmp_path)

    output = failure_output("ERR_PNPM_OUTDATED_LOCKFILE", web)

    specific = output["hookSpecificOutput"]
    assert specific["hookEventName"] == "SessionStart"
    assert "ERR_PNPM_OUTDATED_LOCKFILE" in specific["additionalContext"]
    assert manual_command(web) in specific["additionalContext"]
    assert manual_command(web) in output["systemMessage"]


def test_등록의_시간_제한이_훅_안의_것보다_길다() -> None:
    """훅 안의 시간 제한이 먼저 와야 훅이 스스로 알리고 끝난다. 등록의 것이 먼저 오면 Claude
    Code 가 훅을 끊어 아무것도 알리지 못한다."""
    registration = registered_hooks()["hook_session_web_deps.py"]

    assert registration.event == "SessionStart"
    assert registration.timeout > TIMEOUT_SECONDS


def _cli(tmp_path: Path, remote: str | None) -> subprocess.CompletedProcess[str]:
    """훅을 실제로 부른다. PATH 에는 없는 디렉터리만 두어 진짜 pnpm 을 찾지 못하게 한다.

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
    process = _cli(tmp_path, remote=None)

    assert process.returncode == 0, process.stderr
    assert process.stdout == ""


def test_CLI_는_pnpm_을_찾지_못하면_세션에_알리고_0으로_끝난다(tmp_path: Path) -> None:
    process = _cli(tmp_path, remote="true")

    assert process.returncode == 0, process.stderr
    context = json.loads(process.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "pnpm 을 PATH 에서 찾지 못했다" in context
    assert manual_command(tmp_path / "web") in context
