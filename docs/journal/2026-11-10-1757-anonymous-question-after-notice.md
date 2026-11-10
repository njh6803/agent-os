# 2026-11-10 (17:57) 처음 온 최종 사용자가 고지 덮개에서 확인한 뒤 익명으로 질문한다 (pilot-portal 07)

세션 제목 `feature/07-anonymous-question-after-notice`. 브랜치 같은 이름, 워크트리 `.claude/worktrees/07-anonymous-question-after-notice`. 모델 Sonnet 5.5 / high(지시문).

## 사용자 프롬프트

> .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/pilot-portal/issues/07-anonymous-question-after-notice.md
>
> 다음 작업: .scratch/pilot-portal/issues/07-anonymous-question-after-notice.md. 처음 온 최종 사용자가 고지 덮개에서 확인한 뒤 익명으로 질문한다
> 다음 단계: 구현
> 이번 요청 범위: PR과 병합까지

이 세션에서 사용자가 더한 말은 없었다. 지시문이 덧붙인 이월 몫은 둘이었다. 하나는 07의 e2e가 `browser/portal.ts`와 `server/paths.ts`의 끝점 경로 글자가 어긋나면 빨개져야 한다는 것이고, 다른 하나는 이 기능의 마지막 티켓 뒤에 `e2e-widget`·`e2e-portal`을 `.scratch/harness/probes/ci_job_durations.py`의 `JOBS`에 더하고 `ci.yml`의 `timeout-minutes`를 잰 값으로 고치는 일이다(07의 몫이 아니다).

## 한 일

- 페이지 마크업(`server/page.ts`): 위젯 자리 `#pp-widget`(`tabindex="-1"`) 안에 뼈대, 덮개(`<section aria-labelledby>`), 위젯 요소를 숨긴 채 낸다. 위젯 아래에 짧은 고지와 "고지 전문" 단추. 아이콘 셋(`loader-circle`, `info`, `circle-x`)은 Lucide 모양의 인라인 SVG다. 사이트별 고지 글은 데이터 블록에만 싣는다.
- 페이지 스크립트(`browser/portal.ts`): 사이트를 고를 때마다 상태 끝점에 묻고 0.3초를 넘기면 뼈대, 미확인이면 덮개, 확인했으면 위젯과 짧은 고지를 보인다. 확인 단추는 `aria-busy` 동안 두 번째 누름을 무시하고, 204면 덮개를 걷고 포커스를 `#pp-widget`으로 옮기며, 실패하면 `role="alert"`를 보인다. "고지 전문" 단추는 `aria-expanded`와 전문 펼침을 바꾼다.
- 페이지 CSS(`browser/portal.css`): 뼈대, 덮개, 알림, 주 버튼(도는 표시는 `prefers-reduced-motion`에서 멈춘다), 짧은 고지, 끝에 `[hidden]{display:none !important}`.
- e2e: `e2e/acknowledge.e2e.ts` 열네 사례(티켓의 열 사례 + 뼈대, 전문 펼침, 실패 알림과 재시도, 두 번째 누름 무시). `e2e/sites.ts`의 첫 사이트가 직접 적은 `notice`를 갖고 `e2e/stack.ts`가 그것을 설정에 쓴다.
- `server/page.test.ts`: 새 마크업 시험 아홉.
- 변이 표 `.scratch/pilot-portal/probes/acknowledge_mutations.toml` 14개와 프로브 README 줄.
- 티켓 07을 done으로 하고 `plan_table.py`를 돌렸다(08·09가 이 티켓에 막혀 있어 기능의 `**끝:**` 줄은 쓰지 않는다).

## 결정

- **상태를 묻다 실패하면 덮개를 보인다.** 티켓과 명세가 이 모습을 정하지 않았다. 확인하지 않은 것으로 읽는 쪽이 안전하다(확인 없이 위젯이 열리지 않는다). 로그인 사이트의 모습은 08이 그린다. 이 갈래는 e2e 사례도 변이도 없다.
- **"Tab 한 번에 입력창"은 실제 위젯과 맞지 않았다.** 확인 뒤 포커스가 `#pp-widget`에 있을 때 첫 Tab은 위젯 머리의 "새 대화" 단추가 받고 입력창은 둘째 Tab이다(스크래치패드의 임시 e2e `zz-debug`로 포커스 사슬을 찍어 보았다. 커밋하지 않고 지웠다). e2e의 `tabToField`가 이 차례를 고정한다. 티켓 29행과 명세 223행에 그렇게 고쳐 적었다.
- **`[hidden]{display:none !important}`.** `.pp-widget > *`의 `display:block`과 위젯 요소의 `:host` `display`가 `hidden` 속성을 이기는 것을 e2e 첫 판이 보여 주었다. 끝에 두고 `!important`로 이긴다.
- **덮개와 확인 단추의 포커스.** 덮개는 나타날 때 포커스를 옮기지 않는다(`document.activeElement`가 `body`). 확인이 기록되면 `#pp-widget`으로 옮기고 위젯 요소(호스트)에는 `tabindex`를 두지 않는다. 호스트에 `tabindex`를 달면 Tab 으로 입력창에 닿지 못해 e2e가 빨개진다(변이 8).
- **e2e 보강.** 티켓의 열 사례에 없던 뼈대, 전문 펼침, 실패 알림과 재시도, 두 번째 누름 무시를 e2e로 더했다. 확인 흐름의 체크박스가 요구하는 동작인데 서버 마크업 시험만으로는 브라우저에서 켜고 끄는 일을 볼 수 없어서다.
- **끝점 경로 어긋남.** 이월 몫대로 변이 2·3·4가 페이지 스크립트 쪽과 서버 쪽 경로를 각각 틀리게 해 e2e가 빨개지는 것을 보인다.

## 확인한 것

- **빨강 먼저.** 마크업 시험은 구현 전에 9건이 빨갰다. e2e 사례는 구현과 함께 써서 처음부터 초록이었으므로 변이 표 14개로 그 표가 겨눈 판정마다 빨강을 봤다(표가 겨누지 않은 사례는 아래 셀프 리뷰 절). 첫 판은 표지를 자리표시자로 두고 돌려 실제 실패 출력을 모았고(14개 모두 빨강), 표지를 고른 뒤 한 번 더 돌려 `변이 14 모두 기대대로`였다. 소스는 변이 뒤 원상으로 돌아왔다(`git status`로 보았다).
- 변이 4의 첫 표지는 `waitForResponse` 시간 초과 문구라 어느 대기에서도 같았다. 같은 출처 확인의 응답 대기를 `startsWith`로 넓혀 404가 값(`Received: 404`)으로 드러나게 고치고 그것을 표지로 골랐다.
- 변이 표가 보이지 못하는 것: 위젯 요소의 `tabindex` 속성이 없다는 단언은 Tab 으로 입력창에 닿는 단언이 먼저 빨개져 따로 빨강을 보이지 못한다. 상태를 묻다 실패한 모습과 늦은 답을 가리는 세대 번호는 사례가 없다.
- 질문 페이지 e2e는 18건 초록이었다(`18 passed`, 변이 표를 만들기 전. 그 뒤 사례 하나의 대기 조건과 `toBeVisible` 한 줄을 더했다).
- `uv run ruff check .`와 `ruff format --check .`는 통과했다.
- 전체 검사 `uv run python tools/run_checks.py`의 첫 판은 `web-verify`만 빨갰다(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright 둘, run-hooks, pytest 530.8초는 통과했다. 출력을 읽었다). 빨강 둘을 고쳤다.
  - eslint `no-restricted-syntax`(불리언 매개변수 금지): `setBusy(parts, busy: boolean)`을 `markBusy`와 `clearBusy`로 쪼갰다.
  - `apps/portal/tools/start.spawn.test.ts`가 옛 마크업 `<agent-os-widget>`를 기대했다. 위젯 요소가 `hidden`을 달게 되어 `<agent-os-widget hidden>`으로 고쳤다. prettier는 `acknowledge.e2e.ts`와 `page.test.ts`를 고쳤다.
- 고친 뒤: `pnpm -C web exec vitest run --project node apps/portal`이 파일 15개 모두 통과(207 통과, 1 건너뜀)였고 질문 페이지 e2e가 18건 초록이었다. 고친 뒤의 `pnpm -C web verify` 전체와 `uv run python tools/run_checks.py`는 다시 돌지 않았다. 커밋의 pre-commit이 갈음하되, 셀프 리뷰를 반영하며 코드를 더 고치면 그 뒤 한 번 더 돌린다.

## 셀프 리뷰 (2차 세션)

범위: base `2a61330e`(= HEAD), 추적 파일 11개 변경, 미추적 3개, 커밋 0개. 표준 축(sonnet·high)과 명세 축을 병렬로 돌렸다. 두 축 모두 Critical·Major는 없었다. 첫 세션이 `/code-review`를 밟지 못하고 인계한 몫이다.

고친 것:
- **세대 번호 걷어냄.** `browser/portal.ts`의 `generation`과 `mine === generation` 검사는 사이트를 다시 고르는 길이 없는 07에서 닿지 않고 시험도 없다(표준 축 Speculative Generality, 명세 축 범위 넘침 경미). 티켓의 "체크박스가 요구하는 것만" 규약대로 걷고, 08 티켓에 늦은 답을 가리는 번호와 그 e2e 사례를 새 체크박스로 넘겼다. 이 때문에 변이 9번의 편집 대상 문자열을 새 코드에 맞췄다. 변이 14번은 첫 세션이 `setBusy`를 쪼갠 뒤 들여쓰기가 어긋나 있던 것을 `--check`가 잡아 맞췄다. 두 변이를 새 코드에서 다시 돌려 기대대로 빨강이었다.
- **경로 어긋남 주석.** `server/paths.ts`와 `browser/portal.ts`의 머리 주석이 "질문에 답이 서지 않아 빨개진다"로 모든 끝점에 일반화했는데, 그것은 토큰 끝점에만 맞다(확인 경로는 404와 위험 알림, 상태 경로는 덮개만 보인다). "e2e가 빨개진다"로 줄이고 토큰 끝점의 증상만 따로 적었다.
- **`[hidden]` CSS 주석.** 이유에서 위젯 요소의 `:host`를 뺐다. 위젯은 이미 `:host([hidden]) { display: none; }`을 갖고 있고 문서 규칙이 `:host`를 이기므로(`web/apps/widget/element/styles.ts` 5행의 주석과 19행. 코드를 읽었고 브라우저에서 계산된 스타일을 찍어 보지는 않았다), 이기는 상대는 `.pp-widget > *`와 면마다의 `display` 지정이다.
- **옛 미래형.** `e2e/other-page.ts` 머리의 "이 티켓은 페이지만 세운다"는 06 시점의 문장이라 지웠다.
- **"단언마다 빨강" 과장.** 변이 표의 `-g` 대상에 없는 사례(사이트 고지 글이 전문이 되는 것, 새로 고침, 쿠키 삭제, 시간당 상한, 출력의 쿠키·토큰 부재, 확인 사례의 트레이스 주체 해시와 쿠키 원문 부재)는 빨강을 보지 못했다. 프로브 `README.md` 줄과 변이 표 머리에 그렇게 적었고, 위 "확인한 것"의 서술을 "표가 겨눈 판정마다"로 줄였다. README에서 근거 없는 "한 바퀴가 몇 분"도 뺐다.
- **티켓 "빨강을 먼저 본다" 체크.** "e2e 사례가 구현 전에 빨갛다"는 사실이 아니라서(구현 전에 빨간 것은 마크업 시험 9건) 문구를 사실대로 고쳤다.

남긴 것:
- `portal.ts` 머리의 "고를 때마다"는 "고른 사이트의"로 줄여 고쳤다(Nit이 맞았다).
- `Parts`와 `findParts`의 `byId` 되풀이(Data Clumps, Nit)와 CSS `padding-left:22px`·`margin-top:1px`의 근거 주석 없음(Nit): 지금 규모에서 허용 범위라 두었다.
- 상태를 묻다 실패했을 때 덮개를 보이는 결정은 위 "결정"에 적었고 e2e 사례가 없다. 08이 로그인 사이트 모습을 그리며 이 갈래를 함께 본다.

다시 돌린 명령(반영 뒤, 이 세션에서 출력을 읽었다):
- `uv run ruff check .`와 `ruff format --check .`: 통과.
- `uv run python tools/run_checks.py`: 종료 코드 0. check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright 둘, run-hooks, pytest(436.0초), web-verify(520.7초) 모두 `Passed`.
- `pnpm -C web/apps/portal exec playwright test`: `18 passed`.
- 변이 `--check`: 14개 모두 원문이 한 번씩 있다. 변이 9·14를 새 코드에서 돌려 기대대로 빨강.
- 티켓의 셋째 검증 체크는 위 결과를 보고 체크했고 `plan_table.py`를 돌렸다. 질문 페이지 e2e 말고 사진 비교, 위젯·관리 화면 e2e는 이 변경이 건드리지 않아 돌지 않았다(CI가 돈다).

## 이 세션의 제목

`feature/07-anonymous-question-after-notice` (인계 때 `(인계함)`을 붙였다)

## 인계

컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 셀프 리뷰 직전에 와서 `인계: 셀프 리뷰 직전`으로 넘겼다. 이 세션은 `/code-review`를 밟지 않았다. 지시문은 스크래치패드 `directive-07.txt`에 있고 새 세션의 첫 메시지가 된다. 잠금은 풀었다.

open-session을 부른다 2026-11-10T09:11:31Z

## 인계 (둘째 세션)

둘째 세션은 셀프 리뷰를 밟고(위 "셀프 리뷰 (2차 세션)") 반영한 뒤 `uv run python tools/run_checks.py`와 질문 페이지 e2e 18건이 초록인 것을 보고 커밋했다(`9e1b70d2`, pre-commit 통과). 컨텍스트가 인계 문턱을 넘은 채 `커밋 뒤`에 와서 `인계: 커밋 뒤`로 넘긴다. 남은 단계는 푸시, PR, 봇 회차와 CI, 병합, 이 일지의 "다음"과 retro, 다음 지시문이다. 이 세션의 제목은 `feature/07-anonymous-question-after-notice` (인계 때 `(인계함)`을 붙인다). 이월 몫은 첫 인계 때와 같다. 이 기능의 마지막 티켓 뒤에 `e2e-widget`·`e2e-portal`을 `.scratch/harness/probes/ci_job_durations.py`의 `JOBS`에 더하고 `ci.yml`의 `timeout-minutes`를 잰 값으로 고치는 일이고 07의 몫이 아니다. 08·09가 남아 있어 기능 계획의 `**끝:**` 줄은 쓰지 않는다.

open-session을 부른다 2026-11-10T09:46:30Z

## PR 직전 리뷰 (셋째 세션)

셋째 세션은 워크트리에 들어와 `origin/main`(3dc3f15e, 문서만 바뀜)을 합치고(겹친 파일 없음, `plan_table.py`가 만든 `.scratch/plan.md`에 차이 없음) PR 직전에 `coderabbit-review` 서브에이전트를 돌렸다.

- 아래 CLI 수치는 서브에이전트의 보고에서 옮긴 것이고 이 세션이 CLI를 직접 돌리지 않았다. 명령은 `coderabbit review --agent --include-untracked --base origin/main`이고 종료 코드 0, 끝 줄이 `review_completed`에 `findings` 0이었다고 보고했다. `Seat: not assigned`(Plan: Free)였지만 리뷰는 정상으로 돌았다.
- 리뷰한 파일은 16개(질문 페이지 코드와 시험 10, 문서 6)이다. 지적은 없었다.
- 서브에이전트가 CLI와 별개로 `server/page.ts`, `browser/portal.ts`, `server/paths.ts`의 diff를 읽었다(CSS는 훑기만 했다). 고지 글이 `textContent`로만 들어가고 데이터 블록이 이스케이프되어 XSS 경로가 보이지 않았고, 눈에 띄는 버그와 성능 문제도 없었다. 이 부분은 CLI 결과가 아니라 서브에이전트가 읽은 판단이다.

## PR

PR 518(`gh pr create`의 출력으로 번호를 읽었다). 헤드 `b4f2d83e`에서 아홉 검사가 모두 통과였다(`tools/wait_ci.py 518`의 끝 줄 `끝: 모두 통과. CodeRabbit: Finished`를 읽었다).

## 봇 회차 (첫 회차)

- CodeRabbit: PR 코멘트에 `No actionable comments were generated in the recent review.`가 있다(코멘트를 읽었다). 지적 0건이다.
- claude-review(PR 코멘트를 읽었다): Critical·Major 없음, Minor 셋과 Nit 하나. 첫 회차라 지적마다 판단했다.
  - **Minor `portal.ts:103` 끝점 모양 사본.** 역방향 주석(`paths.ts` 쪽에 "브라우저 스크립트에 사본이 있다")을 권했는데 `server/paths.ts`의 머리 주석이 이미 그것과 "그 경로를 바꿀 때는 `browser/portal.ts`도 같이 고친다"를 적고 있다(파일 1~5행을 읽었다). 반영할 것이 없다.
  - **Minor `portal.ts:263` 늦게 온 답.** 리뷰가 08 티켓에 체크박스가 있는지만 확인하면 된다고 했고, 있다(`git diff origin/main...HEAD`로 08 티켓에 더한 줄을 보았다). 반영할 것이 없다.
  - **Minor 상태 묻기 실패 갈래의 e2e 부재.** 일지 "결정"에는 있었으나 08 티켓에는 체크박스가 없어, 이 회차에 08 티켓에 체크박스 하나를 더했다(뒤로 넘긴 일을 놓치지 않게 하려는 것이다).
  - **Nit `portal.ts:141` 실패를 `false`로 접는 모양.** 리뷰가 지금은 값을 한다고 했고 고치지 않는다.

## 회고

후보 둘을 냈고, 승인 0, 기각 2, 넘김 0이다. 근거는 이 세션에서 본 것에 한한다.

- **기각: 문서만 바꾼 일지 커밋의 pre-commit이 길다.** 일지 한 줄을 고친 커밋이 Bash 도구의 5분 시간 제한에 닿아 백그라운드로 넘어갔다(첫 커밋 `5ac2907f`. 알림이 올 때까지 기다렸다). 원인을 재지 않았다. 4단계의 승인 조건(사건, 층, 되돌림) 가운데 사건의 원인을 대지 못해 기각한다. 다시 겪으면 어떤 훅이 얼마를 쓰는지 재서 올린다.
- **기각: 사용자 수준 `git-pr` 스킬의 "생성 전 확인" 단계와 지시문의 "PR과 병합까지"가 갈린다.** 이 세션은 지시문의 범위를 승인으로 읽고 확인 없이 열었다. 그 스킬은 사용자 수준(`C:\Users\User\.claude\skills`)이라 저장소에서 고칠 수 없고, 이 세션에서 막힌 일도 없었다. 사건이 없어 기각한다.

## 다음

기능 `pilot-portal`의 열린 티켓은 08과 09이고, 둘 다 `Blocked by`가 07뿐이라(각 티켓 파일의 `Blocked by` 줄을 읽었다) 나란히 연다. 마지막으로 닫히는 쪽이 기능 계획에 `**끝:**` 줄을 적는다. 이월 몫(`e2e-widget`·`e2e-portal`을 `.scratch/harness/probes/ci_job_durations.py`의 `JOBS`에 더하고 `ci.yml`의 `timeout-minutes`를 잰 값(약 15)으로 고치는 일)은 기능의 마지막 티켓이 닫힌 뒤의 chore가 맡는다. 지금은 마지막 티켓이 아니라서 chore 배치를 열지 않는다.

```
다음 작업: .scratch/pilot-portal/issues/08-site-switching-and-assurance-modes.md. 셀렉트로 사이트를 바꾸고, 보증 모드와 다크 모드와 보고서 링크가 화면에 보인다
다음 단계: 구현
어디서: 새 세션. 나란히 여는 2 중 1. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 08-site-switching-and-assurance-modes)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
시작 프롬프트: /implement .scratch/pilot-portal/issues/08-site-switching-and-assurance-modes.md
브랜치: feature/08-site-switching-and-assurance-modes
모델: Sonnet 5.5 / high
읽을 것: docs/journal/2026-11-10-1757-anonymous-question-after-notice.md의 "다음". 나란히 여는 다른 지시문은 09(.scratch/pilot-portal/issues/09-real-model-calc-on-portal.md)다
이어받을 상태: 07이 남긴 것은 08 티켓의 체크박스 둘이다(늦게 온 상태 답을 가리는 번호, 상태 묻기 실패 때 덮개를 보이는 갈래의 e2e 사례). 09와 둘 다 질문 페이지 e2e의 준비를 고칠 수 있어 나중에 병합하는 쪽이 main을 받아 맞춘다. 둘 가운데 나중에 닫히는 티켓이 기능 계획의 `**끝:**` 줄을 적는다
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
---
다음 작업: .scratch/pilot-portal/issues/09-real-model-calc-on-portal.md. 실제 모델 시험: 질문 페이지에서 고지를 확인하고 calc에 질문하면 답이 서고 익명 주체의 트레이스가 남는다
다음 단계: 구현
어디서: 새 세션. 나란히 여는 2 중 2. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 09-real-model-calc-on-portal)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
시작 프롬프트: /implement .scratch/pilot-portal/issues/09-real-model-calc-on-portal.md
브랜치: feature/09-real-model-calc-on-portal
모델: Sonnet 5.5 / high
읽을 것: docs/journal/2026-11-10-1757-anonymous-question-after-notice.md의 "다음". 나란히 여는 다른 지시문은 08(.scratch/pilot-portal/issues/08-site-switching-and-assurance-modes.md)이다
이어받을 상태: 08과 둘 다 질문 페이지 e2e의 준비를 고칠 수 있어 나중에 병합하는 쪽이 main을 받아 맞춘다. 둘 가운데 나중에 닫히는 티켓이 기능 계획의 `**끝:**` 줄을 적는다
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```
