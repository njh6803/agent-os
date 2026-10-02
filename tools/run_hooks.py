"""훅을 손으로 쓴 페이로드로 돌려 발동·침묵이 기대와 같은지 본다. 하네스 변경의 실행 확인이다.

새 훅의 넷 중 "실제 입력으로 실행 확인"(대기열 24)을 두 세션이 스크래치패드 스크립트로 손수 다시
만들었다(일지 2026-09-28-05 회고 1). 워크트리 세션의 훅으로는 바뀐 훅을 확인할 수 없다 — 워크트리의
훅 파일에 넣은 계측이 돌지 않았고 주 체크아웃의 파일이 돈다(2026-09-28). 그래서 이 러너가
`.claude/settings.json` 이 등록한 모양(`REGISTRATION` — `uv run --project <루트> --no-sync python
<루트>/tools/launch_hook.py <훅>`)으로 자식을 띄우고 stdin 에 페이로드를 넣는다. 등록 명령이 모두 그
모양인지도 대조한다. 다르면 러너가 재는 것과 세션이 띄우는 것이 갈리고, 래퍼를 거치지 않은 등록은
훅 파일이 없을 때 2로 끝나 PreToolUse 면 그 매처의 모든 호출을 막는다(대기열 91). 자식 환경에서
`PYTHONUTF8` 을 빼고(훅 환경에 있다고 가정하지 않는다, 대기열 25·40) 저장소를 가리키는 `GIT_*`
도 벗긴다(pre-commit 아래에서 git 이 내보낸 값이 임시 저장소를 이 저장소로 돌린다,
tests/conftest.py). `CLAUDE_CODE_ENTRYPOINT` 도 벗긴다(대기열
83 — Stop 훅이 SDK 세션에서 침묵하므로, 물려주면 판정이 러너를 띄운 자리에 기댄다). 자식은
settings.json 이 그 훅에 준 `timeout`(초) 안에 끝나야 한다 — 넘기면 어긋남 `timeout` 이다. 러너는
pre-commit 이 매 커밋 돌리므로 훅 하나가 멈추면 커밋도 멈춘다.

페이로드 표는 `tools/hook_payloads.toml`. 문자열 값의 자리표시자 열하나 — `${ROOT}`(저장소 루트),
`${MAIN_REPO}`·`${WORK_REPO}`(main 과 작업 브랜치의 임시 저장소 — 이 저장소의 브랜치에 기대를 걸지
않는다), `${UNPUSHED_REPO}`(임시 bare 저장소를 upstream 으로 두고 그 위에 푸시하지 않은 커밋이
하나 있는 작업 브랜치 저장소), `${NEW_TRANSCRIPT}`·`${USED_TRANSCRIPT}`(아직 없는 트랜스크립트와
assistant 기록이 있는 트랜스크립트 — 첫 턴과 그 반례), `${KOREAN_HEREDOC_45}`(한글 45줄 heredoc),
`${RUFF_PROJECT}`(ruff 설정이 있는 임시 디렉터리 — 한글 줄이 넘친 `long.py` 와 짧은 `short.py`),
`${LOOSE_PY}`(같은 한글 줄을 ruff 설정 밖에 둔 파일 — 이 저장소의 파일에 기대를 걸지 않는다),
`${OPEN_JOURNAL}`·`${CLOSED_JOURNAL}`(쓰기 뒤의 임시 일지 — 회고 절이 없는 것과 있는 것). 기대는 넷.
deny(`permissionDecision: deny`), block(`decision: block` 또는 종료 코드 2), context
(`additionalContext`), silent(종료 0, 출력 없음). `hookSpecificOutput` 을 내는 훅은
`hookEventName` 을 같이 내야 하고 그 값이 훅이 등록된 이벤트와 같아야 한다 — Claude Code 가 그
필드를 요구하므로 없거나 다르면 유효하게 받지 않는 출력이고, 러너도 `output`·`event <이름>` 으로
어긋남이라 본다. 등록과 표가 한쪽에만 있는 훅(등록됐는데 표에 없다, 표에 있는데 등록되지 않았다)과
발동·침묵 한쪽이 없는 훅도 어긋남이다 — 러너는 표만 믿으므로 표의 빈자리를 스스로 센다. 등록되지
않은 훅의 사례는 돌리지 않는다(대조할 이벤트와 시간 제한이 없다). pre-commit 이 `always_run` 으로
돌리고 하나라도 어긋나면 1 이다. 새 훅은 표에 발동 하나와 침묵 하나를 더하되, 침묵은 손으로 지은
반례가 아니라 그 훅이 실제로 받을 입력 중 발동하지 말아야 할 것으로(대기열 24 — 지시문 훅은 첫
턴이라는 축을 반례가 보지 못했다).
못 보는 것: Claude Code 가 실제로 주는 페이로드 모양과 표가 다른 것(표는 손으로 쓴다 — 런타임 입력
계약은 검증하지 않는다), settings.json 의 매처(어느 도구에 걸리는지는 등록이 정하고 러너는 훅을
이름으로 부른다), 등록 명령을 돌리는 셸(러너는 셸 없이 띄워 `${CLAUDE_PROJECT_DIR}` 의 전개와 따옴표
처리를 재지 않는다), 훅이 쓰는 시간(제한을 넘기는지만 본다).
"""

from __future__ import annotations

import io
import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import tomllib
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, JsonValue, ValidationError

ROOT = Path(__file__).resolve().parent.parent
PAYLOADS = ROOT / "tools" / "hook_payloads.toml"
SETTINGS = ROOT / ".claude" / "settings.json"
# `.claude/settings.json` 이 훅마다 등록하는 명령. `{hook}` 자리에 `tools/` 의 훅 파일 이름이 온다.
# 래퍼(tools/launch_hook.py)가 없는 훅을 지나가게 한다(대기열 91). 저장소 파일을 부르지 않는 훅
# (`echo …`)도 이 모양이 아니라 거절한다. tools/check_instructions.py 는 그런 훅을 받지만, 러너는 그
# 전에도 표에 없는 훅을 빈자리로 세어 커밋을 막았다 — 모든 등록이 tools/ 의 훅이라는 전제는 같다.
REGISTRATION = (
    'uv run --project "${CLAUDE_PROJECT_DIR}" --no-sync python'
    ' "${CLAUDE_PROJECT_DIR}/tools/launch_hook.py" {hook}'
)
_PROJECT_DIR = "${CLAUDE_PROJECT_DIR}"
_REGISTRATION_PATTERN = re.compile(
    re.escape(REGISTRATION).replace(re.escape("{hook}"), r"(hook_\w+\.py)")
)
Expectation = Literal["deny", "block", "context", "silent"]
# Claude Code 가 `timeout` 을 적지 않은 훅에 주는 시간(초).
DEFAULT_HOOK_TIMEOUT = 60
# 저장소를 가리키는 git 환경 변수. tests/conftest.py 도 여기서 import 한다 — 목록의 원천은 하나다.
REPO_LOCATION_VARS = (
    "GIT_DIR",
    "GIT_WORK_TREE",
    "GIT_COMMON_DIR",
    "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_PREFIX",
)


class Case(BaseModel):
    """표의 한 줄. `hook` 은 tools/ 아래 파일 이름, `payload` 는 stdin 에 넣을 JSON 이다."""

    hook: str
    expect: Expectation
    payload: dict[str, JsonValue]
    note: str = ""


class _Table(BaseModel):
    case: list[Case] = []


class _HookSpecific(BaseModel):
    hookEventName: str
    permissionDecision: str | None = None
    additionalContext: str | None = None


class _HookOutput(BaseModel):
    decision: str | None = None
    additionalContext: str | None = None
    hookSpecificOutput: _HookSpecific | None = None


class _HookEntry(BaseModel):
    command: str
    timeout: int = DEFAULT_HOOK_TIMEOUT


class _HookGroup(BaseModel):
    hooks: list[_HookEntry]


class _Settings(BaseModel):
    hooks: dict[str, list[_HookGroup]]


@dataclass(frozen=True)
class Registration:
    """`.claude/settings.json` 이 훅 하나에 준 것. 등록된 이벤트 이름과 시간 제한(초)."""

    event: str
    timeout: int


@dataclass(frozen=True)
class Result:
    case: Case
    outcome: str
    output: str

    @property
    def ok(self) -> bool:
        return self.outcome == self.case.expect


def load_cases(path: Path = PAYLOADS) -> list[Case]:
    """표를 읽는다. 기대가 넷 밖이거나 훅 파일이 없으면 ValueError."""
    try:
        table = _Table.model_validate(tomllib.loads(path.read_text(encoding="utf-8")))
    except ValidationError as error:
        raise ValueError(f"{path.name}: {error}") from error
    for case in table.case:
        if not (ROOT / "tools" / case.hook).is_file():
            raise ValueError(f"tools/{case.hook} 이 없다")
    return table.case


def registered_hooks(settings_path: Path = SETTINGS) -> dict[str, Registration]:
    """`.claude/settings.json` 이 등록한 훅 파일 이름 → 등록.

    명령이 `REGISTRATION` 모양이 아니면 ValueError — 러너는 그 모양으로 띄우므로, 다른 모양이면
    세션이 띄우는 것을 재지 않는다. 훅 하나가 이벤트 둘에 등록되어도 ValueError — 훅은
    `hookEventName` 하나를 내므로 대조할 수 없다.
    """
    settings = _Settings.model_validate_json(settings_path.read_text(encoding="utf-8"))
    registrations: dict[str, Registration] = {}
    for event, groups in settings.hooks.items():
        for group in groups:
            for entry in group.hooks:
                matched = _REGISTRATION_PATTERN.fullmatch(entry.command)
                if matched is None:
                    raise ValueError(
                        f"{event} 훅의 등록 모양이 다르다: {entry.command} — 모양은 {REGISTRATION}"
                    )
                hook = matched.group(1)
                previous = registrations.get(hook)
                if previous is not None and previous.event != event:
                    raise ValueError(f"{hook} 이 {previous.event} 와 {event} 둘에 등록됐다")
                registrations[hook] = Registration(event, entry.timeout)
    return registrations


def coverage_gaps(cases: list[Case], registered: Collection[str]) -> list[str]:
    """등록과 표가 한쪽에만 있는 훅, 발동·침묵 한쪽이 없는 훅. 표만 믿는 러너의 빈자리다."""
    by_hook: dict[str, set[str]] = {}
    for case in cases:
        by_hook.setdefault(case.hook, set()).add(case.expect)
    gaps: list[str] = []
    for hook in sorted({*by_hook, *registered}):
        expects = by_hook.get(hook)
        if expects is None:
            gaps.append(f"{hook}: 등록됐는데 표에 없다")
        elif hook not in registered:
            gaps.append(f"{hook}: 표에 있는데 등록되지 않았다")
        elif "silent" not in expects:
            gaps.append(f"{hook}: 침묵 사례가 없다")
        elif not expects - {"silent"}:
            gaps.append(f"{hook}: 발동 사례가 없다")
    return gaps


def substitute(value: JsonValue, replacements: dict[str, str]) -> JsonValue:
    """문자열 값 안의 `${이름}` 을 바꾼다. 표와 목록은 안으로 들어간다."""
    if isinstance(value, str):
        for name, replacement in replacements.items():
            value = value.replace("${" + name + "}", replacement)
        return value
    if isinstance(value, dict):
        return {key: substitute(item, replacements) for key, item in value.items()}
    if isinstance(value, list):
        return [substitute(item, replacements) for item in value]
    return value


def outcome_of(returncode: int, stdout: str, event: str) -> str:
    """훅의 종료 코드와 stdout 을 기대 넷 중 하나로(또는 그 밖의 설명으로) 읽는다.

    `hookSpecificOutput` 은 `hookEventName` 이 있어야 하고(없으면 Claude Code 가 받지 않는 출력이라
    `output`) 그 값이 `event`(훅이 등록된 이벤트)와 같아야 한다(다르면 `event <이름>`).
    """
    if returncode == 2:
        return "block"
    text = stdout.strip()
    if not text:
        return "silent" if returncode == 0 else f"exit {returncode}"
    try:
        output = _HookOutput.model_validate_json(text)
    except ValidationError:
        return "output"
    specific = output.hookSpecificOutput
    if specific is not None and specific.hookEventName != event:
        return f"event {specific.hookEventName}"
    if specific is not None and specific.permissionDecision == "deny":
        return "deny"
    if output.decision == "block":
        return "block"
    if (specific is not None and specific.additionalContext) or output.additionalContext:
        return "context"
    return "output"


def hook_environment() -> dict[str, str]:
    """자식 훅의 환경. `PYTHONUTF8`, 저장소를 가리키는 `GIT_*`, `CLAUDE_CODE_ENTRYPOINT` 를 뺀다.

    마지막 것은 `hook_stop_korean` 이 SDK 세션에서 침묵하는 근거라, 러너를 띄운 세션의 값을 물려주면
    판정이 러너가 도는 자리에 따라 바뀐다.
    """
    excluded = {"PYTHONUTF8", "CLAUDE_CODE_ENTRYPOINT", *REPO_LOCATION_VARS}
    return {key: value for key, value in os.environ.items() if key not in excluded}


def registration_command(hook: str) -> str:
    """훅 하나의 등록 명령. settings.json 에 적히는 글자 그대로다."""
    return REGISTRATION.replace("{hook}", hook)


def launch_argv(hook: str, root: Path = ROOT) -> list[str]:
    """등록 명령을 셸 없이 띄우는 인자 목록. `${CLAUDE_PROJECT_DIR}` 자리에 `root` 가 온다.

    템플릿을 먼저 나누고 인자마다 루트를 넣는다. 루트를 먼저 넣으면 경로 속 따옴표를 `shlex` 가
    구문으로 읽는다(PR #121 CodeRabbit).
    """
    root_text = root.as_posix()
    return [arg.replace(_PROJECT_DIR, root_text) for arg in shlex.split(registration_command(hook))]


def run_case(case: Case, replacements: dict[str, str], registration: Registration) -> Result:
    """자식 하나를 등록의 모양과 시간 제한으로 돌려 판정한다. 넘기면 어긋남 `timeout`."""
    payload = substitute(case.payload, replacements)
    try:
        process = subprocess.run(
            launch_argv(case.hook),
            input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            capture_output=True,
            env=hook_environment(),
            cwd=ROOT,
            check=False,
            timeout=registration.timeout,
        )
    except subprocess.TimeoutExpired:
        return Result(case, "timeout", f"{registration.timeout}초 안에 끝나지 않았다")
    stdout = process.stdout.decode("utf-8", "replace")
    stderr = process.stderr.decode("utf-8", "replace")
    outcome = outcome_of(process.returncode, stdout, registration.event)
    return Result(case, outcome, (stdout or stderr).strip())


def create_fixtures(scratch: Path) -> dict[str, str]:
    """자리표시자가 가리킬 것들을 `scratch` 에 만들고 그 값을 돌려준다.

    임시 저장소(main, 작업 브랜치, 푸시하지 않은 커밋이 있는 작업 브랜치와 그 upstream 인 bare
    저장소)는 `GIT_*` 를 벗긴 환경으로 만든다. 트랜스크립트 하나는 assistant 기록이 있는 파일로
    두고, 다른 하나는 만들지 않은 경로다(첫 턴). ruff 프로젝트 하나는
    줄 길이 100의 설정과 한글 줄이 넘친 `long.py`, 짧은 `short.py` 를 두고, 같은 한글 줄을 설정
    밖(`loose.py`)에도 둔다. 일지 둘은 "다음" 절을 채운 뒤의 모양이고, 하나만 회고 절이 있다.
    """
    main_repo = scratch / "on-main"
    work_repo = scratch / "on-topic"
    for path, branch in ((main_repo, "main"), (work_repo, "chore/x")):
        subprocess.run(
            ["git", "init", "-q", "-b", branch, str(path)],
            check=True,
            env=hook_environment(),
            timeout=DEFAULT_HOOK_TIMEOUT,
        )
    unpushed_repo = _unpushed_repository(scratch)
    used_transcript = scratch / "transcript-used.jsonl"
    used_transcript.write_text(
        '{"type": "user"}\n{"type": "assistant"}\n', encoding="utf-8", newline="\n"
    )
    korean_heredoc = "cat <<'EOF'\n" + "\n".join(f"한글 줄 {i}" for i in range(45)) + "\nEOF"
    ruff_project = scratch / "ruff-project"
    ruff_project.mkdir()
    # 이 저장소처럼 E 와 F 를 고른다. ruff 의 기본 선택에는 E501 이 없다.
    (ruff_project / "pyproject.toml").write_text(
        '[tool.ruff]\nline-length = 100\n\n[tool.ruff.lint]\nselect = ["E", "F"]\n',
        encoding="utf-8",
    )
    # 52자에 폭 102. 한글은 폭 2라 글자 수로는 짧아도 E501 이다.
    long_korean = "# " + "가" * 50 + "\n"
    (ruff_project / "long.py").write_text(long_korean, encoding="utf-8")
    (ruff_project / "short.py").write_text("x = 1\n", encoding="utf-8")
    loose = scratch / "loose.py"
    loose.write_text(long_korean, encoding="utf-8")
    journals = scratch / "docs" / "journal"
    journals.mkdir(parents=True)
    closing = "## 다음\n\n- web-admin의 04가 다음이다.\n"
    open_journal = journals / "2026-10-01-01-open.md"
    open_journal.write_text(f"# 일지\n\n## 한 것\n\n- 04\n\n{closing}", encoding="utf-8")
    closed_journal = journals / "2026-10-01-02-closed.md"
    closed_journal.write_text(f"# 일지\n\n## 회고\n\n- 62(새로)\n\n{closing}", encoding="utf-8")
    return {
        "ROOT": ROOT.as_posix(),
        "MAIN_REPO": main_repo.as_posix(),
        "WORK_REPO": work_repo.as_posix(),
        "UNPUSHED_REPO": unpushed_repo.as_posix(),
        "NEW_TRANSCRIPT": (scratch / "transcript-not-yet.jsonl").as_posix(),
        "USED_TRANSCRIPT": used_transcript.as_posix(),
        "KOREAN_HEREDOC_45": korean_heredoc,
        "RUFF_PROJECT": ruff_project.as_posix(),
        "LOOSE_PY": loose.as_posix(),
        "OPEN_JOURNAL": open_journal.as_posix(),
        "CLOSED_JOURNAL": closed_journal.as_posix(),
    }


def _unpushed_repository(scratch: Path) -> Path:
    """upstream 에 커밋 하나를 푸시하고 그 위에 푸시하지 않은 커밋 하나를 둔 작업 브랜치 저장소.

    upstream 은 같은 `scratch` 의 bare 저장소다. 네트워크와 이 저장소의 원격에 기대지 않는다.
    """
    origin = scratch / "origin.git"
    repo = scratch / "unpushed"
    identity = ["-c", "user.name=run_hooks", "-c", "user.email=run_hooks@localhost"]
    commands = [
        ["git", "init", "-q", "--bare", "-b", "chore/x", str(origin)],
        ["git", "init", "-q", "-b", "chore/x", str(repo)],
        ["git", "-C", str(repo), *identity, "commit", "-q", "--allow-empty", "-m", "pushed"],
        ["git", "-C", str(repo), "remote", "add", "origin", str(origin)],
        ["git", "-C", str(repo), "push", "-q", "-u", "origin", "chore/x"],
        ["git", "-C", str(repo), *identity, "commit", "-q", "--allow-empty", "-m", "unpushed"],
    ]
    for command in commands:
        subprocess.run(
            command,
            check=True,
            capture_output=True,
            env=hook_environment(),
            timeout=DEFAULT_HOOK_TIMEOUT,
        )
    return repo


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    cases = load_cases()
    registrations = registered_hooks()
    gaps = coverage_gaps(cases, registrations)
    runnable = [case for case in cases if case.hook in registrations]
    with tempfile.TemporaryDirectory() as scratch:
        replacements = create_fixtures(Path(scratch))
        results = [run_case(case, replacements, registrations[case.hook]) for case in runnable]
    failures = [result for result in results if not result.ok]
    for result in results:
        mark = "ok  " if result.ok else "FAIL"
        note = f" — {result.case.note}" if result.case.note else ""
        expect, actual = result.case.expect, result.outcome
        print(f"[{mark}] {result.case.hook:<28} 기대 {expect:<7} 실제 {actual}{note}")
        if not result.ok:
            print(f"       출력: {result.output[:200]}")
    for gap in gaps:
        print(f"[GAP ] {gap}")
    skipped = len(cases) - len(runnable)
    unregistered = f", 등록되지 않아 돌리지 않은 사례 {skipped}건" if skipped else ""
    summary = f"훅 페이로드 {len(results)}건, 어긋남 {len(failures)}건, 표의 빈자리 {len(gaps)}건"
    print(f"{summary}{unregistered}.")
    return 1 if failures or gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
