"""`widget-admin serve` 와 `widget-admin migrate`(`widget_admin.main.main`)를 본다.

운영자가 보는 것을 본다. 종료 코드, 표준 출력과 표준 오류의 글, 판 기록 표의 줄, uvicorn 에 넘기는
인자다. 글은 글자까지 단언한다(명세 widget-admin-server "멈출 때의 글"). `migrate` 의 갈래는
데이터베이스 객체 시험과 같은 시험용 마이그레이션 폴더(9001, 9002, 실패하는 9003)를 객체에 대서
만든다. 제품 폴더 (`0001_sites`)는 조립을 거치는 사례 하나만 쓴다.

비동기 시험에서는 `main` 을 스레드로 부른다(`main` 이 스스로 이벤트 루프를 연다). `serve` 는 uvicorn
을 바꿔 끼워 서버를 띄우지 않고, 실제 프로세스로 `serve` 를 띄우는 사례는 종료 코드 3 하나만 둔다.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys
import tomllib
import uuid
from pathlib import Path

import pytest
from fastapi import FastAPI
from tests.postgres_support import (
    FIRST,
    SECOND,
    broken_versions,
    closed_port,
    copy_versions,
    revisions,
    tables,
)
from tests.widget_admin.support import SECRET
from tools.database_for_tests import ScopedDatabase

from widget_admin import main as main_module
from widget_admin.database import DatabaseUrl, MigrateResult, WidgetAdminDatabase
from widget_admin.main import DATABASE_URL_ENV, main

REPO_ROOT = Path(__file__).resolve().parents[2]

NO_URL = (
    "WIDGET_ADMIN_DATABASE_URL 이 비어 있습니다. widget-admin 의 serve 와 migrate 는 PostgreSQL"
    " 데이터베이스가 있어야 돕니다.\n"
    "  단독 배포에서는 compose 가 .env 의 WIDGET_ADMIN_DATABASE_PASSWORD 로 이 값을 짓습니다."
    " 개발 PC 의 값은 README 에 있습니다.\n"
)
UNREADABLE_URL = (
    "WIDGET_ADMIN_DATABASE_URL 을 읽지 못했습니다."
    " postgresql://계정:비밀번호@호스트:포트/데이터베이스 꼴이어야 합니다.\n"
    "  값에는 비밀번호가 들어 있어 여기 찍지 않습니다. 비밀번호에 @ 가 들면 주소를 읽지 못하므로,"
    " 비밀번호는 영문자와 숫자만 씁니다.\n"
)
UNREACHABLE_PLACEHOLDER = f"postgresql://widget_admin:{SECRET}@127.0.0.1:1/probe"


def _stderr_notice(message: str) -> None:
    sys.stderr.write(f"{message}\n")


@pytest.fixture
def uvicorn_calls(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    """uvicorn 을 바꿔 끼워 서버를 띄우지 않고 받은 인자만 모은다."""
    calls: list[dict[str, object]] = []

    def run(app: object, **kwargs: object) -> None:
        calls.append({"app": app, **kwargs})

    monkeypatch.setattr(main_module.uvicorn, "run", run)
    return calls


def _environment(monkeypatch: pytest.MonkeyPatch, address: str | None) -> None:
    if address is None:
        monkeypatch.delenv(DATABASE_URL_ENV, raising=False)
    else:
        monkeypatch.setenv(DATABASE_URL_ENV, address)


def _use_database(
    monkeypatch: pytest.MonkeyPatch, versions: Path, *, give_up_quickly: bool = False
) -> None:
    """`migrate` 가 시험용 폴더로 객체를 짓게 한다.

    닿는 서버를 상대로 하는 시험은 부하가 큰 실행에서도 시간 때문에 빨개지지 않게 넉넉한 시간을
    준다. 닿지 못하는 갈래를 보는 시험만 `give_up_quickly` 로 짧은 시간을 준다.
    """
    retry_seconds, attempt_seconds = (0.6, 0.4) if give_up_quickly else (8.0, 8.0)

    def build(url: DatabaseUrl) -> WidgetAdminDatabase:
        return WidgetAdminDatabase(
            url,
            notice=_stderr_notice,
            versions=versions,
            retry_seconds=retry_seconds,
            retry_interval=0.1,
            attempt_seconds=attempt_seconds,
        )

    monkeypatch.setattr(main_module, "_build_database", build)


async def _migrate() -> int:
    return await asyncio.to_thread(main, ["migrate"])


# --- 명령의 자리 --------------------------------------------------------------------------------


def test_명령_widget_admin이_패키지의_main을_부른다() -> None:
    pyproject = tomllib.loads((REPO_ROOT / "widget-admin" / "pyproject.toml").read_text("utf-8"))
    assert pyproject["project"]["scripts"] == {"widget-admin": "widget_admin.main:main"}


def test_python_m으로도_돈다_변수가_없으면_이유를_알리고_1로_끝난다() -> None:
    env = {key: value for key, value in _base_environment().items() if key != DATABASE_URL_ENV}
    done = subprocess.run(
        [sys.executable, "-m", "widget_admin.main", "migrate"],
        capture_output=True,
        env=env,
        timeout=60,
        check=False,
    )
    assert done.returncode == 1
    assert (done.stdout, _text(done.stderr)) == (b"", NO_URL)


def _text(stream: bytes) -> str:
    """자식 프로세스가 쓴 글. 윈도의 줄바꿈 변환(`\\r\\n`)을 `\\n` 으로 되돌린다."""
    return stream.decode("utf-8").replace("\r\n", "\n")


def _base_environment() -> dict[str, str]:
    return {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}


# --- 주소를 못 읽을 때: 닿으려 하지도 않고 값을 싣지 않는다 -----------------------------


@pytest.mark.parametrize("command", ["serve", "migrate"])
@pytest.mark.parametrize("value", [None, "", "   "])
def test_주소가_비어_있으면_이유를_알리고_1로_끝난다(
    command: str,
    value: str | None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    uvicorn_calls: list[dict[str, object]],
) -> None:
    _environment(monkeypatch, value)

    assert main([command]) == 1

    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", NO_URL)
    assert uvicorn_calls == []


@pytest.mark.parametrize("command", ["serve", "migrate"])
@pytest.mark.parametrize(
    "value",
    [
        f"mysql://widget_admin:{SECRET}@127.0.0.1:5432/widget_admin",
        f"postgresql://widget_admin:{SECRET}@x@127.0.0.1:5432/widget_admin",
        f"postgresql://widget_admin:{SECRET}@127.0.0.1:5432/widget_admin?sslmode=require",
        f"postgresql://widget_admin:{SECRET}@127.0.0.1:5432/widget_admin@x",
    ],
    ids=["다른_드라이버", "골뱅이가_둘", "질의_문자열", "둘째_골뱅이_앞에_슬래시"],
)
def test_주소를_읽지_못하면_값을_싣지_않고_1로_끝난다(
    command: str,
    value: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    uvicorn_calls: list[dict[str, object]],
) -> None:
    _environment(monkeypatch, value)

    assert main([command]) == 1

    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", UNREADABLE_URL)
    assert SECRET not in captured.out + captured.err
    assert uvicorn_calls == []


# --- serve: uvicorn 에 넘기는 인자 --------------------------------------------------------------


def test_serve는_기본으로_루프백_8100에_서고_수명을_켜고_멈출_때_5초를_기다린다(
    monkeypatch: pytest.MonkeyPatch, uvicorn_calls: list[dict[str, object]]
) -> None:
    _environment(monkeypatch, UNREACHABLE_PLACEHOLDER)

    assert main(["serve"]) == 0

    assert len(uvicorn_calls) == 1
    call = uvicorn_calls[0]
    assert isinstance(call.pop("app"), FastAPI)
    assert call == {
        "host": "127.0.0.1",
        "port": 8100,
        "timeout_graceful_shutdown": 5,
        "lifespan": "on",
    }


def test_serve는_주소와_포트를_인자로_받는다(
    monkeypatch: pytest.MonkeyPatch, uvicorn_calls: list[dict[str, object]]
) -> None:
    _environment(monkeypatch, UNREACHABLE_PLACEHOLDER)

    assert main(["serve", "--host", "::1", "--port", "9100"]) == 0

    assert [(call["host"], call["port"]) for call in uvicorn_calls] == [("::1", 9100)]


def test_serve는_연결_문자열_말고_다른_환경_변수와_파일을_읽지_않는다(
    monkeypatch: pytest.MonkeyPatch, uvicorn_calls: list[dict[str, object]], tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".env").write_text(f"{DATABASE_URL_ENV}={UNREACHABLE_PLACEHOLDER}\n", "utf-8")
    monkeypatch.setenv("AGENT_OS_DATABASE_URL", UNREACHABLE_PLACEHOLDER)
    _environment(monkeypatch, None)

    assert main(["serve"]) == 1
    assert uvicorn_calls == []


# --- 실제 프로세스: 표가 뒤처졌으면 이유를 찍고 3으로 끝난다 ---------------------------


async def test_표가_뒤처진_데이터베이스에서_serve는_이유를_찍고_3으로_끝난다(
    empty_database: ScopedDatabase,
) -> None:
    env = {**_base_environment(), DATABASE_URL_ENV: empty_database.text()}
    port = closed_port()

    done = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-m", "widget_admin.main", "serve", "--port", str(port)],
        capture_output=True,
        env=env,
        timeout=120,
        check=False,
    )

    error = _text(done.stderr)
    assert done.returncode == 3
    assert (
        "데이터베이스의 표가 이 판보다 뒤처져 있습니다. widget-admin migrate 를 먼저 돌리십시오.\n"
        "  표의 판은 없음이고 이 판의 마지막 판은 0001입니다.\n"
    ) in error
    assert f"{empty_database.address.url.username}:{empty_database.address.url.password}@" not in (
        error
    )


# --- migrate: 실제 데이터베이스 -------------------------------------------------------------------


async def test_빈_데이터베이스는_올리고_다시_부르면_이미_마지막_판이다(
    empty_database: ScopedDatabase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _use_database(monkeypatch, copy_versions(tmp_path / "versions", FIRST, SECOND))
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
    _use_database(monkeypatch, copy_versions(tmp_path / "versions", FIRST))
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
    _use_database(monkeypatch, copy_versions(tmp_path / "newer", FIRST, SECOND))
    assert await _migrate() == 0
    capsys.readouterr()
    _use_database(monkeypatch, copy_versions(tmp_path / "older", FIRST))

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
    _use_database(monkeypatch, copy_versions(tmp_path / "versions", FIRST), give_up_quickly=True)
    _environment(monkeypatch, address.render_as_string(hide_password=False))

    assert await _migrate() == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    lines = captured.err.splitlines()
    assert lines[0] == f"데이터베이스({place})에 아직 닿지 못해 최대 0.6초 동안 다시 시도합니다."
    assert lines[1].startswith(
        f"데이터베이스({place})에 닿지 못했습니다. 0.6초 동안 다시 시도했습니다("
    )
    assert len(lines) == 2


async def test_올리다_실패하면_표는_그대로이고_값은_글에_실리지_않는다(
    empty_database: ScopedDatabase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    marker = f"marker_{uuid.uuid4().hex}"
    _use_database(monkeypatch, broken_versions(tmp_path / "versions", marker))
    _environment(monkeypatch, empty_database.text())

    assert await _migrate() == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith(
        "표를 올리다 실패했습니다(오류 번호 22012). 표의 판은 올리기 전 그대로 없음입니다.\n"
    )
    assert "[SQL parameters hidden due to hide_parameters=True]" in captured.err
    assert marker not in captured.err
    assert "계정:비밀번호@" not in captured.err
    assert f"{empty_database.address.url.username}:{empty_database.address.url.password}@" not in (
        captured.err
    )
    assert await revisions(empty_database) == []
    assert not {"probe_one", "probe_two", "probe_three"} & await tables(empty_database)


async def test_제품_폴더로_부르면_성공으로_끝나고_글은_표준_출력으로_간다(
    empty_database: ScopedDatabase,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """조립을 거치는 길(`build_database`)을 바꾸지 않고 부른다. 제품 폴더의 마이그레이션을 빈
    데이터베이스에 올렸다는 글이 나오고 성공으로 끝난다."""
    _environment(monkeypatch, empty_database.text())

    assert await _migrate() == 0

    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("표를 없음에서 0001으로 올렸습니다.\n", "")
    assert await revisions(empty_database) == ["0001"]
    assert "sites" in await tables(empty_database)


def test_객체가_예외를_던지면_예외의_글_대신_까닭만_싣고_1로_끝난다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    async def fail(self: WidgetAdminDatabase) -> object:
        raise RuntimeError(f"비밀번호 {SECRET} 가 섞인 글")

    monkeypatch.setattr(WidgetAdminDatabase, "migrate", fail)
    _environment(monkeypatch, f"postgresql://widget_admin:{SECRET}@127.0.0.1:1/probe")

    assert main(["migrate"]) == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith(
        "데이터베이스(127.0.0.1:1/probe)를 확인하다 뜻밖의 오류로 멈췄습니다(RuntimeError).\n"
    )
    assert "이 판의 결함일 수 있습니다." in captured.err
    assert SECRET not in captured.err


def test_닫기가_예외를_던지면_예외의_글_대신_까닭만_싣고_1로_끝난다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """올리기는 성공했어도 닫다 실패하면 역추적이 새지 않고 닫다 실패했다는 글과 1로 끝난다."""

    async def migrated(self: WidgetAdminDatabase) -> MigrateResult:
        return MigrateResult(ok=True, message="표를 없음에서 0001으로 올렸습니다.")

    async def fail(self: WidgetAdminDatabase) -> None:
        raise RuntimeError(f"비밀번호 {SECRET} 가 섞인 글")

    monkeypatch.setattr(WidgetAdminDatabase, "migrate", migrated)
    monkeypatch.setattr(WidgetAdminDatabase, "close", fail)
    _environment(monkeypatch, f"postgresql://widget_admin:{SECRET}@127.0.0.1:1/probe")

    assert main(["migrate"]) == 1

    captured = capsys.readouterr()
    assert captured.out == "표를 없음에서 0001으로 올렸습니다.\n"
    assert captured.err.startswith(
        "데이터베이스(127.0.0.1:1/probe)의 연결을 닫다 오류가 났습니다(RuntimeError)."
    )
    assert SECRET not in captured.err
    assert "Traceback" not in captured.err
