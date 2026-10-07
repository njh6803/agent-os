"""커밋 직전에 이 브랜치가 새로 매긴 번호와 고친 파일을 형제와 대조한다(대기열 48·115).

형제는 셋이다. 이미 병합된 `origin/main`, 아직 병합되지 않은 열린 PR의 head,
아직 커밋되지 않은 같은 저장소의 다른 워크트리다. `origin/main`과 워크트리만 보던 손 대조는
아직 열린 PR이 먼저 가져간 번호와 다섯 번 부딪혔다(대기열 115). 클라우드 세션에서는 형제가
워크트리가 아니라 다른 세션의 열린 PR이라 손 대조가 보는 것이 main뿐이다(일지 2026-10-07-09).

번호는 넷이고, 형제가 새로 매긴 번호를 이 브랜치도 새로 매겼으면 겹침이다.

- 일지 순번: `docs/journal/YYYY-MM-DD-NN-*.md`의 `YYYY-MM-DD-NN`.
  같은 순번에 다른 파일이면 겹침이다.
- ADR 번호: `docs/adr/NNNN-*.md`의 `NNNN`. 같은 번호에 다른 파일이면 겹침이다.
- 대기열 행: `.scratch/retro-queue.md`의 `| N |`로 시작하는 행.
  같은 번호에 다른 행이면 겹침이다.
- 헌법 판: `docs/constitution/README.md`의 `**Version**: X.Y.Z`.
  둘이 같은 판으로 올렸으면 겹침이다.

"새로"는 이 브랜치와 `origin/main`의 merge-base에 없다는 뜻이다. 열린 PR과 워크트리는
그 merge-base와 `origin/main` 어디에도 없는 번호만 그 형제의 것으로 본다. 그래서 main이
이미 가진 번호는 main 줄에만 한 번 나온다. 이 브랜치는 작업 트리(커밋하지 않은 변경과
미추적 파일)를 읽는다. merge-base에서 네 자리 가운데 하나라도 비면 경로가 어긋난 것으로 보고
2로 끝난다(조용히 겹침 없음이 되지 않게).

열린 PR은 GitHub REST(`gh api repos/<owner>/<repo>/pulls?state=open`)로 읽는다. `origin`이
github.com이 아니거나 `gh`가 없거나 실패하면 `refs/pull/N/merge`가 있는 PR을 열린 것으로 본다.
2026-10-07에 이 클라우드 컨테이너에서 손으로 봤다. `gh pr list`는 GraphQL이 막혀 HTTP 403이었고
`gh api`의 REST는 열렸다. `git ls-remote origin 'refs/pull/*'`에는 PR 160개의 head ref와 merge
ref 하나(열린 #158)가 있었고, #158은 main과 충돌한 뒤에도(`mergeable_state: dirty`) 옛 base의
merge ref가 남아 있었다. 로컬 Windows에서는 아직 돌리지 않았다. head가 이 브랜치의 HEAD에 이미
들었거나 원격의 같은 이름 브랜치와 같은 PR은 이 브랜치 자신의 PR이라 형제가 아니다(앞의 것은
푸시 전의 새 커밋, 뒤의 것은 amend·rebase 뒤 아직 밀지 않은 때).

함께 고친 파일도 알린다. 이 브랜치가 merge-base 뒤에 고친 파일과 형제가 자기 merge-base
뒤에 고친 파일이 겹치면, 나중에 병합하는 쪽에서 글자 충돌이 날 수 있다. 이것은 종료
코드를 바꾸지 않는다. 형제와 main의 merge-base가 이 클론에 없으면(얕은 클론) 그 형제의 고친
파일만 "알 수 없다"로 두고 번호는 그대로 대조한다.

쓰임: `uv run python tools/sibling_overlap.py [저장소 안의 경로]`. 먼저 `origin`의 main과
열린 PR의 head를 fetch한다(`origin/main`이 움직인다). 종료 코드는 번호 겹침이 없으면 0,
있으면 1, 대조를 끝내지 못하면(git 실패, 원격을 읽지 못함, 번호의 자리가 빔) 2다. 겹치면
이 브랜치가 비켜 간다. 출력의 "옮길 번호"는 겹친 종류(일지는 날짜마다)의 이 브랜치 새 번호
전부를 차례를 지켜 형제들의 최대값 뒤로 붙인 것이다(일지 2026-10-07-09가 03~07을 05~09로
옮긴 모양). 헌법 판은 고르지 않는다. 올림의 종류(major·minor·patch)는 바뀐 내용이 정한다.

못 보는 것:
- merge ref로 가릴 때(`gh`를 쓰지 못할 때), 열 때부터 main과 충돌한 PR. 웹 검색 요약이
  그런 PR에는 merge ref가 없고 merge ref는 GitHub이 문서로 약속하지 않은 기능이라고 했다
  (drone 포럼 글, 원문은 이 컨테이너의 egress가 막아 열지 못했다). 재지 않았다. 재려면 이
  저장소에 충돌하는 PR을 하나 열어야 한다.
- 푸시했지만 PR을 열지 않은 브랜치, 다른 기계·다른 클라우드 세션의 커밋하지 않은 변경.
- main을 이미 들여 작업 트리 안에서 같은 번호가 둘이 된 것. 둘 다 merge-base에 있거나 merge-base에
  든 번호와 같아 "새로"가 아니다. 일지는 `tests/test_journal_names.py`, ADR은
  `tools/check_adr_pointers.py`가 본다.
- 번호를 가리키는 참조("일지 03", "대기열 141" 같은 본문의 인용). 번호를 옮길 때 참조를
  고치는 범위는 `.claude/rules/adr.md`의 번호 항목과 같다.
- 함께 고친 파일의 어느 줄이 겹치는지. 파일 이름만 견준다.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol

REMOTE = "origin"
BRANCH = "main"
MAIN = f"{REMOTE}/{BRANCH}"
JOURNAL_DIR = "docs/journal"
ADR_DIR = "docs/adr"
QUEUE = ".scratch/retro-queue.md"
CONSTITUTION = "docs/constitution/README.md"

JOURNAL_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2}-\d{2})-.+\.md$")
ADR_NAME = re.compile(r"^(\d{4})-.+\.md$")
QUEUE_ROW = re.compile(r"^\| (\d+) \|")
VERSION = re.compile(r"\*\*Version\*\*: (\d+\.\d+\.\d+)")
PULL_REF = re.compile(r"^refs/pull/(\d+)/(head|merge)$")
GITHUB_URL = re.compile(r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$")
GH_PULL = re.compile(r"^(\d+) ([0-9a-f]{40})$")
GH_JQ = r'.[] | "\(.number) \(.head.sha)"'

NETWORK_TIMEOUT = 120
LOCAL_TIMEOUT = 30
ROW_WIDTH = 40
SHALLOW_HINT = "얕은 클론이면 `git fetch --unshallow origin` 뒤 다시 친다"


class SurveyError(Exception):
    """대조를 끝내지 못했다. git 이 실패했거나, 원격을 읽지 못했거나, 번호의 자리가 비었다."""


@dataclass(frozen=True)
class Numbers:
    journals: dict[str, str]  # 순번 → 파일 이름
    adrs: dict[str, str]  # 번호 → 파일 이름
    rows: dict[int, str]  # 행 번호 → 행
    version: str | None


@dataclass(frozen=True)
class Clash:
    kind: str
    key: str
    ours: str
    theirs: str


@dataclass(frozen=True)
class Move:
    kind: str
    old: str
    new: str


@dataclass(frozen=True)
class Sibling:
    label: str
    commit: str
    numbers: Numbers  # 이 형제만 새로 매긴 번호
    changed: frozenset[str] | None  # None 이면 merge-base 가 없어 알 수 없다


@dataclass(frozen=True)
class Survey:
    ours: Numbers  # 이 브랜치가 새로 매긴 번호
    changed: frozenset[str]
    siblings: list[Sibling]
    taken: list[Numbers]  # 이 브랜치 밖의 모든 자리(merge-base, main, 형제)의 번호 전체
    pulls_from: str  # 열린 PR 을 읽은 길(FROM_GH 또는 FROM_MERGE_REF)


def read_numbers(
    journal_names: list[str], adr_names: list[str], queue: str, constitution: str
) -> Numbers:
    journals = {m.group(1): name for name in journal_names if (m := JOURNAL_NAME.match(name))}
    adrs = {m.group(1): name for name in adr_names if (m := ADR_NAME.match(name))}
    rows = {int(m.group(1)): line for line in queue.splitlines() if (m := QUEUE_ROW.match(line))}
    version = VERSION.search(constitution)
    return Numbers(journals, adrs, rows, version.group(1) if version else None)


def fresh(numbers: Numbers, *known: Numbers) -> Numbers:
    """`known` 어디에도 없는 번호만 남긴다."""
    version = numbers.version
    if version is not None and any(version == other.version for other in known):
        version = None
    journals = {
        k: v for k, v in numbers.journals.items() if all(k not in n.journals for n in known)
    }
    adrs = {k: v for k, v in numbers.adrs.items() if all(k not in n.adrs for n in known)}
    rows = {k: v for k, v in numbers.rows.items() if all(k not in n.rows for n in known)}
    return Numbers(journals, adrs, rows, version)


def clashes(ours: Numbers, theirs: Numbers) -> list[Clash]:
    """둘 다 새로 매긴 번호 가운데 같은 번호를 다른 것에 쓴 것.

    같은 파일·같은 행은 겹침이 아니라 공유한 이력이다(쌓아 올린 브랜치).
    """
    found: list[Clash] = []
    named = (("일지", ours.journals, theirs.journals), ("ADR", ours.adrs, theirs.adrs))
    for kind, mine, other in named:
        for key in sorted(mine.keys() & other.keys()):
            if mine[key] != other[key]:
                found.append(Clash(kind, key, mine[key], other[key]))
    for row in sorted(ours.rows.keys() & theirs.rows.keys()):
        if ours.rows[row] != theirs.rows[row]:
            found.append(Clash("대기열", str(row), ours.rows[row], theirs.rows[row]))
    if ours.version is not None and ours.version == theirs.version:
        found.append(Clash("헌법", ours.version, ours.version, ours.version))
    return found


def _shift(olds: list[int], top: int) -> list[tuple[int, int]]:
    """`olds` 를 차례대로 `top` 뒤에 붙인다. 자리가 그대로인 것은 뺀다."""
    pairs = [(old, top + 1 + i) for i, old in enumerate(sorted(olds))]
    return [(old, new) for old, new in pairs if old != new]


def moves(ours: Numbers, taken: list[Numbers], found: list[Clash]) -> list[Move]:
    """겹친 종류(일지는 날짜마다)의 이 브랜치 새 번호 전부를 형제들의 최대값 뒤로 옮긴다.

    겹친 번호만 옮기면 이 브랜치의 다른 새 번호와 부딪히거나 일지의 차례가 뒤집힌다.
    헌법 판은 고르지 않는다.
    """
    kinds = {clash.kind for clash in found}
    result: list[Move] = []
    for date in sorted({clash.key[:10] for clash in found if clash.kind == "일지"}):
        olds = [int(key[11:]) for key in ours.journals if key[:10] == date]
        top = max((int(k[11:]) for n in taken for k in n.journals if k[:10] == date), default=0)
        result += [Move("일지", f"{date}-{a:02d}", f"{date}-{b:02d}") for a, b in _shift(olds, top)]
    if "ADR" in kinds:
        top = max((int(k) for n in taken for k in n.adrs), default=0)
        olds = [int(key) for key in ours.adrs]
        result += [Move("ADR", f"{a:04d}", f"{b:04d}") for a, b in _shift(olds, top)]
    if "대기열" in kinds:
        top = max((k for n in taken for k in n.rows), default=0)
        result += [Move("대기열", str(a), str(b)) for a, b in _shift(list(ours.rows), top)]
    return result


def github_repo(url: str) -> tuple[str, str] | None:
    """원격 URL 이 github.com 의 것이면 (owner, repo)."""
    match = GITHUB_URL.search(url.strip())
    return (match.group(1), match.group(2)) if match else None


def gh_pulls(text: str) -> dict[int, str]:
    """`gh api … --jq` 가 낸 "번호 head" 줄에서 열린 PR 의 번호 → head 커밋."""
    found: dict[int, str] = {}
    for line in text.splitlines():
        match = GH_PULL.match(line.strip())
        if match:
            found[int(match.group(1))] = match.group(2)
    return dict(sorted(found.items()))


def open_pulls(listing: str) -> dict[int, str]:
    """`git ls-remote` 의 `refs/pull/*` 줄에서 merge ref 가 있는 PR 의 번호 → head 커밋."""
    heads: dict[int, str] = {}
    merges: set[int] = set()
    for line in listing.splitlines():
        sha, _, ref = line.partition("\t")
        match = PULL_REF.match(ref.strip())
        if match is None:
            continue
        number = int(match.group(1))
        if match.group(2) == "head":
            heads[number] = sha.strip()
        else:
            merges.add(number)
    return {number: heads[number] for number in sorted(merges) if number in heads}


def remote_head(listing: str, branch: str) -> str | None:
    """`git ls-remote` 줄에서 원격 브랜치 `branch` 의 커밋."""
    for line in listing.splitlines():
        sha, _, ref = line.partition("\t")
        if ref.strip() == f"refs/heads/{branch}":
            return sha.strip()
    return None


def worktrees(porcelain: str) -> list[tuple[str, str]]:
    """`git worktree list --porcelain` 에서 (경로, HEAD). bare 와 사라진(prunable) 것은 뺀다."""
    found: list[tuple[str, str]] = []
    for block in re.split(r"\n\s*\n", porcelain.strip()):
        fields: dict[str, str] = {}
        for line in block.splitlines():
            name, _, value = line.partition(" ")
            fields[name] = value
        if "bare" in fields or "prunable" in fields:
            continue
        if "worktree" in fields and "HEAD" in fields:
            found.append((fields["worktree"], fields["HEAD"]))
    return found


def _run(command: list[str], cwd: Path, timeout: float) -> subprocess.CompletedProcess[str] | None:
    """명령을 띄운다. 띄우지 못하거나 시간을 넘기면 None."""
    try:
        return subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None


def _git_result(
    cwd: Path, args: tuple[str, ...], timeout: float
) -> subprocess.CompletedProcess[str]:
    result = _run(["git", "-c", "core.quotepath=false", *args], cwd, timeout)
    if result is None:
        raise SurveyError(f"git {args[0]} 을 띄우지 못했거나 {timeout}초를 넘겼다")
    return result


def git(cwd: Path, *args: str, timeout: float = LOCAL_TIMEOUT) -> str:
    result = _git_result(cwd, args, timeout)
    if result.returncode != 0:
        raise SurveyError(f"git {args[0]} (종료 {result.returncode}): {result.stderr.strip()}")
    return result.stdout


def is_ancestor(root: Path, commit: str, of: str) -> bool:
    result = _git_result(root, ("merge-base", "--is-ancestor", commit, of), LOCAL_TIMEOUT)
    if result.returncode > 1:
        raise SurveyError(f"git merge-base --is-ancestor: {result.stderr.strip()}")
    return result.returncode == 0


def merge_base(root: Path, one: str, other: str) -> str | None:
    """두 커밋의 merge-base. 이 클론에 공통 조상이 없으면(얕은 클론) None."""
    result = _git_result(root, ("merge-base", one, other), LOCAL_TIMEOUT)
    if result.returncode == 1:
        return None
    if result.returncode != 0:
        raise SurveyError(f"git merge-base: {result.stderr.strip()}")
    return result.stdout.strip()


def current_branch(root: Path) -> str | None:
    """지금 브랜치의 이름. detached HEAD 면 None."""
    result = _git_result(root, ("symbolic-ref", "--quiet", "--short", "HEAD"), LOCAL_TIMEOUT)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def gh_listing(root: Path, owner: str, repo: str) -> str | None:
    """`gh api` 로 읽은 열린 PR 의 "번호 head" 줄. gh 가 없거나 실패하면 None."""
    gh = shutil.which("gh")
    if gh is None:
        return None
    endpoint = f"repos/{owner}/{repo}/pulls?state=open&per_page=100"
    result = _run([gh, "api", endpoint, "--paginate", "--jq", GH_JQ], root, NETWORK_TIMEOUT)
    return result.stdout if result is not None and result.returncode == 0 else None


class Snapshot(Protocol):
    def names(self, directory: str) -> list[str]: ...

    def text(self, path: str) -> str: ...


@dataclass(frozen=True)
class Tree:
    """커밋 하나의 트리."""

    root: Path
    commit: str

    def names(self, directory: str) -> list[str]:
        listing = git(self.root, "ls-tree", "--name-only", self.commit, "--", f"{directory}/")
        return [PurePosixPath(line).name for line in listing.splitlines()]

    def text(self, path: str) -> str:
        if not git(self.root, "ls-tree", "--name-only", self.commit, "--", path).strip():
            return ""  # 그 커밋에 파일이 없다
        return git(self.root, "show", f"{self.commit}:{path}")


@dataclass(frozen=True)
class Disk:
    """작업 트리. 커밋하지 않은 변경과 미추적 파일까지 든다."""

    root: Path

    def names(self, directory: str) -> list[str]:
        folder = self.root / directory
        if not folder.is_dir():
            return []
        return sorted(path.name for path in folder.iterdir() if path.is_file())

    def text(self, path: str) -> str:
        file = self.root / path
        return file.read_text(encoding="utf-8", errors="replace") if file.is_file() else ""


def numbers_of(snapshot: Snapshot) -> Numbers:
    return read_numbers(
        snapshot.names(JOURNAL_DIR),
        snapshot.names(ADR_DIR),
        snapshot.text(QUEUE),
        snapshot.text(CONSTITUTION),
    )


def empty_places(numbers: Numbers) -> list[str]:
    places = (
        (JOURNAL_DIR, not numbers.journals),
        (ADR_DIR, not numbers.adrs),
        (QUEUE, not numbers.rows),
        (CONSTITUTION, numbers.version is None),
    )
    return [place for place, empty in places if empty]


def _lines(text: str) -> frozenset[str]:
    return frozenset(line for line in text.splitlines() if line)


def _worktree_changes(path: Path, since: str) -> frozenset[str]:
    """작업 트리가 `since` 뒤에 고친 파일. 미추적 파일을 더한다."""
    tracked = git(path, "diff", "--name-only", since)
    untracked = git(path, "ls-files", "--others", "--exclude-standard")
    return _lines(tracked) | _lines(untracked)


FROM_GH = "gh api"
FROM_MERGE_REF = "merge ref"


@dataclass(frozen=True)
class Remote:
    """원격에서 읽은 것. 열린 PR(번호 → head), 그것을 읽은 길, 이 브랜치의 원격 커밋."""

    pulls: dict[int, str]
    pulls_from: str  # FROM_GH 또는 FROM_MERGE_REF
    own_head: str | None


def read_remote(root: Path) -> Remote:
    """열린 PR 과 이 브랜치의 원격 커밋을 읽는다. 로컬의 ref 는 움직이지 않는다."""
    branch = current_branch(root)
    patterns = ["refs/pull/*/head", "refs/pull/*/merge"]
    patterns += [f"refs/heads/{branch}"] if branch else []
    listing = git(root, "ls-remote", REMOTE, *patterns, timeout=NETWORK_TIMEOUT)
    repo = github_repo(git(root, "remote", "get-url", REMOTE))
    from_gh = gh_listing(root, *repo) if repo else None
    if from_gh is not None:
        pulls, pulls_from = gh_pulls(from_gh), FROM_GH
    else:
        pulls, pulls_from = open_pulls(listing), FROM_MERGE_REF
    return Remote(pulls, pulls_from, remote_head(listing, branch) if branch else None)


def fetch(root: Path, pulls: dict[int, str]) -> None:
    """main 을 `origin/main` 으로 당기고, 열린 PR 의 head 를 ref 없이 받는다."""
    git(
        root,
        "fetch",
        "--quiet",
        "--no-tags",
        "--no-write-fetch-head",
        REMOTE,
        f"+refs/heads/{BRANCH}:refs/remotes/{MAIN}",
        *(f"refs/pull/{number}/head" for number in pulls),
        timeout=NETWORK_TIMEOUT,
    )


def survey(root: Path, remote: Remote) -> Survey:
    """fetch 가 끝난 클론에서 이 브랜치와 형제의 번호와 고친 파일을 읽는다."""
    main_sha = git(root, "rev-parse", MAIN).strip()
    base = merge_base(root, "HEAD", main_sha)
    if base is None:
        raise SurveyError(f"이 브랜치와 {MAIN} 의 merge-base 가 이 클론에 없다. {SHALLOW_HINT}")
    base_numbers = numbers_of(Tree(root, base))
    if missing := empty_places(base_numbers):
        raise SurveyError(f"merge-base 에서 번호의 자리가 비었다: {', '.join(missing)}")
    main_numbers = numbers_of(Tree(root, main_sha))
    main_changed = _lines(git(root, "diff", "--name-only", base, main_sha))
    siblings = [Sibling(MAIN, main_sha, fresh(main_numbers, base_numbers), main_changed)]
    taken = [base_numbers, main_numbers]

    def add(label: str, head: str, numbers: Numbers, changed: frozenset[str] | None) -> None:
        siblings.append(Sibling(label, head, fresh(numbers, base_numbers, main_numbers), changed))
        taken.append(numbers)

    for number, head in remote.pulls.items():
        if head == remote.own_head or is_ancestor(root, head, "HEAD"):
            continue
        since = merge_base(root, head, main_sha)
        changed = _lines(git(root, "diff", "--name-only", since, head)) if since else None
        add(f"PR #{number}", head, numbers_of(Tree(root, head)), changed)
    for location, head in worktrees(git(root, "worktree", "list", "--porcelain")):
        path = Path(location).resolve()
        if path == root or not path.is_dir():
            continue
        since = merge_base(root, head, main_sha)
        changed = _worktree_changes(path, since) if since else None
        add(f"워크트리 {path}", head, numbers_of(Disk(path)), changed)
    ours = fresh(numbers_of(Disk(root)), base_numbers)
    return Survey(ours, _worktree_changes(root, base), siblings, taken, remote.pulls_from)


def findings(result: Survey) -> list[tuple[Sibling, Clash]]:
    return [
        (sibling, clash)
        for sibling in result.siblings
        for clash in clashes(result.ours, sibling.numbers)
    ]


def _short(text: str) -> str:
    return text if len(text) <= ROW_WIDTH else text[: ROW_WIDTH - 1] + "…"


def _describe(clash: Clash) -> str:
    if clash.kind == "헌법":
        return "이 브랜치와 그쪽이 같은 판으로 올렸다"
    if clash.kind == "대기열":
        return f"이 브랜치 `{_short(clash.ours)}`, 그쪽 `{_short(clash.theirs)}`"
    return f"이 브랜치 {clash.ours}, 그쪽 {clash.theirs}"


_PULLS_FROM = {FROM_GH: "gh api", FROM_MERGE_REF: "merge ref(gh api 를 쓰지 못했다)"}


def _ours_line(ours: Numbers) -> str:
    keys = [f"일지 {key}" for key in sorted(ours.journals)]
    keys += [f"ADR {key}" for key in sorted(ours.adrs)]
    keys += [f"대기열 {key}" for key in sorted(ours.rows)]
    keys += [f"헌법 {ours.version}"] if ours.version else []
    return f"이 브랜치의 새 번호: {', '.join(keys)}" if keys else "이 브랜치의 새 번호 없음"


def render(result: Survey, found: list[tuple[Sibling, Clash]]) -> str:
    lines = [
        "형제: " + ", ".join(f"{s.label} {s.commit[:7]}" for s in result.siblings),
        f"열린 PR 을 읽은 길: {_PULLS_FROM[result.pulls_from]}",
        _ours_line(result.ours),
    ]
    if found:
        lines.append(f"번호 겹침 {len(found)}:")
        lines += [f"- {s.label} {c.kind} {c.key}: {_describe(c)}" for s, c in found]
        shifted = moves(result.ours, result.taken, [clash for _, clash in found])
        if shifted:
            lines.append("옮길 번호: " + ", ".join(f"{m.kind} {m.old} → {m.new}" for m in shifted))
    else:
        lines.append("번호 겹침 없음")
    shared: list[str] = []
    for sibling in result.siblings:
        if sibling.changed is None:
            shared.append(f"- {sibling.label}: 알 수 없다(merge-base 가 없다. {SHALLOW_HINT})")
        elif paths := sorted(result.changed & sibling.changed):
            shared.append(f"- {sibling.label}: {', '.join(paths)}")
    if shared:
        lines.append("함께 고친 파일(나중에 병합하는 쪽에서 글자 충돌 후보, 종료 코드와 무관):")
        lines += shared
    else:
        lines.append("함께 고친 파일 없음")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    start = Path(args[0]) if args else Path.cwd()
    try:
        root = Path(git(start, "rev-parse", "--show-toplevel").strip()).resolve()
        remote = read_remote(root)
        fetch(root, remote.pulls)
        result = survey(root, remote)
    except SurveyError as error:
        print(f"형제를 대조하지 못했다. {error}", file=sys.stderr)
        return 2
    found = findings(result)
    print(render(result, found))
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
