"""커밋 검사: 이 브랜치의 변경이 티켓 하나를 가리키는지 본다(ADR 0037).

pre-commit 에 항목을 따로 두지 않고 `tools/run_checks.py` 의 `CHECKS` 에 든다(id `check-ticket`).
건너뛰기는 그 id 의 `SKIP` 이다. 작업 폴더의 저장소를 보고, git 을 부를 때 저장소를 가리키는 환경
변수를 벗기지 않는다. git 이 훅에 임시 색인(`GIT_INDEX_FILE`)을 주는 커밋(일부 파일만 커밋하는
`git commit <경로>`, 고친 추적 파일을 모두 싣는 `-a`)에서는 그 색인이 pre-commit 과 러너를 거쳐
여기까지 닿아야 그 커밋에 들 것을 보기 때문이다.
명세는 `.scratch/ticket-for-every-pr/spec.md` 의 "면제 모양", "커밋 검사", "전환"이다.

바뀐 파일(C). 이 브랜치와 `origin/main` 의 merge-base 에서 지금 색인까지의 차이다. 이름 바꾸기는
지운 것과 더한 것 둘로 센다(rename 감지를 끈다). 켜면 면제 밖의 파일을 면제 모양의 자리로 옮긴
변경이 새 경로 하나로만 보여 지나간다. 병합을 마무리하는 커밋(`MERGE_HEAD` 가 있다)이면
merge-base 를 `git merge-base origin/main HEAD <MERGE_HEAD>` 로 구한다. 충돌을 풀고 친 커밋의
pre-commit 에서 HEAD 는 아직 병합 전이라, HEAD 만으로 구하면 C 에 main 이 들여온 파일이 섞인다.
`MERGE_HEAD` 는 작업 트리 루트의 경로가 아니라 ref 이름으로 찾는다. 링크드 워크트리에서는 그
워크트리의 git 디렉터리에 있어, 루트의 `.git/MERGE_HEAD` 로 찾으면 놓친다
(`.scratch/ticket-for-every-pr/probes/merge_commit/`). 공통 조상이 없으면(고아 브랜치) 빈 트리에서
지금 색인까지다. 그 브랜치의 파일은 모두 그 브랜치가 들인 것이다.

판정. 아래 차례로 처음 맞는 것이다.

1. 분리 HEAD 이거나 브랜치가 main 이면 지난다. main 위의 커밋은 `tools/hook_git_main_commit.py` 가
   막는다.
2. `origin/main` 을 찾지 못하면 한 줄을 알리고 지난다. 원격 없이 연습하는 클론이다. HEAD 가 아직
   커밋을 가리키지 않아도(고아 브랜치의 첫 커밋) 한 줄을 알리고 지난다. 딴 자리가 없어 전환을
   가르지 못한다.
3. 규약 전에 연 브랜치면 한 줄을 알리고 지난다(아래 전환).
4. C 가 비었거나 모두 면제 모양이면 지난다.
5. 티켓 모양 브랜치는 그 티켓이 C 에 있고 색인에 남아 있어야 지난다. `feature/NN-<slug>` 는
   `.scratch/<어느 slug>/issues/NN-<slug>.md`, `chore/NNN-<slug>` 는
   `.scratch/harness/issues/NNN-<slug>.md` 다. 지운 티켓은 가리키지 않은 것으로 본다.
6. `docs/<slug>` 브랜치는 C 에 harness 티켓(`.scratch/harness/issues/NNN-<slug>.md`)이 하나라도
   있으면 지난다. 더한 것이든 고친 것이든 세고, 지운 것은 세지 않는다. 회고가 고침을 반영해 같은
   PR 에 쓴 티켓이다. 번호와 브랜치 이름은 맞대지 않는다. 그 폴더의 다른 파일(`README.md`, 하위
   폴더, `.md` 가 아닌 것)은 티켓이 아니다.
7. 그 밖은 막는다. 앱 워크트리 모양(`claude/<이름>`)과 `worktree-<이름>` 도 여기다.

면제 모양. 이 목록이 모양의 원천이다(`docs/agents/issue-tracker.md` 가 여기를 가리킨다). 기능의
설계·명세·티켓을 쓰는 PR 과 기록만 남기는 PR 이 쓰는 파일이다.

- `docs/journal/*.md`, `.scratch/retro-queue.md`
- `docs/adr/*.md`(색인 `README.md` 포함), `CONTEXT.md`, `.scratch/plan.md`, `docs/PRD.md`
- `docs/constitution/tech.md`, `docs/constitution/README.md`
- `.scratch/<slug>/spec.md`, `.scratch/<slug>/issues/*.md`, `.scratch/<slug>/probes/**`,
  `.scratch/<slug>/design/**`. 이 넷은 `<slug>` 가 `harness` 이면 면제가 아니다.
  `.scratch/harness/issues/` 는 하는 일의 티켓이 사는 자리이고 `.scratch/harness/probes/` 는 하네스
  도구를 받치는 측정이라 그 도구를 고치는 티켓에 든다.

`*` 는 경로 조각 하나이고 `**` 는 그 아래 전부다. 표에 없는 기능 폴더의 파일(`design.md`, `mock/`)은
면제가 아니다.

전환. 규약 전에 연 브랜치는 그 브랜치의 첫 자기 커밋의 부모 트리에 이 파일
(`tools/check_ticket.py`)이 없는 것으로 가른다. 첫 자기 커밋은 `origin/main` 에 없는 이 브랜치의
커밋 가운데 부모가 모두 `origin/main` 쪽에 있는 것이다. 커밋 날짜가 아니라 위상 순서로 가르는 것은
날짜가 rebase 와 시계에 따라 움직여서다. 그런 커밋이 여럿이면(다른 브랜치를 합친 브랜치) 모두의
부모 트리에 이 파일이 없을 때만 규약 전이다. 부모가 없는 첫 자기 커밋(고아 브랜치의 뿌리)은 딴
자리가 없어 그 커밋 자신의 트리로 가른다. `git checkout --orphan` 은 색인을 그대로 두어 뿌리 커밋이
이 파일을 든 채로 시작하고, 빈 트리로 보면 그 브랜치와 그 역사를 합친 브랜치가 끝까지 지난다. 자기
커밋이 아직 없으면 HEAD 를 그 자리로 본다.
merge-base 의 트리로 가르지 않는다. main 을 합치면 merge-base 가 앞으로 와서 그 순간 막힌다. 규약 전
브랜치를 검사가 든 main 으로 rebase 하면 첫 자기 커밋의 부모가 새 main 이 되어 판정을 받는다. 딴
자리가 옮겨진 것이라 그대로 두고, 막히면 막는 글의 길을 따른다.

막는 글(stderr). 면제 모양 밖의 바뀐 파일(앞의 열 개와 나머지 수), 브랜치가 티켓 모양이면 찾은 티켓
경로, 티켓을 쓸 자리와 번호를 받는 명령, 브랜치 이름을 바꾸는 명령, 규약 원천을 싣는다. 가리키는
티켓 파일이 디스크에는 있는데 C 에 없으면 그 티켓의 `Status:` 를 in-progress 로 고치고
스테이지하라는 알림을 더한다. 고치지 않은 것과 고치고 스테이지하지 않은 것을 가르지 않는다.
pre-commit 은 훅이 도는 동안 스테이지하지 않은 고침을 치워 둘이 커밋에서 갈리지 않는다.

러너에 둔 값. 러너는 한 검사가 실패해도 나머지를 끝까지 기다리므로, 막히는 커밋은 러너 한 바퀴 뒤에
글이 보이고 고친 뒤 한 바퀴를 더 돈다. 러너가 곧바로 멈추기를 들이면(대기열 192) 이 값은 사라진다.
변경을 마치고 손으로 친 러너에서도 이 검사가 지금 색인으로 돌아, 티켓을 스테이지하기 전이면 빨갛다.

종료 코드. 0 지남, 1 막음, 2 git 이 실패했다(띄우지 못함, 시간 초과, 판정에 쓰는 git 의 0 아닌
종료. 저장소가 아닌 폴더도 여기다).

못 보는 것.
- pre-commit 을 거치지 않은 커밋은 지난다. 훅을 깔지 않은 클론, `--no-verify`, 이 id 의 `SKIP`,
  충돌 없는 `git merge` 의 병합 커밋(이 저장소는 pre-merge-commit 훅을 깔지 않는다)이다.
- 티켓의 내용(수용 기준이 맞는지, `Status:` 가 무엇인지)은 보지 않는다.
- `docs/` 브랜치에 harness 티켓을 하나 쓰거나 이미 있는 harness 티켓을 고치기만 하고 회고 반영이
  아닌 일을 실어도 지난다.
- 고아 브랜치(`git checkout --orphan`)의 첫 커밋은 HEAD 가 없어 지난다(판정 2). 그 뒤의 커밋은
  뿌리 커밋의 트리로 전환을 가른다. 색인을 비우고(`git rm -r --cached .`) 만든 뿌리는 이 파일이 없어
  규약 전으로 지난다.
- 면제 모양만 고치는 PR 은 고침이 무엇이든 지난다(ADR 의 오타 고침, `CONTEXT.md` 의 말 고침).
- 지나는 갈래가 내는 한 줄(전환, `origin/main` 없음)은 러너가 통과한 검사의 출력을 찍지 않아
  커밋과 손으로 친 러너에서 보이지 않고, 이 검사를 바로 칠 때 보인다.
- 검사가 main 에 들어온 뒤에도 그 전의 main 에서 딴 브랜치(가져오지 않은 `origin/main` 에서 딴 것)는
  딴 자리의 트리에 이 파일이 없어 끝까지 지난다.
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

CHECK_PATH = "tools/check_ticket.py"
BASE = "refs/remotes/origin/main"
GIT_TIMEOUT = 60.0
SHOWN = 10

_EXEMPT_FILES = frozenset(
    {
        ".scratch/retro-queue.md",
        "CONTEXT.md",
        ".scratch/plan.md",
        "docs/PRD.md",
        "docs/constitution/tech.md",
        "docs/constitution/README.md",
    }
)
_HARNESS_ISSUES = ".scratch/harness/issues/"


class GitError(Exception):
    pass


@dataclass(frozen=True)
class Change:
    path: str
    deleted: bool


def _git(cwd: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", "-c", "core.quotepath=false", *args],
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=GIT_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        message = f"git {args[0]} 을 띄우지 못했거나 {GIT_TIMEOUT:.0f}초를 넘겼다: {error}"
        raise GitError(message) from error


def _out(cwd: Path, *args: str) -> str:
    result = _git(cwd, *args)
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise GitError(f"git {' '.join(args)} 가 {result.returncode} 로 끝났다: {message}")
    return result.stdout.decode("utf-8", "replace").strip()


def _maybe(cwd: Path, *args: str) -> str | None:
    """성공하면 출력, 아니면 None. 있는지 묻는 git 에 쓴다."""
    result = _git(cwd, *args)
    if result.returncode != 0:
        return None
    return result.stdout.decode("utf-8", "replace").strip()


def exempt(path: str) -> bool:
    """면제 모양인가. 모양은 모듈 독스트링이 원천이다."""
    if path in _EXEMPT_FILES:
        return True
    parts = path.split("/")
    if len(parts) == 3 and parts[0] == "docs" and parts[1] in ("journal", "adr"):
        return parts[2].endswith(".md")
    if len(parts) >= 3 and parts[0] == ".scratch" and parts[1] != "harness":
        rest = parts[2:]
        if rest == ["spec.md"]:
            return True
        if len(rest) == 2 and rest[0] == "issues":
            return rest[1].endswith(".md")
        return len(rest) >= 2 and rest[0] in ("probes", "design")
    return False


def ticket_stem(branch: str) -> tuple[str, str] | None:
    """티켓 모양 브랜치면 (갈래, stem). 갈래는 `feature` 나 `chore` 다."""
    kind, _, stem = branch.partition("/")
    digits = {"feature": 2, "chore": 3}.get(kind)
    if digits is None or "/" in stem:
        return None
    number, dash, slug = stem.partition("-")
    if len(number) != digits or not (number.isascii() and number.isdigit()) or not dash or not slug:
        return None
    return kind, stem


def is_harness_ticket(path: str) -> bool:
    """`.scratch/harness/issues/NNN-<slug>.md` 인가. 이름은 chore 브랜치의 stem 과 같은 모양이다."""
    folder, _, name = path.rpartition("/")
    return (
        f"{folder}/" == _HARNESS_ISSUES
        and name.endswith(".md")
        and ticket_stem(f"chore/{name.removesuffix('.md')}") is not None
    )


def points_at(kind: str, stem: str, path: str) -> bool:
    """이 경로가 그 브랜치가 가리키는 티켓인가."""
    if kind == "chore":
        return path == f"{_HARNESS_ISSUES}{stem}.md"
    parts = path.split("/")
    return (
        len(parts) == 4
        and parts[0] == ".scratch"
        and parts[2] == "issues"
        and parts[3] == f"{stem}.md"
    )


def tickets_on_disk(root: Path, kind: str, stem: str) -> list[str]:
    """작업 트리에 있는, 그 브랜치가 가리키는 티켓 파일."""
    pattern = f"harness/issues/{stem}.md" if kind == "chore" else f"*/issues/{stem}.md"
    found = sorted((root / ".scratch").glob(pattern))
    return [p.relative_to(root).as_posix() for p in found if p.is_file()]


def merge_head(cwd: Path) -> str | None:
    """병합을 마무리하는 중이면 MERGE_HEAD 의 커밋. 링크드 워크트리에서도 ref 이름으로 찾는다."""
    return _maybe(cwd, "rev-parse", "-q", "--verify", "MERGE_HEAD^{commit}")


def changes(cwd: Path, base: str) -> list[Change]:
    """merge-base 에서 지금 색인까지. 이름 바꾸기는 지운 것과 더한 것 둘이다."""
    result = _git(cwd, "diff", "--cached", "--name-status", "--no-renames", "-z", base, "--")
    if result.returncode != 0:
        raise GitError(f"git diff 가 {result.returncode} 로 끝났다")
    fields = result.stdout.decode("utf-8", "replace").split("\0")
    return [
        Change(path, status == "D")
        for status, path in zip(fields[0::2], fields[1::2], strict=False)
        if path
    ]


def merge_base(cwd: Path, heads: list[str]) -> str:
    """C 를 셀 자리. 공통 조상이 없으면(`merge-base` 가 1 로 끝난다) 빈 트리다."""
    result = _git(cwd, "merge-base", BASE, *heads)
    if result.returncode == 0:
        return result.stdout.decode("utf-8", "replace").strip()
    if result.returncode == 1:
        return _out(cwd, "hash-object", "-t", "tree", "--stdin")
    message = result.stderr.decode("utf-8", "replace").strip()
    raise GitError(f"git merge-base 가 {result.returncode} 로 끝났다: {message}")


def _has_check(cwd: Path, commit: str) -> bool:
    return _git(cwd, "cat-file", "-e", f"{commit}:{CHECK_PATH}").returncode == 0


def before_convention(cwd: Path) -> bool:
    """브랜치를 딴 자리(첫 자기 커밋의 부모, 자기 커밋이 없으면 HEAD)의 트리에 이 검사가 없는가."""
    listing = _out(cwd, "rev-list", "--parents", "HEAD", "--not", BASE)
    own: dict[str, list[str]] = {}
    for line in listing.splitlines():
        commit, *parents = line.split()
        own[commit] = parents
    if not own:
        return not _has_check(cwd, "HEAD")
    firsts = [commit for commit, parents in own.items() if not any(p in own for p in parents)]
    # 부모 없는 자기 커밋(고아 브랜치의 뿌리)은 딴 자리가 없어 그 커밋 자신의 트리로 가른다
    return all(not _has_check(cwd, own[commit][0] if own[commit] else commit) for commit in firsts)


@dataclass(frozen=True)
class Verdict:
    passed: bool
    message: str


def _blocked(root: Path, branch: str, changed: list[Change], outside: list[str]) -> str:
    lines = [f"check-ticket: 브랜치 {branch} 의 변경이 티켓을 가리키지 않아 커밋을 막았다."]
    lines.append(f"면제 모양 밖의 바뀐 파일 {len(outside)}개:")
    lines += [f"  {path}" for path in outside[:SHOWN]]
    if len(outside) > SHOWN:
        lines.append(f"  … 그 밖에 {len(outside) - SHOWN}개")
    stem = ticket_stem(branch)
    if stem is not None:
        kind, name = stem
        on_disk = tickets_on_disk(root, kind, name)
        expected = (
            f"{_HARNESS_ISSUES}{name}.md"
            if kind == "chore"
            else f".scratch/<slug>/issues/{name}.md"
        )
        lines.append(f"이 브랜치가 가리키는 티켓: {', '.join(on_disk) or expected}")
        in_commit = {c.path for c in changed if not c.deleted}
        for path in on_disk:
            if path not in in_commit:
                lines.append(
                    f"알림: {path} 가 디스크에는 있지만 이 커밋에 들지 않는다. 그 파일의"
                    " `Status:` 를 in-progress 로 고치고(이미 고쳤으면 그대로)"
                    f" `git add {path}` 로 스테이지한다."
                )
    lines += [
        "할 일:",
        "  1. 티켓을 쓴다. 기능의 일이면 그 기능 폴더 .scratch/<slug>/issues/NN-<slug>.md, 그 밖의"
        " 하네스 일과 작은 문서 고침이면 .scratch/harness/issues/NNN-<slug>.md 다. 번호는"
        " `uv run python tools/sibling_overlap.py` 가 알린다.",
        "  2. 브랜치 이름을 티켓 파일 이름의 stem 에 맞춘다: `git branch -m <새 이름>`"
        "(feature/NN-<slug> 나 chore/NNN-<slug>). 이미 푸시했으면 새 이름으로 푸시하고 옛 원격"
        " 브랜치를 지운다. 열린 PR 이 있으면 사람에게 묻는다.",
        "규약 원천: docs/agents/issue-tracker.md",
    ]
    return "\n".join(lines)


def current_branch(cwd: Path) -> str | None:
    """브랜치 이름, 분리 HEAD 면 None. `symbolic-ref -q` 는 분리 HEAD 에서 1, 저장소가 아니거나
    git 이 실패하면 128 로 끝나므로 1 만 분리 HEAD 로 읽는다."""
    result = _git(cwd, "symbolic-ref", "-q", "--short", "HEAD")
    if result.returncode == 1:
        return None
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise GitError(f"git symbolic-ref 가 {result.returncode} 로 끝났다: {message}")
    return result.stdout.decode("utf-8", "replace").strip()


def judge(cwd: Path) -> Verdict:
    branch = current_branch(cwd)
    if branch is None or branch == "main":
        return Verdict(passed=True, message="")
    if _maybe(cwd, "rev-parse", "-q", "--verify", f"{BASE}^{{commit}}") is None:
        return Verdict(
            passed=True, message="check-ticket: origin/main 을 찾지 못해 판정하지 않고 지난다."
        )
    if _maybe(cwd, "rev-parse", "-q", "--verify", "HEAD^{commit}") is None:
        return Verdict(
            passed=True, message="check-ticket: HEAD 가 아직 없어(첫 커밋) 판정하지 않고 지난다."
        )
    if before_convention(cwd):
        return Verdict(
            passed=True,
            message=f"check-ticket: 규약 전에 연 브랜치({branch})라 판정하지 않고 지난다.",
        )
    heads = ["HEAD"]
    merging = merge_head(cwd)
    if merging is not None:
        heads.append(merging)
    changed = changes(cwd, merge_base(cwd, heads))
    outside = [c.path for c in changed if not exempt(c.path)]
    if not outside:
        return Verdict(passed=True, message="")
    present = [c.path for c in changed if not c.deleted]
    stem = ticket_stem(branch)
    if stem is not None and any(points_at(*stem, path) for path in present):
        return Verdict(passed=True, message="")
    if branch.startswith("docs/") and any(is_harness_ticket(path) for path in present):
        return Verdict(passed=True, message="")
    root = Path(_out(cwd, "rev-parse", "--show-toplevel"))
    return Verdict(passed=False, message=_blocked(root, branch, changed, outside))


def main(argv: list[str]) -> int:
    cwd = Path(argv[1]) if len(argv) > 1 else Path.cwd()
    try:
        verdict = judge(cwd)
    except GitError as error:
        sys.stderr.buffer.write(f"check-ticket: {error}\n".encode())
        return 2
    if verdict.passed:
        if verdict.message:
            sys.stdout.buffer.write(f"{verdict.message}\n".encode())
        return 0
    sys.stderr.buffer.write(f"{verdict.message}\n".encode())
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
