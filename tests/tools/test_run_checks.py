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
import time
from pathlib import Path

import pytest
from tools.database_for_tests import UP_COMMAND, URL_ENV
from tools.run_checks import (
    CHECKS,
    COMPOSE_UP,
    COMPOSE_UP_SECONDS,
    Check,
    Running,
    UpResult,
    database_answers,
    docker_up,
    prepare_test_database,
    pyright_checks,
    pytest_workers,
    run,
    run_one,
    skipped_ids,
)

from tools import run_checks

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


@pytest.mark.parametrize(
    ("cpu_count", "workers"),
    [(16, 8), (15, 7), (2, 1), (1, 1), (None, 1)],
)
def test_pytest_프로세스_수는_논리_CPU_의_절반이고_1_아래로_내려가지_않는다(
    cpu_count: int | None, workers: int
) -> None:
    """ADR 0035. `os.cpu_count()` 는 값을 알아내지 못하면 None 이다."""
    assert pytest_workers(cpu_count) == workers


def test_러너의_pytest_는_계산한_프로세스_수로_나눠_돈다() -> None:
    """`-n` 은 러너에만 둔다(손으로 치는 pytest, mutate, CI 는 한 프로세스로 둔다는 결정, ADR
    0035)."""
    (pytest_check,) = [check for check in CHECKS if check.id == "pytest"]
    command = pytest_check.command

    assert command[:4] == ("uv", "run", "pytest", "-q")
    assert "-n" in command
    assert command[command.index("-n") + 1] == str(pytest_workers(os.cpu_count()))


@pytest.mark.parametrize("platform", ["win32", "darwin"])
def test_리눅스가_아닌_곳의_pyright_는_리눅스_플랫폼으로_한_번_더_돈다(platform: str) -> None:
    """이 PC(윈도)의 pyright 가 초록인 시험 파일을 리눅스 CI 의 pyright 가 빨갛게
    냈다(대기열 403)."""
    checks = pyright_checks(platform)

    assert [check.id for check in checks] == ["pyright", "pyright-linux"]
    assert checks[0].command == ("uv", "run", "pyright")
    assert checks[1].command == ("uv", "run", "pyright", "--pythonplatform", "Linux")


def test_리눅스의_pyright_는_한_번만_돈다() -> None:
    """리눅스에서는 두 검사가 같아 한 번 더 돌 몫이 없다."""
    assert [check.id for check in pyright_checks("linux")] == ["pyright"]


def test_러너의_pyright_는_이_플랫폼의_검사다() -> None:
    expected = [check.id for check in pyright_checks(sys.platform)]

    assert [check.id for check in CHECKS if check.id.startswith("pyright")] == expected


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


def _stops_growing(path: Path, within: float) -> bool:
    """`within` 초 안에 파일이 1초 동안 자라지 않으면 참. 끝내기가 늦은 것과 끝내지 못한 것을
    가르려고, 한 번만 견주지 않고 기한까지 거듭 견준다(대기열 306)."""
    deadline = time.monotonic() + within
    while time.monotonic() < deadline:
        before = path.stat().st_size
        time.sleep(1)
        if path.stat().st_size == before:
            return True
    return False


def test_시간_제한을_넘긴_검사는_손자까지_끝내고_실패로_알린다(tmp_path: Path) -> None:
    """pytest 작업 프로세스 여덟이 약 11시간 남아 커밋을 붙잡았다(대기열 333). 검사는 손자를
    띄우고 120초 잔다. 손자는 검사의 출력 파이프를 물려받은 채 0.1초마다 표지 파일을 키운다.

    제한(5초)은 부모와 손자가 뜨는 시간보다, 경과의 상한(60초)은 제한과 끝내기를 홀로 잰 시간보다
    한참 넉넉하게 둔다(tests.md).
    """
    beat = tmp_path / "beat"
    grandchild = (
        "import pathlib, time\n"
        "while True:\n"
        f"    with pathlib.Path({str(beat)!r}).open('a') as f:\n"
        "        f.write('.')\n"
        "    time.sleep(0.1)\n"
    )
    parent = (
        "import subprocess, sys, time\n"
        f"subprocess.Popen([sys.executable, '-c', {grandchild!r}])\n"
        "time.sleep(120)\n"
    )
    check = Check("stuck", (sys.executable, "-c", parent), timeout=5)
    out = io.BytesIO()
    start = time.monotonic()

    code = run((check,), {}, tmp_path, out)

    elapsed = time.monotonic() - start
    text = out.getvalue().decode()
    assert code == 1
    assert "5초 시간 제한을 넘겼다" in text
    assert elapsed < 60, f"돌아오기까지 {elapsed:.1f}초"
    assert beat.exists(), "손자가 뜨기 전에 끊었다. 손자를 끝냈는지 재지 못한다"
    assert _stops_growing(beat, within=15), "시간 제한 뒤에도 손자가 돈다"


class _InterruptingOut(io.BytesIO):
    """첫 줄을 쓰는 순간 Ctrl-C 처럼 `KeyboardInterrupt` 를 던지는 출력."""

    def write(self, data: object, /) -> int:
        raise KeyboardInterrupt


def test_기다리는_도중_Ctrl_C_가_나면_남은_검사의_손자까지_끝낸다(tmp_path: Path) -> None:
    """POSIX 에서 자식은 제 세션을 이끌어 터미널의 Ctrl-C 를 받지 못한다. 그래서 러너가 끝낸다.

    빠른 검사는 손자의 표지 파일이 생긴 뒤에 끝나고, 그 결과를 찍는 순간 Ctrl-C 가 난다. 그래서
    손자가 떴는지를 시간에 기대지 않고 안다. 멈춘 검사의 제한(45초)은 러너가 끝내지 않을 때도
    시험이 그때 돌아와 경과의 상한(30초)으로 빨개지게 하려는 것이다. 30초는 홀로 돈 이 시험의
    경과보다 한참 넉넉하다(tests.md).
    """
    beat = tmp_path / "beat"
    grandchild = (
        "import pathlib, time\n"
        "while True:\n"
        f"    with pathlib.Path({str(beat)!r}).open('a') as f:\n"
        "        f.write('.')\n"
        "    time.sleep(0.1)\n"
    )
    stuck = (
        "import subprocess, sys, time\n"
        f"subprocess.Popen([sys.executable, '-c', {grandchild!r}])\n"
        "time.sleep(120)\n"
    )
    waits = (
        "import pathlib, time\n"
        f"while not pathlib.Path({str(beat)!r}).exists():\n"
        "    time.sleep(0.1)\n"
    )
    checks = (
        Check("stuck", (sys.executable, "-c", stuck), timeout=45),
        Check("quick", (sys.executable, "-c", waits)),
    )
    start = time.monotonic()

    with pytest.raises(KeyboardInterrupt):
        run(checks, {}, tmp_path, _InterruptingOut())

    elapsed = time.monotonic() - start
    assert elapsed < 30, f"Ctrl-C 뒤 돌아오기까지 {elapsed:.1f}초"
    assert _stops_growing(beat, within=15), "Ctrl-C 뒤에도 손자가 돈다"


def test_멈춘_뒤에_띄운_검사는_곧바로_끝내고_실패로_알린다(tmp_path: Path) -> None:
    """Ctrl-C 로 `stop` 한 뒤 띄워진 검사는 `add` 가 받지 않아 띄운 스레드가 끝낸다. 남은 출력은
    `_drain` 으로 읽어, 트리를 떠난 손자가 파이프를 쥐어도 기다림이 끝난다. 그 손자는 띄운 직후
    끝내는 순서라 시험으로 만들지 못해, 여기서는 그 갈래가 120초 자는 검사를 곧바로 끝내는지만 본다.
    경과의 상한(30초)은 홀로 돈 경과보다 한참 넉넉하다(tests.md)."""
    running = Running()
    running.stop()
    check = Check("late", (sys.executable, "-c", "import time; time.sleep(120)"))
    start = time.monotonic()

    outcome = run_one(check, tmp_path, running)

    elapsed = time.monotonic() - start
    assert not outcome.passed
    assert "멈추는 중이라 띄운 검사를 곧바로 끝냈다" in outcome.output.decode()
    assert elapsed < 30, f"돌아오기까지 {elapsed:.1f}초"


def test_검사의_시간_제한은_관측_최대의_네_배_이상이다() -> None:
    """관측 최대는 xdist 전 한 프로세스 pre-commit pytest 의 1,048초다(대기열 333, 부하 아래
    web-verify 는 500초). 그보다 짧으면 부하 아래의 정상 실행을 멈춘 검사로 끊는다."""
    assert CHECKS, "검사 목록이 비었다"
    assert all(check.timeout >= 4 * 1048 for check in CHECKS)


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


# --- 테스트 컨테이너를 챙기는 판정: Docker 도 접속도 부르지 않는 함수로 본다 ------------------


class _Docker:
    """`bring_up` 의 대역. 부른 횟수를 세고 준비해 둔 결과를 차례로 돌려준다."""

    def __init__(self, *results: UpResult) -> None:
        self._results = list(results)
        self.calls = 0

    def __call__(self) -> UpResult:
        self.calls += 1
        return self._results.pop(0)


def _must_not_up() -> UpResult:
    raise AssertionError("컨테이너를 띄우면 안 된다")


UNREACHABLE = UpResult(1, "docker compose 가 종료 코드 1 로 끝났습니다")
SUCCESS = UpResult(0)


@pytest.mark.parametrize("value", ["postgresql://u:p@db:5432/x", " x "])
def test_테스트_데이터베이스_변수가_있으면_보지도_띄우지도_않는다(value: str) -> None:
    asked: list[str] = []

    def answers() -> bool:
        asked.append(f"접속 확인 {len(asked) + 1}번째")
        return True

    line = prepare_test_database({URL_ENV: value}, answers=answers, bring_up=_must_not_up)
    assert (line, asked) == (None, [])


@pytest.mark.parametrize("environ", [{}, {URL_ENV: ""}, {URL_ENV: "   "}])
def test_변수가_없거나_비었고_서버가_답하면_띄우지_않고_아무것도_찍지_않는다(
    environ: dict[str, str],
) -> None:
    assert prepare_test_database(environ, answers=lambda: True, bring_up=_must_not_up) is None


def test_답하지_않으면_한_번_띄우고_한_줄을_찍는다() -> None:
    docker = _Docker(SUCCESS)
    line = prepare_test_database({}, answers=lambda: False, bring_up=docker)
    assert (line, docker.calls) == ("테스트 컨테이너를 띄웠습니다.", 1)


def test_0이_아닌_종료는_한_번_더_치고_이번에_0이면_띄운_것이다() -> None:
    """두 세션이 동시에 띄우면 진 쪽이 컨테이너 이름이 겹쳐 1 로 끝난다."""
    docker = _Docker(UNREACHABLE, SUCCESS)
    line = prepare_test_database({}, answers=lambda: False, bring_up=docker)
    assert (line, docker.calls) == ("테스트 컨테이너를 띄웠습니다.", 2)


def test_다시_쳐도_0이_아니면_까닭_한_줄을_찍고_더_치지_않는다() -> None:
    docker = _Docker(UNREACHABLE, UpResult(2, "docker compose 가 종료 코드 2 로 끝났습니다"))
    line = prepare_test_database({}, answers=lambda: False, bring_up=docker)
    assert docker.calls == 2
    assert line == (
        "테스트 컨테이너를 띄우지 못했습니다(docker compose 가 종료 코드 2 로 끝났습니다)."
        f" pytest 는 그대로 띄웁니다. 직접 띄우려면: {UP_COMMAND}"
    )


@pytest.mark.parametrize("failure", ["180초 안에 끝나지 않았습니다", "docker 를 찾지 못했습니다"])
def test_제한_시간을_넘겼거나_치지_못한_것은_다시_치지_않는다(failure: str) -> None:
    docker = _Docker(UpResult(None, failure))
    line = prepare_test_database({}, answers=lambda: False, bring_up=docker)
    assert docker.calls == 1
    assert line == (
        f"테스트 컨테이너를 띄우지 못했습니다({failure}). pytest 는 그대로 띄웁니다."
        f" 직접 띄우려면: {UP_COMMAND}"
    )


def test_띄우는_명령은_명세의_명령이고_호출의_제한_시간은_180초다() -> None:
    assert COMPOSE_UP == (
        "docker",
        "compose",
        "-f",
        "compose.test.yaml",
        "up",
        "-d",
        "--wait",
        "--wait-timeout",
        "60",
    )
    assert COMPOSE_UP_SECONDS == 180


class _Calls:
    """`subprocess.run` 의 대역. 받은 인자를 적고 준비해 둔 결과를 돌려주거나 예외를 던진다."""

    def __init__(self, outcome: int | BaseException) -> None:
        self._outcome = outcome
        self.arguments: list[str] = []
        self.options: dict[str, object] = {}

    def __call__(
        self, arguments: list[str], **options: object
    ) -> subprocess.CompletedProcess[bytes]:
        self.arguments = arguments
        self.options = options
        if isinstance(self._outcome, BaseException):
            raise self._outcome
        return subprocess.CompletedProcess(arguments, self._outcome)


def _found(name: str) -> str:
    return f"/bin/{name}"


def _missing(name: str) -> None:
    return None


def _finished(*args: object, **kwargs: object) -> int:
    return 0


def _fake_docker(monkeypatch: pytest.MonkeyPatch, outcome: int | BaseException) -> _Calls:
    calls = _Calls(outcome)
    monkeypatch.setattr(run_checks.shutil, "which", _found)
    monkeypatch.setattr(run_checks.subprocess, "run", calls)
    return calls


def test_docker_를_찾지_못하면_치지_못한_것으로_센다(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(run_checks.shutil, "which", _missing)
    assert docker_up() == UpResult(None, "docker 를 찾지 못했습니다")


def test_띄우는_명령은_출력을_버리고_제한_시간을_걸어_저장소_루트에서_친다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _fake_docker(monkeypatch, 0)
    assert docker_up() == UpResult(0)
    assert calls.arguments == ["/bin/docker", *COMPOSE_UP[1:]]
    assert calls.options == {
        "cwd": run_checks.ROOT,
        "stdout": subprocess.DEVNULL,
        "stderr": subprocess.DEVNULL,
        "check": False,
        "timeout": COMPOSE_UP_SECONDS,
    }


def test_0이_아닌_종료는_종료_코드를_든_실패다(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_docker(monkeypatch, 3)
    assert docker_up() == UpResult(3, "docker compose 가 종료 코드 3 로 끝났습니다")


def test_제한_시간을_넘기면_종료_코드_없는_실패다(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_docker(monkeypatch, subprocess.TimeoutExpired("docker", COMPOSE_UP_SECONDS))
    assert docker_up() == UpResult(None, "180초 안에 끝나지 않았습니다")


def test_띄우지_못하면_종료_코드_없는_실패다(monkeypatch: pytest.MonkeyPatch) -> None:
    _fake_docker(monkeypatch, PermissionError("거부"))
    assert docker_up() == UpResult(None, "docker 를 띄우지 못했습니다: PermissionError")


def test_기본_주소가_답하는지는_시험의_픽스처와_같은_확인으로_본다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[str] = []

    async def fake(address: object) -> str | None:
        seen.append(repr(address))
        return None if len(seen) == 1 else "닿지 못했습니다"

    monkeypatch.setattr(run_checks, "server_problem", fake)
    monkeypatch.setenv(URL_ENV, "postgresql://u:p@elsewhere:1/x")
    assert database_answers() is True
    assert database_answers() is False
    assert seen == ["DatabaseAddress(127.0.0.1:25432/agent_os)"] * 2


def test_main_은_pytest_를_건너뛰면_컨테이너를_챙기지_않는다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prepared: list[str] = []

    def spy(*args: object, **kwargs: object) -> str | None:
        prepared.append(f"챙긴 {len(prepared) + 1}번째")
        return None

    monkeypatch.setattr(run_checks, "prepare_test_database", spy)
    monkeypatch.setattr(run_checks, "run", _finished)
    monkeypatch.setenv("SKIP", "pytest")
    assert (run_checks.main(), prepared) == (0, [])


def test_main_은_컨테이너를_챙긴_글을_먼저_찍고_검사를_띄운다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    order: list[str] = []

    def prepare(*args: object, **kwargs: object) -> str | None:
        order.append("준비")
        return "테스트 컨테이너를 띄웠습니다."

    def fake_run(*args: object, **kwargs: object) -> int:
        order.append("검사")
        return 7

    monkeypatch.setattr(run_checks, "prepare_test_database", prepare)
    monkeypatch.setattr(run_checks, "run", fake_run)
    monkeypatch.delenv("SKIP", raising=False)
    assert run_checks.main() == 7
    assert (order, capsys.readouterr().out) == (["준비", "검사"], "테스트 컨테이너를 띄웠습니다.\n")
