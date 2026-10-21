"""MCP ToolSource. 파이썬으로 쓴 진짜 stdio 서버(mcp_fixture_server.py)에 붙는다. 네트워크가 없다.

세션을 async 픽스처로 열지 않는다. pytest-asyncio 가 픽스처의 setup 과 teardown 을 다른 태스크에서
돌리는데 MCP 의 stdio 클라이언트는 anyio 취소 범위라 같은 태스크에서 닫혀야 한다(ADR 0007 이력).
그래서 테스트 본문에서 async with 로 열고 닫는다.

닫기 절(ADR 0034)은 가짜 프로세스(`mcp_lingering.py`)가 살아 있는지를 하트비트로 본다. 프로세스마다
0.1초에 1바이트씩 파일에 쓰고, 닫은 뒤 그 파일이 1초 동안 자라지 않으면 멈춘 것이다. 프로세스
번호로 살아 있는지 묻지 않는다. 끝난 프로세스의 번호는 다른 프로세스가 다시 쓰고, 감싼 프로세스
아래 서버의 번호는 클라이언트가 모른다. 대가로 멈춰 있지만 살아 있는 프로세스(쓰기가 막힌 것, 일시
정지된 것)는 멈춘 것으로 보인다. 남은 것은 테스트가 끝날 때 멈춤 파일로 끝내고, 그것도 놓치면 120초
뒤 스스로 끝난다.
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
# 가짜 프로세스. 테스트는 importlib 모드라 같은 폴더의 모듈을 import 하지 못해 경로와 파일 이름으로
# 가리킨다. 하트비트는 `<역할>.hb`, 멈춤 파일은 `stop` 이다(그 모듈의 독스트링).
LINGERING = Path(__file__).with_name("mcp_lingering.py")
STOP = "stop"
PAGED = Path(__file__).with_name("mcp_paged_server.py")
# 쪽 나눔 사례의 기한. 커서를 끝까지 따르지 못하는 어댑터는 같은 쪽을 끝없이 물어 기한이 없으면
# 멈춘다. 끝없는 목록 사례(1000쪽)는 명세의 시제품이 Windows 에서 홀로 2.5~2.9초, 두 OS 를 함께 돈
# 회차에 6.13초였다(`.claude/rules/tests.md` 의 시간 단언).
PAGED_WITHIN_SECONDS = 30
# 가짜 프로세스가 뜨고 하트비트가 생기기까지의 상한. 파이썬을 두세 번 띄운다. 다른 세션의 테스트와
# 겹친 부하(CPU 86%)에서 홀로 돈 명세의 시제품 사례 하나가 12.5초 걸렸고, 20초로 두던 판은 전체
# 회차에서 그 기다림을 넘겼다(`.claude/rules/tests.md` 의 시간 단언).
APPEAR_WITHIN_SECONDS = 30
# 사례 5의 상한. 그 자식은 새 파이썬에서 어댑터와 mcp 를 불러 들인 뒤에야 연결을 연다. 이 PC 에서
# 홀로 연결 표지까지 9.8~12.3초였고(하트비트 둘은 그보다 먼저 생겼다), 30초로 두던 판은 pre-commit
# 러너의 부하에서 표지 셋이 모두 생기기 전에 그 기다림을 넘겼다(일지 2026-10-21-09, 손으로 봤다).
CONNECT_WITHIN_SECONDS = 120
# 닫은 뒤 하트비트가 멈추기를 기다리는 기한. 판정의 꼴은 `_멈췄다` 다.
STOP_WITHIN_SECONDS = 15


@asynccontextmanager
async def _fixture_connection() -> AsyncGenerator[ToolConnection]:
    tools: ToolSource = McpTools()
    async with tools.connect({PluginName("fixture"): FIXTURE}) as connection:
        yield connection


async def test_서버의_도구_목록과_입력_스키마를_준다() -> None:
    async with _fixture_connection() as connection:
        specs = {spec.name: spec for spec in connection.tools()}

    assert set(specs) == {"add", "fail", "blocks"}
    properties = specs["add"].input_schema["properties"]
    assert isinstance(properties, dict)
    assert set(properties) == {"a", "b"}


async def test_도구를_부르면_결과_텍스트가_온다() -> None:
    async with _fixture_connection() as connection:
        result = await connection.call("add", {"a": 2, "b": 3})

    assert result.ok is True
    assert result.content == "5"


async def test_결과의_글은_텍스트_블록과_텍스트_리소스를_차례로_이어_붙인_것이다() -> None:
    """이미지 블록은 글에 들지 않는다."""
    async with _fixture_connection() as connection:
        result = await connection.call("blocks", {})

    assert result.ok is True
    assert result.content == "앞리소스뒤"


async def test_도구가_에러를_내면_실패로_표시되고_에러_내용이_온다() -> None:
    async with _fixture_connection() as connection:
        result = await connection.call("fail", {"reason": "overflow"})

    assert result.ok is False
    assert "overflow" in result.content


async def test_없는_도구는_에러다() -> None:
    async with _fixture_connection() as connection:
        with pytest.raises(LookupError, match="nope"):
            await connection.call("nope", {})


async def test_서버_기동_실패는_연결_단계에서_예외다() -> None:
    tools: ToolSource = McpTools()
    broken = McpServer(command="definitely-not-a-command-agent-os")

    with pytest.raises(FileNotFoundError):
        async with tools.connect({PluginName("broken"): broken}):
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


async def test_끝나지_않는_도구_목록은_쪽_수의_상한에서_여는_단계가_실패한다() -> None:
    """실패는 서버를 여는 동안 나 상류의 태스크 그룹에 싸여 나온다. 그 꼴은 경계의 예외 티켓(02)이
    조이므로 여기서는 그룹 안의 잎에서 쪽 수를 찾는다."""
    with anyio.fail_after(PAGED_WITHIN_SECONDS), pytest.raises(ExceptionGroup) as raised:
        async with McpTools().connect(_paged("endless")):
            pass

    assert raised.group_contains(RuntimeError, match="1000쪽")


# --- 닫기(ADR 0034) ---


@pytest.fixture
def folder(tmp_path: Path) -> Iterator[Path]:
    """가짜 프로세스의 하트비트와 표지가 놓이는 폴더. 끝날 때 멈춤 파일로 남은 것을 끝낸다."""
    yield tmp_path
    (tmp_path / STOP).touch()


def _lingering(role: str, folder: Path) -> dict[PluginName, McpServer]:
    server = McpServer(command=sys.executable, args=(str(LINGERING), role, str(folder)))
    return {PluginName("lingering"): server}


async def _생길_때까지_기다린다(path: Path) -> None:
    with anyio.fail_after(APPEAR_WITHIN_SECONDS):
        while not path.exists():
            await anyio.sleep(0.05)


def _멈췄다(*paths: Path) -> None:
    """15초 안에 하트비트가 모두 1초 동안 자라지 않으면 지난다.

    한 번만 견주지 않고 기한까지 거듭 견준다(`tests/tools/test_run_checks.py` 의 `_stops_growing`).
    부하에서 꺼지는 프로세스의 마지막 쓰기를 산 프로세스로 읽지 않는다. 실패하면 마지막 견줌에서
    자란 하트비트를 든다.
    """
    끝 = time.monotonic() + STOP_WITHIN_SECONDS
    자란: list[str] = []
    while time.monotonic() < 끝:
        크기 = [path.stat().st_size for path in paths]
        time.sleep(1)
        자란 = [
            path.name for path, 앞 in zip(paths, 크기, strict=True) if path.stat().st_size != 앞
        ]
        if not 자란:
            return
    pytest.fail(f"닫은 뒤에도 {STOP_WITHIN_SECONDS}초 동안 {', '.join(자란)} 하트비트가 자란다")


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

    assert (folder / "slow").exists(), "서버가 도구 호출을 받지 않았다"
    assert scope.cancelled_caught
    _멈췄다(folder / "wrapper.hb", folder / "stay.hb")


async def test_스스로_끝나며_자식을_남기는_서버를_닫으면_그_자식도_내려간다(folder: Path) -> None:
    """상류는 유예 안에 스스로 끝난 서버의 트리를 끄지 않는다. 윈도우는 Job Object 를 닫아 남은
    자식을 거두고, POSIX 는 런처가 서버의 프로세스 그룹을 끈다."""
    async with McpTools().connect(_lingering("leaving", folder)):
        await _생길_때까지_기다린다(folder / "child.hb")

    _멈췄다(folder / "child.hb")


# 사례 5의 자식. 연결을 연 뒤 표지 파일을 남기고 기다린다. 테스트가 그 표지와 서버의 하트비트를 본
# 뒤 이 프로세스를 강제로 끈다.
_CONNECTED = "connected"
_PARENT = """
import sys
from pathlib import Path

import anyio

from agent_os.adapters.mcp import McpTools
from agent_os.sdk import McpServer, PluginName

lingering, folder, connected = sys.argv[1], Path(sys.argv[2]), sys.argv[3]
server = McpServer(command=sys.executable, args=(lingering, "wrapper", str(folder)))


async def main() -> None:
    async with McpTools().connect({PluginName("lingering"): server}):
        (folder / connected).touch()
        await anyio.sleep(120)


anyio.run(main)
"""


def test_연결을_연_프로세스가_갑자기_죽어도_서버가_내려간다(folder: Path) -> None:
    """윈도우는 그 프로세스가 끝나며 Job Object 가 닫히고, POSIX 는 런처가 부모가 바뀐 것을 보고
    서버의 프로세스 그룹을 끈다."""
    beats = (folder / "wrapper.hb", folder / "stay.hb")
    ready = (folder / _CONNECTED, *beats)
    parent = subprocess.Popen(
        [sys.executable, "-c", _PARENT, str(LINGERING), str(folder), _CONNECTED]
    )
    try:
        end = time.monotonic() + CONNECT_WITHIN_SECONDS
        while not all(path.exists() for path in ready) and time.monotonic() < end:
            time.sleep(0.05)
    finally:
        parent.kill()
        parent.wait()

    missing = [path.name for path in ready if not path.exists()]
    assert not missing, f"{CONNECT_WITHIN_SECONDS}초 안에 생기지 않았다: {missing}"
    _멈췄다(*beats)
