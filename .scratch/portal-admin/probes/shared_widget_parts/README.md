# shared_widget_parts: 위젯의 화면 부품을 공유 패키지로 옮겨 본 실험

ADR 0065 Consequences "재지 않은 것"이 portal-admin의 명세에 넘긴 물음 둘을 본다. 위젯 앱(`web/apps/widget`)의 화면 부품을 `web/packages/` 아래의 공유 패키지로 옮기는 데 드는 일이 얼마인가, 그리고 옮긴 부품이 위젯 앱의 사진 비교를 그대로 통과하는가.

**범위.** 실제로 옮기는 일은 widget-login-state가 로그인 상태·고지·밝기 스위치의 화면을 지은 뒤다(ADR 0065 결정 "미리보기"). 이 실험은 2026-11-16의 부품(기준 커밋 아래)으로 "옮기는 방식이 서는가"를 본 것이다. Tailwind 클래스 훑기, 스토리와 사진의 이름, 린트 경계, 타입 검사, 빌드, 다른 앱에서 쓰기까지다. 그때의 부품 수와 줄 수는 지금과 다르다.

**근거의 종류.** 이 폴더의 결과는 패치를 붙이고 아래 명령을 사람이 하나씩 치는 실험에서 나왔다. `compare_index.mjs`와 `css_rules.mjs`는 그중 두 걸음을 판정하는 보조 스크립트다. `preview_shield.mjs`는 기대와 견줘 종료 코드를 내지만, 패치를 붙이고 Storybook을 지은 체크아웃이 있어야 돌고 판마다 한 번씩만 돌렸다. 패치를 붙이는 데서 결과까지를 스스로 다시 내는 프로브는 이 폴더에 없다. 그래서 아래 결과는 모두 "손으로 봤다"다(2026-11-16, 이 PC, 한 번씩). 줄 머리의 표시는 이렇다.

- **[손]** 손으로 봤다. 그 줄이나 그 절의 머리에 적은 명령을 쳐서 본 것이다.
- **[코드]** 코드를 읽었다. 파일과 줄을 함께 적는다. 판은 기준 커밋이다.
- **[어림]** 돌려 보지도 읽어 확인하지도 않은 해석이나 수다.

기준 커밋: `02dcfe97d26264d30a8a15b9cd11864446041dce` (`git rev-parse HEAD`, 브랜치 `worktree-agent-a6f8a3e38a870fe3f`).

`.scratch/portal-admin/probes/README.md`의 표가 이 폴더를 한 줄로 든다. 그 파일은 이 실험이 만들지 않았고, 나란히 돈 프로브와 겹치지 않게 본 세션이 그 줄을 적었다.

## 파일

| 파일 | 무엇인가 |
|---|---|
| `move.patch` | 옮기기만 한 상태. 기준 커밋에서 `git diff -M --binary HEAD`로 냈다. 이 상태에서 위젯 쪽 검사가 모두 초록이었다 |
| `move-with-consumer.patch` | 옮기기에 소비자 확인(관리 화면 앱의 임시 파일 셋과 설정 넷)을 더한 누적 패치. `move.patch` 대신 기준 커밋에 붙인다. 이 상태에서는 관리 화면의 스토리 하나(`InAdminFrame`)가 일부러 빨갛다(아래 "소비자 확인") |
| `compare_index.mjs` | 옮기기 전과 뒤의 위젯 Storybook `index.json`을 견준다. 스토리 id가 같은지, 뒤의 빌드가 스토리를 패키지에서 실었는지. 종료 코드는 같으면 0, 측정했는데 다르면 1, 측정이 아니면 2다(파일을 읽지 못했다, 뒤의 빌드가 패키지에서 싣지 않았다) |
| `css_rules.mjs` | 지은 앱의 CSS에 클래스의 규칙이 있는지 본다. 대조 클래스로 CSS를 읽었는지를 먼저 본다. 종료 코드는 기대와 같으면 0, 기대와 다른 클래스가 있으면 1, 측정이 아니면 2다(경로를 읽지 못했다, 대조 클래스의 규칙이 없다) |
| `move-with-consumer-inert.patch` | 옮기기와 소비자 확인에 미리보기를 가리는 갈래와 긴 내용의 스토리를 더한 누적 패치. 다른 두 패치 대신 기준 커밋에 붙인다(아래 "미리보기를 그림으로 가렸을 때") |
| `preview_shield.mjs` | 지은 관리 화면 Storybook을 chromium으로 열어 가린 미리보기를 실제 Tab과 실제 마우스로 본다(같은 절) |

스크립트 셋의 종료 코드 가름(0은 기대와 같다, 1은 측정했는데 다르다, 2는 측정이 아니다)은 PR 직전 리뷰 뒤에 맞췄다. 그 전의 `compare_index.mjs`는 측정이 아닌 끝도 1이었고, 두 보조 스크립트는 준 경로를 읽지 못하면 잡지 않은 예외로 끝났다 **[코드]**(고치기 전 판은 커밋 `fd5beccec`). 고친 뒤 지어낸 입력 아홉 사례로 갈래마다의 문구와 종료 코드를 함께 봤다 **[손]**. `compare_index.mjs`는 같다(0), 스토리 id가 다르다(1), 뒤에 옮기기 전 빌드를 줬다(2), 없는 파일(2), JSON이 아닌 파일(2)이고, `css_rules.mjs`는 규칙이 있다(0), 없어야 하는데 있다(1), 대조 클래스의 규칙이 없다(2), 없는 경로(2)다. 아홉 모두 그 갈래의 문구가 나왔고 종료 코드가 괄호와 같았다. 사례를 돌린 스크립트는 세션 스크래치패드에 있고 저장소에 두지 않았다.

두 패치가 기준 커밋에 붙는지는 임시 인덱스로만 봤다 **[손]**. `GIT_INDEX_FILE=<임시 파일> git read-tree HEAD` 뒤 `git apply --cached <패치>`가 둘 다 오류 없이 끝났고, `move-with-consumer.patch`를 붙인 인덱스와 작업 트리의 `git diff --stat -- web`이 비었다. 새 체크아웃에 `git apply`로 붙여 처음부터 다시 돌려 보지는 않았다.

## 다시 돌리는 법

저장소 루트에서 친다. 이 실험은 워크트리 세션이라 `-C`에 절대 경로를 주고 하나씩 쳤다. 사진 비교는 Docker가 떠 있어야 하고, e2e는 `uv`가 실제 `serve`를 띄운다. 실제 모델을 부르는 시험(`-m llm*`)은 돌리지 않는다.

```bash
# 1. 기준선(옮기기 전)
git rev-parse HEAD                       # 02dcfe97d26264d30a8a15b9cd11864446041dce
pnpm -C web install --frozen-lockfile
pnpm -C web verify
pnpm -C web visual:widget
cp web/apps/widget/storybook-static/index.json /tmp/index-before.json
pnpm -C web/apps/widget exec playwright test

# 2. 옮기기
git apply .scratch/portal-admin/probes/shared_widget_parts/move.patch
pnpm -C web install --frozen-lockfile

# 3. 옮긴 뒤의 검사
pnpm -C web verify
pnpm -C web visual:widget
git status --short -- web/apps/widget/visual      # 비어야 한다(정답 사진이 바뀌지 않았다)

# 4. 스토리 id 와 실린 자리
node .scratch/portal-admin/probes/shared_widget_parts/compare_index.mjs /tmp/index-before.json web/apps/widget/storybook-static/index.json

# 5. e2e
pnpm -C web/apps/widget exec playwright test

# 6. 소비자 확인. 누적 패치는 기준 커밋에 붙으므로 2 에서 붙인 패치를 먼저 걷는다
git apply -R .scratch/portal-admin/probes/shared_widget_parts/move.patch
git apply .scratch/portal-admin/probes/shared_widget_parts/move-with-consumer.patch
pnpm -C web install --frozen-lockfile
pnpm -C web run typecheck
pnpm -C web run lint
pnpm -C web run format
pnpm -C web/apps/admin build
node .scratch/portal-admin/probes/shared_widget_parts/css_rules.mjs web/apps/admin/.next/static present truncate overflow-y-auto max-w-5/6 items-end justify-end self-end mt-auto min-h-0 h-full pl-4 focus-visible:-outline-offset-2
pnpm -C web exec vitest run --project admin-storybook-wide --project admin-storybook-narrow --reporter=verbose WidgetPreviewProbe
```

적은 명령 가운데 그대로 치지 않은 것이 넷이다. 2와 6의 `git apply`는 위 "파일"에 적은 대로 임시 인덱스로만 봤다. 6의 `git apply -R`은 치지 않았다(이 실험은 옮긴 트리에 소비자 파일을 손으로 더해 6의 상태로 갔다). 2의 `--frozen-lockfile`은 치지 않았고(옮길 때는 `pnpm -C web install`로 잠금 파일을 새로 냈다), 6의 상태에서 친 `pnpm -C web install --frozen-lockfile`은 "Already up to date"였다 **[손]**. `/tmp` 자리에는 세션 스크래치패드의 경로를 썼다.

대조를 다시 보려면 CSS의 `@import "@agent-os/widget-ui/source.css";` 한 줄을 지우고 같은 명령을 친다(아래 "대조"). 위젯은 `web/apps/widget/styles/widget.css`, 관리 화면은 `web/apps/admin/styles/admin.css`다. 6의 `css_rules.mjs`는 그때 `present`를 `absent`로 바꾼다.

## 본 판

Node 24.19.0, pnpm 11.24.0, TypeScript 5.9.3, React 19.3.0, Next 16.3.6(Turbopack), Tailwind 4.3.3(`@tailwindcss/postcss`, `@tailwindcss/vite`), Vite 8.3.1, Storybook 10.6.1, Vitest 5.0.2, axe-core 4.14, ESLint 10.11.0, typescript-eslint 8.70.1, eslint-plugin-boundaries 7.2.0, Playwright 1.63.0과 사진 비교 이미지 `mcr.microsoft.com/playwright:v1.63.0-noble@sha256:bc6ab0d6d44ff4826e4cb8c1e6d801e185bfc42bb0753f8e2a30efc70db054c7`, Docker 29.9.2, Windows 10 Home 10.0.19045.

## 옮긴 것

수는 `git diff -M --numstat HEAD`(옮기기만 한 상태)에서 셌다 **[손]**. 모두 34파일, 더한 줄 137, 뺀 줄 31이다.

- **`git mv`로 옮긴 파일 20.** `web/apps/widget/`에서 `web/packages/widget-ui/src/`로, 아래 폴더 모양을 그대로 두고 옮겼다. 17파일은 한 글자도 바뀌지 않았고(이름 바꾸기 100%), 3파일을 고쳤다(더한 줄 8, 뺀 줄 3).
  - 컴포넌트 10: `components/molecules/{ComposerBand,ToolRow,Welcome}.tsx`, `components/organisms/{ApprovalCard,Composer,Conversation,FailureAlert,TopBar}.tsx`, `components/templates/WidgetFrame.tsx`, `components/pages/WidgetScreen.tsx`
  - 스토리 5: `ComposerBand`, `ApprovalCard`, `Conversation`, `FailureAlert`, `WidgetScreen`의 `*.stories.tsx`
  - 값의 모양과 규칙 5: `lib/{approval,chars,conversation,limit,reconnect}.ts`
- **새 패키지의 파일 4, 72줄.** `package.json` 24, `tsconfig.json` 13, `src/index.ts` 28, `src/styles/source.css` 7.
- **고친 설정 5파일.**
  - `web/apps/widget/package.json` 더한 줄 1: 의존성 `@agent-os/widget-ui`
  - `web/apps/widget/styles/widget.css` 더한 줄 2: 주석 한 줄과 `@import "@agent-os/widget-ui/source.css";`
  - `web/apps/widget/.storybook/main.ts` 더한 줄 2, 뺀 줄 1: `stories`에 패키지의 스토리 글롭
  - `web/tools/visual.test.ts` 더한 줄 2, 뺀 줄 1: 위젯이 기대는 워크스페이스 패키지의 정확한 목록에 새 패키지(검사를 고친 자리다. 아래 "고친 검사")
  - `web/pnpm-lock.yaml` 더한 줄 28: 새 importer와 위젯의 의존성
- **고친 import.** 앱 쪽은 5파일(`components/pages/{ConnectedWidget.tsx,drivers.ts,useConversation.ts}`, `lib/{rejection,storage}.ts`)에서 더한 줄 22, 뺀 줄 26이다. 옮긴 모듈을 가리키던 import 문 10개가 `@agent-os/widget-ui`에서 들이는 import 문 5개가 됐다. 뺀 줄에는 `useConversation.ts`에 있던 `Restore` 타입 선언이 주석까지 5줄 든다. 패키지 쪽은 import 문 3개다. `lib/conversation.ts`와 `lib/reconnect.ts`의 `../api/runs`가 `@agent-os/api-client`가 됐고(앱의 `api/runs/index.ts`가 그 타입을 다시 내보내던 것이다), `WidgetScreen.tsx`의 `./useConversation`을 지우고 `Restore` 타입을 그 파일에 선언했다. 옮긴 파일끼리의 상대 import는 폴더 모양이 같아 한 줄도 바뀌지 않았다.

### 값의 모양과 규칙이 함께 온 까닭

화면 부품이 `lib/`의 다섯 모듈을 타입과 함수로 읽는다 **[코드]**(옮긴 컴포넌트의 import 문). `Exchange`·`Decision`·`Approval`·`Outcome` 같은 대화의 모양, `argsText`·`charNote`·`limitSentence`·`waitText` 같은 글자를 내는 함수다. 앱에 남기면 패키지가 앱을 import하게 된다. 그런데 `lib/conversation.ts`·`limit.ts`·`reconnect.ts`에는 위젯 앱의 대화를 돌리는 쪽(`useConversation`, `drivers`, `lib/storage`, `lib/rejection`)만 쓰는 것도 함께 있다. 리듀서 `reduce`, `INITIAL`, `phaseOf`, 재접속 간격 `reconnectDelay`·`SILENCE_MS`, 상한의 `startWait`·`remainingAt`·`untilNextTick` 등이다. 이 실험은 모듈을 쪼개지 않고 통째로 옮기고, 앱이 쓰는 것을 `src/index.ts`가 내보냈다. 모듈을 모양과 화면의 글(패키지)과 대화를 돌리는 규칙(앱)으로 쪼개는 길은 해 보지 않았다.

### 스토리와 테스트를 어디 뒀나

- **스토리는 부품과 함께 패키지로 갔다.** 스토리는 컴포넌트 옆에 두는 것이 이 저장소의 규약이고(ADR 0026), 다른 앱이 부품을 고칠 때도 같은 자리에서 스토리를 본다. 위젯의 Storybook(`apps/widget/.storybook/main.ts`)이 패키지의 스토리를 글롭 하나로 싣는다. 그래서 스토리 시험의 프로젝트(`widget-storybook`), 미리보기(위젯의 CSS와 보통 밀도), 사진 비교의 폴더(`apps/widget/visual/`)와 정답 사진이 모두 그대로다. `web/vitest.config.ts`와 `web/package.json`의 명령은 고치지 않았다.
- **페이지 시험은 앱에 남았다.** `apps/widget/components/pages/Widget*.test.tsx` 일곱은 `WidgetPage`를 jsdom과 msw로 통째로 돌려 연결된 페이지를 본다. 옮긴 부품만 보는 단위 시험은 지금 없다.
- 해 보지 않은 다른 길 **[어림]**. 패키지가 자기 Storybook과 스토리 시험 프로젝트와 사진 폴더를 갖는 길은 `web/vitest.config.ts`, 루트 `package.json`의 `visual:*`, CI의 `visual` 잡, 정답 사진 77장의 자리, 규약 문서를 함께 고쳐야 한다. 스토리를 앱에 남기는 길은 스토리가 컴포넌트 옆에 있다는 규약을 깬다.

## 검사 결과: 옮기기 전과 뒤

모두 **[손]**이고 2026-11-16에 한 번씩 쳤다(e2e의 기준선만 세 번). 요약 줄은 출력에서 옮겼다.

| 명령 | 옮기기 전 | 옮긴 뒤(`move.patch`) |
|---|---|---|
| `pnpm -C web verify` | 종료 0. Test Files 124 passed (124), Tests 2754 passed와 1 skipped (2755), 543초 | 종료 0. Test Files 124 passed (124), Tests 2754 passed와 1 skipped (2755), 415초 |
| `pnpm -C web exec vitest run --project widget-storybook --reporter=verbose` | 종료 0. 5파일, 43 passed | 종료 0. 5파일, 43 passed. 파일 경로가 `../../packages/widget-ui/src/…` |
| `pnpm -C web visual:widget` | 종료 0. 44 passed (4.7m) | 종료 0. 44 passed (1.2m). `git status --short -- web/apps/widget/visual`이 비었다 |
| `compare_index.mjs` | 스토리 43, 패키지에서 실은 것 0 | 스토리 43, 패키지에서 실은 것 43, 스토리 id가 같다 |
| `pnpm -C web/apps/widget exec playwright test` | 세 번 쳤다. 종료 1(serve가 서지 않았다), 종료 1(17 passed, 2 failed), 종료 0(19 passed, 48.2s) | 한 번 쳤다. 종료 0. 19 passed (1.2m) |

- **바뀐 사진은 없다.** 사진 44건(스토리 42와 따로 둔 시험 2)이 정답 사진 77장과 그대로 맞았다. 정답 사진의 이름은 `<스토리 id>-<모드>.png`이고(`apps/widget/visual/stories.visual.ts` 44줄), 스토리 id는 스토리 파일의 `title:`에서 나온다. 다섯 스토리 파일이 `title`을 글자로 적어 둬서(`molecules/ComposerBand`, `organisms/ApprovalCard`, `organisms/Conversation`, `organisms/FailureAlert`, `pages/WidgetScreen`) 파일을 옮겨도 id가 같았다 **[코드]**. `title`을 적지 않은 스토리였다면 id가 경로에서 나와 바뀌었을 것이다 **[어림]**.
- **사진이 옮긴 소스를 찍었는가.** `visual:widget`은 돌 때마다 Storybook을 새로 짓는다(`web/tools/visual.ts`) **[코드]**. 옮긴 뒤 지은 `index.json`의 43스토리가 모두 `packages/widget-ui/src/`에서 실렸다(`compare_index.mjs`의 표지) **[손]**.
- **옮기기 전의 e2e 실패 둘은 옮기기와 무관하다.** 첫 번은 `uv sync` 직후라 `serve`가 60초 안에 서지 못했다. `serve --help`로 import를 한 번 데운 뒤의 둘째 번은 `widget.e2e.ts` 33줄과 86줄의 시험이 5000ms 제한에 걸렸고, 코드를 고치지 않고 다시 친 셋째 번은 19건이 모두 통과했다. 까닭은 차가운 시작으로 본다 **[어림]**. 옮긴 뒤에는 첫 번에 19건이 통과했다.
- e2e는 iframe 방식(Next 빌드)과 페이지 안 방식(`tools/element.ts`의 Vite 번들, `widget.css?inline`)을 함께 본다 **[코드]**(`e2e/widget.e2e.ts`, `e2e/element.e2e.ts`). 위젯의 CSS가 지어지는 길 셋(Next, Storybook, 페이지 안 번들)이 모두 옮긴 뒤에 초록이었다.

### 대조

"초록"이 옮긴 패키지를 실제로 봤다는 것을 가르려고 둔 갈래다. 모두 **[손]**.

- **Tailwind가 패키지의 소스를 훑는 것은 `source.css`를 들인 한 줄 때문이다.** `widget.css`에서 그 `@import`를 지우면 `widget-storybook`이 종료 1이었다. `Test Files 3 failed | 2 passed (5)`, `Tests 31 failed | 12 passed (43)`이고 실패마다 "디자인 토큰에 없는 클래스를 그렸다: 규칙 없는 클래스 items-end, …, truncate"가 찍혔다. 같은 상태의 `pnpm -C web visual:widget`도 종료 1이었다. `31 failed`, `13 passed (1.8m)`이고 실패는 "스토리 … 를 그리다 예외가 나 오류 화면이 떴다"였다(사진의 픽셀이 달라서가 아니라 스토리가 던져서 빨갰다). 줄을 되돌리면 위 표의 초록이다. 디자인 토큰 CSS의 `@source ".."`가 옆 패키지까지 훑는다는 다른 해석은 이 갈래에서 서지 않는다.
- **타입 검사가 패키지를 본다.** 패키지의 `tsconfig.json`에 `allowImportingTsExtensions`가 없던 첫 판에서 `pnpm -C web run typecheck`가 `packages/widget-ui`에서 `../ui/src/themes.ts(32,34): error TS5097`로 종료 1이었다. 그 옵션을 더한 뒤 종료 0이다.
- **린트가 패키지 안의 층 경계를 본다.** `packages/widget-ui/src/components/molecules/`에 organisms를 import하는 파일을 심으니 `boundaries/dependencies`가 "Dependencies to elements of type "organism" are not allowed in elements of type "molecule""로 잡았다. 같은 파일에 넣은 패키지에서 앱으로 가는 상대 import(`../../../../../apps/widget/lib/build`)는 잡지 않았다. 심은 파일은 지웠다.
- **정확한 목록의 시험이 의존성을 본다.** 위젯에 의존성을 더한 직후 `web/tools/visual.test.ts`의 위젯 목록 시험이 `+ "@agent-os/widget-ui": "/web/packages/widget-ui"`로 빨갰다.

### 고친 검사

검사나 기준 그림이나 린트 규칙을 느슨하게 고친 것은 없다. 옮기려면 고쳐야 하는 자리가 둘이었다.

- `web/tools/visual.test.ts`: 위젯(과 소비자 확인에서는 관리 화면)이 기대는 워크스페이스 패키지를 정확한 맵으로 견준다. 새 의존성을 더하면 그 줄을 더해야 한다. 사진 비교의 컨테이너가 그 패키지를 이어야 해서 있는 시험이다.
- `web/apps/widget/.storybook/main.ts`: `stories` 글롭에 패키지의 자리를 더했다. 더하지 않으면 스토리 43과 사진 42가 통째로 빠진다. 지금은 앱에 스토리가 남지 않아 `No story files found for the specified pattern: apps\widget\components\**\*.stories.tsx` 경고가 뜬다 **[손]**.

기준 그림은 한 장도 고치지 않았다.

## 소비자 확인

관리 화면 앱(`web/apps/admin`)에 임시 파일 셋을 두고 `@agent-os/widget-ui`의 `WidgetScreen`을 값만 주어 그렸다. 상태는 `move-with-consumer.patch`다. 모두 **[손]**.

- 더한 것: `apps/admin/package.json`의 의존성 한 줄, `apps/admin/styles/admin.css`의 주석과 `@import "@agent-os/widget-ui/source.css";` 두 줄, `web/tools/visual.test.ts`의 관리 화면 목록 한 줄, 잠금 파일 세 줄, 그리고 새 파일 셋(`components/pages/WidgetPreviewProbe.tsx` 64줄, 그 스토리 61줄, `app/widget-preview-probe/page.tsx` 5줄).
- **타입 검사, 린트, 형식, 빌드가 통과했다.** `pnpm -C web run typecheck`, `pnpm -C web run lint`, `pnpm -C web run format`이 종료 0이고, `pnpm -C web/apps/admin build`가 종료 0으로 `/widget-preview-probe`를 정적 경로로 지었다. 타입 우회는 쓰지 않았다.
- **스타일이 실린다.** 관리 화면의 스토리 시험(`admin-storybook-wide` 1280px, `admin-storybook-narrow` 320px)에서 `Standalone`과 `Dark`가 두 폭 모두 통과했다. 미리보기의 클래스 판정, axe(관리 화면이 켠 `target-size` 포함), 가로 스크롤 검사를 지났고, play가 본 것은 셋이다. 위젯의 `main`이 `overflow-y: auto`다(위젯 화면 부품의 소스에만 있는 클래스). 제목의 글자 크기가 15px다(감싼 요소의 `data-density="regular"`가 넓은 창의 문서 뿌리가 고른 촘촘 14px을 이긴다). 문서는 밝은데 감싼 요소만 `data-mode="dark"`이면 위젯 창의 바탕색이 밝을 때와 다르다.
- **대조.** `admin.css`의 `@import` 줄을 지우면 스토리 여섯이 모두 "규칙 없는 클래스 focus-visible:-outline-offset-2, h-full, items-end, justify-end, max-w-5/6, min-h-0, mt-auto, overflow-y-auto, pl-4, self-end"로 실패했다(`Tests 6 failed (6)`). 그 상태의 `next build`는 그대로 종료 0이었고, `css_rules.mjs`로 본 지은 CSS에 그 열 클래스의 규칙이 없었다(295,926자). 줄이 있으면 열 클래스가 모두 있다(296,331자). 곧 빌드는 이 실수를 잡지 못하고 스토리 시험이 잡는다.
- **막는 것 하나: `main`이 겹친다.** 관리 화면의 틀(`AdminFrame`) 안에 위젯 화면을 둔 스토리 `InAdminFrame`은 두 폭 모두 axe 위반 셋으로 실패했다. `landmark-main-is-top-level`, `landmark-no-duplicate-main`, `landmark-unique`다. 옮긴 `WidgetFrame`이 대화 자리를 `<main>`으로 그리는데 틀의 본문도 `<main>`이다. ADR 0065의 미리보기는 양식 옆, 곧 틀의 본문 안에 선다. 그 스토리를 패치에 그대로 뒀다. 위젯의 `TopBar`는 `<h1>`을 그려 화면의 `<h1>`과 둘이 되지만 axe는 그것을 위반으로 내지 않았다.
- 소비자 상태에서 관리 화면의 스토리 시험과 페이지 시험 전부(`--project admin-storybook-wide --project admin-storybook-narrow --project pages`)는 `Test Files 2 failed | 31 passed (33)`, `Tests 2 failed | 281 passed (283)`이었다. 실패 둘은 위의 `InAdminFrame`이다. `tools/visual.test.ts`는 6건 통과였다.
- 그리려면 감싼 요소에 `data-theme`, `data-mode`, `data-density="regular"`를 달고 높이를 줘야 했다. `WidgetFrame`은 `h-full`로 자기 자리를 채운다 **[코드]**(`components/templates/WidgetFrame.tsx` 15줄). 관리 화면의 문서 뿌리는 밀도를 달지 않는다.

**결과를 본 뒤 바꾼 판정 기준 둘.** `Standalone`의 play는 처음에 제목의 `truncate`(text-overflow)를 "위젯에만 있는 클래스"의 표지로 봤다. 대조에서 빠진 클래스의 목록에 `truncate`가 없어(관리 화면의 CSS에 이미 있다) 표지를 그 목록에 있는 `overflow-y-auto`로 바꿨다. `Dark`의 play는 처음에 문서 뿌리의 `data-mode`가 `light`라고 단언했는데 관리 화면의 Storybook은 뿌리에 모드를 달지 않아(값이 `undefined`) 계산된 `color-scheme`이 `light`인지로 바꿨다.

## 미리보기를 그림으로 가렸을 때

위 "소비자 확인"이 막는 것으로 적은 `main` 겹침을, 옮긴 부품을 고치지 않고 감싸는 쪽에서 가려 푸는 길을 봤다(아래 "명세가 미리 정해야 할 것" 7번의 "다른 길" 가운데 하나다). portal-admin 명세 "미리보기"는 미리보기 안의 위젯이 보기만 하는 그림이고, 그 안의 단추와 입력창이 포커스를 받지 않으며, 화면 읽기 프로그램에는 "미리보기, 저장하지 않은 값으로 그린 위젯" 한 줄로 읽힌다고 이미 적는다. 2026-11-16에 이 PC에서 봤다.

**고친 것.** 임시 소비자 파일 둘뿐이다. `apps/admin/components/pages/WidgetPreviewProbe.tsx`에 가리는 방법을 고르는 값 `shield`를 더했고, 그 스토리 파일에 관리 화면의 틀(`AdminFrame`) 안에 화면의 `h1`, 위젯 화면, "저장" 단추를 차례로 둔 스토리 넷을 뒀다. `web/packages/widget-ui` 아래는 한 글자도 고치지 않았다 **[손]**(임시 인덱스에 `move-with-consumer.patch`를 붙이고 작업 트리와 견준 `git diff --stat -- web`이 그 두 파일만 냈다). 앞 절의 `InAdminFrame`에는 "저장" 단추와 play가 없었다. 이 절에서 그 둘을 더했고 위반 셋은 그대로 났다. 아래 "휠과 클릭"을 보려고 같은 두 파일에 셋을 더 뒀다. 미리보기의 높이를 넘는 내용을 고르는 값 `long`(첫 화면의 긴 안내, 긴 대화), "새 대화"의 처리기가 불린 횟수를 감싼 바깥 요소의 `data-new-conversation-calls`로 내는 것, 그리고 긴 내용의 스토리 넷이다.

| 파일 | 무엇인가 |
|---|---|
| `move-with-consumer-inert.patch` | 옮기기와 소비자 확인에 이 절의 갈래를 더한 누적 패치. 다른 두 패치 대신 기준 커밋에 붙인다. 이 상태에서는 관리 화면의 스토리 넷(`InAdminFrame`, `ShieldedHidden`, `LongIntroInAdminFrame`, `LongTalkInAdminFrame`)이 일부러 빨갛다 |
| `preview_shield.mjs` | 지은 관리 화면 Storybook을 chromium으로 열어 키보드의 Tab을 실제로 누르고 접근성 트리를 읽는다. 긴 내용의 스토리에서는 실제 마우스로 "새 대화"를 누르고 휠을 굴린다. 갈래마다의 기대와 견줘 종료 코드로 낸다(기대와 다르면 1, 표지가 없는 회차가 있으면 2) |

새 패치가 기준 커밋에 붙는지도 임시 인덱스로만 봤다 **[손]**. `git apply --cached`가 오류 없이 끝났고 그 인덱스와 작업 트리의 `git diff --stat`이 비었다.

### 갈래

| 갈래 | 스토리 | 바깥 요소 | 위젯을 감싼 안쪽 요소 |
|---|---|---|---|
| 대조 | `InAdminFrame` | 역할도 이름도 없다 | 없다 |
| A | `ShieldedBoth` | `role="img"`와 `aria-label="미리보기, 저장하지 않은 값으로 그린 위젯"` | `aria-hidden="true"`와 `inert` |
| B | `ShieldedInert` | A와 같다 | `inert`뿐 |
| C | `ShieldedHidden` | A와 같다 | `aria-hidden="true"`뿐 |

폭은 관리 화면의 스토리 시험이 쓰는 둘이다. `admin-storybook-wide`(1280×900)와 `admin-storybook-narrow`(320×640).

**본 판.** axe-core 4.14.0(설치본이 이 하나다), chromium 153.0.8010.12(`preview_shield.mjs`가 `browser.version()`으로 찍었다), Playwright 1.63.0, Storybook 10.6.1, `@testing-library/dom` 10.4.2, React 19.3.0. 스토리 시험의 브라우저도 같은 Playwright 설치본의 chromium으로 본다 **[어림]**.

### 다시 돌리는 법

저장소 루트에서 친다.

```bash
git apply .scratch/portal-admin/probes/shared_widget_parts/move-with-consumer-inert.patch
pnpm -C web install --frozen-lockfile
pnpm -C web run typecheck
# 스토리 시험. 종료 1 이 기대다(가리지 않은 스토리 셋과 ShieldedHidden 이 두 폭에서 빨갛다)
pnpm -C web exec vitest run --project admin-storybook-wide --project admin-storybook-narrow --reporter=verbose WidgetPreviewProbe
# 실제 브라우저. 종료 0 이 기대다
pnpm -C web/apps/admin run build-storybook
node .scratch/portal-admin/probes/shared_widget_parts/preview_shield.mjs <web 디렉터리의 절대 경로>
```

첫 두 줄은 이 실험에서 치지 않았다. 소비자 확인의 트리에서 두 파일을 손으로 고쳐 이 상태로 갔고, 패치는 위에 적은 대로 임시 인덱스로만 붙여 봤다. 나머지는 `-C`에 절대 경로를 주고 하나씩 쳤다 **[손]**. `build-storybook`은 `web/apps/admin/storybook-static`(git이 무시한다)에 짓고 `.next/`는 쓰지 않는다. 관리 화면의 `next build`는 이 절에서 돌리지 않았다.

### 결과

axe 칸은 스토리 시험이 낸 것이다. 관리 화면 Storybook의 axe 설정 그대로이고(`target-size`를 켠 채, 위반이 있으면 실패), 같은 스토리의 play가 위젯이 눈에 그려졌다는 표지(위젯의 `main`이 DOM에 있고 `overflow-y: auto`이며 크기가 0이 아니다, 제목이 15px다)를 먼저 단언한다. 긴 내용의 스토리 넷을 더한 지금 판에서 열 스토리와 두 폭의 스무 건 가운데 `Test Files 2 failed (2)`, `Tests 8 failed와 12 passed (20)`였다. 실패 여덟은 아래 표의 대조와 C, 그리고 "휠과 클릭"에 적은 가리지 않은 긴 내용 둘의 axe 위반이다(play의 단언은 모두 통과했다) **[손]**. 넷을 더하기 전의 판은 열두 건 가운데 `Tests 4 failed와 8 passed (12)`였고 아래 표의 위반은 두 판이 같다.

그려짐 칸의 크기, 포커스 칸, 접근성 트리 칸은 `preview_shield.mjs`가 실제 브라우저에서 낸 것이다. 지금 판의 회차는 열여섯이고(Tab 회차 여덟과 마우스 회차 여덟) 표지가 모두 섰으며 끝줄이 `회차 16, 측정이 아닌 회차 0, 기대와 다른 회차 0`, 종료 0이었다 **[손]**. PR 직전 리뷰 뒤에 마우스 회차가 넘친 자리를 읽지 못하면 그 회차를 측정이 아니라고 세게 고쳤고, 고친 판을 한 번 돌린 끝줄도 같았다 **[손]**. 읽지 못하는 길은 그 실행에서 나지 않아 돌려 보지 못했다. 아래 표는 Tab 회차 여덟의 것이고, 마우스 회차를 더하기 전의 판(`회차 8, 측정이 아닌 회차 0, 기대와 다른 회차 0`)과 값이 같았다. 포커스는 키보드의 Tab을 14번 누르며 그때마다 `document.activeElement`가 위젯 안인지 봤다(가리지 않았을 때 위젯 안에서 Tab이 서는 요소는 넷이다). 접근성 트리는 CDP `Accessibility.getFullAXTree`에서 무시되지 않은 노드를 역할로 모았다.

| 갈래 | 폭 | axe 위반 규칙 id | 그려짐 표지 | 포커스(실제 Tab 14번) | 접근성 트리(chromium) |
|---|---|---|---|---|---|
| 대조 | wide | `landmark-main-is-top-level`, `landmark-no-duplicate-main`, `landmark-unique` | 섰다. `main` 318×436, 제목 15px | 위젯 안 10번. "저장"에 닿는다 | 그림 0, `main` 2, 단추 넷("저장"과 위젯의 "새 대화", "보내기", "도구 1개를 불렀습니다"), 제목 둘, 입력창 1. 50노드 |
| 대조 | narrow | wide와 같은 셋 | 섰다. `main` 254×436, 제목 15px | 위젯 안 10번. "저장"에 닿는다 | wide와 같다. 51노드 |
| A | wide | 없다 | 섰다. `main` 318×436, 제목 15px | 위젯 안 0번. "저장"에 닿는다 | 이름 "미리보기, 저장하지 않은 값으로 그린 위젯"의 그림 1, `main` 1, 단추 "저장" 하나, 제목 "사이트 고치기" 하나, 입력창 0. 14노드. Tab 앞뒤가 같다 |
| A | narrow | 없다 | 섰다. `main` 254×436, 제목 15px | 위젯 안 0번. "저장"에 닿는다 | wide와 같다. 14노드 |
| B | wide | 없다 | 섰다. `main` 318×436, 제목 15px | 위젯 안 0번. "저장"에 닿는다 | A와 같다. 14노드. Tab 앞뒤가 같다 |
| B | narrow | 없다 | 섰다. `main` 254×436, 제목 15px | 위젯 안 0번. "저장"에 닿는다 | A와 같다. 14노드 |
| C | wide | `aria-hidden-focus`, `nested-interactive` | 섰다. `main` 318×436, 제목 15px | 위젯 안 10번. "저장"에 닿는다 | 포커스를 받기 전에는 A와 같다(14노드). 포커스가 위젯 안에 든 때에는 그림 1에 더해 `main` 2, 위젯의 단추 셋과 제목과 입력창이 모두 있다(52노드) |
| C | narrow | wide와 같은 둘 | 섰다. `main` 254×436, 제목 15px | 위젯 안 10번. "저장"에 닿는다 | wide와 같다(14노드, 포커스가 든 때 53노드) |

스토리 시험의 play는 같은 것을 흉내로 봤고 두 폭이 같았다 **[손]**. Tab은 `userEvent.tab()`을 여덟 번(위젯 안의 포커스 가능한 요소 다섯보다 셋 많이), 역할은 testing-library의 `getByRole`과 `queryAllByRole`이다. 횟수는 단언을 적기 전에 값을 콘솔에 찍은 탐색 실행의 것이고, 단언 판은 "0번"과 "한 번 이상"으로만 본다.

| 갈래 | 흉내 Tab | 역할로 찾기 |
|---|---|---|
| 대조 | 위젯 안 6번. "저장"에 닿는다 | 그림이 없다. 위젯 안의 단추 3, `main` 2 |
| A | 위젯 안 0번. body에 머물러 "저장"에 닿지 않는다 | 그 이름의 그림이 감싼 요소 하나다. 위젯 안의 단추 0, `main` 1 |
| B | 위젯 안 0번. body에 머물러 "저장"에 닿지 않는다 | 그 이름의 그림이 감싼 요소 하나다. 위젯 안의 단추 3, `main` 2 |
| C | 위젯 안 6번. "저장"에 닿는다 | 그 이름의 그림이 감싼 요소 하나다. 위젯 안의 단추 0, `main` 1 |

읽는 법은 이렇다.

- **A와 B는 위반 셋을 지우고 새 위반을 내지 않았다.** 두 폭 모두 스토리가 초록이다. `aria-hidden-focus`, `nested-interactive`, `scrollable-region-focusable`, `target-size`를 포함해 어느 규칙도 위반으로 나오지 않았다. 위젯은 가린 뒤에도 그려졌고, 실제 Tab은 위젯을 건너 "저장"에 닿았으며, chromium의 접근성 트리에는 그 이름의 그림 하나만 남았다(위젯의 `main`, `h1`, 단추, 입력창이 없다).
- **A와 B의 차이는 chromium에서 보이지 않았다.** axe의 결과, 실제 Tab, 접근성 트리가 같다. 갈린 것은 시험 도구다. testing-library는 `inert`를 보지 않아 B에서 위젯의 단추와 `main`을 그대로 찾는다. 곧 "미리보기 안의 단추가 역할로 잡히지 않는다"를 스토리 시험이나 jsdom 시험에 두면 A에서만 초록이다.
- **C는 landmark 위반 셋을 지우지만 쓸 수 없다.** `aria-hidden-focus`와 `nested-interactive`가 새로 났고, 실제 Tab이 위젯 안에 들었다. 포커스가 든 순간 chromium이 그 `aria-hidden`을 무시해 위젯이 트리에 통째로 드러났고, 콘솔에 "Blocked aria-hidden on an element because its descendant retained focus."로 시작하는 경고가 회차마다 한 건 찍혔다. 그런데 testing-library의 역할 찾기는 C에서도 A와 같은 답을 낸다. 역할 단언만으로는 C와 A가 갈리지 않고, axe와 실제 Tab이 가른다.
- **대조가 섰다.** 가리지 않은 갈래에서 위반 셋이 그대로 났고, Tab이 위젯 안에 들었고, 위젯의 단추가 역할로도 트리에서도 잡혔다. C에서도 Tab이 들었다. 그래서 A와 B의 "들지 않는다"와 "없다"는 포커스와 트리를 실제로 본 결과다.
- **흉내 Tab은 `inert`를 건너지 못한다.** A와 B에서 `userEvent.tab()`은 body에 머물러 "저장"에 닿지 않았는데 실제 Tab은 닿았다. "Tab이 미리보기를 건너 다음 조작에 닿는다"는 스토리 시험으로 볼 수 없고 실제 브라우저로 봐야 한다.

### 휠과 클릭

명세가 "긴 고지 전문이나 긴 대화가 미리보기의 높이를 넘으면 운영자가 그것을 볼 수 있는가"를 정하는 데 쓰라고 더 본 것이다. 대조(가리지 않음)와 갈래 A에 미리보기의 높이(560px)를 넘는 내용 둘을 줬다.

- **긴 안내**(`LongIntroInAdminFrame`, `LongIntroShielded`). 교환이 없고 첫 화면의 안내가 길다. 위젯의 `main`이 넘친다. 고지를 그리는 부품은 아직 없어(widget-login-state가 짓는다) 첫 화면의 안내로 대신했다.
- **긴 대화**(`LongTalkInAdminFrame`, `LongTalkShielded`). 교환이 열둘이다. 넘치는 자리는 `main`이 아니라 그 안의 대화 영역(`role="region"`, 이름 "대화")이다 **[코드]**(`web/packages/widget-ui/src/components/organisms/Conversation.tsx` 76~87줄). 그 부품은 끝을 보고 있었으면 그릴 때마다 끝으로 내린다(같은 파일 65~73줄). `main`은 `scrollHeight`와 `clientHeight`가 436으로 같았다 **[손]**.

네 스토리는 틀의 끝에 빈 높이 1200px을 둬 페이지도 스크롤되게 했다. 위젯이 받지 않은 휠이 어디로 가는지를 보려는 것이다.

`preview_shield.mjs`의 마우스 회차는 네 스토리와 두 폭의 여덟이고 모두 **[손]**이다. 회차마다 실제 마우스로 "새 대화"의 가운데를 한 번 누르고(`page.mouse.click`) 임시 소비자가 센 처리기의 호출 횟수를 읽는다. 그 뒤 페이지를 300px 내려 두고, 마우스를 넘친 자리의 보이는 부분 가운데에 올려 휠을 200px 굴린다(`page.mouse.wheel`). 방향은 넘친 자리에 굴릴 데가 남은 쪽이다(긴 안내는 아래로, 끝에 내려가 있는 긴 대화는 위로). 표지는 넷이고 여덟 회차에서 모두 섰다. 위젯이 그려졌다, 그 자리가 넘쳤다(`scrollHeight`가 `clientHeight`보다 크다), 페이지에 앞뒤로 굴릴 데가 있다, 문서가 click과 wheel 이벤트를 실제로 받았다.

| 갈래 | 내용 | 폭 | 넘침 표지(`scrollHeight`/`clientHeight`) | 클릭 뒤 처리기 호출 | 휠 앞뒤 넘친 자리의 `scrollTop` | 같은 휠 앞뒤 페이지의 `scrollTop` |
|---|---|---|---|---|---|---|
| 대조 | 긴 안내 | wide | `main` 1348/436 | 0 → 1 | 0 → 200 | 300 → 300 |
| 대조 | 긴 안내 | narrow | `main` 1744/436 | 0 → 1 | 0 → 200 | 300 → 300 |
| A | 긴 안내 | wide | `main` 1348/436 | 0 → 0 | 0 → 0 | 300 → 500 |
| A | 긴 안내 | narrow | `main` 1744/436 | 0 → 0 | 0 → 0 | 300 → 500 |
| 대조 | 긴 대화 | wide | 대화 영역 1120/436 | 0 → 1 | 684 → 484 | 300 → 300 |
| 대조 | 긴 대화 | narrow | 대화 영역 1648/436 | 0 → 1 | 1212 → 1012 | 300 → 300 |
| A | 긴 대화 | wide | 대화 영역 1120/436 | 0 → 0 | 684 → 684 | 300 → 100 |
| A | 긴 대화 | narrow | 대화 영역 1648/436 | 0 → 0 | 1211 → 1211 | 300 → 100 |

- **대조가 섰다.** 가리지 않은 위젯에서는 누르면 처리기가 한 번 불렸고, 휠이 넘친 자리를 200px 굴렸으며 페이지는 그대로였다. 그래서 A의 "불리지 않는다"와 "구르지 않는다"는 마우스를 실제로 움직인 결과다.
- **A에서는 눌러도 처리기가 불리지 않는다.** 단추의 가운데에서 브라우저가 맞히는 요소(`elementFromPoint`)가 단추가 아니라 감싼 바깥 요소(`role="img"`)였고, click 이벤트도 그 요소가 받았다. 대조에서는 단추 안의 `span`이 받았다.
- **A에서는 휠로 미리보기 안을 굴릴 수 없다.** 넘친 자리의 `scrollTop`이 그대로였고, 같은 휠이 페이지를 200px 굴렸다. wheel 이벤트도 감싼 바깥 요소가 받았다. 운영자가 미리보기 위에서 휠을 굴리면 관리 화면이 구른다.
- **그래서 A로 가린 미리보기에서 높이를 넘는 내용은 한쪽 끝만 보인다.** 긴 안내는 처음(`scrollTop` 0)에 머물러 아래쪽이 보이지 않는다. 긴 대화는 부품이 스스로 끝으로 내려가 있어(처음 `scrollTop`이 넓은 폭에서 684로, 1120에서 436을 뺀 값이다. 스크립트가 옮기는 스크롤은 `inert` 안에서도 됐다) 앞쪽이 보이지 않는다.
- **스토리 시험의 axe는 두 폭이 같았다.** A의 긴 안내와 긴 대화는 위반이 없다. 가리지 않은 긴 대화는 landmark 위반 셋이고, 가리지 않은 긴 안내는 그 셋에 `scrollable-region-focusable`이 더 났다. 위젯의 `main`이 스크롤되는데 키보드로 닿을 길이 없다는 것이다. 이것은 미리보기가 만든 것이 아니라 옮긴 부품이 긴 안내를 받았을 때의 모양이다. 실제 위젯에서도 같을 것으로 보지만 위젯의 Storybook에서 보지는 않았다 **[어림]**.

### 읽은 코드

axe가 `inert`와 `aria-hidden`을 다루는 자리다 **[코드]**. 파일은 `web/node_modules/.pnpm/axe-core@4.14.0/node_modules/axe-core/axe.js`다.

- 규칙은 대상을 고를 때 `excludeHidden`(기본값 참, 33565줄)이면 화면 읽기 프로그램에 보이는 요소만 남긴다(33591~33598줄). 그 판정은 요소나 조상이 `aria-hidden`이거나 `inert` 속성을 가지면 거짓이다(21185~21204줄, `inert`는 19959~19990줄). landmark 규칙 셋은 `excludeHidden`을 끄지 않아(37541~37611줄) 위젯의 `main`이 A, B, C 모두에서 대상에서 빠진다. `landmark-no-duplicate-main`의 검사가 `main`을 셀 때(31256~31268줄)와 `landmark-unique`가 대상을 고를 때(32942~32944줄)도 같은 판정을 쓴다.
- `aria-hidden-focus`는 `[aria-hidden="true"]`를 고르고 `excludeHidden`을 끈다(36761~36770줄). 검사 둘은 그 요소 안에 Tab이 서는 요소가 없으면 통과다(31117~31121줄, 31187~31192줄). Tab이 서는 요소는 포커스 가능 여부로 고르고(20202~20209줄, 20239~20251줄), `inert`인 요소와 그 자손은 포커스 가능하지 않다(19995~19999줄). 그래서 A는 통과하고 C는 실패한다. B에는 고를 `aria-hidden`이 없다.
- `nested-interactive`는 자식이 표현용인 역할을 고른다(32915~32921줄. `img` 역할이 그렇다, 17193~17199줄과 17388줄). 검사는 포커스 가능한 자손 위젯이 있으면 실패다(31027~31066줄). 같은 포커스 판정이라 A와 B는 통과하고 C는 실패한다.
- `scrollable-region-focusable`도 `excludeHidden`을 끄지 않는다(37875~37883줄). 가린 위젯의 `main`은 대상에서 빠져, 가리지 않은 긴 안내에서 난 그 위반이 A의 긴 안내에서는 나지 않는다.

위는 코드를 읽어 결과에 맞춘 설명이다. 규칙마다 통과로 끝났는지 대상이 없어 지나갔는지를 axe의 결과(`passes`, `inapplicable`)로 확인하지는 않았다 **[어림]**.

흉내와 실제가 갈린 자리다 **[코드]**.

- `userEvent.tab()`은 다음 요소를 스스로 고르며 `tabindex`, `disabled`, `display`와 `visibility`만 본다(Storybook 10.6.1의 `web/node_modules/storybook/dist/test/index.js` 14612~14659줄). `inert`인 요소를 고르면 브라우저가 그 `focus()`를 받지 않아 포커스가 body에 머문다는 것은 결과에 맞춘 해석이다 **[어림]**.
- 역할로 찾을 때 숨은 요소를 거르는 판정은 `hidden`, `aria-hidden="true"`, `display: none`, `visibility: hidden`만 본다(`@testing-library/dom` 10.4.2의 `dist/role-helpers.js` 33~78줄). Storybook의 `storybook/test`는 그 패키지를 그대로 들인다(같은 `index.js` 13837줄).
- chromium이 포커스가 든 요소의 조상에 단 `aria-hidden`을 무시하는 것은 코드를 읽지 않았다. 위 콘솔 경고와 Tab 앞뒤의 트리로 본 것이다 **[손]**.
- `inert` 안의 요소가 마우스에 맞지 않는 것도 chromium의 코드나 HTML 표준을 읽지 않았다. 한 점에서 맞히는 요소와 click, wheel 이벤트를 받은 요소로 본 것이다 **[손]**. 브라우저가 `inert`인 요소를 마우스가 지나쳐 가는 요소처럼 다룬다는 것은 그 결과에 맞춘 해석이다 **[어림]**.

### 결과를 본 뒤 바꾼 판정 기준

- **스토리의 단언은 탐색 실행을 본 뒤에 적었다.** 먼저 값을 콘솔에 찍기만 하는 play로 한 번 돌렸고, 그 값으로 단언을 적었다. 미리 세운 예측을 맞힌 것이 아니라 본 값을 고정한 것이다. B의 "위젯 안의 단추 3, `main` 2"와, A와 B에서 "저장"에 닿는지를 단언하지 않은 것이 그렇게 정해졌다.
- **`preview_shield.mjs`의 C 기대를 첫 실행 뒤에 바꿨다.** 첫 판은 트리를 Tab을 다 누른 뒤 한 번만 읽고, C에서도 위젯이 트리에 없다고 기대했다. 첫 실행은 종료 1이었다. C의 두 폭에서 `main` 2와 위젯의 단추, 제목, 입력창이 트리에 있었다. 그래서 트리를 두 번 읽게 고쳤고(위젯이 포커스를 받기 전, 포커스가 위젯 안에 처음 든 때), 정적 빌드의 play가 흉내로 넣는 포커스가 섞이지 않게 페이지가 뜨기 전에 `HTMLElement.prototype.focus`를 빈 함수로 바꿨으며(첫 판은 Tab 앞에서 `blur()`만 불렀다), `aria-hidden` 콘솔 경고를 세게 했다. C의 기대는 "처음에는 없고 포커스가 든 때에는 있다"가 됐고 둘째 실행이 종료 0이었다. 대조와 A와 B의 기대는 바꾸지 않았다.
- **마우스 회차의 기대는 돌리기 전에 적었고 바꾸지 않았다.** A에서 처리기가 불리지 않고, 넘친 자리가 구르지 않고, 휠이 페이지로 넘어간다는 예측이 첫 실행에서 여덟 회차 모두 맞았다. 볼 자리는 돌리기 전에 코드를 읽고 정했다. 긴 대화에서 넘치는 것은 `main`이 아니라 대화 영역이어서 그 자리의 `scrollTop`을 보고, `main`이 넘치는 것은 긴 안내로 따로 봤다.

### 명세에 넘길 것

- 미리보기를 가리는 쪽에 `inert`가 있어야 한다(A나 B). `aria-hidden`만으로는 포커스가 들고 axe 위반 둘이 난다.
- A와 B 가운데 무엇을 고를지는 이 실험의 chromium에서는 갈리지 않았다. 다른 브라우저나 화면 읽기 프로그램이 `inert`만으로 위젯을 트리에서 빼는지는 보지 않았다. 시험에서 "미리보기 안의 단추가 역할로 잡히지 않는다"를 testing-library로 단언하려면 A여야 한다.
- 수용 기준을 어디서 볼지 가른다. axe 위반과 이름 붙은 그림은 스토리 시험으로 볼 수 있다. "Tab이 미리보기를 건너 다음 조작에 닿는다"와 "브라우저의 접근성 트리에 위젯의 단추가 없다"는 실제 브라우저(e2e나 이 스크립트 같은 길)로만 볼 수 있다.
- 가리면 위젯의 `h1`도 트리에서 빠져 화면의 제목이 하나가 된다(위 표의 제목 칸).
- 부품(`@agent-os/widget-ui`)은 고치지 않아도 된다. 감싼 요소 둘과 속성 넷(`role`, `aria-label`, `aria-hidden`, `inert`)이 전부이고, 안쪽 요소에는 부품이 자리를 채우게 높이 100%를 줬다.
- A로 가리면 "눌러도 아무 일도 일어나지 않는다"는 선다("새 대화" 하나로 봤다). 같은 까닭으로 운영자는 미리보기 안을 휠로 굴릴 수 없고, 미리보기의 높이를 넘는 내용은 한쪽 끝만 보인다(긴 안내는 처음, 긴 대화는 끝). 넘는 내용을 운영자에게 보일지, 보인다면 어떻게 보일지를 정한다. 해 보지 않은 길은 셋이다 **[어림]**. 미리보기의 높이를 내용에 맞춘다(부품은 감싼 요소의 높이를 채우므로 높이는 감싸는 쪽이 정한다). 가린 요소 바깥에 스크롤하는 요소를 따로 둔다. 넘는 내용은 미리보기에서 잘린다고 안내한다.
- 미리보기 위에서 굴린 휠은 관리 화면을 굴린다. 미리보기가 양식 옆에 길게 서면 운영자는 그 위에서도 페이지를 굴릴 수 있다.
- 가리지 않은 위젯에 긴 안내를 주면 `scrollable-region-focusable`이 난다. 미리보기를 A로 가리면 관리 화면에서는 나지 않지만, 긴 안내나 고지 전문을 위젯의 `main`에 그대로 넣는 설계라면 위젯 쪽에서 따로 볼 일이다.

### 보지 않은 것

- 실제 화면 읽기 프로그램(NVDA, VoiceOver 등)이 미리보기를 무엇으로 읽는지. chromium의 접근성 트리만 봤다.
- chromium 밖의 브라우저(Firefox, Safari)가 `inert`와, 포커스가 든 `aria-hidden`을 어떻게 다루는지.
- 휠과 클릭을 갈래 B와 C에서. 대조와 A만 봤다. 누른 것은 "새 대화" 하나이고 입력창이나 다른 단추는 누르지 않았다.
- 휠 밖의 스크롤. 터치로 미는 것, 스크롤 막대를 끄는 것, 키보드로 굴리는 것은 보지 않았다.
- 고지를 그리는 부품. 아직 없어 첫 화면의 긴 안내로 대신했다.
- 넘는 내용을 보이게 하는 길(높이를 내용에 맞추기, 바깥에 스크롤하는 요소 두기). 하나도 돌려 보지 않았다.
- `role="img"`만 달고 `aria-hidden`도 `inert`도 뺀 갈래. 그림 역할만으로 무엇이 달라지는지는 모른다.
- C에서 포커스가 위젯 밖으로 나간 뒤 트리가 다시 가려지는지.
- axe의 판정 보류(`incomplete`) 결과와, 규칙마다의 `passes`와 `inapplicable`. 스토리 시험이 실패로 내는 위반만 봤다.
- 어두운 모드와 다른 테마에서 가렸을 때.
- 여러 번 돌리기. 스토리 시험은 탐색 판, 단언 판, 긴 내용을 더한 판을 한 번씩 돌렸고, `preview_shield.mjs`는 첫 판, 고친 판, 마우스 회차를 더한 판, 읽지 못한 회차를 측정이 아니라고 세는 판을 한 번씩 돌렸다. 마우스 회차는 뒤의 두 번뿐이다.
- 관리 화면의 `next build`, 사진 비교, e2e, `pnpm -C web verify` 전체. 이 절의 상태에서 돌린 것은 타입 검사, 두 파일의 린트와 형식 검사, 위 스토리 시험, Storybook 정적 빌드다.
- 새 체크아웃에 `move-with-consumer-inert.patch`를 붙여 처음부터 다시 돌리는 것.

## 부딪힌 문제와 푼 방법

1. **TS5097.** 새 패키지의 타입 검사가 `@agent-os/ui`의 소스(`themes.ts`가 `.ts` 확장자로 import한다)를 따라가며 실패했다. 패키지의 `tsconfig.json`에 `allowImportingTsExtensions`를 더했다. 바탕 `tsconfig.base.json`에는 없고 tsconfig마다 따로 켜는 옵션이다 **[코드]**(`web/` 아래 tsconfig 가운데 이 패키지까지 12곳이 켠다).
2. **부품이 앱의 것을 가리켰다.** `WidgetScreen`이 `Restore` 타입을 앱의 `useConversation`에서 들였고, `lib/conversation.ts`와 `lib/reconnect.ts`가 `EndUserItem`을 앱의 `api/runs`에서 들였다. 앞의 것은 타입 선언을 패키지로 옮겨 앱이 거꾸로 들이게 했고, 뒤의 것은 `@agent-os/api-client`에서 바로 들였다. 그래서 패키지가 `@agent-os/api-client`에 타입으로 기댄다.
3. **Tailwind가 패키지의 소스를 모른다.** 디자인 토큰 CSS는 `source(none)`이고 앱의 CSS는 자기 `app`과 `components`만 덮는다. 패키지에 `@source ".."` 한 줄짜리 `src/styles/source.css`를 두고 `exports`로 내, 쓰는 앱의 CSS가 `@import`하게 했다. `@source`는 선언한 파일을 기준으로 풀려 앱마다 상대 경로를 적지 않아도 된다.
4. **형식 검사.** 고친 두 파일(`.storybook/main.ts`, `useConversation.ts`)이 Prettier에 걸려 `pnpm -C web exec prettier --write`로 맞췄다.
5. **e2e의 차가운 시작.** 위 "검사 결과"의 기준선 세 번이다. 옮기기와 무관하다.

## 명세가 미리 정해야 할 것

1. **패키지의 이름과 범위.** 이 실험은 `@agent-os/widget-ui`에 화면 부품과 `lib/`의 다섯 모듈을 통째로 넣었다. 그러면 패키지가 화면만이 아니라 대화의 리듀서와 재접속·상한의 규칙까지 든다. 통째로 둘지, 모양과 글자를 내는 함수만 패키지에 두고 대화를 돌리는 규칙은 앱에 남기게 모듈을 쪼갤지 정한다. 진입점(`src/index.ts`)이 무엇을 내보낼지도 함께다.
2. **패키지 안의 층.** `WidgetScreen`은 `components/pages`에 있어 판정자가 page로 본다. organisms와 templates에 걸린 "swr과 생성 클라이언트를 값으로 부르지 않는다"는 정책은 page에 걸리지 않는다 **[코드]**(`web/eslint.config.mjs` 247~255줄). "값만으로 그린다"를 판정자로 지키려면 폴더를 바꾸거나 패키지에 거는 규칙을 더한다. 규칙을 더하면 `web/eslint.config.test.ts`에 사례를 붙인다(`.claude/rules/web-workspace.md`).
3. **스토리와 시험의 자리.** 스토리는 패키지에, 사진과 스토리 시험은 위젯 앱의 것을 그대로 쓰는 이 실험의 모양으로 갈지 정한다. 패키지에 단위 시험(`*.test.tsx`)을 두려면 `web/vitest.config.ts`에 jsdom 프로젝트의 글롭을 더해야 한다 **[코드]**(10~14줄과 55줄. jsdom 프로젝트 셋의 글롭이 `apps/admin`, `apps/widget`, `packages/ui`만 덮어, 패키지의 `*.test.tsx`는 DOM이 없는 `node` 프로젝트에 든다).
4. **스타일.** 쓰는 앱마다 전역 CSS에 `@import "@agent-os/widget-ui/source.css";`를 두고, 그 앱의 Storybook에 공유 화면을 그리는 스토리를 하나 이상 둔다(빌드는 빠진 줄을 잡지 못한다). 감싼 요소에 다는 테마·모드·밀도와 높이를 누가 정하는지도 적는다.
5. **정답 사진의 이름.** 스토리 파일의 `title`을 그대로 두면 이름과 자리가 바뀌지 않는다. `title`을 바꾸거나 패키지가 자기 사진 폴더를 가지면 77장이 움직인다.
6. **린트 경계.** 층 정책은 패키지 안에서도 선다. 패키지에서 앱으로 가는 상대 import와, 앱이 패키지 안을 상대 경로로 들이는 것은 지금 막지 않는다(생성 클라이언트에만 `API_CLIENT_INTERNALS`가 있다 **[코드]**, `web/eslint.config.mjs` 135~139줄). 막을지 정한다.
7. **`main`과 `h1`.** 미리보기가 관리 화면의 `<main>` 안에 서면 axe 위반 셋이다. 부품이 `<main>`을 그리는 자리를 값으로 바꿀 수 있게 할지, 다른 길로 갈지 정한다. 부품을 값으로 바꾸면 미리보기와 실제 위젯이 입력 밖에서 한 군데 달라진다(ADR 0065가 적은 대가 둘째).
8. **문서와 규칙.** `.claude/rules/web-design.md`의 `paths`(`web/packages/ui/**`, `web/apps/*/components/**`)가 `web/packages/widget-ui/**`에 맞지 않아, 옮긴 organisms를 열어도 그 규칙이 실리지 않는다 **[코드]**. 같은 파일 47줄 "패턴과 화면(organisms 이상)은 앱이 짓는다(ADR 0026)"와 `docs/constitution/tech.md` 21줄이 옛 문장이다. ADR 0026 8줄에는 "(바뀜: ADR 0065)"가 이미 있다.
9. **함께 고칠 자리** **[코드]**(돌려 보지 않았다).
   - `deploy/images/{admin,widget,portal}.Dockerfile`이 워크스페이스 패키지의 `package.json`을 하나씩 `COPY`한다. 새 패키지의 줄이 없으면 이미지 안의 `pnpm install --frozen-lockfile`이 그 패키지를 찾지 못할 것이다 **[어림]**.
   - `.scratch/web-widget/probes/`의 변이 표 일곱(`conversation` 20, `failures` 19, `approval` 12, `widget_app` 11, `storage` 5, `widget_e2e` 2, `widget_llm` 1곳)이 옮긴 경로를 가리킨다.
   - `.scratch/admin-style/probes/canary/web_workspace_organisms.toml`의 실험군 대상이 `web/apps/widget/lib/chars.ts`다. `tools/canary.py --shape`는 대상이 있는지 보지 않아(29줄) 게이트에 걸리지 않고 다시 돌릴 때 드러난다.
   - 옮긴 파일의 머리 주석이 앱의 경로(`lib/storage`, `components/pages/useConversation`)를 가리킨다.

## 보지 않은 것

- widget-login-state가 더할 부품(로그인 상태, 고지, 밝기 스위치)으로 옮기는 일. 이 실험의 수는 2026-11-16의 부품 20파일의 것이다.
- 패키지가 자기 Storybook과 사진 폴더를 갖는 길, 모듈을 쪼개는 길.
- 배포 이미지 빌드(`deploy/images/`), CI, 관리 화면의 사진 비교(`visual:admin`)와 디자인 시스템 패키지의 사진 비교(`pnpm -C web visual`), 관리 화면 e2e와 위젯 테스트 페이지 e2e.
- 파이썬 쪽 검사(`uv run pytest`, ruff, pyright, `lint-imports`, pre-commit, `tools/run_checks.py`). 파이썬 파일은 고치지 않았다. `web/`이나 문서를 읽는 저장소 상태 시험이 옮긴 경로를 보는지는 모른다.
- 실제 모델 시험(`-m llm`, `-m llm_widget`, `-m llm_portal`). 지시대로 돌리지 않았다.
- 개발 서버(`next dev`, `storybook dev`)에서 패키지의 소스를 고쳤을 때 다시 그려지는지.
- 사진 비교가 미세한 스타일 차이에 빨개지는지. 대조에서 사진 비교가 빨갰던 것은 스토리가 던졌기 때문이고 픽셀 차이의 문턱은 건드리지 않았다.
- 새 체크아웃에 패치를 붙여 처음부터 다시 돌리는 것, 옮긴 뒤 검사를 여러 번 돌리는 것(옮긴 뒤는 한 번씩이다).
- `/sync-design-system` 확인. 이 실험은 `web/packages/ui`를 고치지 않았다.
