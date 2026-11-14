"""컨테이너 안에서 도는 도움 스크립트. run.py 가 `python - <명령> <인자…>` 의 표준 입력으로 넘긴다.

혼자서는 아무것도 재지 않는다. 표준 라이브러리만 쓰고, 결과는 마지막 줄 `RESULT <json>` 하나다.
판정과 표지는 run.py 가 그 JSON 을 보고 한다. 서버의 포트는 환경 변수 PROBE_PORT(없으면 8000),
토큰은 인자로 받은 이름의 환경 변수에서 읽는다(값을 출력에 싣지 않는다).

명령(인자의 `-` 는 없음이다. 토큰은 환경 변수의 이름으로 받는다)
  http <메서드> <경로> <토큰|-> <JSON 본문|->       요청 하나의 상태와 본문
  openapi <토큰|->                                  /openapi.json 의 info 의 title 과 version
  sse <경로> <토큰> <JSON 본문> <마감 초>           POST 한 뒤 이벤트 스트림을 끝까지
  handshake <마감 초> <더 넘길 변수들|-> <명령…>    stdio MCP 서버를 띄워 initialize
  orphan                                            부모 잃은 프로세스가 거둬지는지
  procs                                             프로세스 목록과 좀비
  timecmd <횟수> <명령…>                            명령을 여러 번 돌린 종료 코드와 시간
  whoami                                            uid, getpass.getuser(), 환경, HOME
  pkginfo                                           agent-os 의 판이 보이는 자리와 도구 판
  writetest <폴더…>                                 폴더마다 파일 하나를 써 본다
  tree <폴더>                                       폴더 아래 파일과 소유자
  lines <파일> <머리>                               그 머리로 시작하는 줄
  setserver <매니페스트> <명령> <인자 JSON 배열>    stdio 매니페스트의 실행 명령을 바꾼다
  netcheck                                          npm 레지스트리에 TCP 로 닿는가

handshake 가 서버에 넘기는 환경은 `serve` 가 넘기는 것과 같게 고른다. mcp 2.3.0 의
`get_default_environment` 가 POSIX 에서 고르는 여섯(HOME, LOGNAME, PATH, SHELL, TERM, USER) 가운데
있는 것만이다(`mcp/client/stdio.py` 를 읽었다). 둘째 인자로 이름을 더 주면 그것도 넘긴다. 서버는 새
세션(프로세스 그룹)으로 띄우고, 끝나지 않으면 이 스크립트가 띄운 그 그룹만 끈다(자기 자식이고 아직
거두지 않았으므로 번호가 다른 프로세스로 넘어가 있을 수 없다).
"""

from __future__ import annotations

import errno
import getpass
import http.client
import json
import os
import queue
import signal
import socket
import stat
import subprocess
import sys
import threading
import time
from importlib import metadata
from pathlib import Path

PORT = int(os.environ.get("PROBE_PORT", "8000"))
MCP_ENV_KEYS = ("HOME", "LOGNAME", "PATH", "SHELL", "TERM", "USER")
type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

INITIALIZE: Json = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "serve-image-probe", "version": "0"},
    },
}
INITIALIZED: Json = {"jsonrpc": "2.0", "method": "notifications/initialized"}
TOOLS_LIST: Json = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}


def emit(result: Json) -> int:
    print("RESULT " + json.dumps(result, ensure_ascii=False))
    return 0


def headers_for(token_env: str, *, body: bool) -> dict[str, str]:
    headers: dict[str, str] = {}
    if token_env != "-":
        headers["Authorization"] = "Bearer " + os.environ.get(token_env, "")
    if body:
        headers["Content-Type"] = "application/json"
    return headers


def request_once(method: str, path: str, token_env: str, body: str) -> Json:
    connection = http.client.HTTPConnection("127.0.0.1", PORT, timeout=10)
    payload = None if body == "-" else body.encode("utf-8")
    try:
        connection.request(method, path, payload, headers_for(token_env, body=payload is not None))
        reply = connection.getresponse()
        text = reply.read().decode("utf-8", errors="replace")
    except (OSError, http.client.HTTPException) as error:
        return {"error": f"{type(error).__name__}: {error}"}
    finally:
        connection.close()
    return {"status": reply.status, "body": text}


def openapi(token_env: str) -> Json:
    """API 문서에서 판 칸만 꺼낸다. 문서 전체를 결과 줄에 싣지 않는다."""
    reply = request_once("GET", "/openapi.json", token_env, "-")
    body = dig(reply, "body")
    document = parse(body) if isinstance(body, str) else None
    return {
        "status": dig(reply, "status"),
        "error": dig(reply, "error"),
        "title": dig(document, "info", "title"),
        "version": dig(document, "info", "version"),
    }


def read_events(
    connection: http.client.HTTPConnection,
    reply: http.client.HTTPResponse,
    deadline: float,
    events: list[Json],
) -> str:
    """이벤트 스트림의 `data:` 줄을 JSON 으로 풀어 events 에 모은다. 어떻게 끝났는지를 돌려준다."""
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return "마감에 닿았다"
        if connection.sock is not None:
            connection.sock.settimeout(remaining)
        line = reply.readline()
        if not line:
            return "끝까지 읽었다"
        text = line.decode("utf-8", errors="replace").rstrip("\r\n")
        if text.startswith("data:"):
            events.append(parse(text[len("data:") :].strip()))


def post(
    connection: http.client.HTTPConnection, path: str, token_env: str, body: str
) -> http.client.HTTPResponse:
    connection.request("POST", path, body.encode("utf-8"), headers_for(token_env, body=True))
    return connection.getresponse()


def stream(path: str, token_env: str, body: str, seconds: float) -> Json:
    """POST 뒤 이벤트 스트림을 읽는다. 마감은 스트림 전체에 건다. 읽다 끊겨도 모은 것은 돌려준다."""
    started = time.monotonic()
    connection = http.client.HTTPConnection("127.0.0.1", PORT, timeout=seconds)
    events: list[Json] = []
    status = 0
    try:
        reply = post(connection, path, token_env, body)
        status = reply.status
        if status != http.client.OK:
            return {"status": status, "body": reply.read().decode(errors="replace"), "events": []}
        note = read_events(connection, reply, started + seconds, events)
    except (OSError, http.client.HTTPException) as error:
        note = f"{type(error).__name__}: {error}"
    finally:
        connection.close()
    seconds_taken = round(time.monotonic() - started, 3)
    return {"status": status, "events": events, "seconds": seconds_taken, "note": note}


def registry_reachable() -> bool:
    """npm 레지스트리에 TCP 로 닿는가. 네트워크가 끊긴 컨테이너라는 표지로 쓴다."""
    try:
        with socket.create_connection(("registry.npmjs.org", 443), timeout=5):
            return True
    except OSError:
        return False


def parse(text: str) -> Json:
    try:
        parsed: Json = json.loads(text)
    except ValueError:
        return {"unparsed": text[:200]}
    return parsed


def pump(stream: object, lines: queue.Queue[str | None]) -> None:
    """파이프 하나를 줄마다 큐에 넣고 EOF 에서 None 을 넣는다. 막히는 읽기는 이 스레드만 한다."""
    reader = getattr(stream, "readline", None)
    try:
        while callable(reader):
            raw = reader()
            if not isinstance(raw, bytes) or not raw:
                break
            lines.put(raw.decode("utf-8", errors="replace"))
    except (OSError, ValueError):
        pass
    finally:
        lines.put(None)


def next_reply(lines: queue.Queue[str | None], wanted: int, deadline: float) -> Json:
    """id 가 wanted 인 JSON-RPC 응답이 올 때까지 줄을 읽는다. 마감이나 EOF 면 None 이다."""
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        try:
            line = lines.get(timeout=remaining)
        except queue.Empty:
            return None
        if line is None:
            return None
        message = parse(line)
        if isinstance(message, dict) and message.get("id") == wanted:
            return message


def drain(lines: queue.Queue[str | None], seconds: float) -> list[str]:
    deadline = time.monotonic() + seconds
    collected: list[str] = []
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return collected
        try:
            line = lines.get(timeout=remaining)
        except queue.Empty:
            return collected
        if line is None:
            return collected
        collected.append(line.rstrip("\r\n"))


def send(process: subprocess.Popen[bytes], message: Json) -> bool:
    if process.stdin is None:
        return False
    try:
        process.stdin.write((json.dumps(message) + "\n").encode("utf-8"))
        process.stdin.flush()
    except OSError:
        return False
    return True


def dig(value: Json, *keys: str) -> Json:
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else None
    return value


def handshake(seconds: float, extra: str, argv: list[str]) -> Json:
    names = [*MCP_ENV_KEYS, *([] if extra == "-" else extra.split(","))]
    env = {name: os.environ[name] for name in names if name in os.environ}
    reachable = registry_reachable()
    started = time.monotonic()
    try:
        process = subprocess.Popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            start_new_session=True,
        )
    except OSError as error:
        failure = f"{type(error).__name__}: {error}"
        return {"spawned": False, "error": failure, "registry_reachable": reachable}
    out: queue.Queue[str | None] = queue.Queue()
    err: queue.Queue[str | None] = queue.Queue()
    threading.Thread(target=pump, args=(process.stdout, out), daemon=True).start()
    threading.Thread(target=pump, args=(process.stderr, err), daemon=True).start()
    deadline = started + seconds
    send(process, INITIALIZE)
    first = next_reply(out, 1, deadline)
    answered_at = round(time.monotonic() - started, 3)
    tools: Json = None
    if first is not None:
        send(process, INITIALIZED)
        send(process, TOOLS_LIST)
        tools = next_reply(out, 2, deadline)
    closed_at = time.monotonic()
    if process.stdin is not None:
        try:
            process.stdin.close()
        except OSError:
            pass
    exit_code: int | None
    try:
        exit_code = process.wait(timeout=10)
        exit_seconds: float | None = round(time.monotonic() - closed_at, 3)
    except subprocess.TimeoutExpired:
        exit_code, exit_seconds = None, None
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=10)
    stderr = drain(err, 2)
    listed = dig(tools, "result", "tools")
    names_listed = [dig(tool, "name") for tool in listed] if isinstance(listed, list) else []
    tool_names: list[Json] = [name for name in sorted(str(name) for name in names_listed)[:6]]
    http_lines: list[Json] = [line[:240] for line in stderr if "http fetch" in line]
    tail_lines: list[Json] = [line[:240] for line in stderr[-8:]]
    env_names: list[Json] = [name for name in sorted(env)]
    return {
        "spawned": True,
        "registry_reachable": reachable,
        "answered": first is not None and dig(first, "result", "serverInfo") is not None,
        "initialize_seconds": answered_at,
        "server_name": dig(first, "result", "serverInfo", "name"),
        "server_version": dig(first, "result", "serverInfo", "version"),
        "protocol": dig(first, "result", "protocolVersion"),
        "tools": len(names_listed),
        "tool_names": tool_names,
        "exit_code": exit_code,
        "exit_seconds_after_stdin_close": exit_seconds,
        "stderr_lines": len(stderr),
        "stderr_http": http_lines[:12],
        "stderr_tail": tail_lines,
        "env": env_names,
        "cwd": os.getcwd(),
    }


def proc_fields(pid: int) -> tuple[str, str, int] | None:
    """/proc/<pid>/stat 에서 (comm, 상태, 부모 번호). 없으면 None."""
    try:
        text = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    head, _, tail = text.rpartition(")")
    fields = tail.split()
    return head.partition("(")[2], fields[0], int(fields[1])


def cmdline(pid: int) -> str:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return ""
    return raw.replace(b"\0", b" ").decode("utf-8", errors="replace").strip()


def orphan() -> Json:
    """손자를 띄우고 자식을 바로 끝내 손자를 부모 잃은 프로세스로 만든다. 손자는 1초 뒤 끝난다.

    돌려주는 것은 손자의 부모가 누구로 바뀌었는지와, 손자가 끝난 뒤 좀비로 남았는지다.
    """
    reader, writer = os.pipe()
    child = os.fork()
    if child == 0:
        os.close(reader)
        grandchild = os.fork()
        if grandchild == 0:
            os.close(writer)
            time.sleep(1.0)
            os._exit(0)
        os.write(writer, str(grandchild).encode("ascii"))
        os._exit(0)
    os.close(writer)
    os.waitpid(child, 0)
    pid = int(os.read(reader, 32).decode("ascii"))
    os.close(reader)
    time.sleep(0.2)
    alive = proc_fields(pid)
    time.sleep(2.0)
    after = proc_fields(pid)
    return {
        "pid": pid,
        "parent_after_orphaned": alive[2] if alive is not None else None,
        "state_while_alive": alive[1] if alive is not None else None,
        "state_after_exit": after[1] if after is not None else "gone",
        "pid1": cmdline(1),
    }


def procs() -> Json:
    found: list[tuple[int, str, str, int]] = []
    for entry in Path("/proc").iterdir():
        fields = proc_fields(int(entry.name)) if entry.name.isdigit() else None
        if fields is not None:
            found.append((int(entry.name), *fields))
    found.sort()
    table: list[Json] = [
        {"pid": pid, "ppid": ppid, "comm": comm, "state": state} for pid, comm, state, ppid in found
    ]
    zombies: list[Json] = [
        {"pid": pid, "ppid": ppid, "comm": comm} for pid, comm, state, ppid in found if state == "Z"
    ]
    return {"pid1": cmdline(1), "count": len(found), "zombies": zombies, "table": table}


def timecmd(count: int, argv: list[str]) -> Json:
    codes: list[Json] = []
    millis: list[Json] = []
    for _ in range(count):
        started = time.monotonic()
        try:
            done = subprocess.run(argv, capture_output=True, timeout=20, check=False)
            codes.append(done.returncode)
        except subprocess.TimeoutExpired:
            codes.append("timeout")
        except OSError as error:
            codes.append(f"{type(error).__name__}: {error}")
        millis.append(round((time.monotonic() - started) * 1000, 1))
    return {"codes": codes, "ms": millis}


def whoami() -> Json:
    try:
        name: Json = getpass.getuser()
        failure: Json = None
    except Exception as error:  # 어떤 예외로 실패하는지가 재려는 것이다
        name, failure = None, f"{type(error).__name__}: {error}"
    home = os.environ.get("HOME", "")
    return {
        "uid": os.getuid(),
        "gid": os.getgid(),
        "getuser": name,
        "getuser_error": failure,
        "env": {key: os.environ.get(key) for key in ("USER", "LOGNAME", "HOME")},
        "home_writable": bool(home) and os.access(home, os.W_OK),
        "python": sys.version.split()[0],
    }


def tool_version(argv: list[str]) -> Json:
    try:
        done = subprocess.run(argv, capture_output=True, text=True, timeout=60, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"{type(error).__name__}: {error}"
    return (done.stdout + done.stderr).strip()[:200]


def first_line(text: str | None, head: str) -> Json:
    return next((line for line in (text or "").splitlines() if line.startswith(head)), None)


def pkginfo() -> Json:
    """agent-os 의 판이 보이는 자리 넷(명령, metadata, METADATA, dist-info 이름)과 도구 판."""
    dist = metadata.distribution("agent-os")
    folders: list[Json] = []
    for entry in sys.path:
        base = Path(entry)
        if base.is_dir():
            folders.extend(path.name for path in sorted(base.glob("agent_os-*.dist-info")))
    return {
        "cli": tool_version(["agent-os", "--version"]),
        "metadata": dist.version,
        "metadata_line": first_line(dist.read_text("METADATA"), "Version:"),
        "wheel_generator": first_line(dist.read_text("WHEEL"), "Generator:"),
        "dist_info": folders,
        "python": sys.version.split()[0],
        "node": tool_version(["node", "--version"]),
        "npm": tool_version(["npm", "--version"]),
    }


def lines(file: str, head: str) -> Json:
    try:
        text = Path(file).read_text(encoding="utf-8")
    except OSError as error:
        return {"error": f"{type(error).__name__}: {error}"}
    return {"lines": [line for line in text.splitlines() if line.startswith(head)]}


def writetest(folders: list[str]) -> Json:
    results: dict[str, Json] = {}
    for folder in folders:
        target = Path(folder) / f".probe-write-{os.getpid()}"
        try:
            target.write_text("x", encoding="utf-8")
        except OSError as error:
            results[folder] = errno.errorcode.get(error.errno or 0, type(error).__name__)
            continue
        target.unlink()
        results[folder] = "ok"
    return results


def tree(folder: str) -> Json:
    root = Path(folder)
    rows: list[Json] = []
    try:
        info = root.stat()
    except OSError as error:
        return {"error": f"{type(error).__name__}: {error}"}
    for path in sorted(root.rglob("*")):
        if "__pycache__" in path.parts:
            continue
        entry = path.lstat()
        kind = "dir" if stat.S_ISDIR(entry.st_mode) else "file"
        rows.append({"path": path.relative_to(root).as_posix(), "uid": entry.st_uid, "kind": kind})
    owners: set[int] = set()
    paths: list[Json] = []
    for row in rows:
        uid = row.get("uid") if isinstance(row, dict) else None
        if isinstance(uid, int):
            owners.add(uid)
        paths.append(row.get("path") if isinstance(row, dict) else None)
    owner_list: list[Json] = [uid for uid in sorted(owners)]
    return {
        "root_uid": info.st_uid,
        "root_mode": oct(stat.S_IMODE(info.st_mode)),
        "count": len(rows),
        "owners": owner_list,
        "paths": paths[:80],
    }


def setserver(file: str, command: str, args: str) -> Json:
    """stdio MCP 매니페스트의 `command = ` 줄과 `args = ` 줄을 바꿔 쓴다. args 는 JSON 배열이다."""
    path = Path(file)
    wanted = {"command = ": f"command = {json.dumps(command)}", "args = ": f"args = {args}"}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        return {"changed": False, "reason": f"{type(error).__name__}: {error}"}
    seen: list[str] = []
    for index, line in enumerate(lines):
        for head, replacement in wanted.items():
            if line.startswith(head):
                lines[index] = replacement
                seen.append(head)
    if sorted(seen) != sorted(wanted):
        return {"changed": False, "reason": f"command 와 args 줄을 하나씩 찾지 못했다: {seen}"}
    try:
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError as error:
        return {"changed": False, "reason": f"{type(error).__name__}: {error}"}
    return {"changed": True, "lines": [wanted["command = "], wanted["args = "]]}


def main(argv: list[str]) -> int:
    command, rest = argv[0], argv[1:]
    if command == "http":
        return emit(request_once(rest[0], rest[1], rest[2], rest[3]))
    if command == "openapi":
        return emit(openapi(rest[0]))
    if command == "pkginfo":
        return emit(pkginfo())
    if command == "lines":
        return emit(lines(rest[0], rest[1]))
    if command == "sse":
        return emit(stream(rest[0], rest[1], rest[2], float(rest[3])))
    if command == "handshake":
        return emit(handshake(float(rest[0]), rest[1], rest[2:]))
    if command == "orphan":
        return emit(orphan())
    if command == "procs":
        return emit(procs())
    if command == "timecmd":
        return emit(timecmd(int(rest[0]), rest[1:]))
    if command == "whoami":
        return emit(whoami())
    if command == "writetest":
        return emit(writetest(rest))
    if command == "tree":
        return emit(tree(rest[0]))
    if command == "setserver":
        return emit(setserver(rest[0], rest[1], rest[2]))
    if command == "netcheck":
        return emit({"registry_reachable": registry_reachable()})
    return emit({"error": f"모르는 명령: {command}"})


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
