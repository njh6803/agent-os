"""카나리아 명령으로 띄운 `claude -p` 세션에 체크아웃의 git 상태가 실리는지 잰다.

대기열 243 의 전제다. `tools/canary.py` 의 `git_view` 독스트링이 근거로 든다. 둘째 판의 카나리아
대조군이 셋 모두 "없음"이라 답하고도 설명에 커밋하지 않은 훅 파일의 이름을 적었고(일지
2026-10-13-50), 세션의 git 상태로 실린 것으로 보였다. 무엇이 어디까지 실리는지 표지 낱말로 가른다.
- `저장소/`: git 저장소. 브랜치 `probe/mark-branch`, 커밋 여덟(제목 `mark-c01` … `mark-c08`, 뒤가
  최근), 추적하는 파일을 고친 `mark-modified.txt`, 스테이지한 새 파일 `mark-staged.txt`, 추적하지
  않는 파일 `mark-untracked.txt`, 추적하지 않는 폴더 `mark-dir/` 안의 `mark-inside.txt`. 몇 번째
  커밋까지 실리는지, 추적하지 않는 폴더가 폴더 이름으로만 실리는지 본다.
- `밖/`: 같은 파일을 둔 보통 폴더(git 저장소가 아니다). 음성 대조다. 여기서도 표지가 나오면 답이
  git 상태가 아니라 다른 데서(폴더 목록 등) 왔다.
`저장소` 갈래의 상태가 위와 같은지 돌리기 전에 git 으로 본다. 다르면 돌리지 않고 2 로 끝난다.

갈래마다 카나리아 명령(`--setting-sources project,local --strict-mcp-config --model sonnet
--tools Read`)으로 띄워, 도구를 쓰지 말고 컨텍스트에 실린 git 상태 블록을 글자 그대로 옮기게 한다.
회차마다 답에 든 표지와 도구 호출 수를 찍는다. 도구를 불렀으면 답이 파일을 읽은 데서 왔을 수 있어
그 회차는 측정이 아니다. 기대를 단언하지 않고 본 것을 찍는다.

회차마다 stream-json 원본(`.jsonl`)을 출력 디렉터리에 남기고 임시 디렉터리는 끝에 지운다.
돌리는 법: `uv run python .scratch/harness/probes/canary_git_status.py <출력 디렉터리>`.
`claude` CLI 와 인증이 든다. 회차마다 sonnet 호출이 하나이고 모두 셋이다. 종료 코드: 0 모든 회차가
측정이 됐다, 1 도구를 불렀거나 세션이 답을 내지 못한(제한 시간 600초를 넘긴 것 포함) 회차가 있다,
2 `저장소` 갈래의 상태를 만들지 못했다.
"""

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BRANCH = "probe/mark-branch"
COMMITS = [f"mark-c{number:02d}" for number in range(1, 9)]
FILES = ["mark-modified.txt", "mark-staged.txt", "mark-untracked.txt", "mark-dir/mark-inside.txt"]
MARKS = ["mark-branch", *COMMITS, *(Path(name).stem for name in FILES), "mark-dir"]
# `저장소` 갈래에서 돌리기 전에 git status --porcelain 이 내야 하는 줄
EXPECTED_STATUS = {
    " M mark-modified.txt",
    "A  mark-staged.txt",
    "?? mark-untracked.txt",
    "?? mark-dir/",
}
RUNS = {"저장소": 2, "밖": 1}
QUESTION = (
    "도구를 하나도 쓰지 마라. 파일을 읽지 말고, 이 세션의 시스템 프롬프트와 컨텍스트에 이미 실린 "
    "것만 보고 답한다. 거기에 git 상태(지금 브랜치, 바뀐 파일, 최근 커밋)를 적은 블록이 있으면 그 "
    "블록을 처음부터 끝까지 글자 그대로 옮겨라. 그런 블록이 없으면 '없음'이라고만 답하라."
)
COMMAND = [
    "claude",
    "-p",
    "--setting-sources",
    "project,local",
    "--strict-mcp-config",
    "--model",
    "sonnet",
    "--tools",
    "Read",
    "--output-format",
    "stream-json",
    "--verbose",
]
TIMEOUT = 600


def clean_env() -> dict[str, str]:
    """이 저장소를 가리키는 `GIT_*` 를 벗긴다. 남으면 임시 디렉터리의 git 이 이 저장소에 닿는다."""
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def git(*args: str, cwd: Path) -> str:
    done = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        env=clean_env(),
    )
    if done.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 실패({done.returncode}): {done.stderr.strip()}")
    return done.stdout


def write(folder: Path, name: str, text: str) -> None:
    path = folder / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def repo(path: Path) -> None:
    path.mkdir(parents=True)
    git("init", "-q", "-b", BRANCH, cwd=path)
    identity = ("-c", "user.name=probe", "-c", "user.email=probe@invalid")
    write(path, "mark-modified.txt", "처음\n")
    git("add", "mark-modified.txt", cwd=path)
    for number, subject in enumerate(COMMITS):
        write(path, "log.txt", f"{number}\n")
        git("add", "log.txt", cwd=path)
        git(*identity, "commit", "-qm", subject, cwd=path)
    write(path, "mark-modified.txt", "고침\n")
    write(path, "mark-staged.txt", "새 파일\n")
    git("add", "mark-staged.txt", cwd=path)
    write(path, "mark-untracked.txt", "추적하지 않음\n")
    write(path, "mark-dir/mark-inside.txt", "폴더 안\n")


def plain(path: Path) -> None:
    for name in FILES:
        write(path, name, "보통 폴더\n")


def remove_tree(root: Path) -> None:
    """임시 디렉터리를 지운다. 윈도에서는 `.git/objects` 의 읽기 전용 파일이 지우기를 막아, 쓰기를
    풀고 한 번 더 지운다."""

    def writable_retry(function: Callable[[str], object], path: str, _error: BaseException) -> None:
        os.chmod(path, stat.S_IWRITE)
        function(path)

    shutil.rmtree(root, onexc=writable_retry)


def run(cwd: Path) -> str:
    """회차 하나의 stream-json. 제한 시간을 넘기면 그때까지의 출력이라 결과가 없어 무효로 찍힌다."""
    executable = shutil.which(COMMAND[0]) or COMMAND[0]
    try:
        done = subprocess.run(
            [executable, *COMMAND[1:]],
            cwd=cwd,
            input=QUESTION.encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=TIMEOUT,
            env=clean_env(),
        )
    except subprocess.TimeoutExpired as expired:
        return (expired.stdout or b"").decode("utf-8", errors="replace")
    return done.stdout.decode("utf-8", errors="replace")


def facts(raw: str) -> tuple[int, str | None]:
    """도구 호출 수와 성공한 결과의 답. 결과가 없거나 오류면 답은 None 이다."""
    calls = 0
    answer: str | None = None
    for line in raw.splitlines():
        if not line.lstrip().startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:  # 제한 시간에 끊기면 마지막 줄이 잘린다
            continue
        if event.get("type") == "assistant":
            content = event.get("message", {}).get("content", [])
            calls += sum(1 for block in content if block.get("type") == "tool_use")
        if event.get("type") == "result":
            ok = event.get("subtype") == "success" and not event.get("is_error")
            answer = event.get("result") if ok else None
    return calls, answer


def main(out: Path) -> int:
    root = Path(tempfile.mkdtemp(prefix="canary-git-status-"))
    jobs = [(name, index) for name, times in RUNS.items() for index in range(1, times + 1)]
    try:
        places = {"저장소": root / "저장소", "밖": root / "밖"}
        repo(places["저장소"])
        plain(places["밖"])
        status = set(git("status", "--porcelain", cwd=places["저장소"]).splitlines())
        if status != EXPECTED_STATUS:
            print("저장소 갈래의 상태가 기대와 다르다:", *sorted(status), sep="\n  ")
            return 2
        out.mkdir(parents=True, exist_ok=True)
        with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
            raws = list(pool.map(lambda job: run(places[job[0]]), jobs))
    finally:
        try:
            remove_tree(root)
        except OSError as error:
            print(f"임시 디렉터리를 다 지우지 못했다: {root} ({error})")
    invalid = 0
    for (name, index), raw in zip(jobs, raws, strict=True):
        (out / f"{name}-{index}.jsonl").write_text(raw, encoding="utf-8", newline="\n")
        calls, answer = facts(raw)
        seen = [mark for mark in MARKS if answer and mark in answer]
        valid = calls == 0 and answer is not None
        invalid += not valid
        print(f"[{'측정' if valid else '무효'}] {name}-{index} 도구 {calls}회 · 표지 {seen}")
        print("  답:")
        for line in (answer or "결과 없음").splitlines():
            print(f"    {line}")
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
