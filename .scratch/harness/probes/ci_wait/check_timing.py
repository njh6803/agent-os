"""PR마다 검사 이름과 끝난 시각, CodeRabbit 상태의 이력을 찍는다. `tools/wait_ci.py`의 근거.

PR 번호 범위를 받아 `gh pr view <N> --json headRefOid,isDraft,statusCheckRollup`을 읽고, 한 줄에 PR
번호, 첫 검사가 시작한 시각, 검사마다 `<이름>=<끝난 시각>`을 찍는다. 끝나지 않았으면 `<이름>=…`이다.
롤업은 지금 헤드의 검사라, 첫 시작은 그 헤드를 푸시한 무렵이다(CheckRun의 `startedAt` 가운데 가장
이른 것). CheckRun은 끝났을 때의 `completedAt`을, StatusContext는 끝난 상태의 `startedAt`을 끝난
시각으로 본다. StatusContext에는 `completedAt`이 없고, `startedAt`은 그 상태를 마지막으로 쓴
시각이다.

롤업은 상태의 설명을 싣지 않는다. 그래서 헤드 커밋의 상태 이력
(`gh api repos/{owner}/{repo}/commits/<헤드>/statuses`)에서 CodeRabbit의 것을 시각 순으로
`상태:설명@시각`으로 둘째 줄에 찍는다. 끝의 줄들은 CodeRabbit 상태가 없는 PR, 설명의 종류별 빈도,
첫 시작에서 `verify`가 끝나기까지의 분, 첫 시작에서 CodeRabbit의 마지막 상태가 `Review skipped`로
시작하지 않는 끝난 상태가 되기까지의 분(리뷰를 마쳤거나 한도에 걸린 때), 건너뜀 상태에서 처음
`Review in progress`가 되기까지의 초(리뷰 요청이 닿은 때)다. 읽지 못한 PR이 있으면 1로 끝난다.

쓰임: `uv run python .scratch/harness/probes/ci_wait/check_timing.py 196 220`
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import datetime

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


def text(value: Json) -> str:
    return value if isinstance(value, str) else ""


def gh(*args: str) -> Json:
    completed = subprocess.run(["gh", *args], capture_output=True, encoding="utf-8", check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip())
    payload: Json = json.loads(completed.stdout)
    return payload


def finished_at(check: dict[str, Json]) -> str:
    # 진행 중인 CheckRun의 completedAt은 비지 않고 `0001-01-01T00:00:00Z`다
    # (PR #219·#220, 2026-10-13).
    if text(check.get("__typename")) == "CheckRun":
        return text(check.get("completedAt")) if check.get("status") == "COMPLETED" else ""
    if text(check.get("state")) in ("PENDING", "EXPECTED"):
        return ""
    return text(check.get("startedAt"))


def seconds(start: str, end: str) -> float:
    return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()


def minutes(start: str, end: str) -> str:
    return f"{seconds(start, end) / 60:.1f}"


def coderabbit_history(head: str) -> list[tuple[str, str, str]]:
    """헤드의 CodeRabbit 상태를 오래된 것부터 (상태, 설명, 시각)으로 낸다."""
    statuses = gh("api", f"repos/{{owner}}/{{repo}}/commits/{head}/statuses")
    rows = [s for s in statuses if isinstance(s, dict)] if isinstance(statuses, list) else []
    history = [
        (text(s.get("state")), text(s.get("description")), text(s.get("created_at")))
        for s in rows
        if text(s.get("context")) == "CodeRabbit"
    ]
    return sorted(history, key=lambda row: row[2])


def main(argv: list[str]) -> int:
    first, last = int(argv[1]), int(argv[2])
    missing: list[int] = []
    kinds: Counter[str] = Counter()
    to_verify: list[str] = []
    to_review: list[str] = []
    to_request: list[str] = []
    unread: list[int] = []
    for number in range(first, last + 1):
        try:
            payload = gh(
                "pr", "view", str(number), "--json", "headRefOid,isDraft,statusCheckRollup"
            )
        except RuntimeError as error:
            print(f"#{number} 읽지 못함: {error}")
            unread.append(number)
            continue
        if not isinstance(payload, dict):
            continue
        rollup = payload.get("statusCheckRollup")
        checks = [c for c in rollup if isinstance(c, dict)] if isinstance(rollup, list) else []
        starts = [
            text(c.get("startedAt"))
            for c in checks
            if text(c.get("__typename")) == "CheckRun" and text(c.get("startedAt"))
        ]
        start = min(starts) if starts else ""
        cells: list[str] = []
        ends: dict[str, str] = {}
        for check in checks:
            name = text(check.get("name")) or text(check.get("context"))
            end = finished_at(check)
            cells.append(f"{name}={end[11:19] or '…'}")
            ends[name] = end
        draft = " draft" if payload.get("isDraft") is True else ""
        print(f"#{number}{draft} 첫 시작 {start[11:19] or '…'} {' '.join(cells)}")
        history = coderabbit_history(text(payload.get("headRefOid")))
        print("    CodeRabbit " + " → ".join(f"{s}:{d}@{t[11:19]}" for s, d, t in history))
        if not history:
            missing.append(number)
        kinds.update(d.split(":")[0] for _, d, _ in history)
        if start and ends.get("verify"):
            to_verify.append(f"#{number} {minutes(start, ends['verify'])}")
        state, description, at = history[-1] if history else ("", "", "")
        if start and state not in ("", "pending") and not description.startswith("Review skipped"):
            to_review.append(f"#{number} {minutes(start, at)}({description})")
        skipped = [t for _, d, t in history if d.startswith("Review skipped")]
        progressed = [t for _, d, t in history if d == "Review in progress"]
        if skipped and progressed:
            to_request.append(f"#{number} {seconds(skipped[0], progressed[0]):.0f}")
    print(f"CodeRabbit 없음: {missing or '없음'}")
    print(f"CodeRabbit 설명의 빈도: {', '.join(f'{k} {v}' for k, v in kinds.most_common())}")
    print(f"첫 시작에서 verify 까지(분): {', '.join(to_verify)}")
    print(f"첫 시작에서 CodeRabbit 의 건너뜀 아닌 끝까지(분): {', '.join(to_review)}")
    print(f"건너뜀에서 진행까지(초): {', '.join(to_request)}")
    if unread:
        print(f"읽지 못한 PR: {unread}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
