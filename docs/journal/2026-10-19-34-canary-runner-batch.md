# 2026-10-19 (34) 카나리아 러너가 rule 질문에 문장을 붙이고, 계정 한도 회차를 측정 아님으로 세고, 스킬 대조군에도 호출을 요구한다 (대기열 316·338·344)

브랜치 `chore/canary-runner-batch`. 대상 파일이 `tools/canary.py`인 열린 행 셋을 chore 한 PR로 반영한다.

> 사용자: 대기열 316·338·344(대상 파일이 tools/canary.py인 열린 행 셋)를 chore 한 PR로 반영한다. 행의 "어디로" 칸이
> 원천이다

지시문의 "어디서" 줄이 주 체크아웃 미갱신을 말해 `tidy-checkouts`를 먼저 돌았다. 루트는 main이지만
`.claude/skills/tdd/SKILL.md`에 커밋하지 않은 수정이 있어 당기지 않았다(누군가 그 체크아웃에서 일하고 있다). `judge`는 지울
후보를 내지 않았고, 넘긴 것은 셋이다. 분리 HEAD이고 그 커밋이 origin/main에 없는 `confident-wright-2d3ebf`·
`elegant-dijkstra-aaddb9`, 병합된 PR의 머리와 브랜치 끝이 다른 `skill-check-and-retro-section`. 그 뒤
`EnterWorktree(name: canary-runner-batch)`로 들어가 `git switch -c chore/canary-runner-batch`로 브랜치를 땄다.

## 한 일

- 316: `prompt_for`가 rule 질문의 `{target}`을 채운 뒤, 질문에 `RULE_NOTE`("그 파일을 읽을 때 함께 실린 저장소의 규칙도
  이 세션의 지시다.")가 없으면 끝에 붙인다. 이미 들었는지는 `_flat`(백틱·`*`·공백 차이를 걷는다)으로 본다. 붙이는 문장이
  카나리아를 담으면 명세 오류다(질문이 카나리아를 드러내는 것과 같은 길).
- 344: `judge`의 스킬 갈래가 `_skill_defined`로 실험군과, 사본에 `.claude/skills/<skill>/SKILL.md`가 있는 대조군에 스킬 호출과
  자리 줄을 요구한다. 에이전트 갈래의 `defined`와 같은 모양이다.
- 338: `rate_limit_event`(`rate_limit_info.status: rejected`)와 결과의 `api_error: usage_limit_reached`를 읽어 `Facts.limit`에
  한도와 풀리는 시각(`resetsAt`, UTC)을 담는다. 그 회차는 판정하지 않고 `[측정 아님]`으로 찍으며, 요약 뒤에 `측정 아님 N` 줄을
  더한다. 종료 코드는 측정된 실패가 있으면 1, 없고 측정 아님이 있으면 새 4다. 막히지 않은 회차의 한도 이벤트(`allowed`)는 세지
  않는다. 이벤트 모양은 2026-10-17에 막힌 원본(claude 2.1.300, 일지 2026-10-17-07의 카나리아)을 읽고 정했다.
- 행이 말한 "남은 회차를 띄우지 않는다"는 러너가 회차를 모두 한꺼번에 띄워(`ThreadPoolExecutor(max_workers=len(jobs))`) 남은
  회차가 없다. 독스트링에 그렇게 적었다.
- 모듈 독스트링(질문 칸, 스킬 판정, 계정 한도 문단, 종료 코드 4)과 `docs/constitution/operations.md` 카나리아 항목의 "러너는 그
  이벤트를 읽지 않아 그 회차를 실패로 낸다"를 고쳤다. 옛 문장의 잔존은 살아 있는 문서에 없다(일지·대기열 행은 기록).
- 시험 16건(316 여섯, 344 넷, 338 여섯. 셀프 리뷰가 바로잡은 수다)과 변이 열(`.scratch/harness/probes/canary_mutations.toml` 145~154).
  셀프 리뷰 반영 뒤의 수는 아래 셀프 리뷰 절이다.

## 검사

- TDD: 시험을 먼저 써 빨강을 봤다(없는 `RULE_NOTE` import로 수집 실패). 고친 뒤 `tests/tools/test_canary.py` 244 초록(122초).
  `ruff check`·`ruff format`(바꾼 파이썬 둘)은 초록.
- 변이: `--since origin/main` 열(145~154) 모두 기대대로 빨강(기준선 244 초록, 183초). 149는 새 시험이 아니라 기존
  `test_init의_도구와_서버_Read와_Skill_호출_스킬_위치_답을_뽑는다`(info 없는 한도 이벤트)가 잡았다.
- 카나리아(316 행의 "다시 돌려 대조군이 여전히 없음인지"): 문장이 없던 rule 명세
  `.scratch/end-user-continuation/probes/canary/sdk_rule_failure_cause.toml`을 새 러너로 돌려 통과 4(커밋 `519b3820`,
  이 PC). 실험군 셋이 `.claude/rules/sdk.md`의 값을 옮기며 "함께 실린 규칙 파일"이라 밝혔고, 대조군은 "없음"이었다. 그 명세의
  `# 최신 결과:` 줄은 고치지 않았다.
- `sibling_overlap`: 번호 겹침 없음. `docs/constitution/operations.md`를 고쳐 헌법 판을 3.0.46으로 올렸다(형제
  `worktree-overrides-pc-check`가 3.0.45를 먼저 매겼다). 같은 파일을 형제 둘(`token-report-git-timeout`,
  `worktree-overrides-pc-check`)도 고쳐 나중에 병합하는 쪽의 글자 충돌 후보다.
- 대기열 316·338·344를 닫았고 프로브 README의 `canary_mutations.toml` 행(백쉰넷)을 고쳤다.
- 전체 검증(`tools/run_checks.py`)과 pyright·lint-imports는 아직 돌리지 않았다.

## 셀프 리뷰에 밀 주장

- 모듈 독스트링: "회차는 모두 한꺼번에 띄우므로 막힌 회차를 본 뒤에 띄우지 않을 남은 회차는 없다", 한도 표지 문장(거절만
  센다, 막히지 않은 회차에도 찍힌다), 종료 코드 4의 우선순위.
- `_LIMIT_REJECTED` 주석의 "claude 2.1.300 의 원본을 읽었다, 일지 2026-10-17-07"(원본은 세션
  `30dcc9ef…`의 스크래치패드 `canary-retro/워크트리-1.jsonl`, 커밋하지 않았다).
- `operations.md` 카나리아 항목의 새 문장과 헌법 README 3.0.46 문구.
- 316 행의 "그 문장이 카나리아를 담으면 명세 오류"는 행에 없던 것을 더했다(범위 넘침인지 명세 축이 판정).

## 인계

`/code-review`를 부른 직후 인계 계기가 왔다(`셀프 리뷰 직전`, 세션 컨텍스트 308,544 토큰). 곁 세션이 아니다(`get_session`의
`self`에 `parentSessionId`가 없다). 리뷰 단계는 밟지 않았고 새 세션이 셀프 리뷰부터 한다. 변경은 모두 커밋하지 않은 채
워크트리에 있다. `tidy-checkouts`가 넘긴 셋(앞 문단)은 사람에게 보고만 한다. 이 세션의 제목은 `chore/canary-runner-batch`였고
`chore/canary-runner-batch (인계함)`으로 바꾼다.

지시문:

```
다음 작업: 기능 harness. 대기열 316·338·344(대상 파일이 tools/canary.py인 열린 행 셋: rule 질문에 저장소 규칙도 지시라는 문장 붙이기, 계정 한도에 막힌 회차를 측정 아님으로 세기, 스킬 명세의 대조군에도 스킬 호출과 자리 줄 요구하기)를 반영한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 316·338·344(대상 파일이 tools/canary.py인 열린 행 셋)를 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다
브랜치: chore/canary-runner-batch
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-19-34-canary-runner-batch.md(한 일, 검사, 셀프 리뷰에 밀 주장, 인계)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 origin/main, 명세는 .scratch/retro-queue.md 316·338·344 행의 "어디로" 칸을 origin/main 판에서 읽는다. 이 브랜치는 그 행들을 이미 닫았다)부터 한다. 밀 주장은 일지 "셀프 리뷰에 밀 주장" 절이다. 시험·변이·카나리아는 돌았고 전체 검증(tools/run_checks.py)과 린트 둘은 리뷰 반영 뒤에 돈다. 일지는 docs/journal/2026-10-19-34-canary-runner-batch.md이고 "## 다음"은 아직 없다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `chore/canary-runner-batch (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었으며(카나리아와 변이는 끝났다),
`git worktree unlock`은 오류 없이 끝났다.

open-session을 부른다 2026-10-19T09:25:52Z

## 셀프 리뷰

새 세션이 `EnterWorktree(path)`로 이 워크트리에 들어와 `/code-review`를 돌렸다. 범위: base `519b3820`(=HEAD), 바뀐 파일
7, 커밋 0, 미추적 1(이 일지). 명세는 origin/main 판 대기열 316·338·344 행의 "어디로" 칸이다. 두 축 모두 Critical·Major는
없었다.

표준 축(sonnet·high)의 지적:

1. Minor 잔존: 출력 문단이 판정 줄을 "`[통과]`·`[통과·"없음" 섞임]`·`[실패]` 가운데 하나"로 닫아 `[측정 아님]`이 빠졌다.
   skill 칸의 "실험군 회차마다 이 스킬을 Skill 로 불러야 한다"는 344 뒤 대조군에도 해당한다.
2. Minor 근거 표기: `_LIMIT_REJECTED` 주석과 시험 주석이 "일지 2026-10-17-07"을 들지만 그 일지에는 `status: rejected`·
   2.1.300·`api_error`가 없고 원본은 커밋하지 않은 스크래치다. "막히지 않은 회차에도 찍힌다"(`allowed`)는 저장소에 근거가
   없다.
3. Minor 경계 입력: `resetsAt`이 밀리초면 `OSError`, `1e30`이면 `OverflowError`가 `ValidationError` 길 밖으로 나가, `_verdict`가
   `_record`보다 먼저 도는 탓에 이미 돈 회차의 원본을 모두 잃는다. 거절 이벤트 뒤 성공 결과가 와도 답을 버린다.
4. Minor smell: `_Verdict.unmeasured`가 `facts.limit`을 되풀이한다, 회차 상태를 여러 자리가 불리언·선택값으로 가른다,
   `Facts.limit`이 한국어 문장이다, `_skill_defined`가 `spec.source` 대신 경로를 하드코딩했다, `_limit`/`limit` 이름 겹침.
5. Minor 시험: 붙이는 문장의 카나리아 시험의 `match="카나리아"`가 기존 오류 문구에도 맞는다. `_flat`의 `*` 걷기에 시험이 없다.
   새 변이 열에 `expect_output`이 없다.
6. Nit: 338 시험은 여섯이고 합은 16이다(대기열 닫힘의 "다섯"과 일지의 "15건"이 틀렸다).

명세 축의 지적:

1. Minor: `operations.md` 카나리아 항목이 표지를 `rateLimitType: seven_day`로 적은 뒤 러너 문장을 잇는데, 러너는 종류를
   가리지 않고 `status: rejected`를 센다(다섯 시간 한도도 측정 아님).
2. Minor: 이제 `rate_limit_event`의 모양을 검사해, 막히지 않은 회차에도 찍히는 이 이벤트의 모양이 바뀌면 정상 회차가
   어긋난 줄로 실패한다. `resetsAt` 밀리초의 `OSError`(표준 축 3과 같다).
3. Minor 근거 표기(표준 축 2와 같다).
4. 참고: 거절 이벤트 뒤 답을 낸 회차의 측정이 버려진다(표준 축 3과 같다).

고친 것:

- 잔존 둘(판정 줄 목록에 `[측정 아님]`, skill 칸에 대조군).
- 근거 표기: `_LIMIT_REJECTED` 주석과 시험 주석이 원본을 커밋하지 않은 스크래치를 손으로 읽었다고 밝히고 이 일지를
  든다. 새로 쓴 사실 문장 "같은 PC 의 다른 세션이 막히지 않고 돈 카나리아 원본에도 한도 이벤트가 `status: allowed`·
  `allowed_warning`(주간 한도 99% 경고)으로 찍혀"는 이 세션이 스크래치 원본을 Grep으로 다시 열어 봤다(세션
  `007afcf1…`의 `allowed_warning`·`seven_day`·`utilization 0.99`, `05d0c236…`의 `allowed`·`five_hour`, `30dcc9ef…`의
  `rejected`). "종류(`rateLimitType`)는 가리지 않는다. 주간 한도든 다섯 시간 한도든 거절이면 그 회차는 측정이 아니다"도
  새로 썼다(다섯 시간 한도의 거절 원본은 보지 못했다. 코드가 종류를 보지 않는다는 서술이다).
- `resetsAt`을 시각으로 읽지 못하면(`OverflowError`·`OSError`·`ValueError`) "풀리는 시각을 읽지 못했다(resetsAt …)"로 적는다.
- 한도 이벤트의 모양이 어긋나면 어긋난 줄로 세지 않고 건너뛴다(`suppress(ValidationError)`).
- `_verdict`는 한도 표지가 있고 답이 없을 때만 측정 아님으로 센다. 거절 뒤에도 답을 냈으면 판정한다. 독스트링에 "결과가
  성공한 답이 아닌 회차다. 거절 뒤에도 답을 냈으면 측정이라 판정한다"를 새로 썼다.
- `operations.md` 카나리아 항목에 "러너는 한도의 종류를 가리지 않고 거절(`rejected`)이나 `usage_limit_reached`가 찍혔는데
  답을 내지 못한 회차를"을 새로 썼다.
- 시험: 붙이는 문장의 카나리아 시험의 `match`를 그 오류 문구로 좁혔고, `**` 강조 꼴, 모양이 바뀐 한도 이벤트, 읽지 못하는
  풀리는 시각(밀리초·`1e30`), 거절 뒤 답한 회차를 더했다.
- 변이 열을 열셋(145~157)으로 다시 썼다. 코드가 바뀌어 원문이 맞지 않던 둘을 고치고, 새 가드 셋을 더하고, 모두에
  `expect_output`(빨개져야 할 시험 이름)을 붙였다.
- 수: 대기열 316 닫힘의 시험 일곱, 338 닫힘의 시험 열·변이 아홉(149~157), 프로브 README 행.

남긴 것:

- `_skill_defined`의 경로를 `spec.source`로 바꾸지 않는다. `source`는 "바뀐 파일"이라 스킬의 참고 파일일 수도 있고,
  스킬이 사본에 있는지는 `SKILL.md`로 보는 것이 맞다.
- `_Verdict.unmeasured`는 이제 `facts.limit`과 같지 않다(답이 있으면 비운다). 상태를 열거로 모으는 것(Repeated Switches,
  CODING_STANDARDS의 불리언 칸 항목)과 `Facts.limit`의 문장 꼴은 이 PR 범위 밖의 다듬기라 두고, 같은 지적이 다시 나오면
  retro 후보로 올린다. `_limit`/`limit` 이름 겹침은 `_read_limit`으로 바꿔 풀었다.
- `_flat`이 문장 일부만 든 질문에 문장을 다시 붙이는 것은 의도한 동작이다(일부만 들면 그 지시가 온전히 실리지 않는다).

명세 축은 `status: rejected` 판정이 행 글자(`seven_day`)보다 옳다고 봤다(`seven_day`의 `allowed_warning`을 글자대로 잡으면
거짓 양성). 316의 카나리아 검사 추가도 범위 넘침이 아니라고 봤다.

다시 돌린 것(셀프 리뷰 반영 뒤):

- `tests/tools/test_canary.py` 249 초록. 수집으로 센 시험은 316 일곱, 338 열, 344 넷이다.
- 변이 `--since origin/main` 열셋(145~157) 모두 빨강, 열둘은 표지까지 맞았다. 149는 첫 실패에서 멈추어 앞의 init 시험
  (`status` 없는 한도 이벤트)이 먼저 빨개져 시험 이름 표지가 맞지 않았다. 표지를 그 단언의 값
  (`limit: '계정 한도(종류 모름, 풀리는 시각 모름)' != None`)으로 바꾼 뒤 149만 다시 돌려 기대대로.
- `uv run python tools/run_checks.py` 모두 Passed(pytest 445초, web-verify 503초, pyright·lint-imports·check-type-escapes·
  run-hooks·zizmor·check-instructions). `ruff check`·`ruff format --check` 초록.
- `sibling_overlap`: 번호 겹침 없음. origin/main이 `2efb5ea`로 움직였고(#305·#306), 이 브랜치와 함께 고친 파일은
  `.scratch/retro-queue.md` 하나다. 새로 따를 규약은 없다(Glob·Grep의 `.gitignore` 함정, `sibling_overlap` 견딤).
- 첫 커밋 시도를 pre-commit의 변이 표 검사(`mutate.py --staged`)가 막았다. 이 브랜치가 고친 자리를 원문으로 든 옛 변이 셋
  (10 "스킬 호출을 대조군에도 요구한다", 11 "skill 을 주지 않은 명세에도 스킬 호출을 요구한다", 82 "섞인 통과를 판정 줄에
  표시하지 않는다")의 원문이 0번이었다. `--since origin/main`은 표에서 바뀐 열만 골라 이 셋을 돌리지 않았다. 원문을 지금
  코드에 맞추고 10은 이름을 "옛 사본에 스킬이 없는 대조군에도 스킬 호출을 요구한다"로 바꿨다(344 뒤에는 사본에 스킬이 있는
  대조군에 요구하는 것이 옳은 동작이다). 셋을 돌려 모두 기대대로, 각각 이름 그대로의 시험이 빨개졌다.
- 둘째 시도는 무관한 시간 단언(`tests/tools/test_hook_midturn_korean.py::test_트랜스크립트_파일이_없으면_기다리지_않는다`,
  2초 상한에 2.8초)으로 막혔다. 직전 `run_checks.py`에서는 초록이었고 셋째 시도에서 지나 커밋 `8c2af6ce`가 들어갔다.
  한 번이라 retro 후보로 올리지 않는다(같은 꼴은 대기열 332·306).

## 인계 (커밋 뒤)

커밋 `8c2af6ce` 직후 인계 계기가 왔다(`커밋 뒤`, 세션 컨텍스트 266,489 토큰). 이 세션의 지시문의 "이어받을 상태"는
`인계: 셀프 리뷰 직전`이라 같은 경계가 아니고, 요청 범위는 PR과 병합까지이며, `인계 못함` 줄이 없고, 딥링크로 연 세션이다.
이 세션의 제목은 `chore/canary-runner-batch`였고 `chore/canary-runner-batch (인계함)`으로 바꾼다.

남은 단계: origin/main 합치기(`sync_with_base_branch`. origin/main이 `2efb5ea`로 움직였고 함께 고친 파일은
`.scratch/retro-queue.md` 하나다) → PR 직전 리뷰(`docs/constitution/operations.md` 리뷰 파이프라인 2. CLI가 돌지 못하면
`/security-review`와 `bug-perf-review`) → PR → 봇 회차 → 병합 → 일지 "## 다음"과 retro.

PR 직전 `bug-perf-review`에 밀 주장(셀프 리뷰 반영으로 새로 쓴 사실 문장, 원문):

- `_LIMIT_REJECTED` 주석: "같은 PC 의 다른 세션이 막히지 않고 돈 카나리아 원본에도 한도 이벤트가 `status: allowed`·
  `allowed_warning`(주간 한도 99% 경고)으로 찍혀 거절만 센다", "종류(`rateLimitType`)는 가리지 않는다. 주간 한도든 다섯 시간
  한도든 거절이면 그 회차는 측정이 아니다".
- 모듈 독스트링: "결과가 성공한 답이 아닌 회차다. 거절 뒤에도 답을 냈으면 측정이라 판정한다".
- `Reading.add` 주석: "읽지 못한 거절은 결과의 `api_error` 로도 잡지 못하면 실패로 나온다".
- `operations.md` 카나리아 항목: "러너는 한도의 종류를 가리지 않고 거절(`rejected`)이나 `usage_limit_reached`가 찍혔는데 답을
  내지 못한 회차를 판정하지 않고".

지시문:

```
다음 작업: 기능 harness. 대기열 316·338·344(대상 파일이 tools/canary.py인 열린 행 셋: rule 질문에 저장소 규칙도 지시라는 문장 붙이기, 계정 한도에 막힌 회차를 측정 아님으로 세기, 스킬 명세의 대조군에도 스킬 호출과 자리 줄 요구하기)를 반영한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 316·338·344(대상 파일이 tools/canary.py인 열린 행 셋)를 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다
브랜치: chore/canary-runner-batch
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-19-34-canary-runner-batch.md(셀프 리뷰, 인계 (커밋 뒤))
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰와 반영을 마치고 커밋 8c2af6ce까지 했다(푸시 안 함, 열린 PR 없음). 남은 단계는 origin/main 합치기(sync_with_base_branch), PR 직전 리뷰(operations.md 리뷰 파이프라인 2, 밀 주장은 일지 "인계 (커밋 뒤)" 절), PR, 봇 회차, 병합, 일지 "## 다음"과 retro다. docs/journal/2026-10-19-34-canary-runner-batch.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `chore/canary-runner-batch (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었으며, 워크트리는 이미 잠기지 않았다(`is not locked`).

open-session을 부른다 2026-10-19T10:57:33Z

## PR과 병합

새 세션이 지시문대로 `git worktree list`에서 이 브랜치의 워크트리를 찾아 `EnterWorktree(path)`로 들어왔다. 일지의 인계 절을
커밋한 뒤 origin/main(`5e7fa88d`, #301·#305·#306·#307)을 `sync_with_base_branch`로 합친다.
`sync_with_base_branch`는 "앱이 만든 워크트리가 아니다"로 거절해 `git merge origin/main`을 직접 쳤다. 충돌은 대기열
338·339 두 행이었고, 338은 이 브랜치의 닫힘, 339는 main의 고친 문장(367을 가리키는 꼬리)을 골라 병합 커밋 `c7d5c36b`로
넣었다.

### PR 직전 리뷰

CodeRabbit CLI는 `Seat: not assigned`(Plan Free)라 돌지 못해 대체 둘을 돌렸다.

- `/security-review`(서브에이전트, 범위 `origin/HEAD...c7d5c36b`): 지적 없음. 스킬 경로 이어 붙이기는 `is_file()`만 보고 명세는
  저장소에 커밋된 입력이라 오탐으로 접었다. 첫 회차는 세션이 끊겨 끝나지 못했고 새로 띄운 회차가 끝났다.
- `bug-perf-review`: Minor 1, Nit 1. 밀 주장 넷은 코드와 맞았다(첫째의 `allowed_warning` 원본은 그 에이전트가 열지 못해 이
  일지의 기록에 기댔다).
  - Minor(유효, 고쳤다): 거절 이벤트의 `resetsAt`이 ISO 문자열이거나 `rateLimitType`이 null이면 모양 검증이 이벤트 전체를
    버려 `rejected`라는 사실까지 잃었다. 거절을 가르는 `status`만 모양을 묻고 다른 두 칸은 `object`로 받아 읽을 수 있는
    만큼만 읽게 했다(`_resets`). `resetsAt: null`은 "풀리는 시각 모름"이다(고치기 전에는 `float` 검증이 null을 거절해 이벤트째 버렸다. 아래 셀프 리뷰가 바로잡았다). 시험을 먼저 써 빨강 다섯을 봤고
    (읽지 못하는 풀리는 시각에 ISO 문자열·`True`를 더하고 결과 없이 이벤트만으로 읽게 바꿨다, 종류 칸 null·숫자), 고친 뒤
    `tests/tools/test_canary.py` 253 초록. 정수 `resetsAt`은 이제 float로 바뀌지 않아 밀리초 갈래의 기대 문구도 고쳤다.
    변이는 원문이 옮겨 간 152를 고치고 158·159를 더해 셋 모두 기대대로.
  - Nit(유효, 두었다): `_Result.api_error`가 객체로 오면 result 줄 전체가 어긋난 줄이 된다. 2.1.300의 원본은 문자열이었고,
    고치면 결과 줄의 다른 칸도 같은 물음이 생겨 이 PR 범위를 넘는다. PR 체크리스트에 적는다.

## 인계 (셀프 리뷰 직전)

> 사용자: 다시 시도

(세션이 한 번 끊겨 다시 시작된 뒤의 사용자 말이다. 끊기기 전의 보안 리뷰 서브에이전트가 끝나지 못해 새로 띄웠다.)

Minor 반영을 마치고 `/code-review`(고정점 `HEAD` = `c7d5c36b`, 미커밋 변경뿐)를 부른 직후 인계 계기가 왔다(`셀프 리뷰 직전`,
세션 컨텍스트 217,729 토큰). 이 세션의 지시문의 "이어받을 상태"는 `인계: 커밋 뒤`라 같은 경계가 아니고, 딥링크로 연 세션이며,
`인계 못함` 줄이 없다. 리뷰 단계는 밟지 않았다. 변경 여섯 파일(`tools/canary.py`, `tests/tools/test_canary.py`,
`.scratch/harness/probes/canary_mutations.toml`·`README.md`, `.scratch/retro-queue.md`, 이 일지)은 커밋하지 않은 채
워크트리에 있다. 이 세션의 제목은 `chore/canary-runner-batch`였고 `chore/canary-runner-batch (인계함)`으로 바꾼다.

새 세션에 남은 일: 미커밋 수정분의 셀프 리뷰(명세는 위 "PR 직전 리뷰" 절의 Minor와 대기열 338 행) → 반영 → 커밋(pre-commit이 검증
다섯을 갈음한다) → 푸시와 PR(체크리스트에 PR 직전 리뷰 둘의 결과와 둔 Nit, 그 값을 적는다) → `@coderabbitai review` → 봇 회차
→ 병합 → 일지 "## 다음"과 retro. 반영으로 새로 쓴 사실 문장(셀프 리뷰가 겨냥할 것, 원문):

- `_LimitInfo` 주석: "거절을 가르는 것은 `status` 뿐이다. 다른 칸은 모양을 묻지 않고 읽을 수 있는 만큼만 읽어, 그 칸의 모양이
  바뀌었다고 거절까지 버리지 않는다".
- `_resets` 독스트링: "원본의 `resetsAt` 은 초 단위 유닉스 시각이었고, 읽지 못하면 값을 적는다".
- 프로브 README: "159는 정수 `resetsAt`이 float로 읽혀 적힌 값이 달라지는 첫 갈래에서 빨개졌다".

지시문:

```
다음 작업: 기능 harness. 대기열 316·338·344(대상 파일이 tools/canary.py인 열린 행 셋: rule 질문에 저장소 규칙도 지시라는 문장 붙이기, 계정 한도에 막힌 회차를 측정 아님으로 세기, 스킬 명세의 대조군에도 스킬 호출과 자리 줄 요구하기)를 반영한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 316·338·344(대상 파일이 tools/canary.py인 열린 행 셋)를 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다
브랜치: chore/canary-runner-batch
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-19-34-canary-runner-batch.md(PR과 병합, PR 직전 리뷰, 인계 (셀프 리뷰 직전))
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 HEAD = c7d5c36b, 범위는 미커밋 변경뿐. 명세는 일지 "PR 직전 리뷰" 절의 Minor와 대기열 338 행의 "어디로" 칸)부터 한다. origin/main은 이미 합쳤고(c7d5c36b), PR 직전 리뷰 둘(/security-review 지적 없음, bug-perf-review Minor 고침·Nit 둠)도 돌았다. 푸시 안 함, 열린 PR 없음. 남은 단계는 셀프 리뷰 반영, 커밋, PR, 봇 회차, 병합, 일지 "## 다음"과 retro다. docs/journal/2026-10-19-34-canary-runner-batch.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `chore/canary-runner-batch (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었으며, 워크트리는 이미 잠기지 않았다(`is not locked`).

open-session을 부른다 2026-10-19T12:10:58Z

## 셀프 리뷰 (미커밋 수정분)

새 세션이 지시문대로 `EnterWorktree(path)`로 들어와 `/code-review`를 돌렸다. 범위: base `c7d5c36b`(=HEAD), 바뀐 파일 6,
커밋 0, 미추적 0. 명세는 위 "PR 직전 리뷰" 절의 Minor와 origin/main 판 대기열 338 행의 "어디로" 칸이다.
두 축 모두 Critical·Major는 없었다.

표준 축(sonnet·high)은 문서화된 표준 위반을 찾지 못했고, 밀 주장 셋은 맞다고 봤다(풀리는 시각 함수에 None·0·-1·nan·inf·
`10**400`·"x"·`[1]`·dict·`False`를 대 예외로 새는 값이 없었다). 판단 항목:

1. Nit: `_LimitInfo` 주석의 "거절을 가르는 것은 `status` 뿐"은 이벤트 안의 말이고, 회차로는 결과의 `api_error`도 거절을 가른다.
2. Nit: 독스트링의 "초 단위"는 커밋하지 않은 원본을 손으로 읽은 것인데 표시가 없다.
3. Nit smell: `_resets`가 널 판정·형 판정·서식화를 한 함수에서 하고, 이름이 명사인데 문구를 돌려준다(Mysterious Name).
   종류 칸은 인라인으로, 시각 칸은 함수로 갈라 읽는다. 읽지 못한 값을 그대로 적어 줄 길이에 상한이 없다.

명세 축의 지적(`read_facts`를 HEAD 판·지금 판·변이 158·159 판에 대 봤다):

1. Minor 누락: `resetsAt: null`과 키 없음을 고정한 시험이 없어 `if resets is None` 갈래를 지워도 빨간 시험이 없다.
2. Minor 틀린 주장: 위 "PR 직전 리뷰" 절이 `resetsAt: null`을 예전과 같다고 적은 것은 사실이 아니다. 고치기 전 판은 null을 `float`
   검증이 거절해 이벤트째 버렸고, "풀리는 시각 모름"은 키가 없을 때뿐이었다. 이번 수정이 그 버그도 함께 고쳤다.
3. Nit: 대기열 338 닫힘의 "시험 열하나"가 세어지지 않는다(origin/main 대비 시험 함수 열).
4. Nit: "빨강 다섯"의 순서. 지금 시험을 HEAD 판에 대면 빨강이 다섯이다(밀리초, ISO, `True`, 종류 null·7).
5. Nit 범위: 숫자 문자열 `resetsAt`과 `True`를 예전에는 pydantic의 느슨한 변환으로 시각으로 읽었고 지금은 "읽지 못했다"로 적는다.

고친 것:

- 시험 `test_풀리는_시각이_null이거나_없으면_모름으로_적는다`(null·키 없음)와 그 갈래를 지우는 변이 160을 더했다. 이로써 338
  시험 함수가 열하나가 되어 대기열의 수가 맞는다. 대기열 338 닫힘의 변이 수를 열둘(149~160)로, 프로브 README 행을 백예순·
  열여섯(145~160)으로 고쳤다.
- "PR 직전 리뷰" 절의 "예전처럼" 문장을 고쳐 고치기 전 판이 null을 버렸다고 적었다.
- `_resets`를 `_describe_resets`로 바꾸고, 독스트링에 "초 단위"의 근거가 `_LIMIT_REJECTED` 주석의 원본을 손으로 읽은 것임과
  "숫자 문자열과 `True` 는 시각으로 읽지 않는다"를 적었다(명세 축 5의 동작을 의도로 기록).

남긴 것:

- 표준 1: 주석이 `_LimitInfo`(이벤트의 모양) 안에 있어 "이벤트 안"이 문맥으로 읽힌다.
- 표준 3의 함수 쪼개기·인라인 비대칭·출력 길이 상한: 한 함수 범위의 다듬기라 두고, 같은 지적이 다시 나오면 retro 후보로
  올린다.
- 명세 4: 빨강 다섯은 명세 축이 HEAD 판으로 다시 세어 맞았다. 기대 문구를 고친 시점은 앞 세션의 기록이라 다시 가리지 않는다.
- 명세 참고(`rateLimitType: ""`이면 "계정 한도(, …)"): 고치기 전 판도 같았고 원본에 없는 꼴이다.

반영으로 새로 쓴 사실 문장(PR 직전 리뷰는 이미 돌았으니 PR 봇이 겨냥할 것, 원문):

- `_describe_resets` 독스트링: "원본의 `resetsAt` 은 초 단위 유닉스 시각이었고(`_LIMIT_REJECTED` 주석의 원본을 손으로
  읽었다), 읽지 못하면 값을 적는다. 숫자 문자열과 `True` 는 시각으로 읽지 않는다".
- 시험 독스트링: "`resetsAt: null` 은 고치기 전 판에서 모양 검증이 이벤트 전체를 버려 거절까지 잃었다".

다시 돌린 것:

- 변이 `--since c7d5c36b` 넷(152·158·159·160) 모두 기대대로(기준선 `tests/tools/test_canary.py` 255 초록). 160은 새 시험의
  null 갈래에서 빨개졌다.
- 손으로 치는 검증 다섯은 커밋의 pre-commit 결과로 갈음한다(결과는 커밋 뒤 이 절에 적는다).
- 첫 커밋 시도는 pytest의 시간 단언 셋(`test_run.py`의 기한, `test_filesystem.py`의 교체 중 읽기 재시도,
  `test_hook_midturn_korean.py`의 2초)으로 막혔다. 이 브랜치가 건드리지 않은 시험이고, 그 회차의 pytest가 1080초(평소 445초)로
  PC가 붐볐다(대기열 332·306과 같은 꼴). 다시 시도했다.
- 둘째 시도의 pre-commit이 모두 Passed(ruff 둘, pyright, lint-imports, check-type-escapes, check-instructions, zizmor,
  run-hooks, web-verify, pytest, 마크다운 표, 줄 구분 문자, 변이 표, 인용, 커밋 메시지. 카나리아 명세 모양과 헌법 판은
  고친 파일이 없어 Skipped). 커밋 `90097b80`.

## 인계 (커밋 뒤)

커밋 `90097b80` 직후 인계 계기가 왔다(`커밋 뒤`, 세션 컨텍스트 205,715 토큰). 이 세션의 지시문의 "이어받을 상태"는
`인계: 셀프 리뷰 직전`이라 같은 경계가 아니고, 요청 범위는 PR과 병합까지이며, `인계 못함` 줄이 없고, 딥링크로 연 세션이다.
이 세션의 제목은 `chore/canary-runner-batch`였고 `chore/canary-runner-batch (인계함)`으로 바꾼다.

남은 단계: 푸시 → PR(템플릿대로. 체크리스트의 PR 직전 리뷰 줄에 위 "PR 직전 리뷰" 절의 결과와 둔 Nit, 그 값을 적고, 셀프
리뷰 줄에 세 회차 모두 Critical·Major 없음을 적는다. 리뷰어 참고에 위 "셀프 리뷰 (미커밋 수정분)" 절의 "반영으로 새로 쓴
사실 문장" 둘) → `@coderabbitai review` → 봇 회차 → 병합 → 일지 "## 다음"과 retro. PR 직전 리뷰는 이미 돌았으므로 다시
돌리지 않는다(이 커밋의 변경은 셀프 리뷰 반영뿐이다).

지시문:

```
다음 작업: 기능 harness. 대기열 316·338·344(대상 파일이 tools/canary.py인 열린 행 셋: rule 질문에 저장소 규칙도 지시라는 문장 붙이기, 계정 한도에 막힌 회차를 측정 아님으로 세기, 스킬 명세의 대조군에도 스킬 호출과 자리 줄 요구하기)를 반영한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 316·338·344(대상 파일이 tools/canary.py인 열린 행 셋)를 chore 한 PR로 반영한다. 행의 "어디로" 칸이 원천이다
브랜치: chore/canary-runner-batch
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-19-34-canary-runner-batch.md(PR 직전 리뷰, 셀프 리뷰 (미커밋 수정분), 인계 (커밋 뒤) 가운데 마지막 것)
이어받을 상태: 인계: 커밋 뒤. PR 직전 리뷰 둘과 미커밋 수정분의 셀프 리뷰·반영을 마치고 커밋 90097b80까지 했다(pre-commit 모두 Passed, 푸시 안 함, 열린 PR 없음). 남은 단계는 푸시, PR(체크리스트 내용은 일지의 마지막 "인계 (커밋 뒤)" 절), @coderabbitai review, 봇 회차, 병합, 일지 "## 다음"과 retro다. docs/journal/2026-10-19-34-canary-runner-batch.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `chore/canary-runner-batch (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었으며, 워크트리는 이미 잠기지 않았다(`is not locked`).

open-session을 부른다 2026-10-19T13:02:21Z

## 푸시와 PR

새 세션이 지시문대로 `EnterWorktree(path)`로 들어왔다. 커밋 뒤 인계 절을 커밋하고(`63badae1`), origin/main(`7556070`,
#309)을 충돌 없이 합쳤다. `sibling_overlap`이 일지 번호 26이 origin/main의 최신 29보다 이름순으로 앞이라고 내어
`--move`로 34로 옮겼다(그 사이 형제가 33을 가져갔다). 인용을 고친 파일은 `tools/canary.py`, `tests/tools/test_canary.py`,
대기열, 프로브 README, 이 일지다. 옛 번호의 잔존은 0이다.

PR #310. 첫 푸시(`16557304`)의 봇 회차:

- CodeRabbit: `Review rate limited`(OSS 시간당 한도)라 리뷰가 없다. 첫 회차로 세지 않는다. 보안·버그·성능 축은 PR 체크리스트에
  적은 PR 직전 리뷰 둘이 대체다.
- claude-review 첫 회차: 경계 지적 없음, 유지보수성 Minor 셋과 Nit 하나. Minor 셋(`_Verdict`의 상태 세 자리를 열거로,
  `Facts.limit`의 문장이 집계 키를 겸함, `_Result.api_error` 완화의 비대칭)은 PR 본문이 둔 위험으로 적은 것이라 리뷰가 후속
  허용으로 판정했고 두었다. Nit(`_describe_resets` 독스트링의 줄 접힘)은 요약 한 줄과 근거 문단으로 나눠 고쳤다.
- 상태를 열거로 모으라는 지적은 셀프 리뷰(위 "셀프 리뷰" 절 표준 4)에 이어 두 번째다. 그 절이 "같은 지적이 다시 나오면
  retro 후보로 올린다"고 적었으므로 retro 후보로 넘긴다.
- '하네스 작업 진행' 세션이 사용자 요청을 전했다. 이 PR은 병합과 일지까지 마치고, next-session으로 새 세션을 열거나 다음
  작업을 시작하지 않고 재개 메시지를 기다린다.
