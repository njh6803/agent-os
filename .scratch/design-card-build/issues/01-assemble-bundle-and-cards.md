# 01: 짓기 명령이 컴포넌트 묶음·카드·글꼴·옛 이름을 짓고, chromium이 카드를 그린다

**What to build:** 올리기 도구(`web/tools/sync-design-system/`)의 명령 표에 `assemble --out <산출 폴더> --paths <목록 파일>`이 선다. 한 번 치면 디자인 시스템 패키지의 소스에서, 이미 깔린 vite와 Tailwind CLI만으로 컴포넌트 묶음(`components/bundle.js`·`components/bundle.css`), showcase 스토리가 있는 컴포넌트마다의 카드(`components/<이름>/preview.html`)와 카드 README(`components/<이름>/README.md`), 글꼴(`fonts/`와 `fonts/fonts.css`), 목업이 싣는 옛 이름(`_ds_bundle.js`·`_ds_bundle.css`·`styles.css`)이 산출 폴더에 나오고, 산출의 모든 경로를 든 목록이 `--paths`에 쓰인다. `pnpm -C web verify`가 그 명령을 임시 폴더로 한 번 돌려 파일을 검사하고, 카드마다 페이지와 같은 차례로 chromium에 띄워 장면이 그려지는지, 한글 글꼴이 실리는지, 층 밖의 토큰이 묶음의 토큰을 이기는지 본다.

이 티켓은 아무것도 걷어 내거나 옮기지 않는다. 올리기 절차는 이 명령을 아직 부르지 않으므로, 병합된 뒤에도 사람에게 `/design-sync`를 부탁하는 지금 절차가 그대로 돈다. `tokens.json`, 디자인 시스템 README, 기초 카드, 지침은 02가 산출에 더한다.

근거는 `.scratch/design-card-build/spec.md`의 "짓기 명령", "컴포넌트 묶음", "묶음 CSS와 글꼴", "컴포넌트 카드", "옛 이름"과 Testing Decisions(이음매, 자리, React, 파일 검사, chromium 그리기, 변이), 그리고 그 자리들의 2026-10-29 명세 검토 주석이다. 결정은 ADR 0025의 2026-10-28 이력이다. 측정은 `.scratch/design-card-build/probes/`의 `card_build.mjs`(저장소 도구만으로 짓기, chromium 문서의 그리기와 색), `vite_cli.mjs`·`vite_cli_tool.mts`(vite를 import하지 않고 CLI로 짓는 길)이고, 결과는 그 폴더의 `README.md`다.

**Blocked by:** None (can start immediately)

**Status:** in-progress

### 시작 전

- [x] **글꼴 대조를 먼저 본다.** 시험이 카드를 싣는 길(문서의 기준 주소를 산출 폴더의 `components/<이름>/preview.html`로 둔다)로 진단 문서를 띄워, 묶음 CSS의 글꼴 주소가 `../../fonts/`면 Noto Sans KR이 하나 이상 실리고 `../fonts/`로 바꾸면 글꼴 오류가 나는 것을 보인다. `file://` 문서에서 실리지 않으면 Playwright의 요청 가로채기(`route`)로 산출 폴더를 내주는 길로 바꿔 다시 본다. 어느 길에서도 양성과 음성이 갈리지 않으면 멈추고 사람에게 알린다. 명세는 이것을 chromium에서 재지 않았다(Testing Decisions "chromium 그리기"의 주석)

### 명령

- [x] `assemble --out <산출 폴더> --paths <목록 파일>`이 명령 표에 선다. 이미 있는 `build`(`tokens.json` 하나를 짓는다)와 이름이 다르다. 보고는 다른 명령처럼 표준 출력의 JSON 한 줄이고 파일 수, 카드 이름, 바이트를 든다
- [x] 산출 폴더가 있고 비지 않았으면 아무것도 쓰지 않고 오류로 끝난다. 명령은 자기가 만든 임시 폴더 말고는 어떤 폴더도 지우지 않는다
- [x] vite와 Tailwind를 import하지 않는다. 디자인 시스템 패키지 폴더를 작업 폴더로 삼아 패키지에 깔린 CLI를 셸 없이 node로 바로 띄운다. vite 설정은 import 없는 글로 지어 명령의 임시 폴더에 쓰고, 플러그인 셋(JSX 대체 모듈, `storybook/test` 대체 모듈, 컴포넌트 모듈을 전역으로 돌리는 해석기)은 그 글 안의 객체다. 새 의존을 들이지 않아 `web/`의 매니페스트와 잠금 파일이 그대로다
- [x] 빌드의 성공은 종료 코드 0과 산출 파일로 가른다. stderr의 rolldown `"use client"` 경고는 실패가 아니다
- [x] 명령은 임시 폴더에 지은 뒤 그 폴더를 아래 규칙(금지 문자열, 크기 한도, 카드 README)으로 판정하고, 통과할 때만 `--out`에 옮긴다. 빌드가 하나라도 실패하거나 규칙을 어기면 `"ok": false`와 0이 아닌 종료 코드로 끝나고 `--out`에는 아무것도 없다
- [x] 산출에 시각, 명령의 임시 폴더 경로, `--out` 경로가 들지 않는다. 그래서 같은 커밋에서 다시 지으면 같은 바이트다(스토리 12)
- [x] `--paths`에는 산출 폴더의 모든 파일을 `project/<경로>`로, `/` 구분으로, 올리기 도구의 경로 차례(`byPath`, UTF-16 코드 단위)로 정렬한 JSON 배열을 쓴다. 들여쓰기 두 칸에 한 줄 한 경로이고 끝에 줄바꿈이 있다. 04의 올리기가 이 목록을 지난 산출 목록으로 쓴다

### 컴포넌트 묶음

- [x] `components/bundle.js`는 패키지 엔트리를 IIFE 하나로 묶고 전역 이름은 `AgentOsUi`다. `react`·`react-dom`·`react-dom/client`는 묶지 않고 전역 `React`·`ReactDOM`으로 읽는다. JSX 런타임(`react/jsx-runtime`, `react/jsx-dev-runtime`)은 `createElement`와 `Fragment`로 다시 짓는 대체 모듈로 바꾼다. `process.env.NODE_ENV`는 `production`이고 압축한다
- [x] 1행은 `/* @ds-bundle: {"format":4,"namespace":"AgentOsUi","components":[{"name":"…"},…]} */`다. 목록은 카드가 있는 컴포넌트이고, 차례는 층의 차례(atoms 다음 molecules), 같은 층 안에서는 이름 차례다. `sourcePath`는 적지 않는다
- [x] 묶음에 `</script`·`<!--`·`require(`·`import` 문·`react.transitional.element`가 있거나 묶음이 6MB를 넘으면 명령이 실패한다

### 묶음 CSS와 글꼴

- [x] `components/bundle.css`는 패키지의 Tailwind 빌드(`src/styles/theme.css`를 `--minify`로) 뒤에 글꼴의 `@font-face`를 붙인 것이다. 디자인 토큰은 Tailwind가 둔 대로 `@layer theme` 안에 남는다. 2MB를 넘으면 명령이 실패한다
- [x] `fonts/`에는 패키지의 글꼴 CSS(`src/styles/fonts.css`)를 vite로 지어 나온 글꼴 파일을 두고, 그 CSS를 `fonts/fonts.css`로 둔다. 인라인 한도는 vite 기본값이다. 지금 소스로는 글꼴 파일 770개와 data URL 둘이 나오고, 그 770개의 이름은 지난 산출 목록의 `fonts/`와 같다(명세 "`fonts/`"의 손 확인)
- [x] 글꼴 주소는 세 벌이다. vite가 낸 주소에서 파일 이름만 남기고 `fonts/fonts.css`는 `./`, `_ds_bundle.css`는 `./fonts/`, `components/bundle.css`는 `../../fonts/`를 붙인다. data URL은 세 벌 모두 그대로 둔다
- [x] 묶음 CSS의 테마 선택자(`[data-theme="nokcheong"]`와 `[data-mode=dark]`의 짝)는 바꾸지 않는다

### 컴포넌트 카드

- [x] 패키지의 컴포넌트 층 폴더(atoms, molecules)의 스토리 파일 가운데 `tags`에 `showcase`가 든 스토리를 가진 파일마다 카드 하나를 짓는다. 지금은 카드 아홉에 장면 열하나다
- [x] 카드의 1행은 `<!-- @dsCard group="<층 폴더 이름>" -->`, 그다음 `<div id="root" data-ui-root></div>`, 그다음 장면 스크립트 하나다. 표지에 `height`는 적지 않는다
- [x] 장면은 그 스토리 파일을 IIFE로 묶은 것이다. 패키지의 컴포넌트 모듈은 장면에 묶지 않고 전역 `AgentOsUi`에서 읽고, `storybook/test`는 아무 일도 하지 않는 대체 모듈로 바꾼다. showcase 스토리마다 meta의 `args`와 그 스토리의 `args`를 합쳐, `render`가 있으면 그것으로 없으면 meta의 `component`로 그려 `<section data-scene="<스토리 이름>">`에 넣고, 그 모두를 React 루트 하나로 `#root`에 그린다. 스토리의 `play`·`globals`·`parameters`는 쓰지 않고, 카드는 테마와 모드를 정하지 않는다
- [x] 장면 스크립트의 본문에 `</script`·`<!--`·`require(`·`import` 문·`react.transitional.element`가 있으면 명령이 실패한다. 이스케이프하지 않는다. 1행의 표지와 장면을 싸는 `<script>` 태그는 본문이 아니다. 카드가 256KB를 넘어도 실패한다
- [x] `components/<이름>/README.md`는 컴포넌트 옆의 쓰임 설명(`<이름>.md`)을 바이트 그대로 둔 것이다. showcase 스토리가 있는데 그 파일이 없거나 64KB를 넘으면 명령이 실패한다

### 옛 이름

- [x] `_ds_bundle.js`는 `components/bundle.js`와 같은 바이트다
- [x] `_ds_bundle.css`는 `components/bundle.css`와 같은 Tailwind 빌드에 주소가 `./fonts/`인 `@font-face`를 붙인 것이다
- [x] `styles.css`는 `fonts/fonts.css`와 `_ds_bundle.css`를 차례로 `@import`한다

### 시험

- [x] 짓기 시험은 `pnpm -C web verify`의 `vitest run`에서 node 환경 프로젝트로 돈다. 새 vitest 프로젝트를 만들지 않고, chromium은 `web/`이 이미 직접 의존으로 두는 Playwright로 Storybook 스토리 시험과 같은 브라우저 캐시의 것을 띄운다(명세 "자리", 사용자가 고른 것)
- [x] 시험은 명령을 임시 폴더로 한 번 돌리고, 같은 폴더를 파일 검사와 chromium 그리기가 함께 읽는다(명세 "이음매", 사용자가 고른 것)
- [x] **파일 검사.** 카드가 showcase 스토리를 가진 컴포넌트마다 하나씩이고 1행의 무리가 그 컴포넌트의 층 폴더 이름이며, 카드마다 같은 폴더의 `README.md`가 `<이름>.md`와 같다. 묶음 JS의 1행이 `@ds-bundle` 머리(format 4, namespace `AgentOsUi`)이고 머리의 컴포넌트 목록이 카드 이름과 같은 차례로 같다. 묶음 JS와 장면 본문에 금지 문자열이 없다. 크기가 한도 아래다. 글꼴 주소의 꼴이 파일마다 정한 것과 같고, data URL이 아닌 주소가 가리키는 글꼴 파일이 산출에 모두 있다. `_ds_bundle.js`가 `components/bundle.js`와 같고 `styles.css`가 차례대로 들인다. `--paths`의 목록이 산출 폴더를 훑은 것과 같고, 모든 경로가 `project/`로 시작하며 `byPath` 차례다. 산출에 짓기의 임시 폴더 경로와 `--out` 경로가 없다
- [x] **규칙 판정.** 지은 산출을 복사해 규칙을 하나씩 어기게 바꾸고(카드 폴더의 `README.md`를 지운다, 장면 본문에 `</script`를 넣는다, 한도를 넘는 파일을 둔다) 판정이 `"ok": false`를 내는지 본다. 비지 않은 `--out`을 준 실제 명령이 아무것도 쓰지 않고 오류로 끝나는지 본다
- [x] **chromium 그리기.** 시험이 패키지의 React 19에서 전역 `React`·`ReactDOM`을 내는 IIFE를 짓는다. 패키지에 그 파일이 없고(UMD가 없다) `web/tools`의 시험은 vite를 import하지 못하므로, 짓기 명령과 같이 패키지의 vite CLI를 셸 없이 띄워 짓는다. 카드마다 토큰 CSS, 묶음 CSS(`<style>`), React와 ReactDOM 전역, 묶음 JS, 카드의 차례로 실은 문서를 띄우고 기준 주소는 위 "시작 전"에서 고른 길이다. 토큰 CSS는 받아 둔 페이지 토큰 CSS(`.scratch/design-card-build/probes/received/page-tokens.css`)의 사본을 올리기 도구의 시험 자료로 두어 싣고, `data-theme`·`data-mode`는 페이지가 카드에 붙이는 꼴(프로브의 `theme-match`·`dark-match` 회차가 쓴 값)로 단다. 그 문서에서 showcase 스토리 수만큼 장면이 그려지고 페이지 오류와 콘솔 오류가 0이며, Noto Sans KR이 하나 이상 실리고 글꼴 오류가 0이다. 층 밖에서 디자인 토큰 하나를 덮은 토큰 CSS를 실으면 그 토큰을 쓰는 요소의 색이 바뀐다(선례는 프로브의 `cascade` 회차)
- [x] 시험 자료의 사본을 `web/`의 Prettier가 다시 쓰면, 페이지가 지은 바이트 그대로 두도록 `web/.prettierignore`에 까닭과 함께 넣는다(선례는 같은 파일의 `page-saved-README.md` 줄)
- [x] **변이.** 위 판정마다 그 판정만 빨개지는 변이를 `tools/mutate.py`의 표로 `.scratch/design-card-build/probes/`에 두고 돌린다. 표지는 `.claude/rules/probes.md` 첫 항목대로 고른 단언이 실패할 때만 나오는 문구로 고른다. vitest 판정의 선례는 `.scratch/design-reverse-sync/probes/record_check_mutations.toml`이다. 프로브 README에 표마다 한 줄을 더한다

### 마무리

- [x] 한 번 짓기의 시간(명세의 어림은 15초 안팎)과 시험이 `vitest run`에 더한 시간을 이 티켓의 결과에 적는다. 잰 명령과 함께 적고, 재지 않았으면 어림이라고 적는다
- [x] 명령 코드가 `web/`의 eslint와 strict 타입 검사를 지난다. 프로브 README는 eslint를 재지 않았다고 적는다
- [ ] 검증 명령이 모두 초록이다. 모델 경로, 위젯, 관리 화면을 건드리지 않아 `-m llm`·`-m llm_widget`·e2e·사진 비교는 칠 일이 없다. CI의 `pnpm -C web verify`에서 새 node 시험이 chromium을 띄우는지 PR의 CI로 본다

## 결과

- **글꼴 대조(시작 전).** `probes/font_route.mjs`로 쟀다. 두 길(`file://`, 요청 가로채기 `route`) 모두 지은 그대로의 `../../fonts/`는 Noto Sans KR 실림 5·글꼴 오류 0, `../fonts/`로 바꾼 것은 실림 0·오류 5였다(회차 4, 측정 4). 둘 다 갈렸고, 시험은 산출을 고치지 않고 페이지처럼 `http` 출처에서 싣는 `route` 길을 골랐다(프로브 README "2026-10-29 글꼴 대조").
- **산출.** 한 번 지으면 파일 794개다. 명세의 802에서 02가 더할 여덟(`tokens.json`, 디자인 시스템 README, 기초 카드 넷, 지침 둘)을 뺀 수다. 카드는 아홉, 장면은 열하나다(그리기 시험이 장면 수를 스토리 소스에서 센 수와 맞댄다). 글꼴 파일 770개의 이름은 커밋 `35028cba`의 `.design-sync/upload-output.json`의 `fonts/` 770개와 같고, 묶음 CSS의 data URL은 `data:font/woff2` 둘이다. 이 둘은 지은 산출을 그 목록과 `diff`하고 `grep -o "data:font/[a-z0-9]*"`로 세어 손으로 봤다.
- **다시 지으면 같은 바이트.** 같은 판에서 `--out`을 달리해 두 번 지은 산출이 `diff -r`로 같았고 `--paths`의 목록도 `cmp`로 같았다(손으로 봤다).
- **짓기 시간.** `time node web/tools/sync-design-system/main.ts assemble --out <폴더> --paths <파일>`이 7.8초(real)였다. 셀프 리뷰 전의 다른 때 같은 명령이 16.5초였고, 그때는 이 PC에서 다른 세션의 vitest가 돌고 있었다. 한 번씩 잰 값이다. 명세의 어림(15초 안팎)과 같은 자릿수다.
- **시험이 `vitest run`에 더한 시간.** `pnpm -C web exec vitest run --project node --reporter=json --outputFile=<파일>`의 리포트에서 이 시험 파일의 `endTime - startTime`이 17.06초였다(셀프 리뷰를 반영하기 전의 시험 27개 판. 파일 39·시험 933 모두 통과, 첫 파일 시작부터 마지막 파일 끝까지 172.39초. 리포트를 스크래치 스크립트로 읽어 손으로 봤다). 반영 뒤 시험 29개의 이 파일만 돌린 `pnpm -C web exec vitest run --project node tools/sync-design-system/assemble.test.ts`는 Duration 97.40초였다. 같은 명령이 반영 전에 18.33초와 47.26초였고, 이 PC에 다른 세션의 부하가 있어 반영으로 늘어난 몫은 가르지 못했다(어림). node 프로젝트는 파일을 차례로 돌려(`web/vitest.config.ts`의 `fileParallelism: false`) 이 값이 그 프로젝트에 더한 시간이다. node와 Storybook 프로젝트가 함께 도는 `vitest run` 전체에 더한 시간은 이 값을 넘지 않을 것으로 본다(어림). 파일을 넣고 뺀 전체 실행의 비교는 `--exclude`가 먹지 않아(두 실행 모두 1467개) 쓰지 못했다.
- **eslint와 strict.** 셀프 리뷰를 반영한 판에서 `pnpm -C web exec eslint tools/sync-design-system/assemble.ts tools/sync-design-system/assemble.test.ts tools/sync-design-system/command.ts`와 `pnpm -C web exec tsc --noEmit -p tsconfig.json`이 둘 다 0으로 끝났고, 같은 판의 `uv run python tools/run_checks.py`가 `web-verify`(`pnpm -C web verify`)를 포함한 열 검사 모두 `Passed`로 0으로 끝났다.
- **장면의 이름.** `<section data-scene="…">`의 값은 스토리의 내보낸 이름(`ShowcaseApprovalPair` 따위)이고, 스토리 객체의 `name`이 아니다. 명세가 근거로 든 프로브 `card_build.mjs`가 내보낸 이름을 썼다(그 파일 237행). 그 값은 시험이 `[data-scene]`의 수를 셀 때만 쓰인다(`web/`을 `data-scene`으로 grep했다).
- **시험이 지나지 않는 길.** 장면이 meta와 스토리의 `args`를 합친 값이 그리기에 닿는지와, `render` 없이 meta의 `component`로 그리는 갈래는 지금 showcase 스토리 열하나가 모두 `args`를 받지 않는 `render: () =>`를 가져 어떤 시험도 보지 않는다(합치는 줄 자체는 열하나 모두에서 돈다. 스토리 소스를 Grep해 `tags: ["showcase"]` 다음 줄을 손으로 봤다). 명령이 임시 폴더를 지우지 못해 남기는 갈래도 시험이 지나지 않는다. 명령 독스트링의 못 보는 것에 적었다.
- **실패하면 `--out`이 빈다.** 목록 파일을 산출을 옮기기 전에 쓴다. `--paths`에 이미 있는 폴더를 주자 `"kind":"output"`, 종료 1로 끝났고 `--out` 자리에 폴더가 생기지 않았다(`node web/tools/sync-design-system/main.ts assemble --out <폴더>/out --paths <폴더>/list-is-dir`과 `ls -A <폴더>`로 손으로 봤다). 셀프 리뷰 전의 판은 같은 입력에서 `--out`에 794개를 남겼다(명세 축 리뷰어가 돌려 봤다).
- **임시 폴더를 만들지 못하면.** PR 직전 버그 축이 잡았다. 명령이 임시 폴더를 `try` 밖에서 만들어, 만들지 못하면 JSON 보고 없이 예외로 끝났다. 시험(임시 폴더 환경 변수 셋을 없는 폴더로 둔다)을 먼저 써서 이 시험 파일을 `-t 만들지`로 좁혀 돌리자 `mkdtemp`의 ENOENT가 `run()`을 지나 던져져 빨갰다(1 failed | 29 skipped. 앞 세션이 손으로 봤다, 일지 2026-10-30-01 "이어받은 세션(커밋 뒤)"). 그 뒤 그것을 `output` 오류로 바꾸고 임시 폴더를 지우지 못해도 결과를 덮지 않게 고쳤다. 같은 빨강을 변이 표의 23(오류를 `output`으로 바꾸는 줄을 `throw error`로 되돌린다)이 다시 잰다. `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/design-card-build/probes/assemble_mutations.toml 23`이 기준선 초록, 변이 빨강, 표지 `Error: ENOENT: no such file or directory, mkdtemp`까지 기대대로라고 찍었다. 셀프 리뷰가 이 시험과 이웃 `run()` 사례 둘에 오류 문구 단언을 더하게 한 판에서 이 시험 파일이 30 통과였다(`pnpm -C web exec vitest run --project node tools/sync-design-system/assemble.test.ts`, 손으로 봤다).
- **변이.** `probes/assemble_mutations.toml`의 변이 25. 결과와 표지를 고친 까닭은 프로브 README "2026-10-29 짓기 명령의 변이"다.
