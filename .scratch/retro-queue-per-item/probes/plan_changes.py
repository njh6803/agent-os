"""기준 커밋 뒤의 `.scratch/plan.md` 커밋마다 표의 어느 칸을 고쳤는지 센다.

ADR 0045 의 까닭("`plan.md`를 고친 커밋은 Status가 아니라 내용 칸을 고친다")이 근거로 든다.
retro-queue-per-item 설계 인터뷰(일지 2026-11-06-04)에서 세션 스크래치패드의 스크립트로 먼저
세었고, 그 값을 ADR 에 옮기며 여기로 가져왔다(`docs/agents/issue-tracker.md` 프로브와 근거).

재는 것. `git log --format=%h <BASE>..<REF> -- .scratch/plan.md` 가 낸 커밋마다
`git show <h> --format= -- .scratch/plan.md` 의 diff 를 읽어, `-`/`+` 줄 가운데 표의 기능 행
(`|` 로 가른 칸이 다섯이고 첫 칸이 `슬라이스`·`---` 가 아닌 줄)을 slug(둘째 칸)로 짝지어
어느 칸이 달라졌는지(슬라이스, 내용, Blocked by, Status), 행이 새로 들어왔는지(행 추가),
빠졌는지(행 삭제)를 가른다. 바뀐 기능 행이 하나도 없으면 "표 밖"(머리말·프론티어 문단)이다.
커밋 하나가 여러 종류를 고쳤으면 ` + ` 로 이어 하나로 센다. slug 를 바꾼 행은 삭제와 추가로
센다.

기점은 날짜가 아니라 커밋이다. 첫 판은 `git log --since=<날짜>` 로 셌는데, git 의 `--since` 는
날짜만 주면 돌리는 시각의 시분을 붙여 같은 날에도 돌리는 때마다 수가 달랐다(셀프 리뷰 표준 축이
짚었다. 이 PC 의 git 2.32 에서 `--since="2026-10-22 00:00"` 과 `--since="2026-10-22 23:59"` 가 다른
수를 냈다). 그래서 기준 커밋을 받아 `<BASE>..<REF>` 로 센다.

전제(2026-11-05 이 PC 의 git 2.32, 스크래치패드 판의 원본 출력에서 봤다). diff 의 행 줄은
`-| 4 | design-card-build | … |` 처럼 접두 한 글자 뒤에 표 행이 그대로 온다. 칸 안의 `\\|` 는
칸 경계가 아니라 이스케이프라 `(?<!\\\\)\\|` 로 가른다. 표 밖의 `-`/`+` 줄은 칸이 다섯이
아니라 걸러진다.

git 이 0 이 아닌 코드로 끝나면 그 stderr 를 그대로 내보내, 실패가 빈 diff 로 읽히는 것과 가른다.
표지. 커밋이 하나도 없으면 측정이 아니다(기준 커밋이나 가지가 틀렸다). 커밋마다 diff 가 비면
그 회차는 측정이 아니다(git 이 그 커밋의 diff 를 내지 못했다). 측정 아닌 회차가 하나라도
있으면 종료 코드가 1 이다(`.claude/rules/probes.md` 첫 항목, `tools/probe_kit.py` 의 `Rounds`).
"표 밖"은 diff 가 비지 않았는데 바뀐 기능 행이 없는 회차라 따로 표지가 없고, 회차 줄에 찍힌
커밋을 `git show` 로 보면 가른다.

돌리는 법(저장소 루트):
`uv run python .scratch/retro-queue-per-item/probes/plan_changes.py 19bbfa06 origin/main`.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds  # noqa: E402

PLAN = ".scratch/plan.md"
CELL = re.compile(r"(?<!\\)\|")
HEADS = ("슬라이스", "---")
COLUMNS = (("슬라이스", 0), ("내용", 2), ("Blocked by", 3), ("Status", 4))


def git(*args: str) -> str:
    done = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False
    )
    if done.returncode != 0:
        words = " ".join(args)
        print(f"git {words} 실패({done.returncode}): {done.stderr.strip()}", file=sys.stderr)
    return done.stdout


def rows(lines: list[str]) -> dict[str, list[str]]:
    """표의 기능 행만 slug 로 모은다. 칸이 다섯이 아닌 줄과 머리 행은 거른다."""
    out: dict[str, list[str]] = {}
    for line in lines:
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in CELL.split(line)[1:-1]]
        if len(cells) == 5 and cells[0] not in HEADS:
            out[cells[1]] = cells
    return out


def kinds_of(diff: str) -> set[str]:
    removed = rows(
        [ln[1:] for ln in diff.splitlines() if ln.startswith("-") and not ln.startswith("---")]
    )
    added = rows(
        [ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    )
    changed: set[str] = set()
    for slug, new in added.items():
        old = removed.get(slug)
        if old is None:
            changed.add("행 추가")
            continue
        changed.update(name for name, i in COLUMNS if old[i] != new[i])
    if any(slug not in added for slug in removed):
        changed.add("행 삭제")
    return changed or {"표 밖"}


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(f"쓰는 법: {argv[0]} <기준 커밋> <가지>", file=sys.stderr)
        return 2
    base, ref = argv[1], argv[2]
    commits = git("log", "--format=%h", f"{base}..{ref}", "--", PLAN).split()
    if not commits:
        print(f"측정 아님: {base}..{ref} 에 {PLAN} 커밋이 없다")
        return 1
    rounds = Rounds()
    tally: Counter[str] = Counter()
    for commit in commits:
        with rounds.round(commit) as current:
            diff = git("show", commit, "--format=", "--", PLAN)
            if not diff.strip():
                current.mark(measured=False, result="diff 가 비었다")
                continue
            kind = " + ".join(sorted(kinds_of(diff)))
            tally[kind] += 1
            current.mark(measured=True, result=kind)
            print(commit, kind)
    print(f"커밋 {len(commits)}개 ({base}..{ref})")
    for kind, count in tally.most_common():
        print(count, kind)
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
