"""실제 모델 e2e 를 감싸는 pytest 가 Windows 에서 pnpm 을 자식 프로세스로 띄우는지 잰다.

web-widget 명세의 Testing Decisions 6 은 위젯 e2e 의 Playwright 프로젝트 `llm` 을 마커 `llm_widget`
을 단 파이썬 시험 하나가 자식 프로세스로 돌린다고 정했다. 그 시험은
`uv run --env-file .env pytest -m llm_widget` 아래에서 돌고, 키는 `.env` 에서 그 pytest 의 환경으로
들어와 pnpm → Playwright 로 넘어가야 한다. 이 프로브는 그 사슬의 앞 두 고리를 잰다. 같은 판의 uv 가
`pnpm` 을 이름으로 띄우지 못한 것을 손으로 봤고(일지 2026-10-23-40), 그것이 uv 의 몫인지 Windows 의
실행 파일 찾기 몫인지 가르지 않은 채였다.

회차는 넷이다.
- uv 직접: `uv run --env-file <파일> pnpm --version`. 손으로 본 `Failed to spawn: pnpm` 을 다시
  낸다.
- 이름으로: 그 pytest 안에서 `subprocess.run(["pnpm", "--version"])`. Windows 의 CreateProcess 는
  확장자 없는 이름에 `.exe` 만 붙여 찾으므로 `pnpm.cmd` 를 찾지 못할 것이라는 해석을 잰다.
- 경로로: 같은 pytest 안에서 `shutil.which("pnpm")` 이 준 경로로 `pnpm -C web exec node <파일>` 을
  띄워, 손자 node 가 `.env` 에서 온 값을 읽는지 본다. 위의 해석이 맞으면 이 회차는 뜬다(양성 대조).
- Playwright: 같은 경로로 `pnpm -C web/apps/admin exec playwright --version` 을 띄운다. 위젯 앱이
  아직 없어 관리 화면 앱의 Playwright 를 쓴다.

회차마다 표지는 그 상황에서만 나오는 문구다. uv 직접은 `Failed to spawn` 이나 pnpm 의 판 줄,
이름으로는 `FileNotFoundError` 나 판 줄, 경로로는 `TOKEN=<이번 값>`, Playwright 는 `Version 1.`
이다. 표지가 없는 회차는 측정이 아니다(`tools/probe_kit.py` 의 `Rounds`).

못 보는 것.
- Playwright 가 띄우는 손자(관리 화면 e2e 의 `stack.ts` 가 띄우는 `uv run … serve`)까지 값이 닿는지.
  node 의 `child_process.spawn` 은 환경을 주지 않으면 제 환경을 물려준다(node 문서). 재지 않았다.
- pytest 의 `llm_widget` 표지와 `tests/conftest.py`. 저장소의 pytest 설정을 피하려고 임시 폴더의 빈
  `pytest.ini` 로 돈다. 실제 시험은 `tests/` 안에서 그 설정과 함께 돈다.
- Linux(CI). CI 는 매 푸시에서 이 시험을 돌리지 않는다(`docs/constitution/operations.md` LLM
  테스트).

`--env-file` 에는 슬래시 경로를 준다. 첫 실행에서 역슬래시 경로(`C:\\Users\\…\\probe.env`)를 주자 uv
0.10.8 이 `No environment file found at: C:UsersUser…` 로 끝나, 역슬래시가 빠진 경로를 찾았다. 실제
시험의 `.env` 는 상대 경로라 이 일과 무관하다.

돌리기: 저장소 루트에서 `uv run python .scratch/web-widget/probes/pnpm_spawn.py`. `web/node_modules`
가 깔려 있어야 한다(`pnpm -C web install`). 임시 폴더를 만들고 끝나면 지운다.
"""

from __future__ import annotations

import json
import secrets
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds  # noqa: E402

TIMEOUT = 180

# pytest 가 돌릴 시험. 회차마다 JSON 한 줄을 `PROBE ` 머리와 함께 찍는다. 단언하지 않는다.
TEST_SOURCE = """
import json
import shutil
import subprocess

ROOT = {root!r}
ECHO = {echo!r}


def _report(name, **fields):
    print("PROBE " + json.dumps({{"round": name, **fields}}, ensure_ascii=False), flush=True)


def _run(command, cwd):
    try:
        done = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {{"error": type(error).__name__, "detail": str(error)}}
    return {{"code": done.returncode, "stdout": done.stdout, "stderr": done.stderr[-2000:]}}


def test_by_name():
    _report("이름으로", **_run(["pnpm", "--version"], ROOT))


def test_by_path():
    pnpm = shutil.which("pnpm")
    _report("경로로", which=pnpm, **_run([pnpm, "-C", "web", "exec", "node", ECHO], ROOT))


def test_playwright():
    pnpm = shutil.which("pnpm")
    _report(
        "Playwright",
        which=pnpm,
        **_run([pnpm, "-C", "web/apps/admin", "exec", "playwright", "--version"], ROOT),
    )
"""

ECHO_SOURCE = "process.stdout.write('TOKEN=' + (process.env.AGENT_OS_PROBE_TOKEN ?? '<없음>'));\n"


def _version(command: list[str]) -> str:
    try:
        done = subprocess.run(command, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"<{type(error).__name__}>"
    return done.stdout.strip() or done.stderr.strip()


def _reports(stdout: str) -> dict[str, dict[str, object]]:
    found: dict[str, dict[str, object]] = {}
    for line in stdout.splitlines():
        # `-q -s` 에서는 앞 시험의 진행 점(`.`)이 다음 시험이 찍은 줄 앞에 붙는다.
        start = line.find("PROBE ")
        if start < 0:
            continue
        try:
            report = json.loads(line[start:].removeprefix("PROBE "))
        except json.JSONDecodeError:
            continue
        if isinstance(report, dict) and isinstance(report.get("round"), str):
            found[str(report["round"])] = {str(key): value for key, value in report.items()}
    return found


def main() -> int:
    rounds = Rounds()
    token = secrets.token_hex(8)
    print(f"python: {sys.version.split()[0]}  uv: {_version(['uv', '--version'])}")
    print(f"pnpm: {shutil.which('pnpm')}  node: {_version(['node', '--version'])}")
    with tempfile.TemporaryDirectory(prefix="pnpm-spawn-") as folder:
        work = Path(folder)
        env_file = work / "probe.env"
        env_file.write_text(f"AGENT_OS_PROBE_TOKEN={token}\n", encoding="utf-8")
        echo = work / "echo_env.mjs"
        echo.write_text(ECHO_SOURCE, encoding="utf-8")
        test_file = work / "test_spawn.py"
        test_file.write_text(TEST_SOURCE.format(root=str(ROOT), echo=str(echo)), encoding="utf-8")
        (work / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")

        with rounds.round("uv 직접") as current:
            done = subprocess.run(
                ["uv", "run", "--env-file", env_file.as_posix(), "pnpm", "--version"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=TIMEOUT,
            )
            output = done.stdout + done.stderr
            print(f"[uv 직접] 종료 {done.returncode}: {output.strip()[-300:]}")
            if "Failed to spawn" in output:
                current.mark(measured=True, result="띄우지 못함")
            elif done.returncode == 0 and done.stdout.strip()[:1].isdigit():
                current.mark(measured=True, result=f"떴다 {done.stdout.strip()}")

        done = subprocess.run(
            [
                "uv",
                "run",
                "--env-file",
                env_file.as_posix(),
                "pytest",
                "-q",
                "-s",
                "-p",
                "no:cacheprovider",
                "-c",
                str(work / "pytest.ini"),
                "--rootdir",
                str(work),
                str(test_file),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=TIMEOUT * 3,
        )
        print(f"[pytest] 종료 {done.returncode}: {done.stdout.strip().splitlines()[-1:]}")
        reports = _reports(done.stdout)

        with rounds.round("이름으로") as current:
            report = reports["이름으로"]
            print(f"[이름으로] {report}")
            if report.get("error") == "FileNotFoundError":
                current.mark(measured=True, result="띄우지 못함(FileNotFoundError)")
            elif report.get("code") == 0 and str(report.get("stdout", "")).strip()[:1].isdigit():
                current.mark(measured=True, result=f"떴다 {str(report['stdout']).strip()}")

        with rounds.round("경로로") as current:
            report = reports["경로로"]
            print(f"[경로로] {report}")
            if f"TOKEN={token}" in str(report.get("stdout", "")):
                current.mark(measured=True, result=f"떴고 값이 닿았다({report.get('which')})")
            elif "TOKEN=<없음>" in str(report.get("stdout", "")):
                current.mark(measured=True, result="떴으나 값이 닿지 않았다")

        with rounds.round("Playwright") as current:
            report = reports["Playwright"]
            print(f"[Playwright] {report}")
            if "Version 1." in str(report.get("stdout", "")):
                current.mark(measured=True, result=f"떴다 {str(report['stdout']).strip()}")

    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
