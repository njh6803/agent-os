"""최근 성공한 ci 실행의 잡별 소요 시간(분)을 잰다. `.github/workflows/ci.yml`의 `timeout-minutes`
값의 근거다(대기열 204).

`gh run list`로 성공한 ci 실행을 최대 N개(기본 40) 받고, 실행마다 잡 목록 API(`filter=latest`)에서
잡의 `started_at`부터 `completed_at`까지를 잰다. 큐에서 기다린 시간은 들지 않는다. 잡의 시간 제한이
이 구간을 센다는 것(컨테이너 초기화 스텝도 잡의 스텝이라 든다)은 재지 않은 어림이다. 모집단이 성공한
실행뿐이라 멈추거나 취소된 실행, 캐시를 놓친 설치가 얼마나 걸리는지는 따로 재지 않는다.

표지: 워크플로의 잡 여섯(python, web, e2e, visual, ticket, verify)이 모두 결론 `success`와 시작·끝
시각을 가져야 그 실행을 측정으로 센다. 건너뛴 잡도 두 시각을 가져 0분 안팎으로 섞이기 때문에
결론까지 본다. 표지가 없는 실행이 하나라도 있거나 측정이 하나도 없으면 1로 끝난다. `ticket` 잡을
들이기 전의 실행에는 그 잡이 없어 측정이 아니다. 그 실행이 아직 최근 N개에 들면 브랜치를 주어 그
잡이 든 실행만 받는다(`gh run list --branch`. PR 의 실행은 머리 브랜치로 걸린다. 2026-10-22 에 PR
#350 의 머리 브랜치를 주어 그 PR 의 `pull_request` 실행 둘이 나온 것을 손으로 봤다).

돌리는 법: 저장소 루트에서 `uv run python .scratch/harness/probes/ci_job_durations.py [N] [브랜치]`.
`gh` 인증이 든다.
"""

import json
import subprocess
import sys
from datetime import datetime

JOBS = ("python", "web", "e2e", "visual", "ticket", "verify")


def gh(*args: str) -> str:
    done = subprocess.run(["gh", *args], capture_output=True, text=True, encoding="utf-8")
    if done.returncode != 0:
        sys.exit(f"gh {' '.join(args)} 가 {done.returncode} 로 끝났다: {done.stderr.strip()}")
    return done.stdout


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def main() -> int:
    limit = sys.argv[1] if len(sys.argv) > 1 else "40"
    branch = ("--branch", sys.argv[2]) if len(sys.argv) > 2 else ()
    runs = json.loads(
        gh(
            "run",
            "list",
            "--workflow",
            "ci",
            "--status",
            "success",
            "--limit",
            limit,
            *branch,
            "--json",
            "databaseId",
        )
    )
    durations: dict[str, list[float]] = {name: [] for name in JOBS}
    unmeasured: list[int] = []
    for run in runs:
        rid = run["databaseId"]
        data = json.loads(
            gh(
                "api",
                f"repos/{{owner}}/{{repo}}/actions/runs/{rid}/jobs?filter=latest&per_page=100",
            )
        )
        got: dict[str, float] = {}
        for job in data["jobs"]:
            if (
                job["name"] in JOBS
                and job["conclusion"] == "success"
                and job["started_at"]
                and job["completed_at"]
            ):
                got[job["name"]] = (
                    ts(job["completed_at"]) - ts(job["started_at"])
                ).total_seconds() / 60
        if set(got) != set(JOBS):
            unmeasured.append(rid)
            continue
        for name, mins in got.items():
            durations[name].append(mins)

    measured = len(runs) - len(unmeasured)
    print(f"성공한 실행 {len(runs)}개 중 측정 {measured}개")
    if unmeasured:
        print(f"잡 여섯이 모두 성공으로 끝나지 않은 실행: {unmeasured}")
    for name in JOBS:
        xs = sorted(durations[name])
        if not xs:
            print(f"{name}: 측정 없음")
            continue
        median = xs[len(xs) // 2]
        spread = f"최소={xs[0]:4.1f} 중앙={median:4.1f} 최대={xs[-1]:4.1f}"
        print(f"{name:7} n={len(xs):2} {spread}")
    return 1 if unmeasured or measured == 0 else 0


if __name__ == "__main__":
    sys.exit(main())
