"""실제 `npx`의 everything 서버로 닫기를 재현한다(윈도우, 이 PC). ADR 0034 의 재현 프로브다.

`plugins/mcp/everything`의 매니페스트와 같은
명령(`npx -y @modelcontextprotocol/server-everything`)을 mcp 의 `stdio_client`로 띄운다. 연결을 연
뒤 이 프로세스의 자손 프로세스 목록(번호, 만든 시각, 명령줄)을 찍고, 이벤트 루프를 살려 둔 채 닫은
뒤 1초와 4초, 그리고 4초 뒤에 부른 `gc.collect()`의 1초 뒤에 같은 번호·만든 시각의 프로세스가
남았는지 본다. 루프를 닫은 뒤에도 한 번 본다. 목록은 PowerShell 의 `Get-CimInstance
Win32_Process`로 읽는다.

사례:
- `cancel`: 오래 걸리는 도구(이름에 "long"이 든 첫 도구, 30초) 도중에 기한(1초)이 온다.
- `normal`: 도구를 부르지 않고 정상으로 닫는다.

`--adapter raw`(기본)는 상류의 `stdio_client`와 `ClientSession`을 직접 열고, `--adapter repo`는
저장소의 지금 어댑터(`McpTools`, langchain-mcp-adapters 뒤의 mcp 1.30.0)로 연다. 뒤의 것은 저장소
`.venv`에서만 돈다. 첫 판(raw 만)의 1.30.0 회차는 기한 1초 뒤에 남은 프로세스가 4초 뒤에는 없어,
2026-10-15 인터뷰가 지금 어댑터로 본 것(`gc.collect()` 까지 남는다)과 같은 대조군이 되지 못했다.
그래서 지금 어댑터의 갈래를 더했다.

표지: `cancel`은 오래 걸리는 도구가 있었고 그 호출이 기한 전에 돌아오지 않았으며, 두 사례 모두 연
뒤의 자손에 node 가 있었다. 없으면 측정이 아니라고 세고 종료 코드를 1로 둔다.

남은 프로세스는 루프를 닫은 뒤의 목록을 본 다음, 번호와 만든 시각과 명령줄이 연 뒤의 목록과 모두
같은 것만 `taskkill /F /PID`로 끈다(번호는 다시 쓰여 남의 프로세스를 끌 수 있다. 일지 2026-10-16-36
"사고"). 돌리는 명령은 `README.md`에 있다.
"""

from __future__ import annotations

import argparse
import gc
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters, stdio_client

type Json = object

COMMAND = "npx"
ARGS = ["-y", "@modelcontextprotocol/server-everything"]
DEADLINE_SECONDS = 1.0
_LIST = (
    "Get-CimInstance Win32_Process | "
    "Select-Object ProcessId,ParentProcessId,CreationDate,Name,CommandLine | "
    "ConvertTo-Json -Compress"
)

type Proc = dict[str, str | int | None]


def _processes() -> list[Proc]:
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command", _LIST],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    ).stdout
    rows = json.loads(out)
    return [
        {
            "pid": int(row["ProcessId"]),
            "ppid": int(row["ParentProcessId"]),
            "created": str(row["CreationDate"]),
            "name": row["Name"],
            "cmd": row["CommandLine"],
        }
        for row in rows
    ]


def _descendants(root: int) -> list[Proc]:
    rows = _processes()
    children: dict[int, list[Proc]] = {}
    for row in rows:
        children.setdefault(int(str(row["ppid"])), []).append(row)
    found: list[Proc] = []
    stack = [root]
    while stack:
        for row in children.get(stack.pop(), []):
            if str(row["name"]).lower() in {"powershell.exe", "conhost.exe"}:
                continue
            found.append(row)
            stack.append(int(str(row["pid"])))
    return found


def _alive(snapshot: list[Proc]) -> list[Proc]:
    now = {(row["pid"], row["created"], row["cmd"]): row for row in _processes()}
    return [row for row in snapshot if (row["pid"], row["created"], row["cmd"]) in now]


def _short(rows: list[Proc]) -> list[str]:
    return [f"{row['pid']} {row['name']} {str(row['cmd'])[-80:]}" for row in rows]


def _package_version(rows: list[Proc]) -> str | None:
    for row in rows:
        cmd = str(row["cmd"] or "")
        marker = "@modelcontextprotocol\\server-everything"
        if marker in cmd:
            start = cmd.rfind('"', 0, cmd.find(marker)) + 1
            root = Path(cmd[start : cmd.find(marker) + len(marker)].strip('" '))
            package = root / "package.json"
            if package.exists():
                return str(json.loads(package.read_text(encoding="utf-8"))["version"])
    return None


type Call = Callable[[str, dict[str, Json]], Awaitable[object]]


@asynccontextmanager
async def _raw() -> AsyncIterator[tuple[list[str], Call]]:
    """상류의 `stdio_client`와 `ClientSession`을 직접 연다."""
    params = StdioServerParameters(command=COMMAND, args=ARGS)
    async with stdio_client(params, errlog=sys.stderr) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = [tool.name for tool in (await session.list_tools()).tools]
            yield tools, session.call_tool


@asynccontextmanager
async def _repo() -> AsyncIterator[tuple[list[str], Call]]:
    """저장소의 지금 어댑터(`McpTools`, langchain-mcp-adapters)로 연다. 저장소 `.venv`에서만
    된다."""
    from agent_os.adapters.mcp import McpTools
    from agent_os.sdk import McpServer, PluginName

    server = McpServer(command=COMMAND, args=tuple(ARGS))
    async with McpTools().connect({PluginName("everything"): server}) as connection:
        yield [spec.name for spec in connection.tools()], connection.call


async def _case(case: str, adapter: str) -> dict[str, object]:
    record: dict[str, object] = {"_opened_rows": []}
    deadline: float | None = None
    started_close: float | None = None

    async def drive() -> bool:
        """새는 예외를 보려고 연결 전체를 감싼다. 오래 걸리는 도구가 없으면 거짓이고 뒤의 확인을
        건너뛴다(옮기기 전 판의 이른 `return`)."""
        nonlocal deadline, started_close
        with anyio.fail_after(120) as scope:
            async with _repo() if adapter == "repo" else _raw() as (tools, call):
                opened = _descendants(os.getpid())
                record["_opened_rows"] = opened
                record["opened"] = _short(opened)
                record["node_opened"] = any(row["name"] == "node.exe" for row in opened)
                record["everything_version"] = _package_version(opened)
                if case == "cancel":
                    long = next((name for name in tools if "long" in name.lower()), None)
                    record["long_tool"] = long
                    if long is None:
                        return False
                    scope.deadline = anyio.current_time() + DEADLINE_SECONDS
                    deadline = scope.deadline
                    await call(long, {"duration": 30, "steps": 3})
                    record["unexpected"] = "오래 걸리는 도구가 기한 안에 돌아왔다"
                started_close = anyio.current_time()
            if started_close is not None:
                record["close_seconds"] = round(anyio.current_time() - started_close, 3)
        return True

    try:
        if not await drive():
            return record
    except Exception as error:
        record["exception"] = f"{type(error).__name__}: {error}"[:200]
        if deadline is not None:
            record["deadline_to_exception_seconds"] = round(anyio.current_time() - deadline, 3)
    # 이벤트 루프를 살려 둔 채 본다. serve 는 오래 사는 프로세스라, 루프를 닫은 뒤에 보면 닫히다 만
    # 연결의 파이프가 루프와 함께 정리되어 서버가 입력의 끝을 보고 스스로 끝나는 것을 잰다(첫 판이
    # 그랬다. 1초 뒤에 남은 것이 4초 뒤에는 없었다). 2026-10-15 인터뷰는 그것이 `gc.collect()` 까지
    # 남는 것을 봤다. 그래서 4초 뒤에 명시한 `gc.collect()`를 부르고 1초 뒤에 한 번 더 본다.
    opened = record["_opened_rows"]
    rows = opened if isinstance(opened, list) else []
    await anyio.sleep(1)
    record["alive_1s"] = _short(_alive(rows))
    await anyio.sleep(3)
    record["alive_4s"] = _short(_alive(rows))
    record["gc_collected"] = gc.collect()
    await anyio.sleep(1)
    record["alive_after_gc"] = _short(_alive(rows))
    return record


def run_case(case: str, adapter: str) -> dict[str, object]:
    record = anyio.run(_case, case, adapter)
    opened = record.pop("_opened_rows", [])
    if not isinstance(opened, list):
        opened = []
    survivors = _alive(opened)
    record["alive_after_loop"] = _short(survivors)
    killed: list[str] = []
    for row in survivors:
        if not _alive([row]):  # 끄기 직전에 번호·만든 시각·명령줄을 한 번 더 대 본다
            continue
        subprocess.run(["taskkill", "/F", "/PID", str(row["pid"])], capture_output=True)
        killed.append(str(row["pid"]))
    record["killed_by_probe"] = killed
    marked = record.get("node_opened") is True
    if case == "cancel":
        marked = marked and record.get("long_tool") is not None and "unexpected" not in record
    record["marked"] = marked
    return record


def main() -> int:
    if os.name != "nt":
        print("이 프로브는 윈도우에서만 돈다", file=sys.stderr)
        return 2
    parser = argparse.ArgumentParser()
    parser.add_argument("--adapter", choices=("raw", "repo"), default="raw")
    parser.add_argument("cases", nargs="*")
    options = parser.parse_args()
    cases = options.cases or ["normal", "cancel"]
    header: dict[str, str] = {
        "adapter": options.adapter,
        "mcp": importlib.metadata.version("mcp"),
        "anyio": importlib.metadata.version("anyio"),
        "python": platform.python_version(),
        "platform": platform.platform(),
    }
    if options.adapter == "repo":
        header["langchain-mcp-adapters"] = importlib.metadata.version("langchain-mcp-adapters")
    print(json.dumps(header))
    unmarked: list[str] = []
    for case in cases:
        record = run_case(case, options.adapter)
        print(json.dumps({"case": case, **record}, ensure_ascii=False))
        if not record["marked"]:
            unmarked.append(case)
    print(json.dumps({"unmarked": unmarked}, ensure_ascii=False))
    return 1 if unmarked else 0


if __name__ == "__main__":
    sys.exit(main())
