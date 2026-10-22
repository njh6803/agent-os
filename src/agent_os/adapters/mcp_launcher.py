"""MCP 서버 앞에 서는 POSIX 런처(ADR 0034). 서버가 끝나거나 agent-os 프로세스가 죽으면 서버의
프로세스 그룹을 거둔다.

MCP 어댑터(`agent_os.adapters.mcp`)가 윈도우가 아닌 OS 에서 서버 명령을
`<그 프로세스의 파이썬> -I 이 파일 <그 프로세스의 번호> <찾은 서버 명령> <인자…>`로 바꿔 상류(mcp 의
stdio 클라이언트)에 넘긴다. 매니페스트와 플러그인 작성자는 런처를 모른다. 표준 라이브러리만 쓴다.
`-I`는 이 파일의 폴더를 `sys.path`에 넣지 않아, 같은 폴더의 모듈 이름(`mcp` 등)이 표준 라이브러리나
패키지를 가리지 않게 한다.

**하는 일.** 상류는 POSIX 에서 서버를 새 세션으로 띄우므로 이 프로세스가 프로세스 그룹의
우두머리다. 진짜 서버를 같은 그룹의 자식으로 띄우고 표준 입출력은 상속으로 물려준 뒤, 자기 입력과
출력을 `/dev/null`로 바꾼다. 출력의 쓰는 쪽을 쥐고 있으면 서버가 끝나도 클라이언트가 출력의 끝을
보지 못한다. 표준 에러는 남긴다. 끄는 때는 둘이다. 서버가 끝났을 때(입력이 닫히면 스스로 끝나며
자식을 남긴 서버의 그 자식을 거둔다)와, 이 프로세스를 띄운 부모가 죽었을 때다(`kill -9`, 메모리
부족으로 강제 종료, CLI 의 둘째 Ctrl+C. 부모의 번호가 넘겨받은 번호와 달라진다). 그때 그룹 전체를
SIGKILL 로 한 번에 끈다. 그룹에는 이 프로세스도 들어 그 자리에서 함께 끝나므로 서버의 종료 코드는
넘기지 않는다. 상류의 클라이언트는 그것을 읽지 않는다.

**거부하는 때.** 그룹의 우두머리가 아니면(새 세션 없이 띄웠으면) 아무것도 띄우지 않는다. 그때 그룹을
끄면 부른 쪽의 그룹이 꺼진다. 부모의 번호는 뜬 뒤에 스스로 읽지 않고 넘겨받아 뜨자마자 한 번
견준다. 뜨는 사이에 부모가 죽으면 스스로 읽은 번호는 이미 입양한 쪽의 것이라 감시가 켜지지 않는다
(시제품의 첫 판). 둘 다 표준 에러에 한 줄을 남기고 종료 코드 2로 끝난다. 윈도우에서 불렸거나
인자가 모자랄 때도 같다. 서버를 띄우지 못하면(어댑터가 찾아본 뒤에 명령이 사라졌다, 실행할 수 없는
형식이다, 셔뱅이 가리키는 인터프리터가 없다) 한 줄과 종료 코드 127이고, 클라이언트에는 연결이 닫힌
것으로 보인다.

**대가.** 운영자의 프로세스 목록에서 서버마다 이 작은 파이썬 프로세스가 서버 위에 하나씩 보인다.
서버를 기다리는 스레드는 서버가 끝날 때까지 잠들고, 주 스레드는 0.2초마다 깨어나 부모를 본다.
그래서 부모가 죽은 뒤 많아야 0.2초 동안 서버가 남는다. 표준 라이브러리의 `Popen.wait`에 시간 상한을
주면 1ms 에서 시작해 두 배씩 늘린 간격(많아야 0.05초)으로 깨어나므로(CPython 3.12 `subprocess.py`
의 POSIX `Popen._wait`를 읽었다) 기다림을 스레드로 옮겼다. 윈도우가 아닌 모든 OS 에서 서지만 잰 것은
Linux 이고 macOS 는 재지 않았다(`.scratch/mcp-shutdown/spec.md` 의 "Linux 런처").

**거두지 못하는 것.** 런처와 상류는 둘 다 프로세스 그룹을 끄므로, 서버의 자손 가운데 그 그룹을
떠난 것(스스로 새 세션이나 새 프로세스 그룹을 연 것)은 거두지 못한다(ADR 0034 의 알려진 한계).
런처가 그룹을 끄기 전에 밖에서 먼저 죽으면(런처만 노린 SIGKILL, 메모리 부족) 상류는 서버가 끝난
것으로 보고 그룹 끄기를 건너뛰어 서버가 남는다(코드를 읽은 어림. 재지 않았다).

**뺄 계기.** 상류가 POSIX 에서 스스로 끝난 서버의 그룹을 거두게 되면 런처를 뺀다. 그때 부모가 죽는
경우를 누가 맡을지 다시 본다. 상류는 POSIX 에서 부모가 죽는 경우를 다루지 않는다(윈도우는 Job
Object 가 다룬다). 상류(python-sdk)에 올릴 이슈 초안은 `.scratch/mcp-shutdown/upstream-issue.md`
이고, 2026-10-21 사용자가 올리지 않기로 해 아직 올리지 않았다. 그래서 상류가 이 빈틈을 아는지는 알지
못한다.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import threading

PARENT_POLL_SECONDS = 0.2
EXIT_REFUSED = 2
EXIT_SPAWN_FAILED = 127


def main(argv: list[str]) -> int:
    if sys.platform == "win32":
        return _refuse("POSIX 에서만 쓴다")
    if len(argv) < 2 or not (argv[0].isascii() and argv[0].isdecimal()):
        return _refuse("띄운 프로세스의 번호와 서버 명령을 받는다")
    if os.getpgrp() != os.getpid():
        return _refuse("프로세스 그룹의 우두머리가 아니라 서버를 띄우지 않는다")
    parent = int(argv[0])
    if os.getppid() != parent:
        return _refuse("띄운 프로세스가 이미 끝나 서버를 띄우지 않는다")
    try:
        server = subprocess.Popen(argv[1:])
    except OSError as error:
        sys.stderr.write(f"런처: MCP 서버를 띄우지 못했다: {error}\n")
        return EXIT_SPAWN_FAILED
    try:
        _detach_stdio()
        _wait_for_server_or_parent(server, parent)
    finally:
        # 서버를 띄운 뒤라면 어디서 예외가 나도(입출력 바꾸기나 스레드 시작의 자원 고갈) 끈다.
        # 예외로 이 프로세스만 끝나면 상류는 서버가 끝난 것으로 보고 그룹 끄기를 건너뛴다.
        os.killpg(0, signal.SIGKILL)
    return 0  # 닿지 않는다. 그룹에 이 프로세스도 들어 위에서 함께 끝난다.


def _refuse(message: str) -> int:
    sys.stderr.write(f"런처: {message}\n")
    return EXIT_REFUSED


def _detach_stdio() -> None:
    """입력과 출력을 `/dev/null`로 바꾼다. 서버가 물려받은 쪽은 그대로다."""
    devnull = os.open(os.devnull, os.O_RDWR)
    os.dup2(devnull, 0)
    os.dup2(devnull, 1)
    os.close(devnull)


def _wait_for_server_or_parent(server: subprocess.Popen[bytes], parent: int) -> None:
    """서버가 끝나거나 부모의 번호가 넘겨받은 것과 달라질 때까지 기다린다."""
    ended = threading.Event()
    threading.Thread(target=_wait, args=(server, ended), daemon=True).start()
    while not ended.wait(PARENT_POLL_SECONDS):
        if os.getppid() != parent:
            break


def _wait(server: subprocess.Popen[bytes], ended: threading.Event) -> None:
    server.wait()
    ended.set()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
