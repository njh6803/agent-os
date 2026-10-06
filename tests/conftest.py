"""헌법 환경 규약: 한국어 출력이 cp949로 깨지지 않게 stdout을 UTF-8로 고정한다.

원칙 II: 환경 부재로 skip된 테스트는 초록이 아니다. 2026-09-28 까지 이 문장에 장치가 없었고
`operations.md` 는 "CI에서는 에러로 만든다" 고 적어 다음 세션이 보호를 믿게 했다(하네스 감사).
skip 이 하나라도 있으면 세션을 실패로 끝낸다. `-m "not llm"` 의 deselect 는 skip 이 아니다.

pre-commit 이 워크트리에서 훅을 돌리면 git 이 `GIT_DIR` 같은 저장소 위치 변수를 자식에
내보낸다. 그 값이 남으면 테스트의 `git init` 이 임시 디렉터리가 아니라 이 저장소를 재초기화한다
(2026-09-28 실측. 공유 config 의 core.bare 가 true 가 되어 체크아웃 전부가 work tree 를 잃었다).
저장소를 가리키는 변수만 벗긴다. 목록은 `tools/run_hooks.py` 가 원천이다 — 러너도 자식 훅에서 같은
것을 벗긴다.

`agent_os` 는 테스트와 같은 체크아웃의 `src` 에서 불려야 한다. `.venv` 의 editable 설치는 절대
경로라, 다른 체크아웃의 `.venv` 인터프리터(주 체크아웃의 것, IDE 가 잡은 것, 활성화된 셸의 것)로
워크트리의 테스트를 돌리면 테스트와 `tools` 는 이 체크아웃 것이 돌고 `agent_os` 는 그쪽 `src` 가
불려 브랜치의 코드가 검사되지 않는다. 2026-10-05 에 그렇게 돌린 테스트가 조용히 초록이었다(손으로
봤다, 워크트리 감사 12). 그래서 세션을 시작하기 전에 멈춘다. 체크아웃은 `tools` 를 불러온 자리로
정한다 — 이 파일의 위치로 정하면 이 파일을 임시 디렉터리에 옮겨 도는 `tests/test_conftest.py` 가
걸린다.
`uv run pytest` 는 그 체크아웃의 `.venv` 를 쓰므로 걸리지 않는다.
"""

import importlib.util
import io
import os
import sys
from pathlib import Path

import pytest

from tools import run_hooks

CHECKOUT = Path(run_hooks.__file__).resolve().parents[1]

for stream in (sys.stdout, sys.stderr):
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")

for name in run_hooks.REPO_LOCATION_VARS:
    os.environ.pop(name, None)


def pytest_configure(config: pytest.Config) -> None:
    spec = importlib.util.find_spec("agent_os")
    origin = None if spec is None or spec.origin is None else Path(spec.origin).resolve()
    if origin is not None and origin.is_relative_to(CHECKOUT / "src"):
        return
    raise pytest.UsageError(
        f"agent_os 가 이 체크아웃({CHECKOUT})의 src 가 아니라 {origin} 에서 불린다. 다른 체크아웃의"
        " .venv 인터프리터다. 이 체크아웃에서 uv run pytest 로 돌린다"
    )


def pytest_sessionfinish(session: pytest.Session, exitstatus: int | pytest.ExitCode) -> None:
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if not isinstance(reporter, pytest.TerminalReporter):
        return
    skipped = reporter.stats.get("skipped", [])
    if not skipped:
        return
    reporter.write_line(
        f"skip {len(skipped)}건. skip된 테스트는 초록이 아니다(원칙 II). -rs 로 이유를 본다",
        red=True,
    )
    session.exitstatus = pytest.ExitCode.TESTS_FAILED
