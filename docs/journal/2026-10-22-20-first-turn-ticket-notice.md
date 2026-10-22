# 2026-10-22 (20) 첫 턴 훅이 티켓 없는 브랜치를 알린다 (ticket-for-every-pr 05)

## 구현

> 사용자: (next-session 지시문을 첫 메시지로 받았다) ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 (…) 인자: .scratch/ticket-for-every-pr/issues/05-first-turn-ticket-notice.md / 다음 작업: .scratch/ticket-for-every-pr/issues/05-first-turn-ticket-notice.md. 첫 턴 훅이 티켓 없는 브랜치를 알린다 / 다음 단계: 구현 / 어디서: 새 세션. 나란히 여는 2 중 2. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 시작 프롬프트: /implement .scratch/ticket-for-every-pr/issues/05-first-turn-ticket-notice.md / 브랜치: feature/05-first-turn-ticket-notice / 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래 / 읽을 것: docs/journal/2026-10-22-14-commit-check-blocks-ticketless.md의 "다음", 나란히 도는 .scratch/ticket-for-every-pr/issues/04-ci-checks-ticket-done.md(둘 다 KICKOFF.md의 다른 줄을 고친다) / 이어받을 상태: 없음 / 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. (…) / 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꿨다. 묶음의 둘째 세션이라 `tidy-checkouts`는 돌지 않았다.
- `EnterWorktree(05-first-turn-ticket-notice)` 뒤 `git branch -m feature/05-first-turn-ticket-notice`. `git worktree list --porcelain`에 그 브랜치를 쓰는 다른 자리는 없었다. `uv sync`, `pnpm -C web install --frozen-lockfile` 모두 0. 기점은 origin/main `e62eb052`(#350, 티켓 03)다.

### 실제 확인의 길 (사용자가 골랐다)

> 질문: 새 첫 턴 알림이 실제 앱 세션의 모델에게 닿는지 확인하려면, 이 워크트리 폴더(.claude/worktrees/05-first-turn-ticket-notice)를 작업 위치로 둔 새 앱 세션이 하나 필요합니다. (…) 어떻게 할까요?
>
> 고른 것: "이 세션이 새 세션을 연다 (추천)" — 이 세션이 세션 시작 도구로 그 워크트리 폴더에 새 세션을 열고 질문 하나를 보냅니다. 사이드바에 새 세션이 하나 생기고, 답을 받은 뒤 그 세션을 보관할지 묻습니다. 티켓 06의 확인이 같은 길(워크트리 폴더를 작업 위치로 준 새 세션)에서 그 워크트리의 훅이 도는 것을 봤습니다.

다른 선택지는 "직접 연다"(사람이 열고 한 줄을 붙여 넣는다)와 "이번에는 건너뛴다"(일지에 보지 못했다고 적는다)였다.

### 모델에게 닿는지 (실제 앱 세션)

- 2026-10-22 12:27Z, 이 세션이 세션 시작 도구로 작업 위치를 이 워크트리 폴더로 준 새 세션 "첫 턴 알림 확인 (티켓 05)"을 열었다(`claude-sonnet-5-5`, xhigh, auto, 사람이 보는 앱 세션, claude 2.1.302). 첫 메시지는 지시문이 아니고, 훅이 넣은 문맥이 있으면 그 첫 문장과 `git branch -m` 이 든 문장을 글자 그대로 옮기고 없으면 "없음"이라고만 답하라는 한 단락이었다. 도구를 부르지 말라고 했다.
- 답: 문맥이 있다고 했고 첫 문장으로 "지시문 없이 연 세션의 첫 메시지다."를, 둘째로 `TICKET_NOTICE` 의 2) 문장("이름은 티켓 파일 이름의 stem 이라(…) `git branch -m <새 이름>` 으로 바꾼다.")을 옮겼다. 꺾쇠가 따옴표로 바뀐 것 말고는 `tools/hook_prompt_directive.py` 181~183줄과 같다. 도구는 부르지 않았다고 했다.
- 이 문구는 이 브랜치에만 있다(주 체크아웃과 origin/main 의 훅은 지시문이 아닌 첫 메시지에 아무것도 붙이지 않는다). 그래서 옮긴 문장은 이 워크트리의 훅이 그 세션에서 돌았고 그 문맥이 모델에게 닿았다는 표지다.
- 못 본 것: 주 체크아웃에서 연 세션(알림의 "워크트리에 먼저 들어간다" 조건문이 실제로 그 순서를 끌어내는지)과, 알림을 받은 모델이 커밋할 일을 받았을 때 티켓·브랜치·제목을 실제로 차례대로 맞추는지. 이번 확인은 닿는지만 봤다.
- 확인 세션의 정리:

> 질문: 알림 확인용으로 열었던 세션 "첫 턴 알림 확인 (티켓 05)"은 훅 문맥의 첫 문장을 그대로 옮겨 오고 턴을 끝냈습니다. (…) 이 세션을 언제 정리할까요?
>
> 고른 것: "푸시 뒤에 보관 (추천)" — 이 워크트리의 작업을 커밋해 원격에 올린 뒤에 그 세션을 보관합니다. 그 세션은 자기 워크트리 없이 이 워크트리 폴더에서 돌았고, 보관이 작업 폴더를 건드리지 않는다는 것은 도구 설명으로 판단한 어림입니다. 그래서 커밋하지 않은 작업이 없을 때 보관합니다.

다른 선택지는 "그대로 둔다"였다.

## 셀프 리뷰 (`/code-review`)

범위: base `e62eb052`, 바뀐 파일 8, 미추적 4, 커밋 0. 표준 축(sonnet, high)과 명세 축(이 세션의 모델)을 나란히 돌렸다. 리뷰 전 전체 게이트(`tools/run_checks.py`)는 모두 Passed(pytest 531초, web-verify 371초), ruff 둘도 초록이었다.

### 표준 축

Critical·Major 없음. 변이 하나를 넣어 돌리다 170초에 끊었고(다른 세션 셋의 `mutate.py` 가 함께 돌았다), 끊은 뒤 훅 파일이 원문 그대로인 것을 그 축과 이 세션이 다시 봤다.

1. Minor. `TICKET_NOTICE` 1)이 이미 있는 티켓을 "새로 쓰지 않는다"까지만 말해, `to-tickets` 가 쓴 `ready-for-agent` 티켓의 상태를 바꾸라는 말이 없다(`docs/agents/issue-tracker.md` 15줄). → 고친다.
2. Minor. "면제 일 … 티켓을 쓰지 않는다"가 닫힌 주장으로 거짓이다. 면제 PR에서 회고가 고침을 반영하면 harness 티켓 한 장을 같은 PR에 쓴다(같은 문서 7줄). → 고친다.
3. Minor. 슬래시 명령으로 연 세션(`/tidy-checkouts`)도 지시문이 아니라 알림을 받는데 독스트링의 못 보는 것과 시험에 없다. 첫 assistant 기록이 쓰이기 전에 둘째 프롬프트가 들어오면 두 번 알리는지도 보지 않았다. → 못 보는 것과 시험에 더한다.
4. Nit. 독스트링의 "이 프로젝트의 예약 작업은 저장소를 고치지 않아"가 닫힌 현재형이다. 아침 보고는 토큰 보고서를 다시 만든다(`tools/morning_tasks/common.md`). → 명세 검토가 본 범위로 좁힌다.
5. Nit. 프로브 README가 대조 253~485ms를 아침 기록 189~454ms와 "비슷했다"고 쓴다. 하한이 약 34% 높다. → 수로 고친다.

냄새: `(attended, marker)` 쌍(Data Clumps 후보)은 `shows_summary` 와 같은 꼴이라는 저장소 표준이 이겨 내지 않았다. 두 사본의 복제는 대조 시험과 변이 2·3이 어긋남을 잡아 내지 않았다. 확인한 것: 시간 수치 전부, 명세의 `daily-morning-report` 주석, 예약 작업 트랜스크립트 `73e14cc2…` 의 첫 메시지 머리가 시험과 글자 그대로 같은 것, `AGENT_OS_HEADLESS` 이름 셋, 변이 표지의 고른 단언.

### 명세 축

1. Major. 티켓의 잔존 항목(저장소를 grep 해 이 훅을 지시문일 때만으로 든 살아 있는 자리를 고친다)이 덜 됐다. `.claude/skills/next-session/SKILL.md` 107줄의 "라벨을 바꾸면 훅은 예외 없이 침묵하고"가 이제 거짓이다(라벨을 바꾼 지시문은 사람이 보는 세션에서 티켓 알림을 받는다. 그 축이 함수를 불러 봤다). `.scratch/ticket-for-every-pr/spec.md` 25·217줄도 같은 말이다(Minor). → 스킬은 고친다. 명세 두 줄은 두는데, 명세는 to-spec·to-tickets 가 쓰는 문서이고(CLAUDE.md 지도 표) 그 두 줄은 이 기능이 출발한 상태를 "지금 … 넓힌다"로 적은 문장이라서다. 이 세션이 저장소를 다시 grep 해 `hook_prompt_directive`·"첫 턴 훅"이 든 살아 있는 문서(스킬 셋, ADR 0032·0036·0037 본문, `open_session.ps1`, `hook_pr_head_sync.py`, 프로브 README, 대기열의 열린 행, model-rerun 설계, token-usage 명세)를 한 줄씩 열었고, 지시문 전용이라 거짓이 된 줄은 그 하나였다. ADR 0037 15줄의 첫 턴 훅이 침묵한다는 문장은 결정 시점의 근거라 포인터를 달지 않는다(`.claude/rules/adr.md` 달지 않는 것).
2. Minor. 카나리아 명세 머리가 "일지 2026-10-22-20"을 드는데 그 일지에 검사 절이 없다. → 검사 절을 쓴다.
3. Minor(갈래). 면제 일을 주 체크아웃에서 시작하면, 알림이 면제를 "따르지 않는 때"에 넣어 주 체크아웃에서 `docs/<slug>` 를 따고 제목을 둘 수 있다. → 면제 일도 워크트리와 제목은 같다고 적는다.
4. Minor(갈래). 다른 티켓의 워크트리 폴더에서 연 세션이 다른 일을 받으면(이번 확인 세션이 그 길이었다) 2)가 남의 티켓 브랜치 이름을 바꾸게 한다. → 다른 티켓의 브랜치는 두고 사용자에게 알린다고 적는다.
5. Nit. 프로브 README의 "같은 프롬프트와 같은 사본이 … 셋째와 넷째 갈래의 침묵"이 셋째 갈래도 같은 사본이라고 읽힌다. 셋째는 원본이다. → 고친다.

확인한 것: 지시문 계기는 옛 모듈과 새 모듈의 출력이 같았다(지시문 셋으로 맞댔다). 알림의 차례와 따르지 않는 때 셋이 명세·ADR 0037·issue-tracker 와 맞다. 대조 시험은 한쪽만 바꿔도 빨갛다. 확인 세션의 트랜스크립트(`1f73e413…`)에 알림 문맥이 실렸다. 확인하지 못한 것: 빨강을 먼저 본 기록이 일지에 없다(아래 검사 절에 적는다), "통과 4"와 "대조군 '없음' 둘"의 맞춤(원본에서 대조군은 한 회차에 두 물음 모두 "없음"이었다. 명세 머리를 "두 물음 모두"로 고쳤다), 예약 작업 열 가운데 둘만 읽었다.

### 반영

- 고친 것(명세 1·2·3·4·5, 표준 1·2·3·4·5). 시험을 먼저 고쳐(낱말 목록에 `ready-for-agent`·"다른 티켓의 브랜치"·`` `retro` ``, 새 시험 `test_못_보는_것_슬래시_명령으로_연_세션에도_알린다`) 낱말 시험이 `ready-for-agent` 에서 빨간 것을 본 뒤 고쳤다. 새로 쓴 사실 문장(PR 직전 `bug-perf-review` 에 밀 주장으로 넘긴다):
  - `TICKET_NOTICE` 1): "받은 일의 티켓 파일이 이미 있으면 새로 쓰지 않고, 상태가 `ready-for-agent` 면 `in-progress` 로 바꾼다."
  - `TICKET_NOTICE` 2): "지금 브랜치가 이 일이 아닌 다른 티켓의 브랜치(위 모양의 다른 이름)면 그 티켓의 것이라 이름을 두고 사용자에게 알린다."
  - `TICKET_NOTICE` 면제: "면제 일(설계·명세·티켓 쓰기, 일지·대기열만 바꾸기)이면 1) 없이 `docs/<slug>` 브랜치로 하고, 워크트리와 제목은 위와 같다(그 PR 에서 회고가 고침을 반영할 때 쓰는 harness 티켓은 `retro` 가 정한다)."
  - 훅 독스트링: "그 검토가 본, 첫 메시지가 그 머리인 세션 여덟은 모두 저장소를 고치지 않는 일이었고(아침 보고는 `tools/morning_tasks/common.md` 가 "저장소의 파일을 고치거나 커밋하지 않는다"고 적는다), 알림이 할 일을 바꾸지 않는 세션에는 싣지 않는다."
  - 훅 독스트링 못 보는 것: "커밋하지 않는 스킬의 슬래시 명령(`/tidy-checkouts`)으로 연 세션도 첫 메시지가 지시문이 아니라 알린다. 첫 assistant 기록이 쓰이기 전에 둘째 프롬프트가 들어오면 그 프롬프트에도 알리는지는 보지 않았다(지시문 계기도 같다)."
  - `next-session` 107줄: "라벨을 바꾸면 훅이 지시문을 알아보지 못해, 사람이 보는 세션에는 이름을 붙이라는 계기 대신 지시문 없이 연 세션의 티켓 알림(티켓을 쓰고 브랜치를 바꾸라는 것)을 내고 `tests/tools/test_hook_prompt_directive.py`가 빨강이 된다." 함수를 불러 대 봤다(스크래치 스크립트): 라벨을 `갈래:` 로 바꾼 지시문과 `브랜치:` 가 빈 지시문은 사람이 보는 세션에서 티켓 알림, `CLAUDE_CODE_SESSION_ATTENDED=0` 과 표지 변수에서 없음, 원래 지시문은 셋 모두 지시문 계기였다.
  - 프로브 README: "보다 하한이 64ms, 상한이 31ms 높았다", "그 사본을 쓴 넷째 갈래의 침묵은 헤드리스 가름에서, 원본을 쓴 셋째 갈래의 침묵은 원본에만 있는 assistant 기록, 곧 첫 턴 판정에서 왔다", 표의 "뒤는 대조가 아침 기록보다 수십 ms 높았던 때". 프로브 독스트링의 "(실제 첫 턴의 트랜스크립트는 몇 줄이다)"를 "(실제 첫 턴의 트랜스크립트는 첫 assistant 기록 앞의 줄뿐이고, 그 줄 수를 결과에 찍는다)"로 고쳤다(README 의 34줄과 맞추려고 이 세션이 더 고쳤다).
- 남긴 것: 명세 25·217줄(위 명세 1의 까닭).
- 다시 돌린 것: 이 훅의 시험 49 통과, ruff 둘 초록, 변이 표 다섯의 `--check` 모두 원문 있음, 이 티켓의 변이 표 전체 8 모두 기대대로(커밋 전 판이라 도구가 "전체 실행은 커밋 뒤"라고 알렸다. 커밋과 PR 직전 리뷰 뒤에 한 번 더 돈다). 나머지 게이트는 커밋의 pre-commit 으로 갈음한다.
- `next-session` 을 고쳐 `sibling_overlap.py` 가 1로 끝났다(카나리아 명세를 고치지 않은 하네스 파일). 새 명세 `.scratch/harness/probes/canary/next_session_label_ticket_notice.toml` 을 쓰고 사전 확인 통과 뒤 돌렸다(아래 검사 절).

## 검사

- **빨강 먼저.** 구현 전에 이음매(옛 동작) 위에서 새 시험 여섯이 빨갰고, 구현 뒤 모두 초록이었다. 처음부터 초록이던 가드 시험(헤드리스 표지, 두 가름의 대조, 예약 작업 거르기, 트랜스크립트보다 먼저 거르기, 지시문 계기, 제목 문구)은 변이로 빨강을 보였다. 셀프 리뷰 반영에서도 낱말 시험이 `ready-for-agent` 에서 빨간 것을 본 뒤 고쳤다.
- **변이.** `.scratch/ticket-for-every-pr/probes/prompt_directive_mutations.toml` 여덟이 구현 뒤와 셀프 리뷰 반영 뒤 두 번 모두 표지까지 기대대로 빨갰다. 이 변경이 `main` 의 호출 모양을 바꿔 `.scratch/harness/probes/hooks_push_help_and_commit_lock_mutations.toml` 의 16번(행 72, `main` 이 작업 폴더를 넘기지 않는다)의 원문이 낡았고(`--check` 가 잡았다), 새 호출 모양으로 고쳐 그 하나를 돌려 기대대로 빨간 것을 봤다. 반영 뒤 이 훅을 겨누는 표 다섯의 `--check` 가 모두 원문을 찾았다.
- **실제 입력 표.** `uv run python tools/run_hooks.py` 153건, 어긋남 0(셀프 리뷰 전. 반영 뒤는 커밋의 pre-commit 이 돈다).
- **시간.** `.scratch/ticket-for-every-pr/probes/first_turn_time.py` 두 번(결과와 부하는 그 폴더 README 의 2026-10-22 결과 절), 값은 `.claude/rules/tools.md`.
- **카나리아 둘.** `tools_rule_prompt_directive_time.toml`: 통과 4(실험군 3/3이 두 범위를 옮겼고 대조군은 두 물음 모두 "없음", claude 2.1.302, `e62eb052` 위의 커밋 전 작업 트리. 셀프 리뷰 반영은 `.claude/rules/tools.md` 를 고치지 않았다). `next_session_label_ticket_notice.toml`: 통과 4(실험군 3/3이 새 문장을, 대조군 주 체크아웃 `c47bedce` 는 옛 문장 "예외 없이 침묵"을 옮겼다).
- **게이트.** 셀프 리뷰 전 `tools/run_checks.py` 모두 Passed. 반영 뒤는 첫 커밋의 pre-commit 이 모두 Passed 였다(pytest 401초, web-verify 322초, 훅 러너, pyright 둘, 타입 우회, 경계, 커밋 검사, 지침, zizmor, 표·줄 구분 문자·변이 표·카나리아 모양 검사. 헌법 판은 대상 파일이 없어 Skipped). 인용 대조가 경고 10건을 냈다. 둘(티켓 항목과 ADR 0037 문장을 글자가 다르게 옮긴 것)은 따옴표를 떼고 고쳤고, 나머지는 바뀌기 전 옛 문장이나 파이썬 문자열 이음으로 갈라진 새 문장을 옮긴 것이라 둔다.

## 인계 (커밋 뒤)

첫 커밋 뒤 인계 계기(`hook_handoff`)가 왔다. 세션 컨텍스트 335,245 토큰으로 문턱 200,000 을 넘은 채 `커밋 뒤` 경계였다. 인계하지 않는 때 다섯에 들지 않았다(커밋은 성공했다, 요청 범위는 PR과 병합까지다, 지시문의 이어받을 상태는 `없음` 이었다, `인계 못함` 줄이 없다, `get_session self` 에 `parentSessionId` 가 없다). 이 세션의 제목은 `feature/05-first-turn-ticket-notice` 이고 `feature/05-first-turn-ticket-notice (인계함)` 으로 바꾼다. 이 세션이 받은 사용자 프롬프트는 위 "구현"의 지시문과 두 선택 화면의 답이 전부다. 번복한 결정은 없고, 고친 것은 셀프 리뷰 반영 절이 전부다. 주 체크아웃은 `main` 이고 origin/main 과 같은 커밋이었다(`git worktree list`).

지시문:

```
다음 작업: .scratch/ticket-for-every-pr/issues/05-first-turn-ticket-notice.md. 첫 턴 훅이 티켓 없는 브랜치를 알린다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/ticket-for-every-pr/issues/05-first-turn-ticket-notice.md
브랜치: feature/05-first-turn-ticket-notice
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-22-20-first-turn-ticket-notice.md 전체(셀프 리뷰 반영 절의 새 문장이 PR 직전 리뷰에 밀 주장이다)
이어받을 상태: 인계: 커밋 뒤. 구현, 셀프 리뷰와 그 반영, 첫 커밋까지 했다(pre-commit 모두 Passed). 남은 단계는 차례로 이렇다. 일지의 인계 절(커밋하지 않았다)을 다음 커밋에 싣는다. 티켓의 체크박스를 표시하고 Status를 done으로 바꾼다. origin/main을 합친다. PR 직전 리뷰(docs/constitution/operations.md 리뷰 파이프라인 2)를 돌리고 반영한다. 반영을 커밋한 뒤 .scratch/ticket-for-every-pr/probes/prompt_directive_mutations.toml 전체를 다시 돌린다(변이 도구가 커밋 뒤의 전체 실행을 요구했다). 푸시, PR, 봇 회차, 워크트리 길의 병합, 일지 다음과 회고. 첫 푸시 뒤 확인 세션 "첫 턴 알림 확인 (티켓 05)"(local_bb679c5c-6fb3-48dd-b93e-3e4e3b45b94f)을 보관한다. 사용자가 "푸시 뒤에 보관 (추천)"을 골랐다(일지의 모델에게 닿는지 절). 일지 docs/journal/2026-10-22-20-first-turn-ticket-notice.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-22T13:16Z

## 인계받은 세션 (커밋 뒤부터)

> 사용자: (위 지시문을 첫 메시지로 받았다) ".claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. (…) 인자: .scratch/ticket-for-every-pr/issues/05-first-turn-ticket-notice.md / (…) 이어받을 상태: 인계: 커밋 뒤. (…) / 이번 요청 범위: PR과 병합까지"

- 제목을 `feature/05-first-turn-ticket-notice` 로 바꿨다. `git worktree list` 에서 그 브랜치가 `.claude/worktrees/05-first-turn-ticket-notice` 에 있어 `EnterWorktree(path)` 로 들어갔다(잠금에 막히지 않았다).
- 티켓의 체크박스를 모두 표시하고 상태를 `done` 으로 바꿔 위 인계 절과 한 커밋에 실었다. origin/main 은 그새 #351(`c47bedce`) 하나가 더 들어와 있었다.
