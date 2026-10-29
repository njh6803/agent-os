# 2026-10-29 (19) 설정 화면에서 고른 테마가 바로 바뀌고 새로 고쳐도 첫 그림부터 그 테마다 (admin-style 09)

next-session 지시문으로 연 새 세션이다(나란히 여는 4 중 4). 지시문대로 `tidy-checkouts`는 돌지 않았고(묶음의 첫 세션이 돈다), 주 체크아웃에서 브랜치를 따지 않고 `EnterWorktree`(이름 `09-admin-settings-theme`)로 워크트리에 들어갔다. `implement` 스킬을 디스크의 `SKILL.md`로 읽어 따랐다.

> 사용자: "`.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/admin-style/issues/09-admin-settings-theme.md … 다음 단계: 구현 … 어디서: 새 세션, 나란히 여는 4 중 4 … 이어받을 상태: PR #423 claude-review 넷째 회차가 설정 화면의 설명 '테마는 이 브라우저에, ...'가 아직 없는 테마 카드를 가리킨다고 짚었고, 명세와 그림이 정한 문구라 보류했다(issuecomment-6496248361). 이 티켓이 테마 카드를 더하면 문구가 화면과 맞는지 함께 본다 … 확인할 선행 조건: 주 체크아웃 미갱신 … tidy-checkouts는 묶음의 첫 세션이 돈다 … 이번 요청 범위: PR과 병합까지"

## 웹 편집 확인

`/ui-design`의 웹 편집 확인을 그림 둘(`mk-settings.dc.html`, `mk-settings-m.dc.html`)과 `canvas.json`에 했다. 화면 Design 아티팩트에서 받은 세 파일의 sha256이 옮긴 파일과 모두 같아 웹에서 고친 것이 없었다(대조 스크립트가 찍었다). 관리 화면 코드를 처음 고치자 계기 훅이 알려 `/sync-design-system 확인`을 불렀고, `check judge`의 `result`가 `clean`이었다(도구가 찍었다).

## 구현

시험을 먼저 쓰고 빨강을 본 뒤 구현했다. 테마 페이지 시험(`SettingsPage.theme.test.tsx`)과 그리기 전 스크립트의 단위 시험(`theme.prepaint.test.ts`)은 구현 전에 빨갰지만, 그 빨강은 카드나 스크립트 파일이 없어서였다. 구현 뒤 node 11, pages 167, 두 폭의 스토리 10, 관리 화면 e2e 2가 초록이었다(도구가 찍었다).

- **지금 테마의 원천.** 문서 뿌리 `html`의 `data-theme` 하나다(`stores/theme.ts`). 스토어(Zustand)에 복사하지 않는다. 화면은 `useSyncExternalStore`로 그 속성을 읽고, 고르기·다른 탭·되살리기는 모두 `apply` 하나로 속성을 바꾼 뒤 모듈 안의 듣는 쪽에 바로 알린다. `MutationObserver`로 듣지 않은 것은 알림이 React 밖에서 비동기로 와 페이지 시험에 `act` 경고가 났기 때문이다(구현 중 페이지 시험이 찍었다).
- **저장과 다른 탭.** localStorage 키 `agent-os-admin-theme`에 테마 키 글자 그대로 적는다. 기본(녹청)을 골라도 적는다. `storage` 이벤트는 그 키이거나 키가 없는 것(저장소 전체를 비움)만 받고, 목록에 없는 값이나 지워진 키면 속성을 걷는다. 듣기와 마운트 때 되살리기는 모든 화면이 지나는 `pages/AdminScreen`의 `useStoredTheme`이 맡고, 그리기 전에 되살리도록 `useLayoutEffect`다(설치본 Next 가이드 "Preventing Flash"의 "Re-applying attributes in development"를 읽었다).
- **그리기 전 스크립트.** `public/theme.js`를 뿌리 레이아웃 `<head>`의 막는 `<script src>`로 싣고 `<html>`에 `suppressHydrationWarning`을 단다. 키 목록과 저장 키를 따로 적고, 단위 시험이 앱의 `THEMES`와 `THEME_STORAGE_KEY`에 맞댄다.
- **테마 카드.** `molecules/ThemeCard`(라디오와 `inert` 표본, 라디오 이름은 `aria-labelledby`로 테마 이름만)와 `organisms/ThemePicker`(`fieldset` "테마", 본문 칸이 `split` 이상이면 한 줄에 넷)를 짓고 `organisms/Settings`의 화면 머리 아래에 둔다. organisms는 스토어를 import하지 못해(판정자) `pages/SettingsPage`가 읽어 넘긴다.
- **좁힌 단언과 문서.** `HomePage.test.tsx`의 저장 시험과 `admin-token.e2e.ts`의 localStorage 단언을 "어느 값에도 토큰이 없고 키는 테마 키만"으로 좁혔다. `stores/tokens.ts` 머리 주석, `web/eslint.config.mjs`의 stores 요소 주석, `docs/constitution/tech.md` 웹 줄을 고쳤다. 옛 표현("두기로 했다")의 잔존은 티켓·명세·03 티켓(기록)에만 있다(`grep`으로 손으로 봤다). 헌법 판은 형제 대조(`tools/sibling_overlap.py`)가 짚어 3.0.61로 올렸다.

티켓의 메모가 맡긴 구역 머리 묶기는 묶지 않기로 정했다(테마 구역은 `fieldset`과 `legend`라 같은 모양이 여전히 둘이다). PR #423이 짚은 설명 문구는 테마 카드가 서서 화면과 맞아 그대로 둔다. 둘 다 티켓의 "이 티켓이 정한 것"에 적었다.

## 변이 표

구현 뒤에 쓴 단언을 변이 표 `.scratch/admin-style/probes/settings_theme_mutations.toml`(스물셋)로 봤다. 표지를 고르려고 같은 표를 읽어 변이마다 출력 전체를 파일로 남기고 바이트 그대로 되돌리는 스크래치 미리보기를 한 번 돌렸고(스물셋 모두 1로 끝났고 `git status`에 변이가 남지 않았다, 도구가 찍었다), 그 출력에서 실패 머리의 메시지를 골랐다(손으로 봤다). 같은 메시지를 그 시험의 다른 단언도 낼 수 있는 일곱(저장 값과 속성 단언이 같은 꼴, 고른 카드의 요소 비교, 셋업 변이가 다음 시험까지 빨갛게 하는 것, 스토리의 `expected true to be false`·`expected false to be true`·`expected 2 to be 1`)은 실패 줄의 위치(`<파일>:<줄>:`)를 함께 넣었다. 접근자가 던지는 맥락에서 node `vm`은 접근자의 예외 대신 `ReferenceError: localStorage is not defined`를 냈다(미리보기가 찍었다).

`tools/mutate.py`로 표 전체를 돌리니, e2e 기준선이 시험을 통과한 뒤 준비의 정리(`web/apps/admin/e2e/stack.ts`의 `rmSync(work)`)에서 오류로 끝나 변이를 넣지 않았다(도구가 찍었다). e2e를 뺀 스물둘은 표지까지 기대대로였다(도구가 찍었다). e2e 하나만 다시 돌리자 기준선이 같은 정리 오류로 또 끝났고, 바로 그 기준선을 직접(`pnpm -C web/apps/admin exec playwright test e2e/admin-token.e2e.ts -g 첫 그림부터`) 돌리니 오류 없이 지났으며, 셋째 변이 실행에서 기준선이 초록이고 표지까지 기대대로였다(셋 다 도구가 찍었다). 그 오류의 본문은 도구가 끝 열 줄만 내어 보지 못했다. 위젯 e2e가 같은 자리의 EPERM을 serve의 작업 폴더를 `tmpdir()`로 옮겨 고쳤고(일지 2026-10-24-10), 관리 화면의 준비는 아직 serve를 `work`에서 띄운다(코드를 읽었다). 같은 원인이라는 것은 어림이다.

## 사진 비교와 Docker

`timeout 20 docker version`이 `request returned Internal Server Error for API route and version …`였다(Docker가 찍었다). 대기열 494와 같은 엔진 오류다.

> 질문: "사진 비교는 Docker 컨테이너 안의 브라우저로 화면을 찍어 정답 사진과 픽셀 단위로 견줍니다. 컨테이너를 쓰면 어느 PC에서나 같은 글꼴과 렌더링으로 찍히지만, Docker 엔진이 살아 있어야 합니다. 지금 엔진이 `Internal Server Error`로 답해, 테마 카드의 정답 사진을 만들 수 없습니다(사진 비교 설정이 `updateSnapshots: "none"`이라 정답이 없는 새 스토리는 CI의 visual 잡에서 실패합니다). Docker Desktop을 어떻게 다시 켤까요?"
> 고른 답: "에이전트가 끄고 다시 켠다" — "이 세션이 Docker 프로세스를 끄고 Docker Desktop을 다시 띄웁니다. 나란히 도는 다른 세션이 그때 사진 비교를 돌리고 있으면 그 컨테이너가 끊길 것으로 어림합니다."

Docker 프로세스를 `Stop-Process`로 끄고 Docker Desktop을 다시 띄우자 서버 판 24.0.7이 답했다(도구가 찍었다). 변이를 다 돌린 뒤 친 `pnpm -C web visual:admin:update`는 Storybook 정적 빌드를 마치고 `docker run`이 `containers/create`의 같은 오류로 125로 끝났고, 바로 친 `docker version`·`docker ps`도 같은 오류였다(Docker가 찍었다). 다시 켠 뒤 십수 분 사이에 엔진이 다시 죽은 것이다. 같은 목적이라 한 번 더 끄고 켠 뒤, 10초마다 `docker ps`를 묻다가 답하면 바로 사진 정답 만들기를 띄우는 스크래치 대기 스크립트를 돌렸다. 첫 시도에 답했고 사진 정답 만들기가 32 통과, 종료 0이었다(러너가 찍었다).

바뀐 사진은 열둘이다(`git status`가 찍었다). 새 사진 넷은 테마 카드 스토리(`organisms-themepicker--cards`의 1280·320 × 라이트·다크)이고, 다시 만든 여덟은 테마 카드가 든 설정 화면 틀(`templates-adminframe--channel-token-empty`·`--channel-token-entered`의 같은 네 벌)이다. 넷을 열어 봤다(Read로 봤다). 다크 사진의 카드 안 표본은 라이트로 찍혔다. 미리보기의 모드 전역값이 문서 뿌리에 `data-mode="dark"`를 달고 브라우저는 라이트로 두는데(`web/packages/ui/src/storybook/preview.tsx`와 `web/apps/admin/visual/stories.visual.ts`를 읽었다), 표본은 명세대로 `data-mode`를 달지 않아 시스템 모드를 따르기 때문이다. 실제 관리 화면은 뿌리에 모드를 달지 않아 표본도 같은 시스템 모드를 받는다(`card_theme.mjs`가 잰 것, `ThemeCard` 머리 주석).

## 검증 결과

셀프 리뷰 전에 친 것이다(모두 도구가 찍었다).

- 린트: `uv run ruff check .`와 `uv run ruff format --check .`가 통과했다(1166 파일).
- `uv run python tools/run_checks.py`: 열 검사가 모두 Passed, 종료 0이었다(pytest 513초, web-verify 571초).
- 사진 비교: `pnpm -C web visual:admin`이 32 통과, 종료 0이었다.
- 관리 화면 e2e 전체(`pnpm -C web/apps/admin exec playwright test`): 8 통과, 1 실패였다. 실패는 `e2e/decision.e2e.ts:12`의 "멈춘 실행을 허가하면 재개 스트림이 조각으로 붙고 실행이 끝나며 도구가 실제로 불렸다"이고, 39줄의 `expect(events).toContainText("run_finished")`가 5초 동안 기다렸지만 이벤트 구역에는 `run_started`와 `run_paused`만 있었다. 34줄(재개 스트림의 `approval_granted`)과 35줄은 지났다. 그 파일만 다시 돌리니 같은 자리에서 다시 빨갰고(2 통과, 1 실패), 시험 밖 오류 하나가 `stack.ts:64`의 `rmSync(work)`가 낸 `EPERM, Permission denied`였다. 변이 표의 e2e 기준선이 끝 열 줄만 보여 못 본 정리 오류의 본문이 이것으로 보인다(같은 자리, 같은 꼴이라 어림한다).
- 같은 시험이 두 번 연속 빨갰지만 진단(`diagnosing-bugs`, 작업 규약 6)은 하지 않고 인계했다. 이 브랜치의 기준 커밋 3ee0be4f는 main의 CI가 초록이었다(`gh run list --branch main`이 찍었다). 이 PC에서 기준 커밋으로 같은 시험을 돌려 보지는 않았다.

## 인계

세션 컨텍스트가 357,789 토큰으로 인계 문턱을 넘은 채 `셀프 리뷰 직전`에 와서 계기 훅이 인계를 알렸다. `handoff.md`의 인계하지 않는 때 다섯에 들지 않았다(이 세션의 `get_session`에 `parentSessionId`가 없다). 이 세션의 지금 제목은 `feature/09-admin-settings-theme`이다. 셀프 리뷰, 커밋, PR, 병합, 회고, "다음"은 새 세션이 이 파일을 이어 쓴다.

낸 인계 지시문이다(모델 줄은 `tools/model_sweep.py feature/09-admin-settings-theme`이 찍은 값이다).

```
다음 작업: .scratch/admin-style/issues/09-admin-settings-theme.md. 설정 화면에서 테마를 고르면 바로 바뀌고, 새로 고쳐도 첫 그림부터 그 테마다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/admin-style/issues/09-admin-settings-theme.md
브랜치: feature/09-admin-settings-theme
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-29-19-admin-settings-theme.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review origin/main)부터 한다(일지 docs/journal/2026-10-29-19-admin-settings-theme.md). 셀프 리뷰 전에, 관리 화면 e2e의 e2e/decision.e2e.ts:39(허가한 뒤 이벤트 구역에 run_finished가 서지 않는다)가 전체 실행과 다시 돌린 실행에서 두 번 연속 빨갰고 아직 진단하지 않았다. diagnosing-bugs로 이 브랜치의 변경 탓인지부터 가른다. PR 본문에는 바뀐 사진 열둘과 다크 사진의 카드 표본이 라이트로 찍히는 까닭(일지 "사진 비교와 Docker")을 적는다. Docker 엔진은 다시 켜도 십수 분 뒤에 다시 죽었다. 사람이 Docker를 끄고 다시 켜도 된다고 고른 답은 이 세션의 사진 정답 만들기에 한 것이다(일지에 원문)
확인할 선행 조건: 이 PC에서 기준 커밋 3ee0be4f로 decision.e2e.ts를 돌려 보지 않아, 그 실패가 이 브랜치 전부터 있었는지 모른다(main의 CI는 3ee0be4f에서 초록이었다)
이번 요청 범위: PR과 병합까지
```

제목을 `feature/09-admin-settings-theme (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었으며(e2e 전체는 끝났다), `git worktree unlock`이 오류 없이 끝났다.

open-session을 부른다 2026-10-29T13:57:45Z

## 이어받은 세션

인계 지시문으로 연 새 세션이다. 제목을 브랜치 이름으로 바꾸고 `git worktree list`에서 이 브랜치의 워크트리를 찾아 `EnterWorktree(path)`로 들어갔다. `implement` 스킬을 디스크의 `SKILL.md`로 읽어 따랐다.

> 사용자: "`.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: .scratch/admin-style/issues/09-admin-settings-theme.md … 이어받을 상태: 인계: 셀프 리뷰 직전. … 셀프 리뷰 전에, 관리 화면 e2e의 e2e/decision.e2e.ts:39(허가한 뒤 이벤트 구역에 run_finished가 서지 않는다)가 전체 실행과 다시 돌린 실행에서 두 번 연속 빨갰고 아직 진단하지 않았다. diagnosing-bugs로 이 브랜치의 변경 탓인지부터 가른다. … 확인할 선행 조건: 이 PC에서 기준 커밋 3ee0be4f로 decision.e2e.ts를 돌려 보지 않아, 그 실패가 이 브랜치 전부터 있었는지 모른다 … 이번 요청 범위: PR과 병합까지"

### `decision.e2e.ts:39` 진단

`diagnosing-bugs`로 갈랐다. 결론은 이 브랜치와 무관하게 부하에서 흔들리는 시간 창이고, 대기열 306이 받아들여 닫은 종류라 시험도 코드도 고치지 않는다.

- 고리. 이 브랜치에서 그 시험 하나, 그 파일, 관리 화면 e2e 전체가 모두 초록이었다(1, 3, 9 통과). 그래서 `-g "멈춘 실행을 허가하면" --repeat-each 15`를 고리로 삼았고, 첫 반복에서 열다섯 가운데 여덟이 같은 39줄에서 빨갰다(러너가 찍었다). 통과한 반복도 한 번에 7.6~13.1초였다. 실패한 반복의 serve 로그에는 허가(`POST /runs/<id>/approval` 200) 뒤에 트레이스 다시 읽기(`GET /traces/<id>`)가 없었다(로그를 읽었다).
- 가설. ① PC 부하로 재개(MCP 픽스처 기동과 2초 대기)가 5초 창을 넘긴다. ② 이 브랜치의 `useStoredTheme`이나 뿌리 레이아웃의 그리기 전 스크립트가 스트림 끝 처리를 깬다. ③ 같은 serve를 함께 쓰는 반복이 쌓여 늦어진다. 이 브랜치는 `src`·`tests`·`plugins`를 바꾸지 않았다(`git diff --stat HEAD`가 비었다).
- 견줌. 변경을 공유 스태시가 아니라 비공개 참조(`refs/diag/…`)의 커밋 객체로 보관하고 워크트리를 기준 커밋 3ee0be4f로 되돌려 같은 고리를 돌리니 열다섯 모두 초록, 한 번에 6.2~7.4초였다. 변경을 되살려(되살린 트리 해시가 보관 때와 같은 `beffa88c`) 이 브랜치로 다시 돌리니 열다섯 모두 초록, 6.2~8.0초였다(셋 다 러너가 찍었다). 같은 코드가 빨강 8/15와 초록 15/15를 냈으므로 ②는 반박되고, 빨간 반복이 통과한 회차까지 느렸던 것이 ①과 맞는다. ③은 초록 반복이 열다섯까지 늦어지지 않아 반박된다. 빨간 반복 때의 부하는 재지 않았다(어림). 같은 시험의 선례는 일지 2026-10-23-50(기다림을 20초로 늘리자 초록)과 2026-10-20-20(기준 판도 같은 고리에서 빨강)이다.
- 정리. 보관 참조를 지웠다. 임시 계측은 넣지 않았다.

### 셀프 리뷰

`/code-review origin/main`. 기준 SHA 3ee0be4f, 커밋 0, 미커밋 변경 파일 22, 미추적 13(사진 넷 포함).

표준 축(sonnet·high)은 Critical·Major 없이 Minor 셋, Nit 넷을 냈다. 지적마다 근거를 본 판정이다.

- Minor 1, 고친다. `public/theme.js`와 `stores/theme.ts`의 주석이 두 벌 목록의 "어긋남"을 단위 시험이 잡는다고 넓게 적었다. 시험은 `THEMES`의 키마다 달리는지와 정한 음성 값만 보아 `THEMES`에 더하기와 저장 키 바꾸기만 잡고, 빼기는 잡지 않는다(시험 파일을 읽었다. 그 파일의 머리 주석은 이미 "더하거나 … 바꾸고"로 맞게 적었다). 명세 255줄의 같은 문장은 사용자가 승인한 명세라 고치지 않는다.
- Minor 2, 고친다. 실패 줄의 위치를 함께 든 표지는 여덟이 아니라 일곱이다(`grep`으로 `expect_output`의 `<파일>:<줄>:`을 세니 115·130·148·301·317·350·381줄). 프로브 README 행과 이 일지 "변이 표" 절을 고친다.
- Minor 3, 고친다. `HomePage.test.tsx`의 제목 "… 그 밖의 상태는 저장되지 않는다"가 테마를 심어 두는 본문과 어긋난다.
- Nit 4, 고친다. `organisms/Settings` 머리 주석의 "그 모양을 쓰지 않아"가 무엇이 다른지 말하지 않았다. `legend`의 클래스는 두 `h2`와 같은 글자이고(`ChannelTokenForm.tsx:24`, `ClearTokens.tsx:11`을 grep했다) 다른 것은 흐린 설명 줄이 없는 것이다.
- Nit 5, 고친다. `ThemeCard` 머리 주석의 "누르면 카드를 누른 것이다"는 시험이 밟지 않는다. 페이지 시험은 라디오를 누르고(`SettingsPage.theme.test.tsx:63` 등) e2e는 `.check()`이며 스토리는 `inert` 속성만 본다(grep했다). 명세의 테마 카드 문장은 표본을 눌렀을 때의 동작을 요구하지 않아(명세 243줄을 읽었다) 시험을 더하지 않고 그 문장을 어림으로 적는다.
- Nit 6, 남긴다. `ThemeCard`의 `name`(화면 이름)과 `group`(HTML `name`)은 JSDoc이 풀어 주고, `apply`는 모듈 밖에 나가지 않는 이름이다.
- Nit 7, 남긴다. 시험 셋이 저장 키 글자를 저마다 적는 것은 디스크 형식(명세 "저장"의 키)을 글자로 못 박는 뜻이다.

명세 축(본 세션 모델)은 Critical·Major 없이 Minor 둘, Nit 셋을 냈고, 표준 축의 Minor 2(여덟)와 Nit 5(누르기)를 따로 짚었다. 지적마다 근거를 본 판정이다.

- Minor (a), 고친다. 루트 `README.md` 구조 줄이 `stores/(토큰)`이고 `public/`이 없었다(그 줄을 읽었다). `stores/(토큰과 테마)`와 `public/(첫 그림 전에 테마를 다는 스크립트)`로 고친다.
- Minor (c), 고친다. 카드 스토리가 갈래를 잰 컨테이너 폭(`atLeastSplit`)으로 골랐다. 명세 294줄 "갈래의 단언"은 넓은·좁은 프로젝트로 단언하고 "이 단언이 둘의 어긋남도 잡는다"고 적어, 넓은 창에서 데코레이터의 컨테이너가 좁게 서면 두 줄 갈래를 단언해 지나가는 길을 막아야 한다. 같은 폴더의 `AdminFrame.stories.tsx`·`EntryFrame.stories.tsx`처럼 파일 안의 `rootToken`과 창 폭 판정(`isWide`)으로 고른다. 그 어긋남을 넣는 변이(넓은 창에서 데코레이터의 컨테이너를 600px로 좁힌다)를 변이 표 끝에 스물넷째로 더했다. 옛 판정이 그 변이에서 초록인지는 재지 않았다(명세 축이 코드를 읽고 짚은 것이다).
- Nit, 고친다. `admin-token.e2e.ts`의 키 주석 "토큰 밖에 그 저장소에 남는 유일한 것"이 토큰도 거기 남는다고 읽혀 "앱이 그 저장소에 남기는 유일한 것이다. 토큰은 거기 없다."로 고친다. 두 축 모두 앱 소스에서 localStorage에 쓰는 곳이 `stores/theme.ts` 하나라고 grep으로 봤다.
- Nit, 고친다. `organisms/Settings`와 `pages/SettingsPage` 머리 주석이 테마를 "스토어"에서 읽는다고 적었다. 지금 테마의 원천은 문서 뿌리의 속성이고 스토어에 복사하지 않는다(티켓 "이 티켓이 정한 것" 셋째). 두 주석을 "지금 테마(문서 뿌리의 속성)와 토큰 스토어의 값", "지금 테마(`stores/theme`)와 토큰 스토어"로 고친다.
- Nit, 고친다. `stores/theme.ts`의 `restoreStoredTheme` 독스트링이 dev의 Strict Mode 재마운트도 되살린다고 단정했다. e2e는 `next start`에서만 돌고 근거는 설치본 가이드를 읽은 것이라, "같은 길로 되살린다고 본다(설치본 Next 가이드를 읽었다. dev 에서는 재지 않았다)"로 고친다.
- 명세 축이 표본 누르기를 최소 페이지의 chromium에서 따로 재 보니 라벨의 라디오가 골라졌다고 알렸다. 커밋하지 않은 스크래치 스크립트라 근거로 들지 않고, `ThemeCard` 주석은 어림으로 둔다.

반영으로 새로 쓴 사실 문장이다. PR 직전 `bug-perf-review`의 브리프에 밀 주장으로 넘긴다.

- `public/theme.js`: "THEMES 에 테마를 더하거나 저장 키를 바꾸고 이 파일을 고치지 않으면 stores/theme.prepaint.test.ts 가 빨갛다. THEMES 에서 테마를 빼고 이 목록에 남긴 것은 그 시험이 잡지 않는다."
- `stores/theme.ts` 머리: "그 스크립트의 단위 시험(stores/theme.prepaint.test.ts)이 이 모듈의 상수와 맞대어, `THEMES` 에 테마를 더하거나 저장 키를 바꾸고 스크립트를 고치지 않은 어긋남을 잡는다."
- `stores/theme.ts` `restoreStoredTheme`: "dev 의 Strict Mode 가 다시 마운트하며 지운 것도 같은 길로 되살린다고 본다(설치본 Next 가이드를 읽었다. dev 에서는 재지 않았다)."
- `organisms/Settings.tsx`: "테마는 `fieldset` 의 `legend` 가 머리이고 흐린 설명 줄이 없어 그 모양이 아니다. 같은 모양이 둘뿐이라 묶지 않는다."
- `molecules/ThemeCard.tsx`: "표본을 누르면 그 누름이 카드(라벨)에 가 라디오가 골라진다고 본다(어림. 시험은 `inert` 속성만 본다)."
- `e2e/admin-token.e2e.ts`: "앱이 그 저장소에 남기는 유일한 것이다. 토큰은 거기 없다."
- `organisms/ThemePicker.stories.tsx` `isWide`: "갈래를 잰 컨테이너 폭으로 고르지 않는다. 그러면 넓은 창에서 데코레이터의 컨테이너가 본문 칸보다 좁게 서도 두 줄 갈래를 단언해 지나간다."
- 루트 `README.md`: "stores/(토큰과 테마), public/(첫 그림 전에 테마를 다는 스크립트)"
- 변이 표 스물넷째의 주석과 프로브 README 행의 스물넷째 문장.

다시 돌린 것: 변이 표 `--check`가 "변이 24 모두 원문이 한 번씩 있다"였고, 스토리를 겨누는 열여섯째~스물둘째와 스물넷째를 돌려 기준선 둘이 초록이고 "변이 8 모두 기대대로"였다(도구가 찍었다). 뒤에 `git status`에 변이가 남지 않았다. 손으로 치는 검증 다섯은 커밋의 pre-commit으로 갈음한다.
