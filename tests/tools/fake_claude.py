"""다시 풀기 회차 도구의 시험이 진짜 `claude` 대신 띄우는 가짜 실행 파일과 그 각본을 짓는 함수.

가짜는 `sys.executable`로 이 파일을 띄운다(`[sys.executable, FAKE]`가 러너가 명령 줄로 받는 `claude`
자리다). 표준 라이브러리만 쓰고 리눅스 CI에서도 돈다. 각본은 러너가 넘기는 `CLAUDE_CONFIG_DIR`
폴더의 `fake-claude.json`이다. 러너는 허용 목록으로 지은 환경만 넘겨 각본의 자리를 환경 변수로 줄 수
없고, 설정 폴더는 그 목록에 든다. 각본은 `write_script`로 쓴다.

부름마다 하는 일.
- `--version`: 각본의 `version`을 한 줄 낸다.
- `auth status --json`: 각본의 `auth`(로그인 상태와 계정)에 `configDirectory`(넘겨받은 설정 폴더의
  글 그대로)를 더한 JSON을 낸다. 로그아웃이면 `email` 없이 종료 1이다(명세 "계정"의 주석, 2.1.302의
  빈 설정 폴더에서 손으로 본 꼴).
- 세션(`-p`): 표준 입력을 다 읽고, 받은 인자·표준 입력·환경 변수의 이름·작업 폴더·자기 pid를 설정
  폴더의 `fake-calls.jsonl`에 한 줄로 덧붙인 뒤, 그 호출의 각본대로 한다. 각본은 세션
  id(`--session-id`나 `--resume`의 값)마다 줄 수 있고(`sessions`), 없으면 세션 부름의 차례대로
  고른다(`calls`). 같은 세션의 둘째 부름은 그 세션 각본의 둘째 것이다. 각본 하나는 stream-json
  줄(`events`. 사전이면 `session_id`가 없을 때 넣고, 글이면 그대로 낸다), 설정 폴더 아래의 세션 기록
  파일(`main`, `subagents`), 작업 폴더에서 칠 git 명령(`git`, 커밋을 남기는 각본), 이벤트를 내기
  전에 띄워 두는 자식의 초(`child`. 명령 줄에 세션 id를 싣고 pid를 `fake-children.jsonl`에 적는다),
  이벤트를 낸 뒤 표준 출력을 닫는지(`close_stdout`), 멈출 초(`hang`), 표준 출력을 쥐고 남는 손자의
  초(`linger`), 종료 코드(`exit`)다.

세션 기록 파일은 `<설정 폴더>/projects/<작업 폴더에서 지은 이름>/<세션 id>.jsonl`과
`<세션 id>/subagents/<이름>.jsonl`에 덧붙인다. 이름은 작업 폴더의 영문·숫자 밖의 글자를 `-`로 바꾼
것의 끝 `SLUG_MAX`자이고, 러너는 이 이름을 셈하지 않고 세션 id로 찾는다(명세 "러너가 기대는
`claude -p`의 동작"의 주석). 이름을 진짜와 같게 짓는지는 보지 않는다.

이벤트의 꼴은 커밋한 프로브 결과(`.scratch/model-rerun/probes/headless_flags/2026-10-22/`)에서
옮겼고, 그 결과에 없는 한도의 거절(`status: rejected`)과 `api_error`는
`tests/tools/test_canary.py`의 꼴을 따른다. `tests/tools/test_rerun_session.py`가 프로브 결과의
꼴은 그 파일들에서 읽어 견주고, 거절과 `api_error`는 `test_canary.py`에 그 글자가 있는지만 본다.
키는 실제의 일부만 낸다.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

FAKE = Path(__file__).resolve()
SCRIPT = "fake-claude.json"
CALLS = "fake-calls.jsonl"
CHILDREN = "fake-children.jsonl"
CONFIG_DIR_VAR = "CLAUDE_CONFIG_DIR"
GIT_TIMEOUT = 60
# 기록 폴더 이름의 길이. 시험의 임시 폴더는 길어(한글 시험 이름) 작업 폴더 전체로 지으면 윈도의 경로
# 상한(260자)을 넘겨 가짜가 기록을 쓰다 죽었다. 끝의 이만큼만 쓴다.
SLUG_MAX = 60

# 프로브가 init 에서 본 내장 플러그인 셋(`probes/README.md`).
BUILTIN_PLUGINS: tuple[str, ...] = (
    "cc-plugin-agents-md",
    "cc-plugin-telemetry",
    "cc-plugin-plugin-authoring",
)
# 프로브의 `모양` init 의 도구 목록(막는 규칙을 둔 세션이라 PowerShell 이 없다는 것은 실제 회차의
# 몫).
TOOLS: tuple[str, ...] = (
    "Task",
    "Bash",
    "Edit",
    "Glob",
    "Grep",
    "Read",
    "Skill",
    "Write",
)


def claude() -> list[str]:
    """러너에 `claude` 자리로 넘길 명령."""
    return [sys.executable, str(FAKE)]


def claude_direct() -> list[str]:
    """런처를 거치지 않고 띄우는 가짜. 윈도 venv 의 `python.exe`는 진짜 인터프리터를 자식으로 띄우는
    런처라 표준 출력을 함께 쥐어, 가짜가 출력을 닫아도(`close_stdout`) 가짜가 끝날 때까지 EOF 가
    오지 않는다(2026-10-23 이 PC 에서 손으로 봤다. 기본 인터프리터로 띄우면 EOF 가 0.03초 만에
    왔다). 가짜는 표준 라이브러리만 써서 기본 인터프리터로도 돈다. 리눅스의 `sys.executable`은
    런처가 아니다."""
    if sys.platform == "win32":
        return [str(Path(sys.base_prefix, "python.exe")), str(FAKE)]
    return [sys.executable, str(FAKE)]


# --- 각본의 이벤트 ---


def init_event(
    *,
    tools: Sequence[str] = TOOLS,
    plugins: Sequence[str] = BUILTIN_PLUGINS,
    mcp_servers: Sequence[str] = (),
    model: str = "claude-opus-5-5",
    version: str = "2.1.302",
) -> dict[str, Json]:
    return {
        "type": "system",
        "subtype": "init",
        "model": model,
        "permissionMode": "auto",
        "mcp_servers": [{"name": n, "status": "connected"} for n in mcp_servers],
        "plugins": [{"name": p, "path": "builtin", "source": f"{p}@builtin"} for p in plugins],
        "claude_code_version": version,
        "per_turn_effort_active": True,
        "tools": list(tools),
    }


def assistant_event(model: str, text: str, *, tool_input: Json = None) -> dict[str, Json]:
    content: list[Json] = [{"type": "text", "text": text}]
    if tool_input is not None:
        content.append({"type": "tool_use", "id": "toolu_1", "name": "Bash", "input": tool_input})
    return {
        "type": "assistant",
        "parent_tool_use_id": None,
        "message": {"model": model, "id": "msg_1", "role": "assistant", "content": content},
    }


def model_usage(
    model: str,
    *,
    cost: float,
    input_tokens: int = 10,
    output_tokens: int = 300,
    cache_read: int = 100_000,
    cache_write: int = 7_000,
    thinking: int = 0,
) -> dict[str, Json]:
    """결과 이벤트의 `modelUsage` 한 모델(`모양.summary.json`의 `model_usage` 꼴)."""
    return {
        model: {
            "inputTokens": input_tokens,
            "outputTokens": output_tokens,
            "cacheReadInputTokens": cache_read,
            "cacheCreationInputTokens": cache_write,
            "webSearchRequests": 0,
            "costUSD": cost,
            "contextWindow": 1_000_000,
            "maxOutputTokens": 128_000,
            "thinkingTokens": thinking,
            "canonicalModel": model,
            "provider": "firstParty",
            "costBasis": "list",
        }
    }


def result_event(
    cost: float,
    text: str | None,
    *,
    index: int = 0,
    subtype: str = "success",
    terminal_reason: str | None = "completed",
    num_turns: int = 1,
    usage: Mapping[str, Json] | None = None,
) -> dict[str, Json]:
    """결과 이벤트. `cost`는 그 세션의 누적 비용이다(`--resume`의 결과도 누적을 싣는다).
    `text`가 빈 값이면 `result` 키를 내지 않는다(`예산.summary.json`의 `error_max_budget_usd`)."""
    event: dict[str, Json] = {
        "type": "result",
        "subtype": subtype,
        "is_error": subtype != "success",
        "terminal_reason": terminal_reason,
        "num_turns": num_turns,
        "total_cost_usd": cost,
        "result_index": index,
        "stop_reason": "end_turn",
        "permission_denials": [],
        "modelUsage": dict(usage) if usage is not None else {},
    }
    if text is not None:
        event["result"] = text
    return event


def budget_result(cost: float, *, usage: Mapping[str, Json] | None = None) -> dict[str, Json]:
    """예산에 끊긴 결과(`예산.summary.json`)."""
    return result_event(
        cost,
        None,
        subtype="error_max_budget_usd",
        terminal_reason="budget_exhausted",
        usage=usage,
    )


def rate_limit_event(
    status: str = "allowed_warning",
    *,
    five_hour: float = 0.01,
    seven_day: float = 0.97,
    resets_at: int = 1792962000,
) -> dict[str, Json]:
    """한도 이벤트(`서브-2.jsonl`의 `allowed_warning`. 거절은 `tests/tools/test_canary.py`의 꼴)."""
    return {
        "type": "rate_limit_event",
        "rate_limit_info": {
            "status": status,
            "resetsAt": resets_at,
            "rateLimitType": "seven_day",
            "utilization": seven_day,
            "overageStatus": "rejected",
            "isUsingOverage": False,
            "unifiedWindows": {
                "five_hour": {"utilization": five_hour, "resetsAt": resets_at - 300_000},
                "seven_day": {"utilization": seven_day, "resetsAt": resets_at},
            },
        },
    }


def limit_result() -> dict[str, Json]:
    """계정 한도에 막힌 결과(`tests/tools/test_canary.py`의 `_한도_결과`)."""
    return {
        "type": "result",
        "subtype": "success",
        "is_error": True,
        "api_error_status": 429,
        "api_error": "usage_limit_reached",
        "result": "You've hit your weekly limit",
    }


# --- 세션 기록 파일의 줄 ---


def transcript_line(model: str, effort: str | None, message_id: str = "msg_1") -> dict[str, Json]:
    """세션 기록 파일의 assistant 줄. 맨 위 `effort`와 `message.model`이 프로브의
    `assistant_counts`가 읽은 꼴이다. 노력이 빈 값이면 `effort` 키를 내지 않는다."""
    line: dict[str, Json] = {
        "type": "assistant",
        "message": {"model": model, "id": message_id, "role": "assistant", "content": []},
    }
    if effort is not None:
        line["effort"] = effort
    return line


def synthetic_line() -> dict[str, Json]:
    """노력이 없는 `<synthetic>` 줄(프로브의 예산에 끊긴 세션을 이어 부른 기록에 있었다)."""
    return transcript_line("<synthetic>", None, "msg_synthetic")


# --- 각본 ---


def call(
    events: Sequence[Json],
    *,
    main: Sequence[Json] = (),
    subagents: Mapping[str, Sequence[Json]] | None = None,
    git: Sequence[Sequence[str]] = (),
    child: float = 0.0,
    close_stdout: bool = False,
    hang: float = 0.0,
    linger: float = 0.0,
    exit_code: int = 0,
) -> dict[str, Json]:
    """세션 부름 하나의 각본. `linger`는 가짜가 끝나기 전에 띄워 두는 손자가 표준 출력을 쥐고 자는
    초다(손자가 출력을 쥐어 EOF가 오지 않는 갈래). `child`는 이벤트를 내기 전에 띄우는 자식이 자는
    초다(러너가 프로세스 트리를 끄는지 보는 갈래). `close_stdout`이면 이벤트를 낸 뒤 표준 출력을
    닫고 `hang`만큼 멈춘다(출력을 닫고도 끝나지 않는 갈래)."""
    return {
        "events": list(events),
        "main": list(main),
        "subagents": {k: list(v) for k, v in (subagents or {}).items()},
        "git": [list(a) for a in git],
        "child": child,
        "close_stdout": close_stdout,
        "hang": hang,
        "linger": linger,
        "exit": exit_code,
    }


def write_script(
    config_dir: Path,
    *,
    calls: Sequence[Json] = (),
    sessions: Mapping[str, Sequence[Json]] | None = None,
    version: str = "2.1.302 (Claude Code)",
    logged_in: bool = True,
    email: str = "njh6803@example.com",
) -> None:
    """설정 폴더에 각본을 쓴다."""
    auth: dict[str, Json] = {"loggedIn": logged_in}
    if logged_in:
        auth["email"] = email
    script: dict[str, Json] = {
        "version": version,
        "auth": auth,
        "calls": list(calls),
        "sessions": {k: list(v) for k, v in (sessions or {}).items()},
    }
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / SCRIPT).write_text(json.dumps(script, ensure_ascii=False), encoding="utf-8")


def _read_jsonl(path: Path) -> list[dict[str, Json]]:
    if not path.exists():
        return []
    out: list[dict[str, Json]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value: Json = json.loads(line)
        if isinstance(value, dict):
            out.append(value)
    return out


def read_calls(config_dir: Path) -> list[dict[str, Json]]:
    """가짜가 받은 세션 부름들(받은 인자, 표준 입력, 환경 변수의 이름, 작업 폴더, 가짜의 pid)."""
    return _read_jsonl(config_dir / CALLS)


def read_children(config_dir: Path) -> list[dict[str, Json]]:
    """가짜가 띄운 자식들(세션 id와 자식의 pid)."""
    return _read_jsonl(config_dir / CHILDREN)


# --- 가짜의 몸 ---


def _obj(v: Json) -> dict[str, Json]:
    return v if isinstance(v, dict) else {}


def _list(v: Json) -> list[Json]:
    return v if isinstance(v, list) else []


def _flag(argv: Sequence[str], name: str) -> str | None:
    for i, a in enumerate(argv[:-1]):
        if a == name:
            return argv[i + 1]
    return None


def _out(text: str) -> None:
    sys.stdout.buffer.write(text.encode("utf-8"))
    sys.stdout.buffer.flush()


def _append(path: Path, lines: Sequence[Json]) -> None:
    if not lines:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as f:
        for line in lines:
            f.write(json.dumps(line, ensure_ascii=False) + "\n")


def _pick(script: dict[str, Json], config_dir: Path, session_id: str) -> dict[str, Json]:
    """이 부름의 각본. 이 부름은 이미 `fake-calls.jsonl`에 적혀 있다."""
    seen = read_calls(config_dir)
    sessions = _obj(script.get("sessions"))
    if session_id in sessions:
        nth = sum(1 for c in seen if c.get("session_id") == session_id) - 1
        mine = _list(sessions[session_id])
    else:
        nth = len(seen) - 1
        mine = _list(script.get("calls"))
    return _obj(mine[nth]) if 0 <= nth < len(mine) else {}


def _session(argv: list[str], config_dir: Path, script: dict[str, Json]) -> int:
    stdin = sys.stdin.buffer.read().decode("utf-8", errors="replace")
    session_id = _flag(argv, "--session-id") or _flag(argv, "--resume") or "모름"
    cwd = os.getcwd()
    entry: dict[str, Json] = {
        "argv": [a for a in argv],
        "stdin": stdin,
        "env": [n for n in sorted(os.environ)],
        "cwd": cwd,
        "session_id": session_id,
        "pid": os.getpid(),
    }
    _append(config_dir / CALLS, [entry])
    plan = _pick(script, config_dir, session_id)
    folder = config_dir / "projects" / re.sub(r"[^A-Za-z0-9]", "-", cwd)[-SLUG_MAX:]
    _append(folder / f"{session_id}.jsonl", _list(plan.get("main")))
    for name, lines in _obj(plan.get("subagents")).items():
        _append(folder / session_id / "subagents" / f"{name}.jsonl", _list(lines))
    for args in _list(plan.get("git")):
        command = [str(a) for a in _list(args)]
        subprocess.run(
            ["git", "-c", "user.name=fake", "-c", "user.email=fake@example.com", *command],
            cwd=cwd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=GIT_TIMEOUT,
        )
    child = plan.get("child")
    if isinstance(child, (int, float)) and child > 0:
        # 명령 줄에 세션 id 를 실어 시험이 그 pid 가 아직 이 자식인지 가른다. 출력은 쥐지 않는다
        spawned = subprocess.Popen(
            [sys.executable, "-c", f"import time; time.sleep({float(child)})", session_id],
            cwd=os.path.dirname(sys.executable),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _append(config_dir / CHILDREN, [{"session_id": session_id, "pid": spawned.pid}])
    for event in _list(plan.get("events")):
        if isinstance(event, str):
            _out(event if event.endswith("\n") else event + "\n")
            continue
        if isinstance(event, dict) and "session_id" not in event:
            event = {**event, "session_id": session_id}
        _out(json.dumps(event, ensure_ascii=False) + "\n")
    if plan.get("close_stdout") is True:
        os.close(sys.stdout.fileno())  # 파이썬의 표준 출력 객체는 그 서술자를 닫지 않는다
    hang = plan.get("hang")
    if isinstance(hang, (int, float)) and hang > 0:
        time.sleep(float(hang))
    linger = plan.get("linger")
    if isinstance(linger, (int, float)) and linger > 0:
        # 표준 출력을 물려받은 손자. 기다리지 않고 끝나 손자가 파이프를 쥔 채 남는다
        # 작업 폴더는 시험의 임시 폴더 밖이다. 남은 손자가 그 폴더를 쥐면 윈도에서 지우지 못한다
        subprocess.Popen(
            [sys.executable, "-c", f"import time; time.sleep({float(linger)})"],
            cwd=os.path.dirname(sys.executable),
        )
    code = plan.get("exit")
    return code if isinstance(code, int) else 0


def main(argv: list[str]) -> int:
    config_dir = Path(os.environ[CONFIG_DIR_VAR])
    script = _obj(json.loads((config_dir / SCRIPT).read_text(encoding="utf-8")))
    if argv[:1] == ["--version"]:
        _out(f"{script.get('version')}\n")
        return 0
    if argv[:2] == ["auth", "status"]:
        auth = {**_obj(script.get("auth")), "configDirectory": os.environ[CONFIG_DIR_VAR]}
        _out(json.dumps(auth, ensure_ascii=False) + "\n")
        return 0 if auth.get("loggedIn") is True else 1
    return _session(argv, config_dir, script)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
