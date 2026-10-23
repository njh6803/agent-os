# 2026-10-23 (50) 위젯 앱의 뼈대 (web-widget 03)

브랜치 `feature/03-widget-app-skeleton`, 워크트리 `.claude/worktrees/03-widget-app-skeleton`. 티켓은 `.scratch/web-widget/issues/03-widget-app-skeleton.md`. 나란히 여는 2 중 2이고, 함께 도는 티켓은 01(계약)이다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/web-widget/issues/03-widget-app-skeleton.md
>
> 다음 작업: .scratch/web-widget/issues/03-widget-app-skeleton.md. `web/apps/widget` 앱을 세워 `/widget` iframe 페이지가 첫 화면을 사이트가 고른 테마로 그리게 하고 위젯의 Storybook과 사진 비교를 세운다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 2 중 2. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/web-widget/issues/03-widget-app-skeleton.md
> 브랜치: feature/03-widget-app-skeleton
> 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
> 읽을 것: docs/journal/2026-10-23-40-web-widget-spec.md 의 "다음" 절. 나란히 도는 티켓은 .scratch/web-widget/issues/01-contract-calling-item-and-limit-kind.md
> 이어받을 상태: 명세와 티켓 열하나가 PR #373(squash 8a026f3c)으로 main에 병합됐다. 없음
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

## 한 것

- `web/apps/widget`(새): Next 16.3.6 앱. `basePath` `/widget`, iframe 페이지는 `app/page.tsx` 가 `components/pages/WidgetPage` 를 그린다. 질의 다섯은 `lib/embed.ts` 의 `readEmbed` 가 읽고(패턴은 `openapi.json` 의 실행 시작 본문과 시험이 맞댄다), 페이지는 문서 뿌리에 `data-theme`·`data-mode`·`data-density="regular"` 를 칠하기 전에 달고 잘못 준 질의마다 `console.error` 를 남긴다. 화면은 templates `WidgetFrame`, organisms `TopBar`·`Composer`, molecules `Welcome`, pages `WidgetScreen` 이다. 아이콘은 `IconName` 의 것만 쓴다.
- `next.config.ts`: 모든 경로에 `frame-ancestors 'none'`(04가 사이트 파일을 읽을 때까지), `/widget/fonts/*` 에 `Access-Control-Allow-Origin: *`. 시험은 `next.config.test.ts`.
- 시작 래퍼 `apps/widget/tools/start.ts`: 루프백에만 띄우고 dev·build 전에 `@agent-os/ui` 의 woff2 를 `public/fonts/` 로 복사한다(`tools/fonts.ts`). 시험은 `tools/start.test.ts`(인자 판정과, 판정을 지난 명령을 따르는 `launch` 의 차례)와 `tools/start.spawn.test.ts`(실제로 `next dev` 를 띄운다)다.
- 위젯 CSS `styles/widget.css`: 디자인 토큰 CSS 를 `@import` 하고 `@source "../app"; @source "../components";` 로 위젯 소스를 덮는다.
- 시험 프로젝트: 뿌리 `vitest.config.ts` 에 `widget-pages`(jsdom)와 `widget-storybook`(chromium)를 더해 다섯이 됐다.
- 위젯 Storybook `apps/widget/.storybook/`: 미리보기는 `@agent-os/ui/storybook` 을 나눠 쓰고 위젯 CSS 를 shadow 틀에도 넘긴다. 스토리는 `WidgetScreen` 다섯(320px, 400px, 할 수 있는 일 없음, 잘못된 설정, 다크).
- 사진 비교: 정적 빌드를 여는 길을 `web/packages/ui/visual/index.ts` 로 꺼내 `@agent-os/ui/visual` 로 내보냈다(빌드 자리를 인자로 받는다). 위젯은 `apps/widget/visual/` 에 자기 설정과 정답 사진 아홉 장을 둔다. `web/tools/visual.ts` 는 대상 패키지가 `workspace:` 로 기대는 패키지를 컨테이너 안에서 링크로 잇는다. 명령 `visual:widget`·`visual:widget:update`, CI `visual` 잡에 위젯의 빌드·비교·아티팩트 단계를 더했다.
- 디자인 시스템 패키지: `themes.ts` 가 `./styles/contrast.ts` 를 `.ts` 확장자로 들이고 tsconfig 에 `rewriteRelativeImportExtensions` 를 켰다. 컴포넌트와 토큰은 바뀌지 않았다(사진 비교 108 초록).
- 문서: 운영 문서(tsc 범위, Vitest 다섯, 사진 비교), 헌법 판 3.0.53, `CLAUDE.md` 검증 명령, `README.md` 트리, `.claude/rules/web-design.md` 의 앱 Storybook 문단. 정리 도구(`tools/tidy_checkouts.py`)가 위젯의 정적 빌드와 글꼴 복사본을 다시 만들 수 있는 자리로 본다. 게이트 파이프 훅이 `visual:widget` 을 게이트로 읽는 것을 시험에 고정했다.
- 프로브: 위젯 변이 표 `.scratch/web-widget/probes/widget_app_mutations.toml`(32), 규칙 문단 카나리아 `canary/web_design_app_storybook.toml`(통과 4). 디자인 시스템 변이 표 둘은 옮긴 파일과 지금 코드에 맞춰 고쳤다.

## 결정

- 위젯이 자기 시작 래퍼를 둔다(ADR 0024가 넘긴 첫째). 공유 자리로 옮기면 관리 화면의 래퍼와 시험을 함께 옮겨야 하고, 위젯은 글꼴 복사라는 자기 일이 더 있다. 대가로 루프백 목록이 `serve`(`src/agent_os/main.py`), 관리 화면 래퍼(`apps/admin/tools/loopback.ts`), 위젯 래퍼로 세 벌이다.
- vite 판은 고정하지 않는다(둘째). 위젯도 `^8.3.1` 로 선언하고 잠금 파일이 8.3.1 하나를 든다. 디자인 시스템 패키지와 같은 선언이라 pnpm 이 한 판으로 푼다.
- 글꼴은 래퍼가 dev·build 전에 `public/fonts/` 로 복사한다. Next 의 `public/` 은 워크스페이스 패키지의 파일을 가리킬 수 없고, 복사본은 `.gitignore` 가 무시한다.
- `themes.ts` 의 `.ts` 확장자: 위젯의 `next build`(Turbopack)가 디자인 시스템 소스의 `./styles/contrast.js` 를 이웃 `.ts` 로 풀지 못해 "Module not found" 로 멈췄다(이 세션에서 손으로 봤다. 커밋한 프로브는 없다). 선언 파일 `dist/themes.d.ts` 에는 `.ts` 가 남는다. 그것을 읽는 소비자는 `bundler`·`node10` 두 해석 모두 풀었다(스크래치 소비자에 `const wrong: number = MODES` 를 두고 `pnpm -C web exec tsc -p <tsconfig>` 로 두 해석을 돌려, 둘 다 TS2322 하나만 `readonly ["light", "dark"]` 를 들고 냈다. 손으로 봤다).
- 컨테이너 안에서 워크스페이스 패키지는 복사하지 않고 `/web/...` 로 링크를 건다. Playwright 1.63 이 실제 경로가 `node_modules` 아래인 파일을 TypeScript 로 바꾸지 않기 때문이다(설치본 `playwright/lib/transform/esmLoader.js` 의 `shouldTransform` 을 읽었다). 그래서 Playwright 셋은 읽기 전용 bind 에서 tmpfs 로 복사한다.
- ADR 은 고치지 않았다. 계약·디스크 형식이 아니고, ADR 0024·0026 의 이력이 이 배치를 이미 정했다(명세 "위젯 앱의 배치와 빌드").
- `WideDark` 의 사진은 `Wide` 의 다크 사진과 같다(두 정답 사진의 md5 가 같다, 명세 축 리뷰가 봤다). 스토리 테스트가 모드를 정하지 않은 스토리를 라이트로만 돌아, 다크의 axe 를 보려고 남겼다.

## 변이

- 위젯 표 28: 첫 실행에서 도구가 28 모두 기대대로로 판정했다. 셀프 리뷰가 표지 없는 19를 짚었다(아래 표준 축 1).
- 위젯 표 32: 리뷰 반영으로 변이 넷(빈 테마, 빈 모드, 빈 에이전트, 판정을 지난 명령에서 준비 건너뛰기)을 더하고, 표지가 없던 23 모두에 표지를 넣었다. 표지를 고르려고 표지 없는 변이에 없는 문구를 표지로 넣은 스크래치 사본을, 출력의 끝을 120줄 보이게 고친 `tools/mutate.py` 의 스크래치 사본으로 돌려 실패 출력 전체를 봤다(23 모두 기대대로 빨갛고 "표지 없음"). 고른 것은 그 단언의 실패 머리(`expected 'purple' to be 'nokcheong'` 등)나 값이 든 `Received` 줄과 diff 의 받은 쪽 줄이다. 코드 조각의 문구는 고르지 않았다. 다시 돌린 32 모두 기대대로였다. 32번(workspace 가 아닌 의존)은 링크 맵을 맞대는 단언보다 먼저 경로 가드가 `next` 를 거부해 빨개져, 표지가 그 이름을 보고 변이 위에 그 까닭을 적었다.
- 디자인 시스템 `static_play_mutations.toml` 을 `--since origin/main` 으로: 1 기대대로.
- 디자인 시스템 `visual_mutations.toml` 을 `--since origin/main` 으로(바뀐 9): 기준선 둘이 초록이 아니어서 변이를 넣지 않았다. 군청 스토리 변이의 `-g "atoms-button--primary-guncheong 를"` 은 그 스토리가 `judgment` 라 기준선에 시험이 0개였다(원래 표처럼 평소에도 도는 스토리와 함께 걸리게 `atoms-button--primary(-guncheong)? 를 기본` 으로 고쳤다). 전체 사진의 기준선은 한 번 1 failed, 85 passed 였고 같은 명령을 다시 돌리자 86 passed 였다. 실패한 스토리 이름은 도구가 요약만 남겨 모른다. 그 시각에 셀프 리뷰 서브에이전트 둘이 같은 체크아웃에서 명령을 돌리기 시작했다. 원인은 가르지 못했다. 위젯 표 32 뒤에 같은 표를 `--since origin/main` 으로 다시 돌리자 기준선 여덟이 모두 초록(전체 사진 86 passed)이었고 고른 9 모두 기대대로였다.
- 2026-10-23 첫 실행 때 앞선 명령이 표 둘을 한 번에 넘겨 인자 오류(종료 2)로 끝났다. 도구는 `--check` 만 표를 여럿 받는다.

## 셀프 리뷰

base `8a026f3c`(HEAD 와 같다), 바뀐 추적 파일 26, 커밋 0, 미추적 43(위젯 앱 전체와 정답 사진 아홉, `web/packages/ui/visual/index.ts`, 프로브 둘, 이 일지). 리뷰가 도는 동안 변이 도구가 디자인 시스템 파일에 변이를 넣었다 빼고 있어, `visual/index.ts`·`stories.visual.ts` 는 깨끗한 사본을 넘겼다.

### 표준 축 (Critical·Major 없음)

1. Minor: 위젯 변이 표의 빨강 기대 28 가운데 표지는 9뿐인데 README 는 모두 표지를 단언한다고 적었다(`.claude/rules/probes.md` 첫 항목). 판정: 고친다. 표지 없는 19에 없는 문구를 표지로 넣은 스크래치 사본을 돌려 실패 출력을 본 뒤 고른다.
2. Minor: `themes.ts` 주석의 "내보내는 빌드는 `.js` 로 바꿔 쓴다"가 반만 참이다(`.d.ts` 에는 `.ts` 가 남는다). 판정: 고쳤다. 선언 파일에 남는 것과 소비자 해석 둘을 잰 것을 주석에 더했다(위 결정).
3. Minor: `Entrypoints.stories.tsx` 의 "진입점 여섯"이 `./visual` 로 일곱이 된 exports 와 어긋난다. 판정: 고친다.
4. Minor: `.scratch/design-system/probes/README.md` 의 `static_play.mjs` 행이 옮겨 간 머리 주석을 `visual/storybook.ts` 에서 찾는다. 판정: 고친다.
5. Minor: 변이 표·카나리아·README 가 이 일지를 근거로 드는데 일지가 머리 한 줄이었다. 판정: 이 일지를 채운다. 카나리아 머리의 인용 `"앱의 components 에는 아직 스토리가 없다"` 가 원문 `components에는` 과 다르다(Nit). 판정: 고친다.
6. Minor: `packages/ui` 를 바꿔 위젯 사진이 바뀌어도 `web-design.md` 의 정답 갱신 지시는 `visual:update` 뿐이다. CI 는 디자인 시스템 단계가 실패하면 위젯 단계를 건너뛴다. 판정: 둘 다 고친다(규칙 문장, 위젯 단계의 `if`). 잡의 `timeout-minutes: 20` 은 CI 의 실제 시간을 보고 정한다.
- 판단 항목: 시작 래퍼의 중복은 티켓이 정한 대가다. "셋을 함께 고친다"가 위젯 파일에만 있다(명세 축도 짚었다). 판정: 다른 두 자리에도 적는다. 위젯 `visual/stories.visual.ts` 의 `renderedAs` 가 패키지 쪽과 비슷하다. 판정: 대 보고 같으면 `@agent-os/ui/visual` 에서 나눠 쓴다. `start.ts` 의 `if (command.prepare) copyFonts(...)` 배선을 밟는 시험이 없다. 판정: 시험을 더한다. `WidgetFrame.tsx` 주석의 "안쪽 부품은 `@wide:` 로 가른다"가 쓰는 부품 없는 현재형이다. 판정: 고친다. `NextCommand.prepare` 불리언, `fonts.test.ts` 의 "다섯", 스토리의 폭 삼항은 남긴다(굵기 다섯은 글꼴 CSS 의 사실이고 시험이 그것을 센다. 폭은 둘뿐이다).
- 재현하지 못한 주장: Turbopack 의 "Module not found"(스크래치 Next 앱이 Turbopack 의 루트 제약에 막혔다), 윈도우 호스트 폴더의 링크를 컨테이너가 따라가지 못한다는 것, 카나리아 결과 4. 셋 다 이 세션에서 손으로 본 것이라 문서에 그렇게 적는다.

### 명세 축 (Critical·Major 없음)

- Minor: `embed.ts` 의 "빈 값은 주지 않은 것으로 읽는다"는 명세에 없는 결정이다. 명세 "잘못 준 속성"은 "`theme`이나 `mode`가 목록 밖이면 기본값으로 그리고 `console.error`만 남긴다"이고, `theme=` 은 오류 없이 지나간다. 판정: 고친다. `agent`·`theme`·`mode` 의 빈 값은 준 값으로 읽어 패턴·목록 밖으로 보고, 보일 글인 `heading`·`intro` 만 빈 값을 주지 않은 것으로 읽는다.
- Minor: `themes.ts` 변경은 명세 "바뀌는 것은 그 테스트 도구의 자리뿐이다" 밖이고 근거가 기록에 없다. 판정: 컴포넌트와 토큰은 그대로이고, 까닭을 이 일지(위 결정)와 PR 본문에 적는다.
- Nit: 디자인 시스템 사진 변이 표에서 design-refresh 로 낡은 일곱도 고쳤다. 판정: 남긴다. 표를 고치면 pre-commit 의 `--staged` 가 그 표의 원문을 모두 보아, 낡은 원문을 두면 커밋이 막힌다. 머리 주석에 적었다.
- Nit: `next.config.test.ts` 머리의 "e2e(06)가 판정한다"는 반만 맞다. 06은 `frame-ancestors` 를, 10이 글꼴의 출처 허용을 본다. 판정: 고친다.
- Nit: CI 의 위젯 단계 건너뛰기, 루프백 목록의 가리킴. 판정: 표준 축 6과 판단 항목대로 고친다.
- 맞는 것으로 확인한 것: 에이전트 패턴 셋(`AGENT_PATTERN`, `openapi.json` 의 `StartRun.agent`, `sdk/ids.py`), 화면 문구 넷, 문서들끼리의 일치, Next 설치본으로 잰 헤더의 경로(`/widget` 에 CSP, `/widget/fonts/x.woff2` 에 CSP 와 출처 허용).

### 반영

- 고친 것:
  - 명세 축의 빈 값: `embed.ts` 가 `heading`·`intro` 의 빈 값만 주지 않은 것으로 읽는다. 시험 "빈 값은…" 을 둘로 나눴고(보일 글의 빈 값, 빈 테마와 빈 모드), 패턴 밖 에이전트 목록에 `""` 를 더했다. 처음 둘이 빨갛고 고친 뒤 node·widget-pages 40 이 지났다.
  - 판단 항목의 배선: `start.ts` 에 `launch(command, steps)` 를 두고 시험 "판정을 지난 명령을 따르기" 셋(dev·build 는 준비 뒤에 next, start 는 next 만)을 더했다. 처음 셋이 `launch is not a function` 으로 빨갛고 고친 뒤 13 이 지났다.
  - 표준 축 1의 표지: 표지 없던 변이마다 실패 출력을 본 뒤 고른 단언에서만 나오는 문구를 `expect_output` 으로 넣었다(위 변이 절).
  - 표준 축 2·3·4·5·6, 명세 축의 Nit 둘, 판단 항목의 "셋을 함께 고친다"와 `WidgetFrame` 주석: 아래 문장으로 고쳤다.
- 고치며 새로 쓴 사실 문장(PR 직전 `bug-perf-review` 에 밀 주장으로 넘긴다):
  1. `web/apps/widget/lib/embed.ts` 머리: "보일 글인 `heading`·`intro` 의 빈 값은 주지 않은 것으로 읽는다. 보일 것이 없기 때문이다. `agent`·`theme`·`mode` 의 빈 값은 준 값이라 패턴·목록 밖으로 본다(명세의 "없으면"은 주지 않은 것이다)."
  2. `web/apps/widget/components/templates/WidgetFrame.tsx` 머리: "창이 컨테이너다. 안쪽 부품이 폭으로 모양을 가를 때는 `@wide:`(360px)를 쓴다(web-widget 명세 "테마·모드·밀도·글꼴"). 첫 화면의 부품은 아직 폭으로 가르지 않는다."
  3. `web/apps/widget/next.config.test.ts` 머리: "`frame-ancestors` 는 06 이, 글꼴 응답의 `Access-Control-Allow-Origin` 은 10 이 본다."
  4. `web/apps/admin/tools/loopback.ts`: "위젯의 시작 래퍼(`web/apps/widget/tools/start.ts`)도 같은 목록을 따로 든다. 앱 사이 import 는 층 경계가 막아, 목록을 바꾸면 셋을 함께 고친다(web-widget 티켓 03)."
  5. `src/agent_os/main.py` 의 `LOOPBACK_HOSTS` 위: "관리 화면과 위젯의 시작 래퍼(`web/apps/admin/tools/loopback.ts`, `web/apps/widget/tools/start.ts`)가 같은 목록을 따로 든다. 바꾸면 셋을 함께 고친다."
  6. `web/packages/ui/src/themes.ts`: "선언 파일(`dist/themes.d.ts`)에는 `.ts` 가 남지만, 그것을 읽는 `bundler`·`node10` 해석이 모두 이웃 `.d.ts` 로 풀었다(손으로 봤다)."
  7. `web/packages/ui/src/Entrypoints.stories.tsx` 머리: "일곱째 `./visual` 은 `@playwright/test` 를 들이는 사진 비교 도구라 이 스토리가 불러올 수 없고, 그 이름 풀이는 위젯의 사진 비교(`web/apps/widget/visual/`)의 tsc 와 실행이 본다(web-widget 티켓 03)."
  8. `.claude/rules/web-design.md`: "위젯의 화면은 패키지의 컴포넌트와 토큰으로 그려, 패키지의 모양을 바꾸면 위젯의 사진도 바뀔 수 있다. 그래서 패키지를 바꾸면 `visual:widget`도 치고, 빨개지면 바뀐 사진을 보고 `visual:widget:update`로 위젯의 정답도 다시 만든다."
  9. `.github/workflows/ci.yml` 의 `visual` 잡: "위젯은 설치가 됐으면 패키지의 비교가 실패해도 돈다. 패키지를 바꿔 위젯 사진도 바뀐 것을 한 번에 본다."
  10. `web/apps/widget/tools/start.ts` 의 `LaunchSteps`: "빌드의 입력 준비와 next 부르기. 시험은 둘을 바꿔 끼워 차례를 본다."
  11. `.scratch/design-system/probes/README.md` 의 `static_play_mutations.toml` 행: "2026-10-23(web-widget 03)에 정적 빌드를 여는 길이 `visual/index.ts`로 옮겨 1의 `file`을 옮겼고, `--since origin/main`으로 다시 돌린 1이 기대대로였다". 같은 파일의 `visual_mutations.toml` 행: "2026-10-23(web-widget 03)에 사진 비교 도구가 `visual/index.ts`로 나뉘고 design-refresh로 낡은 원문을 고쳐, `--since origin/main`으로 고른 9가 다시 돌아 모두 기대대로였다".
  12. `.scratch/web-widget/probes/README.md` 의 `widget_app_mutations.toml` 행: "32 모두 빨강을 기대하고, 고른 단언이 빨개졌는지를 `expect_output` 표지(그 단언의 실패 머리나 값이 든 `Received` 줄)로 본다", "루프백 변이는 `tools/start.spawn.test.ts` 를 고르지 않는다. 변이 아래에서는 판정을 지난 `next dev` 가 실제로 선다", "32 모두 표지를 단 판이다(첫 판 28은 표지가 9뿐이었다".
  13. 위젯 변이 표 32번 위의 주석: "빨강은 링크 맵을 맞대는 단언보다 먼저, 경로를 고르는 가드가 workspace 가 아닌 next 의 경로(node_modules 아래)를 거부해서 난다."
- 남긴 것과 이유:
  - `renderedAs` 를 `@agent-os/ui/visual` 에서 나눠 쓰지 않는다. 대 보니 여섯 줄이고 모양이 다르다(위젯의 것은 globals 를 받고 테마가 기본인지도 단언한다. 패키지의 것은 모드와 밀도만 받는다). 나누면 패키지의 사진 시험과 그 변이 표를 함께 고쳐야 해 이 티켓 밖이다.
  - `NextCommand.prepare` 불리언, `fonts.test.ts` 의 "다섯", 스토리의 폭 삼항(위 판단 항목).
  - design-refresh 로 낡은 디자인 시스템 사진 변이 일곱의 고침(위 명세 축 Nit).
  - CI `visual` 잡의 `timeout-minutes: 20`: 최근 main 의 그 잡(run 39948500074)이 4분 11초였다. 위젯 단계가 더하는 시간은 이 PR 의 CI 로 본다.
- 다시 돌린 것: 위젯 변이 표 32(모두 기대대로), 디자인 시스템 `visual_mutations.toml --since origin/main`(9 모두 기대대로), 규칙 문단 카나리아(통과 4, 실험군 하나가 반영으로 더한 문장을 옮겼다). 검증 명령은 아래 검사 절.

## 검사

셀프 리뷰를 반영한 커밋 전 작업 트리에서 돌렸다.

- `uv run ruff check .`·`uv run ruff format --check .`: 초록(1019 files already formatted).
- `uv run python tools/run_checks.py`: 열 모두 Passed(check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright-linux 55.7초, pyright 56.0초, run-hooks 156.2초, web-verify 352.9초, pytest 400.5초).
- `uv run --env-file ../../../.env pytest -m llm`: 7 passed, 320.71초. `src/agent_os/main.py`(루프백 목록 위 주석)를 건드려 돌렸다. LLM 토큰 합계 52,136(입력 50,878, 출력 1,258). 트레이스 10개, 모델 호출 21건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다.
- `pnpm -C web visual`(Docker): 108 passed(5.9분).
- `pnpm -C web visual:widget`(Docker): 5 passed(9.3초).
- `pnpm -C web/apps/admin exec playwright test`: 관리 화면 래퍼의 `loopback.ts` 주석과, 관리 화면도 들이는 `themes.ts` 의 확장자를 바꿔 돌렸다. 첫 실행은 6 passed, 1 failed 였고 그 파일만 다시 돌려도 같은 시험이 빨개, diagnosing-bugs 로 갈랐다. 마지막 전체 실행은 7 passed(35.8초)다.
  - 빨간 시험은 `decision.e2e.ts:12`("멈춘 실행을 허가하면…")의 39행이었다. 허가 뒤 5초 안에 이벤트 영역에 `run_finished` 가 붙지 않았다. 남은 임시 폴더의 트레이스에서는 서버가 실행을 끝냈다(`approval_granted` 13:38:54.93, `run_resumed` +2.75초, `tool_called` +0.25초, `run_finished` +2.03초). 허가부터 끝까지가 약 5초라, 서버가 끝낸 뒤 화면이 트레이스를 다시 읽기 전에 창이 닫혔다. 재실행의 다른 두 시험에서는 그 간격이 3.27·3.81초였고, 13:21에 만들어진 다른 e2e 임시 폴더(전체 묶음의 실행 넷이 들었다. 누가 돌렸는지는 가르지 않았다)에서는 4.25~4.63초였다.
  - 가설 넷(PC 부하, 부하와 무관한 윈도의 재개 비용, 이 브랜치의 `themes.ts` 가 화면의 스트림 끝 처리를 깸, 중계가 스트림의 끝을 붙잡음)을 세웠다. 39행의 기다림만 표지를 단 임시 변경으로 20초로 늘리자 7.1초에 초록이었고 서버 로그에 허가 뒤 트레이스 다시 읽기가 찍혀, 셋째와 넷째가 반박됐다. 되돌린 원래 시험도 다음 실행에서 6.5초에 초록이라, 같은 코드에서 결과가 부하에 따라 갈린다(첫째). 빨간 두 번 가운데 첫째는 내가 `sibling_overlap --move` 를 함께 돌린 때였고, 둘째 때의 부하는 재지 않았다. 임시 변경은 되돌렸고(`git diff` 빔, 표지 grep 0), 내 실행이 남긴 임시 폴더는 지웠다.

## 회고

후보 여섯. 승인 2(기존 행의 회차 1, 새 행 1), 기각 2, 일지에만 2. 넘긴 것은 없다.

1. 위젯 변이 표의 빨강 기대 28 가운데 19에 표지(`expect_output`)가 없었고 셀프 리뷰 표준 축이 잡았다 — 승인(회차로 세는 것). 변이 표를 열 때 실리는 `.claude/rules/probes.md` 첫 항목을 어겼고, 열린 대기열 350이 같은 처방(`--since` 로 고른 빨강 변이에 표지가 없으면 `--check` 가 알린다)을 든다. 350에 회차를 더해 2회차다.
2. 표지를 고르려고 표지 없는 변이를 돌렸더니 `tools/mutate.py` 의 `_details` 가 출력의 끝 10줄만 보였고, vitest 변이에서는 그 10줄이 마지막 실패 블록의 코드 조각과 구분선이라 고른 단언의 실패 머리와 `Received:` 줄이 보이지 않았다. 끝 120줄을 보이게 고친 도구의 스크래치 사본을 지어 23을 다시 돌렸다 — 승인(새 행 455, 1회차). 사건은 그 사본을 짓고 다시 돈 비용이고, 처방은 도구 층(표지가 없거나 판정이 어긋난 회차에 실패 머리 줄도 보인다)이며 PR 하나로 되돌릴 수 있다. 도구는 독스트링대로 "출력의 끝"을 보였으므로 고침이 아니라 더하는 것이고, 세 번째에 반영한다.
3. 게이트 파이프 훅 독스트링의 넘친 줄을 `tools/rewrap_comments.py` 로 감자 짧게 끝난 문장 줄이 앞줄의 꼬리를 받아 두 문단이 이어졌고, 가운뎃점 뒤 줄바꿈 자리에 공백이 생겼다. 손으로 되돌렸다 — 기각. 스크래치 `rewrap_repro.py` 로 지금 파일에서 다시 내 보니 같은 두 동작이 났고, 둘 다 그 도구 독스트링의 못 보는 것("혼자 선 짧은 줄은 문단의 일부로 보아 앞줄에서 넘친 꼬리를 받는다", 공백 없는 줄바꿈)에 적혀 시험이 지금 동작으로 고정한다. 도구가 감은 줄 수(`감았다(12줄)`)를 알려 diff 에서 바로 보였다.
4. 이 세션의 다른 실수(표 둘을 한 명령에 넘김, `cd web`, 변수가 든 git 명령, E501, 중간 문장의 영어, 변이 실행 중 편집, 군청 스토리 기준선 시험 0개) — 기각. 차례로 변이 도구의 인자 오류(종료 2), 훅, 앱의 워크트리 가드, ruff 와 줄 폭 훅, `hook_midturn_korean`, `hook_edit_during_mutate`, 변이 도구의 기준선 판정이 그 자리에서 막거나 알렸다. 셀프 리뷰가 잡은 나머지(빈 질의 값, 배선 시험, 문장 고침)는 리뷰가 제 몫을 한 것이다.
5. 디자인 시스템 사진의 기준선이 한 번 1 failed, 85 passed 였고 다시 돌리자 86 passed 였다(위 변이 절) — 일지에만. 사진 하나가 픽셀 차이로 빨갰다가 다시 돌면 초록인 일은 대기열 414가 센다(main 에서 3회차, 셋 모두 다른 사진이다). 그러나 이번에는 변이 도구가 집계 줄만 남겨 실패한 시험의 이름도, 그 실패가 픽셀 차이였는지 부하 아래의 다른 실패였는지도 모른다. 같은 체크아웃에서 리뷰 서브에이전트 둘이 명령을 돌리기 시작한 때였다. 414가 세는 꼴인지 가를 수 없어 회차를 더하지 않는다.
6. 관리 화면 e2e `decision.e2e.ts:12` 가 PC 부하 아래에서 두 번 빨갰고 다음 실행에서 초록이었다(위 검사 절) — 일지에만. 부하 아래에서 시간 창을 가진 시험이 빨개지는 일은 대기열 306이 끝이 열린 결함 종류로 받아들여 닫았고, 같은 종류의 새 사례는 회차를 더하지 않고 일지에만 적는다.

`uv run python tools/queue_open_rows.py`(이 판과 `--ref origin/main`)의 만료할 행은 없었다.

## 다음

- 03이 병합되면 04(Blocked by 03)가 열린다. 시작 래퍼의 자리는 `web/apps/widget/tools/start.ts` 이고(티켓의 "이 티켓이 정한 것" 1), 04는 그 래퍼가 `AGENT_OS_SITE_FILE` 을 넘기게 하고 `next.config.ts` 의 `frame-ancestors 'none'` 을 합친 허용 출처로 바꾸며 Node 의 TOML 파서를 정한다(04 티켓 15·16·19행).
- 01(계약)은 나란히 도는 세션이 한다. 02는 01을, 05는 01과 04를 기다린다. 06은 02와 05를, 07·10·11은 06을 기다린다. `frame-ancestors` 의 e2e 는 06이, 글꼴 응답의 `Access-Control-Allow-Origin` e2e 는 10이 든다.
- 루프백 목록은 세 벌이다(`src/agent_os/main.py`, `web/apps/admin/tools/loopback.ts`, `web/apps/widget/tools/start.ts`). 바꾸면 셋을 함께 고친다. 세 자리 모두에 적었다.
- `sibling_overlap` 이 든 01 워크트리와의 글자 충돌 후보(`.scratch/web-widget/probes/README.md`, `README.md`)는 나중에 병합하는 쪽이 푼다.
- 이 PR은 워크트리에서 병합한다. 주 체크아웃은 당기지 않는다.
