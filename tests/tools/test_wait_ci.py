"""tools/wait_ci.py의 순수 함수와 대기 루프 검증. gh와 git을 부르는 부분은 실제 실행으로 확인한다.

검사 조각은 `gh pr view <N> --json headRefOid,mergeable,statusCheckRollup`의 실제 모양을 따른다
(PR #215·#219, 2026-10-13). 진행 중인 CheckRun도 `completedAt`이 `0001-01-01T00:00:00Z`로 차 있다.
`statuses`는 `fetch_pr`가 헤드의 combined
status(`gh api repos/{owner}/{repo}/commits/<헤드>/status`) 에서 옮겨 붙이는 칸이고, 설명 문구는 PR
#196~#220의 CodeRabbit 상태 이력에 나온 그대로다
(`.scratch/harness/probes/ci_wait/check_timing.py`).
"""

from __future__ import annotations

from collections.abc import Callable

import pytest
from tools.wait_ci import (
    EXIT_CANNOT_WAIT,
    EXIT_FAILED,
    EXIT_PASSED,
    EXIT_TIMED_OUT,
    EXIT_USAGE,
    FetchError,
    Json,
    Options,
    judge,
    main,
    parse_snapshot,
    wait,
)

HEAD = "1c98d6400000000000000000000000000000000a"
OLD_HEAD = "88038b8000000000000000000000000000000000"
NEW_HEAD = "b067ed7000000000000000000000000000000000"
EXPECTED = ("verify", "claude-review", "CodeRabbit")
SKIPPED = "Review skipped: manual review required for this OSS repository"
COMPLETED = "Review completed"
RATE_LIMITED = "Review rate limited"


def run(name: str, status: str = "COMPLETED", conclusion: str = "SUCCESS") -> Json:
    return {
        "__typename": "CheckRun",
        "name": name,
        "status": status,
        "conclusion": conclusion if status == "COMPLETED" else "",
        "startedAt": "2026-10-13T04:41:24Z",
        "completedAt": "2026-10-13T04:44:17Z" if status == "COMPLETED" else "0001-01-01T00:00:00Z",
    }


def context(name: str, state: str) -> Json:
    return {"__typename": "StatusContext", "context": name, "state": state}


def coderabbit(state: str = "SUCCESS", description: str = COMPLETED) -> list[Json]:
    """롤업의 CodeRabbit 칸과 combined status 의 그 설명을 함께 낸다."""
    return [context("CodeRabbit", state), {"context": "CodeRabbit", "description": description}]


def payload(*checks: Json, head: str = HEAD, mergeable: str = "MERGEABLE") -> Json:
    rollup: list[Json] = [c for c in checks if isinstance(c, dict) and "__typename" in c]
    statuses: list[Json] = [c for c in checks if isinstance(c, dict) and "__typename" not in c]
    return {
        "headRefOid": head,
        "mergeable": mergeable,
        "statusCheckRollup": rollup,
        "statuses": statuses,
    }


def green(head: str = HEAD, description: str = COMPLETED) -> Json:
    return payload(
        run("python"),
        run("verify"),
        run("claude-review"),
        *coderabbit(description=description),
        head=head,
    )


def test_기대한_이름이_모두_끝나고_실패가_없으면_통과다() -> None:
    verdict = judge(parse_snapshot(green()), EXPECTED)
    assert verdict.done
    assert verdict.failed == ()


def test_기대한_이름이_빠졌으면_나머지가_끝나도_끝나지_않았다() -> None:
    # 나타난 것만 보면 푸시 직후의 빈 목록이나 아직 붙지 않은 검사 앞에서 끝났다고 한다.
    snapshot = parse_snapshot(payload(run("python"), run("verify"), run("claude-review")))
    verdict = judge(snapshot, EXPECTED)
    assert not verdict.done
    assert verdict.missing == ("CodeRabbit",)


def test_진행_중인_CheckRun은_completedAt이_차_있어도_끝나지_않았다() -> None:
    snapshot = parse_snapshot(payload(run("python", status="IN_PROGRESS")))
    assert snapshot.checks == {"python": None}


def test_StatusContext의_PENDING은_끝나지_않았고_SUCCESS는_끝났다() -> None:
    pending = parse_snapshot(payload(context("CodeRabbit", "PENDING")))
    done = parse_snapshot(payload(context("CodeRabbit", "SUCCESS")))
    assert pending.checks == {"CodeRabbit": None}
    assert done.checks == {"CodeRabbit": "SUCCESS"}


def test_리뷰를_요청하기_전의_건너뜀_상태는_SUCCESS여도_끝나지_않았다() -> None:
    # CodeRabbit 은 푸시마다 리뷰 없이 SUCCESS "Review skipped" 를 먼저 단다(PR #196~#220 모두).
    snapshot = parse_snapshot(
        payload(run("verify"), run("claude-review"), *coderabbit(description=SKIPPED))
    )
    verdict = judge(snapshot, EXPECTED)
    assert not verdict.done
    assert verdict.unrequested == ("CodeRabbit",)
    assert verdict.pending == ()


@pytest.mark.parametrize("conclusion", ["SKIPPED", "NEUTRAL"])
def test_건너뛴_검사와_중립은_통과로_센다(conclusion: str) -> None:
    # 초안 PR의 claude-review는 잡의 if로 건너뛰어 SKIPPED로 남는다.
    snapshot = parse_snapshot(
        payload(run("verify"), run("claude-review", conclusion=conclusion), *coderabbit())
    )
    assert judge(snapshot, EXPECTED).failed == ()


@pytest.mark.parametrize(
    "check",
    [
        run("python", conclusion="FAILURE"),
        run("python", conclusion="CANCELLED"),
        run("python", conclusion="TIMED_OUT"),
        context("python", "ERROR"),
    ],
)
def test_실패와_취소와_시간_초과는_실패로_센다(check: Json) -> None:
    snapshot = parse_snapshot(payload(check, run("verify"), run("claude-review"), *coderabbit()))
    verdict = judge(snapshot, EXPECTED)
    assert verdict.done
    assert verdict.failed == ("python",)


def test_같은_이름이_둘이면_끝나지_않은_쪽과_실패한_쪽을_든다() -> None:
    pending = parse_snapshot(payload(run("python"), run("python", status="QUEUED")))
    failed = parse_snapshot(payload(run("python", conclusion="FAILURE"), run("python")))
    assert pending.checks == {"python": None}
    assert failed.checks == {"python": "FAILURE"}


class Script:
    """조회마다 정해 둔 응답을 차례로 내고(마지막 것은 되풀이한다), 잠든 시간만큼 시계를 민다."""

    def __init__(self, *responses: Json | FetchError) -> None:
        self.responses = list(responses)
        self.now = 0.0
        self.sleeps: list[float] = []
        self.fetched: list[str] = []

    def fetch(self, number: str) -> Json:
        self.fetched.append(number)
        response = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(response, FetchError):
            raise response
        return response

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds

    def clock(self) -> float:
        return self.now


def options(**overrides: float) -> Options:
    return Options(
        expected=EXPECTED,
        timeout=overrides.get("timeout", 600.0),
        interval=overrides.get("interval", 30.0),
        head_grace=overrides.get("head_grace", 120.0),
        max_fetch_errors=3,
    )


def waited(script: Script, opts: Options | None = None) -> tuple[int, str]:
    """기다린 결과를 낸다. 어느 길로 끝나든 마지막 줄이 `끝:` 인지 함께 본다.

    깨어난 세션은 그 줄을 결과와 다음 할 일로 읽는다(next-session 1단계).
    """
    fetch: Callable[[str], Json] = script.fetch
    code, lines = wait("221", HEAD, opts or options(), fetch, script.sleep, script.clock)
    assert lines[-1].startswith("끝:")
    return code, "\n".join(lines)


def test_끝나지_않았으면_간격만큼_자고_다시_본다() -> None:
    script = Script(payload(run("python", status="IN_PROGRESS")), green())
    code, out = waited(script)
    assert code == EXIT_PASSED
    assert script.sleeps == [30.0]
    assert script.fetched == ["221", "221"]
    assert out.endswith(f"끝: 모두 통과. CodeRabbit: {COMPLETED}")


def test_한도에_걸린_리뷰는_통과로_끝나되_끝_줄에_적는다() -> None:
    # PR #196~#220의 마지막 헤드 스물셋 가운데 스물하나가 요청 뒤 몇 초 만에 이 상태였다.
    script = Script(green(description=RATE_LIMITED))
    code, out = waited(script)
    assert code == EXIT_PASSED
    assert out.endswith(f"CodeRabbit: {RATE_LIMITED}")


def test_리뷰가_요청되면_건너뜀에서_진행을_거쳐_끝날_때까지_기다린다() -> None:
    script = Script(
        payload(
            run("verify", status="IN_PROGRESS"),
            run("claude-review"),
            *coderabbit(description=SKIPPED),
        ),
        payload(
            run("verify"),
            run("claude-review"),
            *coderabbit(state="PENDING", description="Review in progress"),
        ),
        green(),
    )
    code, _ = waited(script)
    assert code == EXIT_PASSED
    assert script.sleeps == [30.0, 30.0]


def test_나머지가_끝났는데_리뷰가_요청되지_않았으면_기다릴_수_없다() -> None:
    # PR #208·#214의 마지막 헤드는 요청이 없어 건너뜀 상태에 머물렀다.
    script = Script(green(description=SKIPPED))
    code, out = waited(script)
    assert code == EXIT_CANNOT_WAIT
    assert "@coderabbitai review" in out.splitlines()[-1]
    assert script.sleeps == []


def test_실패가_있으면_1이고_실패한_이름을_찍는다() -> None:
    script = Script(
        payload(
            run("python", conclusion="FAILURE"),
            run("verify", conclusion="FAILURE"),
            run("claude-review"),
            *coderabbit(),
        )
    )
    code, out = waited(script)
    assert code == EXIT_FAILED
    assert "python FAILURE" in out
    assert out.endswith("끝: 실패 python, verify")


def test_PR_헤드가_로컬_HEAD로_바뀌기를_기다린다() -> None:
    # 푸시 직후 PR이 아직 옛 헤드를 가리키면 옛 헤드의 초록을 보고 끝나면 안 된다.
    script = Script(green(head=OLD_HEAD), green())
    code, _ = waited(script)
    assert code == EXIT_PASSED
    assert script.sleeps == [30.0]


def test_헤드가_유예를_넘겨도_다르면_기다릴_수_없다() -> None:
    script = Script(green(head=OLD_HEAD))
    code, out = waited(script, options(head_grace=60.0))
    assert code == EXIT_CANNOT_WAIT
    assert script.sleeps == [30.0, 30.0]
    assert OLD_HEAD[:7] in out
    assert HEAD[:7] in out


def test_기다리던_헤드가_바뀌면_곧바로_끝난다() -> None:
    # 새 푸시가 있으면 앞 대기는 유예를 기다리지 않고 바뀐 헤드를 알리며 끝난다.
    script = Script(payload(run("verify", status="IN_PROGRESS")), green(head=NEW_HEAD))
    code, out = waited(script)
    assert code == EXIT_CANNOT_WAIT
    assert script.sleeps == [30.0]
    assert NEW_HEAD[:7] in out.splitlines()[-1]


def test_시간_제한을_넘기면_남은_이름을_찍는다() -> None:
    script = Script(payload(run("python", status="IN_PROGRESS"), run("verify")))
    code, out = waited(script, options(timeout=90.0))
    assert code == EXIT_TIMED_OUT
    assert script.sleeps == [30.0, 30.0, 30.0]
    last = out.splitlines()[-1]
    assert "python" in last
    assert "claude-review" in last
    assert "CodeRabbit" in last


def test_충돌이면_검사를_기다리지_않는다() -> None:
    # 충돌한 PR에는 pull_request 워크플로가 돌지 않아, 기다리면 시간 제한까지 간다
    # (일지 2026-10-12-34).
    script = Script(payload(mergeable="CONFLICTING"))
    code, out = waited(script)
    assert code == EXIT_FAILED
    assert "충돌" in out.splitlines()[-1]
    assert script.sleeps == []


def test_충돌이면_검사가_다_끝났어도_1이다() -> None:
    script = Script(
        payload(
            run("python"),
            run("verify"),
            run("claude-review"),
            *coderabbit(),
            mergeable="CONFLICTING",
        )
    )
    code, out = waited(script)
    assert code == EXIT_FAILED
    assert "충돌" in out.splitlines()[-1]


def test_gh가_한_번_실패하면_다시_본다() -> None:
    script = Script(FetchError("HTTP 502"), green())
    code, _ = waited(script)
    assert code == EXIT_PASSED


def test_gh_실패는_사이에_성공이_끼면_처음부터_센다() -> None:
    pending = payload(run("verify", status="IN_PROGRESS"))
    script = Script(
        FetchError("HTTP 502"),
        FetchError("HTTP 502"),
        pending,
        FetchError("HTTP 502"),
        FetchError("HTTP 502"),
        green(),
    )
    code, _ = waited(script)
    assert code == EXIT_PASSED
    assert len(script.fetched) == 6


def test_gh가_연달아_실패하면_기다릴_수_없다() -> None:
    script = Script(FetchError("HTTP 502"))
    code, out = waited(script)
    assert code == EXIT_CANNOT_WAIT
    assert "HTTP 502" in out
    assert len(script.fetched) == 3


def test_PR_번호가_숫자가_아니면_끝_줄을_찍고_2로_끝난다(
    capsys: pytest.CaptureFixture[str],
) -> None:
    code = main(["abc"])
    assert code == EXIT_USAGE
    assert capsys.readouterr().out.splitlines()[-1].startswith("끝:")
