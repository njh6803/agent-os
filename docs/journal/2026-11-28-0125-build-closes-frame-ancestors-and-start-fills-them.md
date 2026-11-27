# 2026-11-28 (01:25) 위젯 빌드가 사이트 파일을 읽지 않고 서비스 시작이 허용 출처를 넣는다

브랜치 `feature/02-build-closes-frame-ancestors-and-start-fills-them`, 워크트리 `.claude/worktrees/02-build-closes-frame-ancestors-and-start-fills-them`. 모델 Sonnet 5.5(지시문의 high). 기능 widget-runtime-values의 티켓 02(`.scratch/widget-runtime-values/issues/02-build-closes-frame-ancestors-and-start-fills-them.md`)이다. 기준은 `origin/dev` `0a2662c`(PR #658 병합)다.

## 사용자 프롬프트

> 사용자: .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/widget-runtime-values/issues/02-build-closes-frame-ancestors-and-start-fills-them.md
>
> 이번 요청 범위: PR과 병합까지

(지시문에는 이 PR에서 `.scratch/widget-login-state/`의 계획에 문서 한 줄을 더하라는 인계 문장이 있었다. 아래 "한 것"에 적었다. 사용자의 직접 교정은 없었다. 그 뒤 메시지는 시스템 알림뿐이다.)

## 한 것

- **빌드가 사이트 파일을 읽지 않는다.** `next.config.ts`를 `(phase) => NextConfig` 함수로 바꿨다. 개발 서버 단계(`PHASE_DEVELOPMENT_SERVER`)만 `widgetValues(process.env).allowedOrigins`로 응답 머리를 내고, 빌드와 서비스 시작 단계는 사이트 파일을 읽지 않고 `frame-ancestors 'none'`을 낸다. `@agent-os/site-file`의 `buildInput`은 `widgetValues`로(`siteFileInput`은 `siteFileValues`, `BuildInput`은 `WidgetValues`) 이름을 바꿨고 진단 끝 문장은 "고친 뒤 위젯을 다시 띄운다."로 고쳤다.
- **원본을 남기고 사본을 쓴다.** 새 `tools/manifest.ts`. 바꿀 자리는 머리 이름이 대소문자를 가리지 않고 `content-security-policy`이면서 값이 `frame-ancestors`로 시작하는 자리가 정확히 하나이고 값이 글자 그대로 `frame-ancestors 'none'`일 때뿐이다. 아니면 아무것도 쓰지 않고 "사이트 파일의 문제가 아니라 그 판의 산출물의 문제"라는 진단과 함께 종료 1이다. 사본은 `.next/routes-manifest.json`을 열어 바로 쓴다(이름 바꾸기로 덮지 않는다). 원본(`.next/routes-manifest.original.json`)은 래퍼의 빌드가 프로세스 `exit` 처리기에서 복사한다. Next 16.3.6의 `next build`가 `program.parse` 뒤 기다리지 않고 돌아오고 마치면 `process.exit(0)`으로 끝나기 때문이다(고른 까닭과 대안은 `manifest.ts` 머리 주석).
- **서비스 시작의 차례와 빌드 도구.** `tools/start.ts`: build는 "원본을 남기게 하고", start는 "값 파일, 사본, next", dev는 "값 파일, 준비, next"다. 글꼴 복사와 `element.ts`(Vite, Tailwind)는 `prepare`가 동적으로 불러 서비스 시작 길은 빌드 도구를 불러오지 않는다.
- **시험.** 새 `tools/manifest.test.ts`(자리 규칙, 원본/사본 파일, `exit` 처리기를 자식 프로세스로 확인), `tools/start.test.ts`(차례), `tools/start.spawn.test.ts`(`module.registerHooks`로 `next`와 빌드 도구를 가로채는 실제 래퍼 프로세스 31개. 서비스 시작이 Vite·Tailwind·TypeScript를 불러오면 실패하는 훅과 임시 앱 폴더 사례), `next.config.test.ts`, `site-file.test.ts`. 시험이 한 번에 초록이라 `start.ts`에 정적 `@agent-os/ui/fonts` import를 넣어 spawn 시험 8개가 빨개지는 것을 보고 되돌렸다.
- **e2e.** 위젯 e2e 준비는 빌드에 미끼 사이트 파일(허용 출처 `http://decoy.localhost:9`, 상한 999)을, 띄울 때 진짜 파일을 준다. 빌드가 사이트 파일을 읽으면 원본의 자리가 `'none'`이 아니라 준비의 `start`가 진단과 함께 멈춘다. 위젯만 다시 띄우는 손잡이는 준비 프로세스 안의 작은 HTTP 서버(`e2e/control.ts`)이고, 주소를 환경 변수로 넘겨 사례가 `restartWidget`으로 부른다(앞 위젯을 끄고 같은 포트로 새 사이트 파일로 다시 띄운다). 새 사례는 허용 출처를 `other`, 상한을 777로 다시 띄워 응답 머리, 값 파일, 입력창 상한, 품기/막기가 모두 새 값을 따르는지 보고 끝에 원래 파일로 되돌린다. 위젯 테스트 페이지 e2e 준비도 미끼로 빌드하고 진짜 파일로 띄운다(다시 띄우는 사례는 더하지 않았다).
- **문서.** `EMBED.md`, `docs/constitution/tech.md`·`operations.md`, `CONTEXT.md`의 사이트 파일·값 파일 항목(`domain-modeling` 스킬), `README.md`, `ci.yml`의 e2e 잡 주석, 두 앱의 `e2e/stack.ts`·`playwright.config.ts`의 머리 주석, 그리고 `start.ts`의 "빌드의 입력"을 "빌드 준비물"로 고쳤다. 헌법 판은 3.1.8에서 3.1.10으로 올렸다(열린 PR #651이 3.1.9를 썼다. 비워 둔 판의 문장도 `docs/constitution/README.md`에 더했다). 위젯 컨테이너가 뜰 때 빌드한다는 말(이미지, compose, 배포 안내, 단독 배포 e2e)은 티켓 03의 몫이라 고치지 않았다.
- **인계.** `.scratch/widget-login-state/plan.md` 끝에 문단 하나를 더했다. 코드의 `settings`·`WidgetSettings` 이름이 "위젯 설정"과 겹치니 두 받기를 합칠 때 바꾸고, `lib/runtime.ts`의 시험 전용 이음매(`seedRuntimeValues`, `clearRuntimeValues`, `generation`)는 시험 쪽으로 옮기거나 캐시를 주입하게 정리한다는 내용이다. 코드는 건드리지 않았다.

## 고친 것(검증 중 나온 실패)

- 위젯 e2e의 첫 실행은 준비의 빌드가 `manifest.test.ts`의 타입 오류(`writeServedManifest`에 필요 없는 `requestChars`를 넘김)로 멈췄다. 단위 시험(vitest)은 타입을 보지 않아 초록이었고 `next build`의 타입 검사가 잡았다. 일곱 군데를 지웠다.
- `pnpm -C web verify`의 첫 실행은 같은 파일의 eslint 오류 넷(불필요한 템플릿 식, void 식 반환)에서 빨갰다. `eslint --fix`와 `prettier --write`로 고쳤다.
- 변이 표 여섯이 `next.config.ts`를 다시 쓴 탓에 원문이 사라졌다(들여쓰기가 두 칸 깊어졌고 `const ancestors` 줄이 `ancestorsOf` 함수로 옮겨졌다). 표 넷(`element`, `site_file`, `widget_app`, `widget_e2e`)을 새 코드에 겨눠 `--check`로 원문이 한 번씩 있는 것을 보았다. e2e의 `*` 변이는 실제로 값을 만드는 `tools/manifest.ts`의 줄로 옮겼다.

## 확인한 것(이 세션이 돌린 명령)

- 위젯 e2e `pnpm -C web/apps/widget exec playwright test`: 22개 통과(1.4분, 새 사례 포함).
- 위젯 테스트 페이지 e2e `pnpm -C web/apps/portal exec playwright test`: 41개 통과(1.2분).
- `pnpm -C web verify`(린트, 서식, 타입, vitest, tsconfig): 143개 파일 3,028개 통과 1개 건너뜀(기존 `make-key.test.ts`의 윈도 조건). 초록이다.
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run lint-imports`(계약 9 지킴), `uv run pyright`(0 오류): 초록이다.
- 실제 모델 e2e: `-m llm_widget` 1개 통과(303.78초, LLM 토큰 합계 17,047(입력 16,785, 출력 262), 트레이스 2개, 모델 호출 4건), `-m llm_portal` 1개 통과(151.01초, 토큰 6,997(입력 6,925, 출력 72), 트레이스 1개, 모델 호출 2건).
- 사진 비교 `pnpm -C web visual:widget`(Docker): 46개 통과. 정답 사진은 바뀌지 않았다(`git status`가 비었다).
- 단독 배포 e2e `pnpm -C web/packages/e2e-standalone exec playwright test`: 15개 통과, 214초(3.5분). 지금의 이미지(뜰 때 사이트 파일 없이 빌드한 뒤 서비스 시작이 값 파일과 사본을 쓴다)가 서고 기존 사례가 초록이다.

## 변이 표 고침의 확인

`uv run python tools/mutate.py <표> --since origin/dev`를 표 넷(`widget_app`, `site_file`, `element`, `widget_e2e`)에 돌려 고친 변이 여섯(27·28, 33, 16·19, 4)이 모두 기대대로 빨갰고, 끝난 뒤 `git status`에 변이가 남지 않았다(이 세션이 돌린 명령의 출력이다). 위의 e2e 변이 둘(19, 4)은 실제 위젯 e2e를 돌려 얻은 결과다.

## 티켓과 계획

티켓의 체크박스를 모두 채우고 `Status: done`으로 바꿨고 `uv run python tools/plan_table.py`를 돌렸다. 이 티켓은 기능의 마지막이 아니다(03이 남았다). 그래서 기능 계획의 `**끝:**` 줄과 기능 단락은 더하지 않았다. 운영자가 올릴 때 할 일은 없다(사이트 파일과 배포 파일의 형식이 그대로이고 위젯이 뜰 때 값을 스스로 쓴다). PR 제목에 느낌표를 붙이지 않는다.

## 인계(셀프 리뷰 직전)

컨텍스트가 인계 문턱(20만 토큰)을 넘은 채 `셀프 리뷰 직전` 경계에 와서 인계한다. 구현, 문서, 검증(위 "확인한 것"), 변이 표 고침, 티켓·계획 갱신까지 마쳤고 커밋하지 않았다. 남은 일은 셀프 리뷰(`/code-review`, 고정점 `origin/dev`)와 반영, 커밋 직전의 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`, 커밋(`-F` 파일, 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`), PR(본문 끝에 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`), `merge.md`의 "워크트리에서 병합할 때", 회고와 "다음"이다.

PR 본문과 리뷰에 밀 주장(이 세션이 새로 쓴 사실 문장):
- `tools/manifest.ts`와 `tools/start.ts` 머리의 "Next 16.3.6의 `next build`가 기다리지 않고 돌아오고 마치면 `process.exit(0)`으로 끝난다"는 티켓과 명세 검토의 말을 옮긴 것이다. 이 세션은 스텁으로 처리기가 도는 것을 시험으로 봤고 실제 `next build`가 그렇게 끝나는 것은 위젯 e2e가 원본을 남기고 준비가 서는 것으로만 봤다.
- `EMBED.md`의 "다시 빌드하지 않아도 된다", `CONTEXT.md` 값 파일 항목의 "위젯을 iframe으로 품을 수 있는 사이트의 목록도 위젯이 뜰 때 사이트 파일에서 정해진다", `tech.md` 웹 칸의 "빌드는 사이트 파일을 읽지 않고 … 서비스 시작이 … 사본을 쓴다". 셋 다 위젯 e2e의 새 사례(허용 출처와 상한을 바꿔 다시 띄움)가 본 것과 코드를 읽은 것이다.
- `.scratch/widget-login-state/plan.md` 끝의 인계 문단(코드의 `settings`·`WidgetSettings` 이름과 시험 이음매 정리).
- 헌법 판 3.1.10과 비워 둔 3.1.9의 문장(`docs/constitution/README.md`).
- 이 세션은 `next-session` 병합 전 `sibling_overlap`을 한 번 쳤다(번호 겹침 없음, 높은 판 3.1.9). 커밋 직전에 다시 친다.

PR 본문에 적을 것: 위젯 e2e 22개(새 사례 포함), 위젯 테스트 페이지 e2e 41개, `pnpm -C web verify` 3,028개 통과 1개 건너뜀, `-m llm_widget` 303.78초와 `-m llm_portal` 151.01초 통과, 사진 비교 46개 통과(정답 불변), 단독 배포 e2e 15개 통과 214초, 첫 위젯 e2e가 타입 오류로 준비에서 멈춘 일과 고친 것, 변이 표 여섯을 새 코드에 겨눈 것.

- 이 세션의 제목을 `feature/02-build-closes-frame-ancestors-and-start-fills-them (인계함)`으로 바꾼다(바꾸기 전 제목은 `feature/02-build-closes-frame-ancestors-and-start-fills-them`).
- 백그라운드로 도는 작업은 없다(검증과 변이 실행이 모두 끝났다). `git worktree unlock`으로 이 워크트리의 잠금을 푼다.
- 경계는 `셀프 리뷰 직전`이다. 일지 경로는 `docs/journal/2026-11-28-0125-build-closes-frame-ancestors-and-start-fills-them.md`다.
- open-session을 부른다 2026-11-27T16:36Z

## 셀프 리뷰(`/code-review`, 고정점 `origin/dev` `0a2662c`, 이어받은 세션)

범위: base `0a2662c92`, 수정 29개 파일, 미추적 10개, 커밋 0개. 표준 축(sonnet·high)과 명세 축을 서브에이전트 둘로 돌렸다. 둘 다 코드는 고치지 않았다.

**확정해서 고친 것.**
- 잔존. `README.md`의 위젯 `tools/start.ts` 풀이(사본 쓰기와 원본 남기기 빠짐), `tools/manifest.ts` 줄 없음, "빌드 입력(buildInput …)" 풀이, 49행 "위젯 빌드의 시험", `src/agent_os/main.py` 주석과 `tests/test_main.py` 주석의 "위젯 빌드", `tests/fixtures/site_file/README.md`와 `sites.toml` 머리, `docs/constitution/tech.md` 웹 칸의 "위젯 빌드와 나눠 쓰고", `web/apps/widget/tools/start.ts`의 "번들의 빌드와 설정 파일이 같은 파일을 읽는다", `.scratch/widget-login-state/spec.md` 384행의 "빌드에 굳은 값"을 위젯이 뜰 때 받는 말로 고쳤다.
- 거짓이던 문장. `site-file.ts` 머리는 `manifest.ts`도 `widgetValues`를 부른다고 적었으나 부르는 쪽은 `runtime.ts`뿐이다. `next.config.ts`의 "개발 서버는 산출물을 만들지 않아"는 틀렸다(Next 16.3.6 dev는 `.next/dev/routes-manifest.json`을 쓴다. 서브에이전트가 `setup-dev-bundler.js:211`, `config.js:1249`를 읽었다). "개발 서버는 이 원본과 사본(`.next/routes-manifest*.json`)을 쓰지 않아"로 고쳤다. `widget-login-state/plan.md`는 `generation`을 올리는 것이 `clearRuntimeValues`뿐이라는 것(`lib/runtime.ts:166-179`)과 `WidgetSettings`가 컴포넌트가 아니라 시험 파일 이름이고 코드의 이름은 `settings`·`Settings`·`onRetrySettings`라는 것(`ConnectedWidget.tsx`, `WidgetScreen.tsx`를 grep으로 봤다)을 맞췄다.
- 깨진 프로브. `.scratch/widget-runtime-values/probes/prebuilt_start/entry.mjs`가 이름을 바꾼 `buildInput`을 불러 `widgetValues`로 고치고 README 줄에 옛 이름을 괄호로 남겼다. 프로브를 다시 돌리지는 않았다(import 이름만 바꿨다).
- 약한 단언. `manifest.test.ts`와 `start.test.ts`의 "원본이 없다" 사례가 모든 진단에 붙는 끝 문장만 봐서, 다른 갈래의 실패도 통과했다. 원본이 없다는 문장 `routes-manifest.original.json 이 없다`를 단언하게 고쳤다.
- 이식성. `manifest.test.ts`가 손으로 지은 `file:///…` 주소를 `pathToFileURL`로 바꿨다(`spawn-app.ts`와 같은 길). 불러오기 한 줄을 빠뜨려 시험 셋이 빨개졌다가 더해 고쳤다.
- 이름. 위젯·위젯 테스트 페이지 e2e `stack.ts`의 빌드 함수 인자를 `siteFile`에서 `decoyFile`로 바꾸고 머리 주석 첫 문장을 "미끼 사이트 파일을 주고 위젯을 빌드한다"로 바꿨다.

**남긴 것과 이유.**
- 냄새(판단): `ancestorsOf`와 `manifest.ts`의 같은 삼항 및 `PLACEHOLDER` 중복, `seedOriginal` 세 곳의 중복, `DECOY_ORIGIN`의 두 e2e 중복, `NextCommand`의 `manifest` 갈래와 `runtime` 결합, `LaunchSteps.keep` 이름, `control.ts`의 `parseRestart` 단위 시험 없음. 문서화된 표준 위반이 아니고 이 티켓의 체크박스 밖이라 고치지 않았다. 중복과 `parseRestart`는 회고 후보로 올린다.
- 명세 축의 (a)3("서비스 시작이 기대는 파일이 TypeScript 패키지 없이 Node만으로 도는지 본다"): 가로채기 훅이 `typescript` import를 거절하는 것까지가 시험이고, 실제 Next가 `next.config.ts`를 읽는 길은 시험하지 않았다. 이 항목은 03의 이미지 단독 배포 e2e가 본다.
- 명세 축의 (c): `manifest.ts` 머리에 길을 고른 까닭이 있고 `start.ts` 머리는 그곳을 가리킨다. 티켓의 "래퍼의 머리 주석"과 어긋나는 정도라 그대로 둔다.
- `.scratch/widget-login-state/plan.md`의 인계 문단은 지시문이 시킨 것(범위 넘침이 아니다).

**밀 주장.** (가) `tools/manifest.ts`·`tools/start.ts` 머리의 "Next 16.3.6의 next build는 기다리지 않고 돌아오고 마치면 process.exit(0)": 두 서브에이전트가 설치본 `next/dist/bin/next`를 읽어 맞다고 봤다(134~140줄 `process.exit(0)`, 243줄 `program.parse`). 코드를 읽은 것이고, 실제 `next build`로 잰 것은 위젯 e2e가 원본을 남기고 준비가 서는 것뿐이다. (나) EMBED.md, CONTEXT.md, tech.md의 문장은 코드와 맞다. (다) plan.md 인계 문단은 위 고침 뒤의 문장이다. (라) 헌법 판 3.1.10과 비워 둔 3.1.9: `origin/feature/04-standalone-compose-adds-widget-admin`과 PR #651이 3.1.9를 쓴다.

**다시 돌린 명령.** `pnpm -C web/apps/widget exec vitest run tools/manifest.test.ts tools/start.test.ts tools/start.spawn.test.ts next.config.test.ts`: 4개 파일 165개 통과. 나머지 손으로 치는 다섯은 커밋의 pre-commit 결과로 갈음하고, 전체는 `tools/run_checks.py`를 한 번 돌린다.
