"""Linux 런처 시제품(ADR 0034). 구현 티켓이 옮길 모양을 재려고 프로브에 둔다.

mcp 2.x의 `stdio_client`는 POSIX에서 서버를 새 세션(`start_new_session=True`)으로 띄우므로, 그
자리에 이 파일을 띄우면 이것이 프로세스 그룹의 우두머리가 된다. 진짜 서버를 같은 그룹의 자식으로
띄우고 표준 입출력은 상속으로 물려준 뒤 자기 사본은 놓는다. 서버가 끝나면 그룹 전체를 SIGKILL로
끈다. 그룹에는 런처 자신도 들어 런처도 그 자리에서 끝난다.

인자: `[--watch-parent] <서버 명령> [인자…]`. `--watch-parent`를 주면 서버를 기다리는 동안 0.2초마다
부모가 바뀌었는지(부모가 죽어 다른 프로세스에 입양되었는지) 보고, 바뀌면 서버가 끝나기 전이라도
그룹을 끈다.

그룹의 우두머리가 아니면(새 세션 없이 띄웠으면) 아무것도 띄우지 않고 끝난다. 그때 `killpg(0)`은
부른 쪽의 그룹을 끈다.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys

PARENT_POLL_SECONDS = 0.2
EXIT_NOT_LEADER = 2
EXIT_SPAWN_FAILED = 127


def _release_stdio() -> None:
    """런처가 쥔 표준 입출력의 사본을 놓는다. 입력의 끝과 출력의 끝은 서버의 것이다."""
    devnull = os.open(os.devnull, os.O_RDWR)
    os.dup2(devnull, 0)
    os.dup2(devnull, 1)
    os.close(devnull)


def main(argv: list[str]) -> int:
    watch = bool(argv) and argv[0] == "--watch-parent"
    command = argv[1:] if watch else argv
    if not command:
        sys.stderr.write("런처: 서버 명령이 없다\n")
        return EXIT_NOT_LEADER
    if os.getpgrp() != os.getpid():
        sys.stderr.write("런처: 프로세스 그룹의 우두머리가 아니라 서버를 띄우지 않는다\n")
        return EXIT_NOT_LEADER
    parent = os.getppid()
    try:
        server = subprocess.Popen(command)
    except OSError as error:
        sys.stderr.write(f"런처: MCP 서버를 띄우지 못했다: {error}\n")
        return EXIT_SPAWN_FAILED
    _release_stdio()
    while True:
        try:
            server.wait(timeout=PARENT_POLL_SECONDS if watch else None)
            break
        except subprocess.TimeoutExpired:
            if os.getppid() != parent:
                break
    os.killpg(0, signal.SIGKILL)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
