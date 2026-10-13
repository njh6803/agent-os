"""PR마다 CI(`ci` 워크플로)가 몇 번 돌았고, 각 실행을 부른 커밋이 무엇이었는지 가른다.

PR 번호 범위를 받아 `gh pr view <N> --json headRefName,commits`와 `gh run list --workflow ci
--branch <브랜치> --event pull_request --json headSha,conclusion,createdAt`을 읽는다. 실행마다 그
헤드 커밋의 제목으로 가른다. `Merge`로 시작하면 main 합치기, 가장 이른 실행이면 첫 푸시, 나머지는
수정이다. 같은 헤드의 실행이 여럿이면(다시 돌리기) 다시로 센다. 취소(`cancelled`)는 푸시가 이어져
concurrency가 앞 실행을 끊은 것이다.

main 합치기는 다시 둘로 가른다. 그 합치기 커밋의 두 부모를 옛 `git merge-tree <base> <ours>
<theirs>`(git 2.32에 있는 판)로 다시 합쳐 출력에 충돌 표지(`<<<<<<<`)가 있으면 충돌, 없으면 뒤처짐만
이다. 뒤처짐만인 합치기는 보호 규칙의 strict(필수 검사가 최신 main 위에서 돌아야 병합된다,
`tools/protection.json`)가 부른 것으로 어림한다. 합친 까닭은 재지 않으므로 다른 까닭(새 규약을
받으려고 일찍 합친 것)도 이 갈래에 섞인다. 충돌이면 표지가 든 파일을 함께 센다. 커밋은
`git fetch origin pull/<N>/head`로 받는다(FETCH_HEAD만 쓴다).

한 줄에 PR 번호, 실행 수, 갈래별 수를 찍고, 끝에 합계와 충돌 파일의 빈도를 찍는다. 읽지 못한 PR이
있으면 1로 끝난다.

못 보는 것: 충돌로 CI가 아예 돌지 않은 헤드(실행이 없어 세지 않는다). 옛 merge-tree는 이름 바꾸기를
모르고 파일 단위의 3자 합치기만 하므로, 실제 `git merge`가 풀었을 충돌을 충돌로 셀 수 있다. 실행
기록이 지워진 PR.

쓰임: `uv run python .scratch/harness/probes/ci_wait/runs_per_pr.py 196 220`
"""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


def text(value: Json) -> str:
    return value if isinstance(value, str) else ""


def gh(*args: str) -> Json:
    completed = subprocess.run(["gh", *args], capture_output=True, encoding="utf-8", check=False)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.strip())
    payload: Json = json.loads(completed.stdout)
    return payload


def git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args], capture_output=True, encoding="utf-8", errors="replace", check=True
    )
    return completed.stdout


def conflicted_files(merge_sha: str) -> list[str]:
    """합치기 커밋의 두 부모를 다시 합쳐 충돌 표지가 든 파일을 낸다. 없으면 빈 목록."""
    parents = git("rev-list", "--parents", "-n", "1", merge_sha).split()[1:]
    if len(parents) != 2:
        return []
    ours, theirs = parents
    base = git("merge-base", ours, theirs).strip()
    files: list[str] = []
    path = ""
    for line in git("merge-tree", base, ours, theirs).splitlines():
        if line.startswith(("  base ", "  our ", "  their ")):
            path = line.split()[-1]
        elif "<<<<<<<" in line and path and path not in files:
            files.append(path)
    return files


def main(argv: list[str]) -> int:
    first, last = int(argv[1]), int(argv[2])
    total: Counter[str] = Counter()
    hot: Counter[str] = Counter()
    unread: list[int] = []
    for number in range(first, last + 1):
        try:
            pr = gh("pr", "view", str(number), "--json", "headRefName,commits")
        except RuntimeError as error:
            print(f"#{number} 읽지 못함: {error}")
            unread.append(number)
            continue
        if not isinstance(pr, dict):
            continue
        git("fetch", "-q", "origin", f"pull/{number}/head")
        branch = text(pr.get("headRefName"))
        raw = pr.get("commits")
        commits = [c for c in raw if isinstance(c, dict)] if isinstance(raw, list) else []
        headline = {text(c.get("oid")): text(c.get("messageHeadline")) for c in commits}
        runs = gh(
            "run",
            "list",
            "--workflow",
            "ci",
            "--branch",
            branch,
            "--event",
            "pull_request",
            "--limit",
            "100",
            "--json",
            "headSha,conclusion,createdAt",
        )
        runs_list = [r for r in runs if isinstance(r, dict)] if isinstance(runs, list) else []
        runs_list.sort(key=lambda r: text(r.get("createdAt")))
        kinds: Counter[str] = Counter()
        seen: set[str] = set()
        notes: list[str] = []
        for index, run in enumerate(runs_list):
            sha = text(run.get("headSha"))
            if sha in seen:
                kind = "다시"
            elif index == 0:
                kind = "첫 푸시"
            elif headline.get(sha, "").startswith("Merge"):
                files = conflicted_files(sha)
                kind = "합치기(충돌)" if files else "합치기(뒤처짐만)"
                hot.update(files)
                if files:
                    notes.append(f"{sha[:7]} {' '.join(files)}")
            else:
                kind = "수정"
            seen.add(sha)
            kinds[kind] += 1
            if text(run.get("conclusion")) == "cancelled":
                kinds["(그중 취소)"] += 1
        total.update(kinds)
        total["PR"] += 1
        cells = ", ".join(f"{k} {v}" for k, v in sorted(kinds.items()))
        tail = f" | 충돌: {'; '.join(notes)}" if notes else ""
        print(f"#{number} 실행 {len(runs_list)}: {cells}{tail}")
    print(f"합계: {', '.join(f'{k} {v}' for k, v in sorted(total.items()))}")
    print(f"충돌 파일 빈도: {', '.join(f'{k} {v}' for k, v in hot.most_common()) or '없음'}")
    if unread:
        print(f"읽지 못한 PR: {unread}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
