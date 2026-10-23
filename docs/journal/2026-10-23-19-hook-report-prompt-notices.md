# 2026-10-23 (19) 훅 보고가 사용자 프롬프트 훅의 알림을 센다 (harness 005)

## 구현

> 사용자: (next-session 지시문을 첫 메시지로 받았다) "대기열 404를 티켓 .scratch/harness/issues/005-hook-report-prompt-notices.md로 쓰고 한다 / 다음 작업: 받는 세션이 쓸 .scratch/harness/issues/005-hook-report-prompt-notices.md. `tools/hook_report.py`가 UserPromptSubmit 훅의 알림(명령 없는 `hook_additional_context` 첨부)을 그 훅의 알림으로 세어 뺄 후보로 잘못 내지 않는다 / 다음 단계: 구현 / 어디서: 새 세션. 나란히 여는 6 중 3. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 시작 프롬프트: 대기열 404를 티켓 .scratch/harness/issues/005-hook-report-prompt-notices.md로 쓰고 한다 / 브랜치: chore/005-hook-report-prompt-notices / 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래 / 읽을 것: docs/agents/issue-tracker.md(harness 티켓의 서식·상태·번호). 나란히 여는 나머지 티켓: (…) / 이어받을 상태: 없음 / 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. (…) / 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꿨다. 묶음의 셋째 세션이라 `tidy-checkouts`는 돌지 않았다.
- `EnterWorktree(005-hook-report-prompt-notices)` 뒤 `git branch -m chore/005-hook-report-prompt-notices`. 기점은 origin/main `975bf04c`(#355)다.
- 티켓 번호 005는 지시문이 준 것이다. 티켓과 일지 머리를 쓴 뒤 `tools/sibling_overlap.py`를 다시 치니 일지 05가 나란히 도는 004 세션과 겹쳤다. `--move`를 치는 사이 004 세션이 먼저 06으로 옮겨, 옮길 번호가 없어 옮기지 않았다.

### 기록의 모양 (손으로 봤다)

커밋하지 않은 스크래치 스크립트로 이 PC의 이 저장소 기록 5430개(주 체크아웃과 워크트리 폴더, 같은 uuid 는 한 번)를 읽었다(2026-10-23).

- `hook_success`(명령 있음)는 PostToolUse 7447, Stop 4347, PreToolUse 2201, SessionStart 183건이고 UserPromptSubmit 에는 한 건도 없다. UserPromptSubmit 에는 명령 없는 `hook_additional_context` 462건, 명령 든 `hook_cancelled` 275건, `hook_non_blocking_error` 1건이 있다.
- PreToolUse·PostToolUse 의 계기는 같은 `toolUseID`의 `hook_success`(stdout 원문)와 명령 없는 `hook_additional_context`(모델에게 간 글)로 함께 남는다. 이 세션의 기록에서도 `hook_grep_omitted`·`hook_large_result`·`hook_scratch_probe_rule`이 그 꼴이었고, 첫 턴의 `hook_prompt_directive`는 첨부 하나만 남겼다.
- 두 이벤트는 같은 도구 호출의 `toolUseID`를 함께 쓴다(`hook_midturn_korean`의 PreToolUse 계기와 `hook_pr_next_session`의 PostToolUse 계기가 한 ID 에 있었다). SessionStart 의 첨부는 `toolUseID`가 `"SessionStart"`라 `hook_success`의 uuid 와 다르다. 그래서 `toolUseID`로 짝지으면 SessionStart 계기(클라우드의 `hook_session_web_deps`)를 두 번 센다.
- (세션, 이벤트, 글)로 짝지으니 계기를 낸 `hook_success`는 모두 짝이 있었다(짝 없는 성공 0). 짝 없는 첨부는 UserPromptSubmit 462, SessionStart 72(앱의 "Also still to do in this turn" 59, 워크트리 안내 7, 다른 세션이 연 세션 안내 6), PostToolUse 15(앱의 "PostToolUse hook modified …"와 경로 줄)였다. 짝 없는 UserPromptSubmit 462건은 조각 대조로 모두 `hook_prompt_directive`였다.
- `hook_system_message`(사용자에게 간 글)는 모두 같은 글의 `hook_success`와 짝이 있었다(Stop 165, PostToolUse 143, SessionStart 8, PreToolUse 5). 그래서 홀로 남는 꼴은 계기 첨부 하나다.

### 설계

- 계기 첨부 하나를 같은 (세션, 이벤트, 글)의 `hook_success` 하나와 짝짓고, 짝이 없는 첨부의 글만 막음과 같은 조각 대조로 훅을 골라 알림으로 센다. 짝은 명령을 가리지 않아 플러그인 훅의 글은 그 훅의 `hook_success`와 짝이 되어 빠진다. 래퍼의 두 문구는 짝 없는 첨부에서도 거른다(UserPromptSubmit 은 래퍼의 `CONTEXT_EVENTS`다).
- 짝 없는 첨부 가운데 어느 훅인지 가르지 못한 것(앱의 글)은 버리지 않고 표 밖에 "가르지 못한 알림"으로 글의 머리와 함께 적는다. 등록 훅이 계기 문장을 바꿔 조각과 맞지 않게 되면 여기서 보인다.
- 조각 대조 함수 `blocking_hook`을 `fragment_owner`로 이름을 바꿨다. 알림에도 쓰게 되어서다.
- `tools/morning_collect.py`의 "가르지 못한 막음이 N건" 줄은 종류를 보지 않고 세어, 가르지 못한 알림이 생기면 막음으로 보였다. 같은 PR 에서 막음과 알림으로 나눴다.
- ADR 0036 의 "`hook_report.py`가 읽는 것"은 알림을 `hook_success`로만 적지만, 그 절이 독스트링을 원천으로 들고 대기열 행이 ADR 불필요로 판정해 ADR 은 고치지 않았다.
- `KICKOFF.md`의 저장소 상태 시험 줄에 셋째 시험(`ran >= 1`, 이 저장소의 UserPromptSubmit 훅의 계기 사례를 실제로 돌린다)을 더했다. 이 저장소의 훅 페이로드 사례를 돌리는 시험이라 런북을 복사하는 쪽이 알아야 해서다.

### 시험과 변이

- 빨강을 먼저 봤다. 새 시험 열셋을 고르고 고치기 전의 코드로 돌리니 8 failed, 5 passed였다. 통과한 다섯은 첨부를 세지 않는 옛 코드에서도 참인 "세지 않는다" 쪽 시험(짝이 있으면 세지 않는다, 이벤트가 다르면 짝이 아니다, 래퍼 알림은 세지 않는다 등)이다.
- 고친 뒤 `tests/tools/test_hook_report.py`와 `tests/tools/test_morning_collect.py` 115개가 통과했다.
- 이 PC의 실제 기록으로 보고를 고치기 전과 뒤로 돌렸다. 전에는 `뺄 후보: hook_prompt_directive.py(2026-09-23 들임)`였고, 뒤에는 `hook_prompt_directive.py`가 알림 461건·발동한 날 25일로 표에 들고 `뺄 후보: (없음)`이다.
- `.scratch/harness/probes/hook_report_mutations.toml`에 변이 열둘(21~32)을 더하고 전체 서른둘을 돌려 모두 기대대로 빨강이었다. `tools/mutate.py`가 시험을 고친 판이라 리뷰 반영과 커밋 뒤 전체를 다시 돌리라고 알렸다(대기열 359). 프로브 README 의 결과 줄은 이 실행으로 적었다.
- `uv run python tools/run_checks.py`를 백그라운드로 띄웠고 인계 전에 멈췄다. 멈출 때까지 check-ticket, check-instructions, lint-imports, zizmor, check-type-escapes, pyright, pyright-linux, run-hooks 여덟이 Passed였고, pytest 갈래와 web 은 결과를 보지 못했다. ruff check 와 format --check 는 통과했다.

### 이 세션이 막히거나 고친 것

- Grep 에 `!{...}` 부정 glob 을 주자 `hook_env_read`가 `.env`에 닿는다며 막았다. 확장자 glob 으로 좁혀 다시 찾았다.
- 스크래치패드로 `cd`하자 `hook_bash_cd_outside`가 막았다. 스크립트는 Edit 도구로 직접 고쳤다.
- 파이프를 쓴 pytest 에 `hook_bash_gate_pipe`가 경고해, 그 뒤로는 출력을 스크래치패드 파일로 리다이렉트했다.

## 인계 (셀프 리뷰 직전)

- `/code-review`를 부르자 `hook_handoff`가 세션 컨텍스트 340,760 토큰으로 문턱 200,000 을 넘은 채 `셀프 리뷰 직전`에 왔다고 알렸다. 셀프 리뷰는 밟지 않고 넘긴다.
- 인계하지 않는 다섯 경우는 없었다. Skill 호출은 실패하지 않았고, 요청 범위는 PR 과 병합까지이며, 이어받을 상태는 `없음`이고, 이 일지에 `인계 못함` 줄이 없으며, `get_session`의 `self`에 `parentSessionId`가 없다.
- 지금 제목: `chore/005-hook-report-prompt-notices`.
- 새 세션이 할 일: `/code-review` 셀프 리뷰와 반영, 이 일지 마무리, 티켓을 done 으로 바꾸고 수용 기준 체크, 커밋, PR 직전 리뷰, 변이 서른둘 다시 돌리기와 README 결과 줄 고치기, PR·봇 회차·워크트리에서 병합, 다음 지시문.

지시문:

```
다음 작업: .scratch/harness/issues/005-hook-report-prompt-notices.md. `tools/hook_report.py`가 UserPromptSubmit 훅의 알림(명령 없는 `hook_additional_context` 첨부)을 그 훅의 알림으로 세어 뺄 후보로 잘못 내지 않는다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 404를 티켓 .scratch/harness/issues/005-hook-report-prompt-notices.md로 쓰고 한다
브랜치: chore/005-hook-report-prompt-notices
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/agents/issue-tracker.md(harness 티켓의 서식·상태·번호), .scratch/harness/issues/005-hook-report-prompt-notices.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review`)부터 한다. docs/journal/2026-10-23-19-hook-report-prompt-notices.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

- 제목을 `chore/005-hook-report-prompt-notices (인계함)`으로 바꿨고, 백그라운드 `run_checks.py`를 멈췄고, `git worktree unlock`으로 이 워크트리의 잠금을 풀었다.
- open-session을 부른다 2026-10-22T18:25:37Z

## 셀프 리뷰 (이어받은 세션)

> 사용자: (위 지시문을 첫 메시지로 받았다) "대기열 404를 티켓 .scratch/harness/issues/005-hook-report-prompt-notices.md로 쓰고 한다 / (…) 이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review`)부터 한다. (…) 이번 요청 범위: PR과 병합까지"

- 제목을 브랜치 이름으로 되돌리고 `EnterWorktree(path)`로 이 워크트리에 들어왔다.
- 리뷰 전에 `uv run python tools/run_checks.py`를 백그라운드로 다시 돌렸다. 열 검사가 모두 Passed였다(pytest 613.9초, web-verify 530.2초. 리뷰 서브에이전트 둘이 함께 돌던 때다).
- `/code-review`의 범위: 기준 `975bf04c`, 수정 7개, 커밋 0개, 미추적 2개(이 티켓과 이 일지).

### 두 축의 보고

명세 축:
- 수용 기준 1·2·3은 충족했다. 실제 기록으로 돌린 보고에서 `hook_prompt_directive.py`가 알림 464건으로 표에 들고 `뺄 후보: (없음)`이었다. 기준 5는 그때 결과를 보지 못했다.
- Major: 짝 없는 첨부를 이벤트를 가리지 않고 모든 훅의 조각과 견줘, 앱이 넣은 글이 훅의 알림으로 잡힌다. `…\scratchpad\ins-runs-empty.html is now visible in the Browser pane.`(PostToolUse 3건)이 10자 조각 `scratchpad`로 `hook_scratch_probe_rule.py`의 알림이 됐고, `PostToolUse hook modified …` 7건은 조각 `PostToolUse` 때문에 `(여럿)`이 됐다. 독스트링의 "앱이 넣은 계기는 `UNKNOWN`"과 어긋나고, 조용한 훅이 뺄 후보에서 숨는 반대 방향의 오판이다.
- Minor(기준 4): 시험이 없는 항목이 셋이다. `hook_system_message`를 읽지 않는다는 항목, JSON 이지만 `additionalContext`가 없는 `hook_success`의 갈래, 그리고 `test_짝은_세션과_이벤트가_모두_같아야_짓는다`가 서로 다른 `toolUseID`를 써서 `toolUseID`로 짓지 않는 까닭을 고정하지 못한다.
- Minor(잔존): ADR 0036 32행 "그 호출은 기록에 `hook_success` 첨부를 남기고, 훅 이름은 그 명령에서 읽는다"가 이제 틀렸다.
- Nit: 갈라진 세션이 같은 uuid 를 다른 세션 id 로 옮겨 적은 훅 기록이 이 PC에 253건 있다. 짝 가운데 하나만 옮겨지고 그 파일이 먼저 읽히면 두 번 센다(함수로 재현). 일지의 "새 시험 열셋"은 diff 에서 12개다.
- 범위 넘침은 없다(`morning_collect` 줄 분리는 기준 3에서, `KICKOFF.md` 줄은 시험이 셋으로 는 데서 따라 나온다).

표준 축:
- Major: 명세 축과 같은 오귀속(scratchpad 3건, `PostToolUse` 7건이 `(여럿)`)이고, 그 입력을 고정한 시험이 없다.
- Minor: ADR 0036 "`hook_report.py`가 읽는 것"이 이제 거짓이다. ADR 은 살아 있는 문서라 승인을 받아 고쳐야 한다.
- Nit: 독스트링의 "5430개 … 손으로 봤다"에 명령이 없다. "`toolUseID`로 짓지 않는 것은 PreToolUse 와 PostToolUse 가 같은 ID 를 쓰고"는 `(toolUseID, 이벤트)`로 지으면 풀리므로 까닭이 되지 못하고, 까닭은 SessionStart 쪽뿐이다. 일지의 열셋은 12개다.
- 냄새(판단): `scan`의 `sent`/`shown` 이름, `ContextKey`를 `key[2]`로 읽는 것(NamedTuple 후보), `_context_keys`가 내는 두 리스트의 뜻이 자리로만 정해지는 것.
- 확인한 것: "이 저장소의 훅은 JSON 을 낸다"는 `tools/hook_*.py`의 출력 전수에서 맞았고, KICKOFF 의 문턱 셋은 시험의 값과 같았다.

### 반영

고친 것:
- Major(두 축): 짝 없는 첨부는 UserPromptSubmit(`PROMPT_EVENT`)의 것만 그 이벤트에 등록된 훅의 조각과 견주고, 다른 이벤트의 것은 `(모름)` 알림으로 센다. `scan`이 셋째 인자로 그 이벤트의 훅을 받고(빠뜨리면 pyright 가 잡도록 기본값 없이), `registered_hooks`가 이벤트를 받는다. `main`과 `morning_collect._gather_hooks`가 넘긴다.
- 차례: 동작을 바꾸지 않는 정리(아래 냄새)를 먼저 하고 두 시험 파일 115개가 그대로 통과하는 것을 본 뒤, 시험을 먼저 고치고 더해 고치기 전 코드로 돌리니 9 failed(일곱은 기대값이 어긋난 단언, 둘은 아직 없는 `registered_hooks`의 이벤트 인자)였다. 구현 뒤 121 passed.
- Minor(명세 축 기준 4): `hook_system_message` 첨부를 읽지 않는 시험, JSON 이지만 `additionalContext`가 없는 갈래(못 보는 것 시험의 매개변수 하나와 `model_context`의 경계 입력 시험), `test_짝은_세션과_이벤트가_모두_같아야_짓는다`에서 PreToolUse 와 PostToolUse 가 같은 `toolUseID`를 쓰게 했다.
- Minor(잔존, 두 축): ADR 0036 에 이력 "2026-10-23 UserPromptSubmit 훅의 알림은 hook_success 없이 첨부로만 남아 글의 조각으로 센다"와 32행의 포인터를 더했다. `tools/check_adr_pointers.py`가 통과했다.

> 사용자: (선택 화면 "ADR 0036에 이력 한 절과 본문 포인터 하나를 더해도 될까요? 결정 자체(0건의 뜻, 뺄 후보 판정)는 바뀌지 않고, 훅 보고가 기록을 읽는 사실만 고칩니다.") "이대로 더한다 (Recommended)" — "본문 32행의 '훅 이름은 그 명령에서 읽는다.' 뒤에 '(바뀜: 이력 2026-10-23 …)' 표시가 붙고, 파일 끝에 '## 이력' 절이 새로 생깁니다. 초안은 작업 트리에 이미 써 두었고(포인터 검사 통과), 승인하면 이 PR에 함께 싣습니다." (미리보기는 지금 ADR 의 이력 절 그대로다)

- Nit(표준 축): 독스트링에서 `toolUseID`로 짓지 않는 까닭을 SessionStart 쪽 하나로 고쳤다. 짝 열쇠에 이벤트가 드는 까닭은 위 시험이 고정한다.
- Nit(명세 축): 같은 uuid 의 기록이 다른 세션 id 로 여러 기록 파일에 있는 것을 손으로 다시 봤다(이 PC의 훅 첨부 172개. 명세 축의 253은 다른 단위로 센 것으로 보인다). 못 보는 것에 적고 시험으로 고정했다.
- 냄새(표준 축): `ContextKey`를 `NamedTuple`로, 두 리스트를 내던 `_context_keys`를 `_given_context`·`_attached_contexts`로 나눴다. `sent`/`shown`은 없어졌다. `_is_notice`의 인자 이름을 `text`로 바꿔 변이 원문 둘을 함께 고쳤다.
- 이 PC의 기록으로 고친 보고를 돌렸다(UTC 2026-10-22 창). `hook_prompt_directive.py`가 알림 467건으로 표에 들고 `뺄 후보: (없음)`이며, 가르지 못한 알림 87건(SessionStart 72, PostToolUse 15)에 리뷰가 짚은 `scratchpad` 경로 글 3건과 `PostToolUse hook modified` 7건이 `(모름)`으로 들었다.
- 변이 표: 셋을 더하고(UserPromptSubmit 밖을 조각으로 가르기, 모든 훅의 조각과 견주기, 등록 훅을 이벤트로 거르지 않기) 원문 열하나를 고쳐 서른다섯이다. 커밋 전 작업 트리에서 모두 기대대로 빨강이었고, `tools/mutate.py`가 커밋하지 않은 변경이 있다고 알려 커밋 뒤 다시 돈다.
- main 대조: `tools/sibling_overlap.py`의 origin/main 줄이 움직여 `git diff --name-only HEAD...origin/main`을 이 브랜치가 고친 파일과 맞댔다. main에 새로 선 규약 둘을 봤다. `docs/agents/issue-tracker.md`의 "결과를 본 뒤 판정 기준(표지, 문턱, 무엇을 하나로 세는지)을 바꿨으면 바꾼 기준과 그 까닭을 결과와 함께 적는다"에 따라 프로브 README 행에 `toolUseID` 변이의 `-k`를 넓힌 것과 그 까닭을 더했다. `CODING_STANDARDS.md`의 `bool | None` 금지는 이 브랜치의 코드에 해당하는 자리가 없다.

PR 직전 `bug-perf-review`에 밀 주장으로 넘길 새 사실 문장(원문):
- `.scratch/harness/probes/README.md`의 `hook_report_mutations.toml` 행: "`tools/mutate.py`가 pytest에 `-x`를 붙여, 그 변이는 파일에서 앞선 SessionStart 갈래 시험이 빨개지자 멈추고 짝 열쇠 시험을 돌지 않았다."
- `tools/hook_report.py` 독스트링: "다른 이벤트에서는 이 저장소의 훅이 `hook_success`를 남겨 짝이 있으니, 짝 없는 첨부는 `UNKNOWN` 알림이다."
- 같은 곳: "이벤트를 가리지 않고 모든 훅의 조각과 견주던 판은 앱의 글에 든 낱말(경로의 `scratchpad`, `PostToolUse`)이 10자 이상 조각과 맞아 그 훅의 알림이나 `AMBIGUOUS`로 셌다"
- 같은 곳: "짝을 `toolUseID`로 짓지 않는 것은 SessionStart의 첨부는 그 자리가 이벤트 이름이라 `hook_success`의 것과 달라서다."
- 못 보는 것: "짝 없는 UserPromptSubmit 첨부는 조각으로만 훅을 가르므로, 그 이벤트의 훅 조각이 든 다른 글(앱이 그 이벤트에 넣은 글이 있다면)도 그 훅의 알림으로 센다."
- 못 보는 것: "stdout이 JSON이 아니거나 `additionalContext`가 없는 `hook_success`는 짝이 되지 못해, 같은 글의 첨부가 짝 없는 첨부로 남아 그 알림을 한 번 더 센다(UserPromptSubmit 밖이면 `UNKNOWN` 알림으로)."
- 못 보는 것: "같은 uuid의 기록이 다른 세션 id로 여러 기록 파일에 있다(2026-10-23 이 PC의 훅 첨부 172개, 손으로 봤다). 같은 uuid는 처음 읽은 것만 세므로, 앞 파일에 `hook_success`만 다른 세션 id로 적혀 있으면 뒤 파일의 첨부가 짝을 잃어 한 번 더 센다"
- ADR 0036 이력: "다른 이벤트의 훅이 모델에게 넘긴 글은 `hook_success`와 같은 글의 첨부로 함께 남는다"
- 시험 독스트링: "사용자에게 간 글이고, 같은 글의 `hook_success` 와 늘 짝이 있었다"

남긴 것:
- Nit(표준 축) "5430개 … 손으로 봤다"에 명령이 없다: 앞 세션의 커밋하지 않은 스크래치 스크립트라 명령을 되살릴 수 없고, 같은 독스트링의 2026-10-19 관찰도 같은 꼴이다. 두 리뷰가 같은 수(짝 없는 첨부 469~470/72/15, 짝 없는 `hook_success` 0)를 다시 내어 사실은 맞다. 고치지 않는다.
- Nit "새 시험 열셋": 앞 절은 앞 세션의 기록이라 고치지 않는다. 리뷰가 diff 에서 센 새 시험 함수는 열둘(`hook_report` 11, `morning_collect` 1)이었다.

다시 돌린 명령:
- `uv run pytest -q tests/tools/test_hook_report.py tests/tools/test_morning_collect.py`: 121 passed.
- `uv run ruff check`·`uv run ruff format --check`(고친 세 파이썬 파일): 통과. `uv run python tools/check_adr_pointers.py`: 출력 없이 0.
- `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/hook_report_mutations.toml`: 변이 35 모두 기대대로.
- 나머지 손으로 치는 검증 명령은 커밋의 pre-commit 으로 갈음한다. 결과는 커밋 뒤 아래에 적는다.

### 커밋 뒤

- 커밋 `50218031`의 pre-commit: ruff check·ruff format 통과, 러너(`tools/run_checks.py`)의 열 검사(check-ticket, lint-imports, check-instructions, zizmor, check-type-escapes, pyright-linux, pyright, run-hooks, web-verify, pytest) 모두 통과(353.95s), 마크다운 표·줄 구분 문자·변이 표 원문 통과, 카나리아 명세와 헌법 판은 고친 파일이 없어 `Skipped`(이 브랜치는 둘 다 건드리지 않았다). 인용 대조 경고 둘은 막지 않는 경고이고, 하나는 셀프 리뷰가 옛 독스트링을 옮긴 기록(92행), 하나는 main 에만 있던 `docs/agents/issue-tracker.md`의 문장(111행)이라 main 을 합쳐 풀렸다.
- 앱의 `sync_with_base_branch`는 앱이 만든 워크트리가 아니라고 거절해, `git fetch origin` 뒤 `git merge --no-edit origin/main`으로 합쳤다(커밋 `1106dbbe`, 충돌 없음. `.scratch/harness/probes/README.md`는 자동으로 합쳐졌다). 합친 뒤 `tools/sibling_overlap.py`는 번호 겹침 없음.
- 합친 판에서 `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/hook_report_mutations.toml`: 변이 35 모두 기대대로. 그런데 `toolUseID` 변이의 출력이 "1 failed, 51 deselected"로, `-k`에 든 두 시험 가운데 앞의 것에서 멈췄다. `tools/mutate.py`가 pytest에 `-x`를 붙이기 때문이다(891행). 셀프 리뷰 반영에서 `-k`에 짝 열쇠 시험을 `or`로 더한 것은 아무것도 더 재지 않았다. 그 변이를 갈래마다 하나로 나눠(서른여섯) `… hook_report_mutations.toml 25 26`으로 돌리니 둘 다 기대대로 빨강이었고, 짝 열쇠 시험(`test_짝은_세션과_이벤트가_모두_같아야_짓는다`)이 혼자서도 그 변이를 잡았다. README 행을 이 사실로 고쳤다.
- 그 고침을 커밋 `3d43ccca`로 했다. pre-commit: ruff 둘은 `.py`가 없어 `Skipped`(이 커밋은 파이썬을 고치지 않았다), 러너의 열 검사 모두 통과(452.06s, main 을 합친 판의 전체 검사이기도 하다), 마크다운 표·줄 구분 문자·변이 표 원문 통과, 카나리아와 헌법 판은 `Skipped`. 인용 대조 경고 하나는 도구 출력("1 failed, 51 deselected")을 옮긴 것이다.
- CodeRabbit CLI 는 `coderabbit auth status`가 `Seat: not assigned`라 PR 직전 리뷰는 대체 둘(`/security-review`, `bug-perf-review`)로 한다. 아직 돌리지 않았다.

### 인계 (커밋 뒤)

세션 컨텍스트가 229,830 토큰으로 문턱을 넘은 채 커밋 `3d43ccca` 뒤 경계에 와서 인계 계기가 왔다. 인계하지 않는 때 다섯을 대 봤다. 커밋은 성공했고, 요청 범위는 병합까지이며, 이 세션을 연 지시문의 경계는 `셀프 리뷰 직전`이라 다르고, `인계 못함` 줄이 없으며, `get_session`의 `self`에 `parentSessionId`가 없다. 넘기기 전 이 세션의 제목은 `chore/005-hook-report-prompt-notices`다.

지시문:

다음 작업: .scratch/harness/issues/005-hook-report-prompt-notices.md. `tools/hook_report.py`가 UserPromptSubmit 훅의 알림(명령 없는 `hook_additional_context` 첨부)을 그 훅의 알림으로 세어 뺄 후보로 잘못 내지 않는다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 404를 티켓 .scratch/harness/issues/005-hook-report-prompt-notices.md로 쓰고 한다
브랜치: chore/005-hook-report-prompt-notices
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-23-19-hook-report-prompt-notices.md(셀프 리뷰 반영, 커밋 뒤, 이 인계 절), docs/agents/issue-tracker.md(harness 티켓의 서식·상태·번호)
이어받을 상태: 인계: 커밋 뒤. 구현과 셀프 리뷰 반영(커밋 50218031), origin/main 합침(1106dbbe), toolUseID 변이 나누기(3d43ccca)까지 커밋했고 아직 푸시하지 않았다(열린 PR 없음). 남은 단계는 PR 직전 리뷰(CodeRabbit CLI 는 좌석 미배정이라 `/security-review`와 `bug-perf-review`를 나란히 돌리고, 일지의 "PR 직전 `bug-perf-review`에 밀 주장으로 넘길 새 사실 문장" 목록을 그 브리프에 넘긴다), 반영, 푸시와 PR 열기, 봇 회차, 워크트리에서 병합, next-session 이다. 일지는 이 인계 절까지 커밋하지 않았다. docs/journal/2026-10-23-19-hook-report-prompt-notices.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지

제목을 `chore/005-hook-report-prompt-notices (인계함)`으로 바꿨다. 멈출 백그라운드 작업은 없었고, `git worktree unlock`은 `is not locked`로 넘어갔다.

open-session을 부른다 2026-10-22T23:34:41Z

## PR 직전 리뷰 (이어받은 둘째 세션)

> 사용자: (위 지시문을 첫 메시지로 받았다) "대기열 404를 티켓 .scratch/harness/issues/005-hook-report-prompt-notices.md로 쓰고 한다 / (…) 이어받을 상태: 인계: 커밋 뒤. 구현과 셀프 리뷰 반영(커밋 50218031), origin/main 합침(1106dbbe), toolUseID 변이 나누기(3d43ccca)까지 커밋했고 아직 푸시하지 않았다(열린 PR 없음). (…) 이번 요청 범위: PR과 병합까지"

- 제목을 브랜치 이름으로 되돌리고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. `git fetch origin` 뒤 origin/main 은 `d0e696c9`로 합친 판 그대로였다.
- `coderabbit auth status`는 앞 세션이 본 대로 좌석 미배정이라, 대체 둘을 나란히 돌렸다. `/security-review`는 커밋 `3d43ccca`(origin/main 합침 뒤)에서 돌렸다.

### PR 직전 리뷰의 보고

`/security-review`: 1단계 서브태스크가 후보를 하나도 내지 않아 2단계(오탐 거르기)를 띄우지 않았다. 바뀐 코드는 개발자 PC의 기록을 읽어 수를 세는 로컬 CLI이고, 새 실행 경로(`eval`, `subprocess` 등)와 경로 탈출이 없으며, 수집 JSON에는 여전히 건수만 든다.

`bug-perf-review`(기준 `975bf04c`, 범위 `origin/main...HEAD`의 10개 파일, 호출 36번):
- 유효 Minor 1: `main`(`tools/hook_report.py`)과 `_gather_hooks`(`tools/morning_collect.py`)가 UserPromptSubmit 의 훅을 `scan`에 넘기는 배선을 지키는 시험이 없다. 누가 그 인자를 `()`로 바꿔도 시험이 모두 초록이고, 그러면 `hook_prompt_directive`가 다시 뺄 후보로 나온다. `main` 시험의 임시 저장소는 PostToolUse 훅만 등록하고, `_gather_hooks`를 부르는 시험은 없었다.
- 밀 주장 아홉은 모두 근거와 맞았다. 일곱째(같은 uuid 가 다른 세션 id 로 여러 파일에 있는 것)에는 반대 방향(앞 파일에 첨부만 다른 세션 id 로 있는 것)도 같은 결과라는 보강을 권했고, 리뷰가 센 수는 125개(`hook_success`와 `hook_additional_context`만)였다.
- 오탐 여섯: 수집 JSON 으로 첨부 머리가 샌다(건수만 직렬화된다), `blocking_hook` 옛 이름의 잔존(일지 한 줄뿐), `content`가 문자열인 첨부의 누락(이 PC의 485건 모두 리스트), 짝 없는 첨부의 날짜가 파일 순서에 따라 하루 어긋날 수 있음(건수는 맞다), ADR 0036 본문의 "변이 스물"(날짜가 붙은 이력), 독스트링의 462건·5430개(날짜가 붙은 손 측정).

### 반영

고친 것:
- 유효 Minor: `main` 시험의 임시 저장소(`_hook_repository`)가 UserPromptSubmit 에도 훅을 등록하게 하고, 그 훅의 짝 없는 첨부를 기록에 더해 표의 행(`| hook_prompt.py | 1 | 0 | 1 | 2026-10-18 |`)을 단언한다. `morning_collect`에는 임시 git 저장소로 그 함수를 부르는 시험을 더했다. 시험에서 부르려고 `_gather_hooks`를 `gather_hooks`로 바꿨다(pyright strict 가 다른 모듈의 비공개 이름을 막는다. 같은 파일의 `gather_tickets`·`gather_works`와 같은 꼴이다).
- 두 배선을 깨는 변이 둘(37·38)을 표에 더했다. `… hook_report_mutations.toml 37 38`로 둘 다 기대대로 빨강이었고, 이어 서른여덟 전체를 커밋 전 작업 트리에서 돌려 모두 기대대로 빨강이었다. 프로브 README 행에 적었다.
- 파이썬 `write_text`로 README 행을 고치자 윈도에서 그 파일 전체가 CRLF 가 됐다(`git ls-files --eol`의 `w/crlf`). `test_hook_report.py`도 같은 꼴이었다(어느 편집에서 바뀌었는지는 가르지 않았다). 둘 다 `sed -i 's/\r$//'`로 LF 로 되돌렸다. 색인은 LF 이고 `.gitattributes`가 `eol=lf`라 커밋에는 영향이 없었다.

남긴 것:
- 밀 주장 일곱째의 반대 방향 보강: 리뷰가 이 PC의 기록에서 세션 id 를 무시하면 짝이 지어질 첨부가 0이라 지금은 과다 계산이 없다고 봤고, 독스트링에 더하면 시험 하나를 함께 둬야 한다. 판정을 바꾸지 않는 보강이라 이 PR 에서는 더하지 않는다.
- 172 와 125 의 차이: 앞 세션의 172는 손으로 본 수이고 명령이 남지 않았다. 리뷰의 125는 첨부 종류 둘만 센 것이라 단위가 다르다. 독스트링의 문장(같은 uuid 가 여러 세션 id 에 있다)은 두 수 어느 쪽으로도 참이다.

다시 돌린 명령:
- `uv run pytest -q tests/tools/test_hook_report.py tests/tools/test_morning_collect.py`: 122 passed.
- `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/hook_report_mutations.toml`: 변이 38 모두 기대대로(커밋하지 않은 변경이 있다는 알림이 함께 났다).
