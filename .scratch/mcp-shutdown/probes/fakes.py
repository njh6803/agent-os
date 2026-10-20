"""닫기 프로브가 띄우는 가짜 프로세스 셋. `close_paths.py`와 `serve_shutdown.py`가 쓴다.

역할은 첫 인자로 고른다. 모두 하트비트 파일에 0.1초마다 한 바이트를 덧붙이고, 같은 폴더의 멈춤
파일(`stop`)이 생기거나 수명(60초)이 지나면 스스로 끝난다. 프로브는 남은 프로세스를 pid로 끄지 않고
멈춤 파일로 끝낸다(pid는 다시 쓰여 남의 프로세스를 끌 수 있다. 일지 2026-10-16-36 "사고").

- `child <하트비트> <멈춤>`: 하트비트만 쓰는 프로세스. 서버가 남기는 자식이다.
- `server <하트비트> <멈춤> <site> <eof> <자식> <sigterm>`: MCP stdio 서버. 도구 `slow(seconds)`는
  시작할 때 `<하트비트>.slow`를 만들고 잠든다. `eof`가 stay면 입력이 닫혀도 끝나지 않고(하트비트가
  계속 뛴다), exit면 입력이 닫히는 대로 끝난다. `자식`에 하트비트 경로를 주면 뜨자마자 그 자식을
  띄우고 끝날 때 거두지 않는다(`-`면 띄우지 않는다). `sigterm`이 ignore면 SIGTERM을 무시하고(POSIX),
  keep이면 기본 동작 그대로다.
- `wrapper <하트비트> <멈춤> <server 역할의 인자들…>`: 서버를 자식으로 띄우고 그 종료 코드로 끝나는
  감싸는 프로세스(`npx`·`cmd` 흉내). 표준 입출력을 그대로 물려준다.

`site`는 프로브 환경의 site-packages다. 기본 파이썬으로 띄워도 mcp를 import하게 `site.addsitedir`로
더한다. mcp 2.x의 `MCPServer`가 없으면 1.x의 `FastMCP`를 쓴다.
"""

from __future__ import annotations

import os
import signal
import site
import subprocess
import sys
import threading
import time
from pathlib import Path

BEAT_SECONDS = 0.1
LIFETIME_SECONDS = 60.0


def _beat_until_stopped(heartbeat: Path, stop: Path) -> None:
    """하트비트를 쓰다 멈춤 파일이 생기거나 수명이 지나면 프로세스째 끝낸다."""
    end = time.monotonic() + LIFETIME_SECONDS
    while time.monotonic() < end and not stop.exists():
        try:
            with heartbeat.open("ab") as file:
                file.write(b".")
        except OSError:
            pass
        time.sleep(BEAT_SECONDS)
    os._exit(0)


def _child(heartbeat: Path, stop: Path) -> None:
    _beat_until_stopped(heartbeat, stop)


def _server(
    heartbeat: Path, stop: Path, site_dir: str, on_eof: str, child: str, sigterm: str
) -> None:
    site.addsitedir(site_dir)
    if sigterm == "ignore":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    if child != "-":
        subprocess.Popen(
            [sys.executable, __file__, "child", child, str(stop)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
    threading.Thread(target=_beat_until_stopped, args=(heartbeat, stop), daemon=True).start()
    try:
        from mcp.server.mcpserver import MCPServer as Server
    except ImportError:
        from mcp.server.fastmcp import FastMCP as Server
    import anyio

    server = Server("probe", log_level="ERROR")

    @server.tool()
    async def slow(seconds: float) -> str:
        Path(f"{heartbeat}.slow").touch()
        await anyio.sleep(seconds)
        return "done"

    try:
        server.run()
    except Exception as error:
        # 읽는 쪽이 사라진 출력에 쓰다 난 오류(BrokenPipeError 따위)도 stay 면 남는다. 첫 판은
        # 이것을 잡지 않아, serve 를 SIGKILL 로 끈 사례에서 서버가 이 오류로 스스로 끝나 측정이
        # 갈렸다.
        sys.stderr.write(f"server.run 이 예외로 끝났다: {type(error).__name__}\n")
    if on_eof == "stay":
        while True:
            time.sleep(1)


def _wrapper(heartbeat: Path, stop: Path, server_args: list[str]) -> None:
    threading.Thread(target=_beat_until_stopped, args=(heartbeat, stop), daemon=True).start()
    sys.exit(subprocess.call([sys.executable, __file__, "server", *server_args]))


def main(argv: list[str]) -> None:
    role, heartbeat, stop, *rest = argv
    if role == "child":
        _child(Path(heartbeat), Path(stop))
    elif role == "server":
        site_dir, on_eof, child, sigterm = rest
        _server(Path(heartbeat), Path(stop), site_dir, on_eof, child, sigterm)
    elif role == "wrapper":
        _wrapper(Path(heartbeat), Path(stop), rest)
    else:
        raise SystemExit(f"모르는 역할: {role}")


if __name__ == "__main__":
    main(sys.argv[1:])
