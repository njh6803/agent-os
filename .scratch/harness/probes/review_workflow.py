"""claude-review 워크플로의 체크아웃 토큰과 코멘트 0개 가드의 건너뛰기를 판정한다.

하나. `.github/workflows/claude-code-review.yml` 의 체크아웃 단계에서 `persist-credentials` 가
`false` 인지 본다. 없으면 기본값 true 라 어긋남이다.

둘. 가드 스텝("Fail when Claude left no comment")의 `run` 을 꺼내 사례마다 돌려 결과를 기대와
견준다. 셸은 러너가 `shell:` 이 없을 때 쓰는 `bash -e` 이고, `gh` 는 셸 함수로 갈아 끼워
`pr diff` 에는 바뀐 파일 목록을, `api` 에는 코멘트 JSON 을 낸다. `jq` 는 진짜를 쓴다.
결과는 셋으로 가른다. 집계 줄("claude[bot] 코멘트 (")이 없이 0 이면 건너뜀, 집계 줄이 있으면
종료 0 은 통과, 1 은 실패다. 그 밖(집계 없이 0 이 아닌 종료 등)은 이상으로 찍고 어긋남으로 센다.
종료 코드만 보면 스크립트를 찾지 못한 실행도 "실패"로 기대와 맞아 버린다(첫 판이 그랬다).

기대는 대기열 50 을 반영한 판이다. 가드는 이 워크플로 파일 자체가 바뀐 PR 에서만 건너뛰고,
`ci.yml` 같은 다른 워크플로만 바뀐 PR 에서는 코멘트를 센다. 반영 전의 판(`.github/workflows/`
아래 어느 파일이든 건너뛰기)에 돌리면 가드 사례 셋이 어긋난다. `ci.yml` 만 바꾼 두 사례와 같은
이름의 다른 경로(`x/...`, `....orig`)다.

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
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

WORKFLOW = ".github/workflows/claude-code-review.yml"
GUARD_STEP = "Fail when Claude left no comment"
STARTED_AT = "2026-10-07T05:23:00Z"

FAKE_GH = """\
gh() {
  case "$1 $2" in
    "pr diff") printf '%s\\n' "$FAKE_FILES" ;;
    "api "*) printf '%s\\n' "$FAKE_COMMENTS" ;;
    *) echo "가짜 gh: 모르는 호출: $*" >&2; return 2 ;;
  esac
}
"""


def _comment(login: str, created_at: str) -> dict[str, object]:
    return {"user": {"login": login}, "created_at": created_at}


AFTER = _comment("claude[bot]", "2026-10-07T05:30:00Z")
BEFORE = _comment("claude[bot]", "2026-10-07T05:00:00Z")
OTHER = _comment("coderabbitai[bot]", "2026-10-07T05:30:00Z")

COUNT_LINE = "claude[bot] 코멘트 ("
SKIP, PASS, FAIL = "건너뜀", "통과", "실패"

# (이름, 바뀐 파일, 코멘트, 기대 결과)
CASES: list[tuple[str, list[str], list[dict[str, object]], str]] = [
    ("이 워크플로를 바꿈, 코멘트 없음", [WORKFLOW, "docs/x.md"], [], SKIP),
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


def _run(script: Path, files: list[str], comments: list[dict[str, object]]) -> tuple[str, str]:
    env = {
        **os.environ,
        "GH_TOKEN": "가짜",
        "REPO": "owner/repo",
        "PR": "1",
        "STARTED_AT": STARTED_AT,
        "FAKE_FILES": "\n".join(files),
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
    if not counted and done.returncode == 0:
        outcome = SKIP
    elif counted and done.returncode in (0, 1):
        outcome = PASS if done.returncode == 0 else FAIL
    else:
        outcome = f"이상(종료 {done.returncode})"
    return outcome, lines[-1] if lines else ""


def main() -> int:
    rev = sys.argv[1] if len(sys.argv) > 1 else None
    steps = _steps(_load(rev))
    print(f"원천: {rev or '작업 트리'}:{WORKFLOW}")
    persist = _persist_credentials(steps)
    mismatches = int(persist is not False)
    mark = "어긋남" if mismatches else "기대대로"
    print(f"[{mark}] 체크아웃 persist-credentials: {persist!r}(기대 False)")
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "guard.sh"
        script.write_text(FAKE_GH + _guard(steps), encoding="utf-8", newline="\n")
        for name, files, comments, expected in CASES:
            outcome, last = _run(script, files, comments)
            mark = "기대대로" if outcome == expected else "어긋남"
            mismatches += outcome != expected
            print(f"[{mark}] {name}: {outcome}(기대 {expected}) — {last}")
    print(f"어긋남 {mismatches}/{len(CASES) + 1}")
    return 1 if mismatches else 0


if __name__ == "__main__":
    sys.exit(main())
