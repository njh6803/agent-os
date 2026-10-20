"""MCP 서버 앞에 서는 POSIX 런처(ADR 0034). 어댑터가 `python -I 이 파일 <서버 명령> [인자…]`로
띄운다.

(시제품. `.scratch/mcp-shutdown/probes/full_stack.py`가 저장소 사본에 얹어 잰다.)

mcp 의 stdio_client 는 POSIX 에서 서버를 새 세션으로 띄우므로 이 프로세스가 프로세스 그룹의
우두머리다. 진짜 서버를 같은 그룹의 자식으로 띄우고 표준 입출력은 상속으로 물려준 뒤 자기 사본은
놓는다. 서버가 끝나거나, 이 프로세스를 띄운 부모가 죽으면(부모 프로세스 번호가 바뀐다) 그룹 전체를
SIGKILL 로 끈다. 그룹에는 이 프로세스도 들어 그 자리에서 함께 끝난다. 서버의 종료 코드는 넘기지
않는다 — mcp 의 클라이언트는 그것을 읽지 않는다.

그룹의 우두머리가 아니면(새 세션 없이 띄웠으면) 아무것도 띄우지 않고 끝난다. 그때 그룹을 끄면 부른
쪽의 그룹이 꺼진다. `-I`로 띄우는 것은 이 파일의 폴더가 `sys.path`에 들어 같은 폴더의 `mcp.py`가
표준 라이브러리처럼 읽히지 않게 하기 위해서다.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys

PARENT_POLL_SECONDS = 0.2
EXIT_REFUSED = 2
EXIT_SPAWN_FAILED = 127


def main(argv: list[str]) -> int:
    if sys.platform == "win32":
        sys.stderr.write("런처: POSIX 에서만 쓴다\n")
        return EXIT_REFUSED
    if not argv:
        sys.stderr.write("런처: 서버 명령이 없다\n")
        return EXIT_REFUSED
    if os.getpgrp() != os.getpid():
        sys.stderr.write("런처: 프로세스 그룹의 우두머리가 아니라 서버를 띄우지 않는다\n")
        return EXIT_REFUSED
    parent = os.getppid()
    try:
        server = subprocess.Popen(argv)
    except OSError as error:
        sys.stderr.write(f"런처: MCP 서버를 띄우지 못했다: {error}\n")
        return EXIT_SPAWN_FAILED
    devnull = os.open(os.devnull, os.O_RDWR)
    os.dup2(devnull, 0)
    os.dup2(devnull, 1)
    os.close(devnull)
    while True:
        try:
            server.wait(timeout=PARENT_POLL_SECONDS)
            break
        except subprocess.TimeoutExpired:
            if os.getppid() != parent:
                break
    os.killpg(0, signal.SIGKILL)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
