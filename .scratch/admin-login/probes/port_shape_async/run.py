"""계정 포트의 비동기 모양이 실제 `agent_os` 패키지 자리에서 pyright strict, import-linter, 실제
PostgreSQL 실행을 지나는지 잰다.

왜. ADR 0062 결정 "경로와 층"은 계정 포트를 `agent_os.http` 가 선언하고 PostgreSQL 구현을
`agent_os.adapters` 가 들되, 어댑터는 `agent_os.http` 를 가져오지 않고 시그니처로 만족한다고 정한다.
앞선 프로브(`../port_shape/`)는 작은 모듈 둘의 동기 메서드로만 쟀고, 비동기 메서드, 실제 패키지,
import-linter, 드라이버 타입을 재지 못했다. 이 프로브는 그 넷을 저장소 사본에서 잰다.

어떻게. 저장소의 `src/agent_os`, `pyproject.toml`, `tools/database_for_tests.py` 를 임시 폴더에
복사하고, `tree/` 의 모듈을 같은 자리에 얹고, `patches/` 의 조각을 `adapters/postgres/database.py`
와 `main.py` 에 붙인다. 나무는 셋이다.

  clean      포트(`http/accounts.py`), core 의 예외(`core/conflicts.py`), 어댑터
             (`adapters/postgres/accounts.py`), (가)의 메서드와 (나)의 속성·만드는 메서드
             (`database.py` 끝), 조립(`main.py` 끝), 포트 타입을 적은 픽스처
             (`tests/adapters/test_accounts_probe.py`), strict 대조(`http/_probe_control.py`).
             트랜잭션 갈래로 트랜잭션 포트와 작업 객체(`http/account_work.py`), 그 어댑터 두
             모양과 잠그지 않는 대조군(`adapters/postgres/account_work.py`), 조립
             (`main_work_tail.txt`), 픽스처(`tests/adapters/test_account_work_probe.py`)를 더한다.
  drift      clean 에 어긋난 어댑터와 그것을 포트 자리에 넘기는 조립·픽스처, 칸의 차례를 틀린
             읽기 둘(`Table`, `text()`)을 더한다. 트랜잭션 갈래로 어긋난 작업 객체와 문맥 관리자
             (`adapters/postgres/account_work_drift.py`), 문맥 관리자의 둘째 타입 인자를 바꾼
             포트(`http/account_work_exit.py`), 그 조립(`main_work_drift_tail.txt`)과 픽스처
             (`tests/adapters/test_account_work_drift_probe.py`)를 더한다.
  violation  clean 에 계약을 깨는 가져오기 둘을 더한다(어댑터가 `agent_os.http` 를, `http` 가
             SQLAlchemy 를).

보는 것(회차의 셈은 `tools/probe_kit.py` 의 `Rounds`).
  tree      나무를 지었는가. 표지는 붙인 조각이 AST 에 든 것이다(`PostgresDatabase` 의 메서드
            넷과 속성, `main` 의 조립 함수).
  range     pyright 가 그 나무를 strict 로, 임시 사본의 `agent_os` 로 분석했는가. 표지는 셋이다.
            `filesAnalyzed` 가 `[tool.pyright].include` 아래 파일 수와 같다, 대조 파일에서
            strict 에서만 나는 `reportMissingParameterType` 이 난다, 대조 파일의 `reveal_type` 이
            임시 사본에만 있는 포트를 푼다(가져오기가 풀리지 않으면 그 줄 대신
            `reportMissingImports` 다). 표지가 없으면 그 나무의 pyright 회차는 모두 측정이 아니다.
  subject   clean 나무의 파일마다 오류 수. 대조 파일 밖의 오류 합도 본다.
  drift     어긋남 하나마다 기대한 규칙이 그 함수(또는 클래스)의 줄 범위에서 나고, 그 글에
            어긋난 자리의 낱말이 드는가. 대조 함수(같은 어댑터를 `Sequence` 포트에 넘김 등,
            `rule` 이 `None`)는 그 범위의 오류 수를 적는다.
  order     칸의 차례를 틀린 읽기에서 `Table` 판은 `reportArgumentType`, `text()` 판은 오류 0 이고
            `reveal_type` 이 `Any` 행을 드러내는가. NULL 을 받는 칸을 타입 인자 없이 적은 판
            (`accounts_nullable.py`)의 `reveal_type` 이 `None` 을 품는가.
  escapes   더하거나 고친 파일에 타입 우회가 없는가. 검사가 듣는다는 표지는 `escape_control.py`
            에서 셋이 잡히는 것이다.
  graph     import-linter 가 쓰는 import 그래프(grimp)가 임시 사본을 보는가. 표지는 임시 사본에만
            있는 모듈과 가져오기가 그래프에 있는 것이다.
  contracts 저장소 계약 그대로 import-linter 를 돌린 결과. clean 은 모두 KEPT, violation 은 깨질
            계약 둘이 BROKEN 이고 그 글이 임시 사본에만 있는 가져오기를 든다.
  runtime   테스트 컨테이너에 빈 데이터베이스를 만들고(`tools/database_for_tests.py`), `drive.py`
            가 clean 나무의 `agent_os.main` 에 붙인 조립 함수로 사례를 돌린다. 사례마다 표지가
            다르다(`measure_runtime`, `measure_work`). 끝나면 그 데이터베이스를 지우고 없어졌는지
            본다.
  work      트랜잭션 포트의 런타임(`drive.py` 의 `WORK` 줄). 줄을 잠그는 겹침은 셋째 연결이
            `FOR UPDATE` 로 기다리는 잠금을 봤고 둘째의 읽기가 `PAUSE` 의 절반 넘게 기다렸을
            때만, 잠그지 않는 대조군은 두 시도가 모두 1을 적어 끝 횟수가 1이고 둘째가 첫째가
            끝나기 전에 읽었을 때만 측정이다. 되돌림은 같은 트랜잭션에서 다시 읽은 값이 적은
            값이고 그 예외가 블록 밖으로 나왔을 때만, 대조(`commit`)는 적은 값을 돌려받았을 때만
            측정이다.
  cleanup   임시 폴더를 지웠는가.

돌리기(저장소 루트에서). 테스트 컨테이너가 떠 있어야 한다(`docker compose -f compose.test.yaml up
-d --wait`). 네트워크로 내려받는 것은 없다. 2026-11-24 이 PC 에서 트랜잭션 갈래 전의 판이 35초와
1분 36초, 그 갈래를 더한 판이 54초~1분 59초였다.
  uv run python .scratch/admin-login/probes/port_shape_async/run.py
  [--work <절대 경로>]  임시 폴더를 만들 부모. 없으면 시스템 임시 폴더다.
  [--keep]              임시 폴더를 지우지 않고 경로를 찍는다.
  [--dump <절대 경로>]  pyright·import-linter·`drive.py` 의 원본 출력을 그 폴더에 쓴다.

지우는 것. `--work` 는 절대 경로만 받는다. 지우는 것은 이 프로브가 그 아래에 `mkdtemp` 로 새로
만들고 바로 표지 파일(`MARKER_FILE`)을 심은 폴더 하나뿐이고, 지우기 전에 표지를 다시 본다.
지우다 실패하면 그 자리에서 멈춘다.

못 보는 것.
- `create_app` 과 라우터·미들웨어가 포트를 받는 자리. 조립은 `main.py` 끝에 붙인 함수로만 본다.
- pytest 로 픽스처를 실제로 돌리는 것. 픽스처의 자리는 타입 검사만 본다.
- 리눅스, pyright 와 import-linter 의 다른 판, 다른 타입 검사기.
- 트랜잭션 갈래 밖의 동시성(같은 이름을 동시에 넣기), 둘보다 많은 시도의 겹침, 다른 격리 수준,
  잠금을 기다리다 끝나는 제한 시간(`lock_timeout`), 교착.
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.check_type_escapes import escapes_in  # noqa: E402
from tools.database_for_tests import (  # noqa: E402
    DatabaseAddress,
    create_database,
    drop_database,
    make_name,
    resolve_address,
    server_problem,
)
from tools.probe_kit import Rounds  # noqa: E402

MARKER_FILE = ".port_shape_async_probe"
DB_PREFIX = "port_shape_async"
URL_ENV = "PORT_SHAPE_ASYNC_URL"
INCLUDE = ("src", "tests", "tools")
CONTROL = "src/agent_os/http/_probe_control.py"
STRICT_RULE = "reportMissingParameterType"
CONTROL_REVEAL = "AccountRow | None"
DATABASE = "src/agent_os/adapters/postgres/database.py"
MAIN = "src/agent_os/main.py"
DATABASE_ANCHOR = "from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine\n"
GA_METHODS = ("find", "list_all", "record_failure", "add", "engine", "accounts")

WORK_FUNCTIONS = ("probe_transactions", "probe_attempt", "probe_write_then", "probe_read_failures")
WORK_REVEAL = 'Type of "AccountTransactions.transaction"'

CLEAN_SUBJECTS = (
    "src/agent_os/http/accounts.py",
    "src/agent_os/core/conflicts.py",
    "src/agent_os/adapters/postgres/accounts.py",
    DATABASE,
    MAIN,
    "src/agent_os/server.py",
    "tests/adapters/test_accounts_probe.py",
    "src/agent_os/http/account_work.py",
    "src/agent_os/adapters/postgres/account_work.py",
    "tests/adapters/test_account_work_probe.py",
)


@dataclass(frozen=True)
class Drift:
    """어긋남 하나. `rule` 이 `None` 이면 오류 0 을 기대하는 대조다. `silent` 는 그 글에 드는지를
    결과에 적는 낱말(어긋난 메서드를 이르는 글)이다."""

    label: str
    file: str
    function: str
    rule: str | None
    words: tuple[str, ...]
    silent: tuple[str, ...] = ()


ASSEMBLY = MAIN
FIXTURE = "tests/adapters/test_accounts_drift_probe.py"
# 어긋남마다의 낱말은 첫 실행(--dump)의 원본 출력을 본 뒤 골랐다. 그 어긋남이 아니면 글에 나오지
# 않는 조각이다(비동기가 아닌 반환, 칸이 없는 줄의 클래스, 인자의 타입, 값의 낱말, 원소 타입).
SYNC_WORDS = ('"find" is an incompatible type', "-> (Row | None)")
SHORT_WORDS = ('"find" is an incompatible type', "ShortRow | None")
BYTES_WORDS = ('Parameter 1: type "str" is incompatible with type "bytes"',)
DRIFTS = (
    Drift(
        "조립 find 가 비동기가 아님", ASSEMBLY, "drift_sync_find", "reportArgumentType", SYNC_WORDS
    ),
    Drift("조립 줄에 칸 없음", ASSEMBLY, "drift_short_row", "reportArgumentType", SHORT_WORDS),
    Drift("조립 인자 타입 다름", ASSEMBLY, "drift_bytes_name", "reportArgumentType", BYTES_WORDS),
    Drift(
        "조립 값 갈래의 낱말 다름",
        ASSEMBLY,
        "drift_result_word",
        "reportArgumentType",
        ("Literal['exists']", "Literal['taken']"),
    ),
    Drift(
        "조립 포트가 list 로 적음",
        ASSEMBLY,
        "drift_list_port",
        "reportArgumentType",
        ('"list_all" is an incompatible type', "list[Row]", "list[AccountRow]"),
    ),
    Drift(
        "조립 같은 어댑터를 Sequence 포트에(대조)",
        ASSEMBLY,
        "control_list_rows_on_sequence_port",
        None,
        (),
    ),
    Drift(
        "조립 비공개 엔진을 꺼냄",
        ASSEMBLY,
        "drift_private_engine",
        "reportPrivateUsage",
        ('"_engine" is protected',),
    ),
    Drift(
        "픽스처 find 가 비동기가 아님",
        FIXTURE,
        "sync_find_store",
        "reportAssignmentType",
        SYNC_WORDS,
    ),
    Drift("픽스처 줄에 칸 없음", FIXTURE, "short_row_store", "reportAssignmentType", SHORT_WORDS),
    Drift(
        "픽스처 인자 타입 다름", FIXTURE, "bytes_name_store", "reportAssignmentType", BYTES_WORDS
    ),
)
WORK_ADAPTER = "src/agent_os/adapters/postgres/account_work_drift.py"
WORK_EXIT = "src/agent_os/http/account_work_exit.py"
WORK_FIXTURE = "tests/adapters/test_account_work_drift_probe.py"
# 트랜잭션 갈래의 낱말도 첫 실행(--dump)의 원본 출력을 본 뒤 골랐다. 작업 객체가 어긋난 셋은 글이
# 문맥 관리자의 자리에서 멈춰 어느 메서드인지 말하지 않아, 그 작업 객체의 클래스 이름을 고른다.
# 첫 실행에서 기대 없이 규칙만 적던 여섯(AsyncIterator 둘, 둘째 인자 넷)은 그 출력을 본 뒤 기대를
# 적었다.
WORK_PROTOCOL = '"transaction" is an incompatible type'


def work_cm(work: str) -> tuple[str, str]:
    return (WORK_PROTOCOL, f"_AsyncGeneratorContextManager[{work}, None]")


NO_DECORATOR_WORDS = (WORK_PROTOCOL, '"AsyncGenerator[PgWork, None]" is incompatible with protocol')
SELF_ENTER_WORDS = (WORK_PROTOCOL, '"SelfEnterTransaction" is incompatible with protocol')
# 작업 객체를 `AccountWork` 에 바로 적은 자리의 글(둘째 실행에서 봤다). 트랜잭션 포트 자리의 글에
# 이것이 드는지를 `silent` 로 적는다.
SYNC_LOCK_METHOD = ('"lock" is an incompatible type', "-> (Row | None)")
LOCK_ONLY_METHOD = ('"write_failures" is not present',)
TEXT_FAILURES_METHOD = (
    '"write_failures" is an incompatible type',
    'Keyword parameter "failures" of type "int" is incompatible with type "str"',
)
METHOD_WORDS = (SYNC_LOCK_METHOD[0], LOCK_ONLY_METHOD[0], TEXT_FAILURES_METHOD[0])
WORK_DRIFTS = (
    Drift(
        "조립 작업 asynccontextmanager 빠짐",
        ASSEMBLY,
        "drift_work_no_decorator",
        "reportArgumentType",
        NO_DECORATOR_WORDS,
    ),
    Drift(
        "조립 작업 lock 이 비동기가 아님",
        ASSEMBLY,
        "drift_work_sync_lock",
        "reportArgumentType",
        work_cm("SyncLockWork"),
        METHOD_WORDS,
    ),
    Drift(
        "조립 작업 write_failures 없음",
        ASSEMBLY,
        "drift_work_lock_only",
        "reportArgumentType",
        work_cm("LockOnlyWork"),
        METHOD_WORDS,
    ),
    Drift(
        "조립 작업 횟수를 str 로 받음",
        ASSEMBLY,
        "drift_work_text_failures",
        "reportArgumentType",
        work_cm("TextFailuresWork"),
        METHOD_WORDS,
    ),
    Drift(
        "조립 작업 __aenter__ 가 자기를 돌려줌",
        ASSEMBLY,
        "drift_work_self_enter",
        "reportArgumentType",
        SELF_ENTER_WORDS,
    ),
    Drift(
        "픽스처 작업 asynccontextmanager 빠짐",
        WORK_FIXTURE,
        "no_decorator_store",
        "reportAssignmentType",
        NO_DECORATOR_WORDS,
    ),
    Drift(
        "픽스처 작업 write_failures 없음",
        WORK_FIXTURE,
        "lock_only_store",
        "reportAssignmentType",
        work_cm("LockOnlyWork"),
        METHOD_WORDS,
    ),
    Drift(
        "픽스처 작업 __aenter__ 가 자기를 돌려줌",
        WORK_FIXTURE,
        "self_enter_store",
        "reportAssignmentType",
        SELF_ENTER_WORDS,
    ),
    Drift(
        "작업 객체 자리 lock 이 비동기가 아님",
        WORK_FIXTURE,
        "sync_lock_work",
        "reportAssignmentType",
        SYNC_LOCK_METHOD,
    ),
    Drift(
        "작업 객체 자리 write_failures 없음",
        WORK_FIXTURE,
        "lock_only_work",
        "reportAssignmentType",
        LOCK_ONLY_METHOD,
    ),
    Drift(
        "작업 객체 자리 횟수를 str 로 받음",
        WORK_FIXTURE,
        "text_failures_work",
        "reportAssignmentType",
        TEXT_FAILURES_METHOD,
    ),
    Drift(
        "AsyncIterator 로 적은 asynccontextmanager(어댑터)",
        WORK_ADAPTER,
        "IteratorAnnotatedTransactions",
        "reportDeprecated",
        ("Annotating the return type as `-> AsyncIterator[Foo]`",),
    ),
    Drift(
        "AsyncIterator 로 적은 asynccontextmanager(조립, 대조)",
        ASSEMBLY,
        "observe_work_iterator_annotated",
        None,
        (),
    ),
    Drift(
        "둘째 인자 None 포트에 asynccontextmanager 어댑터",
        ASSEMBLY,
        "observe_none_exit_context",
        "reportArgumentType",
        (
            WORK_PROTOCOL,
            '"_AsyncGeneratorContextManager[PgWork, None]" is not assignable to '
            '"AbstractAsyncContextManager[AccountWork, None]"',
        ),
    ),
    Drift(
        "둘째 인자 None 포트에 클래스 어댑터(대조)",
        ASSEMBLY,
        "observe_none_exit_class",
        None,
        (),
    ),
    Drift(
        "둘째 인자 기본 포트의 블록 뒤(대조)",
        WORK_EXIT,
        "after_block_default",
        None,
        (),
    ),
    Drift(
        "둘째 인자 bool 포트의 블록 뒤",
        WORK_EXIT,
        "after_block_swallowing",
        "reportPossiblyUnboundVariable",
        ('"failures" is possibly unbound',),
    ),
)
ORDER_TABLE = "src/agent_os/adapters/postgres/accounts_order_table.py"
ORDER_TEXT = "src/agent_os/adapters/postgres/accounts_order_text.py"
ORDER_WORDS = ('parameter "name" of type "str"', 'parameter "failures" of type "int"')
TEXT_REVEAL = "*tuple[Any, ...]"
NULLABLE = "src/agent_os/adapters/postgres/accounts_nullable.py"
NULLABLE_REVEAL = 'Type of "select(LOOSE_HASH)"'

GRAPH_CLEAN = (
    ("agent_os.main", "agent_os.adapters.postgres.accounts", True),
    ("agent_os.main", "agent_os.http.accounts", True),
    ("agent_os.adapters.postgres.database", "agent_os.adapters.postgres.accounts", True),
    ("agent_os.adapters.postgres.accounts", "agent_os.core.conflicts", True),
    ("agent_os.http.accounts", "agent_os.core.conflicts", True),
    ("agent_os.adapters.postgres.accounts", "sqlalchemy", True),
    ("agent_os.adapters.postgres.accounts", "agent_os.http.accounts", False),
    ("agent_os.main", "agent_os.adapters.postgres.account_work", True),
    ("agent_os.main", "agent_os.http.account_work", True),
    ("agent_os.http.account_work", "agent_os.http.accounts", True),
    ("agent_os.adapters.postgres.account_work", "sqlalchemy", True),
    ("agent_os.adapters.postgres.account_work", "agent_os.http.account_work", False),
    ("agent_os.adapters.postgres.account_work", "agent_os.http.accounts", False),
)
GRAPH_VIOLATION = (
    ("agent_os.adapters.postgres.accounts_violation", "agent_os.http.accounts", True),
    ("agent_os.http.accounts_violation", "sqlalchemy", True),
)
BROKEN_EXPECTED = {
    "adapters are not an HTTP surface (principle IV, ADR 0016)": (
        "agent_os.adapters.postgres.accounts_violation -> agent_os.http.accounts"
    ),
    "only the adapters import DB libraries (principle IV, ADR 0066)": (
        "agent_os.http.accounts_violation -> sqlalchemy"
    ),
}

GRAPH_CODE = """
import importlib.util, json, sys
import grimp
spec = importlib.util.find_spec("agent_os")
graph = grimp.build_graph("agent_os", include_external_packages=True, cache_dir=None)
pairs = json.loads(sys.argv[1])
print(json.dumps({
    "origin": spec.origin if spec else None,
    "modules": [name for name in json.loads(sys.argv[2]) if name in graph.modules],
    "edges": [graph.direct_import_exists(importer=a, imported=b) for a, b in pairs],
}))
"""

PROBE_AT = "2026-11-24T09:00:00+00:00"
WALKS = ("ga_walk", "na_property_walk", "na_factory_walk")
TAKEN = ("taken_core", "taken_injected", "taken_recognized", "taken_result")
UNTRANSLATED = ("untranslated_core", "untranslated_injected", "untranslated_recognized")
UNIQUE_VIOLATION = "23505"
WORK_PAUSE = 0.5  # drive.py 의 PAUSE 와 같다
WORK_LINES = 3 * 3 + 2 * 2 + 1  # 겹침 세 모양 세 번, 되돌림과 대조 두 모양, 연결 반납
ABORTED = "agent_os.http.account_work.AbortedAfterWrite"

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


def parse(text: str) -> Json:
    try:
        parsed: Json = json.loads(text)
    except ValueError:
        return None
    return parsed


def dig(value: Json, *keys: str) -> Json:
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else None
    return value


# ---- 나무 짓기 ----


def overlay(layer: Path, dest: Path) -> None:
    for source in sorted(layer.rglob("*.py")):
        target = dest / source.relative_to(layer)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)


def insert_after(path: Path, anchor: str, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(anchor) != 1:
        raise RuntimeError(f"{path.name} 에 붙일 자리가 하나가 아니다")
    path.write_text(text.replace(anchor, anchor + addition), encoding="utf-8", newline="\n")


def append(path: Path, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    if not text.endswith("\n"):
        raise RuntimeError(f"{path.name} 가 줄바꿈으로 끝나지 않는다")
    path.write_text(text + addition, encoding="utf-8", newline="\n")


def patch(name: str) -> str:
    return (HERE / "patches" / name).read_text(encoding="utf-8")


def last_class_is(path: Path, name: str) -> bool:
    body = ast.parse(path.read_text(encoding="utf-8")).body
    return bool(body) and isinstance(body[-1], ast.ClassDef) and body[-1].name == name


def class_members(path: Path, name: str) -> set[str]:
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return {
                item.name
                for item in node.body
                if isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef)
            }
    return set()


def module_functions(path: Path) -> dict[str, tuple[int, int]]:
    """모듈 수준 함수의 이름과 줄 범위(1부터)."""
    found: dict[str, tuple[int, int]] = {}
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            found[node.name] = (node.lineno, node.end_lineno or node.lineno)
    return found


def module_spans(path: Path) -> dict[str, tuple[int, int]]:
    """모듈 수준 함수와 클래스의 이름과 줄 범위(1부터). 데코레이터의 줄도 든다."""
    found: dict[str, tuple[int, int]] = {}
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            first = min([node.lineno, *(item.lineno for item in node.decorator_list)])
            found[node.name] = (first, node.end_lineno or node.lineno)
    return found


def build_tree(dest: Path, layers: tuple[str, ...], main_tails: tuple[str, ...]) -> list[str]:
    """나무 하나를 짓고 표지가 빠진 자리를 돌려준다. 빈 목록이면 표지를 모두 봤다."""
    shutil.copytree(
        ROOT / "src" / "agent_os",
        dest / "src" / "agent_os",
        ignore=shutil.ignore_patterns("__pycache__"),
    )
    shutil.copy2(ROOT / "pyproject.toml", dest / "pyproject.toml")
    (dest / "tools").mkdir()
    shutil.copy2(ROOT / "tools" / "database_for_tests.py", dest / "tools" / "database_for_tests.py")
    for layer in layers:
        overlay(HERE / "tree" / layer, dest)
    missing: list[str] = []
    database = dest / DATABASE
    if not last_class_is(database, "PostgresDatabase"):
        missing.append("database.py 의 마지막이 PostgresDatabase 가 아니다")
    insert_after(database, DATABASE_ANCHOR, patch("database_imports.txt"))
    append(database, patch("database_tail.txt"))
    members = class_members(database, "PostgresDatabase")
    missing.extend(f"PostgresDatabase.{name} 없음" for name in GA_METHODS if name not in members)
    main = dest / MAIN
    for tail in main_tails:
        append(main, patch(tail))
    functions = module_functions(main)
    missing.extend(
        f"main.py 에 {name} 없음"
        for name in ("probe_scenario", *WORK_FUNCTIONS)
        if name not in functions
    )
    return missing


# ---- pyright ----


def pyright(tree: Path) -> Json:
    done = subprocess.run(
        [
            sys.executable,
            "-m",
            "pyright",
            "--outputjson",
            "-p",
            str(tree),
            "--venvpath",
            str(ROOT),
        ],
        cwd=tree,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=900,
        check=False,
    )
    return parse(done.stdout)


@dataclass(frozen=True)
class Diagnostic:
    file: str
    line: int
    severity: str
    rule: str
    message: str


def diagnostics(report: Json, tree: Path) -> list[Diagnostic]:
    found: list[Diagnostic] = []
    items = dig(report, "generalDiagnostics")
    for item in items if isinstance(items, list) else []:
        file, line = dig(item, "file"), dig(item, "range", "start", "line")
        severity, rule, message = dig(item, "severity"), dig(item, "rule"), dig(item, "message")
        try:
            relative = Path(str(file)).resolve().relative_to(tree.resolve()).as_posix()
        except ValueError:
            relative = str(file)
        found.append(
            Diagnostic(
                file=relative,
                line=(line + 1) if isinstance(line, int) else 0,
                severity=str(severity),
                rule=rule if isinstance(rule, str) else "",
                message=str(message),
            )
        )
    return found


def included_files(tree: Path) -> int:
    paths = {
        path
        for name in INCLUDE
        for path in (tree / name).rglob("*.py")
        if "__pycache__" not in path.parts
    }
    return len(paths)


def range_seen(report: Json, found: list[Diagnostic], tree: Path) -> tuple[bool, str]:
    analyzed = dig(report, "summary", "filesAnalyzed")
    expected = included_files(tree)
    control = [item for item in found if item.file == CONTROL]
    strict = any(item.rule == STRICT_RULE for item in control)
    revealed = any(
        item.severity == "information" and CONTROL_REVEAL in item.message for item in control
    )
    missing_imports = [item for item in found if item.rule == "reportMissingImports"]
    seen = analyzed == expected and strict and revealed and not missing_imports
    detail = (
        f"filesAnalyzed {analyzed}/{expected}, strict 표지 {strict}, 임시 사본의 포트를 풂 "
        f"{revealed}, reportMissingImports {len(missing_imports)}"
    )
    return seen, detail


def errors(found: list[Diagnostic]) -> list[Diagnostic]:
    return [item for item in found if item.severity == "error"]


# ---- import-linter ----


def lint_env(tree: Path) -> dict[str, str]:
    return {**os.environ, "PYTHONPATH": str(tree / "src")}


def lint_imports(tree: Path) -> tuple[int, str]:
    exe = shutil.which("lint-imports", path=str(Path(sys.executable).parent))
    if exe is None:
        raise RuntimeError("lint-imports 를 찾지 못했다")
    done = subprocess.run(
        [exe, "--config", str(tree / "pyproject.toml"), "--no-cache", "--no-logo"],
        cwd=tree,
        env=lint_env(tree),
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        check=False,
    )
    return done.returncode, done.stdout + done.stderr


def graph(tree: Path, pairs: tuple[tuple[str, str, bool], ...]) -> Json:
    modules = sorted({name for a, b, _ in pairs for name in (a, b)})
    done = subprocess.run(
        [
            sys.executable,
            "-c",
            GRAPH_CODE,
            json.dumps([[a, b] for a, b, _ in pairs]),
            json.dumps(modules),
        ],
        cwd=tree,
        env=lint_env(tree),
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
    )
    lines = done.stdout.strip().splitlines()
    return parse(lines[-1]) if lines else None


def graph_seen(
    found: Json, tree: Path, pairs: tuple[tuple[str, str, bool], ...]
) -> tuple[bool, str]:
    origin = dig(found, "origin")
    edges = dig(found, "edges")
    inside = isinstance(origin, str) and Path(origin).resolve().is_relative_to(tree.resolve())
    expected = [want for _, _, want in pairs]
    matches = isinstance(edges, list) and edges == expected
    detail = f"agent_os 의 자리가 임시 사본 {inside}, 가져오기 {edges} (기대 {expected})"
    return inside and matches, detail


def contract_names() -> list[str]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    contracts = data["tool"]["importlinter"]["contracts"]
    return [str(item["name"]) for item in contracts]


def contract_states(output: str) -> dict[str, str | None]:
    flat = " ".join(output.split())
    states: dict[str, str | None] = {}
    for name in contract_names():
        if f"{name} KEPT" in flat:
            states[name] = "KEPT"
        elif f"{name} BROKEN" in flat:
            states[name] = "BROKEN"
        else:
            states[name] = None
    return states


# ---- 런타임 ----


async def create_probe_database() -> tuple[DatabaseAddress, str]:
    address = resolve_address(os.environ)
    problem = await server_problem(address)
    if problem is not None:
        raise RuntimeError(problem)
    name = make_name(DB_PREFIX, "test")
    await create_database(address, name)
    return address, name


async def database_exists(address: DatabaseAddress, name: str) -> bool:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(
        address.with_database(address.url.database or ""), poolclass=NullPool
    )
    try:
        async with engine.connect() as connection:
            result = await connection.execute(
                text("SELECT count(*) FROM pg_database WHERE datname = :name"), {"name": name}
            )
            return int(result.scalar_one()) > 0
    finally:
        await engine.dispose()


def drive(tree: Path, url_text: str) -> tuple[int, str, str]:
    env = {**lint_env(tree), URL_ENV: url_text}
    done = subprocess.run(
        [sys.executable, str(HERE / "drive.py")],
        cwd=tree,
        env=env,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
    )
    return done.returncode, done.stdout, done.stderr


def drive_lines(stdout: str) -> dict[str, list[Json]]:
    found: dict[str, list[Json]] = {}
    for line in stdout.splitlines():
        kind, _, rest = line.partition(" ")
        if kind in ("ORIGIN", "VERSION", "RESULT", "DETAIL", "WORK"):
            found.setdefault(kind, []).append(parse(rest))
    return found


def results_by_scenario(lines: dict[str, list[Json]]) -> dict[str, Json]:
    found: dict[str, Json] = {}
    for item in lines.get("RESULT", []):
        name = dig(item, "scenario")
        if isinstance(name, str):
            found[name] = item
    return found


def walk_check(name: str, value: Json) -> list[str]:
    """한 바퀴의 값이 기대와 다른 자리. 빈 목록이면 기대대로다."""
    wrong: list[str] = []
    listed = dig(value, "listed")
    expected: dict[str, Json] = {
        "added": name,
        "found_tier": "admin",
        "failures_after": 2,
        "locked_until": PROBE_AT,
        "missing_is_none": True,
    }
    if name == "ga_walk":
        expected["same_object"] = True
    for key, want in expected.items():
        got = dig(value, key)
        if got != want:
            wrong.append(f"{key}={got!r}(기대 {want!r})")
    if not isinstance(listed, list) or name not in listed:
        wrong.append(f"listed 에 {name} 없음")
    return wrong


# ---- 정리 ----


def make_work(parent: Path) -> Path:
    work = Path(tempfile.mkdtemp(prefix="port_shape_async_", dir=parent))
    (work / MARKER_FILE).touch()
    return work


def remove_work(work: Path) -> bool:
    if not (work / MARKER_FILE).is_file():
        raise RuntimeError(f"표지 파일이 없어 지우지 않는다: {work}")
    shutil.rmtree(work)
    return not work.exists()


def versions() -> str:
    names = ("pyright", "import-linter", "grimp", "sqlalchemy", "asyncpg")
    parts = [f"{name} {importlib.metadata.version(name)}" for name in names]
    parts.append(f"python {sys.version.split()[0]}")
    return ", ".join(parts)


def git_state() -> str:
    head = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    ).stdout.strip()
    dirty = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "status",
            "--porcelain",
            "--",
            "src",
            "pyproject.toml",
            "tools/database_for_tests.py",
        ],
        capture_output=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    ).stdout.strip()
    return f"저장소 HEAD {head}, 복사한 자리의 커밋하지 않은 변경 {'있음' if dirty else '없음'}"


# ---- 회차 ----


def measure_pyright_clean(rounds: Rounds, tree: Path, dump: Path | None) -> None:
    report = pyright(tree)
    if dump is not None:
        (dump / "pyright_clean.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    found = diagnostics(report, tree)
    seen, detail = range_seen(report, found, tree)
    print(f"pyright clean: {dig(report, 'version')}, {detail}")
    with rounds.round("range clean") as current:
        current.mark(measured=seen, result="분석했다" if seen else f"표지 없음: {detail}")
    work_reveal = [
        item.message
        for item in found
        if item.file == CONTROL and item.message.startswith(WORK_REVEAL)
    ]
    print(f"  트랜잭션 포트의 reveal_type: {work_reveal}")
    failing = errors(found)
    for name in CLEAN_SUBJECTS:
        rules = sorted({item.rule for item in failing if item.file == name})
        count = sum(1 for item in failing if item.file == name)
        print(f"  {name}: 오류 {count} {rules}")
        with rounds.round(f"subject {name}") as current:
            current.mark(measured=seen, result=f"오류 {count}")
    others = [item for item in failing if item.file != CONTROL]
    print(f"  대조 파일 밖의 오류 합 {len(others)}")
    for item in others:
        print(f"    {item.file}:{item.line} {item.rule} {item.message.splitlines()[0]}")
    with rounds.round("subject 대조 밖 전체") as current:
        current.mark(measured=seen, result=f"오류 {len(others)}")


def measure_pyright_drift(rounds: Rounds, tree: Path, dump: Path | None) -> None:
    report = pyright(tree)
    if dump is not None:
        (dump / "pyright_drift.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    found = diagnostics(report, tree)
    seen, detail = range_seen(report, found, tree)
    print(f"pyright drift: {detail}")
    with rounds.round("range drift") as current:
        current.mark(measured=seen, result="분석했다" if seen else f"표지 없음: {detail}")
    failing = errors(found)
    every = (*DRIFTS, *WORK_DRIFTS)
    spans = {name: module_spans(tree / name) for name in {drift.file for drift in every}}
    for drift in every:
        start, end = spans[drift.file].get(drift.function, (0, -1))
        inside = [item for item in failing if item.file == drift.file and start <= item.line <= end]
        rules = sorted({item.rule for item in inside})
        print(f"  {drift.label} ({drift.function}): {rules}")
        for item in inside:
            print(f"    {item.line} {item.rule}: {' / '.join(item.message.splitlines()[:12])}")
        with rounds.round(f"drift {drift.label}") as current:
            located = end >= start > 0
            if drift.rule is None:
                current.mark(measured=seen and located, result=f"오류 {len(inside)}")
                continue
            messages = " ".join(item.message for item in inside if item.rule == drift.rule)
            caught = (
                seen
                and located
                and drift.rule in rules
                and all(word in messages for word in drift.words)
            )
            result = "잡혔다" if caught else ""
            if caught and drift.silent:
                named = any(word in messages for word in drift.silent)
                result = f"잡혔다, 어긋난 메서드의 글 {'있음' if named else '없음'}"
            current.mark(measured=caught, result=result)
    table = [item for item in failing if item.file == ORDER_TABLE]
    table_info = [item.message for item in found if item.file == ORDER_TABLE]
    print(f"  {ORDER_TABLE}: {[(item.line, item.rule) for item in table]}")
    print(f"    정보: {[m for m in table_info if m.startswith('Type of')]}")
    with rounds.round("order Table 판") as current:
        argument = " ".join(item.message for item in table if item.rule == "reportArgumentType")
        caught = seen and all(word in argument for word in ORDER_WORDS)
        current.mark(measured=caught, result=f"reportArgumentType {len(table)}" if caught else "")
    text_errors = [item for item in failing if item.file == ORDER_TEXT]
    text_reveal = [
        item.message for item in found if item.file == ORDER_TEXT and item.severity == "information"
    ]
    print(f"  {ORDER_TEXT}: 오류 {len(text_errors)}, 정보 {text_reveal}")
    with rounds.round("order text() 판") as current:
        revealed = any(TEXT_REVEAL in message for message in text_reveal)
        current.mark(measured=seen and revealed, result=f"오류 {len(text_errors)}")
    loose = [
        item.message
        for item in found
        if item.file == NULLABLE and item.message.startswith(NULLABLE_REVEAL)
    ]
    loose_errors = [item for item in failing if item.file == NULLABLE]
    print(f"  {NULLABLE}: 오류 {len(loose_errors)}, 정보 {loose}")
    with rounds.round("타입 인자 없는 NULL 칸") as current:
        current.mark(
            measured=seen and len(loose) == 1,
            result=f"None 을 품음 {'None' in loose[0]}" if len(loose) == 1 else "",
        )


def measure_escapes(rounds: Rounds, trees: tuple[Path, ...]) -> None:
    control = escapes_in((HERE / "escape_control.py").read_text(encoding="utf-8"))
    listening = all(any(word in line for line in control) for word in ("`Any`", "`cast`", "억제"))
    names = sorted(
        {
            tree / name
            for tree in trees
            for name in (
                *(
                    path.relative_to(HERE / "tree" / layer).as_posix()
                    for layer in ("clean", "drift")
                    for path in (HERE / "tree" / layer).rglob("*.py")
                ),
                DATABASE,
                MAIN,
            )
            if (tree / name).is_file()
        }
    )
    total = 0
    for path in names:
        found = escapes_in(path.read_text(encoding="utf-8"))
        total += len(found)
        if found:
            print(f"  타입 우회 {path}: {found}")
    print(f"타입 우회: 파일 {len(names)}개에서 {total}건, 대조가 듣는다 {listening}")
    with rounds.round("escapes 더하거나 고친 파일") as current:
        current.mark(measured=listening and bool(names), result=f"우회 {total}")


def measure_contracts(rounds: Rounds, clean: Path, violation: Path, dump: Path | None) -> None:
    for label, tree, pairs in (
        ("clean", clean, GRAPH_CLEAN),
        ("violation", violation, GRAPH_CLEAN + GRAPH_VIOLATION),
    ):
        found = graph(tree, pairs)
        seen, detail = graph_seen(found, tree, pairs)
        print(f"graph {label}: {detail}")
        with rounds.round(f"graph {label}") as current:
            current.mark(
                measured=seen, result="임시 사본을 본다" if seen else f"표지 없음: {detail}"
            )
        code, output = lint_imports(tree)
        if dump is not None:
            (dump / f"lint_{label}.txt").write_text(output, encoding="utf-8")
        states = contract_states(output)
        flat = " ".join(output.split())
        print(f"lint-imports {label}: 종료 {code}")
        for name, state in states.items():
            print(f"  {state} {name}")
        summary = re.search(r"Contracts: (\d+) kept, (\d+) broken\.", flat)
        print(f"  요약 {summary.group(0) if summary else '(없음)'}")
        with rounds.round(f"contracts {label}") as current:
            all_named = all(state is not None for state in states.values())
            if label == "clean":
                kept = all(state == "KEPT" for state in states.values())
                current.mark(
                    measured=seen and all_named and summary is not None,
                    result="모두 KEPT" if kept and code == 0 else f"KEPT 아님 {states}",
                )
                continue
            broken = {name for name, state in states.items() if state == "BROKEN"}
            named = all(edge in flat for edge in BROKEN_EXPECTED.values())
            current.mark(
                measured=seen and all_named and named,
                result=f"BROKEN {sorted(broken)}, 종료 {code}",
            )


def measure_runtime(rounds: Rounds, clean: Path, dump: Path | None) -> None:
    address, name = asyncio.run(create_probe_database())
    try:
        code, stdout, stderr = drive(clean, address.text_for(name))
    finally:
        asyncio.run(drop_database(address, name))
        gone = not asyncio.run(database_exists(address, name))
    if dump is not None:
        (dump / "drive_stdout.txt").write_text(stdout, encoding="utf-8")
        (dump / "drive_stderr.txt").write_text(stderr, encoding="utf-8")
    lines = drive_lines(stdout)
    origin = dig((lines.get("ORIGIN") or [None])[0], "agent_os")
    inside = isinstance(origin, str) and Path(origin).resolve().is_relative_to(clean.resolve())
    version = dig((lines.get("VERSION") or [None])[0], "server_version")
    print(f"drive.py: 종료 {code}, agent_os 가 임시 사본 {inside}, PostgreSQL {version}")
    if code != 0:
        print(f"  stderr 끝: {stderr.strip().splitlines()[-5:]}")
    by_name = results_by_scenario(lines)
    for scenario in WALKS:
        item = by_name.get(scenario)
        value = dig(item, "value")
        print(f"  {scenario}: {item}")
        with rounds.round(f"runtime {scenario}") as current:
            if not inside or not isinstance(value, dict):
                current.mark(measured=False, result=f"값이 없다: {item}")
                continue
            wrong = walk_check(scenario, value)
            current.mark(measured=True, result="끝까지 돌았다" if not wrong else f"다름 {wrong}")
    for scenario in TAKEN + UNTRANSLATED:
        item = by_name.get(scenario)
        outcome, state = dig(item, "value", "outcome"), dig(item, "sqlstate")
        print(f"  {scenario}: {item}")
        with rounds.round(f"runtime {scenario}") as current:
            if inside and outcome == "taken":
                current.mark(measured=True, result="포트가 약속한 신호로 알아봤다")
            elif inside and state == UNIQUE_VIOLATION:
                error = dig(item, "error")
                current.mark(measured=True, result=f"알아보지 못하고 {error} 가 올라왔다")
            else:
                current.mark(measured=False, result=f"유일 제약 위반의 표지가 없다: {item}")
    found = (lines.get("DETAIL") or [None])[0]
    print(f"  detail: {json.dumps(found, ensure_ascii=False, indent=1)}")
    with rounds.round("runtime DETAIL") as current:
        seen = (
            inside
            and dig(found, "raw_sqlstate") == UNIQUE_VIOLATION
            and dig(found, "chained_traceback_has_marker") is True
            and dig(found, "port_error_seen") is True
        )
        result = (
            f"원래 예외의 글에 값 {dig(found, 'raw_has_marker')}, "
            f"DETAIL 속성에 값 {dig(found, 'detail_attr_has_marker')}, "
            f"사슬마다 글에 값 {dig(found, 'chain_str_has_marker')}, "
            f"포트 예외의 역추적에 값 {dig(found, 'port_traceback_has_marker')}"
        )
        current.mark(measured=seen, result=result if seen else "")
    measure_work(rounds, lines.get("WORK", []), inside=inside)
    with rounds.round("runtime 데이터베이스 지움") as current:
        current.mark(measured=True, result="지웠다" if gone else "남았다")


def overlap_marked(item: Json) -> tuple[bool, str]:
    """겹침 한 회차의 표지와 결과. 잠그는 모양은 기다린 잠금, 잠그지 않는 대조군은 잃은 적기다."""
    final, first, second = dig(item, "final"), dig(item, "first"), dig(item, "second")
    wait = dig(item, "second_wait")
    waits = dig(item, "waits")
    waited_for_update = isinstance(waits, list) and any(
        dig(sample, "for_update") is True for sample in waits
    )
    if dig(item, "style") == "unlocked":
        before_done = dig(item, "second_read_before_first_done") is True
        lost = final == 1 and first == 1 and second == 1
        if before_done and lost:
            return True, "횟수 1(한 번을 잃었다)"
        return False, f"겹침의 표지 없음: final {final}, first {first}, second {second}"
    long_wait = isinstance(wait, float | int) and wait >= 0.5 * WORK_PAUSE
    if waited_for_update and long_wait:
        return True, f"횟수 {final}"
    return False, f"겹침의 표지 없음: FOR UPDATE 기다림 {waited_for_update}, 둘째 기다림 {wait}"


def measure_work(rounds: Rounds, items: list[Json], *, inside: bool) -> None:
    """트랜잭션 포트의 런타임 회차. `drive.py` 의 `WORK` 줄마다 하나다."""
    print(f"  WORK 줄 {len(items)}개 (기대 {WORK_LINES})")
    with rounds.round("runtime WORK 줄 수") as current:
        complete = inside and len(items) == WORK_LINES
        current.mark(measured=complete, result=f"{len(items)}줄" if complete else "")
    for item in items:
        case, style = dig(item, "case"), dig(item, "style")
        print(f"  work {json.dumps(item, ensure_ascii=False)}")
        label = f"runtime work {case} {style}"
        if case == "overlap":
            label = f"{label} {dig(item, 'repeat')}"
        with rounds.round(label) as current:
            if not inside:
                current.mark(measured=False, result="agent_os 가 임시 사본이 아니다")
            elif case == "overlap":
                measured, result = overlap_marked(item)
                current.mark(measured=measured, result=result)
            elif case in ("rollback", "commit"):
                before, after = dig(item, "before"), dig(item, "after")
                written = before + 5 if isinstance(before, int) else None
                if case == "rollback":
                    marked = dig(item, "raised") == ABORTED and dig(item, "seen_inside") == written
                    kept = "되돌려졌다" if after == before else f"남았다 {after}"
                else:
                    marked = dig(item, "returned") == written and dig(item, "raised") is None
                    kept = "남았다" if after == written else f"없어졌다 {after}"
                current.mark(measured=marked, result=kept if marked else f"표지 없음 {item}")
            elif case == "pool":
                checked = dig(item, "checked_out")
                current.mark(measured=isinstance(checked, int), result=f"빌려 간 연결 {checked}")
            else:
                current.mark(measured=False, result=f"사례가 실패했다 {item}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, default=Path(tempfile.gettempdir()))
    parser.add_argument("--keep", action="store_true")
    parser.add_argument("--dump", type=Path, default=None)
    args = parser.parse_args()
    parent: Path = args.work
    dump: Path | None = args.dump
    if not parent.is_absolute() or (dump is not None and not dump.is_absolute()):
        print("--work 와 --dump 는 절대 경로만 받는다. 아무것도 하지 않는다.")
        return 2
    if dump is not None:
        dump.mkdir(parents=True, exist_ok=True)
    print(versions())
    print(git_state())
    rounds = Rounds()
    work = make_work(parent)
    print(f"임시 폴더 {work}")
    try:
        clean, drift, violation = work / "clean", work / "drift", work / "violation"
        work_tail = "main_work_tail.txt"
        plans = (
            (clean, ("clean",), ("main_tail.txt", work_tail)),
            (
                drift,
                ("clean", "drift"),
                ("main_tail.txt", "main_drift_tail.txt", work_tail, "main_work_drift_tail.txt"),
            ),
            (violation, ("clean", "violation"), ("main_tail.txt", work_tail)),
        )
        for tree, layers, tails in plans:
            with rounds.round(f"tree {tree.name}") as current:
                missing = build_tree(tree, layers, tails)
                current.mark(measured=not missing, result="지었다" if not missing else "")
                if missing:
                    print(f"  {tree.name} 표지 없음: {missing}")
        with rounds.round("pyright clean 단계") as current:
            measure_pyright_clean(rounds, clean, dump)
            current.mark(measured=True, result="돌았다")
        with rounds.round("pyright drift 단계") as current:
            measure_pyright_drift(rounds, drift, dump)
            current.mark(measured=True, result="돌았다")
        measure_escapes(rounds, (clean, drift))
        with rounds.round("import-linter 단계") as current:
            measure_contracts(rounds, clean, violation, dump)
            current.mark(measured=True, result="돌았다")
        with rounds.round("runtime 단계") as current:
            measure_runtime(rounds, clean, dump)
            current.mark(measured=True, result="돌았다")
    finally:
        if args.keep:
            print(f"임시 폴더를 남겼다: {work}")
        else:
            removed = remove_work(work)
            with rounds.round("cleanup 임시 폴더") as current:
                current.mark(measured=True, result="지웠다" if removed else "남았다")
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
