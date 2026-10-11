"""claude-review 워크플로의 체크아웃 토큰과 코멘트 0개 가드의 건너뛰기를 판정한다.

하나. `.github/workflows/claude-code-review.yml` 의 체크아웃 단계에서 `persist-credentials` 가
`false` 인지 본다. 없으면 기본값 true 라 어긋남이다.

둘. 리뷰 단계의 허용 규칙 `Bash(gh pr comment …)` 안의 명령이 프롬프트에 백틱으로 글자 그대로
있는지 본다. 허용은 정확 일치라 한쪽만 고치면 CI 에서 게시가 거부된다.

셋. 가드 스텝("Fail when Claude left no comment")의 `run` 을 꺼내 사례마다 돌려 결과를 기대와
견준다. 셸은 러너가 `shell:` 이 없을 때 쓰는 `bash -e` 이고, `gh` 는 셸 함수로 갈아 끼워
`api …/pulls/…/files` 에는 바뀐 파일 이름을(이름 바꾸기면 새 이름과 옛 이름을. `--jq` 를 거친
모양이다), 그 밖의 `api` 에는 코멘트 JSON 을 낸다. 전의 판이 쓰던 `pr diff` 에는
`gh pr diff --name-only` 처럼 새 이름만 내고 한글 이름은 따옴표와 8진수로 낸다(PR #70·#153).
사례의 이름 바꾸기는 `옛 -> 새` 로 적는다. `jq` 는 진짜를 쓴다. 바뀐 파일 목록이 없는
사례(`None`)는 가짜 목록 호출이 HTTP 500 처럼 실패한다. 결과는 다섯으로 가른다. 건너뛴다는
줄이 있고 집계 줄("claude[bot] 코멘트 (")이 없이 0 이면 건너뜀, 집계 줄이 있으면 종료 0 은 통과,
1 은 실패, 함께 실었다는 오류 줄이 있고 1 이면 함께 실음, 목록을 얻지 못했다는 오류 줄이 있고
1 이면 목록 실패다. 그 밖은 이상으로 찍고 어긋남으로 센다. 종료 코드만
보면 스크립트를 찾지 못한 실행도 "실패"로 기대와 맞아 버린다(첫 판이 그랬다).

기대는 대기열 50·158·161 을 반영한 판이다. 가드는 이 워크플로 파일 자체가 바뀐 PR 에서만 코멘트를
세지 않고, `ci.yml` 같은 다른 워크플로만 바뀐 PR 에서는 센다(50). 이 파일을 바꾼 PR 이 일지
(`docs/journal/`), 대기열(`.scratch/retro-queue.md`), 하네스 탐침(`.scratch/harness/probes/`) 밖의
파일을 함께 실으면 실패한다(158). 목록을 얻지 못하면 그 까닭을 찍고 실패한다(161). 50 반영 전의 판
(`.github/workflows/` 아래 어느 파일이든 건너뛰기)에 돌리면 `ci.yml` 만 바꾼 두 사례와 같은 이름의
다른 경로(`x/...`, `....orig`)가 어긋나고, 158·161 반영 전의 판에 돌리면 함께 실음 사례들이
건너뜀으로, 목록 실패 사례들이 코멘트를 센 통과·실패로 어긋난다.

사용: 저장소 루트에서 Git Bash 로
    PYTHONUTF8=1 uv run python .scratch/harness/probes/review_workflow.py [<rev>]
<rev> 를 주면 작업 트리 대신 `git show <rev>:<워크플로>` 를 읽는다(예: origin/main).
bash 와 jq 가 PATH 에 있어야 하고 PyYAML 을 쓴다(프로젝트의 `uv sync` 가 깐다). PowerShell 의
PATH 에서는 `bash` 가 System32 의 WSL 로 찾아져 모든 사례가 이상으로 나온다.
모두 기대대로면 0, 하나라도 어긋나면 1 로 끝난다.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

WORKFLOW = ".github/workflows/claude-code-review.yml"
GUARD_STEP = "Fail when Claude left no comment"
REVIEW_STEP = "Run Claude Code Review"
PUBLISH_RULE = re.compile(r"Bash\((gh pr comment [^)]*|gh pr comment:\*)\)")
STARTED_AT = "2026-10-07T05:23:00Z"

FAKE_GH = """\
gh() {
  case "$1 $2" in
    "api "*/pulls/*/files)
      if [ -n "$FAKE_LIST_FAIL" ]; then echo "HTTP 500: 가짜" >&2; return 1; fi
      printf '%s\\n' "$FAKE_FILES" ;;
    "pr diff")
      if [ -n "$FAKE_LIST_FAIL" ]; then echo "HTTP 500: 가짜" >&2; return 1; fi
      printf '%s\\n' "$FAKE_DIFF_NAMES" ;;
    "api "*) printf '%s\\n' "$FAKE_COMMENTS" ;;
    *) echo "가짜 gh: 모르는 호출: $*" >&2; return 2 ;;
  esac
}
"""
RENAME = " -> "


def _comment(login: str, created_at: str) -> dict[str, object]:
    return {"user": {"login": login}, "created_at": created_at}


AFTER = _comment("claude[bot]", "2026-10-07T05:30:00Z")
BEFORE = _comment("claude[bot]", "2026-10-07T05:00:00Z")
OTHER = _comment("coderabbitai[bot]", "2026-10-07T05:30:00Z")

COUNT_LINE = "claude[bot] 코멘트 ("
SKIP_LINE = "이 워크플로를 바꾼 PR: 액션이 건너뛰므로"
MIXED_LINE = "::error::이 워크플로를 바꾼 PR은 리뷰가 건너뛰므로"
LIST_FAIL_LINE = "::error::바뀐 파일 목록을 얻지 못했다"
SKIP, PASS, FAIL, MIXED, LIST_FAIL = "건너뜀", "통과", "실패", "함께 실음", "목록 실패"

JOURNAL = "docs/journal/2026-10-07-19-x.md"
JOURNAL_KO = "docs/journal/2026-10-07-19-한글 이름.md"
QUEUE = ".scratch/retro-queue.md"
PROBE = ".scratch/harness/probes/review_workflow.py"
MOVED = ".scratch/harness/probes/moved.py"
# 사례가 기록으로 쓰는 경로. 함께 실음의 목록에서 빠져야 한다
RECORDS = (JOURNAL, JOURNAL_KO, QUEUE, PROBE, MOVED)

# (이름, 바뀐 파일(None 이면 목록 호출이 실패한다), 코멘트, 기대 결과)
CASES: list[tuple[str, list[str] | None, list[dict[str, object]], str]] = [
    # 옛 경로가 기록 밖이면 그 지우기가 리뷰 없이 병합된다. `pr diff` 는 새 경로만 찍었다
    ("기록으로 옮긴 이름 바꾸기", [WORKFLOW, ".scratch/x/a.py" + RENAME + MOVED], [], MIXED),
    # `pr diff` 는 한글 이름을 따옴표와 8진수로 찍어 `^` 정규식에 걸리지 않았다(PR #153)
    ("한글 이름의 일지", [WORKFLOW, JOURNAL_KO], [], SKIP),
    # 161 전에는 실패가 이 파일을 바꾸지 않은 PR 로 읽혀 코멘트를 셌다
    ("목록 실패, 시작 뒤 코멘트", None, [AFTER], LIST_FAIL),
    ("목록 실패, 코멘트 없음", None, [], LIST_FAIL),
    ("이 워크플로만 바꿈, 코멘트 없음", [WORKFLOW], [], SKIP),
    ("이 워크플로와 기록 셋", [WORKFLOW, JOURNAL, QUEUE, PROBE], [], SKIP),
    ("이 워크플로와 다른 문서", [WORKFLOW, JOURNAL, "docs/x.md"], [], MIXED),
    ("이 워크플로와 코드", [WORKFLOW, "src/agent_os/main.py"], [AFTER], MIXED),
    ("이 워크플로와 다른 워크플로", [WORKFLOW, ".github/workflows/ci.yml"], [], MIXED),
    ("기록 비슷한 이름: 일지 폴더 밖", [WORKFLOW, "docs/journal.md"], [], MIXED),
    ("기록 비슷한 이름: 대기열 뒤에 더 붙음", [WORKFLOW, QUEUE + ".bak"], [], MIXED),
    ("기록 비슷한 이름: 다른 기능의 탐침", [WORKFLOW, ".scratch/x/probes/a.py"], [], MIXED),
    ("기록 비슷한 이름: 앞에 더 붙음", [WORKFLOW, "x/docs/journal/a.md"], [], MIXED),
    ("ci.yml 만, 코멘트 없음", [".github/workflows/ci.yml"], [], FAIL),
    ("ci.yml 만, 시작 뒤 코멘트", [".github/workflows/ci.yml"], [AFTER], PASS),
    ("코드만, 코멘트 없음", ["src/agent_os/main.py"], [], FAIL),
    ("코드만, 시작 전 코멘트와 다른 봇", ["src/agent_os/main.py"], [BEFORE, OTHER], FAIL),
    ("코드만, 시작 뒤 코멘트", ["src/agent_os/main.py"], [AFTER], PASS),
    ("같은 이름의 다른 경로", ["x/" + WORKFLOW, WORKFLOW + ".orig"], [], FAIL),
]


def _load(rev: str | None) -> dict[str, object]:
    if rev is None:
        text = Path(WORKFLOW).read_text(encoding="utf-8")
    else:
        text = subprocess.run(
            ["git", "show", f"{rev}:{WORKFLOW}"],
            check=True,
            capture_output=True,
            encoding="utf-8",
        ).stdout
    loaded = yaml.safe_load(text)
    assert isinstance(loaded, dict)
    return loaded


def _steps(workflow: dict[str, object]) -> list[dict[str, object]]:
    jobs = workflow["jobs"]
    assert isinstance(jobs, dict)
    job = jobs["claude-review"]
    assert isinstance(job, dict)
    steps = job["steps"]
    assert isinstance(steps, list)
    return [step for step in steps if isinstance(step, dict)]


def _persist_credentials(steps: list[dict[str, object]]) -> object:
    for step in steps:
        if str(step.get("uses", "")).startswith("actions/checkout@"):
            with_ = step.get("with") or {}
            assert isinstance(with_, dict)
            return with_.get("persist-credentials", "(기본값 true)")
    raise SystemExit("체크아웃 단계가 없다")


def _guard(steps: list[dict[str, object]]) -> str:
    for step in steps:
        if step.get("name") == GUARD_STEP:
            assert "shell" not in step
            return str(step["run"])
    raise SystemExit(f"가드 스텝 {GUARD_STEP!r} 가 없다")


def _api_names(files: list[str]) -> list[str]:
    """pulls files API 를 `--jq '.[] | .filename, (.previous_filename // empty)'` 로 거친 모양."""
    names: list[str] = []
    for entry in files:
        old, _, new = entry.partition(RENAME)
        names += [new, old] if new else [old]
    return names


def _diff_names(files: list[str]) -> list[str]:
    """`gh pr diff --name-only` 의 모양. 이름 바꾸기는 새 이름만, 한글 이름은 따옴표와 8진수다."""
    names: list[str] = []
    for entry in files:
        old, _, new = entry.partition(RENAME)
        name = new or old
        if not name.isascii():
            escaped = "".join(
                char if char.isascii() else "".join(f"\\{byte:o}" for byte in char.encode())
                for char in name
            )
            name = f'"{escaped}"'
        names.append(name)
    return names


def _run(
    script: Path, files: list[str] | None, comments: list[dict[str, object]]
) -> tuple[str, str]:
    env = {
        **os.environ,
        "GH_TOKEN": "가짜",
        "REPO": "owner/repo",
        "PR": "1",
        "STARTED_AT": STARTED_AT,
        "FAKE_FILES": "\n".join(_api_names(files or [])),
        "FAKE_DIFF_NAMES": "\n".join(_diff_names(files or [])),
        "FAKE_LIST_FAIL": "1" if files is None else "",
        "FAKE_COMMENTS": json.dumps(comments),
    }
    # Windows 에서 맨 "bash" 는 PATH 보다 System32 를 먼저 보아 WSL 의 bash 가 되고, 그 bash 는
    # Windows 경로도 이 환경 변수도 받지 못한다. 그래서 PATH 에서 찾은 bash 를 절대 경로로 부르고,
    # 스크립트 경로는 Git Bash 가 받는 슬래시 경로로 넘긴다.
    bash = shutil.which("bash")
    assert bash is not None, "PATH 에 bash 가 없다"
    done = subprocess.run(
        [bash, "-e", script.as_posix()], env=env, capture_output=True, encoding="utf-8"
    )
    lines = (done.stdout + done.stderr).strip().splitlines()
    counted = any(line.startswith(COUNT_LINE) for line in lines)
    skipped = any(line.startswith(SKIP_LINE) for line in lines)
    mixed = any(line.startswith(MIXED_LINE) for line in lines)
    list_failed = any(line.startswith(LIST_FAIL_LINE) for line in lines)
    marks = (counted, skipped, mixed, list_failed)
    if marks == (False, True, False, False) and done.returncode == 0:
        outcome = SKIP
    elif marks == (True, False, False, False) and done.returncode in (0, 1):
        outcome = PASS if done.returncode == 0 else FAIL
    elif marks == (False, False, False, True) and done.returncode == 1:
        outcome = LIST_FAIL
    elif marks == (False, False, True, False) and done.returncode == 1 and files is not None:
        # 가드가 찍은 목록이 기록을 뺀 나머지와 같아야 한다. 기록까지 찍어도 실패는 실패라 따로 본다
        # (목록이 다르면 기대와 다른 결과로 남긴다)
        start = next(i for i, line in enumerate(lines) if line.startswith(MIXED_LINE))
        listed = lines[start + 1 :]
        others = [path for path in _api_names(files) if path not in (WORKFLOW, *RECORDS)]
        outcome = MIXED if listed == others else f"{MIXED}(목록 {listed}, 기대 {others})"
    else:
        outcome = f"이상(종료 {done.returncode})"
    return outcome, lines[-1] if lines else ""


def _publish_command(steps: list[dict[str, object]]) -> tuple[str, bool]:
    """허용 규칙의 게시 명령과, 그것이 정확 일치이고 프롬프트에 백틱으로 그대로 있는지."""
    for step in steps:
        if step.get("name") == REVIEW_STEP:
            with_ = step.get("with") or {}
            assert isinstance(with_, dict)
            found = PUBLISH_RULE.search(str(with_.get("claude_args", "")))
            if found is None:
                return "(규칙 없음)", False
            command = found.group(1)
            exact = "*" not in command
            return command, exact and f"`{command}`" in str(with_.get("prompt", ""))
    raise SystemExit(f"리뷰 단계 {REVIEW_STEP!r} 가 없다")


def main() -> int:
    rev = sys.argv[1] if len(sys.argv) > 1 else None
    steps = _steps(_load(rev))
    print(f"원천: {rev or '작업 트리'}:{WORKFLOW}")
    persist = _persist_credentials(steps)
    mismatches = int(persist is not False)
    mark = "어긋남" if mismatches else "기대대로"
    print(f"[{mark}] 체크아웃 persist-credentials: {persist!r}(기대 False)")
    command, same = _publish_command(steps)
    mismatches += not same
    mark = "기대대로" if same else "어긋남"
    print(f"[{mark}] 게시 명령이 정확 일치 규칙이고 프롬프트에 그대로 있다: {command}")
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "guard.sh"
        script.write_text(FAKE_GH + _guard(steps), encoding="utf-8", newline="\n")
        for name, files, comments, expected in CASES:
            outcome, last = _run(script, files, comments)
            mark = "기대대로" if outcome == expected else "어긋남"
            mismatches += outcome != expected
            print(f"[{mark}] {name}: {outcome}(기대 {expected}) — {last}")
    print(f"어긋남 {mismatches}/{len(CASES) + 2}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
