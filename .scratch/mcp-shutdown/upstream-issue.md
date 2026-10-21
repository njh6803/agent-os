# python-sdk에 올릴 이슈 초안

상태: **올리지 않았다.** 2026-10-21 티켓 03 세션이 이 초안을 보이고 올릴지 물었고, 사용자가 "올리지 않는다"를 골랐다(일지 2026-10-21-14). 바깥에 글을 올리는 일이라 사용자의 승인 없이는 올리지 않는다. 같은 사실을 런처 모듈(`src/agent_os/adapters/mcp_launcher.py`)의 독스트링에도 적었다. 뒤에 올리면 이 줄에 이슈 URL을 적는다.

올릴 곳은 <https://github.com/modelcontextprotocol/python-sdk/issues>다. 아래 `---` 사이가 본문이고, 제목은 첫 줄이다. 근거는 셋이다.

- 런처 없이 사례 2와 5를 더한 실험 커밋의 CI 실행(Linux의 `python` 잡에서 그 둘만 하트비트가 자란 까닭으로 빨갰다): <https://github.com/njh6803/agent-os/actions/runs/39579303270>
- 명세의 측정. `close_paths.py`의 `exit_child_normal`(Docker의 Linux, mcp 2.3.0 런처 없이 0.455초 뒤 자식 남음)과 `full_stack.py`의 런처 없는 대조군(사례 2와 5가 빨갰다). `probes/README.md`
- 본문의 재현 스크립트. 2026-10-21에 Docker의 `python:3.12.10-slim-bookworm`(`--init`)에서 `pip install mcp==2.3.0`만 하고 두 번 돌려 두 번 모두 자식이 남았고, `--control`(입력이 닫혀도 끝나지 않는 서버)은 상류가 그룹을 꺼 자식이 사라졌다

닫는 도중의 네이티브 취소 뒤 끝나지 않는 것(`cli_ctrl_c_closing`, `cli_ctrl_c_twice`)은 상류의 어디서 멈추는지 가르지 않아 본문의 "관련" 절에 관찰로만 든다. 부모가 죽는 경우(런처의 부모 감시)는 상류가 POSIX에서 다루지 않는 일이라(Windows는 Job Object가 다룬다) 들지 않는다.

---

stdio_client (POSIX): children left by a server that exits within the grace period are never terminated

**Version:** mcp 2.3.0, Python 3.12.10, Linux (Debian bookworm container, WSL2 kernel).

**What happens.** `stdio_client` starts the server in a new session, and on shutdown `_stop_server_process` closes stdin and waits `PROCESS_TERMINATION_TIMEOUT` for the server to exit. Only when the server does *not* exit in time does it call `_terminate_process_tree`, which kills the whole process group. If the server exits on its own within the grace period (the well-behaved case, and the fastest shutdown), any children it started stay in the group and keep running. On Windows the same path is covered by `close_process_job`, which reaps surviving job members; on POSIX that call is a no-op, so the two platforms differ.

We hit it with test servers shaped like a wrapper: a parent process that exits when stdin closes while a child it started keeps running. We have not checked whether real wrappers such as `npx` or `uvx` end up in this state.

**Reproduction.** Save as `repro.py` and run `python repro.py`, then `python repro.py --control`:

```python
import os
import sys
import tempfile
import time

import anyio
from mcp import StdioServerParameters, stdio_client

# A "server" that starts a long-lived child, then exits as soon as its stdin closes.
SERVER = """
import subprocess, sys
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
with open(sys.argv[1], "w") as f:
    f.write(str(child.pid))
sys.stdin.read()
"""
# Control: ignore stdin closing, so stdio_client escalates and kills the process group.
if "--control" in sys.argv:
    SERVER = SERVER.replace("sys.stdin.read()", "import time; time.sleep(60)")


async def main() -> None:
    pid_file = os.path.join(tempfile.mkdtemp(), "child.pid")
    params = StdioServerParameters(command=sys.executable, args=["-c", SERVER, pid_file])
    async with stdio_client(params):
        while not os.path.exists(pid_file) or not open(pid_file).read():
            await anyio.sleep(0.05)
    child = int(open(pid_file).read())
    time.sleep(1)
    try:
        os.kill(child, 0)
        print(f"child {child} is still running after stdio_client exited")
    except ProcessLookupError:
        print(f"child {child} is gone")


anyio.run(main)
```

Output (Linux, mcp 2.3.0, two runs and the control):

```
child 14 is still running after stdio_client exited
child 17 is still running after stdio_client exited
child 20 is gone
```

The same shape failed our CI on Linux while passing on Windows: https://github.com/njh6803/agent-os/actions/runs/39579303270 (`test_스스로_끝나며_자식을_남기는_서버를_닫으면_그_자식도_내려간다`, the child's heartbeat kept growing 15 s after the client closed).

**Expected.** After `stdio_client` exits, nothing from the server's process group is left running, on POSIX as on Windows.

**Possible fix.** On POSIX, after the server has exited (on its own or after escalation), signal the server's process group as well, e.g. `os.killpg(process.pid, signal.SIGKILL)` guarded for `ProcessLookupError`. The server was started with `start_new_session=True`, so its pid is the group id, and on Linux that id is not handed to a new process while any member of the group is alive. A SIGTERM-then-SIGKILL sequence like `terminate_posix_process_tree` would also work; we chose SIGKILL in our workaround because by then nobody waits for a graceful shutdown.

**Our workaround.** We start each server behind a small launcher that leads the process group, runs the real server as a child with inherited stdio, and kills the group with SIGKILL when the server exits. We would like to remove it once the SDK covers this case.

**Related (observation, not isolated).** On mcp 2.3.0 a second native `asyncio` cancellation (a second Ctrl+C under `asyncio.run`) that arrives while `stdio_client` is closing a server that ignores stdin closing does not let the process exit for at least 10 s; a stack dump showed the main thread inside `asyncio.runners._cancel_all_tasks`. We suspect `_drain_stdout` waiting for EOF from a live server under cancellation shielding, but did not confirm where it blocks. We avoided it by delivering Ctrl+C as an anyio cancel-scope cancellation instead of a native task cancellation.

---
