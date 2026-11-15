"""노트 검사: 릴리스 노트 조각의 빠뜨림과 모양을 병합 전에 막는다(release-image 티켓 05).

명세는 `.scratch/release-image/spec.md` 의 "릴리스 노트", "노트 검사", "느낌표의 기준과 그것을 보는
때"이고, 판정의 원천은 이 독스트링이다. 노트 조각은 셋이다(`docs/release-notes/` 아래).
기능 단락 `features/<기능 slug>.md`, 올릴 때 할 일 `upgrade/<이름>.md`, 소개 글 `intro/<X.Y.Z>.md`.
표준 라이브러리만 쓴다. 의존성을 깔지 않은 CI 잡에서 `python3 tools/check_notes.py` 로 돌기
때문이다(커밋 검사 `tools/check_ticket.py` 와 같다).

입구는 모드 셋이다.

- 인자 없음(커밋 검사). 스테이지한 변경을 지난 커밋(HEAD)에 견준다. pre-commit 이
  `tools/run_checks.py` 의 `CHECKS`(id `check-notes`)로 부른다. 건너뛰기는 그 id 의 `SKIP` 이다.
  PR 제목을 모르므로 (나)와 (다)만 본다.
- `--ci`. PR 의 변경 전체(base 와 머리의 merge-base 에서 머리 커밋까지)를 본다. (가)(나)(다)를 모두
  본다. ci.yml 의 `ticket` 잡이 부른다.
- `--title-only`. 같은 입력에서 (가)만 본다. PR 제목만 고쳤을 때 도는 작은 워크플로
  (`.github/workflows/pr-title.yml`)가 부른다.

CI 의 두 모드는 PR 의 값을 환경 변수로 받는다. `PR_HEAD_REF`(머리 브랜치), `PR_HEAD_SHA`(머리 커밋),
`PR_BASE_SHA`(base 커밋), `PR_TITLE`(PR 제목)이다. 제목을 워크플로 식에 바로 넣지 않고 환경 변수로
넘기는 것은 명령 주입(zizmor 의 template-injection)을 피하려는 것이다. 머리 브랜치가 비면 PR 이 아닌
실행이라 한 줄을 알리고 지난다. 그런데 이벤트 이름(`GITHUB_EVENT_NAME`)이 `pull_request` 인데 비거나
PR 실행의 제목이 비면 워크플로가 값을 넘기지 못한 것이라 종료 2 다. 머리 브랜치가 main 이나 dev 인
PR(출시 PR, 되돌려 합치기 PR)은 건너뛴다. 티켓들이 더한 조각이 한꺼번에 실리기 때문이다.

판정.

(가) 느낌표와 할 일(CI 만). 커밋 검사(`tools/check_commit_msg.py`)의 `PATTERN` 에 맞지 않는 제목은
빨강이다. 그 제목이 squash 커밋의 제목이 되어 판 번호를 정하기 때문이다. 길이 상한과 끝 마침표는
보지 않는다. 그 검사의 `PASS_PREFIXES` 로 시작하는 제목(`Revert "…"` 등)은 받고 느낌표가 없는
제목으로 읽는다. 접두 뒤에 느낌표가 있으면 PR 이 `upgrade/` 파일을 하나 이상 새로 더하고 제품
경로(`tools/release.py` 의 `PRODUCT_PATHS`)를 하나 이상 고쳐야 한다. 느낌표가 없는데 `upgrade/`
파일을 새로 더했으면 빨강이다. 있던 파일을 고치는 것은 된다. 이름은 보지 않는다. `upgrade/` 아래에
더한 파일은 하위 폴더와 확장자를 가리지 않고 센다. 판 내기(`tools/release.py` 의 `_upgrade_entry`)가
그 아래에 더한 파일을 모두 노트에 싣기 때문이다.

(나) 기능 단락의 빠뜨림. 변경이 기능 계획 `.scratch/<slug>/plan.md` 에 `**끝:**` 줄(줄 머리)을
더하거나 `features/<slug>.md` 를 더하면 그 기능이 제품 변경을 담았는지 본다. 그 기능의 티켓 파일
(`.scratch/<slug>/issues/` 아래)을 고친 커밋 가운데 제품 경로도 고친 것이 하나라도 있으면(지금 보는
변경 포함) 담은 것이다. 담았으면 변경 뒤의 트리에 `features/<slug>.md` 가 있어야 하고, 담지 않았으면
그 파일을 더하지 못한다. `features/` 파일의 이름은 변경 뒤의 트리에 있는 기능 계획의 slug 여야
한다(`harness` 와 `retro-queue` 는 기능이 아니다). 이력은 머리 커밋(커밋 검사는 HEAD)에서 닿는
병합 아닌 커밋이고 `--full-history` 로 읽는다. 지금 보는 변경은 커밋 검사에서는 스테이지한 변경,
CI 에서는 PR 의 변경 전체다.

(다) 모양. 바뀌거나 더해진(지운 것은 아니다) 조각은 비어 있지 않고 `#` 으로 시작하는 줄이 없다.
기능 단락은 빈 줄(공백만 있는 줄과 앞쪽의 빈 줄도)이 없는 한 단락이고 줄바꿈을 뺀 글자 수가 400자
이하다. 소개 글의 이름은 `X.Y.Z.md` 다(출시 후보 `X.Y.Z-rc.N.md` 는 아니다). 할 일과 소개 글에는
길이 상한이 없다. 조각은 세 폴더 바로 아래의 `.md` 파일이다. 하위 폴더나 `.md` 가 아닌 파일은
조각으로 읽지 않고 모양을 보지 않지만, `upgrade/` 에 그런 파일을 새로 더하면 판 내기가 그대로
노트에 싣기 때문에 조각이 아니라며 막는다. 400자는 지난 기능 넷의 초안으로 정한
값이다(`.scratch/release-image/probes/notes_summary/README.md` 1번).

막는 글(stderr)은 첫 줄이 `check-notes: ` 로 시작하고, 어긴 판정마다 한 항목을 싣고 규약 원천을
적는다. 종료 코드는 0 지남, 1 막음, 2 git 이나 입력의 실패(저장소가 아닌 폴더, 받은 커밋을 찾지
못함, 빈 제목, 얕은 체크아웃)다. 인자를 잘못 준 것도 argparse 가 2 로 끝낸다.

못 보는 것.

- 커밋 검사는 스테이지한 변경만 본다. 한 PR 안에서 제품 변경과 끝 줄이 다른 커밋에 나뉘고 끝 줄을
  싣는 커밋의 변경에 제품 경로가 없으면 놓친다. CI 가 PR 의 변경 전체를 지금 보는 변경으로 보아
  잡는다.
- 병합을 마무리하는 커밋(`MERGE_HEAD` 가 있다)은 커밋 검사가 보지 않고 한 줄을 알리고 지난다.
  main 에서 끝난 다른 기능의 단락이 들어오는 병합을 이 브랜치의 이력으로 판정하면 잘못 막기
  때문이다. 그 커밋이 든 PR 은 CI 가 본다.
- (가)는 CI 만 본다. 훅을 깔지 않은 클론, `--no-verify`, `SKIP` 은 커밋 검사를 지나가고 CI 가
  잡는다. 제목만 고친 PR 의 빨강은 필수 검사가 아니라서 GitHub 가 막지 않는다(병합하는 세션이 본다).
- 단락의 내용(운영자의 말로 썼는지, 경로와 ADR 번호를 싣지 않았는지)과 할 일이 구체적인지,
  느낌표가 기준에 맞는지는 보지 않는다. 리뷰와 셀프 리뷰의 몫이다.
- 제품 변경은 경로로만 가른다. `PRODUCT_PATHS` 밖의 파일(문서, 도구, 시험)은 제품 변경이 아니다.
- 이름 바꾸기는 지운 것과 더한 것 둘로 센다(`--no-renames`). 조각을 다른 이름으로 옮기면 옛 이름의
  삭제와 새 이름의 추가다.
- 얕은 클론에서는 이력이 잘려 (나)의 이력 판정이 담은 기능을 놓칠 수 있다. CI 는 전체 이력을
  받는다(`fetch-depth: 0`). 얕은 CI 체크아웃은 merge-base 를 찾지 못해 종료 2 다.
- `**끝:**` 줄이 있던 계획에서 날짜만 고친 변경은 더한 것이 아니다. 기능 단락을 다시 묻지 않는다.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

if __package__ in (None, ""):  # 스크립트로 부르면 저장소 루트가 import 경로에 없다
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.check_commit_msg import PASS_PREFIXES, PATTERN, TYPES  # noqa: E402
from tools.check_ticket import (  # noqa: E402
    PROTECTED_BRANCHES,
    GitError,
    current_branch,
    merge_base,
    merge_head,
    pull_request,
)
from tools.release import FEATURES, INTRO, PRODUCT_PATHS, UPGRADE, classify  # noqa: E402

PREFIX = "check-notes: "
GIT_TIMEOUT = 60.0
PR_TITLE = "PR_TITLE"
CONVENTION = "규약 원천: docs/constitution/operations.md"
MAX_PARAGRAPH = 400
END_LINE = "**끝:**"
# 기능 폴더가 아닌 `.scratch/` 아래 폴더. 계획 파일이 있어도 기능 계획이 아니다
_NOT_FEATURES = frozenset({"harness", "retro-queue"})
_PLAN = re.compile(r"\.scratch/([^/]+)/plan\.md")
_INTRO_NAME = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)")
_NOTES_PATHS = ("docs/release-notes", ".scratch")


@dataclass(frozen=True)
class Change:
    """한 파일의 변경. 상태는 git 의 `A` 더함, `M` 고침, `D` 지움이다(`T` 는 `M` 으로 읽는다)."""

    status: str
    path: str


@dataclass(frozen=True)
class Wording:
    """막는 글의 머리가 커밋 검사와 CI 에서 다르다."""

    blocked: str


COMMIT_WORDING = Wording("커밋을 막았다")
PR_WORDING = Wording("PR 을 막았다")


@dataclass(frozen=True)
class Scene:
    """판정할 변경과 그 앞뒤의 트리.

    `after` 는 변경 뒤의 트리를 읽는 자리다. 지금 색인이면 빈 문자열이고(`git show :경로`), 커밋이면
    그 커밋이다. `before` 는 변경 앞의 커밋이다. `tip` 은 이력을 읽는 끝 커밋이다.
    """

    root: Path
    changes: tuple[Change, ...]
    after: str
    before: str | None
    tip: str


def _run(cwd: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
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


def _text(raw: bytes) -> str:
    return raw.decode("utf-8", "replace")


def _out(cwd: Path, *args: str) -> str:
    result = _run(cwd, *args)
    if result.returncode != 0:
        message = _text(result.stderr).strip()
        raise GitError(f"git {args[0]} 가 {result.returncode} 로 끝났다: {message}")
    return _text(result.stdout)


def _commit(cwd: Path, value: str) -> str | None:
    result = _run(cwd, "rev-parse", "-q", "--verify", f"{value}^{{commit}}")
    return _text(result.stdout).strip() if result.returncode == 0 else None


def _received(cwd: Path, name: str, value: str) -> str:
    commit = _commit(cwd, value) if value else None
    if commit is None:
        raise GitError(f"{name} 의 커밋({value or '빈 값'})을 이 체크아웃에서 찾지 못했다.")
    return commit


def _changes(cwd: Path, *diff: str) -> tuple[Change, ...]:
    raw = _out(cwd, "diff", "--name-status", "--no-renames", "-z", *diff, "--")
    fields = raw.split("\0")
    changes = [
        Change("M" if status == "T" else status, path)
        for status, path in zip(fields[0::2], fields[1::2], strict=False)
        if path
    ]
    return tuple(changes)


def _paths_after(scene: Scene) -> set[str]:
    """변경 뒤의 트리에서 노트와 `.scratch/` 아래의 파일."""
    if scene.after:
        raw = _out(
            scene.root, "ls-tree", "-r", "--name-only", "--full-tree", "-z", scene.after, "--",
            *_NOTES_PATHS,
        )  # fmt: skip
    else:
        raw = _out(scene.root, "ls-files", "-z", "--", *_NOTES_PATHS)
    return {path for path in raw.split("\0") if path}


def _read(cwd: Path, revision: str | None, path: str) -> str | None:
    """그 트리의 파일 글, 없으면 None. 빈 `revision` 은 색인이다."""
    if revision is None:
        return None
    done = _run(cwd, "show", f"{revision}:{path}")
    return _text(done.stdout) if done.returncode == 0 else None


# ---------- 순수 판정 ----------


def _under(path: str, folder: str) -> bool:
    """`folder` 바로 아래의 `.md` 파일인가."""
    head, _, name = path.rpartition("/")
    return head == folder and name.endswith(".md") and len(name) > len(".md")


def _fragment_folder(path: str) -> str | None:
    """조각으로 읽는 경로의 폴더. 조각이 아닌 경로는 None."""
    folder = path.rpartition("/")[0]
    return folder if folder in (FEATURES, UPGRADE, INTRO) and _under(path, folder) else None


def _stray_upgrade(path: str) -> bool:
    """`upgrade/` 아래인데 조각으로 읽히지 않는 경로(하위 폴더, `.md`가 아닌 파일)인가."""
    return path.startswith(f"{UPGRADE}/") and _fragment_folder(path) is None


def _is_product(path: str) -> bool:
    return any(path == product or path.startswith(f"{product}/") for product in PRODUCT_PATHS)


def _slug(path: str) -> str:
    return path.rpartition("/")[2].removesuffix(".md")


def title_problems(title: str, changes: Sequence[Change]) -> list[str]:
    """(가). PR 제목의 꼴과, 느낌표와 할 일 파일의 짝."""
    exclaim = False
    if not title.startswith(PASS_PREFIXES):
        if PATTERN.match(title) is None:
            return [
                "(가) PR 제목이 커밋 제목의 꼴(`<타입>: <제목>`,"
                f" 타입은 {', '.join(TYPES)})이 아니다: {title!r}."
                " 이 제목이 squash 커밋의 제목이 되어 판 번호를 정한다."
            ]
        exclaim = classify(title)[1]
    added = [c.path for c in changes if c.status == "A" and c.path.startswith(f"{UPGRADE}/")]
    if exclaim:
        problems: list[str] = []
        if not added:
            problems.append(
                f"(가) 제목 접두에 느낌표가 있는데 `{UPGRADE}/` 에 새로 더한 파일이 없다. 운영자가"
                " 올릴 때 무엇을 무엇으로 바꾸는지 그 폴더에 파일로 쓴다."
            )
        if not any(_is_product(c.path) for c in changes):
            problems.append(
                f"(가) 제목 접두에 느낌표가 있는데 제품 경로({', '.join(PRODUCT_PATHS)})를 고친"
                " 변경이 없다. 느낌표는 운영자가 올릴 때 손댈 것이 있는 제품 변경에만 붙인다."
            )
        return problems
    return [
        f"(가) 제목 접두에 느낌표가 없는데 `{path}` 를 새로 더했다. 올릴 때 운영자가 손댈 것이 있는"
        " 변경이면 제목 접두에 느낌표를 붙이고, 아니면 그 파일을 뺀다."
        for path in added
    ]


def fragment_problems(path: str, text: str) -> list[str]:
    """(다). 조각 하나의 모양. 조각이 아닌 경로는 빈 목록이다."""
    folder = _fragment_folder(path)
    if folder is None:
        return []
    problems: list[str] = []
    if not text.strip():
        return [f"(다) `{path}` 가 비어 있다. 조각은 비어 있지 않다."]
    if any(line.startswith("#") for line in text.split("\n")):
        problems.append(
            f"(다) `{path}` 에 `#` 으로 시작하는 줄이 있다. 노트가 머리를 달므로 조각에는 없다."
        )
    if folder == INTRO and _INTRO_NAME.fullmatch(_slug(path)) is None:
        problems.append(f"(다) 소개 글의 이름 `{path}` 가 `X.Y.Z.md` 꼴이 아니다.")
    if folder == FEATURES:
        problems += _paragraph_problems(path, text)
    return problems


def _paragraph_problems(path: str, text: str) -> list[str]:
    lines = text.replace("\r", "").rstrip("\n").split("\n")
    problems: list[str] = []
    if any(not line.strip() for line in lines):
        problems.append(
            f"(다) 기능 단락 `{path}` 에 빈 줄이 있다. 기능 단락은 빈 줄 없는 한 단락이다."
        )
    count = len(text.replace("\r", "").replace("\n", ""))
    if count > MAX_PARAGRAPH:
        problems.append(
            f"(다) 기능 단락 `{path}` 가 줄바꿈을 뺀 {count}자다. {MAX_PARAGRAPH}자 이하로 줄인다."
        )
    return problems


# ---------- (나) 기능 단락의 빠뜨림 ----------


def _has_end(text: str | None) -> bool:
    return text is not None and any(line.startswith(END_LINE) for line in text.split("\n"))


def _delivered(scene: Scene, slug: str) -> bool:
    """그 기능의 티켓 파일을 고친 커밋 가운데 제품 경로도 고친 것이 있는가(지금 보는 변경 포함)."""
    tickets = f".scratch/{slug}/issues/"
    if any(c.path.startswith(tickets) for c in scene.changes) and any(
        _is_product(c.path) for c in scene.changes
    ):
        return True
    log = _out(
        scene.root,
        "log",
        "--no-merges",
        "--full-history",
        "--format=%x01%H",
        "--name-only",
        scene.tip,
        "--",
        tickets.rstrip("/"),
        *PRODUCT_PATHS,
    )
    for block in log.split("\x01")[1:]:
        names = [line for line in block.split("\n")[1:] if line]
        if any(n.startswith(tickets) for n in names) and any(_is_product(n) for n in names):
            return True
    return False


def feature_problems(scene: Scene) -> list[str]:
    """(나)."""
    triggered: set[str] = set()
    added_features: set[str] = set()
    named: set[str] = set()
    for change in scene.changes:
        if change.status == "D":
            continue
        if _under(change.path, FEATURES):
            named.add(_slug(change.path))
            if change.status == "A":
                added_features.add(_slug(change.path))
                triggered.add(_slug(change.path))
            continue
        found = _PLAN.fullmatch(change.path)
        if found is None or found.group(1) in _NOT_FEATURES:
            continue
        if _has_end(_read(scene.root, scene.after, change.path)) and not _has_end(
            _read(scene.root, scene.before, change.path)
        ):
            triggered.add(found.group(1))
    if not triggered and not named:
        return []
    present = _paths_after(scene)
    problems: list[str] = []
    for slug in sorted(named):
        plan = f".scratch/{slug}/plan.md"
        if slug in _NOT_FEATURES or plan not in present:
            problems.append(
                f"(나) `{FEATURES}/{slug}.md` 의 이름 `{slug}` 가 있는 기능 계획의 slug 가 아니다."
                f" `{plan}` 가 없다. features/ 파일은 기능 slug 로 짓는다."
            )
    for slug in sorted(triggered):
        if slug in named and (slug in _NOT_FEATURES or f".scratch/{slug}/plan.md" not in present):
            continue  # 이름 문제는 위에서 알렸다
        has_file = f"{FEATURES}/{slug}.md" in present
        delivered = _delivered(scene, slug)
        if delivered and not has_file:
            problems.append(
                f"(나) 기능 `{slug}` 가 제품 변경을 담았는데 기능 단락 `{FEATURES}/{slug}.md` 가"
                " 없다. 기능의 마지막 티켓을 닫는 커밋이 `**끝:**` 줄과 함께 운영자의 말로 쓴 한"
                " 단락을 싣는다."
            )
        if not delivered and slug in added_features:
            problems.append(
                f"(나) 기능 `{slug}` 의 티켓은 제품 경로를 고친 적이 없는데 기능 단락"
                f" `{FEATURES}/{slug}.md` 를 더했다. 제품 변경이 없는 기능은 단락을 쓰지 않는다."
            )
    return problems


# ---------- 판정 ----------


def shape_problems(scene: Scene) -> list[str]:
    """(다). 바뀌거나 더해진 조각의 모양."""
    problems: list[str] = []
    for change in scene.changes:
        if change.status == "D":
            continue
        if change.status == "A" and _stray_upgrade(change.path):
            problems.append(
                f"(다) `{change.path}` 는 할 일 조각이 아니다. `{UPGRADE}/` 에는 `<이름>.md`"
                " 파일만 둔다. 판 내기는 그 폴더에 더한 파일을 모두 노트에 싣는다."
            )
        if _fragment_folder(change.path) is None:
            continue
        text = _read(scene.root, scene.after, change.path)
        if text is not None:
            problems += fragment_problems(change.path, text)
    return problems


def blocked_text(problems: Sequence[str], wording: Wording) -> str:
    lines = [f"릴리스 노트 조각이 규약을 어겨 {wording.blocked}."]
    lines += [f"  {problem}" for problem in problems]
    lines.append(CONVENTION)
    return "\n".join(lines)


@dataclass(frozen=True)
class Verdict:
    code: int
    message: str = ""


_PASS = Verdict(0)


def judge_staged(cwd: Path) -> Verdict:
    """커밋 검사. 스테이지한 변경을 HEAD 에 견줘 (나)와 (다)를 본다."""
    branch = current_branch(cwd)
    if branch is None or branch in PROTECTED_BRANCHES:
        return _PASS
    if _commit(cwd, "HEAD") is None:
        return Verdict(0, "HEAD 가 아직 없어(첫 커밋) 판정하지 않고 지난다.")
    if merge_head(cwd) is not None:
        return Verdict(
            0, "병합을 마무리하는 커밋이라 판정하지 않고 지난다. CI 가 PR 의 변경 전체를 본다."
        )
    root = Path(_out(cwd, "rev-parse", "--show-toplevel").strip())
    scene = Scene(root, _changes(root, "--cached", "HEAD"), "", "HEAD", "HEAD")
    problems = shape_problems(scene) + feature_problems(scene)
    return Verdict(1, blocked_text(problems, COMMIT_WORDING)) if problems else _PASS


def _pr_scene(cwd: Path, branch_head: str, base: str) -> Scene:
    head = _received(cwd, "PR_HEAD_SHA", branch_head)
    base_commit = _received(cwd, "PR_BASE_SHA", base)
    start = merge_base(cwd, base_commit, [head])
    if start is None:
        raise GitError(
            "CI 의 체크아웃이 얕아 base 와 머리 커밋의 merge-base 를 찾지 못했다."
            " 체크아웃을 fetch-depth: 0 으로 받는다."
        )
    root = Path(_out(cwd, "rev-parse", "--show-toplevel").strip())
    return Scene(root, _changes(root, start, head), head, start, head)


def judge_pr(cwd: Path, environ: Mapping[str, str], *, title_only: bool) -> Verdict:
    """CI 의 판정. 제목만 고친 실행(`title_only`)은 (가)만 본다."""
    pr = pull_request(environ)
    if pr is None:
        return Verdict(0, "PR 이 아닌 실행(main·dev 의 push)이라 판정하지 않고 지난다.")
    if pr.branch in PROTECTED_BRANCHES:
        return _PASS
    title = environ.get(PR_TITLE, "")
    if not title.strip():
        raise GitError(
            f"PR 실행인데 {PR_TITLE} 가 비었다. 워크플로가 PR 제목을 env 로 넘기는지 본다."
        )
    scene = _pr_scene(cwd, pr.head, pr.base)
    problems = title_problems(title, scene.changes)
    if not title_only:
        problems += shape_problems(scene) + feature_problems(scene)
    return Verdict(1, blocked_text(problems, PR_WORDING)) if problems else _PASS


# ---------- 입구 ----------


def _write(stream: TextIO, message: str) -> None:
    stream.buffer.write(f"{PREFIX}{message}\n".encode())
    stream.buffer.flush()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="노트 검사(release-image 티켓 05). 판정은 이 파일의 독스트링이다"
    )
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--ci",
        action="store_true",
        help="CI 의 판정. 환경 변수 PR_HEAD_REF, PR_HEAD_SHA, PR_BASE_SHA, PR_TITLE 로 받는다",
    )
    modes.add_argument(
        "--title-only",
        action="store_true",
        help="--ci 와 같은 입력에서 (가) 느낌표와 할 일만 본다",
    )
    parser.add_argument("cwd", nargs="?", type=Path, help="판정할 저장소. 없으면 작업 폴더")
    return parser


def main(argv: list[str]) -> int:
    args = _parser().parse_args(argv[1:])
    ci: bool = args.ci
    title_only: bool = args.title_only
    where: Path | None = args.cwd
    cwd = Path.cwd() if where is None else where
    try:
        if ci or title_only:
            verdict = judge_pr(cwd, os.environ, title_only=title_only)
        else:
            verdict = judge_staged(cwd)
    except GitError as error:
        _write(sys.stderr, str(error))
        return 2
    if verdict.code == 1:
        _write(sys.stderr, verdict.message)
    elif verdict.message:
        _write(sys.stdout, verdict.message)
    return verdict.code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
