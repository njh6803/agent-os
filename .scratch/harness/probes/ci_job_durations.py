"""최근 성공한 워크플로 실행의 잡별 소요 시간(분)을 잰다. `.github/workflows/ci.yml`과
`.github/workflows/release.yml`의 `timeout-minutes` 값의 근거다(대기열 204, harness 티켓
`release-followup-timeouts-and-failure-table`).

`gh run list`로 성공한 실행을 최대 N개(기본 40) 받고, 실행마다 잡 목록 API(`filter=latest`)에서
잡의 `started_at`부터 `completed_at`까지를 잰다. 큐에서 기다린 시간은 들지 않는다. 잡의 시간 제한이
이 구간을 센다는 것(컨테이너 초기화 스텝도 잡의 스텝이라 든다)은 재지 않은 어림이다. 모집단이 성공한
실행뿐이라 멈추거나 취소된 실행, 캐시를 놓친 설치가 얼마나 걸리는지는 따로 재지 않는다.

표지: ci 워크플로의 잡 여섯(`JOBS`: python, web, e2e, visual, ticket, verify)이 모두 결론
`success`와 시작·끝 시각을 가져야 그 실행을 측정으로 센다. 건너뛴 잡도 두 시각을 가져 0분 안팎으로
섞이기 때문에 결론까지 본다. 표지가 없는 실행이 하나라도 있거나 측정이 하나도 없으면 1로 끝난다.
`ticket` 잡을 들이기 전의 실행에는 그 잡이 없어 측정이 아니다. 그 실행이 아직 최근 N개에 들면
브랜치를 주어 그 잡이 든 실행만 받는다(`gh run list --branch`. PR 의 실행은 머리 브랜치로 걸린다.
2026-10-22 에 PR #350 의 머리 브랜치를 주어 그 PR 의 `pull_request` 실행 둘이 나온 것을 손으로
봤다). 브랜치를 주면 `--status success` 대신 `completed` 로 받아 결론으로 거른다. 실행 목록 API
(`actions/workflows/ci.yml/runs`)에 `branch` 와 `status=success` 를 함께 주면 성공한 실행이 있는
브랜치 둘(PR #350 과 #355 의 머리)에서 모두 0개였고, `status=completed` 나 `status` 없이는 그 실행이
나왔다(2026-10-22 손으로 봤다).

조건부 잡(`GATED`): ci 의 `e2e-standalone` 은 base 가 main 인 PR 과 main 푸시에서만 시험하고 그
밖에서는 첫 스텝이 판정해 나머지를 건너뛴 채 몇 초 만에 성공으로 끝난다(ci.yml 의 그 잡 위 주석). 그
실행은 시험을 돌지 않았으므로 측정이 아니다. 시험 스텝(이름에 표지 문구가 든 스텝)의 결론이
`success` 인 실행만 그 잡의 측정으로 세고, 그렇지 않은 실행은 "시험 안 돈 실행"으로 따로 센다.
조건부 잡은 `JOBS` 여섯의 표지에 들지 않아, 시험이 없는 실행이 나머지 잡의 측정을 가리지 않는다.

release 워크플로(`--release`): `build` 와 `publish` 를 잰다(`RELEASE_JOBS`). 제품 변경이 없는
푸시에서는 첫 잡이 판 내기 단계를 건너뛴 채 성공으로 끝나고 둘째 잡은 건너뛴다. 그래서 두 잡 모두
표지 스텝(`build` 는 `아티팩트 올리기`, `publish` 는 `공개`)의 결론이 `success` 인 실행만 측정으로
센다. 두 잡이 모두 표지를 가진 실행만 측정이고, 그렇지 않은 성공 실행은 "판 안 낸 실행"으로 센다.
`--release` 에서는 실행 수(성공한 실행 가운데 판을 낸 것)가 적어 N 을 크게 줄 필요가 없다.

못 보는 것: `e2e-standalone` 의 표지는 스텝 이름의 부분 문자열로 가른다. 그 시험 스텝은 이름이 없어
자동 이름(`Run pnpm … exec playwright test`)에 기대므로 스텝에 이름을 붙이면 표지가 맞지 않아 그
잡의 측정이 0이 되고 종료 코드가 1이다. release 의 표지는 스텝 이름 전체 일치로 가른다. release.yml
의 publish 잡에는 이름에 `공개` 를 담은 스텝이 둘(`공개`, `이미 공개된 판`)이라 부분 일치로 가르면
새로 내지 않은 실행이 섞인다(PR 직전 리뷰가 release.yml 을 읽어 짚었다. 부분 일치 판의 결과는 돌려
보지 않았다). 표지 스텝의 이름을 바꾸면 release 쪽 측정이 0이 되고 종료 코드가 1이다.

돌리는 법: 저장소 루트에서 `uv run python .scratch/harness/probes/ci_job_durations.py [N] [브랜치]`
(ci), `uv run python .scratch/harness/probes/ci_job_durations.py --release [N]` (release).
`gh` 인증이 든다.
"""

import json
import subprocess
import sys
import time
from datetime import datetime

JOBS = ("python", "web", "e2e", "visual", "ticket", "verify")
# 조건부 잡: 잡 이름 -> 시험을 돌았다는 표지 스텝 이름의 한 토막
GATED = {"e2e-standalone": "e2e-standalone exec playwright test"}
# release 워크플로: 잡 이름 -> 판을 냈다는 표지 스텝 이름
RELEASE_JOBS = {"build": "아티팩트 올리기", "publish": "공개"}


def gh(*args: str) -> str:
    # 일시 장애(HTTP 502 를 한 번 봤다, 2026-11-17)나 호출 하나의 멈춤으로 백 번 가까운 호출
    # 전체가 죽지 않게 세 번까지 다시 친다
    problem = ""
    for attempt in range(3):
        if attempt:
            time.sleep(3)
        try:
            done = subprocess.run(
                ["gh", *args], capture_output=True, text=True, encoding="utf-8", timeout=120
            )
        except subprocess.TimeoutExpired:
            problem = "120초 안에 끝나지 않았다"
            continue
        if done.returncode == 0:
            return done.stdout
        problem = f"{done.returncode} 로 끝났다: {done.stderr.strip()}"
    sys.exit(f"gh {' '.join(args)} 가 {problem}")


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def minutes(job: dict[str, object]) -> float | None:
    started, completed = job["started_at"], job["completed_at"]
    if job["conclusion"] != "success" or not isinstance(started, str):
        return None
    if not isinstance(completed, str):
        return None
    return (ts(completed) - ts(started)).total_seconds() / 60


def ran_marker(job: dict[str, object], marker: str, *, exact: bool = False) -> bool:
    steps = job["steps"]
    assert isinstance(steps, list)
    return any(
        (step["name"] == marker if exact else marker in step["name"])
        and step["conclusion"] == "success"
        for step in steps
    )


def report(title: str, durations: dict[str, list[float]]) -> None:
    for name, values in durations.items():
        xs = sorted(values)
        if not xs:
            print(f"{title}{name}: 측정 없음")
            continue
        median = xs[len(xs) // 2]
        spread = f"최소={xs[0]:5.1f} 중앙={median:5.1f} 최대={xs[-1]:5.1f}"
        print(f"{title}{name:15} n={len(xs):2} {spread}")


def measure_ci(limit: str, branch: tuple[str, ...]) -> int:
    # 브랜치와 함께 주면 success 거르기가 빈 목록을 낸다(독스트링). 그때는 끝난 실행을 받아
    # 결론으로 거른다
    status = "completed" if branch else "success"
    listed = json.loads(
        gh(
            "run",
            "list",
            "--workflow",
            "ci",
            "--status",
            status,
            "--limit",
            limit,
            *branch,
            "--json",
            "databaseId,conclusion",
        )  # fmt: skip
    )
    runs = [run for run in listed if run["conclusion"] == "success"]
    durations: dict[str, list[float]] = {name: [] for name in JOBS}
    gated: dict[str, list[float]] = {name: [] for name in GATED}
    gated_ids: dict[str, list[int]] = {name: [] for name in GATED}
    unmeasured: list[int] = []
    not_run = 0
    absent = 0
    for run in runs:
        rid = run["databaseId"]
        data = json.loads(
            gh(
                "api",
                f"repos/{{owner}}/{{repo}}/actions/runs/{rid}/jobs?filter=latest&per_page=100",
            )
        )
        got: dict[str, float] = {}
        gated_seen = False
        for job in data["jobs"]:
            mins = minutes(job)
            if job["name"] in JOBS and mins is not None:
                got[job["name"]] = mins
            elif job["name"] in GATED and mins is not None:
                gated_seen = True
                if ran_marker(job, GATED[job["name"]]):
                    gated[job["name"]].append(mins)
                    gated_ids[job["name"]].append(rid)
                else:
                    not_run += 1
        if not gated_seen:
            # 조건부 잡이 없던 시기의 실행이거나 그 잡이 성공으로 끝나지 않은 실행
            absent += 1
        if set(got) != set(JOBS):
            unmeasured.append(rid)
            continue
        for name, mins in got.items():
            durations[name].append(mins)

    measured = len(runs) - len(unmeasured)
    print(f"성공한 실행 {len(runs)}개 중 측정 {measured}개")
    if unmeasured:
        print(f"잡 여섯이 모두 성공으로 끝나지 않은 실행: {unmeasured}")
    report("", durations)
    ran = sum(len(ids) for ids in gated_ids.values())
    print(
        f"조건부 잡: 시험이 든 실행 {ran}개, 시험 안 돈 실행 {not_run}개, "
        f"그 잡이 없거나 성공이 아닌 실행 {absent}개 "
        f"(합 {ran + not_run + absent}, 성공한 실행 {len(runs)}개)"
    )
    report("", gated)
    for name, ids in gated_ids.items():
        print(f"{name} 시험이 든 실행: {ids}")
    # 조건부 잡이 하나도 측정되지 않았으면 표지를 가진 회차가 없는 것이라 0 으로 끝내지 않는다
    return 1 if unmeasured or measured == 0 or not all(gated.values()) else 0


def measure_release(limit: str) -> int:
    listed = json.loads(
        gh(
            "run",
            "list",
            "--workflow",
            "release",
            "--status",
            "success",
            "--limit",
            limit,
            "--json",
            "databaseId",
        )  # fmt: skip
    )
    durations: dict[str, list[float]] = {name: [] for name in RELEASE_JOBS}
    released: list[int] = []
    skipped: list[int] = []
    for run in listed:
        rid = run["databaseId"]
        data = json.loads(
            gh(
                "api",
                f"repos/{{owner}}/{{repo}}/actions/runs/{rid}/jobs?filter=latest&per_page=100",
            )
        )
        got: dict[str, float] = {}
        for job in data["jobs"]:
            mins = minutes(job)
            marker = RELEASE_JOBS.get(job["name"])
            if marker is not None and mins is not None and ran_marker(job, marker, exact=True):
                got[job["name"]] = mins
        if set(got) != set(RELEASE_JOBS):
            skipped.append(rid)
            continue
        released.append(rid)
        for name, mins in got.items():
            durations[name].append(mins)
    print(f"성공한 실행 {len(listed)}개 중 판을 낸 실행 {len(released)}개: {released}")
    print(f"판 안 낸 실행 {len(skipped)}개")
    report("release ", durations)
    return 1 if not released else 0


def main() -> int:
    args = sys.argv[1:]
    if args and args[0] == "--release":
        return measure_release(args[1] if len(args) > 1 else "40")
    limit = args[0] if args else "40"
    branch = ("--branch", args[1]) if len(args) > 1 else ()
    return measure_ci(limit, branch)


if __name__ == "__main__":
    sys.exit(main())
