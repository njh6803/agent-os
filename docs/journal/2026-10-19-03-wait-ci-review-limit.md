# 2026-10-19 (03) 계정 한도로 빨간 claude-review를 wait_ci가 실패로 세지 않게

브랜치 `chore/wait-ci-review-limit`. 대기열 327을 chore 한 PR로 반영했다.

> 사용자: 대기열 327(claude-review가 계정 주간 한도로 빨간 동안 tools/wait_ci.py가 그 빨강을 실패로 세는 열린 행)을 chore
> 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다

시작 전에 주 체크아웃 세션으로 `tidy-checkouts`를 돌았다. 루트를 88fed982에서 655b19a8(origin/main)로 빨리감기했다. 병합된
워크트리 둘(`09-human-verification-checks`, `retro-reject-criteria`)과 그 브랜치를 지웠다. 같은 때 다른 세션도 정리를 돌고
있어, 나머지 후보(`handoff-notice-and-runbook-quotes`, `hook-list-check-and-timing-guards`, `scratch-probe-rule-hook`,
`chore/filesystem-read-retry-under-load`)는 이 세션이 치기 전에 사라졌거나 판정이 바뀌어 `남겼다`로 끝났다. 남은 브랜치 후보
셋(`chore/grill-with-docs-model-invoked`, `docs/token-usage-09-handoff-cost`, `worktree-mutate-ctrl-c-under-load`)은 치지 않고
다음 정리에 넘겼다. 넘긴 것은 분리 HEAD 셋(`confident-wright-2d3ebf`, `elegant-dijkstra-aaddb9`,
`vigorous-mahavira-ebe993`, 그 커밋이 origin/main에 없다)과 `skill-check-and-retro-section`(병합된 PR의 머리와 브랜치 끝이
다르다)이고, `ruff-try-statements`는 그 폴더를 작업 디렉터리로 쥔 `tail.exe`(pid 27716) 때문에 남았다.

## 한 일

- `tools/wait_ci.py`. claude-review가 빨가면 롤업 CheckRun의 `detailsUrl`에서 잡 번호를 꺼내 `gh run view --job <잡> --log`를
  한 번 읽는다. 결과 블록이 `"is_error": true`이고 `result`가 `LIMIT_PREFIX`("You've hit your weekly limit")로 시작하면 그
  이름을 `judge`의 `excused`로 넘겨 실패로 세지 않는다. 그러면 기존 갈래대로 CodeRabbit의 요청 유예와 진행을 마저 기다리고,
  통과 줄 끝에 `claude-review: 계정 한도로 리뷰 없음(<문구>)`을 붙인다. 잡 번호마다 한 번만 읽고(끝난 잡의 로그는 바뀌지
  않는다), 읽지 못했거나 잡 주소가 없으면 가르지 못한 것이라 실패로 세며 그 이유를 끝 줄 앞에 적는다. 한도로 잘못 읽어
  통과시키는 쪽이 리뷰 없는 병합으로 이어지므로 모를 때는 실패 쪽이다.
- 로그 읽기는 `gh_run_summary.py`를 부르지 않고 같은 모양(접두를 뗀 `{`에서 `}`까지)을 이 도구 안에 다시 짰다. 이 도구는
  `uv run python tools/wait_ci.py`로 스크립트로 돌고 `tools`가 설치 패키지가 아니라 그 모듈을 import하지 못한다. 그 요약은
  `result` 칸을 내지 않고, Claude의 말은 `show_full_output`이 켜졌을 때만 실린다.
- REST(`gh api repos/{owner}/{repo}/actions/jobs/<잡>/logs`)도 봤다. 이 PC의 gh는 로그에 터미널 이스케이프가 있다며
  `--allow-escape-sequences` 없이는 내지 않아(종료 1), `gh_run_summary.py`와 같은 `gh run view`를 썼다. 클라우드에서
  `gh run view`를 돌려 본 기록은 없어 독스트링의 못 보는 것에 적었다.
- 시험 아홉(`tests/tools/test_wait_ci.py`): 한도 블록, 한도가 아닌 빨강 여섯 갈래(오류 아닌 블록, 다른 API 오류, 지어낸
  다른 한도 문구, 문자열 아닌 결과, 결과 블록 없음, 블록 밖의 문구), 잡 번호 읽기, 한도면 CodeRabbit을 마저 기다림, 진짜
  빨강은 곧바로 실패, 가르지 못하면 실패, 한도여도 다른 실패는 실패, 다른 검사의 빨강은 가르지 않음, 잡 로그 호출의 시간
  제한. 결과 블록의 줄은 실행 39047880157의 잡 117440173217 로그에서 판정에 쓰는 키만 남겼다.
- 변이 여덟(`.scratch/harness/probes/wait_ci_mutations.toml`, 30~37)과 그 README 줄.
- 독스트링의 판정 항목과 못 보는 것(리뷰 코멘트의 내용만 남기고, 주간 한도 밖의 문구, 결과 블록 밖의 문구, 클라우드의
  `gh run view`를 더했다). `next-session` 1의 2 대기 문장에 한도 끝 줄을 더했다. 대기열 327을 닫았다(4회차로 PR #292를 더했다).

## 검사

- 실제 실행: `job_limit('117440173217')`(PR #292의 한도 잡)이 "You've hit your weekly limit · resets Oct 18, 9pm (UTC)"를,
  `job_limit('116898067422')`(실행 38878140947, 리뷰를 마친 초록)이 None을 냈다. `uv run python tools/wait_ci.py 292 --head
  bf30dba8… --timeout 3`이 `끝: 모두 통과. CodeRabbit: Review rate limited. claude-review: 계정 한도로 리뷰 없음(You've hit
  your weekly limit · resets Oct 18, 9pm (UTC))`로 끝났다.
- `tests/tools/test_wait_ci.py` 50건 초록. 변이는 `--since origin/main`으로 여덟을 돌려 모두 기대대로 빨갰다.

- 카나리아 `next_session_ci_wait_review_limit.toml`(새 명세): 통과 4(claude 2.1.302). 실험군 셋은 더한 글
  `claude-review: 계정 한도로 리뷰 없음(<한도 문구>)`을 옮겼고, 대조군(주 체크아웃 655b19a8)은 "없음"을 답했다.

## 셀프 리뷰

이어받은 세션이 돌았다. 앞 세션의 프로세스(pid 26524)가 턴을 마친 뒤에도 워크트리 잠금을 쥐어 `EnterWorktree`가 거부했고,
주 체크아웃 세션에서 `git -C`·`uv run --directory`와 절대 경로로 이 워크트리를 다뤘다. 범위: base 655b19a8(origin/main), 파일
여섯, 커밋 0, 미추적 둘. 명세는 대기열 327 행의 "어디로" 칸. 두 축 모두 Critical 없음.

- 표준 축(Major 1, Minor 7, Nit 4). Major: 옛 변이 "끝 줄의 접두를 뺀다"의 `old`가 바뀐 통과 줄과 맞지 않아
  `tools/mutate.py --check`가 종료 2였다(`--since origin/main`은 그 변이를 고르지 않았다). Minor: 독스트링이 실행
  38878140947을 PR #292로 적었다(PR #278이다), 로그 읽기가 한 번 실패하면 곧바로 실패로 끝난다, `job is None` 갈래의 시험이
  없다, 같은 이름의 CheckRun이 둘이면 잡 번호는 나중 것·결과는 나쁜 쪽이라 진짜 실패가 면제될 수 있다, `_limits`가 인자 캐시를
  바꾼다(CQS), 다른 검사의 빨강 시험이 까닭을 단언하지 않는다, `LOG_PREFIX`가 `gh_run_summary.PREFIX`와 같다는 주장의 시험이
  없다. Nit: 독스트링의 "끝 줄"은 통과 줄만이다, "본 문구는 주간 한도의 것뿐"이 모호하다, README가 변이 방향을 반대로 적었다,
  `limits`·`unclear` dict 한 쌍.
- 명세 축(Minor 4, Nit 2). 명세가 든 `terminal_reason`을 보지 않는다, 같은 이름의 잡 둘(표준 축과 같다), gh 실패 한 번(표준
  축과 같다), `next-session`이 "가르지 못했다" 줄의 할 일을 말하지 않는다. Nit: 시각 없는 주간 한도 문구도 통과한다, 한도가
  실패·시간 초과 끝 줄에는 실리지 않는다.

고친 것:
- 변이 표의 옛 변이 `old`를 `{notes}{reviewless}`로 맞췄고, 대기열 327 몫을 바뀐 코드에 맞춰 열넷으로 다시 썼다.
- `limit_message`가 `"terminal_reason": "api_error"`도 본다(본 한도 실행은 모두 그 값이었다, 일지 2026-10-16-69 외 여럿).
- `_limits`와 인자 캐시를 `ReviewLimits`(잡별 판정과 실패 횟수를 든다)와 `Review`로 바꿨다. 로그 읽기가 실패하면
  `max_fetch_errors`번째까지 다음 조회에서 다시 읽고 그동안 끝내지 않는다.
- `Snapshot.jobs`를 `failed_jobs`(이름에서 빨간 실행마다의 잡 번호)로 바꿔, 같은 이름의 빨간 잡이 모두 한도일 때만 뺀다.
- 시험 다섯을 더했다(`LOG_PREFIX` 일치, 한 번 실패 뒤 다시 읽기, 잡 주소 없음, 같은 이름의 잡 둘의 두 순서, 둘 다 한도). 다른
  검사의 빨강 시험이 끝 줄을 단언한다. 가르지 못하는 시험은 세 번 읽고 두 번 잔 것을 단언한다.
- 독스트링의 판정 항목과 실행 귀속, `next-session` 1의 2 대기 문장에 가르지 못했을 때의 할 일, 프로브 README 줄, 대기열 327의
  닫힘 문구를 맞췄다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장):
- `tools/wait_ci.py` 독스트링: "같은 이름의 빨간 잡이 여럿이면 모두 한도일 때만 빼고, 하나라도 한도가 아니면 실패로 센다", "로그
  읽기가 실패하면 PR 조회처럼 `max_fetch_errors`번까지 다음 조회에서 다시 읽고", "PR #278의 실행 38878140947(리뷰를 마친
  초록)", "실행 로그에서 본 한도 문구는 `LIMIT_PREFIX` 주석의 실행 셋에 나온 주간 한도의 것뿐이다".
- `ReviewLimits` 독스트링: "읽기가 실패하면 `max_errors`번째까지는 다시 읽으라고 내고, 그 뒤에는 가르지 못한 것으로 낸다".
- `wait` 주석: "다시 읽기는 max_fetch_errors 번으로 끝난다".
- `next-session` SKILL.md: "잡 로그를 읽지 못하면 그 도구는 한도인지 모르는 빨강을 실패로 세고 끝 줄 앞에 `claude-review 이
  한도인지 가르지 못했다`를 적는다".

남긴 것:
- 시각 없는 주간 한도 문구도 통과한다(Nit). 본 문구는 모두 시각이 있었고, 시각이 없어도 한도라는 판정은 맞다.
- 실패·시간 초과 끝 줄에 한도가 실리지 않는다(Nit). 명세의 "끝 줄"은 통과 길이고, 실패 길은 앞 줄에 남는다고 독스트링에 적었다.
- `limit_message`와 `gh_run_summary._blocks`의 중복(Minor, Duplicated Code). import하지 못하는 까닭이 맞고, 접두가 같다는
  주장은 시험으로 고정했다.
- `Snapshot.failed_jobs`가 모든 이름을 담는다(Nit, Speculative Generality). 롤업을 읽는 자리는 이름을 가리지 않는 것이 다른
  칸과 같다.

## 회고

후보 다섯. 승인 둘, 기각 셋, 넘김 없음.

- 승인(회차): 잡 로그를 REST로 받으려다 gh가 이스케이프 문자 때문에 거부했다. 열린 280이 처방한 사건이라 280에 회차를
  더했다(2회차).
- 승인(고침): `tools/gh_run_summary.py`가 결과 블록의 `result`를 내지 않아, 한도 문구를 원본 로그에서 grep해야 했다. 도구의
  빠진 칸이라 사건 하나로 승인하고, 이 PR의 범위 밖이라 대기열 343(1회차)에 뒀다.
- 기각: 다른 세션과 `tidy-checkouts`가 겹쳐 `remove`가 `등록된 워크트리가 아니다`로 끝났다. 도구가 지우기 전에 다시
  판정해 막았다.
- 기각: 85줄 heredoc을 PreToolUse 훅이(상한 40줄), 변수를 든 `sed`를 워크트리 가드가 막았다. 이미 있는 훅·가드가 그 자리에서
  막았다.
- 기각: 일지 번호 01이 형제(`full-checks-via-runner`)와 겹쳤다. 일지 계기 훅이 알리고 `sibling_overlap.py --move`가 옮겼다.

## 인계

셀프 리뷰 직전에 인계 계기가 왔다(세션 컨텍스트 268,843 토큰). `/code-review`는 부른 채 단계를 밟지 않았고, 새 세션이
셀프 리뷰부터 한다. 이 세션의 제목은 `chore/wait-ci-review-limit`이었고 `chore/wait-ci-review-limit (인계함)`으로 바꾼다.
변경은 모두 커밋하지 않은 채 워크트리에 있다. 이 세션이 띄운 전체 `uv run pytest -q`(백그라운드)는 끝을 보지 못하고 멈춘다.
`ruff check`·`pyright`·`lint-imports`는 초록이었고, `ruff format --check`는 시험 파일 하나를 고친 뒤 다시 치지 않았다.
`## 다음`은 단계를 닫는 새 세션이 쓴다. 회고는 이 세션이 위에서 돌았다.

지시문:

```
다음 작업: 기능 harness. 대기열 327(claude-review가 계정 주간 한도로 빨간 동안 tools/wait_ci.py가 그 빨강을 실패로 세는 것)을 반영한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 327(claude-review가 계정 주간 한도로 빨간 동안 tools/wait_ci.py가 그 빨강을 실패로 세는 열린 행)을 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다
브랜치: chore/wait-ci-review-limit
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-19-03-wait-ci-review-limit.md(한 일, 검사, 회고, 인계, 이어받은 일)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 origin/main, 명세는 .scratch/retro-queue.md 327 행의 "어디로" 칸)부터 한다. 리뷰 뒤 검증 명령을 다시 돌린다(전체 pytest는 이 세션에서 끝을 보지 못했다). 일지는 docs/journal/2026-10-19-03-wait-ci-review-limit.md이고 "## 다음"은 아직 없다. 그 일지의 "이어받은 일"(PR #292 카나리아 셋의 실제 회차)은 이 PR 밖의 일이라 "다음"으로 옮긴다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-18T22:06:11Z

## 이어받은 일

- PR #292 일지에 "다음" 절이 없어 여기에 옮긴다: 계정 한도가 풀린 뒤(2026-10-19 06시 KST) PR #292의 카나리아
  셋(`.scratch/harness/probes/canary/probes_rule_kill_and_snapshot.toml`, `spec_reviewer_evidence_kinds.toml`,
  `tools_rule_scratch_probe_hook.toml`)의 실제 회차를 돌려 각 명세 머리 주석에 결과를 적는다.
