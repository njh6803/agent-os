"""주 체크아웃 안의 워크트리에서 띄운 `claude -p` 에 상위 폴더의 `CLAUDE.md` 도 실리는지 잰다.

대기열 171 의 전제다. `docs/constitution/operations.md` 환경 규약 상세의 대조군 안내와 모드 표,
`tools/canary.py` 독스트링이 근거로 든다. 이 저장소의 워크트리가 주 체크아웃 안
(`.claude/worktrees/`)에 있는 모양을 임시 디렉터리에 흉내 낸다. 폴더마다 `CLAUDE.md` 의 표지
낱말이 다르다.
- `뿌리/`: 임시 디렉터리 자체. 별빛두더지. git 저장소가 아니다.
- `뿌리/바깥/`: git 저장소. 노을고래.
- `뿌리/바깥/.claude/worktrees/안쪽/`: `바깥` 의 워크트리. 새벽수달.
- `뿌리/바깥/둥지/`: `.claude/` 밖에 꺼낸 `바깥` 의 워크트리. 은빛참새. 경로가 아니라 git 루트에서
  멈추는지 가른다.
- `뿌리/바깥/빈칸/`: `바깥` 의 워크트리인데 꺼낸 뒤 자기 `CLAUDE.md` 를 지운다. 표지 낱말이 없다.
  `안쪽`·`둥지` 에서 `바깥` 의 것이 빠진 까닭이 주 워크트리 루트를 건너뛰어서인지, 같은 자리의
  자기 파일이 가려서인지 가른다.
- `뿌리/바깥/하위/`: `바깥` 안의 보통 폴더(워크트리가 아니다). 가을사슴. 상위 파일이 실리면 모델이
  그것을 옮기는지 보는 양성 대조다.
- `뿌리/옆/`: `바깥` 밖의 git 저장소. 한낮여우.
워크트리는 꺼낸 뒤 `CLAUDE.md` 를 바꾼다(커밋하지 않는다. 세션은 디스크의 파일을 읽는다).

갈래마다 카나리아 명령(`--setting-sources project,local --strict-mcp-config --model sonnet
--tools Read`)으로 띄워, 도구를 쓰지 말고 실린 프로젝트 지시마다 경로와 표지 낱말을 옮기게 한다.
회차마다 답에 든 표지 낱말과 도구 호출 수를 찍는다. 도구를 불렀으면 답이 파일을 읽은 데서 왔을 수
있어 그 회차는 측정이 아니다. 기대를 단언하지 않고 본 것을 찍는다.

임시 디렉터리(`%TEMP%`)의 상위 폴더에 `CLAUDE.md` 가 있으면 섞이므로 돌리지 않고 2 로 끝난다.
회차마다 stream-json 원본(`.jsonl`)을 출력 디렉터리에 남기고 임시 디렉터리는 끝에 지운다.
돌리는 법: `uv run python .scratch/harness/probes/claude_md_parent.py <출력 디렉터리>`.
`claude` CLI 와 인증이 든다. 회차마다 sonnet 호출이 하나이고 모두 여덟이다. 종료 코드: 0 모든
회차가 측정이 됐다, 1 도구를 불렀거나 세션이 답을 내지 못한(제한 시간 600초를 넘긴 것 포함) 회차가
있다, 2 임시 디렉터리의 상위 폴더에 `CLAUDE.md` 가 있다.
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

MARKS = {
    "뿌리": "별빛두더지",
    "바깥": "노을고래",
    "안쪽": "새벽수달",
    "둥지": "은빛참새",
    "하위": "가을사슴",
    "옆": "한낮여우",
}
RUNS = {"안쪽": 2, "둥지": 1, "빈칸": 1, "하위": 2, "바깥": 1, "옆": 1}
QUESTION = (
    "도구를 하나도 쓰지 마라. 파일을 읽지 말고, 이 세션에 이미 실린 프로젝트 지시(CLAUDE.md)만 "
    "보고 답한다. 실린 프로젝트 지시 파일마다 한 줄씩, 그 파일의 경로와 그 파일이 적은 표지 낱말을 "
    "글자 그대로 옮겨라. 실린 프로젝트 지시가 하나도 없으면 '없음'이라고만 답하라."
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


def git(*args: str, cwd: Path) -> None:
    done = subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=False, env=clean_env()
    )
    if done.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 실패({done.returncode}): {done.stderr.strip()}")


def write_instruction(folder: Path, name: str) -> None:
    text = f"# {name} 지시\n\n이 저장소의 표지 낱말은 {MARKS[name]}다.\n"
    (folder / "CLAUDE.md").write_text(text, encoding="utf-8")


def repo(path: Path, name: str) -> None:
    path.mkdir(parents=True)
    git("init", "-q", "-b", "main", cwd=path)
    write_instruction(path, name)
    git("add", "CLAUDE.md", cwd=path)
    identity = ("-c", "user.name=probe", "-c", "user.email=probe@invalid")
    git(*identity, "commit", "-qm", "init", cwd=path)


def worktree(outer: Path, path: Path, name: str) -> None:
    git("worktree", "add", "-q", "--detach", str(path), cwd=outer)
    write_instruction(path, name)


def layout(root: Path) -> dict[str, Path]:
    write_instruction(root, "뿌리")
    outer = root / "바깥"
    repo(outer, "바깥")
    inner = outer / ".claude" / "worktrees" / "안쪽"
    worktree(outer, inner, "안쪽")
    nest = outer / "둥지"
    worktree(outer, nest, "둥지")
    empty = outer / "빈칸"
    git("worktree", "add", "-q", "--detach", str(empty), cwd=outer)
    (empty / "CLAUDE.md").unlink()
    sub = outer / "하위"
    sub.mkdir()
    write_instruction(sub, "하위")
    side = root / "옆"
    repo(side, "옆")
    return {"안쪽": inner, "둥지": nest, "빈칸": empty, "하위": sub, "바깥": outer, "옆": side}


def remove_tree(root: Path) -> None:
    """임시 디렉터리를 지운다. 윈도에서는 `.git/objects` 의 읽기 전용 파일이 지우기를 막아, 쓰기를
    풀고 한 번 더 지운다. 그래도 남으면 경로를 찍는다(남은 것에는 `.git` 만 있다)."""

    def writable_retry(function: Callable[[str], object], path: str, _error: BaseException) -> None:
        os.chmod(path, stat.S_IWRITE)
        function(path)

    shutil.rmtree(root, onexc=writable_retry)


def ancestors_with_instructions(path: Path) -> list[Path]:
    return [parent / "CLAUDE.md" for parent in path.parents if (parent / "CLAUDE.md").is_file()]


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
    temp = Path(tempfile.gettempdir())
    stray = ancestors_with_instructions(temp / "x")
    if stray:
        print("임시 디렉터리의 상위 폴더에 CLAUDE.md 가 있어 섞인다:", *stray, sep="\n  ")
        return 2
    out.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="claude-md-parent-"))
    jobs = [(name, index) for name, times in RUNS.items() for index in range(1, times + 1)]
    try:
        places = layout(root)
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
        seen = [mark for mark in MARKS.values() if answer and mark in answer]
        valid = calls == 0 and answer is not None
        invalid += not valid
        print(f"[{'측정' if valid else '무효'}] {name}-{index} 도구 {calls}회 · 표지 {seen}")
        print("  답:", " ".join((answer or "결과 없음").split()))
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
