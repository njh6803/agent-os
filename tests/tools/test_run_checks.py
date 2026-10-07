"""tools/run_checks.py — 검사를 함께 띄우고 결과를 모으는 러너(ADR 0005 이력 2026-10-07).

함께 띄우는지는 시간으로 재지 않는다. 두 검사가 서로의 표지 파일을 기다리게 해, 하나씩 돌면 앞의
것이 기다리다 실패하고 함께 돌아야만 둘 다 통과한다. 배관은 SKIP 으로 모든 검사를 건너뛴 CLI 를
실제로 불러 본다. 진짜 검사를 띄우면 이 테스트가 pytest 를 다시 띄워 돌고 돌아서, CLI 테스트는
PATH 를 비워 둔다.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

from tools.run_checks import CHECKS, Check, run, skipped_ids

ROOT = Path(__file__).resolve().parents[2]


def _python(check_id: str, code: str) -> Check:
    return Check(check_id, (sys.executable, "-c", code))


def _waits_for(mine: Path, other: Path) -> str:
    return (
        "import pathlib, sys, time\n"
        f"pathlib.Path({str(mine)!r}).touch()\n"
        "deadline = time.monotonic() + 20\n"
        "while time.monotonic() < deadline:\n"
        f"    if pathlib.Path({str(other)!r}).exists():\n"
        "        sys.exit(0)\n"
        "    time.sleep(0.05)\n"
        "sys.exit(1)\n"
    )


def test_SKIP_을_pre_commit_처럼_쉼표로_나누고_공백을_걷는다() -> None:
    assert skipped_ids({"SKIP": " pytest, web-verify ,,"}) == {"pytest", "web-verify"}
    assert skipped_ids({}) == frozenset()


def test_검사를_함께_띄운다(tmp_path: Path) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    checks = (_python("a", _waits_for(a, b)), _python("b", _waits_for(b, a)))
    out = io.BytesIO()

    code = run(checks, {}, tmp_path, out)

    assert code == 0, out.getvalue().decode()


def test_실패한_검사의_출력만_찍고_1로_끝난다(tmp_path: Path) -> None:
    checks = (
        _python("loud", "import sys; print('boom'); sys.exit(3)"),
        _python("calm", "print('quiet')"),
    )
    out = io.BytesIO()

    code = run(checks, {}, tmp_path, out)

    text = out.getvalue().decode()
    assert code == 1
    assert "boom" in text
    assert "quiet" not in text
    assert any(line.startswith("loud") and "Failed" in line for line in text.splitlines())
    assert any(line.startswith("calm") and "Passed" in line for line in text.splitlines())


def test_SKIP_에_든_검사는_띄우지_않는다(tmp_path: Path) -> None:
    mark = tmp_path / "ran"
    checks = (_python("pytest", f"import pathlib; pathlib.Path({str(mark)!r}).touch()"),)
    out = io.BytesIO()

    code = run(checks, {"SKIP": "pytest"}, tmp_path, out)

    assert code == 0
    assert not mark.exists()
    assert "Skipped" in out.getvalue().decode()


def test_명령을_찾지_못하면_실패로_알린다(tmp_path: Path) -> None:
    checks = (Check("ghost", ("agent-os-no-such-command",)),)
    out = io.BytesIO()

    code = run(checks, {}, tmp_path, out)

    assert code == 1
    assert "agent-os-no-such-command" in out.getvalue().decode()


def test_띄우지_못한_명령도_실패로_알린다(tmp_path: Path) -> None:
    """찾았지만 띄울 수 없는 파일(실행 형식이 아니다)도 traceback 이 아니라 실패 한 줄이다."""
    program = tmp_path / "not-a-program"
    program.write_bytes(b"\x00\x01 not an executable")
    program.chmod(0o755)
    out = io.BytesIO()

    code = run((Check("broken", (str(program),)),), {}, tmp_path, out)

    assert code == 1
    assert "not-a-program" in out.getvalue().decode()


def _cli(path_dir: Path, skips: list[str]) -> subprocess.CompletedProcess[str]:
    """CLI 를 PATH 를 비운 채 부른다.

    PATH 가 빈 디렉터리라 SKIP 이 깨져도 uv·pnpm 을 찾지 못해 곧바로 끝난다. 그러지 않으면 러너가
    띄운 pytest 가 이 테스트를 다시 불러 러너를 또 띄운다(변이 표를 처음 돌릴 때 그렇게 돌았다).
    """
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "run_checks.py")],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
        env={**os.environ, "PATH": str(path_dir), "SKIP": ",".join(skips)},
        check=False,
    )


def test_CLI_진입점이_SKIP_으로_모든_검사를_건너뛴다(tmp_path: Path) -> None:
    """main 의 배관(검사 목록, SKIP)을 진짜 검사를 띄우지 않고 지난다."""
    process = _cli(tmp_path, [check.id for check in CHECKS])

    assert process.returncode == 0, process.stdout + process.stderr
    assert process.stdout.count("Skipped") == len(CHECKS)


def test_CLI_진입점이_알려진_빨강을_종료_코드와_출력으로_낸다(tmp_path: Path) -> None:
    """검사 하나만 남기고 PATH 를 비우면 그 명령을 찾지 못한다. 종료 코드가 main 밖으로 나가는지
    본다."""
    target = CHECKS[-1]
    process = _cli(tmp_path, [check.id for check in CHECKS if check is not target])

    assert process.returncode == 1, process.stdout + process.stderr
    assert target.command[0] in process.stdout
    assert any(
        line.startswith(target.id) and "Failed" in line for line in process.stdout.splitlines()
    )


def test_이_저장소의_pre_commit_은_러너의_검사를_따로_등록하지_않는다() -> None:
    """같은 검사를 러너와 훅에 함께 두면 커밋마다 두 번 돈다(대기열 118과 같은 낭비).

    글자 그대로의 명령과 같은 id 만 본다. 옵션을 바꿔 적은 명령(`uv run pytest` 처럼 `-q` 를 뺀
    것)은 못 본다.
    """
    config = (ROOT / ".pre-commit-config.yaml").read_text(encoding="utf-8")
    lines = [line.strip() for line in config.splitlines()]
    entries = {line.removeprefix("entry:").strip() for line in lines if line.startswith("entry:")}
    hook_ids = {line.removeprefix("- id:").strip() for line in lines if line.startswith("- id:")}

    assert "uv run python tools/run_checks.py" in entries
    assert CHECKS
    for check in CHECKS:
        assert " ".join(check.command) not in entries, check.id
        assert check.id not in hook_ids, check.id
