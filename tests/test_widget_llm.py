"""위젯의 실제 모델 e2e(web-widget 티켓 11, 명세 Testing Decisions 6).

마커 `llm_widget` 의 시험 하나가 위젯 e2e 의 Playwright 프로젝트 `llm` 을 자식 프로세스로 돌린다. 그
프로젝트는 06 의 준비(실제 serve·Next 와 같은 출처의 중계)에서 저장소의 계산 에이전트로 iframe
위젯에 요청 하나를 보내 출력이 서는 것까지 본다. 모델이 도구를 부를지는 단언하지 않는다. 명령은
`uv run --env-file .env pytest -m llm_widget` 이고 원칙 I 의 판정(`-m llm`)과 따로다(ADR 0024 의
2026-10-23 이력). 기본 실행과 `-m llm` 은 이것을 돌리지 않는다. 파이썬 시험이 감싸므로 키가 없으면
실패하는 규칙과 실행 끝의 토큰 합계 줄(`tests/conftest.py`)이 다른 LLM 시험과 같다.

- 프로젝트 `llm` 은 이 시험이 자식의 환경에 준 `AGENT_OS_WIDGET_LLM=1` 이 있을 때만 서고
  (`web/apps/widget/playwright.config.ts`), serve 는 `AGENT_OS_WIDGET_TRACES` 가 준 `tmp_path`
  아래에 트레이스를 남긴다(`e2e/stack.ts`). 두 이름은 `e2e/env.ts` 와 같은 글자다. 키는 이
  프로세스의 환경이 pnpm → Playwright → serve 로 물려 간다.
- pnpm 은 이름이 아니라 `shutil.which` 가 준 경로로 띄운다. 이 PC 의 Windows 에서
  `uv run --env-file` 아래의 pytest 는 `pnpm` 을 이름으로 띄우지 못했다(`FileNotFoundError`,
  `.scratch/web-widget/probes/pnpm_spawn.py`). 그 경로(`pnpm.CMD`)는 cmd.exe 가 명령 줄을 다시
  읽으므로 넘기는 인자는 고정 글자이고 cmd.exe 의 메타 문자(`&`, `^`, `%`)가 들지 않는다. 바뀌는
  값(앱 폴더, 트레이스와 리포트의 자리)은 작업 폴더와 환경으로 준다.
- 기준 다섯. Playwright 의 종료 코드 0 과 JSON 리포터의 통과 1, 건너뜀 0(종료 코드 0 만 보면 모두
  건너뛴 실행이 초록이다). 트레이스에 `llm_called`(키가 serve 에 닿지 않으면 모델 호출이 없다).
  화면에 선 출력이 그 트레이스의 `run_finished` 의 `output` 과 같다. pnpm 을 찾지 못하면 깔라는
  문구로 실패한다. 제한 시간을 넘기면 Playwright 가 띄운 프로세스까지 트리째 끝낸다. 앞의 셋은 실제
  모델과 빌드를 쓰는 한 바퀴의 결과라, 기준마다 멈추지 않고 어긋난 것을 모두 모아 알린다. 뒤의 둘은
  모델 없이 기본 실행에서 잰다.

못 보는 것: POSIX 에서 제 세션을 따로 연 손자는 프로세스 그룹으로 끝내지
못한다(`tools/run_checks.py` 의 `kill_tree`). 제한 시간에 끊으면 준비(globalSetup)의 정리가 돌지
않아 그 임시 폴더(`agent-os-widget-e2e-*`)가 남고, serve·Next 의 출력도 `test-results/` 에 쓰이지
않을 것이다(정리가 쓴다). 그때 실패 메시지에 실리는 것은 Playwright 가 표준 출력에 낸 것뿐이다.
POSIX 에서 이 pytest 를 Ctrl-C 로 끊으면 SIGINT 가 제 세션을 연 자식에 닿지 않고 `_run_tree` 는
제한 시간만 받아, Playwright 와 그것이 띄운 serve·Next 가 시험을 마칠 때까지 남을 것이다. 셋 다
코드를 읽은 것이고 재지 않았다.
"""

import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest
from tools.run_checks import kill_tree

from agent_os.adapters.jsonl import JsonlTrace
from agent_os.core.ports import Trace
from agent_os.sdk import Json, LlmCalled, RunFinished, RunId

REPO_ROOT = Path(__file__).resolve().parents[1]
WIDGET = REPO_ROOT / "web" / "apps" / "widget"
LLM_ENV = "AGENT_OS_WIDGET_LLM"
TRACES_ENV = "AGENT_OS_WIDGET_TRACES"
REPORT_ENV = "PLAYWRIGHT_JSON_OUTPUT_FILE"
# Playwright 의 llm 시험이 화면에 선 출력을 싣는 주석의 이름(`e2e/calc.llm.ts`).
SHOWN_ANNOTATION = "화면의 출력"
# 고정 글자만 둔다(위 독스트링의 cmd.exe).
PLAYWRIGHT = ("exec", "playwright", "test", "--project", "llm", "--reporter", "json")
TIMEOUT = 600
PASSED_ONCE = {"expected": 1, "skipped": 0, "unexpected": 0, "flaky": 0}


def _pnpm() -> str:
    found = shutil.which("pnpm")
    if found is None:
        pytest.fail(
            "pnpm 을 찾지 못했다(shutil.which). pnpm 을 깔고 PATH 에 둔 뒤 다시 돌린다."
            " 판은 web/package.json 의 packageManager 다"
        )
    return found


def _run_tree(
    command: Sequence[str],
    *,
    cwd: Path,
    env: Mapping[str, str],
    log: Path,
    timeout: float,
) -> int | None:
    """`command` 를 띄워 끝나기를 기다리고 종료 코드를 돌려준다. 출력은 `log` 에 쓴다. `timeout`
    초를 넘기면 그 아래 프로세스까지 트리째 끝내고 None 이다. 출력을 파이프가 아니라 파일로 받아,
    남은 손자가 파이프를 쥐어 기다림이 멈추는 일이 없다."""
    with log.open("wb") as out:
        process = subprocess.Popen(
            list(command),
            cwd=cwd,
            env=dict(env),
            stdin=subprocess.DEVNULL,
            stdout=out,
            stderr=subprocess.STDOUT,
            start_new_session=True,  # POSIX 에서 자식이 제 프로세스 그룹을 이끈다
        )
        try:
            return process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            kill_tree(process)
            process.wait()  # kill_tree 가 자식까지 끝내 곧 돌아온다
            return None


@dataclass(frozen=True)
class _Report:
    """Playwright 의 JSON 리포트에서 판정에 쓰는 것."""

    stats: Mapping[str, Json]
    errors: list[str]
    shown: list[str]


def _read_report(path: Path) -> _Report | None:
    if not path.is_file():
        return None
    value: Json = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        return None
    stats = value.get("stats")
    objects = list(_objects(value))
    return _Report(
        stats=stats if isinstance(stats, dict) else {},
        errors=list(_error_messages(objects)),
        shown=sorted(set(_annotations(objects))),
    )


def _objects(value: Json) -> Iterator[dict[str, Json]]:
    """리포트 안의 객체를 깊이와 상관없이 모두."""
    if isinstance(value, dict):
        yield value
        children = list(value.values())
    elif isinstance(value, list):
        children = value
    else:
        return
    for child in children:
        yield from _objects(child)


def _annotations(objects: Sequence[dict[str, Json]]) -> Iterator[str]:
    """`SHOWN_ANNOTATION` 주석의 설명. 시험과 그 결과 양쪽에 실릴 수 있다."""
    for item in objects:
        description = item.get("description")
        if item.get("type") == SHOWN_ANNOTATION and isinstance(description, str):
            yield description


def _error_messages(objects: Sequence[dict[str, Json]]) -> Iterator[str]:
    """준비의 실패(최상위 `errors`)와 시험의 실패(결과의 `errors`)에 적힌 문구."""
    for item in objects:
        errors = item.get("errors")
        if not isinstance(errors, list):
            continue
        for error in errors:
            message = error.get("message") if isinstance(error, dict) else None
            if isinstance(message, str):
                yield message


def _failures(report: _Report | None, traces: Path, code: int) -> list[str]:
    """기준 다섯 가운데 한 바퀴의 결과인 앞의 셋(종료 0·통과 1·건너뜀 0, `llm_called`, 화면과
    트레이스의 출력)에서 어긋난 것을 모두. 시험이 통과해도 정리(globalSetup 이 돌려준 함수)가 던지면
    종료 코드만 0 이 아니다."""
    failures: list[str] = []
    if code != 0:
        failures.append(f"Playwright 가 종료 코드 {code} 로 끝났다")
    if report is None:
        failures.append("Playwright 의 JSON 리포트가 없다")
    else:
        played = {key: report.stats.get(key) for key in PASSED_ONCE}
        if played != PASSED_ONCE:
            failures.append(f"프로젝트 llm 이 통과 1, 건너뜀 0 이 아니다: {played}")
        if failures:
            failures.extend(f"  {message}" for message in report.errors)
    files = sorted(traces.glob("*.jsonl")) if traces.is_dir() else []
    events = [event for file in files for event in _read_trace(file).events]
    if not any(isinstance(event, LlmCalled) for event in events):
        failures.append(
            f"트레이스 {len(files)}개에 llm_called 가 없다. 키가 serve 에 닿지 않았을 수 있다"
        )
    outputs = [event.output for event in events if isinstance(event, RunFinished)]
    shown = [] if report is None else report.shown
    if len(outputs) != 1 or shown != outputs:
        failures.append(
            f"화면에 선 출력 {shown!r} 이 트레이스의 run_finished 출력 {outputs!r} 과 같지 않다"
        )
    return failures


def _read_trace(trace_file: Path) -> Trace:
    """serve 가 남긴 파일을 같은 어댑터로 읽는다. 파일이 있는데 None 이면 어댑터의 결함이다."""
    trace = JsonlTrace(trace_file.parent).read(RunId(trace_file.stem))
    assert trace is not None
    return trace


@pytest.mark.llm_widget
def test_위젯에서_보낸_요청_하나에_계산_에이전트가_실제_모델로_답한다(tmp_path: Path) -> None:
    """바깥 이음매. 실제 브라우저, 실제 serve 와 Next, 같은 출처의 중계, 사이트 파일과 서명 토큰,
    실제 모델이 한 길에 든다. 끝까지 돈 실행이면 준비가 띄운 프로세스의 출력이
    `web/apps/widget/test-results/` 에 남는다(제한 시간에 끊긴 실행은 머리 독스트링의 못 보는
    것)."""
    if "ANTHROPIC_API_KEY" not in os.environ:
        # assert 로 두면 pytest 가 실패 출력에 os.environ 의 repr 을 싣는다(대기열 463).
        pytest.fail("ANTHROPIC_API_KEY 가 없다. .env 를 확인한다")
    pnpm = _pnpm()
    traces = tmp_path / "traces"
    report = tmp_path / "report.json"
    log = tmp_path / "playwright.log"
    env = {**os.environ, LLM_ENV: "1", TRACES_ENV: str(traces), REPORT_ENV: str(report)}

    code = _run_tree([pnpm, *PLAYWRIGHT], cwd=WIDGET, env=env, log=log, timeout=TIMEOUT)

    output = log.read_text(encoding="utf-8", errors="replace")
    assert code is not None, f"{TIMEOUT}초 안에 끝나지 않아 프로세스 트리를 끝냈다:\n{output}"
    failures = _failures(_read_report(report), traces, code)
    assert not failures, "\n".join([*failures, f"Playwright 종료 {code}, 출력:", output])


def test_pnpm_을_찾지_못하면_깔라는_문구로_실패한다(monkeypatch: pytest.MonkeyPatch) -> None:
    def not_found(_name: str) -> None:
        return None

    monkeypatch.setattr(shutil, "which", not_found)

    with pytest.raises(pytest.fail.Exception, match="pnpm 을 깔고"):
        _pnpm()


def test_끝난_명령의_종료_코드를_돌려주고_출력을_기록에_남긴다(tmp_path: Path) -> None:
    log = tmp_path / "log"

    code = _run_tree(
        [sys.executable, "-c", "print('끝났다'); raise SystemExit(3)"],
        cwd=tmp_path,
        env=dict(os.environ),
        log=log,
        timeout=60,
    )

    assert code == 3
    assert "끝났다" in log.read_text(encoding="utf-8")


def _stops_growing(path: Path, within: float) -> bool:
    """`within` 초 안에 파일이 1초 동안 자라지 않으면 참. 끝내기가 늦은 것과 끝내지 못한 것을
    가르려고 한 번만 견주지 않고 기한까지 거듭 견준다(`tests/tools/test_run_checks.py` 의 같은
    이름)."""
    deadline = time.monotonic() + within
    while time.monotonic() < deadline:
        before = path.stat().st_size
        time.sleep(1)
        if path.stat().st_size == before:
            return True
    return False


def _shell_wrapped(folder: Path, script: str) -> list[str]:
    """`folder` 의 `script` 를 이 파이썬으로 돌리는 셸 스크립트를 쓰고 그 명령을 준다. 실제 시험의
    `pnpm.CMD` 가 cmd.exe 로 읽혀 node 에 스크립트 파일을 넘기듯, 셸이 자식이 되고 파이썬은 그
    아래에 뜬다. 윈도우는 `.cmd`, POSIX 는 실행 권한을 준 `sh` 스크립트다(`.claude/rules/tests.md`).
    스크립트는 작업 폴더 기준의 이름으로 적어, cmd.exe 가 `.cmd` 를 읽는 코드 페이지에 `tmp_path`
    의 한국어가 닿지 않게 한다."""
    if sys.platform == "win32":
        launcher = folder / "child.cmd"
        launcher.write_text(f'@"{sys.executable}" {script}\r\n', encoding="utf-8")
    else:
        launcher = folder / "child.sh"
        launcher.write_text(f'#!/bin/sh\n"{sys.executable}" {script}\n', encoding="utf-8")
        launcher.chmod(0o755)
    return [str(launcher)]


def test_제한_시간을_넘기면_손자까지_끝내고_None_이다(tmp_path: Path) -> None:
    """실제 시험에서는 pnpm 이 자식이고(윈도우는 `pnpm.CMD` 를 읽는 cmd.exe) Playwright 와 그것이
    띄운 serve·Next 가 그 아래에 뜬다. `.cmd` 를 거친 자식만 끊으면 그 아래가 남을 수 있다(티켓 11).
    여기서도 셸 스크립트가 자식이고(`_shell_wrapped`), 그것이 띄운 파이썬이 손자를 띄우고 잔다.
    손자는 0.1초마다 표지 파일을 키우고, 아무도 끝내지 못해도 60초 뒤 스스로 끝난다(빨간 회차가
    고아를 오래 남기지 않게).

    제한(5초)은 셸과 그 아래가 뜨는 시간보다 넉넉하게 둔다(`.claude/rules/tests.md`).
    """
    beat = tmp_path / "beat"
    grandchild = (
        "import pathlib, time\n"
        "end = time.monotonic() + 60\n"
        "while time.monotonic() < end:\n"
        f"    with pathlib.Path({str(beat)!r}).open('a') as f:\n"
        "        f.write('.')\n"
        "    time.sleep(0.1)\n"
    )
    (tmp_path / "child.py").write_text(
        "import subprocess, sys, time\n"
        f"subprocess.Popen([sys.executable, '-c', {grandchild!r}])\n"
        "time.sleep(120)\n",
        encoding="utf-8",
    )

    code = _run_tree(
        _shell_wrapped(tmp_path, "child.py"),
        cwd=tmp_path,
        env=dict(os.environ),
        log=tmp_path / "log",
        timeout=5,
    )

    assert code is None
    assert beat.exists(), "손자가 제한 시간 안에 뜨지 않아 끝내기를 재지 못했다"
    assert _stops_growing(beat, within=30), "제한 시간을 넘긴 뒤에도 손자가 살아 있다"
