"""헌법 환경 규약: 한국어 출력이 cp949로 깨지지 않게 stdout을 UTF-8로 고정한다.

원칙 II: 환경 부재로 skip된 테스트는 초록이 아니다. 2026-09-28 까지 이 문장에 장치가 없었고
`operations.md` 는 "CI에서는 에러로 만든다" 고 적어 다음 세션이 보호를 믿게 했다(하네스 감사).
skip 이 하나라도 있으면 세션을 실패로 끝낸다. `-m "not llm"` 의 deselect 는 skip 이 아니다.

pre-commit 이 워크트리에서 훅을 돌리면 git 이 `GIT_DIR` 같은 저장소 위치 변수를 자식에
내보낸다. 그 값이 남으면 테스트의 `git init` 이 임시 디렉터리가 아니라 이 저장소를 재초기화한다
(2026-09-28 실측. 공유 config 의 core.bare 가 true 가 되어 체크아웃 전부가 work tree 를 잃었다).
저장소를 가리키는 변수만 벗긴다. 목록은 `tools/run_hooks.py` 가 원천이다 — 러너도 자식 훅에서 같은
것을 벗긴다.
"""

import io
import os
import sys

import pytest
from tools.run_hooks import REPO_LOCATION_VARS

for stream in (sys.stdout, sys.stderr):
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")

for name in REPO_LOCATION_VARS:
    os.environ.pop(name, None)


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
