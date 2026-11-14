"""위젯 미리보기 페이지의 실제 모델 e2e(pilot-portal 티켓 09, 명세 "실제 모델 e2e 하나").

마커 `llm_portal` 의 시험 하나가 위젯 미리보기 페이지 e2e 의 Playwright 프로젝트 `llm` 을 자식
프로세스로 돌린다. 그 프로젝트는 실제 serve·위젯 Next·위젯 미리보기 페이지와 같은 출처의 중계
위에서, `?site=` 없이 연 첫 사이트(익명, 에이전트 `calc`)의 고지 덮개를 확인하고 요청 하나를 보내
출력이 서는 것과 실행 주체의 `anon-` 접두까지 본다(주체는 Playwright 사례가 읽는다). 모델이 도구를
부를지는 단언하지 않는다. 명령은 `uv run --env-file .env pytest -m llm_portal` 이고 원칙 I 의
판정(`-m llm`)과 위젯의 것(`-m llm_widget`)과 따로다. 기본 실행과 `-m llm` 은 이것을 돌리지 않는다.
파이썬 시험이 감싸므로 키가 없으면 실패하는 규칙과 실행 끝의 토큰 합계 줄(`tests/conftest.py`)이
다른 LLM 시험과 같다.

위젯의 래퍼(`tests/test_widget_llm.py`)와 같은 모양이다. 뼈대(pnpm 경로, 트리째 끝내기, 기준)는 그
파일이 원천이다. 여기는 같은 코드를 따로 두었다(그 파일의 변이 표가 그 파일의 글자를 겨눠 옮기지
않았다). 제한 시간에 끊기와 pnpm 부재의 시험은 위젯 쪽 사본만 잰다. 이 사본이 위젯 쪽과 갈라져도 그
시험은 잡지 못한다.

- 프로젝트 `llm` 은 이 시험이 자식의 환경에 준 `AGENT_OS_PORTAL_LLM=1` 이 있을 때만 서고
  (`web/apps/portal/playwright.config.ts`), serve 는 `AGENT_OS_PORTAL_TRACES` 가 준 `tmp_path`
  아래에 트레이스를 남긴다(`e2e/stack.ts`). 두 이름은 `e2e/env.ts` 와 같은 글자다. 키는 이
  프로세스의 환경이 pnpm → Playwright → serve 로 물려 간다.
- 기준 셋. Playwright 의 종료 코드 0 과 JSON 리포터의 통과 1, 건너뜀 0(종료 코드 0 만 보면 모두
  건너뛴 실행이 초록이다). 트레이스에 `llm_called`(키가 serve 에 닿지 않으면 모델 호출이 없다).
  화면에 선 출력이 그 트레이스의 `run_finished` 의 `output` 에서 온 글이다(화면은 마크다운 부품이
  그린 글이라 글자 그대로가 아니라 기호를 뗀 글이 원문의 부분열인지 본다. 규칙은 위젯 래퍼와 함께
  부르는 `tests/screen_text.py`). 기준마다 멈추지 않고 어긋난 것을 모두 모아 알린다.
- pnpm 은 이름이 아니라 `shutil.which` 가 준 경로로 띄운다(윈도우의 `pnpm.CMD` 는 cmd.exe 가 명령
  줄을 다시 읽으므로 넘기는 인자는 고정 글자다. 이유는 위젯 래퍼의 독스트링).

못 보는 것은 위젯 래퍼의 독스트링과 같다: 제한 시간에 끊으면 준비의 정리가 돌지 않아 그 임시 폴더
(`agent-os-portal-e2e-*`)가 남고, POSIX 에서 Ctrl-C 로 끊으면 자식이 남을 수 있다. 위젯 래퍼의
독스트링처럼 코드를 읽은 것이고 이 사본에서 재지 않았다.
"""

import json
import os
import shutil
import subprocess
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import pytest
from tests.screen_text import screen_matches_output
from tools.run_checks import kill_tree

from agent_os.adapters.jsonl import JsonlTrace
from agent_os.core.ports import Trace
from agent_os.sdk import Json, LlmCalled, RunFinished, RunId

REPO_ROOT = Path(__file__).resolve().parents[1]
PORTAL = REPO_ROOT / "web" / "apps" / "portal"
LLM_ENV = "AGENT_OS_PORTAL_LLM"
TRACES_ENV = "AGENT_OS_PORTAL_TRACES"
REPORT_ENV = "PLAYWRIGHT_JSON_OUTPUT_FILE"
# Playwright 의 llm 사례가 화면에 선 출력을 싣는 주석의 이름(`e2e/calc.llm.ts`).
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
    """기준 셋(종료 0·통과 1·건너뜀 0, `llm_called`, 화면과 트레이스의 출력)에서 어긋난 것을 모두.
    시험이 통과해도 정리(globalSetup 이 돌려준 함수)가 던지면 종료 코드만 0 이 아니다."""
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
    if len(outputs) != 1 or len(shown) != 1 or not screen_matches_output(shown[0], outputs[0]):
        failures.append(
            f"화면에 선 출력 {shown!r} 이 트레이스의 run_finished 출력 {outputs!r} 에서 온 글로"
            " 보이지 않는다(기호를 뗀 글이 원문의 부분열이 아니거나 화면 글이 비었다)"
        )
    return failures


def _read_trace(trace_file: Path) -> Trace:
    """serve 가 남긴 파일을 같은 어댑터로 읽는다. 파일이 있는데 None 이면 어댑터의 결함이다."""
    trace = JsonlTrace(trace_file.parent).read(RunId(trace_file.stem))
    assert trace is not None
    return trace


@pytest.mark.llm_portal
def test_위젯_미리보기_페이지에서_고지를_확인하고_보낸_요청에_계산_에이전트가_실제_모델로_답한다(
    tmp_path: Path,
) -> None:
    """바깥 이음매. 실제 브라우저, 실제 serve 와 위젯 Next 와 위젯 미리보기 페이지, 같은 출처의
    중계, 사이트 파일과 위젯 미리보기 페이지가 서명한 토큰, 실제 모델이 한 길에 든다. 끝까지 돈
    실행이면 준비가 띄운 프로세스의 출력이 `web/apps/portal/test-results/` 에 남는다(제한 시간에
    끊긴 실행은 머리 독스트링의 못 보는 것)."""
    if "ANTHROPIC_API_KEY" not in os.environ:
        # assert 로 두면 pytest 가 실패 출력에 os.environ 의 repr 을 싣는다(대기열 463).
        pytest.fail("ANTHROPIC_API_KEY 가 없다. .env 를 확인한다")
    pnpm = _pnpm()
    traces = tmp_path / "traces"
    report = tmp_path / "report.json"
    log = tmp_path / "playwright.log"
    env = {**os.environ, LLM_ENV: "1", TRACES_ENV: str(traces), REPORT_ENV: str(report)}

    code = _run_tree([pnpm, *PLAYWRIGHT], cwd=PORTAL, env=env, log=log, timeout=TIMEOUT)

    output = log.read_text(encoding="utf-8", errors="replace")
    assert code is not None, f"{TIMEOUT}초 안에 끝나지 않아 프로세스 트리를 끝냈다:\n{output}"
    failures = _failures(_read_report(report), traces, code)
    assert not failures, "\n".join([*failures, f"Playwright 종료 {code}, 출력:", output])
