"""아침 보고 수집 도구(`tools/morning_collect.py`)가 직접 부르는 바깥 명령(gh·git·tasklist)과 그
출력의 풀이. 수집 도구가 다른 도구(`hook_report`)를 거쳐 부르는 git은 그 도구에 있다. 수집 도구에서
절을 짓는 함수는 이 명령을 부르지 않고, `collect`와 그 모으기 함수가 불러 결과를 넘긴다.

명령은 저장소 루트(`root`)에서 돌고 호출마다 `CALL_TIMEOUT`초 제한을 둔다(`.claude/rules/tools.md`).
실패하거나 시간을 넘기면 대개 None을 돌려주고, 빈 값과 실패를 가르지 않는 함수는 빈 것을
돌려준다(예: `worktree_list`, `ticket_paths`, `latest_journal`). 함수마다의 값은 그 반환형과
독스트링이 원천이고, 그 값으로 무엇을 적는지는 수집 도구가 정한다. 통합 브랜치(`integration_ref`)를
읽는 git은 fetch하지 않는다. 예외는 `main_queue`다. 대기열 폴더는
`queue_open_rows.read_ref_folder`로 읽어 git을 띄우는 시간 제한이 그 도구의 `GIT_TIMEOUT`이고, 작업
폴더를 `root`로 옮긴 동안 부른다.

못 보는 것.
- 클라우드 세션에서 `gh pr list`는 실패했고 `gh pr view`는 요청한 필드에 따라 갈렸다. 이 도구가
  요청하는 필드와 `gh run list`는 클라우드에서 본 기록이 없다. 그때 보고에 적는 것은 수집 도구
  독스트링의 못 보는 것이 원천이다.
- `tasklist`가 없는 기계(윈도 밖)에서는 `processes`가 None이다.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import re
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

# 바깥 명령 층이 그리기 도구에서 JSON 풀이를 가져오는 까닭은 `morning_report.py`의 JSON 풀이
# 주석에 있다(그리기 도구는 스크립트로 돌아 `tools` 패키지를 가져오지 못한다).
from tools.morning_report import Json, json_int, json_list, json_obj, json_str, json_time
from tools.sibling_overlap import journal_order

from tools import base_rule, queue_open_rows

CALL_TIMEOUT = 60
PR_LIMIT = 1000  # `gh pr list`의 기본 한도는 30이라 넘으면 조용히 잘린다
REVIEW = {
    "APPROVED": "리뷰 승인",
    "CHANGES_REQUESTED": "리뷰 변경 요청",
    "REVIEW_REQUIRED": "리뷰 대기",
}
FAILED = frozenset(
    {"FAILURE", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED", "ERROR", "STARTUP_FAILURE"}
)
PASSED = frozenset({"SUCCESS", "SKIPPED", "NEUTRAL"})


def _run(args: Sequence[str], cwd: Path) -> str | None:
    """명령의 stdout. 실패하거나 `CALL_TIMEOUT`초를 넘으면 None이다."""
    try:
        done = subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=CALL_TIMEOUT,
            check=False,
            cwd=cwd,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout if done.returncode == 0 else None


def _gh_json(args: Sequence[str], cwd: Path) -> Json:
    out = _run(["gh", *args], cwd)
    if out is None:
        return None
    try:
        j: Json = json.loads(out)
    except ValueError:
        return None
    return j


# gh


@dataclass(frozen=True)
class GhPr:
    number: int
    title: str
    branch: str
    created: datetime
    merged: datetime | None


def _gh_pr(j: Json) -> GhPr | None:
    o = json_obj(j)
    number = json_int(o.get("number"))
    created = json_time(o.get("createdAt"))
    if number is None or created is None:
        return None
    merged = json_time(o.get("mergedAt"))
    return GhPr(number, json_str(o.get("title")), json_str(o.get("headRefName")), created, merged)


def merged_prs(since: date | None, root: Path) -> list[GhPr] | None:
    """`since`(UTC 날짜라 하루 앞부터 받는다) 뒤에 병합된 PR. `since`가 None이면 기간 없이
    `PR_LIMIT`개까지 받는다."""
    window = (
        [] if since is None else ["--search", f"merged:>={(since - timedelta(days=1)).isoformat()}"]
    )
    j = _gh_json(
        [
            "pr",
            "list",
            "--state",
            "merged",
            "--limit",
            str(PR_LIMIT),
            *window,
            "--json",
            "number,title,headRefName,createdAt,mergedAt",
        ],
        root,
    )
    if not isinstance(j, list):
        return None
    return [p for x in j if (p := _gh_pr(x)) is not None and p.merged is not None]


def ci_state(checks: Sequence[Json]) -> str:
    """열린 PR의 검사 상태. 실패가 하나라도 있으면 실패, 끝나지 않은 것이 있으면 도는 중이다."""
    results: list[str] = []
    running = False
    for c in checks:
        o = json_obj(c)
        result = (json_str(o.get("conclusion")) or json_str(o.get("state"))).upper()
        status = json_str(o.get("status")).upper()
        if status and status != "COMPLETED" and not result:
            running = True
        elif result in ("PENDING", "EXPECTED", "QUEUED", "IN_PROGRESS"):
            running = True
        results.append(result)
    if not checks:
        return "CI 없음"
    if any(r in FAILED for r in results):
        return "CI 실패"
    if running or not all(r in PASSED for r in results):
        return "CI 도는 중"
    return "CI 통과"


def open_state(pr: Json) -> str:
    """열린 PR의 상태. 초안, 리뷰 결정(`reviewDecision`), CI를 ` · `로 잇는다. 리뷰 결정이 비었으면
    (리뷰를 요구하지 않는 저장소) 그 칸을 뺀다."""
    o = json_obj(pr)
    parts = ["초안"] if o.get("isDraft") is True else []
    review = REVIEW.get(json_str(o.get("reviewDecision")))
    if review is not None:
        parts.append(review)
    return " · ".join([*parts, ci_state(json_list(o.get("statusCheckRollup")))])


@dataclass(frozen=True)
class OpenPr:
    pr: GhPr
    state: str


def open_prs(root: Path) -> list[OpenPr] | None:
    """열린 PR(`PR_LIMIT`개까지)과 그 상태(`open_state`). gh가 실패하거나 JSON 목록이 아니면
    None이고, 번호나 연 시각을 읽지 못한 PR은 뺀다."""
    j = _gh_json(
        [
            "pr",
            "list",
            "--state",
            "open",
            "--limit",
            str(PR_LIMIT),
            "--json",
            "number,title,headRefName,createdAt,isDraft,reviewDecision,statusCheckRollup",
        ],
        root,
    )
    if not isinstance(j, list):
        return None
    return [OpenPr(p, open_state(x)) for x in j if (p := _gh_pr(x)) is not None]


@dataclass(frozen=True)
class PrView:
    """`commits`는 (커밋 시각, 머리줄)이다."""

    title: str
    body: str
    branch: str
    created: datetime | None
    commits: tuple[tuple[datetime, str], ...]


def pr_view(number: int, root: Path) -> PrView | None:
    """PR 하나의 제목·본문·브랜치·연 시각·커밋. gh가 실패하거나 JSON 객체가 아니거나 빈 객체이면
    None이다."""
    j = _gh_json(
        ["pr", "view", str(number), "--json", "title,body,headRefName,createdAt,commits"], root
    )
    o = json_obj(j)
    if not o:
        return None
    commits = tuple(
        (t, json_str(json_obj(c).get("messageHeadline")))
        for c in json_list(o.get("commits"))
        if (t := json_time(json_obj(c).get("committedDate"))) is not None
    )
    return PrView(
        json_str(o.get("title")),
        json_str(o.get("body")),
        json_str(o.get("headRefName")),
        json_time(o.get("createdAt")),
        commits,
    )


def integration_ref(root: Path) -> str:
    """보고가 읽는 통합 브랜치의 원격 추적 ref. 브랜치가 없는 보고라 hotfix 가 아닌 쪽의 기준
    브랜치다(`tools/base_rule.py`). 티켓 PR 이 병합되는 자리라 대기열과 티켓과 일지가 가장 먼저
    오르고, `origin/dev` 가 없으면 `origin/main` 이다."""
    return base_rule.base_ref(root, None)


def ci_runs(root: Path) -> list[tuple[str, float]] | None:
    """통합 브랜치(`integration_ref`)의 최근 CI 열 번의 (결과, 걸린 초)."""
    j = _gh_json(
        [
            "run",
            "list",
            "--branch",
            integration_ref(root).removeprefix(f"{base_rule.REMOTE}/"),
            "--limit",
            "10",
            "--json",
            "conclusion,createdAt,updatedAt",
        ],
        root,
    )
    if not isinstance(j, list):
        return None
    out: list[tuple[str, float]] = []
    for x in j:
        o = json_obj(x)
        a, b = json_time(o.get("createdAt")), json_time(o.get("updatedAt"))
        if a is not None and b is not None:
            out.append((json_str(o.get("conclusion")), (b - a).total_seconds()))
    return out


# tasklist


def tasklist_load(text: str) -> tuple[int, int]:
    """`tasklist /FO CSV /NH`의 출력에서 프로세스 수와 메모리 합(MB)."""
    count = 0
    kb = 0
    for row in csv.reader(io.StringIO(text)):
        if len(row) < 5 or not row[0].lower().endswith(".exe"):
            continue
        digits = re.sub(r"\D", "", row[4])
        count += 1
        kb += int(digits) if digits else 0
    return count, kb // 1024


def processes(root: Path) -> tuple[int, int] | None:
    """`claude.exe` 프로세스의 (수, 메모리 합 MB)(`tasklist_load`). `tasklist`가 없거나 실패하면
    None이다."""
    out = _run(["tasklist", "/FI", "IMAGENAME eq claude.exe", "/FO", "CSV", "/NH"], root)
    return None if out is None else tasklist_load(out)


# git


def worktree_entries(porcelain: str) -> list[tuple[str, str | None]]:
    """`git worktree list --porcelain`의 (경로, 브랜치). 첫 항목(주 체크아웃)은 뺀다."""
    entries: list[tuple[str, str | None]] = []
    path: str | None = None
    branch: str | None = None
    for line in [*porcelain.splitlines(), ""]:
        if line.startswith("worktree "):
            path, branch = line.removeprefix("worktree "), None
        elif line.startswith("branch refs/heads/"):
            branch = line.removeprefix("branch refs/heads/")
        elif not line and path is not None:
            entries.append((path, branch))
            path = None
    return entries[1:]


def worktree_list(root: Path) -> list[tuple[str, str | None]]:
    """주 체크아웃을 뺀 워크트리의 (경로, 브랜치). git이 실패하면 빈 목록이다."""
    return worktree_entries(_run(["git", "worktree", "list", "--porcelain"], root) or "")


def main_text(root: Path, path: str) -> str | None:
    """통합 브랜치(`integration_ref`)에 있는 파일 `path`의 글. 없거나 git이 실패하면 None이다."""
    return _run(["git", "show", f"{integration_ref(root)}:{path}"], root)


def main_queue(root: Path) -> dict[str, str] | None:
    """통합 브랜치의 회고 대기열 폴더(`queue_open_rows.QUEUE`)에 든 항목 파일의 이름→내용.
    `README.md`는 뺀다. `queue_open_rows.read_ref_folder`의 읽기를 그대로 쓰며(목록 한 번, 내용
    한 번), 그 함수가 git을 띄우는 곳이 작업 폴더라 `root`로 옮겨 간 동안만 부른다. 폴더가
    없거나(이행 전 커밋. 옛 파일로 돌아가지 않는다) git이 실패하거나 UTF-8이 아니면 None이다."""
    # 통합 ref 는 옮겨 가기 전에 정한다. 상대 `root` 는 옮겨 간 뒤에 다른 폴더를 가리킨다
    ref = integration_ref(root)
    try:
        with contextlib.chdir(root):
            return queue_open_rows.read_ref_folder(ref)
    except (OSError, UnicodeDecodeError):
        return None


def branch_subject(root: Path, branch: str) -> str | None:
    """통합 브랜치에 없는 `branch`의 커밋 가운데 마지막 것의 제목(줄바꿈이 붙는다). 그런 커밋이
    없으면 빈 글, git이 실패하면 None이다."""
    return _run(["git", "log", "-1", "--format=%s", f"{integration_ref(root)}..{branch}"], root)


def journal_next(text: str) -> str:
    """일지의 `## 다음` 절. 없으면 빈 글이다."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "## 다음":
            body: list[str] = []
            for rest in lines[i + 1 :]:
                if rest.startswith("## "):
                    break
                body.append(rest)
            return "\n".join(body).strip()
    return ""


def latest_journal(root: Path) -> tuple[str, str]:
    """통합 브랜치에서 `## 다음`으로 시작하는 줄이 있는 가장 늦은 일지의 (경로, 그 일지의
    `## 다음` 절). 그런 일지가 없으면 빈 글 둘이다. 그 일지를 읽지 못하거나 그 줄이 `## 다음(…)`처럼
    덧붙은 것뿐이면 절은 빈 글이다(`journal_next`).

    가장 늦은 일지는 이름이 아니라 main에 더해진 차례로 고른다. 같은 날 옛 순번 꼴(`-12-`)이
    새 시각 꼴(`-0930-`)보다 이름순으로 뒤라서, 이름순으로 고르면 나중에 더한 일지를 지나친다.
    한 커밋이 일지를 여럿 더했으면 그 안에서는 이름순이 아니라 시각순(`journal_order`)으로 늦은
    것부터 본다.

    못 보는 것. `git mv` 로 이름만 바뀐 일지는 더한 파일(`--diff-filter=A`)로 잡히지 않아
    더한 차례가 없는 일지로 밀리고, 더한 차례가 있는 일지가 모두 `## 다음` 이 없을 때에만 걸린다.
    얕은 클론은 경계 커밋이 그 시점의 파일을 모두 더한 것으로 보이므로, 그 일지들이 한 커밋의
    블록으로 들어가 시각순으로 가려진다(코드를 읽은 것이고 얕은 클론으로 돌려 보지는 않았다).
    """
    ref = integration_ref(root)
    out = _run(["git", "grep", "-n", "^## 다음", ref, "--", "docs/journal/"], root)
    wanted = {line.split(":", 2)[1] for line in (out or "").splitlines() if ":" in line}
    if not wanted:
        return "", ""
    added = _run(
        [
            "git",
            "log",
            "--diff-filter=A",
            "--name-only",
            "--format=%x00",
            ref,
            "--",
            "docs/journal/",
        ],
        root,
    )
    ordered: list[str] = []
    for block in (added or "").split("\0"):
        names = {line for line in block.splitlines() if line}
        ordered += sorted(names, key=lambda name: journal_order(Path(name).name), reverse=True)
    rest = sorted(wanted - set(ordered), key=lambda name: journal_order(Path(name).name))
    found = next((name for name in [*ordered, *reversed(rest)] if name in wanted), None)
    if found is None:
        return "", ""
    return found, journal_next(main_text(root, found) or "")


def ticket_paths(root: Path) -> dict[str, str]:
    """통합 브랜치의 `.scratch` 아래에서 경로에 `/issues/`가 든 `.md` 파일을 이름(확장자를 뗀
    것)마다. 같은 이름이 여럿이면 처음 것이다."""
    ref = integration_ref(root)
    out = _run(["git", "ls-tree", "-r", "--name-only", ref, "--", ".scratch"], root)
    found: dict[str, str] = {}
    for line in (out or "").splitlines():
        if "/issues/" in line and line.endswith(".md"):
            found.setdefault(Path(line).stem, line)
    return found
