# 2026-10-22 (09) 규약 문서와 스킬이 "PR마다 티켓 하나"의 차례를 가르친다 (ticket-for-every-pr 02)

> 사용자: (next-session 지시문을 첫 메시지로 받았다) "다음 작업: .scratch/ticket-for-every-pr/issues/02-docs-and-skills-teach-tickets.md. 규약 문서와 스킬이 "PR마다 티켓 하나"의 차례를 가르친다 … 이번 요청 범위: PR과 병합까지"

## 체크아웃 정리

지시문의 "어디서"대로 제목을 `feature/02-docs-and-skills-teach-tickets`로 바꾸고 `tidy-checkouts`를 돌았다. 루트를 `98272c4f`에서 `caaa062b`(origin/main, #345의 병합)로 당겼다. `03-posix-launcher`를 쥔 쉬는 세션의 프로세스를 끄고 그 워크트리와 브랜치를 지웠고, 체크아웃되지 않은 `worktree-design-reverse-sync-tickets` 브랜치를 지웠다. 쥔 프로세스가 있는 넷, 병합된 PR이 없는 여덟, 앱의 표지가 있는 둘은 남겼다. 휴지통의 `node_modules` 아홉과 `.venv` 하나는 다른 체크아웃의 node·esbuild·python이 모듈을 올려 남았다. 그 뒤 `EnterWorktree`로 새 워크트리에 들어가 브랜치를 바꿨다.

## 구현

첫 편집으로 티켓 02의 `Status:`를 `in-progress`로 바꿨다. 스킬을 고치기 전에 `writing-for-agents`를 불렀다.

- 규약 원천. `docs/agents/issue-tracker.md` 규약 절에 PR마다 티켓 하나와 면제 둘, harness 티켓의 자리·세 자리 번호·서식, 기능 밖 제품 고침의 자리, 브랜치 이름이 stem이라는 것, 상태의 흐름, 병합된 티켓을 잇는 새 티켓을 더했다. 같은 파일의 전체 계획 절과 화면 디자인 절, `docs/constitution/operations.md`의 세 절(브랜치와 병합, 문서 위치의 기록 판정, 리뷰 파이프라인 1의 명세 축), 헌법 판 3.0.49, `CLAUDE.md` 지도 표, 루트 `README.md` 원천 표, PR 템플릿, 대기열 머리, `model_sweep` README의 "조건 변경(ADR 0037)" 문단을 고쳤다. 헌법 판은 번호 도구의 "형제가 쓴 가장 높은 헌법 판"(3.0.48)보다 높다.
- 스킬 다섯. `implement`(티켓 맞추기 문단), `next-session`(chore 배치 줄을 티켓 단위로, 3단계의 티켓 번호, 프론티어 줄, 지시문 형식), `code-review`(명세 출처의 셋째 항목), `retro`(회고 반영 줄, 티켓 경로로 닫기), `to-tickets`(stem이 구현 브랜치). 사본의 센티널 주석도 고쳤다.
- 고치지 않은 자리. `docs/model-selection.md`(티켓이 그렇게 정했다), `tools/morning_collect.py`와 그 테스트의 번호 없는 `chore/<slug>` 주석(지금도 참이다), `session_cost` README의 측정 분류, `KICKOFF.md`의 `chore/kickoff`, done 기능인 design-refresh의 티켓, `CLAUDE.md`와 `tools/morning_tasks/environment.md`의 "chore 브랜치"(지금도 참이다). `next-session`의 "하네스·문서만 고친 PR … 같은 주제가 남았다" 줄은 처음에 이 티켓의 범위 밖이라 두었는데, 명세 203행이 그 줄을 이름으로 들어 셀프 리뷰가 짚었고 고쳤다(아래 셀프 리뷰). 잔존 grep에서 옛 정의(`chore/<slug>`, `fix/<slug>`, "티켓 밖의 하네스/제품")를 든 살아 있는 문서는 0이었다.

## 검사 (셀프 리뷰 전)

카나리아. 바꾼 스킬 다섯마다 `.scratch/harness/probes/canary/`에 명세를 새로 썼다(`implement_ticket_status`, `next_session_chore_tickets`, `code_review_branch_ticket`, `retro_ticket_reflection`, `to_tickets_stem_branch`). 실험군은 이 워크트리, 대조군은 주 체크아웃(`caaa062b`)이다. 사전 확인 다섯이 통과했고, claude 2.1.302에서 다섯 모두 통과 4였다. `retro_ticket_reflection`의 첫 판은 통과 2·실패 2였다. 2번 질문이 취소선 문장의 "바로 다음 문장"을 물어, 실험군 두 회차가 새 문장을 건너뛰고 그 뒤의 문장을 옮겼다. 세 회차 모두 1번에 새 4단계 줄을 옮겨 새 사본은 실렸으므로, 닫힌 자리를 적는 법의 문장을 모두 옮기게 질문을 고쳐 다시 돌렸다. 기존 카나리아 서른의 사전 확인은 모두 막혔다. 대조군인 주 체크아웃이 그 명세를 들인 PR의 병합 뒤 새 사본이거나, `--control-commit`에 줄 옛 판 체크아웃이 없어서다. 지난 PR의 확인 기록이라 이 티켓에서 고칠 것이 아니다.

검증 명령. `uv run ruff check . && uv run ruff format --check .`가 통과했고, `uv run python tools/run_checks.py`의 검사 여덟(zizmor, check-instructions, lint-imports, check-type-escapes, pyright, run-hooks, web-verify, pytest)이 모두 통과했다.

## 셀프 리뷰

`/code-review`(base `caaa062b`, 고친 파일 14, 미추적 6, 커밋 0). Skill 도구가 실은 것은 주 체크아웃의 옛 사본이라 명세 출처의 셋째 항목이 없었지만, 티켓과 명세를 인자로 넘겨 같은 결과다. 표준 축은 Major 셋과 Minor 여섯, 명세 축은 Minor 넷과 Nit 셋이었다. 두 축이 같은 자리를 셋 짚었다(면제 PR의 회고 티켓 예외, `.scratch/harness/`의 기록 판정, chore 세션이 `implement`를 싣지 않는 것).

고친 것.
- `docs/agents/issue-tracker.md`. 면제 PR에서 회고가 harness 티켓을 쓰면 브랜치 이름과 맞대지 않고 `docs/<slug>` 그대로라는 예외를 PR마다 티켓 하나 항목과 stem 항목에 더했다(명세 166행 판정 6). 상태 항목의 부정형 문장을 "티켓은 그 일을 하는 PR에 함께 싣는다"로 바꿨다. `operations.md` 브랜치 절의 "티켓을 쓰지 않는 면제 PR"에서 "티켓을 쓰지 않는"을 뺐다.
- `docs/constitution/operations.md` 문서 위치. `.scratch/harness/`는 기능 디렉터리가 아니어서 폴더째 기록이 되지 않는다는 괄호를 더했다. 001이 done이라 하네스 기능의 기록 판정(티켓이 있고 모두 done)을 `.scratch/harness/`에 대면 같은 문단의 `.scratch/harness/probes/`와 어긋났다.
- `next-session` 87행. 병합된 PR의 남은 일을 이 세션에서 이을 때 다음 번호의 새 harness 티켓을 쓰고 새 브랜치를 딴다고 더했다(명세 203행).
- `next-session` chore 줄. 받는 세션은 `implement`를 싣지 않으므로 "읽을 것" 줄에 `docs/agents/issue-tracker.md`를 둔다고 더했다. 시작 프롬프트의 꼴은 명세 257행이 정해 두었다.
- `implement`. 티켓 없이 받은 일의 브랜치를 바꾸면 `set_session_title`로 세션 제목도 바꾼다고 더했다(사용자 스토리 25).
- `retro` 4단계. 회고 반영 줄을 종류별 목록("고침", "더하는 것")의 끝으로 옮기고 "어느 종류든"으로 열었다. 지금 PR이 이미 병합된 갈래(다음 번호의 새 harness 티켓과 새 브랜치)를 더하고, 번호 도구를 다시 치는 문장을 새로 쓰는 harness 티켓 모두에 걸리게 했다. 센티널 주석도 고쳤다.
- 대기열 머리의 닫힘 꼴에 retro와 같은 `. …`를 넣었다.
- retro 카나리아의 1번 질문을 옮긴 줄에 맞게 고쳤다.

남긴 것과 이유.
- chore 시작 프롬프트를 `/implement`로 바꾸는 것. 명세 257행이 꼴을 "명세가 정했다"로 고정했다. 대신 "읽을 것" 줄로 규약 문서를 가리켰다.
- `implement`의 "PR을 열기 전에 done" 문장을 끝 단계로 옮기는 것. 상태의 흐름을 한 문단에 모아 둔 것이고, PR의 티켓이 done인지는 CI(티켓 04)가 본다(명세 192행).
- 같은 뜻이 여러 문서에 있다는 지적(브랜치 이름, 다시 치기, 닫힘 꼴). 티켓이 스킬마다 그 문장을 요구했고, 각 자리가 `docs/agents/issue-tracker.md`를 원천으로 가리킨다. 대기열 머리의 "티켓은 행 번호만 가리키고"도 같다.
- `wontfix` harness 티켓의 기록 판정. 명세 285행이 처음 필요해지는 세션이 사람에게 묻는다고 미뤘다.
- `model_sweep` README 문단의 날짜가 효력이 서는 날이 아니라 넣은 날이라는 지적. 티켓이 "그 문단이 들어간 날"을 요구했다.
- 시작 프롬프트의 `<NNN>`과 티켓의 `NNN`. 스킬의 다른 자리 표시와 같은 꺾쇠 꼴이고 뜻이 같다.
- 루트 README 행, to-tickets의 slug 문장. 규약의 원천을 가리키는 포인터와 그 stem이 브랜치가 된다는 요구에서 바로 나오는 문장이라 둔다.

PR 직전 `bug-perf-review`에 밀 주장으로 넘길 새 문장(코드 리뷰 6단계 1).
- issue-tracker.md: "다만 그 PR에서 회고가 고침을 반영하면 harness 티켓 한 장을 같은 PR에 쓰고, 그 티켓은 브랜치 이름과 맞대지 않아 브랜치는 `docs/<slug>` 그대로다(`retro` 4단계, ADR 0037)", "예외는 위 면제 PR에 회고가 쓴 harness 티켓 하나다", "티켓은 그 일을 하는 PR에 함께 싣는다"
- operations.md: "`.scratch/harness/`는 기능 디렉터리가 아니어서 폴더째 기록이 되지 않고 티켓을 하나씩 본다"
- implement: "`set_session_title`에 `self`와 새 브랜치를 주어 세션 제목도 바꾼다. 형제 거르기와 체크아웃 정리가 제목으로 세션을 찾는다."
- next-session: "받는 세션은 `implement`를 싣지 않으므로 "읽을 것" 줄에 `docs/agents/issue-tracker.md`(harness 티켓의 서식·상태·번호)를 둔다.", "병합된 티켓은 다시 열지 않으므로 남은 일로 다음 번호의 새 harness 티켓을 쓰고 그 stem으로 새 브랜치를 딴다(`docs/agents/issue-tracker.md`)"
- retro: "지금 PR이 이미 병합됐으면 반영은 새 PR이라 다음 번호의 새 harness 티켓을 쓰고 그 stem으로 브랜치를 딴다."

다시 돌린 것. 카나리아 명세 다섯의 사전 확인이 통과했고, 질문을 고친 `retro_ticket_reflection`은 다시 돌려 통과 4였다. 나머지 넷은 질문이 가리키는 문장이 그대로라 사전 확인으로 갈음했다. 손으로 치는 검증 다섯은 이 커밋의 pre-commit 결과로 갈음한다.

## 인계 (커밋 뒤)

커밋 `19f11896`의 pre-commit은 모두 통과했다(ruff 둘은 `.py`가 없어 Skipped이고, 앞서 손으로 친 ruff 둘이 통과했다. 러너 검사 여덟, 마크다운 표, 줄 구분 문자, 변이 표, 카나리아 명세 모양, 헌법 판, 커밋 메시지). 인용 대조가 경고 둘을 냈다. `docs/constitution/README.md` 11행은 고친 판 줄에 원래 있던 이력의 인용이라 두었다. 이 일지의 경고는 내가 풀어 쓴 말에 따옴표를 붙인 것이라 따옴표를 떼었고, 그 고침은 커밋하지 않았다. 그 커밋 뒤 세션 컨텍스트가 29만 6천 토큰으로 인계 문턱을 넘어 `커밋 뒤` 경계에서 넘긴다. 곁 세션이 아니다(`get_session`에 `parentSessionId`가 없다). 이 세션의 지금 제목은 `feature/02-docs-and-skills-teach-tickets`다.

남은 단계. PR은 아직 열지 않았고 푸시도 하지 않았다. CodeRabbit CLI는 `Seat: not assigned`라 PR 직전 리뷰는 대체 둘이다. origin/main을 합친 뒤 `/security-review`를 돌리고, `bug-perf-review` 서브에이전트의 브리프에 위 셀프 리뷰 절의 "밀 주장으로 넘길 새 문장"을 나열한다. 그 뒤 티켓의 마지막 두 체크박스를 체크하고 `Status:`를 `done`으로 바꿔 커밋하고, `/git-pr`로 PR을 열고, `@coderabbitai review`를 남기고, `tools/wait_ci.py`를 띄운다. 봇 회차를 반영한 뒤 `next-session`의 "워크트리에서 병합할 때"대로 병합하고, 회고(`retro`)와 `next-session`을 돈다.

지시문(새 세션에 보낸 것).

```
다음 작업: .scratch/ticket-for-every-pr/issues/02-docs-and-skills-teach-tickets.md. 규약 문서와 스킬이 "PR마다 티켓 하나"의 차례를 가르친다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/ticket-for-every-pr/issues/02-docs-and-skills-teach-tickets.md
브랜치: feature/02-docs-and-skills-teach-tickets
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-22-09-docs-and-skills-teach-tickets.md의 "셀프 리뷰"와 "인계 (커밋 뒤)" 절
이어받을 상태: 인계: 커밋 뒤. 구현·카나리아·셀프 리뷰 반영을 커밋 19f11896까지 했고, 그 뒤 일지의 인용 따옴표를 뗀 고침 하나가 커밋되지 않았다. PR은 열지 않았고 푸시하지 않았다. 남은 것은 PR 직전 리뷰(CodeRabbit 좌석이 없어 origin/main을 합친 뒤 /security-review와 bug-perf-review, 밀 주장은 일지 셀프 리뷰 절의 목록), 티켓 done 커밋, /git-pr, 봇 회차, 병합, 회고다. 일지 docs/journal/2026-10-22-09-docs-and-skills-teach-tickets.md
확인할 선행 조건: 주 체크아웃(루트, main, caaa062b)의 작업 트리가 깨끗한지는 워크트리 가드가 git -C를 막아 보지 못했다
이번 요청 범위: PR과 병합까지
```

제목을 `feature/02-docs-and-skills-teach-tickets (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었으며, `git worktree unlock`으로 이 워크트리의 잠금을 풀었다.

open-session을 부른다 2026-10-22T08:08:11Z

## PR 직전 리뷰 (인계받은 세션)

> 사용자: (위 지시문을 첫 메시지로 받았다) "… 이번 요청 범위: PR과 병합까지"

제목을 브랜치 이름으로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. 커밋하지 않은 일지 고침을 `c1509de7`로 커밋했고(pre-commit 모두 통과), origin/main `b2f5c61d`(#346, model-rerun 설계)를 합쳤다. 그 PR이 고친 여섯 파일은 브랜치 규약을 건드리지 않았고, 새 `.scratch/model-rerun/design.md`가 든 "병합된 `feature/` 브랜치의 티켓"은 새 규약과 맞는다.

`/security-review`. 지적 없음. 서브태스크가 `tools/canary.py`가 새 카나리아 명세의 칸을 쓰는 길(인자 목록의 `subprocess.run`, 질문은 stdin, 경로는 읽기만)을 따라가 봤다.

`bug-perf-review`(기준 `b2f5c61d`, 파일 20, 호출 41). Critical·Major 없음, Minor 셋, 오탐 다섯. 밀 주장은 `implement`의 제목 문장 하나만 반만 맞았고 나머지는 근거와 맞았다.
- 고쳤다. `next-session` 결정표의 하네스 chore 배치 줄 "어디서" 칸이 "각자 워크트리"를 말해, 티켓이 하나이고 주 체크아웃이 깨끗할 때 3단계의 워크트리 문장 조건과 어긋났다. "티켓마다 새 세션. 둘 이상이면 2단계의 묶음"으로 줄였다. 묶음이면 3단계가 워크트리 문장을 넣는다.
- 고쳤다. `implement`의 "형제 거르기와 체크아웃 정리가 제목으로 세션을 찾는다". `tidy-checkouts` 판정 3은 실행 중 세션의 제목과 `branch`를 모두 받으므로, 제목만 보는 두 자리(`next-session` 2단계의 1, `operations.md` 브랜치와 병합의 워크트리 진입 전 확인)를 들었다. 터미널이라 도구가 없거나 앱이 거절하면 제목을 두고 잇는다는 갈래를 더했다(`next-session` "인계할 때" 4의 제목·데스크톱 앱 밖 항목과 같은 두 경우).
- 두었다. 기능 밖 제품 고침의 "다음 두 자리 번호"를 나란히 도는 두 세션이 같이 고르면 알리는 곳이 없다는 지적. 명세 212행이 "기능 폴더의 두 자리 티켓 번호는 보지 않는다"를 번호 도구의 못 보는 것으로 받아들였고, `tools/sibling_overlap.py` 독스트링도 같다. PR 체크리스트에 적는다.

다시 돌린 것. 바꾼 두 스킬의 카나리아 명세(`implement_ticket_status`, `next_session_chore_tickets`)는 `--preflight`가 통과했다. 같은 PR·같은 claude 판(2.1.302)이고, 원천 본문만 고쳤고, 명세의 칸은 그대로이며, 카나리아는 질문이 묻는 자리에 남아 갈음 조건 넷이 맞는다. 두 명세의 `# 최신 결과:` 줄 뒤에 갈음을 덧붙였다. 셀프 리뷰 뒤의 갈음도 그 줄에 빠져 있어 함께 적었다.

PR 봇에 밀 주장으로 넘길 새 문장.
- implement: "형제 거르기(`next-session` 2단계의 1)와 워크트리에 들어가기 전의 세션 확인(`docs/constitution/operations.md` 브랜치와 병합)이 제목만 보고 세션을 찾는다. 터미널이라 그 도구가 없거나 앱이 거절하면 제목은 그대로 두고 잇는다."

리뷰 반영과 티켓 done을 `3ceecb42`로 커밋했다(pre-commit 모두 통과, ruff 둘은 손으로 쳐 통과). 그 커밋 뒤 인계 계기(`커밋 뒤`, 22만 6천 토큰)가 왔지만, 이 세션의 지시문이 `인계: 커밋 뒤`로 시작해 같은 경계라 넘기지 않았다(`next-session` "인계할 때" 1).

## 인계 (PR 연 뒤)

`coderabbit auth status`는 이번에도 `Seat: not assigned`였다. base가 움직이지 않아 푸시하고 `/git-pr`로 PR #348을 열었다. 확인 방법에 넣은 `--preflight --control-commit caaa062b` 명령은 열기 전에 쳐서 다섯 모두 통과를 봤다. 앱이 PR을 이 세션에 묶었다. 그 직후 인계 계기(`PR 연 뒤`, 25만 1천 토큰)가 왔고, 넘겨받은 경계(`커밋 뒤`)와 달라 넘긴다. 곁 세션이 아니다(`get_session`에 `parentSessionId`가 없다). 이 세션의 지금 제목은 `feature/02-docs-and-skills-teach-tickets`다.

남은 단계. 첫 `@coderabbitai review` 코멘트와 `tools/wait_ci.py`는 새 세션이 한다. 그 뒤 봇 회차를 반영하고 `next-session`의 "워크트리에서 병합할 때"대로 병합한 뒤 회고(`retro`)와 `next-session`을 돈다. 병합 직전에 `tools/sibling_overlap.py`가 일지 번호가 이 브랜치(09)보다 큰 형제(PR #347의 10, `choice-facts-batch`의 11 등)를 찍었다. 그쪽이 먼저 병합되면 이 일지 번호를 옮긴다. 이 인계 절은 커밋하지 않았다.

지시문(새 세션에 보낸 것).

```
다음 작업: .scratch/ticket-for-every-pr/issues/02-docs-and-skills-teach-tickets.md. 규약 문서와 스킬이 "PR마다 티켓 하나"의 차례를 가르친다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/ticket-for-every-pr/issues/02-docs-and-skills-teach-tickets.md
브랜치: feature/02-docs-and-skills-teach-tickets
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-22-09-docs-and-skills-teach-tickets.md의 "PR 직전 리뷰 (인계받은 세션)"과 "인계 (PR 연 뒤)" 절, PR #348 본문
이어받을 상태: 인계: PR 연 뒤. PR #348을 열고 푸시했다. PR 직전 리뷰(/security-review 지적 없음, bug-perf-review 유효 Minor 셋 가운데 둘을 고치고 하나는 명세 212행대로 둠)는 반영해 PR 체크리스트에 적었다. 첫 @coderabbitai review 코멘트와 tools/wait_ci.py 대기는 아직이다. 남은 것은 next-session 순서 1의 2(봇 회차)부터 병합까지와 회고, 그리고 커밋하지 않은 일지의 인계 절을 이어 쓰고 커밋하는 것이다. 병합 직전에 sibling_overlap.py를 다시 쳐 일지 번호가 더 큰 형제가 먼저 병합됐으면 이 일지 번호를 옮긴다. 일지 docs/journal/2026-10-22-09-docs-and-skills-teach-tickets.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `feature/02-docs-and-skills-teach-tickets (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었으며(리뷰 서브에이전트 둘은 끝났다), `git worktree unlock`은 `is not locked`라 넘어갔다.

open-session을 부른다 2026-10-22T08:38:09Z

## 봇 회차 (두 번째로 인계받은 세션)

> 사용자: (위 지시문을 첫 메시지로 받았다) "… 이번 요청 범위: PR과 병합까지"

제목을 브랜치 이름으로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다. `@coderabbitai review`를 남기고 `tools/wait_ci.py 348`을 백그라운드로 띄웠다.

claude-review 첫 회차(`3ceecb42`). 지적 없음. 잡 로그의 `rate_limit_info`가 `seven_day` 사용률 0.97(`allowed_warning`)을 보였다. 다음 푸시의 리뷰는 계정 한도에 걸릴 수 있다.

CodeRabbit 첫 회차(`3ceecb42`, `Review completed`). Minor 하나. `docs/agents/issue-tracker.md` 7~16행에 대해, 기능 폴더마다 번호가 `01`부터 다시 시작하니 서로 다른 기능의 티켓이 같은 stem(`01-login`)을 지으면 같은 브랜치 이름을 요구한다며, stem을 기능 폴더 전체에서 유일하게 하고 만들기 전에 겹침을 거부하라고 했다. 보류했다. 지금 기능 티켓 81개의 파일 이름에 겹치는 것이 없고(`ls .scratch/*/issues/[0-9][0-9]-*.md`를 이름만 남겨 `uniq -d`), 새 지침 문장과 검사는 세 번째나 손상 한 번에서 더하며(`CLAUDE.md` 교정 루프), 만들기 전 거부 검사는 새 도구라 이 티켓의 범위 밖이다(명세 212행이 번호 도구는 기능 폴더의 두 자리 번호를 보지 않는다고 정했다). 이유는 그 스레드의 답글로 남겼다. 고친 것이 없는 회차다.

## 회고

티켓 02 단계(세 세션) 전체를 이 일지와 이 세션으로 봤다. 이 PR이 `retro`를 고쳐, Skill 도구가 실을 주 체크아웃의 옛 사본 대신 워크트리의 `SKILL.md`를 Read로 열어 따랐다. 후보 여덟, 모두 기각이다. 만료할 행은 없었다(`tools/queue_open_rows.py`, `--ref origin/main`도 같다).

1. **기능 폴더 사이의 stem 겹침**(CodeRabbit 첫 회차 Minor). 기각이다. 사건 없이 떠올린 것이다(위 "봇 회차").
2. **`retro_ticket_reflection` 카나리아의 첫 질문이 "바로 다음 문장"을 물어 실험군 둘이 다른 문장을 옮겼다.** 기각이다. 카나리아 자체가 그 자리에서 실패로 알렸고, 질문을 고쳐 다시 돌렸다. 명세마다의 질문 문구를 일반 검사로 옮길 길이 없다.
3. **기존 카나리아 서른의 사전 확인이 모두 막혔다.** 기각이다. 프로브 README의 `canary/` 행이 병합 뒤에는 그대로 돌지 않는 명세가 있다고 이미 적었고, 다시 돌릴 때는 옛 판의 커밋을 `--control-commit`으로 준다. 이 티켓이 그 서른을 다시 돌릴 까닭은 없었다.
4. **`next-session` 87행을 범위 밖이라 두었는데 명세 203행이 이름으로 들었다**(셀프 리뷰 명세 축). 기각이다. 리뷰가 잡도록 둔 기준(명세 축)을 리뷰가 잡아 제 몫을 했고, 검사로 옮길 수도 새 판단 기준도 아니다.
5. **PR 직전 `bug-perf-review`의 유효 Minor 둘**(chore 줄의 "각자 워크트리", `implement`의 제목 문장). 기각이다. 4와 같다.
6. **복합 git 명령(`grep … ; git fetch -q; for … git show`)을 워크트리 가드가 거부했다.** 기각이다. 앱 가드가 그 자리에서 막았고 `CLAUDE.md` 환경 함정이 이미 하나씩 치라고 한다.
7. **Skill 도구가 `code-review`와 `retro`의 옛 사본을 실었다.** 기각이다. `CLAUDE.md` 환경 함정대로 인자로 넘기거나 Read로 열어 따랐고 잃은 것이 없다.
8. **claude-review 계정의 주간 사용률이 0.97이었다.** 기각이다. 실수가 아니라 정보이고, 한도로 빨개지면 `tools/wait_ci.py`와 리뷰 파이프라인 3이 이미 가른다.

## 다음

- **다음 티켓은 03(`03-commit-check-blocks-ticketless.md`)이다.** 이 PR이 병합되면 막힌 것이 없어지고(01·02 done), 04는 03에, 05는 02·03에 막힌다.
- **03의 커밋 검사가 브랜치로 티켓을 찾을 때.** 위 CodeRabbit 보류대로 기능 폴더 사이의 stem 겹침은 지금 0건이다. 겹침이 생기면 브랜치 하나에 티켓 파일 둘이 맞는다. 03의 판정이 그 경우를 어떻게 다룰지는 03의 티켓과 명세가 정한다.
- 주 체크아웃 미갱신: 루트는 main. 병합된 이 워크트리와 브랜치는 다음 주 체크아웃 세션의 `tidy-checkouts`가 지운다.

## 인계 (봇 회차 일지 커밋 뒤)

봇 첫 회차의 판정, 회고, "다음"을 `00e7a6ce`로 커밋했다(pre-commit 모두 통과. ruff 둘, 카나리아 명세 모양, 헌법 판은 대상 파일이 없어 Skipped). 그 직후 인계 계기(`커밋 뒤`, 22만 5천 토큰)가 왔다. 이 세션의 지시문의 "이어받을 상태"는 `인계: PR 연 뒤`라 같은 경계가 아니고, 곁 세션이 아니다(`get_session`에 `parentSessionId`가 없다). 이 세션의 지금 제목은 `feature/02-docs-and-skills-teach-tickets`다.

남은 단계. `00e7a6ce`는 푸시하지 않았다. 새 세션은 이 인계 절을 이어 쓰고 커밋한 뒤 함께 푸시하고, `@coderabbitai review`를 남기고 `tools/wait_ci.py`를 띄운다. 이 푸시의 리뷰는 두 봇 모두 둘째 회차라 Critical·Major만 고친다. claude-review는 계정의 주간 사용률이 0.97이라 계정 한도로 빨개질 수 있고, CodeRabbit은 08:47 UTC의 리뷰가 시간당 포함 리뷰를 다 썼다고 적어 그 뒤 한 시간 안에는 한도에 걸릴 수 있다. 초록이면 병합 직전에 `tools/sibling_overlap.py`를 다시 쳐 일지 번호를 보고(이름순으로 앞서는 형제는 PR #347의 10, `choice-facts-batch`의 11), `next-session`의 "워크트리에서 병합할 때"대로 병합한 뒤 `next-session`을 돈다. 다음 티켓은 위 "다음"대로 03이다.

지시문(새 세션에 보낸 것).

```
다음 작업: .scratch/ticket-for-every-pr/issues/02-docs-and-skills-teach-tickets.md. 규약 문서와 스킬이 "PR마다 티켓 하나"의 차례를 가르친다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/ticket-for-every-pr/issues/02-docs-and-skills-teach-tickets.md
브랜치: feature/02-docs-and-skills-teach-tickets
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-22-09-docs-and-skills-teach-tickets.md의 "봇 회차 (두 번째로 인계받은 세션)", "다음", "인계 (봇 회차 일지 커밋 뒤)" 절
이어받을 상태: 인계: 커밋 뒤. 봇 첫 회차(claude-review 지적 없음, CodeRabbit Minor 하나는 사건 0건이라 보류하고 스레드에 답글)와 회고(후보 여덟 모두 기각), "다음"을 일지에 적어 00e7a6ce로 커밋했고 푸시하지 않았다. 남은 것은 일지의 인계 절을 이어 써 커밋하고 함께 푸시한 뒤 next-session 순서 1의 2(봇 회차, 두 봇 모두 둘째 회차라 Critical·Major만)부터 병합까지, 그리고 next-session이다. claude-review는 계정 주간 사용률 0.97이라 한도로 빨개질 수 있다. 병합 직전에 sibling_overlap.py를 다시 쳐 일지 번호가 더 큰 형제가 먼저 병합됐으면 이 일지 번호를 옮긴다. 일지 docs/journal/2026-10-22-09-docs-and-skills-teach-tickets.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 `feature/02-docs-and-skills-teach-tickets (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었으며(`tools/wait_ci.py` 대기는 끝났다), `git worktree unlock`은 `is not locked`라 넘어갔다.

open-session을 부른다 2026-10-22T08:57:33Z

## 봇 둘째 회차와 병합 (세 번째로 인계받은 세션)

> 사용자: (위 지시문을 첫 메시지로 받았다) "… 이번 요청 범위: PR과 병합까지"

제목을 브랜치 이름으로 바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다(잠금 거부 없음). PR #348은 `OPEN`, `CLEAN`이고 헤드는 `3ceecb42`다. `tools/sibling_overlap.py`는 번호 겹침이 없다고 했고 origin/main은 `b2f5c61d` 그대로다. 일지 번호가 이름순으로 앞서는 형제는 여전히 PR #347의 10, `choice-facts-batch`와 `design-reverse-sync-tickets` 워크트리의 11과 10이다.

앞 세션이 쓰고 커밋하지 않은 인계 절과 이 절을 함께 커밋해 `00e7a6ce`와 같이 푸시한다. 고친 것이 없는 회차의 일지 푸시라, 이 푸시로 도는 리뷰는 두 봇 모두 둘째 회차로 세어 Critical·Major만 고친다. 그 리뷰에서 보류하는 지적과 병합 결과는 일지를 다시 푸시하지 않고 PR 코멘트와 다음 지시문에 적는다(`next-session` 순서 1의 2 "뒤로 넘긴 일").
