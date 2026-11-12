"""위젯의 실제 모델 e2e(web-widget 티켓 11, 명세 Testing Decisions 6).

마커 `llm_widget` 의 시험 하나가 위젯 e2e 의 Playwright 프로젝트 `llm` 을 자식 프로세스로 돌린다. 그
프로젝트는 06 의 준비(실제 serve·Next 와 같은 출처의 중계)에서 iframe 위젯에 요청을 보내 출력이 서는
것까지 본다. 사례는 둘이다. 저장소의 계산 에이전트(`calc`)에게 계산을 묻는 것과, 기본 에이전트
`assistant` 에게 등록된 문서에 근거가 있는 질문을 보내 출처가 붙은 답이 서는 것이다(base-agent 티켓
06). 모델이 도구를 부를지는 계산 사례에서 단언하지 않고, `assistant` 사례는 트레이스에 성공한
`search` 가 있는지 본다. 명령은 `uv run --env-file .env pytest -m llm_widget` 이고 원칙 I 의 판정
(`-m llm`)과 따로다(ADR 0024 의 2026-10-23 이력). 기본 실행과 `-m llm` 은 이것을 돌리지 않는다.
파이썬 시험이 감싸므로 키가 없으면 실패하는 규칙과 실행 끝의 토큰 합계 줄(`tests/conftest.py`)이
다른 LLM 시험과 같다.

- 프로젝트 `llm` 은 이 시험이 자식의 환경에 준 `AGENT_OS_WIDGET_LLM=1` 이 있을 때만 서고
  (`web/apps/widget/playwright.config.ts`), serve 는 `AGENT_OS_WIDGET_TRACES` 가 준 `tmp_path`
  아래에 트레이스를 남긴다(`e2e/stack.ts` 가 패키지 `@agent-os/e2e-stack` 의 `startServe` 로
  띄운다). 두 이름은 `e2e/env.ts` 와 같은 글자다. 키는 이
  프로세스의 환경이 pnpm → Playwright → serve 로 물려 간다.
- `assistant` 사례의 문서는 이 시험이 띄운 가짜 문서 검색 서버(`tests/fake_doc_search.py`)의
  표본이다. 그 주소를 `AGENT_OS_WIDGET_DOC_SEARCH_URL` 로, 서버가 기대하는 `Authorization` 값을
  `DOC_SEARCH_AUTHORIZATION` 으로 자식의 환경에 준다(준비가 `doc-search` 연결의 주소를 그 값으로
  바꿔 쓴다. `e2e/env.ts`, `pointDocSearchAt`). 서버의 기록은 `tmp_path` 밖에 두어 토큰 합계가 그
  기록을 트레이스로 세지 않게 한다.
- pnpm 은 이름이 아니라 `shutil.which` 가 준 경로로 띄운다. 이 PC 의 Windows 에서
  `uv run --env-file` 아래의 pytest 는 `pnpm` 을 이름으로 띄우지 못했다(`FileNotFoundError`,
  `.scratch/web-widget/probes/pnpm_spawn.py`). 그 경로(`pnpm.CMD`)는 cmd.exe 가 명령 줄을 다시
  읽으므로 넘기는 인자는 고정 글자이고 cmd.exe 의 메타 문자(`&`, `^`, `%`)가 들지 않는다. 바뀌는
  값(앱 폴더, 트레이스와 리포트의 자리)은 작업 폴더와 환경으로 준다.
- 기준 다섯. Playwright 의 종료 코드 0 과 JSON 리포터의 통과 2(사례 수), 건너뜀 0(종료 코드 0 만
  보면 모두 건너뛴 실행이 초록이다). 사례마다 그 에이전트로 시작한 실행(`run_started` 의 `agent`)을
  짝지어, 그 실행의 트레이스에 `llm_called`(키가 serve 에 닿지 않으면 모델 호출이 없다). 화면의
  출력은 사례가 연 에이전트의 이름과 함께 리포트에 실리고, 계산 사례는 화면에 선 출력이 그 실행의
  `run_finished` 의 `output` 과 같다. `assistant` 사례는 글자를 견주지 않고(낱말은 Playwright 사례가
  본다) 그 실행에 성공한 `search` 가 있는지 본다. pnpm 을 찾지 못하면 깔라는 문구로 실패한다. 제한
  시간을 넘기면 Playwright 가 띄운 프로세스까지 트리째 끝낸다. 앞의 셋은 실제 모델과 빌드를 쓰는 한
  바퀴의 결과라, 기준마다 멈추지 않고 어긋난 것을 모두 모아 알린다. 뒤의 둘은 모델 없이 기본
  실행에서 잰다.

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
from datetime import UTC, datetime
from pathlib import Path

import pytest
from tests.fake_doc_search import serving
from tools.run_checks import kill_tree

from agent_os.adapters.jsonl import JsonlTrace
from agent_os.core.ports import Trace, UnknownEvent
from agent_os.sdk import (
    AgentName,
    Event,
    Json,
    LlmCalled,
    Principal,
    RunFinished,
    RunId,
    RunStarted,
    ToolCalled,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
WIDGET = REPO_ROOT / "web" / "apps" / "widget"
LLM_ENV = "AGENT_OS_WIDGET_LLM"
TRACES_ENV = "AGENT_OS_WIDGET_TRACES"
DOC_SEARCH_URL_ENV = "AGENT_OS_WIDGET_DOC_SEARCH_URL"
DOC_SEARCH_AUTHORIZATION_ENV = "DOC_SEARCH_AUTHORIZATION"
# 가짜 검색 서버가 기대하는 값. 시험용이라 비밀이 아니다(원칙 V: 서버의 기록에 원문이 실린다).
DOC_SEARCH_AUTHORIZATION = "Bearer widget-llm-test-token"
REPORT_ENV = "PLAYWRIGHT_JSON_OUTPUT_FILE"
# Playwright 의 llm 사례가 화면에 선 출력을 싣는 주석의 이름(`e2e/llm-ask.ts`). 설명은 `agent` 와
# `text` 를 든 JSON 글이다.
SHOWN_ANNOTATION = "화면의 출력"
# 사례가 여는 에이전트. 사례마다 하나다(`e2e/calc.llm.ts`, `e2e/assistant.llm.ts`).
CALC = "calc"
ASSISTANT = "assistant"
CASES = (CALC, ASSISTANT)
# 고정 글자만 둔다(위 독스트링의 cmd.exe).
PLAYWRIGHT = ("exec", "playwright", "test", "--project", "llm", "--reporter", "json")
TIMEOUT = 600
PASSED_ALL = {"expected": len(CASES), "skipped": 0, "unexpected": 0, "flaky": 0}


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
    # 에이전트 이름 → 그 사례가 화면에 선 출력들.
    shown: Mapping[str, list[str]]


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
        shown=_by_agent(set(_annotations(objects))),
    )


def _by_agent(shown: set[tuple[str, str]]) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for agent, text in sorted(shown):
        grouped.setdefault(agent, []).append(text)
    return grouped


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


def _annotations(objects: Sequence[dict[str, Json]]) -> Iterator[tuple[str, str]]:
    """`SHOWN_ANNOTATION` 주석의 설명이 든 (에이전트, 화면의 출력). 시험과 그 결과 양쪽에 실릴 수
    있어 같은 쌍이 거듭 나온다."""
    for item in objects:
        description = item.get("description")
        if item.get("type") != SHOWN_ANNOTATION or not isinstance(description, str):
            continue
        try:
            shown: Json = json.loads(description)
        except json.JSONDecodeError:
            # 읽지 못한 주석은 뺀다. 그 사례는 화면에 선 출력이 없는 것으로 보여 `_failures` 가
            # 알린다.
            continue
        if not isinstance(shown, dict):
            continue
        agent, text = shown.get("agent"), shown.get("text")
        if isinstance(agent, str) and isinstance(text, str):
            yield agent, text


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
    """기준 다섯 가운데 한 바퀴의 결과인 앞의 셋(종료 0·통과 2·건너뜀 0, 사례마다의 `llm_called`,
    사례마다의 화면과 트레이스)에서 어긋난 것을 모두. 시험이 통과해도 정리(globalSetup 이 돌려준
    함수)가 던지면 종료 코드만 0 이 아니다."""
    failures: list[str] = []
    if code != 0:
        failures.append(f"Playwright 가 종료 코드 {code} 로 끝났다")
    if report is None:
        failures.append("Playwright 의 JSON 리포트가 없다")
    else:
        played = {key: report.stats.get(key) for key in PASSED_ALL}
        if played != PASSED_ALL:
            failures.append(f"프로젝트 llm 이 통과 {len(CASES)}, 건너뜀 0 이 아니다: {played}")
        if failures:
            failures.extend(f"  {message}" for message in report.errors)
    runs = _runs(traces)
    for agent in CASES:
        mine = [events for name, events in runs if name == agent]
        if len(mine) != 1:
            failures.append(
                f"에이전트 {agent} 로 시작한 실행이 {len(mine)}개다(트레이스 {len(runs)}개)."
                " 사례마다 하나여야 한다"
            )
            continue
        shown = [] if report is None else report.shown.get(agent, [])
        failures.extend(_case_failures(agent, mine[0], shown))
    return failures


def _runs(traces: Path) -> list[tuple[str, Sequence[Event | UnknownEvent]]]:
    """폴더의 트레이스마다 (시작한 에이전트, 이벤트). 시작 이벤트가 없는 트레이스는 뺀다."""
    files = sorted(traces.glob("*.jsonl")) if traces.is_dir() else []
    runs: list[tuple[str, Sequence[Event | UnknownEvent]]] = []
    for file in files:
        events = _read_trace(file).events
        started = next((event for event in events if isinstance(event, RunStarted)), None)
        if started is not None:
            runs.append((started.agent, events))
    return runs


def _case_failures(
    agent: str, events: Sequence[Event | UnknownEvent], shown: list[str]
) -> list[str]:
    """사례 하나의 실행(`events`)과 그 사례가 화면에 선 출력(`shown`)에서 어긋난 것."""
    failures: list[str] = []
    if not any(isinstance(event, LlmCalled) for event in events):
        failures.append(
            f"에이전트 {agent} 의 실행에 llm_called 가 없다. 키가 serve 에 닿지 않았을 수 있다"
        )
    outputs = [event.output for event in events if isinstance(event, RunFinished)]
    if agent == CALC:
        # 글자를 견주는 것은 계산 사례 하나다.
        if len(outputs) != 1 or shown != outputs:
            failures.append(
                f"{agent}: 화면에 선 출력 {shown!r} 이 트레이스의 run_finished 출력 {outputs!r} 과"
                " 같지 않다"
            )
    else:
        # 화면의 낱말은 Playwright 사례가 보고, 여기서는 화면에 출력이 섰고 실행이 끝났는지만 본다.
        if len(shown) != 1 or len(outputs) != 1:
            failures.append(
                f"{agent}: 화면에 선 출력 {shown!r} 과 트레이스의 run_finished 출력 {outputs!r} 이"
                " 하나씩이 아니다"
            )
        if not any(isinstance(e, ToolCalled) and e.tool == "search" and e.ok for e in events):
            failures.append(f"에이전트 {agent} 의 실행에 성공한 search 호출이 없다")
    return failures


def _read_trace(trace_file: Path) -> Trace:
    """serve 가 남긴 파일을 같은 어댑터로 읽는다. 파일이 있는데 None 이면 어댑터의 결함이다."""
    trace = JsonlTrace(trace_file.parent).read(RunId(trace_file.stem))
    assert trace is not None
    return trace


@pytest.mark.llm_widget
def test_위젯에서_보낸_요청에_계산_에이전트와_기본_에이전트가_실제_모델로_답한다(
    tmp_path: Path, tmp_path_factory: pytest.TempPathFactory
) -> None:
    """바깥 이음매. 실제 브라우저, 실제 serve 와 Next, 같은 출처의 중계, 사이트 파일과 서명 토큰,
    가짜 문서 검색 서버, 실제 모델이 한 길에 든다. 끝까지 돈 실행이면 준비가 띄운 프로세스의
    출력이 `web/apps/widget/test-results/` 에 남는다(제한 시간에 끊긴 실행은 머리 독스트링의 못
    보는 것)."""
    if "ANTHROPIC_API_KEY" not in os.environ:
        # assert 로 두면 pytest 가 실패 출력에 os.environ 의 repr 을 싣는다(대기열 463).
        pytest.fail("ANTHROPIC_API_KEY 가 없다. .env 를 확인한다")
    pnpm = _pnpm()
    traces = tmp_path / "traces"
    report = tmp_path / "report.json"
    log = tmp_path / "playwright.log"
    # 서버의 기록(record.jsonl)이 토큰 합계에 트레이스로 세이지 않도록 tmp_path 밖에 둔다.
    server_folder = tmp_path_factory.mktemp("widget_doc_search")

    with serving(server_folder, "--expect-authorization", DOC_SEARCH_AUTHORIZATION) as doc_search:
        env = {
            **os.environ,
            LLM_ENV: "1",
            TRACES_ENV: str(traces),
            REPORT_ENV: str(report),
            DOC_SEARCH_URL_ENV: doc_search.url,
            DOC_SEARCH_AUTHORIZATION_ENV: DOC_SEARCH_AUTHORIZATION,
        }
        code = _run_tree([pnpm, *PLAYWRIGHT], cwd=WIDGET, env=env, log=log, timeout=TIMEOUT)
        served = [call["name"] for call in doc_search.tool_calls()]

    output = log.read_text(encoding="utf-8", errors="replace")
    assert code is not None, f"{TIMEOUT}초 안에 끝나지 않아 프로세스 트리를 끝냈다:\n{output}"
    failures = _failures(_read_report(report), traces, code)
    if "search" not in served:
        failures.append(f"가짜 문서 검색 서버가 받은 도구 호출 {served!r} 에 search 가 없다")
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


# --- 사례별 짝짓기(`_failures`). 모델 없이 가짜 트레이스와 가짜 리포트로 본다
# ---------------------------

NOW = datetime(2026, 11, 12, 12, 0, tzinfo=UTC)
CALC_OUTPUT = "2 더하기 3은 5입니다."
ASSISTANT_OUTPUT = (
    "육아휴직은 1년까지 쓸 수 있습니다. [1]\n\n출처\n1. 육아휴직 업무편람 (갱신일 2026-10-01)"
)


def _write_run(
    traces: Path,
    run_id: str,
    agent: str,
    output: str,
    *,
    llm_calls: int = 1,
    searches: Sequence[bool] = (),
) -> None:
    """`agent` 로 시작해 모델을 `llm_calls` 번 부르고, `searches` 의 성공 여부대로 `search` 를 부른
    뒤 `output` 으로 끝난 실행의 트레이스 하나를 `traces` 에 쓴다."""
    trace = JsonlTrace(traces)
    rid = RunId(run_id)
    events: list[Event] = [
        RunStarted(
            run_id=rid, ts=NOW, agent=AgentName(agent), request="질문", principal=Principal("p")
        )
    ]
    events.extend(
        LlmCalled(run_id=rid, ts=NOW, model="m", input_tokens=1, output_tokens=1)
        for _ in range(llm_calls)
    )
    events.extend(ToolCalled(run_id=rid, ts=NOW, tool="search", ok=ok) for ok in searches)
    events.append(RunFinished(run_id=rid, ts=NOW, output=output))
    for event in events:
        trace.write(event)


def _report(**shown: list[str]) -> _Report:
    return _Report(stats=PASSED_ALL, errors=[], shown=shown)


def test_두_사례가_각자의_실행과_짝이_맞으면_어긋남이_없다(tmp_path: Path) -> None:
    _write_run(tmp_path, "r-calc", CALC, CALC_OUTPUT)
    _write_run(tmp_path, "r-assistant", ASSISTANT, ASSISTANT_OUTPUT, searches=[True])
    report = _report(calc=[CALC_OUTPUT], assistant=[ASSISTANT_OUTPUT])

    assert _failures(report, tmp_path, 0) == []


def test_assistant_사례는_화면의_글을_트레이스의_출력과_글자로_견주지_않는다(
    tmp_path: Path,
) -> None:
    _write_run(tmp_path, "r-calc", CALC, CALC_OUTPUT)
    _write_run(tmp_path, "r-assistant", ASSISTANT, ASSISTANT_OUTPUT, searches=[True])
    report = _report(calc=[CALC_OUTPUT], assistant=["위첨자와 작은 글자로 그린 같은 답"])

    assert _failures(report, tmp_path, 0) == []


def test_계산_사례의_화면_글이_그_실행의_출력과_다르면_알린다(tmp_path: Path) -> None:
    _write_run(tmp_path, "r-calc", CALC, CALC_OUTPUT)
    _write_run(tmp_path, "r-assistant", ASSISTANT, ASSISTANT_OUTPUT, searches=[True])
    report = _report(calc=["2 더하기 3은 6입니다."], assistant=[ASSISTANT_OUTPUT])

    failures = _failures(report, tmp_path, 0)

    assert len(failures) == 1
    assert failures[0].startswith("calc")
    assert "화면에 선 출력 ['2 더하기 3은 6입니다.']" in failures[0]


def test_assistant_의_실행에_성공한_search_가_없으면_알린다(tmp_path: Path) -> None:
    _write_run(tmp_path, "r-calc", CALC, CALC_OUTPUT)
    _write_run(tmp_path, "r-assistant", ASSISTANT, ASSISTANT_OUTPUT, searches=[False])
    report = _report(calc=[CALC_OUTPUT], assistant=[ASSISTANT_OUTPUT])

    failures = _failures(report, tmp_path, 0)

    assert len(failures) == 1
    assert "assistant 의 실행에 성공한 search 호출이 없다" in failures[0]


def test_사례의_실행에_llm_called_가_없으면_그_에이전트를_짚어_알린다(tmp_path: Path) -> None:
    _write_run(tmp_path, "r-calc", CALC, CALC_OUTPUT)
    _write_run(tmp_path, "r-assistant", ASSISTANT, ASSISTANT_OUTPUT, llm_calls=0, searches=[True])
    report = _report(calc=[CALC_OUTPUT], assistant=[ASSISTANT_OUTPUT])

    failures = _failures(report, tmp_path, 0)

    assert failures == [
        "에이전트 assistant 의 실행에 llm_called 가 없다. 키가 serve 에 닿지 않았을 수 있다"
    ]


def test_사례의_에이전트로_시작한_실행이_하나가_아니면_알린다(tmp_path: Path) -> None:
    _write_run(tmp_path, "r-calc", CALC, CALC_OUTPUT)
    report = _report(calc=[CALC_OUTPUT], assistant=[ASSISTANT_OUTPUT])

    failures = _failures(report, tmp_path, 0)

    assert len(failures) == 1
    assert "assistant 로 시작한 실행이 0개다" in failures[0]


def test_JSON_이_아닌_화면_주석은_뺀_채_그_사례를_화면이_빈_것으로_알린다(tmp_path: Path) -> None:
    _write_run(tmp_path, "r-calc", CALC, CALC_OUTPUT)
    _write_run(tmp_path, "r-assistant", ASSISTANT, ASSISTANT_OUTPUT, searches=[True])
    notes: list[dict[str, Json]] = [
        {"type": SHOWN_ANNOTATION, "description": "JSON 이 아닌 글"},
        {"type": SHOWN_ANNOTATION, "description": json.dumps({"agent": CALC, "text": CALC_OUTPUT})},
    ]
    shown = _by_agent(set(_annotations(notes)))

    failures = _failures(_Report(stats=PASSED_ALL, errors=[], shown=shown), tmp_path, 0)

    assert len(failures) == 1
    assert "assistant: 화면에 선 출력 []" in failures[0]


def test_통과한_사례가_둘이_아니면_알린다(tmp_path: Path) -> None:
    _write_run(tmp_path, "r-calc", CALC, CALC_OUTPUT)
    _write_run(tmp_path, "r-assistant", ASSISTANT, ASSISTANT_OUTPUT, searches=[True])
    report = _Report(
        stats={"expected": 0, "skipped": 2, "unexpected": 0, "flaky": 0},
        errors=[],
        shown={CALC: [CALC_OUTPUT], ASSISTANT: [ASSISTANT_OUTPUT]},
    )

    failures = _failures(report, tmp_path, 0)

    assert failures == [
        "프로젝트 llm 이 통과 2, 건너뜀 0 이 아니다: "
        "{'expected': 0, 'skipped': 2, 'unexpected': 0, 'flaky': 0}"
    ]
