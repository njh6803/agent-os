"""`agent-os migrate` 명령(`agent_os.main.main(["migrate"])`)을 실제 테스트 데이터베이스에 붙여
본다.

운영자가 보는 것을 본다. 종료 코드, 표준 출력과 표준 오류의 글, 판 기록 표의 줄이다. 글은 글자까지
단언한다(명세 postgres-foundation "멈출 때의 글"). 판의 갈래는 어댑터 시험과 같은 시험용
마이그레이션 폴더(9001, 9002, 실패하는 9003)를 어댑터에 대서 만든다. 제품 폴더(`0001` 부터)는 조립을
거치는 사례 하나만 쓴다.

비동기 시험에서는 `main` 을 스레드로 부른다(`main` 이 스스로 이벤트 루프를 연다). 스레드에서는
SIGINT 처리기를 걸 수 없어, 처리기를 거는 `run_interruptibly` 만 `asyncio.run` 으로 바꾼다. 처리기는
`tests/channel/cli/` 쪽 시험이 본다.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from collections.abc import Callable, Coroutine
from pathlib import Path

import pytest
from tests.postgres_support import (
    FIRST,
    NO_URL,
    SECOND,
    UNREADABLE_URL,
    broken_versions,
    closed_port,
    copy_versions,
    revisions,
    tables,
)
from tools.database_for_tests import ScopedDatabase

from agent_os import main as main_module
from agent_os.adapters.models import MODEL_ENV
from agent_os.adapters.postgres.database import DatabaseUrl, PostgresDatabase
from agent_os.main import DATABASE_URL_ENV, main

SECRET = "leak_probe_pw"


def _stderr_notice(message: str) -> None:
    sys.stderr.write(f"{message}\n")


def _run_plainly[T](work: Callable[[], Coroutine[object, object, T]]) -> T:
    return asyncio.run(work())


def _run_without_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    """스레드에서는 SIGINT 처리기를 걸 수 없으므로 처리기를 거는 함수를 바꾼다."""
    monkeypatch.setattr(main_module, "run_interruptibly", _run_plainly)


def _use_adapter(
    monkeypatch: pytest.MonkeyPatch, versions: Path, *, give_up_quickly: bool = False
) -> None:
    """`migrate` 가 시험용 폴더로 어댑터를 짓게 한다.

    닿는 서버를 상대로 하는 시험은 부하가 큰 실행에서도 시간 때문에 빨개지지 않게 넉넉한 시간을
    준다. 닿지 못하는 갈래를 보는 시험만 `give_up_quickly` 로 짧은 시간을 준다.
    """
    retry_seconds, attempt_seconds = (0.6, 0.4) if give_up_quickly else (8.0, 8.0)

    def build(url: DatabaseUrl) -> PostgresDatabase:
        return PostgresDatabase(
            url,
            notice=_stderr_notice,
            versions=versions,
            retry_seconds=retry_seconds,
            retry_interval=0.1,
            attempt_seconds=attempt_seconds,
        )

    monkeypatch.setattr(main_module, "_build_database", build)
    _run_without_handler(monkeypatch)


def _environment(monkeypatch: pytest.MonkeyPatch, address: str | None) -> None:
    """주소만 주고 모델 환경 변수는 비운다. `migrate` 는 모델을 읽지 않는다."""
    monkeypatch.delenv(MODEL_ENV, raising=False)
    if address is None:
        monkeypatch.delenv(DATABASE_URL_ENV, raising=False)
    else:
        monkeypatch.setenv(DATABASE_URL_ENV, address)


async def _migrate() -> int:
    return await asyncio.to_thread(main, ["migrate"])


# --- 주소를 못 읽을 때: 닿으려 하지도 않고 값을 싣지 않는다
# ------------------------------------------


@pytest.mark.parametrize("value", [None, "", "   "])
def test_주소가_비어_있으면_이유를_알리고_1로_끝난다(
    value: str | None, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _environment(monkeypatch, value)
    assert main(["migrate"]) == 1
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", NO_URL)


@pytest.mark.parametrize(
    "value",
    [
        f"postgresql://agent:{SECRET}@x@127.0.0.1:5432/agent_os",
        f"postgresql://agent:{SECRET}@127.0.0.1:5432/agent_os?sslmode=disable",
    ],
    ids=["골뱅이가_둘", "질의_문자열"],
)
def test_주소를_읽지_못하면_값을_싣지_않고_1로_끝난다(
    value: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _environment(monkeypatch, value)
    assert main(["migrate"]) == 1
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", UNREADABLE_URL)
    assert SECRET not in captured.out + captured.err


# --- 실제 데이터베이스 ---------------------------------------------------------------------------


async def test_빈_데이터베이스는_올리고_다시_부르면_이미_마지막_판이다(
    empty_database: ScopedDatabase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _use_adapter(monkeypatch, copy_versions(tmp_path / "versions", FIRST, SECOND))
    _environment(monkeypatch, empty_database.text())
    assert await _migrate() == 0
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("표를 없음에서 9002으로 올렸습니다.\n", "")
    assert await revisions(empty_database) == ["9002"]
    assert {"probe_one", "probe_two"} <= await tables(empty_database)
    assert await _migrate() == 0
    again = capsys.readouterr()
    assert (again.out, again.err) == ("표가 이미 마지막 판(9002)입니다.\n", "")
    assert await revisions(empty_database) == ["9002"]


async def test_주소_앞뒤의_공백과_개행은_걷고_읽는다(
    empty_database: ScopedDatabase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _use_adapter(monkeypatch, copy_versions(tmp_path / "versions", FIRST))
    _environment(monkeypatch, f"  {empty_database.text()}\n")
    assert await _migrate() == 0
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("표를 없음에서 9001으로 올렸습니다.\n", "")
    assert await revisions(empty_database) == ["9001"]


async def test_이_판이_모르는_번호의_데이터베이스는_건드리지_않고_1로_끝난다(
    empty_database: ScopedDatabase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _environment(monkeypatch, empty_database.text())
    _use_adapter(monkeypatch, copy_versions(tmp_path / "newer", FIRST, SECOND))
    assert await _migrate() == 0
    capsys.readouterr()
    _use_adapter(monkeypatch, copy_versions(tmp_path / "older", FIRST))
    assert await _migrate() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "데이터베이스가 이 판보다 새롭습니다. 되돌리려면 올리기 전의 백업을 복원하십시오.\n"
        "  표의 판은 9002이고 이 판이 아는 마지막 판은 9001입니다.\n"
    )
    assert await revisions(empty_database) == ["9002"]


async def test_닿지_못하면_다시_시도한다는_알림과_닿지_못했다는_글로_1로_끝난다(
    empty_database: ScopedDatabase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    port = closed_port()
    place = f"{empty_database.address.url.host}:{port}/{empty_database.name}"
    address = empty_database.address.url.set(database=empty_database.name, port=port)
    _use_adapter(monkeypatch, copy_versions(tmp_path / "versions", FIRST), give_up_quickly=True)
    _environment(monkeypatch, address.render_as_string(hide_password=False))
    assert await _migrate() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    lines = captured.err.splitlines()
    assert lines[0] == f"데이터베이스({place})에 아직 닿지 못해 최대 0.6초 동안 다시 시도합니다."
    unreached = f"데이터베이스({place})에 닿지 못했습니다. 0.6초 동안 다시 시도했습니다("
    assert lines[1].startswith(unreached)
    assert len(lines) == 2


async def test_올리다_실패하면_표는_그대로이고_값은_글에_실리지_않는다(
    empty_database: ScopedDatabase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    marker = f"marker_{uuid.uuid4().hex}"
    _use_adapter(monkeypatch, broken_versions(tmp_path / "versions", marker))
    _environment(monkeypatch, empty_database.text())
    assert await _migrate() == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith(
        "표를 올리다 실패했습니다(오류 번호 22012). 표의 판은 올리기 전 그대로 없음입니다.\n"
    )
    assert "[SQL parameters hidden due to hide_parameters=True]" in captured.err
    assert marker not in captured.err
    assert "agent_os:agent_os@" not in captured.err
    assert await revisions(empty_database) == []
    assert not {"probe_one", "probe_two", "probe_three"} & await tables(empty_database)


async def test_제품_폴더로_부르면_성공으로_끝나고_글은_표준_출력으로_간다(
    empty_database: ScopedDatabase,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """조립을 거치는 길(`_build_database`)을 바꾸지 않고 부른다. 제품 폴더의 마이그레이션을 빈
    데이터베이스에 올렸다는 글이 나오고 성공으로 끝난다."""
    _run_without_handler(monkeypatch)
    _environment(monkeypatch, empty_database.text())
    assert await _migrate() == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out.startswith("표")
    assert captured.out.endswith("올렸습니다.\n")


def test_어댑터가_예외를_던지면_예외의_글_대신_까닭만_싣고_1로_끝난다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    async def fail(self: PostgresDatabase) -> object:
        raise RuntimeError(f"비밀번호 {SECRET} 가 섞인 글")

    monkeypatch.setattr(PostgresDatabase, "migrate", fail)
    _environment(monkeypatch, f"postgresql://agent:{SECRET}@127.0.0.1:1/probe")
    assert main(["migrate"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith(
        "데이터베이스(127.0.0.1:1/probe)를 확인하다 뜻밖의 오류로 멈췄습니다(RuntimeError).\n"
    )
    assert "이 판의 결함일 수 있습니다." in captured.err
    assert SECRET not in captured.err
