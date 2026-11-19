"""헌법 환경 규약: 한국어 출력이 cp949로 깨지지 않게 stdout을 UTF-8로 고정한다.

원칙 II: 환경 부재로 skip된 테스트는 초록이 아니다. 2026-09-28 까지 이 문장에 장치가 없었고
`operations.md` 는 "CI에서는 에러로 만든다" 고 적어 다음 세션이 보호를 믿게 했다(하네스 감사).
skip 이 하나라도 있으면 세션을 실패로 끝낸다. 기본 실행의 마커 제외(`pyproject.toml` 의 `addopts`
의 `-m`, 네 LLM 마커를 뺀다)로 생기는 deselect 는 skip 이 아니다.

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

실제 모델을 부르는 마커(`llm`, `llm_widget`, `llm_portal`, `llm_local`)의 테스트가 돌았으면 실행
끝의 결과 요약 바로 위에, 그 테스트들이 `tmp_path` 에 남긴 트레이스의 토큰 합계를 찍는다(대기열
113). `llm_widget` 과 `llm_portal` 의 시험은 serve 의 트레이스 자리로 `tmp_path` 아래를
넘기고(`tests/test_widget_llm.py`, `tests/test_portal_llm.py`), `llm_local` 의 시험은 CLI 의
`--traces` 로 넘긴다(`tests/test_local_model_llm.py`). 세는 법과 못 보는 것은
`tools/llm_tokens.py` 가 원천이다. 그 테스트가 하나도 돌지 않은 실행(기본 실행)에서는 찍지 않는다. 0
이 찍히면 LLM 테스트를 돌렸다고 읽힌다.

매개변수 id 는 `pyproject.toml` 의 옵션이 이스케이프를 꺼 한국어를 그대로 둔다(대기열 56). 그 옵션은
줄바꿈 같은 인쇄되지 않는 문자도 그대로 두어 그런 값의 id 가 출력 줄을 갈랐다(2026-10-11, 여섯 개).
문자열 값에 그런 문자가 있으면 그 문자만 `\\n` 꼴로 되돌린다. 바이트 값은 그 옵션이 켜지면 pytest
가 문자열로 바꾸지 않아 수집이 죽으므로 언제나 `\\xff` 꼴의 문자열로 바꿔 같은 길로 보낸다. 손으로
준 id(`ids=` 의 목록과 함수, `pytest.param(id=...)`)는 이 훅을 거치지 않아 보지 않는다.
"""

import importlib.util
import io
import os
import sys
from pathlib import Path

import pytest
from tests.database import (
    database_address_fixture,
    database_fixture,
    database_template_fixture,
    empty_database_fixture,
)

from tools import llm_tokens, run_hooks

CHECKOUT = Path(run_hooks.__file__).resolve().parents[1]

# agent_os 의 데이터베이스 시험이 쓰는 이름의 접두. 위젯 관리 서버는 자기 폴더의 conftest 에서 다른
# 접두로 같은 픽스처 함수를 부른다(`tests/database.py`).
DATABASE_PREFIX = "agent_os"

# 실제 모델을 부르는 시험의 마커. `llm` 은 원칙 I 의 판정이고 `llm_widget` 과 `llm_portal` 은 위젯
# e2e 와 위젯 미리보기 페이지 e2e 를 감싸며, `llm_local` 은 빌린 모델 서버(로컬 모델)에 붙는 calc
# 시험이다.
_LLM_MARKERS = ("llm", "llm_widget", "llm_portal", "llm_local")

# 네 마커의 테스트가 하나라도 돌았을 때만 값이 있다. 둘째 값은 트레이스를 남기지 않은 그 테스트의
# 수다.
_LLM_TOKENS = pytest.StashKey[tuple[llm_tokens.Tokens, int]]()


def _ignore_notice(message: str) -> None:
    """템플릿을 만들 때는 닿을 때까지 기다린다는 알림을 찍지 않는다."""


async def _migrate_product(url_text: str) -> None:
    """제품의 마이그레이션 폴더를 템플릿 데이터베이스에 올린다. 멈추면 그 글로 예외를 던진다.

    `agent_os` 는 여기서 불러온다. 맨 위에서 부르면 다른 체크아웃의 `agent_os` 를 잡은 세션이
    `pytest_configure` 의 안내 대신 가져오기 오류로 먼저 죽는다(`tests/test_conftest.py`).
    """
    from agent_os.adapters.postgres.database import PostgresDatabase, parse_database_url

    url = parse_database_url(url_text)
    if url is None:
        raise RuntimeError("테스트 데이터베이스의 주소를 어댑터가 읽지 못했다")
    database = PostgresDatabase(url, notice=_ignore_notice)
    try:
        result = await database.migrate()
    finally:
        await database.close()
    if not result.ok:
        raise RuntimeError(result.message)


database_address = database_address_fixture()
database_template = database_template_fixture(DATABASE_PREFIX, _migrate_product)
database = database_fixture(DATABASE_PREFIX)
empty_database = empty_database_fixture(DATABASE_PREFIX)

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


def pytest_make_parametrize_id(config: pytest.Config, val: object, argname: str) -> str | None:
    if isinstance(val, bytes):
        text = val.decode("ascii", "backslashreplace")
    elif isinstance(val, str) and not val.isprintable():
        text = val
    else:
        return None
    return "".join(
        ch if ch.isprintable() else ch.encode("unicode_escape").decode("ascii") for ch in text
    )


# tryfirst 라 픽스처를 정리하기 전이고, teardown 이라 테스트 본문은 끝났다. funcargs 에는 테스트가
# 거쳐 받은 픽스처까지 든다.
@pytest.hookimpl(tryfirst=True)
def pytest_runtest_teardown(item: pytest.Item) -> None:
    if all(item.get_closest_marker(marker) is None for marker in _LLM_MARKERS):
        return
    root = item.funcargs.get("tmp_path") if isinstance(item, pytest.Function) else None
    found = llm_tokens.count(root) if isinstance(root, Path) else llm_tokens.Tokens()
    tokens, untraced = item.config.stash.get(_LLM_TOKENS, (llm_tokens.Tokens(), 0))
    untraced += 1 if found.traces == 0 else 0
    item.config.stash[_LLM_TOKENS] = (tokens + found, untraced)


def pytest_terminal_summary(
    terminalreporter: pytest.TerminalReporter, config: pytest.Config
) -> None:
    counted = config.stash.get(_LLM_TOKENS, None)
    if counted is not None:
        terminalreporter.write_line(llm_tokens.summary(*counted))


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
