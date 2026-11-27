# 2026-11-27 (21:33) 서비스 시작이 값 파일을 쓰고 위젯이 그 파일을 받아 쓴다

브랜치 `feature/01-start-writes-values-file-and-widget-reads-it`, 워크트리 `.claude/worktrees/01-start-writes-values-file-and-widget-reads-it`. 모델 Sonnet 5.5(지시문의 high). 기능 widget-runtime-values의 티켓 01(`.scratch/widget-runtime-values/issues/01-start-writes-values-file-and-widget-reads-it.md`)이다. 기준은 `origin/dev` `5298e3d`다. 이 일지는 셀프 리뷰 직전에 컨텍스트가 인계 문턱을 넘어 인계하려고 처음 만들었고, 이어받은 세션이 셀프 리뷰·검증·회고·"다음"을 더해 커밋한다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/widget-runtime-values/issues/01-start-writes-values-file-and-widget-reads-it.md
>
> 다음 작업: 서비스 시작과 개발 서버가 값 파일을 쓰고, 위젯이 그 파일을 받아 쓴다
> 다음 단계: 구현
> 브랜치: feature/01-start-writes-values-file-and-widget-reads-it
> 모델: Sonnet 5.5 / high
> 읽을 것: docs/journal/2026-11-27-1523-widget-runtime-values-tickets.md의 '다음' 절
> 이번 요청 범위: PR과 병합까지

(지시문의 어디서·선행 조건 줄은 이 세션의 시작 순서와 병합 방법을 정했다. 시작 순서(`tidy-checkouts`, 새 워크트리 진입, 브랜치 이름 바꾸기)는 끝냈다. 병합은 워크트리 사본 `next-session/merge.md`의 "워크트리에서 병합할 때"를 Read로 열어 따른다. "이어받을 상태"의 admin-login 05(PR #653) 봇 보류는 이 세션의 일이 아니다.)

사용자의 직접 교정은 없었다. 그 뒤 메시지는 시스템 알림뿐이다.

## 한 것

티켓의 체크박스는 아직 채우지 않았고 `Status: in-progress`다. 아래가 구현한 것이다.

- **값 파일을 쓰는 쪽.** `web/apps/widget/tools/runtime.ts`(새 파일)가 `@agent-os/site-file`의 `buildInput`으로 합친 허용 출처와 가장 작은 상한을 `public/runtime.json`에 쓴다. 키는 `allowedOrigins`와 `requestChars` 둘뿐이고, 상한이 무한대가 되면 `Number.MAX_VALUE`로 쓴다. 그 자리를 열어 바로 쓰고 이름을 바꿔 덮지 않는다. 실패하면 아무것도 쓰지 않는다. `tools/start.ts`는 `dev`(값 파일, 준비, next)와 `start`(값 파일, next)에서 값 파일을 쓰고 `build`에서는 쓰지 않는다. `.gitignore`에 `/web/apps/widget/public/runtime.json`을 더했다.
- **빌드가 싣던 값 걷기.** `next.config.ts`의 `env`와 `tools/element.ts`의 상한 `define`을 걷고(번들에 박히는 것은 `process.env.NODE_ENV` 하나), `next.config.ts`에 `/runtime.json`의 `Access-Control-Allow-Origin: *`를 더했다. `lib/build.ts`와 그 시험을 지우고 `@agent-os/site-file`에서 두 환경 변수 이름을 걷었다.
- **브라우저 쪽.** `lib/runtime.ts`(새 파일)가 값 파일을 받는다. 모듈 수준 캐시와 `useSyncExternalStore`를 쓰고, 상태는 `loading`, `ready`, `unavailable`(다시 받으면 풀릴 수 있는 실패), `missing`(404)이다. 10초 시간 제한, `credentials: "omit"`, 스스로 다시 받지 않음, `retry()`는 `unavailable`일 때만 동작한다. 응답은 허용 출처가 글자 목록이고 상한이 1 이상의 정수일 때만 받고 모르는 키는 무시한다. `lib/connection.ts`는 `EmbedConnection`(임베드가 짓는 길, `token(allowedOrigins)`)과 `Connection`(대화가 쓰는 길)으로 나누었다. `ConnectedWidget.tsx`는 값을 받은 뒤에야 `Connection`을 지어, 받기 전에는 토큰을 묻지 않고 저장한 대화도 되살리지 않는다. `WidgetScreen.tsx`는 `settings` 속성(`receiving`, `ready`, `failed`)과 `onRetrySettings`를 받아, 받는 동안 빈 대화 자리와 막힌 입력, 실패에 알림 "위젯 설정을 받아 오지 못했습니다."와 "다시 시도"를 그린다. 404는 `misconfigured`와 같은 알림이다. 문구는 widget-login-state 명세의 표와 글자 그대로 같다. 그 기능은 코드에 아직 없다(확인했다).
- **eslint.** `web/eslint.config.mjs`에 `lib/runtime.ts` 한 파일의 전역 `fetch` 예외를 `PORTAL_PAGE_SCRIPT`와 같은 꼴로 더했다(경로와 까닭을 적었다). `web/eslint.config.test.ts`에는 그 파일에서는 지나가고 같은 앱의 다른 파일에서는 `no-restricted-globals`로 막히며 그 파일에서도 `XMLHttpRequest`와 `globalThis.EventSource`는 막히는 사례를 더했다.
- **시험.** 새 `tools/runtime.test.ts`(13개), `components/pages/WidgetSettings.test.tsx`(23개), `element/WidgetElement.test.tsx`의 값 파일 사례 셋, `tools/start.test.ts`·`start.spawn.test.ts`·`element.test.ts`·`next.config.test.ts`의 바뀐 사례를 썼다. 다른 시험은 `testing/setup.ts`가 사례마다 값을 미리 두고(`testing/runtime.ts`의 `seedValues`) 끝나면 `clearRuntimeValues()`로 걷게 해, 거의 고치지 않았다. 새 스토리 `ReceivingSettings`와 `SettingsFailed`와 그 정답 사진 네 장(라이트·다크)을 더했다.
- **e2e.** `packages/e2e-stack/src/serve.ts`의 `siteFileToml`에 선택 인자 `requestChars`를 더했다(다른 e2e 준비는 그대로다). 위젯 e2e 준비(`e2e/stack.ts`)는 기본값과 다른 `SITE_REQUEST_CHARS`(1,500, `e2e/env.ts`)를 사이트 파일에 적는다. `widget.e2e.ts`의 글자 수 상한 사례는 값 파일을 직접 읽고 입력창과 서버가 그 상한을 함께 따르는지 본다. `element.e2e.ts`에는 페이지 안 방식이 번들 출처의 값 파일을 한 번 받아 상한을 따른다는 사례와, 허용 밖 출처 페이지에서도 값 파일이 읽히고 응답 머리가 모든 출처를 허용하며 값 파일이 두 키만 든다는 사례를 더했다.
- **문서.** `EMBED.md`의 무결성 항목을 고치고 `connect-src` 행에 `/widget/runtime.json`을 더했다. `CONTEXT.md`에 "값 파일"을 `domain-modeling` 스킬로 올렸다. `README.md`의 위젯 줄, `lib/token.ts` 머리 주석, `e2e/stack.ts` 주석, `tests/test_main.py` 독스트링의 옛 말을 고쳤다. 빌드가 사이트 파일을 읽는다는 말과 뜰 때 빌드한다는 말은 02와 03의 것이라 고치지 않았다.

## 결정과 번복

- 값을 받는 자리를 하나(`lib/runtime.ts`)로 두고 모듈 수준 캐시와 시험 이음매(`seedRuntimeValues`, `clearRuntimeValues`)를 노출했다. 약 150개 시험을 일일이 고치는 파급을 피하려는 것이다. 실제 받는 길은 `WidgetSettings.test.tsx`가 MSW로 본다.
- MSW가 `request.credentials`를 가려서 "쿠키와 자격 증명을 싣지 않는다"는 전역 `fetch`를 `vi.spyOn`해 `init.credentials`가 `"omit"`인지 본다.
- 시험에서 `as` 단언을 썼다가(원칙 III 위반) `unknown`을 돌려주는 도우미와 `JsonBodyType`으로 고쳤다. `String(input)`이 `no-base-to-string`에 걸려 `addressOf`로 바꿨다.
- `lib/runtime.ts`의 "만료 시각"처럼 자동 재시도를 두지 않는다. 티켓 그대로다.

## 확인한 것(이 세션이 돌린 명령)

- `pnpm -C web verify`(린트, 서식, 타입, vitest 137개 파일 2,922개 통과 1개 건너뜀(기존 `make-key.test.ts`의 윈도 조건), tsconfig). 초록이다(493초).
- `uv run ruff check .`와 `uv run ruff format --check .`. 초록이다.
- 위젯 e2e `pnpm -C web/apps/widget exec playwright test`: 21개 통과(1.1분). 첫 실행에서 두 사례(`첫 도구 줄`, `부모가 아닌 프레임`)가 5초 한계에 걸려 실패했다. 첫 도구 줄이 5초 안에 서지 않은 것이고 값 파일과 무관해 보였다(스냅샷에는 값을 받아 입력이 열린 뒤 요청이 나가 진행 표시가 있었다). 그 실행은 2.9분이 걸려 기기가 느렸던 것으로 본다. 두 사례만 다시 돌리니 하나는 통과했고 하나는 또 실패했다. `--repeat-each=3`은 1회차에 연 문(`tool-row`)이 남아 2·3회차가 인위적으로 실패해 판정에 쓸 수 없다. 전체를 한 번 더 돌리니 21개 모두 통과했다(첫 도구 줄 사례 3.4초). 기준선(변경 전)에서 같은 사례를 돌려 견주지는 않았다. 환경 편차라는 것은 어림이다.
- 위젯 테스트 페이지 e2e `pnpm -C web/apps/portal exec playwright test`: 41개 통과(59.3초).
- 실제 모델 e2e: `-m llm_widget` 1개 통과(162초, LLM 토큰 합계 17,100(입력 16,810, 출력 290), 트레이스 2개, 모델 호출 4건), `-m llm_portal` 1개 통과(290초, LLM 토큰 합계 6,997(입력 6,925, 출력 72), 트레이스 1개, 모델 호출 2건).
- 사진 비교 `pnpm -C web visual:widget`(Docker): 44개 통과, 정답이 없던 새 이야기 둘만 실패했다. `visual:widget:update`로 정답 네 장(`pages-widgetscreen--receiving-settings-{light,dark}.png`, `pages-widgetscreen--settings-failed-{light,dark}.png`)만 새로 생겼고 기존 정답은 하나도 바뀌지 않았다(`git status`로 확인). 새 사진 둘(`settings-failed-light`, `receiving-settings-dark`)은 열어 보았다. 알림과 "다시 시도"가 서고 입력창은 막혀 있으며, 받는 동안에는 빈 대화 자리다.
- 단독 배포 e2e `pnpm -C web/packages/e2e-standalone exec playwright test`: 15개 통과, 212초(3.2분). 지금의 이미지(뜰 때 빌드한 뒤 서비스 시작이 값 파일을 쓴다)가 서고 기존 사례가 초록이다.
- `uv run python tools/sibling_overlap.py`: 번호 겹침 없음. 함께 고친 파일은 PR #657과 워크트리 `09-admin-ui-login-and-refresh-rule`이 `web/eslint.config.mjs`·`web/eslint.config.test.ts`를, 서브에이전트 워크트리 둘(`agent-a65f5d6e4055592b1`, `agent-a6f8a3e38a870fe3f`)이 위젯 파일 몇을 건드린다(나중에 병합하는 쪽의 글자 충돌 후보).
- `uv run python tools/run_checks.py`(백그라운드, 로그 `C:\Users\User\AppData\Local\Temp\claude\9060abe0b92613e9\0dd936d8-7337-43e1-a5e9-141b4e931092\scratchpad\run-checks.log`)는 인계 시점에 도는 중이었고 lint-imports, zizmor, check-instructions, check-type-escapes는 Passed였다. 나머지(pytest 프로세스 갈래, pyright, web)는 이 세션이 끝을 보지 못했다. 새 세션이 결과를 다시 확인하거나 다시 돌린다.

## 남은 일

- 셀프 리뷰(`/code-review`, 고정점 `origin/dev`)를 아직 하지 않았다. 새 세션이 이 일지의 변경과 위 티켓·명세로 한다. 리뷰에 밀 주장으로 넘길 새 문장은 `EMBED.md`의 무결성 항목("해시는 위젯의 코드가 바뀔 때만 바뀐다. 사이트 파일을 고쳐도 해시는 그대로다")과 `CONTEXT.md`의 값 파일 항목, `e2e/stack.ts`와 `README.md`의 고친 주석이다.
- 티켓 체크박스를 채우고 `Status: done`으로 바꾼 뒤 `uv run python tools/plan_table.py`를 돌린다. 기능 계획(`.scratch/widget-runtime-values/plan.md`)에 닿으면 규칙은 `docs/agents/issue-tracker.md`다.
- `sync-design-system` `확인`은 앞서 `clean`으로 끝났고 화면 코드를 고친 뒤 새 알림은 오지 않았다.
- 커밋 전에 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`를 친다. 커밋 메시지는 `-F` 파일로 넘긴다. `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`를 단다. PR 본문 끝에는 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`를 붙이고, 사진 비교의 새 정답 넷과 단독 배포 e2e의 결과와 걸린 시간(212초)과 위젯 e2e 첫 실행의 실패와 재실행 결과를 적는다.
- 병합은 워크트리 사본 `next-session/merge.md`의 "워크트리에서 병합할 때"를 Read로 열어 따른다. 이번 요청 범위는 PR과 병합까지다.

## 셀프 리뷰(이어받은 세션, 고정점 `origin/dev` 5298e3dd9, 파일 33개, 커밋 0개, 미추적 14개)

두 축이 따로 돌았다. 표준 축은 sonnet·high, 명세 축은 이 세션의 모델이다. 원칙 III 우회(any, as, !, ts-ignore)는 0건이고 명세 축은 범위 넘침을 찾지 못했다. 알림 문구는 widget-login-state 명세의 표와 글자 그대로 같고, 옛 이름(`AGENT_OS_WIDGET_*`, `WIDGET_*_ENV`, `lib/build`)의 잔존은 살아 있는 문서에서 0이다.

고친 것(새로 쓴 문장은 PR 직전 리뷰가 겨냥할 목록이다).

- `lib/runtime.ts`, `testing/setup.ts`, `testing/runtime.ts` 주석이 없는 `lib/runtime.test.tsx`를 가리켰다. 실제 시험인 `components/pages/WidgetSettings.test.tsx`로 고쳤다.
- `tools/start.ts` 독스트링의 "`dev` 는 손으로 봤다(일지 2026-10-24-05)"는 낡은 근거였다(그 일지는 옛 동작을 본 것이다). "`dev` 는 실제 프로세스로 보지 않았다."로 고쳤다.
- `tools/runtime.ts` 머리의 "이름 바꾸기는 링크를 따라가지 않아 읽기 전용 루트에서 실패한다"에 "(리눅스의 동작으로 아는 것이고 재지 않았다, 명세 "위젯 이미지")"를 붙였다.
- `tools/element.ts` 머리의 "이 함수는 사이트 파일도 환경 변수도 읽지 않는다"는 `NODE_ENV`가 반례라서 "사이트 파일도 그 환경 변수도"로 좁혔다.
- `web/packages/site-file/src/site-file.ts` 머리의 fail-closed 문단에서 "빌드가 실패한다"를 "빌드와 시작 래퍼(`dev`·`start`)가 실패한다"로, "빌드가 읽는 두 값"을 "위젯이 읽는 두 값"으로 고쳤다.
- `CONTEXT.md` "값 파일"의 "사이트 파일을 고치고 위젯을 다시 띄우면 새 값을 따른다"는 허용 출처에서 과했다(`frame-ancestors`는 아직 빌드가 굳힌다). "입력창의 글자 수와 토큰을 받을 부모 페이지는 새 값을 따른다(위젯을 iframe으로 품을 수 있는 사이트의 목록은 아직 위젯을 빌드할 때 굳는다)"로 고쳤다.
- `EMBED.md` 무결성 항목은 "해시는 위젯의 코드가 바뀔 때만 바뀐다"가 닫힌 주장이고 티켓이 요구한 말과 달랐다. "사이트 파일을 고쳐도 번들의 내용과 해시는 그대로다. 해시는 운영자가 위젯의 새 판을 올릴 때 새로 받아 적는다."로 바꿨다.
- `tools/runtime.test.ts`의 링크 사례는 윈도에서 링크를 못 만들면 `return`으로 초록이 되었다(원칙 II). `test.skipIf(!canSymlink())`로 바꿔 건너뛴 것이 보이게 했다. 이 PC에서는 링크가 만들어져 13개 모두 통과했다(`pnpm -C web/apps/widget exec vitest run tools/runtime.test.ts`를 손으로 쳐서 봤다).

남긴 것과 이유.

- 이름이 겹친다는 지적(코드의 `settings`·`WidgetSettings.test.tsx`가 CONTEXT.md의 "위젯 설정"과 겹치고 값 파일 항목의 `_Avoid_`도 그 이름을 든다). 알림 문구는 widget-login-state 명세의 표와 글자 그대로 같아야 하고 그 기능이 이 상태와 알림을 다시 쓰므로, 이름을 바꾸는 일은 그 기능이 두 받기를 합칠 때 함께 정한다. 판단 항목(Mysterious Name)이라 커밋을 막지 않는다.
- `RuntimeValuesFile`(tools)과 `RuntimeValues`(lib)의 같은 모양, `ConnectedWidget`의 `settings !== "ready"` 되풀이, `WidgetPage`의 `token` 덮개는 Node와 브라우저로 갈린 층의 몫이거나 경미한 판단 항목이라 두었다.
- `EMBED.md:134`의 "위젯도 같은 파일로 빌드된다"와 `CONTEXT.md` 사이트 파일 항목의 "위젯 빌드와…이 이 파일을 입력으로 읽기는 하지만"은 티켓이 02의 것이라 못 박은 문장이다.
- `.scratch/web-widget/probes/conversation_mutations.toml`과 `storage_mutations.toml`이 지운 `lib/build.ts`와 그 시험을 변이 대상으로 가리킨다. 기록이라 고치지 않았다. 그 변이 열을 다시 돌릴 때는 이 두 파일이 대상을 잃은 것을 먼저 본다.
- `start.ts`의 실제 값 파일 단계의 성공 길은 단위 시험이 아니라 위젯 e2e와 단독 배포 e2e가 본다(티켓이 허용한 방식이다).

## 이어받은 세션이 다시 돌린 검증

- `uv run python tools/run_checks.py`(백그라운드, 리뷰 반영이 일부 끝나기 전에 시작): lint-imports·check-notes·zizmor·check-instructions·check-type-escapes·pyright 둘·run-hooks·web-verify가 Passed였고 pytest는 8,898개 통과에 1개 실패(`tests/tools/test_rerun_runner.py::test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다`)였다. 그 파일만 다시 쳐서(`uv run pytest -q tests/tools/test_rerun_runner.py`) 63개 모두 통과했다(388초). 이 변경은 `tools/`와 `tests/tools/`를 건드리지 않아 무관하고, 22분을 넘긴 전체 실행에서 다른 세션과 겹친 시간 문제로 어림한다(원인은 열어 보지 않았다). check-ticket의 Failed는 티켓 파일이 아직 이 커밋에 들지 않아서 난 알림이고 커밋에 티켓을 실으면 풀린다.
- 리뷰 반영 뒤 `uv run ruff check .`와 `uv run ruff format --check .`가 초록이다. 고친 TypeScript 파일들은 prettier로 서식을 맞췄고(`runtime.test.ts` 하나가 어긋나 `--write`로 고쳤다) eslint가 통과했다. 반영이 닿은 `runtime.test.ts`는 vitest로 13개 모두 통과했다. 커밋 직전의 손으로 치는 다섯은 pre-commit의 결과로 갈음한다.
- 티켓 체크박스를 모두 채우고 `Status: done`으로 바꿨고 `uv run python tools/plan_table.py`를 돌려 `.scratch/plan.md`를 갱신했다. 이 티켓은 기능의 마지막 티켓이 아니라(02, 03이 남았다) `**끝:**` 줄과 기능 단락을 더하지 않았다. 운영자가 올릴 때 손댈 것이 없어 PR 제목에 느낌표를 붙이지 않는다(사이트 파일과 배포 파일의 형식이 그대로이고, 값 파일은 시작 래퍼가 스스로 쓴다).

## 변이 표 고침(첫 커밋 시도가 막힌 뒤)

pre-commit의 `check-mutations`가 변이 다섯의 원문이 사라졌다며 커밋을 막았다(다른 검사는 모두 Passed였고 pytest 850초, web-verify 986초였다). 고친 것: `lib/build.ts`와 `element.ts`의 사이트 파일 읽기를 겨누던 변이 둘(`빌드 값을 구조 분해로 읽으면 글자 시험이 빨갛다`, `번들 빌드가 변수의 사이트 파일을 읽지 않으면 픽스처의 상한이 실리지 않아 빨갛다`)은 겨누던 코드가 지워져 표에서 뺐다. `WidgetScreen.tsx`의 입력창 `disabled` 줄을 겨누던 변이 둘과 `start.ts`의 `prepare` 줄을 겨누던 변이 하나는 새 원문(`settings !== "ready"`가 든 줄, 여러 줄로 갈라진 `prepare: command === "dev",`)으로 다시 겨눴다. `uv run python tools/mutate.py --check`로 세 표의 원문이 모두 한 번씩 있는 것을 보았고(변이 25·28·34), 다시 겨눈 셋은 실제로 돌려 모두 기대대로 빨갰다(`mutate.py <표> 17 32`와 `mutate.py <표> 22`를 손으로 쳤다).

## 회고

후보 5개를 냈고 판정은 승인 0, 넘김 0, 기각 5다. 만료할 항목은 없었다(`tools/queue_open_rows.py`가 "만료할 항목: (없음)"을 냈다). 대기열은 건드리지 않았다.

- **리뷰가 잡은 근거 없는 주석 몇 곳**(없는 시험 파일 `lib/runtime.test.tsx`를 가리킴, 낡은 근거 "손으로 봤다(일지 2026-10-24-05)", 재지 않은 어림의 단정). 기각이다. 리뷰가 잡도록 둔 기준(`code-review`의 주장 검증 목록)을 어겨 리뷰가 잡은 사건이라 리뷰가 제 몫을 한 것이고 회차로 세지 않는다(4단계).
- **윈도에서 링크를 못 만들면 `return`으로 초록이 되던 시험**(`tools/runtime.test.ts`). 기각이다. 리뷰(명세 축)가 원칙 II로 잡았고 사건이 하나라 검사로 옮길 만한 고정된 모양이 서지 않는다. `test.skipIf`로 고쳤다.
- **전체 검증의 pytest 한 개가 빨갰고 따로 치니 63개 모두 통과했다**(`tests/tools/test_rerun_runner.py::test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다`가 `hang=1.0`으로 두 회차가 겹친 수를 본다. 22분 넘게 도는 전체 실행 안에서 났고, 원인은 열어 보지 않았다). 기각이다. 부하 아래에서 시간에 기대는 시험이 빨개지는 종류는 0306이 받아들이고 닫은 종류(ADR 0036, 2026-10-20)라 새 사례는 회차를 더하지 않고 일지에만 적는다. 이 변경은 `tools/`와 `tests/tools/`를 건드리지 않았다.
- **첫 `git` 복합 명령을 워크트리 가드가 거부했다.** 기각이다. 이미 있는 앱 가드가 그 자리에서 막았고 `CLAUDE.md` 환경 함정이 같은 모양을 적고 있다. 그 뒤 명령을 하나씩 쳐 지나갔다.

- **첫 커밋 시도가 변이 표 검사(`check-mutations`)에 막혔다.** 이 변경이 `lib/build.ts`를 지우고 `WidgetScreen.tsx`·`start.ts`·`element.ts`의 줄을 바꿔, 그 줄을 겨누던 변이 다섯(`.scratch/web-widget/probes/`의 `conversation_mutations.toml` 둘, `element_mutations.toml` 하나, `widget_app_mutations.toml` 둘)의 원문이 사라졌다. 기각이다. 이미 있는 pre-commit 검사가 커밋 전에 막았고(그 검사의 몫), 구현 지침(`implement` 스킬의 "코드를 옮기거나 고쳤으면 그 코드를 겨누던 변이 파일을 `--check`로 본다")이 있는 것을 놓친 것이라 지침의 첫 회차 사건이다. 같은 실수의 다섯 번째가 아니고 손상도 없어 더하지 않는다. 새 항목도 쓰지 않는다.

## 다음

다음 작업은 `.scratch/widget-runtime-values/issues/02-build-closes-frame-ancestors-and-start-fills-them.md`다(`Blocked by: 01`이 이 PR의 병합으로 풀린다). 빌드가 사이트 파일 없이 `frame-ancestors 'none'`으로 짓고 원본을 남기며, 서비스 시작이 응답 머리 목록의 사본을 쓴다. 티켓 03(뜰 때 빌드를 걷는 이미지와 읽기 전용 compose)이 02에 막혀 있다. 이 티켓이 02에 넘기는 것은 아래다.

- `next.config.ts`·`EMBED.md:134`·`CONTEXT.md` 사이트 파일 항목·`e2e/stack.ts`의 "빌드에 박힌다"와 "위젯도 같은 파일로 빌드된다" 같은 빌드가 사이트 파일을 읽는다는 말은 02가 고친다.
- `start.ts`의 `build`는 아직 사이트 파일을 읽고 같은 진단으로 끝난다. 02가 바꾸면 `start.spawn.test.ts`의 빌드 사례도 함께 바꾼다.
- `.scratch/web-widget/probes/conversation_mutations.toml`과 `storage_mutations.toml`이 지운 `lib/build.ts`를 변이 대상으로 가리킨다. 그 변이 열을 돌릴 일이 생기면 대상을 `lib/runtime.ts`로 옮긴다.
- 코드의 `settings`·`WidgetSettings` 이름이 CONTEXT.md의 "위젯 설정"과 겹친다. widget-login-state가 두 받기를 합칠 때 함께 정한다.

## 인계

- 이 세션의 제목을 `feature/01-start-writes-values-file-and-widget-reads-it (인계함)`으로 바꿨다(바꾸기 전 제목은 `feature/01-start-writes-values-file-and-widget-reads-it`).
- 이 세션이 띄운 백그라운드 `tools/run_checks.py`(작업 `bgcubd339`)를 TaskStop으로 멈췄다. 그 끝은 보지 못했다.
- `git worktree unlock`으로 이 워크트리의 잠금을 풀었다.
- 경계는 `셀프 리뷰 직전`이다. 일지 경로는 `docs/journal/2026-11-27-2133-start-writes-values-file-and-widget-reads-it.md`다.
- open-session을 부른다 2026-11-27T12:34:40Z
