# wait-ci-coderabbit-check-run: `wait_ci`가 CodeRabbit의 체크 런 제목을 상태 설명처럼 읽는다

**What to build:** CodeRabbit은 결과를 커밋 상태(StatusContext)의 설명이 아니라 체크 런(CheckRun)의 `output.title`로 내게 바뀌었다. `tools/wait_ci.py`는 설명을 combined status(`gh api repos/{owner}/{repo}/commits/<헤드>/status`)의 `statuses`에서만 읽는다. 그래서 체크 런 모양이 된 CodeRabbit은 두 자리가 보이지 않는다. 요청 전 건너뜀 판정(`UNREQUESTED_PREFIX`)과 통과 줄의 리뷰 여부다. 건너뜀 체크 런이 롤업의 `SKIPPED`로만 읽혀 통과로 끝나고, 통과 줄에는 CodeRabbit의 설명이 붙지 않아 한도에 걸린 것과 리뷰한 것이 같은 줄이 된다.

손으로 본 모양이다(`gh api repos/{owner}/{repo}/commits/<헤드>/check-runs`와 같은 헤드의 `/status`, 2026-11-08). PR #489의 헤드는 combined status가 비어 있고 CodeRabbit이 체크 런 하나로 `conclusion: skipped`, `output.title: Review skipped: manual review required for this OSS repository`였다. PR #401의 헤드는 `neutral`과 `Review rate limited`, PR #405의 헤드는 `success`와 `Finished`(요약 첫 줄은 `Result: Success - Review completed`)였다. `gh pr view --json statusCheckRollup`의 CheckRun 항목에는 `output`이 없어 롤업만으로는 제목을 읽을 수 없다. 리뷰가 진행 중일 때 체크 런의 제목은 보지 못했다(진행 중 판정은 제목이 아니라 `status`가 `completed`인지로 한다).

고칠 곳은 `tools/wait_ci.py` 하나다. `fetch_pr`가 헤드의 체크 런 목록(`.../commits/<헤드>/check-runs?per_page=100`, REST)도 읽어 `check_runs` 칸으로 붙이고, `parse_snapshot`이 `output.title`이 비지 않은 체크 런을 StatusContext와 같이 다룬다. 제목을 `notes`에 넣어 건너뜀 판정과 통과 줄이 읽게 하고, 상태는 그 체크 런(`status`가 `completed`면 `conclusion`, 아니면 진행 중)에서 읽는다. 롤업은 따로 읽어 시각이 달라, 롤업의 건너뜀과 체크 런의 진행 중이 함께 오면 통과로 읽히기 때문이다. combined status의 길은 그대로 둔다. 독스트링의 CodeRabbit 상태 문단, `tests/tools/test_wait_ci.py`의 시험, `.scratch/harness/probes/wait_ci_mutations.toml`의 변이를 같이 맞춘다. 끝 줄을 읽는 `next-session`의 `merge.md` 2 대기 문장은 끝 줄 모양이 그대로라 바뀌는지만 본다.

범위 밖이다. 파일 수 한도(대기열 374, 만료됨)는 같은 설명을 읽는 자리지만 이 티켓이 가르지 않는다. 체크 런으로 와도 그 제목은 `Review skipped`로 시작해 지금과 같이 요청 전의 건너뜀으로 읽힌다. 체크 런의 그 제목은 보지 못했다.

**대기열:** 499

**Status:** done

## 수용 기준

- [x] 체크 런 모양의 CodeRabbit이 `Review skipped: …` 제목이면 `judge`가 요청 전(`unrequested`)으로 세고, 나머지 검사가 끝난 뒤 요청 유예가 지나면 종료 4와 `@coderabbitai review` 안내로 끝난다. 이전에는 통과 0이었다
- [x] 체크 런 모양의 CodeRabbit이 `Review rate limited`(neutral)나 `Finished`(success)면 통과 줄에 그 제목이 `CodeRabbit: <제목>`으로 붙어 한도와 리뷰를 가른다
- [x] 롤업이 건너뜀을 보는 사이 체크 런이 진행 중이면 끝나지 않은 것으로 읽는다. 건너뜀에서 진행을 거쳐 끝날 때까지 기다린다
- [x] `fetch_pr`가 체크 런 목록을 읽어 `check_runs` 칸으로 붙이고, 그 호출도 시간 제한(`CALL_TIMEOUT`)을 지킨다. 기존 combined status 길의 시험은 그대로 초록이다
- [x] 변이: 체크 런의 제목을 읽지 않는 변이와 체크 런의 상태를 롤업에서만 읽는 변이가 빨강이다(`wait_ci_mutations.toml` 45~48번, 표 전체를 돌려 기대 표지로 빨강)
- [x] 독스트링의 CodeRabbit 상태 문단과 못 보는 것(진행 중 제목을 보지 못했다, 파일 수 한도의 체크 런 모양)이 이 변경과 맞다. `next-session`의 `merge.md` 2 대기 문장은 고치지 않았다. 끝 줄의 모양(`끝:`과 종료 코드)은 그대로이고, 문장이 든 `Review completed`는 상태 모양의 예로 남는다. 그 파일은 카나리아 명세 아홉 개(`next_session_*.toml`)의 원천이라 한 구절을 더해도 `claude -p` 재실행이 따라붙어, 체크 런 모양의 완료 제목 `Finished`는 `wait_ci.py` 독스트링에만 적었다
- [x] 검증 명령이 모두 초록이다(손으로 치는 명령 전부와 `uv run python tools/run_checks.py`. 커밋 직전의 pre-commit이 갈음하는 것은 그 결과로 갈음한다)
