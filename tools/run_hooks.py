"""훅을 실제 페이로드로 돌려 발동·침묵이 기대와 같은지 본다. 하네스 변경의 실행 확인이다.

새 훅의 넷 중 "실제 입력으로 실행 확인"(대기열 24)을 두 세션이 스크래치패드 스크립트로 손수 다시
만들었다(일지 2026-09-28-05 회고 1). 워크트리 세션의 훅으로는 바뀐 훅을 확인할 수 없다 — 워크트리의
훅 파일에 넣은 계측이 돌지 않았고 주 체크아웃의 파일이 돈다(2026-09-28). 그래서 이 러너가
`.claude/settings.json` 이 등록한 모양(`uv run --project <루트> --no-sync python <훅>`)으로 자식을
띄우고 stdin 에 페이로드를 넣는다. 자식 환경에서 `PYTHONUTF8` 을 빼고(훅 환경에 있다고 가정하지
않는다, 대기열 25·40) 저장소를 가리키는 `GIT_*` 도 벗긴다(pre-commit 아래에서 git 이 내보낸 값이
임시 저장소를 이 저장소로 돌린다, tests/conftest.py).

페이로드 표는 `tools/hook_payloads.toml`. 문자열 값의 자리표시자 여섯 — `${ROOT}`(저장소 루트),
`${MAIN_REPO}`·`${WORK_REPO}`(main 과 작업 브랜치의 임시 저장소 — 이 저장소의 브랜치에 기대를 걸지
않는다), `${NEW_TRANSCRIPT}`·`${USED_TRANSCRIPT}`(아직 없는 트랜스크립트와 assistant 기록이 있는
트랜스크립트 — 첫 턴과 그 반례), `${KOREAN_HEREDOC_45}`(한글 45줄 heredoc). 기대는 넷.
deny(`permissionDecision: deny`), block(`decision: block` 또는 종료 코드 2), context
(`additionalContext`), silent(종료 0, 출력 없음). 등록된 훅인데 표에 없거나 발동·침묵 한쪽이 없으면
그것도 어긋남이다 — 러너는 표만 믿으므로 표의 빈자리를 스스로 센다. pre-commit 이 `always_run`
으로 돌리고 하나라도 어긋나면 1 이다. 새 훅은 표에 발동 하나와 침묵 하나를 더하되, 침묵은 손으로
지은 반례가 아니라 그 훅이 실제로 받을 입력 중 발동하지 말아야 할 것으로(대기열 24 — 지시문 훅은
첫 턴이라는 축을 반례가 보지 못했다).
못 보는 것: Claude Code 가 실제로 주는 페이로드 모양과 표가 다른 것(표는 손으로 쓴다), settings.json
의 매처(어느 도구에 걸리는지는 등록이 정하고 러너는 훅 파일을 직접 부른다), 훅이 쓰는 시간.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, JsonValue, ValidationError

ROOT = Path(__file__).resolve().parent.parent
PAYLOADS = ROOT / "tools" / "hook_payloads.toml"
SETTINGS = ROOT / ".claude" / "settings.json"
Expectation = Literal["deny", "block", "context", "silent"]
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
    permissionDecision: str | None = None
    additionalContext: str | None = None


class _HookOutput(BaseModel):
    decision: str | None = None
    additionalContext: str | None = None
    hookSpecificOutput: _HookSpecific | None = None


class _HookEntry(BaseModel):
    command: str


class _HookGroup(BaseModel):
    hooks: list[_HookEntry]


class _Settings(BaseModel):
    hooks: dict[str, list[_HookGroup]]


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


def registered_hooks(settings_path: Path = SETTINGS) -> set[str]:
    """`.claude/settings.json` 이 등록한 훅 파일 이름들."""
    settings = _Settings.model_validate_json(settings_path.read_text(encoding="utf-8"))
    return {
        entry.command.rsplit("/", 1)[-1].rstrip('"')
        for groups in settings.hooks.values()
        for group in groups
        for entry in group.hooks
    }


def coverage_gaps(cases: list[Case], registered: set[str]) -> list[str]:
    """등록된 훅인데 표에 없거나 발동·침묵 한쪽이 없는 것. 표만 믿는 러너의 빈자리를 여기서 센다."""
    by_hook: dict[str, set[str]] = {}
    for case in cases:
        by_hook.setdefault(case.hook, set()).add(case.expect)
    gaps: list[str] = []
    for hook in sorted(registered):
        expects = by_hook.get(hook)
        if expects is None:
            gaps.append(f"{hook}: 등록됐는데 표에 없다")
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


def outcome_of(returncode: int, stdout: str) -> str:
    """훅의 종료 코드와 stdout 을 기대 넷 중 하나로(또는 그 밖의 설명으로) 읽는다."""
    if returncode == 2:
        return "block"
    text = stdout.strip()
    if not text:
        return "silent" if returncode == 0 else f"exit {returncode}"
    try:
        output = _HookOutput.model_validate_json(text)
    except ValidationError:
        return "output"
    specific = output.hookSpecificOutput or _HookSpecific()
    if specific.permissionDecision == "deny":
        return "deny"
    if output.decision == "block":
        return "block"
    if specific.additionalContext or output.additionalContext:
        return "context"
    return "output"


def hook_environment() -> dict[str, str]:
    """자식 훅의 환경. `PYTHONUTF8` 과 저장소를 가리키는 `GIT_*` 를 뺀다."""
    excluded = {"PYTHONUTF8", *REPO_LOCATION_VARS}
    return {key: value for key, value in os.environ.items() if key not in excluded}


def run_case(case: Case, replacements: dict[str, str]) -> Result:
    payload = substitute(case.payload, replacements)
    process = subprocess.run(
        [
            "uv",
            "run",
            "--project",
            str(ROOT),
            "--no-sync",
            "python",
            str(ROOT / "tools" / case.hook),
        ],
        input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
        env=hook_environment(),
        cwd=ROOT,
        check=False,
    )
    stdout = process.stdout.decode("utf-8", "replace")
    stderr = process.stderr.decode("utf-8", "replace")
    return Result(case, outcome_of(process.returncode, stdout), (stdout or stderr).strip())


def create_fixtures(scratch: Path) -> dict[str, str]:
    """자리표시자가 가리킬 것들을 `scratch` 에 만들고 그 값을 돌려준다.

    임시 저장소 둘(main, 작업 브랜치)은 `GIT_*` 를 벗긴 환경으로 만든다. 트랜스크립트 하나는
    assistant 기록이 있는 파일로 두고, 다른 하나는 만들지 않은 경로다(첫 턴).
    """
    main_repo = scratch / "on-main"
    work_repo = scratch / "on-topic"
    for path, branch in ((main_repo, "main"), (work_repo, "chore/x")):
        subprocess.run(
            ["git", "init", "-q", "-b", branch, str(path)], check=True, env=hook_environment()
        )
    used_transcript = scratch / "transcript-used.jsonl"
    used_transcript.write_text(
        '{"type": "user"}\n{"type": "assistant"}\n', encoding="utf-8", newline="\n"
    )
    korean_heredoc = "cat <<'EOF'\n" + "\n".join(f"한글 줄 {i}" for i in range(45)) + "\nEOF"
    return {
        "ROOT": ROOT.as_posix(),
        "MAIN_REPO": main_repo.as_posix(),
        "WORK_REPO": work_repo.as_posix(),
        "NEW_TRANSCRIPT": (scratch / "transcript-not-yet.jsonl").as_posix(),
        "USED_TRANSCRIPT": used_transcript.as_posix(),
        "KOREAN_HEREDOC_45": korean_heredoc,
    }


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    cases = load_cases()
    gaps = coverage_gaps(cases, registered_hooks())
    with tempfile.TemporaryDirectory() as scratch:
        replacements = create_fixtures(Path(scratch))
        results = [run_case(case, replacements) for case in cases]
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
    print(f"훅 페이로드 {len(results)}건, 어긋남 {len(failures)}건, 표의 빈자리 {len(gaps)}건.")
    return 1 if failures or gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
