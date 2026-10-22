"""MCP 어댑터의 닫기 테스트와 CLI 처리기 테스트가 띄우는 가짜 프로세스. 첫 인자가 역할이다.

`leaving` 을 뺀 셋은 하트비트 파일(`<역할>.hb`)에 0.1초마다 한 바이트를 덧붙이고, 같은 폴더의 멈춤
파일이 생기거나 120초가 지나면 스스로 끝난다. `leaving` 은 하트비트를 쓰지 않고(그 자식이 쓴다)
입력이 닫혀야 끝난다. 테스트는 남은 프로세스를 프로세스 번호로 끄지 않고 멈춤 파일로 끝낸다. 번호는
다시 쓰여 남의 프로세스를 끌 수 있다(일지 2026-10-16-36 "사고"). 120초는 한 사례가 부하에서 쓰는
가장 긴 시간(하트비트가 생기기를 기다리는 30초, 닫기, 멈췄는지 보는 15초)보다 넉넉하다. 그보다
짧으면 닫기가 서버를 끄지 못한 회차에도 스스로 끝나 초록이 될 수 있다.

- `wrapper <폴더>`: `stay` 서버를 자식으로 띄우고 그 종료 코드로 끝나는 감싸는 프로세스(`npx` 흉내).
- `stay <폴더>`: 입력이 닫혀도 끝나지 않는 MCP 서버. 도구 `slow(seconds)`와 `crash()`가 있다.
  `slow`는 불리면 폴더에 `slow` 파일을 남긴다(CLI 처리기 테스트가 도구 호출 도중에 누르려고
  기다린다). 읽는 쪽이 사라진 출력에 쓰다 난 오류에도 남는다.
- `leaving <폴더>`: 뜨자마자 `child`를 띄우고, 입력이 닫히면 그 자식을 거두지 않고 끝나는 MCP 서버.
- `child <폴더>`: 하트비트만 쓴다.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import anyio
from mcp.server.mcpserver import MCPServer

STOP = "stop"
SLOW = "slow"
LIFETIME_SECONDS = 120.0
BEAT_SECONDS = 0.1


def heartbeat(folder: Path, role: str) -> Path:
    return folder / f"{role}.hb"


def _beat(folder: Path, role: str) -> None:
    """하트비트를 쓰다 멈춤 파일이 생기거나 수명이 지나면 프로세스째 끝낸다.

    쓰기가 한 번 실패해도 이 스레드가 죽지 않게 넘긴다. 죽으면 하트비트만 멈춘 채 프로세스가 남아
    닫기를 지난 것처럼 보인다(명세 PR 직전 리뷰).
    """
    end = time.monotonic() + LIFETIME_SECONDS
    while time.monotonic() < end and not (folder / STOP).exists():
        try:
            with heartbeat(folder, role).open("ab") as file:
                file.write(b".")
        except OSError:
            pass
        time.sleep(BEAT_SECONDS)
    os._exit(0)


def _beating_in_background(folder: Path, role: str) -> None:
    threading.Thread(target=_beat, args=(folder, role), daemon=True).start()


def _server(folder: Path) -> MCPServer:
    server = MCPServer("lingering", log_level="ERROR")

    @server.tool()
    async def slow(seconds: float) -> str:
        (folder / SLOW).touch()
        await anyio.sleep(seconds)
        return "done"

    @server.tool()
    def crash() -> str:
        os._exit(3)

    return server


def main(role: str, folder: Path) -> None:
    if role == "child":
        _beat(folder, role)
    elif role == "wrapper":
        _beating_in_background(folder, role)
        sys.exit(subprocess.call([sys.executable, __file__, "stay", str(folder)]))
    elif role == "leaving":
        child = [sys.executable, __file__, "child", str(folder)]
        subprocess.Popen(child, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        _server(folder).run()
    elif role == "stay":
        _beating_in_background(folder, role)
        try:
            _server(folder).run()
        except Exception:
            pass  # 읽는 쪽이 사라진 출력에 쓰다 난 오류에도 남는다
        while True:
            time.sleep(1)
    else:
        raise SystemExit(f"모르는 역할: {role}")


if __name__ == "__main__":
    main(sys.argv[1], Path(sys.argv[2]))
