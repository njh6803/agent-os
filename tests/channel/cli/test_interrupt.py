"""CLI 의 Ctrl+C 처리기. 처리기가 프로세스를 끝내므로 자식 프로세스에서 잰다.

MCP 사례의 자식은 처리기 아래에서 진짜 MCP 어댑터로 입력이 닫혀도 끝나지 않는 서버
(`tests/adapters/mcp_lingering.py` 의 `stay`)를 열고 스스로 SIGINT 를 올린다. 그 서버를 닫는 데
상류의 유예 2초가 든다. 사례마다 재려는 상황이 났다는 표지를 먼저 본다. 도구 호출 도중의 누름은
서버가 호출을 받았다는 표지(`slow`) 뒤에 오고, 닫는 도중의 누름은 자식이 연결을 나서기 직전에 쓴
표지(`closing`) 0.5초 뒤에 온다. 가짜 포트로 상류의 닫기를 흉내 내지 않는다. 처리기가 바꾸는 모양이
진짜 상류의 닫기에서만 나서, 흉내로는 처리기를 빠뜨린 구현도 초록이 된다(명세의 Testing Decisions).

신호를 올리는 법은 OS 마다 다르다. POSIX 에서 보조 스레드가 `raise_signal` 로 올리면 그 스레드가
신호를 받아 주 스레드의 대기가 깨지지 않는다. 그래서 그 스레드는 SIGINT 를 막고 프로세스에 보낸다.
윈도우는 C 처리기가 올린 스레드에서 돌고 이벤트 루프를 깨우므로 그대로 올린다. 시각은 모두
벽시계이고 자식이 파일에 남긴다.
"""

import signal
import subprocess
import sys
import time
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

from agent_os.channel.cli.interrupt import FORCED, INTERRUPTED, STATUS_CONTROL_C_EXIT

LINGERING = Path(__file__).parents[2] / "adapters" / "mcp_lingering.py"
# 처리하지 않은 KeyboardInterrupt 로 끝나는 파이썬과 같은 꼴. `Popen` 이 보는 값이다.
DIED_INTERRUPTED = STATUS_CONTROL_C_EXIT if sys.platform == "win32" else -signal.SIGINT
# 자식이 끝나기를 기다리는 상한. 넘으면 끝나지 않은 것으로 보고 `Popen` 핸들로 끈다.
ENDED_WITHIN_SECONDS = 30
# 둘째가 닫기를 끊으면 둘째 뒤 끝나기까지가 명세의 프로브(`close_paths.py --cli-handler scope`)에서
# 0.006~0.133초라 문턱은 그 7배가 넘는다(`.claude/rules/tests.md` 의 시간 단언). 이 구현은
# 윈도우에서 홀로 0.015~0.017초였다(아래 `_누른다` 를 사례마다 세 번 불러 손으로 봤다, 일지
# 2026-10-21-06). 끊지 못하면 자식은 첫째의 닫기(상류의 유예 2초)를 마치고서야 끝나 둘째 뒤 약
# 1.5초다.
FORCED_WITHIN_SECONDS = 1.0
# 닫는 도중의 첫째 뒤 끝나기까지. 범위로 전하는 처리기의 시제품은 누른 뒤 1.48~1.56초였고, 네이티브
# 취소로 전하면 10초 안에 끝나지 않았다(`close_paths.py` 의 `cli_ctrl_c_closing`, 두 OS). 이 구현은
# 윈도우에서 홀로 1.47~1.53초였다(위와 같이 손으로 봤다).
CLOSED_WITHIN_SECONDS = 8.0

_MCP_CHILD = """
import asyncio
import os
import signal
import sys
import threading
import time
from pathlib import Path

from agent_os.adapters.mcp import McpTools
from agent_os.channel.cli.interrupt import run_interruptibly
from agent_os.sdk import McpServer, PluginName

lingering, folder, moment, presses = sys.argv[1], Path(sys.argv[2]), sys.argv[3], int(sys.argv[4])
server = McpServer(command=sys.executable, args=(lingering, "stay", str(folder)))
marker = folder / ("closing" if moment == "closing" else "slow")


def press() -> None:
    if os.name == "posix":
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
    end = time.monotonic() + 30
    while not marker.exists() and time.monotonic() < end:
        time.sleep(0.05)
    for count in range(presses):
        if count or moment == "closing":
            time.sleep(0.5)
        (folder / f"pressed-{count}").write_text(str(time.time()), encoding="utf-8")
        if os.name == "posix":
            os.kill(os.getpid(), signal.SIGINT)
        else:
            signal.raise_signal(signal.SIGINT)


async def main() -> None:
    async with McpTools().connect({PluginName("lingering"): server}) as connection:
        threading.Thread(target=press, daemon=True).start()
        if moment == "closing":
            await connection.call("slow", {"seconds": 0.1})
            marker.write_text(str(time.time()), encoding="utf-8")
        else:
            try:
                await connection.call("slow", {"seconds": 30})
            except asyncio.CancelledError:
                (folder / "cancelled").write_text(str(time.time()), encoding="utf-8")
                raise
    (folder / "closed").write_text(str(time.time()), encoding="utf-8")


run_interruptibly(main)
"""

_SLEEPING_CHILD = """
import asyncio
import os
import signal
import sys
import threading
import time
from pathlib import Path

from agent_os.channel.cli.interrupt import run_interruptibly

folder = Path(sys.argv[1])


def press() -> None:
    if os.name == "posix":
        signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGINT})
    end = time.monotonic() + 30
    while not (folder / "pipe-closed").exists():
        if time.monotonic() > end:
            return
        time.sleep(0.05)
    (folder / "pressed-0").write_text(str(time.time()), encoding="utf-8")
    if os.name == "posix":
        os.kill(os.getpid(), signal.SIGINT)
    else:
        signal.raise_signal(signal.SIGINT)


async def main() -> None:
    threading.Thread(target=press, daemon=True).start()
    await asyncio.sleep(60)


run_interruptibly(main)
"""

_RAISING_CHILD = """
import asyncio
import signal
import sys
from pathlib import Path

from agent_os.channel.cli.interrupt import run_interruptibly

folder = Path(sys.argv[1])


async def main() -> None:
    signal.raise_signal(signal.SIGINT)
    try:
        await asyncio.sleep(60)
    finally:
        (folder / "raised").touch()
        raise RuntimeError("정리가 터졌다")


run_interruptibly(main)
"""


@pytest.fixture
def folder(tmp_path: Path) -> Iterator[Path]:
    """가짜 서버의 하트비트와 자식의 표지가 놓이는 폴더. 끝날 때 멈춤 파일로 남은 서버를 끝낸다."""
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


def _기다린다(child: subprocess.Popen[bytes]) -> bool:
    """자식이 상한 안에 끝났는가. 넘으면 `Popen` 핸들로 끄고 거둔다. 실패는 부른 쪽이 예외 처리
    밖에서 낸다. 안에서 내면 시간 초과의 추적이 실패에 이어 붙는다."""
    try:
        child.wait(timeout=ENDED_WITHIN_SECONDS)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait()
        return False
    return True


def _시각(path: Path) -> float | None:
    return float(path.read_text(encoding="utf-8")) if path.exists() else None


@dataclass(frozen=True)
class _끝:
    code: int
    stderr: str
    called: bool
    pressed: list[float]
    cancelled: float | None
    closing: float | None
    closed: float | None
    ended: float


def _누른다(folder: Path, moment: str, presses: int) -> _끝:
    """MCP 사례의 자식이 `moment`(도구 호출 도중 `calling`, 닫는 도중 `closing`)에 SIGINT 를
    `presses` 번 올린다."""
    command = [sys.executable, "-c", _MCP_CHILD, str(LINGERING), str(folder), moment, str(presses)]
    with (folder / "stderr.txt").open("w", encoding="utf-8") as stderr:
        child = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=stderr)
        ended_in_time = _기다린다(child)
    if not ended_in_time:
        pytest.fail(f"Ctrl+C 를 누른 자식이 {ENDED_WITHIN_SECONDS}초 안에 끝나지 않았다")
    ended = time.time()
    pressed = [_시각(folder / f"pressed-{count}") for count in range(presses)]
    return _끝(
        code=child.returncode,
        stderr=(folder / "stderr.txt").read_text(encoding="utf-8", errors="replace"),
        called=(folder / "slow").exists(),
        pressed=[at for at in pressed if at is not None],
        cancelled=_시각(folder / "cancelled"),
        closing=_시각(folder / "closing"),
        closed=_시각(folder / "closed"),
        ended=ended,
    )


def test_도구_호출_도중에_한_번_누르면_서버를_닫고_중단으로_끝난다(folder: Path) -> None:
    끝 = _누른다(folder, "calling", presses=1)

    assert 끝.called, "서버가 도구 호출을 받지 않았다"
    assert len(끝.pressed) == 1
    assert 끝.cancelled is not None, "첫째가 도구 호출을 취소하지 않았다"
    assert 끝.pressed[0] < 끝.cancelled
    assert 끝.code == DIED_INTERRUPTED
    # 둘째의 한 줄이 첫째의 한 줄로 시작하므로 둘째의 것이 아님도 본다.
    assert INTERRUPTED in 끝.stderr
    assert FORCED not in 끝.stderr
    assert "Traceback" not in 끝.stderr
    _멈췄다(folder / "stay.hb")


def test_닫는_도중에_한_번_더_누르면_닫기를_기다리지_않고_끝난다(folder: Path) -> None:
    끝 = _누른다(folder, "calling", presses=2)

    assert 끝.called, "서버가 도구 호출을 받지 않았다"
    assert len(끝.pressed) == 2
    assert 끝.cancelled is not None, "첫째가 도구 호출을 취소하지 않았다"
    assert 끝.cancelled < 끝.pressed[1], "둘째가 닫는 도중에 오지 않았다"
    assert 끝.code == DIED_INTERRUPTED
    assert FORCED in 끝.stderr
    assert 끝.ended - 끝.pressed[1] < FORCED_WITHIN_SECONDS


def test_서버를_닫기_시작한_뒤에_한_번_누르면_닫기를_마치고_중단으로_끝난다(folder: Path) -> None:
    """답을 받은 뒤 core 가 도구 연결을 닫는 동안이나 실행 타임아웃 뒤의 닫기에서 누른 것과 같다.
    누름이 닫기 끝보다 늦으면 재려는 상황이 아니다. 닫기 끝이 없으면(취소가 닫기 끝의 기록 앞에서
    빠져나갔다) 앞으로 센다."""
    끝 = _누른다(folder, "closing", presses=1)

    assert 끝.closing is not None, "자식이 연결을 나서지 않았다"
    assert len(끝.pressed) == 1
    assert 끝.closing < 끝.pressed[0]
    assert 끝.closed is None or 끝.pressed[0] < 끝.closed, "누르기 전에 닫기가 끝났다"
    assert 끝.code == DIED_INTERRUPTED
    assert INTERRUPTED in 끝.stderr
    assert FORCED not in 끝.stderr
    assert 끝.ended - 끝.pressed[0] < CLOSED_WITHIN_SECONDS
    _멈췄다(folder / "stay.hb")


def test_표준_에러를_읽는_쪽이_떠나도_중단의_꼴로_끝난다(folder: Path) -> None:
    """`agent-os run … 2>&1 | head` 처럼 읽는 쪽이 먼저 떠나 한 줄을 쓰지 못한 경우다."""
    command = [sys.executable, "-c", _SLEEPING_CHILD, str(folder)]
    child = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if child.stderr is not None:
        child.stderr.close()
    (folder / "pipe-closed").touch()
    if not _기다린다(child):
        pytest.fail(f"자식이 {ENDED_WITHIN_SECONDS}초 안에 끝나지 않았다")

    assert (folder / "pressed-0").exists(), "파이프를 닫은 뒤에 누르지 않았다"
    assert child.returncode == DIED_INTERRUPTED


def test_누른_뒤_실행이_취소가_아닌_예외로_끝나도_중단의_꼴로_끝난다(folder: Path) -> None:
    """첫째의 취소를 받은 정리가 다른 예외를 내 범위가 그 취소를 삼키지 못한 경우다. 누른 사람이
    바란 것은 중단이라 그 예외의 추적 대신 첫째의 한 줄로 끝난다."""
    command = [sys.executable, "-c", _RAISING_CHILD, str(folder)]
    with (folder / "stderr.txt").open("w", encoding="utf-8") as stderr:
        child = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=stderr)
        ended_in_time = _기다린다(child)
    if not ended_in_time:
        pytest.fail(f"자식이 {ENDED_WITHIN_SECONDS}초 안에 끝나지 않았다")
    written = (folder / "stderr.txt").read_text(encoding="utf-8", errors="replace")

    assert (folder / "raised").exists(), "취소를 받은 정리가 예외를 내지 않았다"
    assert child.returncode == DIED_INTERRUPTED
    assert INTERRUPTED in written
    assert FORCED not in written
    assert "Traceback" not in written
