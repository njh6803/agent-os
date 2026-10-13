"""PR의 검사와 리뷰 봇이 모두 끝날 때까지 기다렸다가 결과를 한 번 찍고 끝난다.

Bash 도구의 `run_in_background`로 띄운다. 그 도구는 띄운 명령이 끝나면 세션을 다시 부르므로
(2026-10-13 데스크톱 앱 세션에 실린 Bash 도구 설명을 읽었다), 사람이 "CI 끝났어"로 깨우던
자리를 이 도구의 종료가 맡는다. 기다리는 동안 모델은 돌지 않는다.

왜 앱의 감시로 안 되나. 앱의 PR 감시(auto_fix)가 세션을 깨우는 계기로 도구 설명이 드는 것은 CI
실패, 충돌, 리뷰 코멘트이고 초록 완료는 들지 않는다(같은 날 읽은 `set_monitor` 도구 설명). PR
구독은 연 지 몇 분 뒤에 생겨 그 전에 끝난 첫 푸시의 CI는 알림이 없었다(대기열 37의 4회차). 앱 지침은
세션이 CI를 스케줄하거나 `gh`로 폴링하지 말라고 하는데, 이 도구는 그 지침과 어긋난다. 사용자가 자동
대기를 요청해 들였다(일지 2026-10-13-38). 앱의 감시가 초록 완료로도 깨우게 되면 이 도구를 걷어 낸다.

CodeRabbit의 상태. 푸시마다 리뷰 없이 `success`와 설명 `Review skipped: …`를 먼저 달고,
`@coderabbitai review`를 남기면 `pending`(`Review in progress`)을 거쳐 `success`의 `Review rate
limited`(한도 초과, 리뷰 없음)나 `Review completed`로 끝난다. 롤업의 상태만 보면 셋 다 SUCCESS라
설명을 함께 읽는다. 시간과 빈도는 `.scratch/harness/probes/ci_wait/check_timing.py`와 그 README 행이
원천이다.

판정. `gh pr view <N> --json headRefOid,mergeable,statusCheckRollup`과 그 헤드의 combined
status(`gh api repos/{owner}/{repo}/commits/<헤드>/status`, 맥락마다 마지막 상태와 설명)를
`interval`초마다 읽는다. gh 호출 하나는 `GH_TIMEOUT`초에서 끊고 조회 실패로 센다. 멈춘 gh는
돌아오지 않아 대기의 시간 제한에도 걸리지 않는다(PR 직전 버그 리뷰). StatusContext의 상태는
설명과 같은 combined status에서 읽는다. 따로 읽은 롤업은 시각이 달라, 롤업의 건너뜀 SUCCESS와
combined의 `Review in progress`가 함께 오면 통과로 읽힌다.
- PR 헤드가 로컬 `HEAD`(`--head`로 바꾼다)와 다르면 기다린다. 푸시 직후에는 PR이 옛 헤드를
  가리켜, 옛 헤드의 초록을 보고 끝나면 초록 착시다. 처음부터 다른 채 `head_grace`초가 지나면
  기다릴 수 없다고 끝나고(푸시하지 않았거나 다른 커밋을 푸시했다), 같다가 바뀌면 새 푸시라 곧바로
  끝난다.
- 기대 이름(`EXPECTED`, `--expect`로 바꾼다)이 모두 나타났고, 나타난 검사가 모두 끝났고, 설명이
  `UNREQUESTED_PREFIX`로 시작하는 상태가 없으면 끝이다. 나타난 것만 보면 푸시 직후의 빈 목록이나
  아직 붙지 않은 검사 앞에서 끝났다고 한다. `verify`는 CI 잡을 모으는 잡이다.
- 나머지가 다 끝났는데 대기를 띄운 지 `request_grace`초(90)가 지나도 건너뜀 상태가 남았으면 리뷰를
  요청하지 않은 것이라 기다리지 않는다. 요청이 닿아 `Review in progress`가 되기까지 수십 초가
  걸려(같은 프로브), 요청하고 곧바로 다시 띄운 대기의 첫 조회는 아직 건너뜀을 볼 수 있다.
  `verify`는 needs가 끝난 뒤에야 롤업에 나타났다(PR #223에서 `gh pr checks`로 손으로 봤다).
- 나머지가 다 끝났고 실패가 있으면 리뷰 요청을 기다리지 않고 실패로 끝난다. 고쳐서 다시 푸시할
  헤드라 요청은 한도만 쓴다.
- 충돌이면 기다리지 않는다. 충돌한 PR에는 `pull_request` 워크플로가 돌지 않고(일지 2026-10-12-34),
  끝난 검사가 있어도 main을 합쳐야 병합할 수 있다.
- 끝난 검사의 결과가 `PASSING`이면 통과, 그 밖은 실패다. 같은 이름이 둘이면 끝나지 않은 쪽,
  다음으로 실패한 쪽을 든다.

종료 코드는 0 통과, 1 실패나 충돌, 2 인자 오류, 3 시간 초과, 4 기다릴 수 없음(gh가 연달아
실패했다, 헤드가 다르거나 바뀌었다, 리뷰가 요청되지 않았다, 로컬 HEAD를 읽지 못했다)이다. 출력의
마지막 줄은 `끝:`으로 시작하는 결과와 다음 할 일 한 줄이다. 통과면 상태의 설명(리뷰를 했는지)을
붙인다. 예외는 argparse가 직접 찍는 인자 오류다.

못 보는 것.
- 기대 이름 밖에서 늦게 붙는 검사. 다른 검사가 다 끝난 뒤에 나타나면 그 전에 끝났다고 한다.
- 이름이 바뀐 기대 검사. 끝내 나타나지 않아 시간 초과로 끝나고, 출력에 빠진 이름을 적는다.
- 요청이 늦게 닿은 리뷰. 나머지 검사가 끝나고 요청 유예가 지날 때까지 건너뜀 상태면 요청이 없다고
  끝난다.
- 충돌은 한 번의 조회로 판정한다. 충돌을 풀고 푸시한 직후의 조회가 옛 헤드 기준의 `CONFLICTING`을
  읽는지는 재지 않았다. 틀리면 대기를 한 번 더 띄운다.
- 리뷰 코멘트의 내용과, claude-review가 계정 한도로 빨간 것과 진짜 실패의 차이. 끝났다는 것만
  알리고, 나머지는 깨어난 세션이 읽는다(`docs/constitution/operations.md` 리뷰 파이프라인 3).
- 같은 이름의 재실행. 실패 뒤 다시 돌아 통과한 검사가 옛 실패와 함께 남으면 실패로 든다.
- 세션이 꺼진 뒤의 완료. 대기는 그 세션의 백그라운드 작업이다. 세션을 닫은 뒤 대기가 어떻게
  되는지는 재지 않았다.

쓰임: `uv run python tools/wait_ci.py <PR 번호>`를 Bash 도구의 `run_in_background`로 띄운다.
`--expect`는 이 도구를 복사한 저장소(KICKOFF.md)가 자기 검사 이름을 줄 때, `--interval`은 손으로
돌려 볼 때 쓴다.
"""

from __future__ import annotations

import argparse
import io
import json
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

EXPECTED = ("verify", "claude-review", "CodeRabbit")
PASSING = frozenset({"SUCCESS", "NEUTRAL", "SKIPPED"})
# StatusContext 의 끝나지 않은 상태. CheckRun 은 status 가 COMPLETED 인지로 본다.
PENDING_STATES = frozenset({"PENDING", "EXPECTED"})
# 리뷰를 요청받기 전의 CodeRabbit 상태 설명. 상태는 SUCCESS 라 결과만 보면 끝난 것으로 읽힌다.
UNREQUESTED_PREFIX = "Review skipped"
# gh 호출 하나의 시간 제한(초). 멈춘 gh 는 돌아오지 않아 대기의 시간 제한에도 걸리지 않는다.
GH_TIMEOUT = 60.0

EXIT_PASSED = 0
EXIT_FAILED = 1
EXIT_USAGE = 2
EXIT_TIMED_OUT = 3
EXIT_CANNOT_WAIT = 4


class FetchError(Exception):
    """gh 가 PR 이나 상태를 읽지 못했다."""


@dataclass(frozen=True)
class Snapshot:
    """한 번 읽은 PR.

    checks 는 이름에서 결과로 가고, 끝나지 않은 검사는 None 이다. notes 는 StatusContext 의
    이름에서 마지막 상태의 설명으로 간다.
    """

    head: str
    conflicting: bool
    checks: dict[str, str | None]
    notes: dict[str, str]


@dataclass(frozen=True)
class Verdict:
    done: bool
    failed: tuple[str, ...]
    pending: tuple[str, ...]
    missing: tuple[str, ...]
    unrequested: tuple[str, ...]


@dataclass(frozen=True)
class Options:
    expected: tuple[str, ...]
    timeout: float
    interval: float
    head_grace: float
    request_grace: float
    max_fetch_errors: int


def _text(value: Json) -> str:
    return value if isinstance(value, str) else ""


def _result(check: dict[str, Json]) -> tuple[str, str | None]:
    if _text(check.get("__typename")) == "StatusContext":
        state = _text(check.get("state"))
        return _text(check.get("context")), None if state in PENDING_STATES else state
    # 진행 중인 CheckRun 의 completedAt 은 비지 않고 0001-01-01T00:00:00Z 라 보지 않는다.
    name = _text(check.get("name"))
    if _text(check.get("status")) != "COMPLETED":
        return name, None
    return name, _text(check.get("conclusion")) or "UNKNOWN"


def _worse(left: str | None, right: str | None) -> str | None:
    if left is None or right is None:
        return None
    return right if left in PASSING else left


def parse_snapshot(payload: Json) -> Snapshot:
    """`fetch_pr` 의 출력(PR 의 세 칸과 combined status 의 `statuses`)을 읽는다."""
    if not isinstance(payload, dict):
        raise FetchError(f"PR 응답이 객체가 아니다: {payload!r}")
    rollup = payload.get("statusCheckRollup")
    checks: dict[str, str | None] = {}
    for check in rollup if isinstance(rollup, list) else []:
        if not isinstance(check, dict):
            continue
        name, result = _result(check)
        checks[name] = _worse(checks[name], result) if name in checks else result
    # StatusContext 의 상태는 설명과 같은 combined status 에서 읽는다. 롤업은 따로 읽어 시각이
    # 달라, 롤업의 건너뜀 SUCCESS 와 combined 의 Review in progress 가 함께 오면 통과로 읽힌다.
    statuses = payload.get("statuses")
    notes: dict[str, str] = {}
    for status in statuses if isinstance(statuses, list) else []:
        if not isinstance(status, dict):
            continue
        name = _text(status.get("context"))
        state = _text(status.get("state")).upper()
        notes[name] = _text(status.get("description"))
        if state:
            checks[name] = None if state in PENDING_STATES else state
    return Snapshot(
        head=_text(payload.get("headRefOid")),
        conflicting=payload.get("mergeable") == "CONFLICTING",
        checks=checks,
        notes=notes,
    )


def judge(snapshot: Snapshot, expected: Sequence[str]) -> Verdict:
    pending = tuple(name for name, result in snapshot.checks.items() if result is None)
    failed = tuple(
        name
        for name, result in snapshot.checks.items()
        if result is not None and result not in PASSING
    )
    missing = tuple(name for name in expected if name not in snapshot.checks)
    unrequested = tuple(
        name for name, note in snapshot.notes.items() if note.startswith(UNREQUESTED_PREFIX)
    )
    return Verdict(
        done=not pending and not missing and not unrequested,
        failed=failed,
        pending=pending,
        missing=missing,
        unrequested=unrequested,
    )


def _report(number: str, snapshot: Snapshot) -> list[str]:
    lines = [f"PR #{number} 헤드 {snapshot.head[:7]}"]
    for name, result in sorted(snapshot.checks.items()):
        note = f" ({snapshot.notes[name]})" if snapshot.notes.get(name) else ""
        lines.append(f"  {name} {'진행 중' if result is None else result}{note}")
    return lines


def _settle(
    number: str, snapshot: Snapshot, elapsed: float, options: Options
) -> tuple[int, list[str]] | None:
    """헤드가 맞는 PR 로 끝낼지 정한다. 더 기다리면 None."""
    verdict = judge(snapshot, options.expected)
    lines = _report(number, snapshot)
    if snapshot.conflicting:
        return EXIT_FAILED, [*lines, "끝: 충돌. main 을 합치고 푸시한 뒤 다시 띄운다"]
    settled = not verdict.pending and not verdict.missing
    # 실패가 있으면 리뷰 요청을 기다리지 않는다. 고쳐서 다시 푸시할 헤드라 요청은 한도만 쓴다.
    if settled and verdict.failed:
        return EXIT_FAILED, [*lines, f"끝: 실패 {', '.join(verdict.failed)}"]
    if verdict.done:
        notes = "".join(f". {name}: {note}" for name, note in sorted(snapshot.notes.items()))
        return EXIT_PASSED, [*lines, f"끝: 모두 통과{notes}"]
    # 요청 직후에 띄운 대기의 첫 조회는 아직 건너뜀을 볼 수 있어 요청 유예를 둔다.
    if settled and elapsed >= options.request_grace:
        names = ", ".join(verdict.unrequested)
        return EXIT_CANNOT_WAIT, [
            *lines,
            f"끝: {names} 리뷰가 요청되지 않았다. `@coderabbitai review` 를 남기고 다시 띄운다",
        ]
    if elapsed < options.timeout:
        return None
    waiting = [
        *verdict.pending,
        *(f"{name}(나타나지 않음)" for name in verdict.missing),
        *(f"{name}(요청되지 않음)" for name in verdict.unrequested),
    ]
    minutes = options.timeout / 60
    return EXIT_TIMED_OUT, [
        *lines,
        f"끝: 시간 초과 {minutes:.0f}분. 남은 것 {', '.join(waiting)}. "
        "`gh pr checks` 로 멈춘 잡인지 보고 사람에게 알린다",
    ]


def wait(
    number: str,
    head: str,
    options: Options,
    fetch: Callable[[str], Json],
    sleep: Callable[[float], None],
    clock: Callable[[], float],
) -> tuple[int, list[str]]:
    """검사가 끝날 때까지 PR 읽기와 `interval`초 잠자기를 되풀이한다. 종료 코드와 찍을 줄을 낸다."""
    started = clock()
    errors: list[str] = []
    seen_head = False
    while True:
        elapsed = clock() - started
        try:
            snapshot = parse_snapshot(fetch(number))
        except FetchError as error:
            errors.append(str(error))
            if len(errors) >= options.max_fetch_errors:
                return EXIT_CANNOT_WAIT, [
                    *errors,
                    f"끝: gh 가 연달아 {len(errors)}번 실패했다. 위 오류를 사람에게 알린다",
                ]
        else:
            errors.clear()
            if snapshot.head == head:
                seen_head = True
                settled = _settle(number, snapshot, elapsed, options)
                if settled is not None:
                    return settled
            elif seen_head:
                return EXIT_CANNOT_WAIT, [
                    f"끝: PR #{number} 헤드가 {head[:7]} 에서 {snapshot.head[:7]} 로 바뀌었다. "
                    "새 푸시면 새 헤드로 대기를 다시 띄운다"
                ]
            elif elapsed >= options.head_grace:
                return EXIT_CANNOT_WAIT, [
                    f"끝: PR #{number} 헤드 {snapshot.head[:7]} 가 로컬 {head[:7]} 와 "
                    f"{elapsed:.0f}초 동안 다르다. 푸시했는지 본다"
                ]
        sleep(options.interval)


def _gh(*args: str) -> Json:
    try:
        completed = subprocess.run(
            ["gh", *args],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            check=False,
            timeout=GH_TIMEOUT,
        )
    except subprocess.TimeoutExpired as error:
        raise FetchError(f"gh 가 {GH_TIMEOUT:.0f}초 안에 돌아오지 않았다") from error
    except OSError as error:
        raise FetchError(f"gh 를 띄우지 못했다: {error}") from error
    if completed.returncode != 0:
        raise FetchError(completed.stderr.strip() or f"gh 종료 코드 {completed.returncode}")
    try:
        payload: Json = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        raise FetchError(f"gh 출력이 JSON 이 아니다: {error}") from error
    return payload


def fetch_pr(number: str) -> Json:
    """PR 의 세 칸에 그 헤드의 combined status 의 `statuses` 를 붙여 한 번의 조회로 낸다."""
    pr = _gh("pr", "view", number, "--json", "headRefOid,mergeable,statusCheckRollup")
    if not isinstance(pr, dict):
        raise FetchError(f"PR 응답이 객체가 아니다: {pr!r}")
    head = _text(pr.get("headRefOid"))
    combined = _gh("api", f"repos/{{owner}}/{{repo}}/commits/{head}/status")
    statuses = combined.get("statuses") if isinstance(combined, dict) else None
    return {**pr, "statuses": statuses if isinstance(statuses, list) else []}


def local_head() -> str:
    completed = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        encoding="utf-8",
        check=True,
        timeout=GH_TIMEOUT,
    )
    return completed.stdout.strip()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PR 의 검사가 모두 끝날 때까지 기다린다.")
    parser.add_argument("number", help="PR 번호")
    parser.add_argument("--head", help="기다릴 헤드 커밋. 없으면 로컬 HEAD")
    parser.add_argument(
        "--expect", action="append", help="나타나야 끝인 검사 이름. 주면 기본값을 갈음한다"
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="분. 기본 30")
    parser.add_argument("--interval", type=float, default=30.0, help="초. 기본 30")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    number: str = args.number
    head_arg: str | None = args.head
    expect_arg: list[str] | None = args.expect
    timeout_minutes: float = args.timeout
    interval: float = args.interval
    # isdigit 만으로는 '²' 같은 비ASCII 숫자가 지나가 gh 실패 세 번 뒤에야 끝난다.
    if not (number.isascii() and number.isdigit()):
        print(f"끝: PR 번호가 숫자가 아니다: {number}")
        return EXIT_USAGE
    if interval <= 0 or timeout_minutes <= 0:
        print(f"끝: --interval 과 --timeout 은 0보다 커야 한다: {interval}, {timeout_minutes}")
        return EXIT_USAGE
    # PR 헤드는 40자 SHA 라 짧은 SHA 는 끝내 같지 않고 헤드 유예 뒤에 끝난다.
    if head_arg is not None and len(head_arg) != 40:
        print(f"끝: --head 는 40자 SHA 로 준다: {head_arg}")
        return EXIT_USAGE
    if head_arg is None:
        try:
            head_arg = local_head()
        except (OSError, subprocess.SubprocessError) as error:
            print(f"끝: 로컬 HEAD 를 읽지 못했다: {error}. `--head` 로 준다")
            return EXIT_CANNOT_WAIT
    options = Options(
        expected=tuple(expect_arg) if expect_arg else EXPECTED,
        timeout=timeout_minutes * 60,
        interval=interval,
        head_grace=120.0,
        request_grace=90.0,
        max_fetch_errors=3,
    )
    code, lines = wait(number, head_arg, options, fetch_pr, time.sleep, time.monotonic)
    print("\n".join(lines))
    return code


if __name__ == "__main__":
    # 한글을 찍는다. PYTHONUTF8 이 없는 윈도 파이프에서는 cp949 로 나간다(대기열 228).
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main())
