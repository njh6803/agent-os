# 2026-11-27 admin-login 티켓 09: 관리 화면의 로그인 화면과 갱신 규칙

브랜치 `feature/09-admin-ui-login-and-refresh-rule`, 티켓 `.scratch/admin-login/issues/09-admin-ui-login-and-refresh-rule.md`. 새 세션(Sonnet 5.5 / high)이 워크트리 `09-admin-ui-login-and-refresh-rule`에서 구현했다.

## 사용자 프롬프트

붙여 넣은 `next-session` 지시문 하나뿐이다(원문은 길어 요지만 옮긴다).

> 사용자: 다음 작업은 `.scratch/admin-login/issues/09-admin-ui-login-and-refresh-rule.md`다. 관리 화면에 로그인 화면과 갱신 규칙을 더하고, 설정 화면에서 공유 토큰 입력 칸을 걷는다. 다음 단계는 구현이고 어디서는 새 세션(나란히 여는 2 중 2)이다. 주 체크아웃에서 브랜치를 따지 않고 `EnterWorktree`(name `09-admin-ui-login-and-refresh-rule`)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다. 시작 프롬프트는 `/implement .scratch/admin-login/issues/09-admin-ui-login-and-refresh-rule.md`, 브랜치는 `feature/09-admin-ui-login-and-refresh-rule`, 모델은 Sonnet 5.5 / high다. 나란히 도는 06은 `.scratch/admin-login/issues/06-account-routes-set-password-and-change-my-password.md`다. 04가 서버에 더한 `POST /auth/refresh`의 401 규칙과 만료된 JWT로 로그아웃하는 길은 일지 `2026-11-26-2116-admin-login-ticket-04.md`에 있다. `tidy-checkouts`는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 `merge.md`의 "워크트리에서 병합할 때"를 따른다. 이번 요청 범위는 PR과 병합까지다.

사용자의 정정이나 피드백은 없었다.

## 한 것

- 운영자 api-client(`createOperatorClient`)를 토큰 없이 만들고, 관리 화면의 `api/session`(주소 규칙 `address.ts`, 갱신 규칙 `rule.ts`, 이동 `navigation.ts`)과 `hooks/queries/session`(`useMe`, `useNeedsFirstAccount`, `useLogIn`, `useLogOut`)을 더했다.
- `/login` 화면(`LoginPage`, `LoginForm`, `FirstAccountGuide`): 첫 계정 안내, 401이면 알림을 두고 비밀번호만 비움, `next`는 `new URL`로 같은 출처만, notice 셋(`logged-out`, `expired`, `password-set`), 루프백이 아닌 http 호스트에는 https 안내.
- 화면 틀: `AdminScreen`이 `GET /auth/me`를 기다리고, `AccountMenu`는 "로그아웃" 하나. `RunDecision`은 채널 토큰 없음 갈래를 잃었다.
- 걷은 것: 관리 토큰·채널 토큰 입력 칸(`AdminTokenForm`, `ChannelTokenForm`, `ClearTokens`), `stores/tokens.ts`, `useHydrated`, 토큰 헤더. 옛 `sessionStorage` 키 `agent-os-admin-tokens`는 뜰 때 지운다(`useForgetOldTokens`).
- 시험: 페이지 시험 `LoginPage.test.tsx`(22), `LoginPage.insecure.test.tsx`(루프백이 아닌 http 주소의 안내), `AdminScreen.test.tsx`(16), `AdminScreen.refresh.test.tsx`(9), `address.test.ts`(36. 셀프 리뷰 뒤의 수), 관리 화면 e2e(`login.e2e.ts`가 `admin-token.e2e.ts`를 대신하고 나머지 e2e는 로그인 화면으로 들어간다), 사진 비교 정답을 새로 찍었다.
- 규칙·문서: `.claude/rules/web-admin.md`의 결정 자리 줄, `README.md`, `.scratch/admin-login/spec.md`의 `[::1]` 문장. 프로브 둘(`cookie_relay` 갱신, 새 `playwright_secure_cookie`)을 `.scratch/admin-login/probes/`에 더했다.

## 검증 결과(셀프 리뷰 전, 이 세션이 직접 친 명령의 결과)

- 사진 비교 정답은 `pnpm -C web visual:admin:update`가 두 번 통과한 판이다. 갱신 뒤에 `pnpm -C web visual:admin`을 비교만으로 따로 다시 돌리지는 않았다(아래 "남은 것"). 바뀐 사진은 이 세션이 몇 장 열어 눈으로 봤다(손으로 본 것).
- `pnpm -C web verify` 통과. 관리 화면 e2e 12건, 위젯 e2e 19건 통과. `uv run ruff check .`와 `uv run ruff format --check .` 통과. `uv run python tools/run_checks.py`는 `check-ticket`만 티켓 파일이 스테이지되기 전이라 빨갰고 나머지는 통과했다(스테이지한 뒤 커밋의 pre-commit이 다시 판정한다).
- 카나리아: `.claude/rules/web-admin.md`를 고쳤다는 알림이 가리킨 명세 둘(`.scratch/admin-style/probes/canary/web_admin_plugins_read.toml`, `.scratch/connection-check/probes/canary/web_admin_periodic_read.toml`)을 새 `claude -p` 세션(2.1.325)으로 실제로 돌려 모두 통과 4, 실패 0, "없음" 섞임 0이다(커밋 `c3ad162fc` 위의 작업 트리). 이 PR 안에서 처음 도는 것이라 사전 확인으로 갈음하지 않았다. 두 명세의 `# 최신 결과:` 줄을 고쳤다.

## 셀프 리뷰(`/code-review`, 표준 축과 명세 축 서브에이전트 둘)

범위: 기준 `c3ad162fc`(origin/dev와의 merge-base), 163개 파일(사진 정답 70장 포함), 커밋 0개, 미추적 0개(모두 스테이지한 작업 트리를 봤다).

### 고친 것

- 계정 메뉴: 로그아웃 요청이 가는 동안 Esc와 메뉴 밖 누르기로 메뉴가 닫히면 실패 알림이 사라진다. `AccountMenu`의 두 닫기 처리가 `pending`을 보게 고치고, `AdminScreen.test.tsx`에 그 갈래의 시험을 더했다.
- 주소 규칙: 퍼센트로 쓴 글자(`/%6cogin`)가 로그인 화면 검사를 지나치던 틈을 `decodedPath`로 막고, 역빗금(`/\evil.test`)도 시험에 더했다. `canSignInAt`의 설명을 실제 조건(https 주소와 루프백의 http)에 맞게 고쳤다.
- 갱신 규칙(`rule.ts`): `Renewal` 타입(`renewed`, `ended`, `unknown`)으로 세 갈래를 가르고, 머리 주석에 `/auth/me` 예외(알림 없이 `/login?next=`)와 규칙 밖 요청 넷을 적었다. 링크로 비밀번호 정하기 경로를 `OUTSIDE_RULE`에 미리 넣었다.
- 시험: 본문이 있는 요청을 다시 보내는 시험(`setPluginEnabled`), 같은 출처의 절대 주소가 빗금 둘로 시작하는 `next`, 루프백이 아닌 http 주소의 안내(`LoginPage.insecure.test.tsx`)를 더했다. 이 시험들은 구현 뒤에 써서 빨강을 본 적이 없어, 변이 표 `.scratch/admin-login/probes/login_rule_mutations.toml`로 열 곳을 망가뜨려 모두 빨간 것을 봤다.
- 옛 변이 표 네 개(`admin-style`의 `settings_theme`, `organisms_props`, `frame_common_states`, `admin_storybook`)가 가리키던 원문이 이 변경으로 사라져 있었다(토큰 입력 칸, 토큰 스토어). 원문을 지금 코드에 맞게 고치거나 지웠고, 관리 화면을 가리키는 변이 표 열두 개를 모두 `--check`로 다시 확인했다.
- 문서: `README.md`의 두 문장(공유 토큰은 `serve`가 시작할 때 아직 요구한다, `http:` 주소에서 쿠키가 저장되지 않는다는 말은 프로브가 잰 주소 하나를 밝힌다), 명세의 `/auth/me` 예외 한 줄과 알림 문구(제목과 본문, 그린 화면대로), `CONTEXT.md`의 설정 화면 풀이, `cookie_relay`와 `playwright_secure_cookie` 프로브 문서의 낡은 문장(빌드 실패, 재지 못함, 걸리는 시간)을 고쳤다. 티켓 09에 "결과 기록"을 더하고, 받는 티켓 10·12의 문장(`run_timeout_seconds`의 출처, `OUTSIDE_RULE`에 이미 든 경로)을 고쳤다. 10·12·13의 Blocked by에는 09가 이미 있다.
- 프로브: `cookie_relay`의 `next start` 갈래를 다시 쟀다(`--mode start --update`, 종료 코드 0). `[::1]` 갈래 둘이 `next dev`의 결과와 같았고 앞 회차의 `start` 몫은 바뀌지 않았다(JSON을 손으로 맞대 봤다).

### 남긴 것과 이유

- `LogInAttempt`와 `LoginForm`에 같은 몇 값이 함께 다닌다(Data Clumps). 아직 쓰는 곳이 둘뿐이고 12의 화면이 같은 모양을 쓰는지 본 뒤 묶는 편이 낫다.
- `address.ts`와 `LoginForm`에 알림 값 표가 따로 있다(중복). 한쪽은 값의 집합, 한쪽은 문구라 지금은 나누는 쪽이 읽기 쉽다. 알림이 하나 더 늘 때 합친다.
- `useLogIn`의 `try` 범위가 넓다. 동작은 맞고 오류 종류별 시험이 있어 두었다.
- 루프백이 아닌 http 주소에서 입력 칸을 모두 끈 것은 디자인이 주 버튼만 끄라고 한 것과 다르다는 지적이 있었다. 어느 쪽도 로그인할 수 없는 주소라 동작은 같고, 디자인 쪽 확인이 필요해 12의 화면을 짓는 때 함께 본다.
- `packages/ui`의 `TextField.tsx` 주석과 `TextField`·`Button` 스토리의 예시 글에 옛 토큰 입력 칸 문구가 남았다. 건드리면 디자인 시스템 동기화와 사진 정답이 따라 움직이는 범위라 이 티켓에 넣지 않았다.
- e2e 하네스의 채널 토큰(`channel.ts` 등)은 13이 걷는다. 티켓 09가 그렇게 정했다.

### 다시 돌린 명령과 결과

- `pnpm -C web exec vitest run --project pages`로 바뀐 페이지 시험 파일 넷(`AdminScreen.refresh`, `AdminScreen`, `LoginPage`, `LoginPage.insecure`): 54건 통과. `--project node`로 `address.test.ts` 36건 통과(각각 이 세션이 쳤다).
- `pnpm -C web verify`: 첫 판은 prettier가 `AccountMenu.tsx`와 `LoginPage.insecure.test.tsx`의 서식에서 멈췄다. 두 파일을 고친 뒤 다시 쳐 141개 파일 2938건 통과(1건은 원래 건너뜀), `check:tsconfig`까지 종료 코드 0.
- `uv run ruff check .`와 `uv run ruff format --check .` 통과.
- `tools/mutate.py --check` 열두 개 표 모두 "원문이 한 번씩 있다". 새 표 `login_rule_mutations.toml`은 변이 10건 모두 기대대로 빨강(기준선은 모두 초록이었다).
- `uv run python tools/run_checks.py`(전체를 스테이지한 뒤): check-notes, check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright 둘, run-hooks, web-verify, pytest가 모두 통과, 종료 코드 0(이 세션이 쳤다). e2e와 사진 비교는 셀프 리뷰 반영 전에 친 결과가 그대로 유효한지 아래에서 가린다.
- 첫 커밋 시도는 pre-commit의 변이 표 검사(`check-mutations`)가 막았다. 새 표 `login_rule_mutations.toml`의 변이 열 개에 `expect_output`이 없다는 이유였다. 표지 없이 돌려 본 실제 실패 줄에서 단언마다 값까지 든 문구를 골라 달고(손으로 본 것), 표를 다시 돌려 열 개 모두 기대대로 빨간 것을 본 뒤 `fc3cdca8d`로 커밋했다. pre-commit이 17분쯤 걸려 백그라운드로 쳤다.
- 셀프 리뷰 반영이 닿은 파일은 시험, 로직(`AccountMenu`의 닫기 가드, `address.ts`, `rule.ts`)과 문서뿐이고 화면 모양은 바뀌지 않았다. 사진 정답과 e2e의 화면은 그대로라 앞서 친 사진 비교(`visual:admin`, 종료 코드 0)와 e2e(관리 화면 12건, 위젯 19건)를 다시 치지 않았다. 이 판단은 어림이고, CI의 `e2e`와 `visual` 잡이 판정한다.

## 인계(2026-11-27, 컨텍스트가 인계 문턱을 넘어 커밋 뒤에 넘겼다)

이 세션은 커밋 `fc3cdca8d`까지 했고 푸시, PR, 병합이 남았다. 새 세션이 같은 브랜치·워크트리에서 이어 쓴다. 이 세션의 제목은 `feature/09-admin-ui-login-and-refresh-rule`이었고 `(인계함)`으로 바꾼다. 일지의 "## 다음"은 쓰지 않았다. 새 세션이 PR을 열고 병합한 뒤 쓴다.

PR 본문에 넣을 것(지시문에도 같은 것을 적었다):

- 명세 `.scratch/admin-login/spec.md`의 두 줄을 고쳤다. 558번 줄 알림 문구는 제목과 본문 둘로 그린 화면대로 바꿨고(`design/mk-login-notices.dc.html`), 573번 줄에는 `/auth/me` 예외(갱신까지 401이어도 알림 없이 `/login?next=`)를 더했다.
- 병합 충돌 후보: `README.md`(PR #651, 워크트리 04), `web/packages/api-client/src/clients.test-d.ts`(워크트리 06).
- e2e와 사진 비교는 셀프 리뷰 반영 전에 쳤고 반영은 화면 모양을 바꾸지 않아 다시 치지 않았다(어림). CI의 `e2e`와 `visual` 잡이 판정한다.

### 이어받은 세션(2026-11-27)

새 세션이 같은 워크트리에 들어와 이어받았다. 시작할 때 `git fetch origin`과 `tools/sibling_overlap.py`를 쳤다(번호 겹침 없음). origin/dev는 `c3ad162fc`에서 `793298c85`(PR #655, 위젯 런타임 값 티켓 문서)로 한 칸 나아갔고, 그 변경은 이 브랜치가 건드린 파일과 겹치지 않는다(`git diff --name-only HEAD...origin/dev`를 손으로 대 봤다). `tools/plan_table.py`를 돌려도 `.scratch/plan.md`는 바뀌지 않았다. 디자인 시스템 `확인`(`/sync-design-system 확인`)은 새 세션의 첫 화면 코드 수정 전에 돌려 `clean`(웹 편집 없음, 결정표 `continue`)이었다(`web/tools/sync-design-system/main.ts check judge`와 `decide`의 출력을 손으로 봤다).

PR을 열었다: [#657](https://github.com/njh6803/agent-os/pull/657)(제목에 느낌표 없음, 릴리스 노트 조각 없음, 본문 끝에 `🤖 Generated with [Claude Code]` 줄). 푸시 전에 `origin/dev`(`793298c85`, 문서만 바뀐 #655)를 합쳤고 충돌은 없었다. 합친 뒤 `uv run python tools/sibling_overlap.py`는 번호 겹침 없음, 글자 충돌 후보는 앞과 같은 둘(`README.md`, `clients.test-d.ts`)이었다. 첫 커밋 시도는 시험의 에러 코드(`"internal"`, 계약의 값은 `"internal_error"`)로 pre-commit의 `web-verify`(tsc)에 막혔고, 고쳐서 다시 커밋해 통과했다. 이 세션도 컨텍스트가 문턱을 넘어 `PR 연 뒤` 경계에서 새 세션에 인계한다. 남은 일은 봇 회차(`merge.md` 2)와 병합이고, 앱의 PR 감시는 이 세션에 묶여 있다(`get_status`로 PR #657이 묶인 것을 보았다).

### PR 직전 리뷰(`coderabbit-review` 서브에이전트)

CodeRabbit CLI 0.7.5가 `--base origin/dev`로 163개 파일을 끝까지 돌았다(`review_completed`, findings 11건, 서브에이전트가 보고했다). `coderabbit auth status`의 Seat 줄은 `not assigned`(Plan: Free)였고 리뷰는 좌석 없이도 돌았다. 서브에이전트의 판정을 이 세션이 코드로 다시 읽어 갈랐다.

고친 것:

- 결정 자리가 침묵하던 틈(Major). 갱신이 네트워크나 5xx로 실패하면 `rule.ts`는 로그인 화면으로 보내지 않고 처음 401을 그대로 돌려주는데, `RunDecision.noticeOf`가 401이면 알림을 숨겨서 승인을 눌러도 화면에 아무 반응이 없었다(`rule.ts` 92번 줄 근처와 `RunDecision.tsx`를 직접 읽어 확인했다). 401도 "결정을 보내지 못했다"로 보이게 고치고, 숨기는 데만 쓰이던 `isRejection`을 걷었다. 갱신까지 401이면 화면이 로그인 화면으로 가므로 알림은 이동 직전에 잠깐 보일 뿐이다(어림이고 e2e는 다시 치지 않았다). 시험 `RunPage.decision.test.tsx`의 "결정이 401 을 받고 갱신이 서버 오류로 실패하면…"을 더했고, 고치기 전에 알림이 없다는 이유로 빨간 것을 보았다(손으로 쳤다).
- 계정 단추(Minor). 로그아웃 요청이 가는 동안 계정 단추를 다시 누르면 메뉴가 닫혀 실패 알림이 사라졌다. Esc와 바깥 누르기와 같게 `pending`이면 무시한다. 기존 시험 "요청이 가는 동안에는…"에 단추를 누르는 단계를 더했고, 고치기 전에 메뉴가 닫혀 빨간 것을 보았다(손으로 쳤다).

오탐으로 가른 것(서브에이전트와 이 세션이 코드를 읽었다): 결정 요청이 갱신 규칙을 안 지난다는 지적(`sendDecision`은 `refreshRule`이 꽂힌 클라이언트를 쓴다), 옛 `data`와 새 `error`가 함께 오는 `AdminScreen` 경로(없다고 가렸으나 틀렸다. 아래 "봇 회차"에서 CodeRabbit이 다시 짚어 고쳤다), 결정 e2e가 `next`로 돌아오는지(같은 파일이 이어서 단언한다), 프로브 중계 소켓 하나만 파괴한다는 지적(정상 경로에 영향 없다).

보류한 것과 이유:

- 다른 탭이 다른 계정으로 로그인하면 이 탭은 옛 이름을 보이는 채로 새 계정의 쿠키로 요청이 나간다(Minor). 쿠키 로그인 구조의 흔한 한계이고 서버가 요청마다 권한을 판정한다. `useMe`가 창 포커스에서 다시 읽지 않는 까닭이 갱신 겹침 방지라 손대려면 그 조정이 따라온다. 명세가 받아들이는지 판단이 필요해 PR 코멘트와 다음 지시문의 "이어받을 상태"에 적는다.
- 계정 메뉴의 키보드 흐름(열릴 때 첫 항목에 포커스, Esc로 닫으면 계정 단추로 복귀)과 불러오는 중을 `disabled` 대신 `aria-busy`로 바꾸기(Minor). 모양과 사진 정답이 따라 움직일 수 있어 12의 화면 작업에서 함께 본다.
- `playwright_secure_cookie/probe.mjs`의 `try`가 `page.goto`와 `context.cookies()`의 오류까지 `addCookiesError`로 기록할 수 있다(Minor). 근거로 든 프로브라 고치면 `expected.json`을 다시 재야 한다. 이번 PR이 근거로 쓰는 갈래의 값은 바뀌지 않았다고 보고 다음 회차에 맡긴다(프로브를 다시 돌려 보지 않은 어림이다).

open-session을 부른다 2026-11-27T10:52:30Z

## 봇 회차

첫 요청(푸시 `bfe9c8cfb`)에서 CodeRabbit은 `Review rate limited`로 리뷰 없이 끝났고(`wait_ci.py`의 끝 줄), 한도에 걸려 리뷰가 없던 푸시는 회차로 세지 않는다. `claude-review`는 지적 없음이었고, 검사는 `python`, `web`, `visual`, `e2e`, `e2e-widget`, `e2e-portal`, `e2e-standalone`, `ticket`, `verify`가 모두 SUCCESS였고 `llm`은 SKIPPED였다(`wait_ci.py`가 낸 목록을 읽었다). 앞서 어림으로 남긴 e2e와 사진 비교는 CI의 `e2e`와 `visual` 잡이 통과해 확인됐다.

`origin/dev`(PR #656, 티켓 06)를 합친 푸시 `af327d315`에서 CodeRabbit이 `Finished`로 첫 리뷰를 냈다(이 PR의 첫 회차). 지적 넷이 모두 Minor였고 지적마다 판단했다. 합친 결과는 충돌이 없었고 `pnpm -C web verify`가 통과했다(손으로 쳤다).

- 고친 것: `AdminScreen`이 `me.data`가 있으면 `me.error`를 보지 않아, 화면을 옮겨 캐시된 `me`로 다시 읽다 서버가 오류를 내면 옛 계정과 본문이 그대로 남았다(`web-admin.md`의 서버 데이터를 다시 읽다 실패하면 이미 보인 것을 지우고 실패만 보인다는 줄과 어긋난다). 앞서 이 경로를 "없다"로 가른 것은 틀렸다. SWR이 마운트 때 다시 읽고, 실패하면 `data`를 둔 채 `error`를 채운다(`READ`에 `revalidateIfStale`을 끄는 줄이 없는 것을 코드로 읽었다). 오류를 먼저 보게 순서를 바꿨고, 캐시를 하나 넘겨 화면을 두 번 그리는 시험(`AdminScreen.test.tsx`)을 더했다. 고치기 전에 알림이 없다는 이유로 빨간 것을 보았다(손으로 쳤다).
- 보류한 것: ① `AccountMenu`의 키보드 흐름(열릴 때 첫 항목 포커스, Esc 뒤 단추로 복귀)은 앞서 보류한 것과 같은 지적이다(12의 화면 작업). ② `playwright_secure_cookie/probe.mjs`의 `try` 범위도 앞서 보류한 것과 같다. ③ `cookie_relay/probe.mjs`의 `::1` 바인딩 실패가 표지 없이 지나 종료 코드 0으로 끝날 수 있다는 지적은 새것이다. 프로브의 `catch` 한 곳을 고치는 일이지만 고친 프로브는 다시 재야 하고(`--update`의 종료 판정이 바뀐다) 이 PR이 근거로 쓰는 값은 정상 경로에서 바뀌지 않으므로, ②와 함께 그 프로브들을 다시 잴 때 고친다.

## 다음

PR #657을 병합하면 admin-login 티켓 09가 끝난다.

- 다음 단계는 열린 티켓 10(`10-chat-read-screens-list-panel-and-polling.md`, 막는 것 07·09), 12(`12-account-password-and-set-password-screens.md`, 막는 것 06·09), 13(`13-remove-shared-tokens.md`, 막는 것 05·09)의 구현이다. 막는 티켓이 모두 done이라 셋 다 시작할 수 있다. 06은 이미 병합됐다(PR #656). 11은 10을, 14는 13을 기다린다.
- 뒤로 넘긴 일(모두 Minor, 이유는 위 "보류한 것과 이유"와 "봇 회차"): 다른 탭의 계정 전환 표시 불일치는 명세가 받아들이는지 판단이 필요하다. 계정 메뉴의 키보드 흐름과 `aria-busy`는 12의 화면 작업에서 함께 본다. `playwright_secure_cookie` 프로브의 `try` 범위와 `cookie_relay` 프로브의 `::1` 바인딩 실패 표지는 그 프로브들을 다시 잴 때 함께 고친다.
- 13이 걷는 것: e2e 하네스의 채널 토큰(`channel.ts` 등)과 `serve`의 공유 토큰 요구. 티켓 09가 그렇게 정했다.
- 12의 화면을 지을 때 볼 것: 루프백이 아닌 http 주소에서 입력 칸을 모두 끈 것이 디자인(주 버튼만 끔)과 다르다. `LogInAttempt`와 `LoginForm`의 Data Clumps, 알림 값 표 중복도 그때 묶는다.
- `packages/ui`의 `TextField.tsx` 주석과 `TextField`·`Button` 스토리 예시 글에 옛 토큰 입력 칸 문구가 남았다. 디자인 시스템 동기화와 사진 정답이 따라 움직이는 범위라 따로 한다.
- 병합 충돌 후보였던 `web/packages/api-client/src/clients.test-d.ts`(06)는 `origin/dev`를 합칠 때 충돌 없이 합쳐졌다. `README.md`(PR #651, 티켓 04 단독 배포)는 아직 열려 있어, 그 PR이 나중에 병합되면 그쪽이 푼다.
- 워크트리에서 병합하므로 주 체크아웃은 당기지 않는다. 다음 세션이 `tidy-checkouts`를 먼저 돈다.
- 이 PR은 로컬 모델 시험(`llm_local`)의 병합 조건 범위(`operations.md` LLM 테스트의 "범위": `src/agent_os/adapters/`, `core/loop.py`·`model.py`·`run.py`, `channel/`, `main.py`, 로컬 모델 시험 자신, `langchain-openai`·`openai` 판)에 닿지 않아 돌리지 않았다. 근거는 `git diff --name-only origin/dev...HEAD`를 손으로 쳐 본 결과로, `web/`, `.scratch/`, `docs/`, `.claude/rules/web-admin.md`, `CONTEXT.md`, `README.md`뿐이고 `src/`와 `pyproject.toml`·`uv.lock`은 없었다.
