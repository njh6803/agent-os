"""CLI 의 Ctrl+C 처리기. 처리기가 프로세스를 끝내므로 자식 프로세스에서 잰다.

(시제품. `.scratch/mcp-shutdown/probes/full_stack.py`가 저장소 사본에 얹어 잰다.)

자식은 처리기 아래에서 진짜 MCP 어댑터로 입력이 닫혀도 끝나지 않는 서버(`mcp_lingering.py`의
`stay`)를 열고, 그 서버가 도구 `slow`를 받았다는 표지 파일이 생기면 스스로 SIGINT 를 올린다. 도구
호출이 취소되면 그 시각을 남긴다. 그 서버를 닫는 데 상류의 유예 2초가 들어, 둘째 SIGINT(첫째 0.5초
뒤)는 닫는 도중에 온다. 테스트는 그것을 취소의 시각이 둘째보다 앞선 것으로 본다. 처리기 없이
(`asyncio.run`의 처리기로) 돌면 mcp 2.3.0 에서 둘째 뒤 끝나지 않는다.

신호를 올리는 법은 OS 마다 다르다. POSIX 에서 보조 스레드가 `raise_signal` 로 올리면 그 스레드가
신호를 받아 주 스레드의 대기가 깨지지 않는다. 그래서 그 스레드는 SIGINT 를 막고 프로세스에 보낸다.
윈도우는 C 처리기가 올린 스레드에서 돌고 이벤트 루프를 깨우므로 그대로 올린다.
"""

import json
import signal
import subprocess
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

# 모듈째 가져온다. ruff 의 isort 는 모듈 경로 전체가 `src`에 있어야 1st-party 로 보는데, 시제품의
# `interrupt`는 저장소의 `src`에 없어 이름을 가져오면 이 자리와 사본의 자리가 다른 정렬을 요구했다.
from agent_os.channel.cli import interrupt

LINGERING = Path(__file__).parents[2] / "adapters" / "mcp_lingering.py"
DIED_INTERRUPTED = interrupt.STATUS_CONTROL_C_EXIT if sys.platform == "win32" else -signal.SIGINT
# 둘째가 닫기를 끊으면 자식이 둘째를 보낸 시각부터 부모가 그 끝을 본 시각까지가 홀로 돌린
# 프로브(`close_paths.py --cli-handler force`, 같은 양을 같은 방법으로 잰다)에서 0.006~0.013초라,
# 문턱은 그 70배가 넘는다(tests.md 의 시간 단언). 끊지 못하면 자식은 첫째의 닫기(상류의 유예 2초)를
# 마치고서야 끝나 둘째 뒤 약 1.5초다. 이 쪽과의 차는 1.5배뿐이지만 부하에서는 이 쪽이 더 늦어진다.
FORCED_WITHIN_SECONDS = 1.0
CANCELLED = "cancelled"

_CHILD = """
import asyncio
import json
import os
import signal
import sys
import threading
import time
from pathlib import Path

from agent_os.adapters.mcp import McpTools
from agent_os.channel.cli.interrupt import run_interruptibly
from agent_os.sdk import McpServer, PluginName

lingering, folder, presses = sys.argv[1], Path(sys.argv[2]), int(sys.argv[3])
server = McpServer(command=sys.executable, args=(lingering, "stay", str(folder)))


def press() -> None:
    if os.name == "posix":
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
    end = time.monotonic() + 30
    while not (folder / "slow").exists() and time.monotonic() < end:
        time.sleep(0.05)
    for count in range(presses):
        if count:
            time.sleep(0.5)
        print(json.dumps({"pressed": time.time()}), flush=True)
        if os.name == "posix":
            os.kill(os.getpid(), signal.SIGINT)
        else:
            signal.raise_signal(signal.SIGINT)


async def main() -> None:
    async with McpTools().connect({PluginName("lingering"): server}) as connection:
        threading.Thread(target=press, daemon=True).start()
        try:
            await connection.call("slow", {"seconds": 30})
        except asyncio.CancelledError:
            (folder / "cancelled").write_text(str(time.time()), encoding="utf-8")
            raise


run_interruptibly(main)
"""


@pytest.fixture
def folder(tmp_path: Path) -> Iterator[Path]:
    yield tmp_path
    (tmp_path / "stop").touch()


def _멈췄다(path: Path) -> None:
    """15초 안에 하트비트가 1초 동안 자라지 않으면 지난다. 기한까지 거듭 견준다
    (`tests/tools/test_run_checks.py` 의 `_stops_growing`)."""
    끝 = time.monotonic() + 15
    while time.monotonic() < 끝:
        크기 = path.stat().st_size
        time.sleep(1)
        if path.stat().st_size == 크기:
            return
    pytest.fail(f"중단한 뒤에도 15초 동안 {path.name} 하트비트가 자란다")


@dataclass(frozen=True)
class _끝:
    code: int
    stderr: str
    pressed: list[float]
    cancelled: float | None
    ended: float


def _누른다(folder: Path, presses: int) -> _끝:
    """자식이 SIGINT 를 presses 번 올린다. 시각은 모두 벽시계다."""
    command = [sys.executable, "-c", _CHILD, str(LINGERING), str(folder), str(presses)]
    with (folder / "stderr.txt").open("w", encoding="utf-8") as stderr:
        child = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=stderr, text=True, encoding="utf-8"
        )
        try:
            out, _ = child.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            child.kill()
            child.communicate()
            pytest.fail("Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다")
    ended = time.time()
    pressed = [float(json.loads(line)["pressed"]) for line in out.splitlines() if "pressed" in line]
    cancelled = folder / CANCELLED
    return _끝(
        code=child.returncode,
        stderr=(folder / "stderr.txt").read_text(encoding="utf-8", errors="replace"),
        pressed=pressed,
        cancelled=float(cancelled.read_text(encoding="utf-8")) if cancelled.exists() else None,
        ended=ended,
    )


def test_Ctrl_C_를_한_번_누르면_서버를_닫고_중단으로_끝난다(folder: Path) -> None:
    끝 = _누른다(folder, presses=1)

    assert len(끝.pressed) == 1
    assert 끝.cancelled is not None, "첫째가 도구 호출을 취소하지 않았다"
    assert 끝.code == DIED_INTERRUPTED
    assert interrupt.INTERRUPTED in 끝.stderr
    _멈췄다(folder / "stay.hb")


def test_닫는_도중에_한_번_더_누르면_닫기를_기다리지_않고_끝난다(folder: Path) -> None:
    끝 = _누른다(folder, presses=2)

    assert len(끝.pressed) == 2
    assert 끝.cancelled is not None, "첫째가 도구 호출을 취소하지 않았다"
    assert 끝.cancelled < 끝.pressed[1], "둘째가 닫는 도중에 오지 않았다"
    assert 끝.code == DIED_INTERRUPTED
    assert interrupt.FORCED in 끝.stderr
    assert 끝.ended - 끝.pressed[1] < FORCED_WITHIN_SECONDS
