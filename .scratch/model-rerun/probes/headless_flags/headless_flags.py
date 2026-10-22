"""다시 풀기 러너가 기대는 `claude -p` 의 동작을 잰다.

명세(`.scratch/model-rerun/spec.md`)가 근거로 든다. 설계(`.scratch/model-rerun/design.md`)가
파일럿으로 미룬 확인 가운데 결과에 따라 러너의 모양이 달라지는 것을 명세 단계에서 먼저 본다. 전용
설정 폴더의 로그인이 없어도 되는 것만 잰다. 이 프로브는 기본 설정 폴더(지금 `claude` 가 로그인한
계정)로 돌고, 사용자 설정은 `--setting-sources project,local` 로 뺀다.

갈래 일곱. 모두 임시 git 저장소(`repo/`, 원격은 같은 임시 폴더의 bare 저장소)에서
`--model claude-sonnet-5-5 --effort low --permission-mode auto --strict-mcp-config` 와 stream-json
으로 돈다. 환경은 물려받은 것이 아니라 허용 목록(`ALLOWED_ENV`)으로 짓는다.
- `모양`: Bash 로 환경 변수 이름만 찍고, Read 로 파일 셋을 하나씩 읽고, 세 표지 낱말을 이어 답한다.
  init·assistant·result 이벤트의 칸, 결과의 `total_cost_usd`·`modelUsage`, 이벤트와 세션 기록
  파일(`~/.claude/projects/*/<세션 id>.jsonl`)에 노력이 실리는 자리를 본다. 같은 저장소에서 그
  세션을 `--resume` 으로 한 번 더 부른다(원본 이름 `이어가기`). 세션 기록이 작업 폴더마다 묶여
  저장소를 지운 뒤에는 찾지 못할 수 있어서다. 그 결과의 `total_cost_usd` 가 그 호출의 몫인지 세션
  누적인지 가른다. 누적이면 `모양` 의 값보다 크거나 같고, 호출의 몫이면 도구 없는 한 줄 답이라 훨씬
  작다.
- `예산`: `모양` 과 같은 질문에 `--max-budget-usd 0.01`. 첫 응답 하나가 그 값을 넘으므로(캐시 쓰기만
  수만 토큰) 플래그가 멈추면 읽기 셋을 마치지 못한다. `모양` 이 양성 대조다. 같은 저장소에서 그
  세션을 같은 예산으로 `--resume` 해 도구 없는 한 줄 답을 시킨다(원본 이름 `예산이어가기`). 그
  호출의 몫은 `이어가기` 처럼 예산보다 훨씬 작으므로, 그래도 예산으로 멈추면 플래그가 세션 누적을
  본다는 것이다.
- `누적`: `예산이어가기` 는 도구 없는 한 줄 답이라, 예산을 응답마다 재는데 다음 응답이 없어 멈출
  자리가 없었다는 해석과 가르지 못한다. 그래서 도구 없는 한 낱말 답으로 새 세션을 열고(약
  0.027달러), 같은 저장소에서 `--max-budget-usd 0.02` 로 `--resume` 해 `모양` 의 질문(도구 호출
  넷)을 시킨다(원본 이름 `누적이어가기`). 예산은 응답이 끝난 뒤에 재고 넘긴 응답의 도구 호출은
  돌지 않는다(`예산`). 그래서 세션 누적을 보면 첫 응답 뒤에 멈춰 그 응답이 낸 도구 호출이 돌지 않고,
  그 호출의 몫을 보면 응답 하나가 약 0.009달러라 첫 응답의 도구 호출이 돌고 다음 응답이 나온다.
- `거부`: 저장소의 `.claude/settings.local.json` 에 막는 규칙(`DENY` 와 저장소 밖 경로의 Read
  규칙)을 두고 행동 여섯(`ACTIONS`)을 하나씩 시킨다. `gh`, `git push`, 가운데 와일드카드의 Bash
  규칙(`open_session.ps1`), 저장소 밖 절대 경로의 Read, Skill, WebFetch 도메인이다.
- `거부대조`: 같은 모양의 저장소에 규칙 없이 같은 행동. auto 모드의 분류기가 스스로 막는 것과 규칙이
  막는 것을 가른다.
- `질문`: `AskUserQuestion` 을 부르게 하고 그 도구 결과를 옮기게 한다.
- `서브`: Task 도구로 `model: haiku` 인 서브에이전트를 띄워 `a.txt` 를 읽게 한다. 서브에이전트의
  응답이 stream-json(`parent_tool_use_id` 가 붙은 assistant 이벤트)과 세션 기록의 어느 파일에 어느
  모델로 실리는지 본다. 본 세션(sonnet)과 다른 모델을 주어 두 기록을 가른다.

판정은 하지 않고 본 것을 찍는다. 호출마다 회차 하나이고, 그 회차에 재려던 상황이 났다는 표지를
본다(`.claude/rules/probes.md` 첫 항목, `missing_marker`). 회차 셈은 `tools/probe_kit.py` 의
`Rounds` 가, `claude` 출력 읽기는 같은 파일의 `LineReader` 가 한다. 2026-10-22 의 실행(커밋한
요약)은 그 둘을 이 파일 안에 직접 짠 판으로 돌았다. 옮긴 판은 `claude` 를 다시 띄우지 않았고,
`--judge` 와 손으로 돌린 가짜 시험(세션 스크래치의 가짜 자식 프로세스로 읽기, 가짜 `drive` 로 회차
셈, 커밋하지 않았다)으로만 봤다. 모든 갈래에 init 과 result 이벤트가 있어야
하고, 계정 한도에 막힌 회차(`rate_limit_event` 의 `status: rejected`, 결과 `api_error` 의
`usage_limit_reached`. `tools/canary.py` 와 같은 표지)는 측정이 아니다. 그 위에 갈래마다 하나다.
`모양` 은 Bash 하나와 Read 셋을 불렀는지, `예산` 은 쓴 비용이 예산을 넘었는지, `누적` 은 세션 누적이
이어 부를 예산을 넘었는지, 이어 부른 셋은 앞 갈래의 세션을 이었는지와(예산을 준 것은) 이어 부르기
전의 누적이 그 예산을 넘었는지, `거부`·`거부대조` 는 행동 여섯을 모두 시도했는지(`tool_use`, 부르지
않은 행동은 `시도 없음` 으로 찍는다), `질문` 은 `AskUserQuestion` 을 부르거나 `ToolSearch` 로
찾았는지, `서브` 는 서브에이전트 도구를 부르고 그 응답이 stream 이나 세션 기록에 있는지다. 막힘은
결과의 `permission_denials` 와 그 호출의 도구 결과(`is_error`, 글)로, 실행은 도구 결과와 파일
표지(`opened.txt`)로 본다.

못 보는 것: 전용 `CLAUDE_CONFIG_DIR` 의 격리(로그인이 든다), 구독 계정마다 다를 수 있는 동작,
데스크톱 앱. 한 갈래 한 회차다. 막는 규칙은 고른 모양만 재고, 같은 규칙을 다른 꼴의 명령으로 비켜
가는 길(따옴표, 다른 셸, PowerShell 도구)은 재지 않는다. `질문` 은 그 도구가 세션에 있는지를 init
의 `tools` 로 본다. 그 목록에는 스키마를 늦게 싣는 도구도 든다(`WebFetch` 가 목록에 있으면서
`ToolSearch` 로 실린 것이 `거부` 원본에 있다).

돌리는 법은 워크트리 루트에서 아래 한 줄이다.

    uv run python .scratch/model-rerun/probes/headless_flags/headless_flags.py <출력> [--arm <갈래>]

출력 디렉터리는 저장소 밖(세션 스크래치패드)에 둔다. 원본에 세션 셸의 환경 변수 이름이 실린다.
`--arm` 을 주면 그 갈래만 돈다. 갈래마다 `<갈래>.jsonl`(원본), `<갈래>.times`(줄마다 받은 시각,
시작부터의 초), `<갈래>.summary.json` 을 남기고 임시 폴더는 끝에 지운다. `claude` CLI 와 인증이
들고, 갈래마다 sonnet 세션 하나다(`모양`·`예산`·`누적` 은 호출 둘). 끝에 회차 셈을 찍는다. 종료
코드: 0 회차가 모두 측정이다, 1 측정이 아닌 회차가 있다(예외로 끝난 호출과 앞 호출이 끝나지 않아
돌지 않은 이어 부르기도 측정이 아니다), 2 임시 폴더의 상위에 `.claude/` 가 있다.

저장한 요약만 읽는 길이 둘이다. `claude` 를 띄우지 않는다.

    uv run python .scratch/model-rerun/probes/headless_flags/headless_flags.py --judge <디렉터리>
    uv run python .scratch/model-rerun/probes/headless_flags/headless_flags.py --prices <디렉터리>

`--judge` 는 요약마다 위 표지를 다시 판정해 회차 셈을 찍고, 모두 측정이면 0, 아니면(요약이 없어도)
1로 끝난다. `--prices` 는
요약의 `modelUsage` 마다 토큰을 공식 단가(`PRICES`)로 셈해 `costUSD` 와 견주고, 캐시 쓰기를 5분
수명(입력의 1.25배)과 1시간 수명(2배) 가운데 어느 배수로 셈해야 맞는지 찍는다. 맞는 배수가 없는
모델이 있으면 1로 끝난다. `modelUsage` 는 캐시 쓰기를 수명으로 나누지 않으므로, 한 모델의 쓰기가
두 수명에 걸쳤으면 어느 배수와도 맞지 않는다.
"""

import argparse
import json
import math
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import uuid
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import LineReader, Rounds, Slot  # noqa: E402

ARMS = ("모양", "예산", "누적", "거부", "거부대조", "질문", "서브")
MARKS = {"a.txt": "노을고래", "b.txt": "새벽수달", "c.txt": "은빛참새"}
OUTSIDE_MARK = "겨울솔개"
SKILL_MARK = "가을사슴"
TIMEOUT = 600
BUDGET = "0.01"
# `누적` 이 이어 부를 때의 예산. 새 세션의 첫 응답(약 0.027달러)보다 작고, 이어 부른 호출의 응답
# 하나(약 0.009달러, `이어가기`)보다 크다.
RESUME_BUDGET = "0.02"
# 허용 목록. 설계 5절 환경 변수 문단의 목록에 윈도의 기본값을 더했다. 값은 기록에 남기지 않는다.
ALLOWED_ENV = (
    "PATH",
    "PATHEXT",
    "SYSTEMROOT",
    "SystemDrive",
    "WINDIR",
    "COMSPEC",
    "USERPROFILE",
    "HOME",
    "HOMEDRIVE",
    "HOMEPATH",
    "APPDATA",
    "LOCALAPPDATA",
    "PROGRAMDATA",
    "ProgramFiles",
    "ProgramFiles(x86)",
    "TEMP",
    "TMP",
)
BASE_COMMAND = [
    "-p",
    "--model",
    "claude-sonnet-5-5",
    "--effort",
    "low",
    "--permission-mode",
    "auto",
    "--setting-sources",
    "project,local",
    "--strict-mcp-config",
    "--output-format",
    "stream-json",
    "--verbose",
]
READ_QUESTION = (
    "다음을 차례로 한다. 1) Bash 도구로 `env | cut -d= -f1 | sort | tr '\\n' ' '` 를 한 번 "
    "친다(값은 찍지 않는다). 2) Read 도구로 a.txt, b.txt, c.txt 를 한 번에 하나씩 차례로 "
    "읽는다. 3) 세 파일에 든 낱말을 a, b, c 차례로 공백 하나로 이어 한 줄로 답한다. 다른 일은 "
    "하지 마라."
)
RESUME_QUESTION = "방금 답한 한 줄을 그대로 다시 적어라. 도구는 쓰지 마라."
NO_TOOL_QUESTION = "'좋다' 한 낱말로만 답해라. 도구는 쓰지 마라."
SUBAGENT_QUESTION = (
    "Task 도구로 general-purpose 에이전트를 한 번 띄워라. 그 도구의 model 인자는 haiku 로 주고, "
    "에이전트에게는 Read 도구로 a.txt 를 읽어 든 낱말 하나만 답하라고 시킨다. 에이전트가 돌려준 "
    "낱말을 그대로 한 줄로 답하라. 너는 다른 도구를 쓰지 마라."
)
ASK_QUESTION = (
    "AskUserQuestion 도구를 한 번 불러 '사과와 배 가운데 무엇이 좋은가?'를 선택지 둘(사과, 배)로 "
    "물어라. 그 도구의 결과를 받으면 받은 결과의 글을 그대로 옮겨 적어라. 다른 도구는 쓰지 마라."
)
DENY = [
    "Bash(gh:*)",
    "Bash(git push:*)",
    "Bash(*open_session.ps1*)",
    "Skill(probe-open)",
    "WebFetch(domain:github.com)",
]
# (이름, 도구, 입력에 들어야 할 글) 행동마다 한 줄.
ACTIONS = (
    ("gh", "Bash", "gh --version"),
    ("push", "Bash", "git push"),
    ("open_session", "Bash", "open_session.ps1"),
    ("read_outside", "Read", "secret.txt"),
    ("skill", "Skill", "probe-open"),
    ("webfetch", "WebFetch", "github.com"),
)

# 이어 부른 갈래와 그 세션을 연 갈래.
FIRST_OF = {"이어가기": "모양", "예산이어가기": "예산", "누적이어가기": "누적"}
# 입력, 출력, 캐시 읽기($/MTok). `docs/model-selection.md` 2절의 공식 단가. Haiku 는 프롬프트 10만
# 토큰 이하의 값이고, 이 프로브의 프롬프트는 그보다 작다.
PRICES = {
    "claude-opus-5-5": (4.0, 20.0, 0.20),
    "claude-sonnet-5-5": (2.0, 10.0, 0.10),
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
}
# 캐시 쓰기의 배수(입력 단가에 곱한다). 캐시 수명마다 다르다.
WRITE_RATES = {"5분": 1.25, "1시간": 2.0}

type Summary = dict[str, object]
type Drove = tuple[list[str], list[float], int | None]


def deny_question(outside: Path) -> str:
    return (
        "아래 여섯을 하나씩, 한 번에 도구 호출 하나로 차례로 시도한다. 막히거나 실패해도 다음으로 "
        "넘어간다. 1) Bash 도구로 `gh --version`. 2) Bash 도구로 `git push origin main`. "
        "3) Bash 도구로 `pwsh -NoProfile -File tools/open_session.ps1`. "
        f"4) Read 도구로 `{outside.as_posix()}`. 5) Skill 도구로 `probe-open`. "
        "6) WebFetch 도구로 `https://github.com/` 를 받아 제목만 묻는다. 끝나면 여섯마다 "
        "한 줄로 무엇이 돌아왔는지(오류면 그 문구) 적는다."
    )


def allowed_env() -> dict[str, str]:
    env = {key: os.environ[key] for key in ALLOWED_ENV if key in os.environ}
    env["DISABLE_AUTOUPDATER"] = "1"
    return env


def git(*args: str, cwd: Path) -> None:
    clean = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    done = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False, env=clean, timeout=60
    )
    if done.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 실패({done.returncode}): {done.stderr.strip()}")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def outside_rule(root: Path) -> str:
    """저장소 밖 폴더의 Read 규칙. 윈도 경로는 `//c/…` 꼴로 쓴다(권한 규칙 문서의 절대 경로)."""
    drive, rest = root.resolve().as_posix().split(":", 1)
    return f"Read(//{drive.lower()}{rest}/outside/**)"


def layout(root: Path, *, rules: bool) -> Path:
    """임시 저장소를 짓는다. 원격은 bare 저장소이고, 저장소 밖에 읽기 대상 파일을 둔다."""
    bare = root / "origin.git"
    git("init", "-q", "--bare", "-b", "main", str(bare), cwd=root)
    repo = root / "repo"
    repo.mkdir()
    git("init", "-q", "-b", "main", cwd=repo)
    for name, mark in MARKS.items():
        write(repo / name, f"{mark}\n")
    write(repo / "README.md", "프로브 저장소\n")
    write(
        repo / ".claude" / "skills" / "probe-open" / "SKILL.md",
        "---\nname: probe-open\ndescription: 프로브용 스킬. 부르라고 하면 부른다.\n---\n\n"
        f"이 스킬의 표지 낱말은 {SKILL_MARK}다.\n",
    )
    write(
        repo / "tools" / "open_session.ps1",
        "Set-Content -Path (Join-Path $PSScriptRoot '..' 'opened.txt') -Value 'opened'\n",
    )
    git("add", ".", cwd=repo)
    git("-c", "user.name=p", "-c", "user.email=p@invalid", "commit", "-qm", "init", cwd=repo)
    git("remote", "add", "origin", str(bare), cwd=repo)
    git("push", "-q", "origin", "main", cwd=repo)
    write(root / "outside" / "secret.txt", f"{OUTSIDE_MARK}\n")
    if rules:
        settings = {"permissions": {"deny": [*DENY, outside_rule(root)]}}
        write(
            repo / ".claude" / "settings.local.json",
            json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
        )
    return repo


def remove_tree(root: Path) -> None:
    """mkdtemp 로 만든 이 프로브의 임시 폴더만 지운다. 읽기 전용 파일은 쓰기를 풀고 다시 지운다."""

    def writable_retry(function: Callable[[str], object], path: str, _error: BaseException) -> None:
        os.chmod(path, stat.S_IWRITE)
        function(path)

    shutil.rmtree(root, onexc=writable_retry)


def ancestors_with_claude_dir(path: Path) -> list[Path]:
    return [
        parent / ".claude"
        for parent in path.parents
        if parent != Path.home() and (parent / ".claude").is_dir()
    ]


def event_of(line: str) -> dict[str, object] | None:
    if not line.lstrip().startswith("{"):
        return None
    try:
        event = json.loads(line)
    except ValueError:  # 제한 시간에 끊기면 마지막 줄이 잘린다
        return None
    return event if isinstance(event, dict) else None


def drive(args: list[str], cwd: Path, question: str) -> Drove:
    """`claude` 하나를 띄워 질문을 stdin 으로 넣고 끝까지 읽는다. 줄과 받은 시각, 종료 코드.
    출력은 `tools/probe_kit.py` 의 `LineReader` 로 읽는다(`.claude/rules/probes.md` 의 읽기
    항목)."""
    executable = shutil.which("claude") or "claude"
    started = time.monotonic()
    process = subprocess.Popen(
        [executable, *args],
        cwd=cwd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=allowed_env(),
    )
    stdin, stdout = process.stdin, process.stdout
    assert stdin is not None and stdout is not None
    reader = LineReader(stdout)
    try:
        stdin.write(question.encode("utf-8"))
        stdin.close()
    except OSError:  # 질문을 받기 전에 끝난 claude 는 파이프를 닫는다
        pass
    lines: list[str] = []
    times: list[float] = []
    deadline = started + TIMEOUT
    while not reader.ended and (left := deadline - time.monotonic()) > 0:
        line = reader.readline(min(left, 5))
        if line is not None:
            lines.append(line)
            times.append(round(time.monotonic() - started, 2))
    try:
        code = process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        process.kill()  # Popen 이 쥔 핸들이라 pid 재사용과 섞이지 않는다
        process.wait(timeout=60)
        code = None
    # 손자가 stdout 을 쥐고 남으면 EOF 가 오지 않으므로 배출에도 제한 시간을 둔다.
    for line in reader.drain(10):
        lines.append(line)
        times.append(round(time.monotonic() - started, 2))
    return lines, times, code


def keys_with(value: object, name: str, path: str = "") -> list[str]:
    """값 안에서 키 `name` 이 나오는 자리(점으로 이은 경로)를 모두 찾는다."""
    found: list[str] = []
    if isinstance(value, dict):
        for key, inner in value.items():
            here = f"{path}.{key}" if path else str(key)
            if key == name:
                found.append(here)
            found.extend(keys_with(inner, name, here))
    elif isinstance(value, list):
        for index, inner in enumerate(value):
            found.extend(keys_with(inner, name, f"{path}[{index}]"))
    return found


def text_of(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [part.get("text", "") for part in content if isinstance(part, dict)]
        return "".join(str(part) for part in parts)
    return ""


def pick(event: dict[str, object] | None, keys: tuple[str, ...]) -> dict[str, object] | None:
    return {key: event.get(key) for key in keys} if event else None


def summarize(lines: list[str], code: int | None) -> Summary:
    events = [event for line in lines if (event := event_of(line)) is not None]
    init = next(
        (e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), None
    )
    results = [e for e in events if e.get("type") == "result"]
    result = results[-1] if results else None
    rejected = any(
        e.get("type") == "rate_limit_event"
        and isinstance(info := e.get("rate_limit_info"), dict)
        and info.get("status") == "rejected"
        for e in events
    )
    limited = rejected or (result is not None and result.get("api_error") == "usage_limit_reached")
    tool_uses: list[dict[str, object]] = []
    tool_results: dict[str, dict[str, object]] = {}
    models: dict[str, int] = {}
    nested_models: dict[str, int] = {}
    for event in events:
        message = event.get("message")
        if not isinstance(message, dict):
            continue
        if event.get("type") == "assistant":
            model = str(message.get("model"))
            models[model] = models.get(model, 0) + 1
            if event.get("parent_tool_use_id"):
                nested_models[model] = nested_models.get(model, 0) + 1
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "tool_use":
                tool_uses.append(
                    {"id": part.get("id"), "name": part.get("name"), "input": part.get("input")}
                )
            elif part.get("type") == "tool_result":
                tool_results[str(part.get("tool_use_id"))] = {
                    "is_error": part.get("is_error"),
                    "text": text_of(part.get("content"))[:400],
                }
    init_keys = (
        "model",
        "permissionMode",
        "mcp_servers",
        "plugins",
        "claude_code_version",
        "per_turn_effort_active",
        "tools",
    )
    infos = [
        info
        for e in events
        if e.get("type") == "rate_limit_event"
        and isinstance(info := e.get("rate_limit_info"), dict)
    ]
    rate_keys = ("status", "rateLimitType", "utilization", "unifiedWindows")
    result_keys = (
        "subtype",
        "is_error",
        "terminal_reason",
        "num_turns",
        "total_cost_usd",
        "session_id",
        "permission_denials",
        "result",
    )
    return {
        "exit": code,
        "lines": len(lines),
        "event_types": sorted({str(e.get("type")) for e in events}),
        "limited": limited,
        "rate_limit": pick(infos[-1], rate_keys) if infos else None,
        "init_keys": sorted(init) if init else None,
        "init": pick(init, init_keys),
        "assistant_models": models,
        "nested_assistant_models": nested_models,
        "effort_keys_in_events": sorted({p for e in events for p in keys_with(e, "effort")}),
        "result_keys": sorted(result) if result else None,
        "result": pick(result, result_keys),
        # 한 호출에 결과 이벤트가 여럿일 수 있다(백그라운드 서브에이전트의 알림이 본 세션을 다시
        # 깨운다).
        "results": [pick(r, (*result_keys, "result_index", "stop_reason")) for r in results],
        "init_count": sum(
            1 for e in events if e.get("type") == "system" and e.get("subtype") == "init"
        ),
        "model_usage": result.get("modelUsage") if result else None,
        "tool_uses": [{**use, "result": tool_results.get(str(use.get("id")))} for use in tool_uses],
    }


def assistant_counts(files: list[Path]) -> tuple[dict[str, int], dict[str, int]]:
    """기록 파일들의 assistant 줄에서 `effort` 와 `message.model` 을 센다."""
    efforts: dict[str, int] = {}
    models: dict[str, int] = {}
    for file in files:
        for line in file.read_text(encoding="utf-8", errors="replace").splitlines():
            record = event_of(line)
            if record is None or record.get("type") != "assistant":
                continue
            effort = str(record.get("effort"))
            efforts[effort] = efforts.get(effort, 0) + 1
            message = record.get("message")
            if isinstance(message, dict):
                model = str(message.get("model"))
                models[model] = models.get(model, 0) + 1
    return efforts, models


def transcript_effort(session_id: str) -> dict[str, object]:
    """세션 기록 파일(`<세션 id>.jsonl`)과, 같은 이름의 폴더 아래 기록(서브에이전트 등)을 센다."""
    root = Path.home() / ".claude" / "projects"
    files = list(root.glob(f"*/{session_id}.jsonl"))
    efforts, models = assistant_counts(files)
    side = sorted(p for d in root.glob(f"*/{session_id}") if d.is_dir() for p in d.rglob("*.jsonl"))
    nested: dict[str, object] = {}
    for path in side:
        side_efforts, side_models = assistant_counts([path])
        nested[path.relative_to(root).as_posix()] = {"effort": side_efforts, "model": side_models}
    names = [f"{file.parent.name}/{file.name}" for file in files]
    return {"files": names, "effort": efforts, "model": models, "nested": nested}


def denied_ids(result: object) -> set[str]:
    denials = result.get("permission_denials") if isinstance(result, dict) else None
    if not isinstance(denials, list):
        return set()
    return {str(d.get("tool_use_id")) for d in denials if isinstance(d, dict)}


def action_outcomes(summary: Summary, repo: Path) -> dict[str, str]:
    uses = summary.get("tool_uses")
    result = summary.get("result")
    denied = denied_ids(result)
    outcomes: dict[str, str] = {}
    for name, tool, needle in ACTIONS:
        use = None
        for candidate in uses if isinstance(uses, list) else []:
            if not isinstance(candidate, dict) or candidate.get("name") != tool:
                continue
            if needle in json.dumps(candidate.get("input"), ensure_ascii=False):
                use = candidate
                break
        if use is None:
            outcomes[name] = "시도 없음"
            continue
        got = use.get("result")
        text = got.get("text") if isinstance(got, dict) else None
        error = got.get("is_error") if isinstance(got, dict) else None
        mark = "거부 목록에 있음" if str(use.get("id")) in denied else "거부 목록에 없음"
        outcomes[name] = f"{mark}, is_error={error}, 결과={text!r}"
    outcomes["opened.txt"] = "있음" if (repo / "opened.txt").exists() else "없음"
    answer = str(result.get("result")) if isinstance(result, dict) else ""
    outcomes["outside_mark_in_answer"] = str(OUTSIDE_MARK in answer)
    return outcomes


def record(arm: str, out: Path, args: list[str], drove: Drove) -> Summary:
    lines, times, code = drove
    (out / f"{arm}.jsonl").write_text("".join(lines), encoding="utf-8")
    (out / f"{arm}.times").write_text("\n".join(map(str, times)) + "\n", encoding="utf-8")
    summary = summarize(lines, code)
    summary["arm"] = arm
    summary["args"] = args
    summary["env_names"] = sorted(allowed_env())
    return summary


def number(value: object) -> float:
    return float(value) if isinstance(value, int | float) else 0.0


def result_of(summary: Summary) -> dict[str, object]:
    result = summary.get("result")
    return result if isinstance(result, dict) else {}


def flag_value(summary: Summary, flag: str) -> str | None:
    """요약의 `args` 에서 플래그 뒤의 값."""
    args = summary.get("args")
    if not isinstance(args, list) or flag not in args:
        return None
    index = args.index(flag)
    return str(args[index + 1]) if index + 1 < len(args) else None


def tool_uses_of(summary: Summary) -> list[dict[str, object]]:
    uses = summary.get("tool_uses")
    return [use for use in uses if isinstance(use, dict)] if isinstance(uses, list) else []


def missing_marker(arm: str, summary: Summary, first: Summary | None) -> str | None:
    """재려던 상황이 그 회차에 났다는 표지가 없으면 그 까닭, 있으면 None.

    표지는 결과(멈췄는지, 막혔는지)가 아니라 결과를 가를 상황이다. `예산` 은 쓴 비용이 예산을
    넘었는지를 보고, 넘었는데도 멈추지 않았다면 그것도 측정이다. 이어 부른 갈래는 앞 갈래의 세션을
    이었는지와, 예산을 준 것이면 이어 부르기 전의 세션 누적이 그 예산을 넘었는지를 본다.
    """
    if not summary.get("init") or not summary.get("result"):
        return "init 이나 result 이벤트가 없다"
    if summary.get("limited"):
        return "계정 한도에 막혔다"
    uses = tool_uses_of(summary)
    names = [str(use.get("name")) for use in uses]
    budget = flag_value(summary, "--max-budget-usd")
    if arm == "모양" and (names.count("Read") < 3 or "Bash" not in names):
        return "Bash 하나와 Read 셋을 부르지 않았다"
    if arm in FIRST_OF:
        if first is None:
            return f"앞 갈래 {FIRST_OF[arm]} 의 요약이 없다"
        if flag_value(summary, "--resume") != result_of(first).get("session_id"):
            return "앞 갈래의 세션을 이어 부르지 않았다"
        if budget is not None and number(result_of(first).get("total_cost_usd")) <= float(budget):
            return "이어 부르기 전의 세션 누적이 예산을 넘지 않았다"
    if arm == "예산" and (
        budget is None or number(result_of(summary).get("total_cost_usd")) <= float(budget)
    ):
        return "쓴 비용이 예산을 넘지 않았다"
    if arm == "누적" and number(result_of(summary).get("total_cost_usd")) <= float(RESUME_BUDGET):
        return "세션 누적이 이어 부를 예산을 넘지 않았다"
    if arm in ("거부", "거부대조"):
        actions = summary.get("actions")
        if not isinstance(actions, dict) or any(
            actions.get(name) == "시도 없음" for name, _tool, _needle in ACTIONS
        ):
            return "시도하지 않은 행동이 있다"
    if arm == "질문" and not any(
        use.get("name") == "AskUserQuestion"
        or (
            use.get("name") == "ToolSearch"
            and "AskUserQuestion" in json.dumps(use.get("input"), ensure_ascii=False)
        )
        for use in uses
    ):
        return "AskUserQuestion 을 부르거나 찾지 않았다"
    if arm == "서브":
        if not {"Agent", "Task"} & set(names):
            return "서브에이전트 도구를 부르지 않았다"
        transcript = summary.get("transcript")
        nested = transcript.get("nested") if isinstance(transcript, dict) else None
        if not summary.get("nested_assistant_models") and not nested:
            return "서브에이전트의 응답이 stream 과 세션 기록 어디에도 없다"
    return None


def save(arm: str, out: Path, summary: Summary) -> None:
    (out / f"{arm}.summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"{arm} 종료 {summary['exit']}, 줄 {summary['lines']}")


def mark(current: Slot, arm: str, summary: Summary, first: Summary | None) -> None:
    """요약 하나를 갈래의 표지로 판정해 그 회차에 적는다. 측정이 아니면 그 까닭이 결과다."""
    reason = missing_marker(arm, summary, first)
    print(f"[{'측정' if reason is None else f'측정 아님: {reason}'}] {current.label}")
    current.mark(measured=reason is None, result="표지 있음" if reason is None else reason)


def load_summaries(directory: Path) -> dict[str, Summary]:
    """`<이름>.summary.json` 을 이름으로. 같은 갈래를 더 돈 것은 `<갈래>-<n>` 이름이다."""
    found: dict[str, Summary] = {}
    for path in sorted(directory.glob("*.summary.json")):
        loaded = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(loaded, dict):
            found[path.name.removesuffix(".summary.json")] = loaded
    return found


def judge(directory: Path) -> int:
    """저장한 요약을 갈래마다의 표지로 다시 판정한다. 모두 측정이면 0, 아니면 1(요약이 없어도 1)."""
    summaries = load_summaries(directory)
    rounds = Rounds()
    for name, summary in summaries.items():
        arm = str(summary.get("arm"))
        first_name = FIRST_OF.get(arm)
        first = summaries.get(first_name) if first_name else None
        with rounds.round(name) as current:
            mark(current, arm, summary, first)
    print(rounds.summary())
    return rounds.exit_code()


def official_cost(
    usage: dict[str, object], price: tuple[float, float, float], rate: float
) -> float:
    """`modelUsage` 한 모델의 토큰을 공식 단가로 셈한다. 캐시 쓰기는 입력 단가에 `rate` 를
    곱한다."""
    unit_in, unit_out, unit_read = price
    return (
        number(usage.get("inputTokens")) * unit_in
        + number(usage.get("outputTokens")) * unit_out
        + number(usage.get("cacheReadInputTokens")) * unit_read
        + number(usage.get("cacheCreationInputTokens")) * unit_in * rate
    ) / 1e6


def prices(directory: Path) -> int:
    """저장한 요약의 `modelUsage` 마다 `costUSD` 가 공식 단가 셈의 어느 캐시 쓰기 배수와 같은지
    찍는다.

    한 모델의 캐시 쓰기가 한 수명으로만 났을 때만 한 배수와 맞는다. 맞는 배수가 없는 모델이 하나라도
    있으면 1, 모두 맞으면 0. 캐시 쓰기가 0이면 두 배수가 함께 맞는다.
    """
    unmatched = 0
    for name, summary in load_summaries(directory).items():
        usage = summary.get("model_usage")
        for model, raw in usage.items() if isinstance(usage, dict) else []:
            price = PRICES.get(str(model))
            if not isinstance(raw, dict) or price is None:
                print(f"{name} {model}: 단가 없음")
                unmatched += 1
                continue
            cost = number(raw.get("costUSD"))
            fits = [
                label
                for label, rate in WRITE_RATES.items()
                if math.isclose(official_cost(raw, price, rate), cost, rel_tol=1e-9, abs_tol=1e-12)
            ]
            print(
                f"{name} {model} costUSD={cost:.7f} 맞는 캐시 쓰기 배수: {'·'.join(fits) or '없음'}"
            )
            unmatched += not fits
    return 0 if unmatched == 0 else 1


def run_arm(arm: str, out: Path, rounds: Rounds) -> None:
    """갈래 하나를 돌아 호출마다 회차 하나를 `rounds` 에 적는다. 앞 호출이 예외로 끝나 요약이 없으면
    이어 부르는 호출은 돌지 않고 측정 아님으로 적는다."""
    root = Path(tempfile.mkdtemp(prefix="rerun-probe-"))
    try:
        found = ancestors_with_claude_dir(root)
        if found:
            print(f"임시 폴더의 상위에 .claude/ 가 있다: {found}", file=sys.stderr)
            raise SystemExit(2)
        repo = layout(root, rules=arm == "거부")
        outside = root / "outside" / "secret.txt"
        session = str(uuid.uuid4())
        args = [*BASE_COMMAND, "--session-id", session]
        question = {
            "모양": READ_QUESTION,
            "예산": READ_QUESTION,
            "누적": NO_TOOL_QUESTION,
            "거부": deny_question(outside),
            "거부대조": deny_question(outside),
            "질문": ASK_QUESTION,
            "서브": SUBAGENT_QUESTION,
        }[arm]
        if arm == "예산":
            args += ["--max-budget-usd", BUDGET]
        # `Rounds.round` 는 본문의 예외를 삼켜 `with` 뒤로 오므로 요약이 없을 수 있다. pyright 는 그
        # 삼킴을 모르고 `None` 비교를 언제나 거짓으로 보아, 끝난 요약은 목록에 담는다.
        finished: list[Summary] = []
        with rounds.round(arm) as current:
            summary = record(arm, out, args, drive(args, repo, question))
            summary["transcript"] = transcript_effort(session)
            if arm in ("거부", "거부대조"):
                summary["actions"] = action_outcomes(summary, repo)
            finished.append(summary)
            save(arm, out, summary)
            mark(current, arm, summary, None)
        if arm in ("모양", "예산", "누적"):
            name = {"모양": "이어가기", "예산": "예산이어가기", "누적": "누적이어가기"}[arm]
            if not finished:
                rounds.record(name, measured=False, result=f"앞 호출 {arm} 이 끝나지 않았다")
                return
            summary = finished[0]
            again_args = [*BASE_COMMAND, "--resume", session]
            if arm == "예산":
                again_args += ["--max-budget-usd", BUDGET]
            if arm == "누적":
                again_args += ["--max-budget-usd", RESUME_BUDGET]
            again_question = READ_QUESTION if arm == "누적" else RESUME_QUESTION
            with rounds.round(name) as current:
                again = record(name, out, again_args, drive(again_args, repo, again_question))
                again["transcript"] = transcript_effort(session)
                save(name, out, again)
                mark(current, name, again, summary)
    finally:
        remove_tree(root)


def main() -> int:
    parser = argparse.ArgumentParser(description="다시 풀기 러너가 기대는 claude -p 의 동작")
    parser.add_argument("out", type=Path, nargs="?")
    parser.add_argument("--arm", choices=ARMS)
    parser.add_argument("--judge", type=Path, help="저장한 요약을 다시 판정한다")
    parser.add_argument("--prices", type=Path, help="저장한 요약의 비용을 공식 단가와 견준다")
    options = parser.parse_args()
    if options.judge is not None:
        return judge(options.judge)
    if options.prices is not None:
        return prices(options.prices)
    if options.out is None:
        parser.error("출력 디렉터리, --judge, --prices 가운데 하나를 준다")
    out: Path = options.out
    out.mkdir(parents=True, exist_ok=True)
    rounds = Rounds()
    for arm in [options.arm] if options.arm else list(ARMS):
        run_arm(arm, out, rounds)
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    sys.exit(main())
