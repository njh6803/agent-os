"""MCP ToolSource. 파이썬으로 쓴 진짜 stdio 서버(mcp_fixture_server.py)에 붙는다. 네트워크가 없다.

(시제품. `.scratch/mcp-shutdown/probes/full_stack.py`가 저장소 사본에 얹어 잰다.)

세션을 async 픽스처로 열지 않는다. pytest-asyncio 가 픽스처의 setup 과 teardown 을 다른 태스크에서
돌리는데 MCP 의 stdio 클라이언트는 anyio 취소 범위라 같은 태스크에서 닫혀야 한다(ADR 0007 이력).
그래서 테스트 본문에서 async with 로 열고 닫는다.

닫기 절(ADR 0034)은 `mcp_lingering.py`의 가짜 프로세스가 쓰는 하트비트가 닫은 뒤 멈췄는지 본다.
멈춰 있지만 살아 있는 프로세스는 가려내지 못한다. 남은 프로세스는 테스트가 끝날 때 멈춤 파일로
끝낸다.
"""

import subprocess
import sys
import time
from collections.abc import AsyncGenerator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path

import anyio
import pytest

from agent_os.adapters.mcp import McpTools
from agent_os.core.ports import ToolConnection, ToolSource
from agent_os.sdk import McpServer, PluginName

FIXTURE = McpServer(
    command=sys.executable, args=(str(Path(__file__).with_name("mcp_fixture_server.py")),)
)
LINGERING = Path(__file__).with_name("mcp_lingering.py")
PAGED = Path(__file__).with_name("mcp_paged_server.py")
# 쪽 나눔 사례의 기한. 고치기 전의 어댑터는 같은 쪽을 끝없이 물어 기한이 없으면 멈춘다. 끝없는
# 목록 사례(1000쪽)가 Windows 에서 홀로 2.5~2.9초, full_stack 의 두 OS 를 함께 돈 회차에 6.13초였다
# (tests.md 의 시간 단언).
PAGED_WITHIN_SECONDS = 30


@asynccontextmanager
async def _fixture_connection() -> AsyncGenerator[ToolConnection]:
    tools: ToolSource = McpTools()
    async with tools.connect({PluginName("fixture"): FIXTURE}) as connection:
        yield connection


async def test_서버의_도구_목록과_입력_스키마를_준다() -> None:
    async with _fixture_connection() as connection:
        specs = {spec.name: spec for spec in connection.tools()}

    assert set(specs) == {"add", "fail"}
    properties = specs["add"].input_schema["properties"]
    assert isinstance(properties, dict)
    assert set(properties) == {"a", "b"}


async def test_도구를_부르면_결과_텍스트가_온다() -> None:
    async with _fixture_connection() as connection:
        result = await connection.call("add", {"a": 2, "b": 3})

    assert result.ok is True
    assert result.content == "5"


async def test_도구가_에러를_내면_실패로_표시되고_에러_내용이_온다() -> None:
    async with _fixture_connection() as connection:
        result = await connection.call("fail", {"reason": "overflow"})

    assert result.ok is False
    assert "overflow" in result.content


async def test_없는_도구는_에러다() -> None:
    async with _fixture_connection() as connection:
        with pytest.raises(LookupError, match="nope"):
            await connection.call("nope", {})


async def test_서버_기동_실패는_서버_이름과_명령을_든_연결_오류다() -> None:
    tools: ToolSource = McpTools()
    broken = McpServer(command="definitely-not-a-command-agent-os")

    with pytest.raises(
        ConnectionError, match="broken.*definitely-not-a-command-agent-os"
    ) as raised:
        async with tools.connect({PluginName("broken"): broken}):
            pass
    assert isinstance(raised.value.__cause__, FileNotFoundError)


async def test_뜨자마자_끝나는_서버는_서버_이름을_든_연결_오류다() -> None:
    """세션을 연 뒤 실패하므로 그 예외가 상류의 태스크 그룹을 지나 두 겹으로 싸인다. 어댑터가
    벗겨 그 `ConnectionError` 하나로 낸다."""
    tools: ToolSource = McpTools()
    exiting = McpServer(command=sys.executable, args=("-c", "pass"))

    with pytest.raises(ConnectionError, match="exiting.*Connection closed"):
        async with tools.connect({PluginName("exiting"): exiting}):
            pass


async def test_서버를_지정하지_않으면_도구_없이_연다() -> None:
    tools: ToolSource = McpTools()

    async with tools.connect({}) as opened:
        assert list(opened.tools()) == []


def _paged(shape: str) -> dict[PluginName, McpServer]:
    server = McpServer(command=sys.executable, args=(str(PAGED), shape))
    return {PluginName("paged"): server}


async def test_빈_커서는_도구_목록의_끝이다() -> None:
    """빈 커서로 다시 물으면 같은 쪽이 끝없이 온다."""
    with anyio.fail_after(PAGED_WITHIN_SECONDS):
        async with McpTools().connect(_paged("empty")) as connection:
            names = [spec.name for spec in connection.tools()]

    assert names == ["paged"]


async def test_끝나지_않는_도구_목록은_쪽_수의_상한에서_연결_오류다() -> None:
    with (
        anyio.fail_after(PAGED_WITHIN_SECONDS),
        pytest.raises(ConnectionError, match="paged.*1000쪽"),
    ):
        async with McpTools().connect(_paged("endless")):
            pass


# --- 닫기(ADR 0034) ---


@pytest.fixture
def folder(tmp_path: Path) -> Iterator[Path]:
    yield tmp_path
    (tmp_path / "stop").touch()


def _lingering(role: str, folder: Path) -> dict[PluginName, McpServer]:
    server = McpServer(command=sys.executable, args=(str(LINGERING), role, str(folder)))
    return {PluginName("lingering"): server}


# 가짜 프로세스가 뜨고 하트비트가 생기기까지의 상한. 파이썬을 두세 번 띄운다. 다른 세션의 테스트와
# 겹친 부하(CPU 86%)에서 홀로 돈 사례 5가 12.5초 걸렸고, 20초로 두던 판은 전체 회차에서 그 기다림을
# 넘겼다(tests.md 의 시간 단언).
APPEAR_WITHIN_SECONDS = 30


async def _생길_때까지_기다린다(path: Path) -> None:
    with anyio.fail_after(APPEAR_WITHIN_SECONDS):
        while not path.exists():
            await anyio.sleep(0.05)


def _멈췄다(*paths: Path) -> None:
    """15초 안에 하트비트가 모두 1초 동안 자라지 않으면 지난다. 한 번만 견주지 않고 기한까지 거듭
    견준다(`tests/tools/test_run_checks.py` 의 `_stops_growing`). 부하에서 꺼지는 프로세스의 마지막
    쓰기나 부모 감시의 간격(0.2초)을 산 프로세스로 읽지 않는다."""
    끝 = time.monotonic() + 15
    while time.monotonic() < 끝:
        크기 = [path.stat().st_size for path in paths]
        time.sleep(1)
        if [path.stat().st_size for path in paths] == 크기:
            return
    자란 = ", ".join(path.name for path in paths)
    pytest.fail(f"닫은 뒤에도 15초 동안 {자란} 하트비트가 자란다")


class _본문의_예외(Exception):
    pass


async def test_도구_호출_도중에_기한이_오면_감싼_프로세스_아래의_서버까지_내려간다(
    folder: Path,
) -> None:
    """core 의 실행 타임아웃과 같은 범위(`move_on_after`)다. 범위가 기한의 취소를 받았는지
    (`cancelled_caught`)로 기한을 본다 — 보호된 닫기가 그 취소를 삼키지 않는다."""
    with anyio.move_on_after(60) as scope:
        async with McpTools().connect(_lingering("wrapper", folder)) as connection:
            await _생길_때까지_기다린다(folder / "stay.hb")
            scope.deadline = anyio.current_time() + 1
            await connection.call("slow", {"seconds": 30})

    assert scope.cancelled_caught
    _멈췄다(folder / "wrapper.hb", folder / "stay.hb")


async def test_스스로_끝나며_자식을_남기는_서버를_닫으면_그_자식도_내려간다(folder: Path) -> None:
    async with McpTools().connect(_lingering("leaving", folder)):
        await _생길_때까지_기다린다(folder / "child.hb")

    _멈췄다(folder / "child.hb")


async def test_연결_안에서_난_예외는_감싸이지_않고_나오며_서버가_내려간다(folder: Path) -> None:
    thrown = _본문의_예외()

    with pytest.raises(_본문의_예외) as raised:
        async with McpTools().connect(_lingering("wrapper", folder)):
            await _생길_때까지_기다린다(folder / "stay.hb")
            raise thrown

    assert raised.value is thrown
    _멈췄다(folder / "wrapper.hb", folder / "stay.hb")


async def test_연결_안에서_던진_예외_그룹은_그_그룹_그대로_나온다() -> None:
    """부르는 쪽이 스스로 낸 그룹도 겉봉(상류의 태스크 그룹 두 겹)만 벗고 그 객체로 나온다."""
    thrown = ExceptionGroup("본문", [_본문의_예외()])

    with pytest.raises(ExceptionGroup) as raised:
        async with _fixture_connection():
            raise thrown
    assert raised.value is thrown


async def test_연결_안의_yield_에_멈춘_제너레이터는_예외_없이_닫힌다() -> None:
    """core 는 연결을 연 채 이벤트를 내는 제너레이터를 그 자리에서 닫는다(트레이스 쓰기가 실패한
    실행, `core/run.py` 의 `_drive`). 닫기가 넣는 GeneratorExit 를 상류의 태스크 그룹이 감싸 그대로
    두면 `aclose` 가 `BaseExceptionGroup` 을 내고, 결말을 쓴 실행도 그것을 밖으로 올린다."""

    async def 연결_안에서_낸다() -> AsyncGenerator[str]:
        async with _fixture_connection():
            yield "연결 안"

    events = 연결_안에서_낸다()
    assert await anext(events) == "연결 안"
    await events.aclose()


async def test_도구_호출_도중에_서버가_죽으면_서버를_든_RuntimeError_다(folder: Path) -> None:
    async with McpTools().connect(_lingering("stay", folder)) as connection:
        with pytest.raises(RuntimeError, match="lingering.*crash"):
            await connection.call("crash", {})


_PARENT = """
import sys
import anyio
from pathlib import Path
from agent_os.adapters.mcp import McpTools
from agent_os.sdk import McpServer, PluginName

server = McpServer(command=sys.executable, args=(sys.argv[1], "wrapper", sys.argv[2]))


async def main() -> None:
    async with McpTools().connect({PluginName("lingering"): server}):
        await anyio.sleep(60)


anyio.run(main)
"""


def test_연결을_연_프로세스가_갑자기_죽어도_서버가_내려간다(folder: Path) -> None:
    parent = subprocess.Popen([sys.executable, "-c", _PARENT, str(LINGERING), str(folder)])
    try:
        end = time.monotonic() + APPEAR_WITHIN_SECONDS
        while not (folder / "stay.hb").exists() and time.monotonic() < end:
            time.sleep(0.05)
    finally:
        parent.kill()
        parent.wait()

    assert (folder / "stay.hb").exists(), f"{APPEAR_WITHIN_SECONDS}초 안에 서버가 뜨지 않았다"
    _멈췄다(folder / "wrapper.hb", folder / "stay.hb")
