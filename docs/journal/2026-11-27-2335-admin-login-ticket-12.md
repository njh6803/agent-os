# 2026-11-27 admin-login 티켓 12: 계정 화면, 내 비밀번호 바꾸기, 링크로 비밀번호 정하기

브랜치 `feature/12-account-password-and-set-password-screens`, 티켓 `.scratch/admin-login/issues/12-account-password-and-set-password-screens.md`. 새 세션(Sonnet 5.5 / high)이 워크트리 `12-account-password-and-set-password-screens`에서 구현했다.

## 사용자 프롬프트

붙여 넣은 `next-session` 지시문 하나뿐이다(원문은 길어 요지만 옮긴다).

> 사용자: 다음 작업은 `.scratch/admin-login/issues/12-account-password-and-set-password-screens.md`다. 계정 화면, 내 비밀번호 바꾸기 화면, 링크로 비밀번호 정하기 화면을 짓는다. 다음 단계는 구현이고 어디서는 새 세션(나란히 여는 3 중 2)이다. 09에서 보류한 Minor 둘(계정 메뉴의 키보드 흐름과 `aria-busy`, 루프백이 아닌 http 주소의 로그인에서 주 버튼만 끄기와 `LogInAttempt`·`LoginForm`의 Data Clumps)을 이어받는다. 나란히 도는 10은 탐색에 "대화"를 더하므로 사진 정답이 겹칠 수 있고, 나중에 병합하는 쪽이 푼다. 병합은 이 워크트리 사본의 `merge.md`의 "워크트리에서 병합할 때"를 따른다. 이번 요청 범위는 PR과 병합까지다.

사용자의 정정이나 피드백은 없었다.

## 한 것

- `api/accounts`(목록, 만들기, 링크 다시 만들기, 켜고 끄기, 잠금 풀기)와 `hooks/queries/accounts`, `api/session`의 `changePassword`·`setPassword`와 훅 둘, `setPasswordAddress`를 더했다.
- 화면: `AccountsPage`(`/accounts`, 관리자는 한 줄만), `PasswordPage`(`/password`), `SetPasswordPage`(`/set-password#<토큰>`, 토큰은 `useState` 초깃값으로 읽고 `history.replaceState`로 주소창에서 지운다).
- 부품: `Dialog`(포털, 포커스 가두기, Esc), `usePopupMenu`(계정 메뉴와 줄 끝 메뉴가 함께 쓴다), `PasswordRuleList`와 `passwordRules`(NFKC와 코드 포인트 셈), `AccountList`(표와 카드), 창 셋, `ChangePasswordForm`, `SetPasswordForm`, `atoms/clock`.
- 09에서 넘어온 것: 계정 메뉴의 키보드 흐름, 로그아웃 중의 `aria-busy`, http 로그인에서 주 버튼만 끄기, `LoginForm`의 `state` 묶음.
- 시험: 페이지 시험 셋(`AccountsPage`, `PasswordPage`, `SetPasswordPage`)과 `AdminScreen.test`, 스토리 여덟 파일, 관리 화면 e2e(`accounts.e2e.ts`), 사진 정답(새 92장, 바뀐 16장).
- 문서: `README.md`의 로그인 문단에 세 화면을 더했다.

## 검증 결과

- 스토리 테스트 두 폭: 160건 통과. 관리 화면 e2e 13건 통과(새 `accounts.e2e.ts` 포함). `pnpm -C web visual:admin:update`가 종료 코드 0으로 끝났다.
- 바뀐 사진 가운데 계정 목록(넓은 폭과 좁은 폭), 비밀번호 링크 창(다크), 비밀번호 정하기의 링크 못 씀(좁은 폭)을 열어 눈으로 봤다(손으로 본 것).

## 인계(2026-11-27, 셀프 리뷰 직전)

이 세션은 컨텍스트가 인계 문턱을 넘어 셀프 리뷰(`/code-review`) 직전 경계에서 새 세션에 넘긴다. 이 세션의 제목은 `feature/12-account-password-and-set-password-screens`였고 `(인계함)`으로 바꾼다. 번복하거나 고친 결정은 없다.

- 지금 상태(손으로 본 것: `git add -A` 뒤 `git status`): 모든 변경이 스테이지되어 있고 커밋은 없다. 티켓 `.scratch/admin-login/issues/12-account-password-and-set-password-screens.md`는 `Status: done`에 체크박스를 모두 `[x]`로 바꿨고 "결과 기록" 절을 더했다. 마지막 두 검증 칸(검증 명령이 모두 초록, e2e와 사진 비교를 로컬에서 친다)은 아직 다 끝나지 않았다. 아래 "남은 일"이 초록이 아니면 그 칸을 `[ ]`로 되돌린다.
- 이 세션이 친 것: 스토리 테스트 두 폭 160건 통과, 관리 화면 e2e 13건 통과, `visual:admin:update` 종료 코드 0, `uv run ruff check .`·`ruff format --check .` 통과, `tsc --noEmit`과 `eslint --max-warnings 0 apps/admin` 통과. `tools/run_checks.py`는 check-notes, lint-imports, zizmor, check-instructions, check-type-escapes까지 통과한 줄을 본 뒤 이 인계로 멈췄다(백그라운드에서 TaskStop으로 멈춤). 나머지는 확인하지 못했다.
- 남은 일: ① `uv run python tools/plan_table.py`(티켓 상태를 done으로 바꿨으니 `.scratch/plan.md`가 바뀌는지 보고 같은 커밋에 싣는다. 아직 돌리지 않았다), ② 셀프 리뷰(`/code-review`)와 Critical·Major 반영, ③ `uv run python tools/run_checks.py`(백그라운드로, 뒤에 일지로 옮긴다), `pnpm -C web verify`, `pnpm -C web visual:admin`을 비교만으로 한 번 더, ④ 커밋 직전 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`, ⑤ 커밋·푸시·PR·봇 회차·병합(`merge.md`의 "워크트리에서 병합할 때"). 티켓 10(탐색에 "대화"를 더한다)이 먼저 병합되면 탐색과 사진 정답이 겹치므로, 나중에 병합하는 쪽이 푼다.
- 확인하지 못한 것: 새 사진 정답이 CI의 `visual` 잡과 같은 결과인지(로컬 Docker로만 갱신했다), 스토리가 아닌 화면 전체의 사진은 이 기능에 없다. 키보드 흐름(계정 메뉴 첫 항목 포커스, Esc 복귀)은 페이지 시험과 스토리 play가 본다.
- 이 세션이 조심해야 했던 것(다시 겪지 않게): Bash 훅이 `cd <하위 폴더>`와 `.env`를 건드리는 저장소 전체 grep을 거부한다. `( cd … && … )`나 `pnpm -C`, `git -C`를 쓴다. ESLint는 불리언 인자, 숫자의 템플릿 보간(`String()`), `require-await`(스토리의 `fn(async …)`는 `Promise.resolve`), 층 경계(organism 스토리가 template을 import하면 `templates/`로 옮긴다)를 막는다. 타입 우회(`as`, `!`, `any`)는 시험에서도 막힌다.

open-session을 부른다 2026-11-27T14:43:23Z
인계 못함 셀프 리뷰 직전: open_session.ps1 호출이 자동 모드 분류기에 거절되어(Destructive or Unwanted Actions) 새 세션을 열지 못했다. 제목을 되돌리고 이 세션에서 잇는다. 이 세션이 멈춘 백그라운드 검증(run_checks)은 다시 돌려야 한다. 2026-11-27T14:44:04Z

## 셀프 리뷰(`/code-review`, 표준 축 sonnet·high와 명세 축 서브에이전트 둘)

범위: 기점 `a11fffed48`(origin/dev와의 merge-base), 사진을 뺀 변경 파일 48개와 사진 정답 108장(새 92, 바뀐 16), 커밋 0개, 미추적 0개(모두 스테이지한 작업 트리). 인계를 시도했으나 열기가 자동 모드 분류기에 거절되어(위 `인계 못함` 줄) 이 세션이 이어 했다.

### 고친 것

- 내 비밀번호 화면의 안내(명세 "ADR 0062가 넘긴 둘"과 그린 화면 `mk-my-password`가 요구, 명세 축이 짚었고 이 세션이 명세 332행과 그린 화면 51행을 직접 읽어 확인했다). 머리 설명을 "<계정 이름>의 비밀번호를 바꾼다."로, 버튼 위에 `바꾸면 이 계정의 다른 로그인은 길어야 N분 안에 모두 끊긴다. 이 브라우저의 로그인은 그대로다.`를 더했다(`ChangePasswordForm`에 `name` prop). 페이지 시험을 더했다.
- 사실과 어긋난 주석 넷. `passwordRules.ts`의 그림 문자 128자가 UTF-16 단위로 253이라는 주석을 256으로(이 세션이 `node -e`로 `"😀".repeat(128).length`를 쳐 256을 봤다), `Dialog.tsx`의 포커스 복귀 문장에 "그 자리가 아직 문서에 있을 때만"을, 같은 파일 `onClose`의 "창 안의 닫기 단추가 부른다"를 쓰는 쪽이 단추를 둔다는 말로, `PasswordLinkDialog.tsx`와 `usePopupMenu.ts`의 문장을 코드의 동작대로 고쳤다. `hooks/queries/session/index.ts`의 "입력 칸을 막는다"는 "화면이 입력 칸을 걷는다"로.
- 시험이 없던 메뉴의 키보드 갈래(위 방향 키가 맨 위에서 맨 아래로 돈다, Home과 End, Tab이 메뉴를 닫는다)를 `AdminScreen.test.tsx`에 더했다. 표준 축이 바깥 누르기 시험이 없다고 했으나 이미 있었다(코드를 읽어 확인).
- 티켓의 검증 두 칸을 근거가 생기기 전에 `[x]`로 둔 것을 `[ ]`로 되돌렸다(표준 축과 명세 축이 모두 짚었다). 검증이 끝난 뒤 다시 채운다.

### 남긴 것과 이유

- 같은 모양의 중복(실패 알림 처리 다섯 곳, 두 `Fields`, `TIER_LABEL`과 메뉴 항목 클래스 표, `PasswordChangeAttempt`와 `ChangePasswordState` 같은 쌍, 시험 도우미 `fill`)은 Minor다. 훅 쪽 타입이 organisms를 import할 수 없는 층 경계라 쌍은 구조가 같은 두 선언으로 남는다. `LogInAttempt`와 `LoginState`도 같다. 묶으면 열 곳 넘게 닿아 이 티켓의 범위를 넓힌다.
- `AccountList.tsx`가 510줄이다(Divergent Change, Minor). 표, 카드, 메뉴 규칙, 창 열기가 한 파일에 있어 나중에 쪼갠다. `preview`와 `initiallyOpen`은 사진 스토리가 열린 상태를 그리려면 필요한 입구라 둔다(`.claude/rules/web-design.md`: 사진은 play가 `userEvent`를 부르기 전의 그림이다).
- `ChangePasswordState`의 `changed`·`locked`와 `SetPasswordState.unusable`이 상태를 불리언으로 쪼갰다(`CODING_STANDARDS.md`의 "갈래를 고르는 인터페이스의 불리언 칸은 열거로"). 훅, 폼, 시험, 스토리가 모두 닿아 같은 방향의 정리로 따로 한다. Minor.
- 404 문구는 제목 "이 링크는 더 쓸 수 없다"와 본문(그린 화면의 두 문장 + "관리하는 사람에게 새 링크를 받는다")으로 갈렸다. 티켓·명세의 이어진 한 문장과 글자가 다르지만 두 조각 모두 들어 있고 그린 화면과 같다. 성공 알림도 제목과 본문으로 갈렸다(그린 화면 방식).
- 카드로 바뀌는 기준이 창 폭 768px이 아니라 본문 칸의 `@split`(784px)이다(실행 목록과 같은 방식, admin-style 티켓 06). 옆 탐색이 선 768~1000px 창에서는 표 대신 카드가 뜬다. 사진은 320과 1280만 찍어 중간 폭은 보지 못했다.
- 비밀번호 링크 창은 Esc로 확인 없이 닫힌다. 링크를 다시 볼 수 없으므로 어색할 수 있으나 명세가 정한 것은 막을 눌러 닫지 않는 것까지다. 확인 한 단계를 더하는 일은 명세 결정이라 후속으로 넘긴다.
- `useChangePassword`와 `useSetPassword`의 `try` 범위(`CODING_STANDARDS.md`의 에러 처리 줄은 파이썬 `except`가 대상이다)와 `PasswordRuleList`의 세 갈래 반복은 Minor로 남긴다.

### 다시 돌린 명령과 결과(셀프 리뷰 반영 뒤, 이 세션이 쳤다)

- `prettier --write`, `tsc --noEmit -p apps/admin`, `eslint --max-warnings 0 apps/admin` 통과. 페이지 시험 네 파일(`PasswordPage`, `AdminScreen`, `AccountsPage`, `SetPasswordPage`) 68건 통과, 스토리 시험 두 폭 160건 통과.
- `pnpm -C web visual:admin:update`를 다시 돌려 바뀐 사진이 내 비밀번호 화면 스토리 다섯의 20장뿐인 것을 `git status`로 보았고 한 장(`organisms-changepasswordform--empty-1280-light`)을 열어 설계 화면의 머리 설명과 버튼 위 안내가 서 있는 것을 눈으로 확인했다(손으로 본 것).
- `uv run ruff check .`와 `ruff format --check .` 통과(앞서 쳤고 파이썬 변경은 없다). `uv run python tools/run_checks.py`는 스테이지한 전체에서 check-notes, check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright 둘, run-hooks, web-verify, pytest가 모두 통과, 종료 코드 0.
- `pnpm -C web/apps/admin exec playwright test` 13건 통과, `pnpm -C web visual:admin`(비교만) 154건 통과, 종료 코드 0.
- 티켓의 검증 두 칸을 위 결과가 나온 뒤 `[x]`로 다시 채웠다.
