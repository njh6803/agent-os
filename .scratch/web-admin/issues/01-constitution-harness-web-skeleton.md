# 01: 헌법·하네스·web 뼈대 — 원칙 III이 TypeScript에도 걸리고 다섯째 검증 명령이 돈다

**What to build:** 개발자가 `pnpm -C web verify`를 치면 web 워크스페이스에서 네 가지가 한 번에 돈다. 린트(typescript-eslint, 타입 기반 규칙, 경고 0), 타입, 단위 테스트, tsconfig 검사다. pre-commit은 커밋마다, CI의 `verify` 잡은 푸시마다 같은 명령을 돈다. TS에서 `any`·타입 단언·비null 단언·`@ts-ignore`를 쓰거나 tsconfig의 `strict`를 끄면 빨갛다. 헌법 3.0.0의 원칙 III이 두 언어를 말하고, 검증 명령을 세는 살아 있는 문장은 모두 다섯을 말한다. 뼈대에는 앱도 생성물도 없다. 앱은 04, 생성물은 03이다.

이 기능의 뿌리 둘 가운데 하나다. 계약 티켓(02)과 서로 막지 않는다. 헌법을 바꾸므로 계약에 닿는 티켓이다. web 뼈대가 여기 드는 이유는 둘이다. 첫째, 다섯째 명령이 실제로 돌아야 명령 목록에 적을 수 있다(`operations.md` 머리의 "실제로 돌려 통과한 명령만 적는다"). 둘째, web 규칙의 `paths`는 가리키는 것이 있어야 지침 검사를 지난다. 리뷰의 질문은 명세대로 이 판정자와 명령으로 오래 살 수 있느냐다.

근거는 `.scratch/web-admin/spec.md`의 "첫 티켓", "판정자와 검사", "판정자와 검사의 변이 테스트" 절이다. ADR 0020·0021과 그 2026-09-28 이력, ADR 0004·0013도 근거다.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

### 헌법과 문서

- [x] **헌법 3.0.0.** `principles.md`의 원칙 III이 두 언어를 말한다. 파이썬은 지금 문장 그대로이고, TS는 ADR 0020의 금지 목록과 판정자(typescript-eslint)다. 원칙의 문장이 바뀌므로 major다. `docs/constitution/README.md`는 지금 2.5.4(#96)이고 3.0.0이 된다
- [x] **`tech.md`.**
  - 웹 행이 ADR 0021의 스택을 적는다. Node 24, pnpm 11, TypeScript 5.9 고정, Next 16, React 19, 나머지 라이브러리다
  - 프론트 구성 행의 미결이 닫힌다. 화면은 `components/pages/`의 클라이언트 컴포넌트이고, `app/**/page.tsx`는 라우팅과 레이아웃만 한다
  - 원격·CI 행이 Node·pnpm과 e2e를 안다
- [x] **`CLAUDE.md`.** 검증 명령에 다섯째 `pnpm -C web verify`를 더하고, 레이어 절에 `web/`의 한 줄을 더한다. e2e 명령은 여기서 적지 않는다. e2e가 서는 05가 LLM 테스트처럼 괄호로 적는다
- [x] **`operations.md`.** 머리를 고친다. 가드레일 절의 검사 목록에 web의 판정자와 검사를 더한다. #96이 마크다운 검사 둘을 더한 그 문단이다. 클론 뒤 설치에 `pnpm -C web install`을 더한다
- [x] **`README.md`.** 트리에 `web/`을, 원천 표와 클론 블록을 고친다
- [x] **`.gitignore`.** `node_modules/`, `.next/`, 테스트 산출물이다

### 검증 명령을 세는 문장

명세는 #96 전(게이트 일곱)에 grep했다. 이 티켓을 쓰며(2026-09-29) 같은 패턴으로 다시 쟀고, 아래가 그 결과를 반영한 목록이다.

- [x] **고치는 것.** 명령이 다섯이 되어 거짓이 되는 문장이다
  - `CLAUDE.md`의 게이트 줄. `넷은 그중`과 `검사 넷이 초록이다`만 고칠 것이 아니다. **같은 줄의 게이트 수(`게이트는 아홉`)도 고친다.** 명세는 이것을 "게이트를 세는 줄을 고친다"로 따로 들었다. 그러나 그 수는 명세 때(`일곱`)부터 grep 패턴 밖이었다. 그래서 잔존 grep이 그 수까지 보도록 아래 패턴에 더했다. 전체 수와 손으로 치는 수를 다시 센다. #96이 셋에서 다섯으로 바꾼 "나머지 다섯은 훅이 돌린다"가 여전히 맞는지도 본다. 다섯째 명령은 pre-commit도 돌지만 pytest처럼 손으로 치는 명령의 자리다. 같은 줄 끝의 정의 문장도 바뀐다. 이 문장은 티켓의 "검사 넷이 초록이다"가 무엇을 말하는지 정한다. 이 기능의 티켓은 수에 묶이지 않게 "`CLAUDE.md`의 검증 명령이 모두 초록이다"로 썼다. 그 문장도 수를 빼는 쪽이 다음 명령 변경에서 썩지 않는다
  - `CLAUDE.md` 작업 규약 3
  - `docs/constitution/operations.md`의 머리와 가드레일 절. 가드레일은 "넷"이라는 말 없이 검사를 나열해 grep에 걸리지 않는다
  - `README.md` 원천 표의 검증·운영 규약 행
  - `code-review` 스킬 6단계의 5
  - `tools/export_openapi.py`와 `tests/tools/test_export_openapi.py`의 독스트링
- [x] **같은 뜻의 다른 말.** "넷"이라는 말 없이 명령을 넷으로 나열하거나 옛 설치를 싣는 자리다
  - `.github/PULL_REQUEST_TEMPLATE.md`: 체크리스트의 명령 줄과 "확인 방법" 블록. 이 티켓의 PR이 바로 이 템플릿을 채운다
  - `README.md`의 클론 블록과 `.pre-commit-config.yaml` 머리의 "클론 뒤 한 번" 주석에 `pnpm -C web install`이 없다. 다섯째 명령의 훅이 `always_run`으로 서면, 이 설치 없이는 첫 커밋이 빨강이다
- [x] **그대로 두는 것.**
  - `tools/check_type_escapes.py`와 `tests/sdk/test_ids.py`: 지난 사건을 적은 문장이라 그대로 참이다
  - `KICKOFF.md`: **명세가 적은 "검사 넷"은 #96 뒤 "검사 여섯과 훅 러너"이고, 이제 패턴에 걸리지 않는다.** 명세의 이 항목은 낡았다. 뜻은 하네스 검사 스크립트의 수라 검증 명령과 다르다. 중첩 지침 검사를 기존 `check_instructions.py`에 넓히면 그 수는 그대로다. `tools/`에 검사 스크립트를 새로 두기로 하면 그 문장도 함께 고친다
- [x] **잔존 grep.** 제외는 일지, ADR, `.scratch/`, `.claude/worktrees/`다
  - 수를 말하는 패턴: `검사 넷|명령 넷|넷은 그중|게이트는 아홉`
  - 같은 뜻의 다른 말을 찾는 셋: `검증 명령`, `lint-imports`, `별도 PR로 먼저`
  - 걸린 것마다 수를 말하거나 명령을 나열하는지 본다
  - 2026-09-29에 `별도 PR로 먼저`는 두 곳에 걸렸다. PR 템플릿과 `operations.md` 리뷰 파이프라인이다. 둘 다 `claude-code-review.yml`의 범위로 좁혀져 참이다. 템플릿은 #95가, `operations.md`는 그보다 앞선 #91이 좁혔다

### 게이트 훅

- [x] **`tools/hook_bash_gate_pipe.py`의 게이트 목록에 다섯째 명령과 e2e 명령을 더한다.** 파이프 뒤 `$?`가 판정을 속이는 것은 명령의 언어와 무관하다. e2e 스크립트의 이름은 05가 정한다. 그래서 여기서는 스크립트 이름에 기대지 않는 모양으로 잡는다(예: Playwright 실행). 05가 실제 명령으로 발동을 다시 본다
- [x] `tests/tools/test_hook_bash_gate_pipe.py`: 두 명령을 파이프 뒤에 둔 입력은 경고하고, 단독으로 친 입력은 조용하다
- [x] `tools/hook_payloads.toml`에 발동할 실제 입력 하나와 발동하지 말아야 할 실제 입력 하나를 더한다. `tools/run_hooks.py`로 실행을 확인한다(`.claude/rules/tools.md`)

### 중첩 지침 파일 검사

- [x] **`tools/check_instructions.py`가 루트 밖의 `CLAUDE.md`와 `AGENTS.md`를 빨강으로 본다.** `node_modules/`와 `.claude/worktrees/`는 뺀다. pre-commit은 작업 트리에서 돌므로 추적하지 않는 파일도 보고, CI는 추적하는 것만 본다. `next dev`가 에이전트를 감지하면 앱 폴더에 두 파일을 만든다(ADR 0021). `agentRules: false`(04)가 그것을 끄지만, 결과를 보는 검사는 원인과 무관하게 잡는다
- [x] 이 저장소는 지금 통과한다. 하위 디렉터리에 둔 사본에서는 실패한다. `node_modules/` 아래의 것은 무시한다
- [x] 검사의 CLI 진입점을 subprocess로 한 번 부르는 테스트가 이 빨강을 출력에서 본다. 저장소 밖 임시 트리를 루트 인자로 준다(`.claude/rules/tests.md`)

### web 뼈대

- [x] pnpm 워크스페이스와 TypeScript 5.9 고정을 세운다
- [x] 워크스페이스의 기준 tsconfig를 하나 두고, 뒤의 패키지와 앱의 tsconfig는 그것을 `extends`한다. 앱의 tsconfig에 `extends`도 `strict`도 없으면 Next가 `"strict": false`를 써 넣는다. tsconfig 검사가 그것을 잡지만, 처음부터 물려받게 둔다
- [x] ESLint flat config와 Prettier를 둔다
- [x] `verify` 스크립트는 린트(`--max-warnings 0`), 타입, 단위 테스트(Vitest), tsconfig 검사를 돈다. 생성물 최신성은 03의 것이다. 생성물이 없는 여기에 서면 빈 것을 재고 초록이 된다
- [x] 뼈대에 소스가 거의 없어도 판정자와 검사는 실제로 무언가를 본다. 아래 변이 테스트가 그 증거다

### 판정자 (ADR 0020)

- [x] **typescript-eslint.**
  - `strictTypeChecked`를 켜고, 타입 단언을 막는 설정을 더한다(`as const`는 제외)
  - 비null 단언, `@ts-ignore`, `@ts-nocheck`를 막는다
  - `@ts-expect-error`는 타입 테스트 파일(`*.test-d.ts`)에서만, 설명과 함께 허용한다. strict 설정의 `ban-ts-comment`는 설명이 붙은 것을 어디서나 허용한다. 그래서 글롭별 설정이 든다(명세 검토가 8.33.1 설치본을 읽었다)
- [x] **`linterOptions.noInlineConfig`를 켠다.** 켜진 파일의 인라인 설정 주석은 에러가 아니라 경고로 나오고, ESLint CLI는 경고만 있으면 종료 코드 0이다. 그래서 경고 0이 게이트다
- [x] **대상 글롭은 `.ts`, `.tsx`, `.d.ts`와 생성물 전부다.** 판정 범위에서 빼는 목록을 두지 않는다
- [x] **ESLint가 함께 판정하는 것.** 내장 규칙이나 이미 승인된 플러그인으로만 하고, 새 플러그인을 들이지 않는다
  - eslint-plugin-boundaries: 층 경계, 앱 사이의 import, barrel import, 아이콘 서브패스 import
  - `app/`의 파일은 pages와 templates만 import한다
  - TS `enum` 금지
  - `dangerouslySetInnerHTML` 금지
  - Next에서 API를 부르는 서버 코드 금지. 셋이다
    - Server Actions 지시문(`"use server"`)은 web 전체에서 막는다
    - Next 서버가 돌리는 파일(`route`, `middleware`, `proxy`, `instrumentation`)은 앱의 어느 자리에 두어도 막는다
    - 전역 `fetch`는 생성 클라이언트 패키지 밖에서 막는다(`no-restricted-globals`)
- [x] **경로에 기대는 규칙은 경로와 무관하게 쓴다.** 앱은 04에 선다. 앱이 다른 배치(예: `src/app/`)를 쓰면 가상 경로에 건 규칙은 아무것도 보지 않고, 변이 테스트는 초록이 된다. 실제 배치에서의 재확인은 04가 받는다
- [x] **타입 기반 규칙을 앱 자리의 파일에 돌릴 수 있는지 먼저 본다.** 프로젝트 서비스가 tsconfig 밖의 파일을 거부할 수 있다. 명세 검토도 재지 않았다

### 판정자의 변이 테스트

- [x] **위반을 담은 코드는 테스트가 만들어 판정자에 넣는다.** 커밋한 파일에 위반을 두지 않는다. 두면 그 파일을 빼는 목록이 생긴다(ADR 0013이 경계한 모양)
- [x] **아래는 각각 빨강이다.**
  - `.ts`: `any`, `as`, 꺾쇠 단언, `!`, `@ts-ignore`, `@ts-nocheck`, TS `enum`, 생성 클라이언트 밖의 전역 `fetch`
  - `.tsx`: `dangerouslySetInnerHTML`
  - `.d.ts`: `any`
  - 타입 테스트가 아닌 파일의 `@ts-expect-error`
  - `"use server"`, 그리고 Next 서버 파일 넷
  - 층 경계: atoms가 organisms를 import하는 것, 앱 사이의 import, barrel을 거르지 않는 import
  - 아이콘 세트를 통째로 import하는 것
  - **끄기 주석과 그것이 끄려던 위반.** `verify`의 린트 명령으로 돌린 결과가 빨강이고, 끄려던 위반도 그대로 보고된다
- [x] **`as const`와 타입 테스트 파일의 설명 붙은 `@ts-expect-error`는 초록이다**
- [x] 명세가 재지 않았다고 적은 것은 여기서 잰다. 비null 단언, `@ts-ignore`, `@ts-nocheck`, 꺾쇠 단언, `.d.ts`, 인라인 설정 주석, 내장 규칙들이다. ADR 0020의 금지 목록을 확인하는 일이라, 어긋나면 설정을 고치고 새 결정을 낳지 않는다

### tsconfig 검사 (ADR 0020이 넘겼다)

- [x] **`pnpm -C web verify`의 한 단계다.** 파이썬 `tools/`에 두지 않는다. `extends`를 풀려면 TS 도구가 필요하고, 언어마다의 검사는 그 언어의 명령이 돈다
- [x] **검사할 tsconfig는 `web/` 아래를 훑어 찾는다**(`node_modules/` 제외). 목록으로 적으면 뒤 티켓의 tsconfig가 조용히 빠진다
- [x] **찾은 tsconfig마다 TypeScript가 풀게 한다.** `tsc --showConfig`가 `extends`를 풀어, 부모의 `strict: true`와 자식의 `strictNullChecks: false`를 함께 드러냈다(`tsc_showconfig.sh`). `strict`가 참이고, strict 계열 개별 플래그 가운데 거짓으로 덮인 것이 없는지 본다
- [x] **순수 함수의 테스트.**
  - `strict: true`만 있으면 통과한다
  - `strict`가 없거나 거짓이면 실패한다
  - `extends`로 물려받은 설정을 자식이 끄면 실패한다
  - `strict: true`에 `strictNullChecks: false`가 있으면 실패한다
- [x] **저장소 상태의 테스트.**
  - 워크스페이스의 실제 tsconfig 전부가 통과한다
  - 하나를 바꾼 사본은 실패한다
  - `web/` 아래에 새로 둔 tsconfig는 목록을 고치지 않아도 검사에 든다

### 지침

- [x] **`.claude/rules/web-*.md` + `paths`.** 린터가 판정하지 못하는 판단 기준만 둔다. ESLint가 판정하는 것은 적지 않는다
  - 규칙 파일은 자기 `paths`가 가리키는 경로가 생기는 티켓에서 선다. 그래서 여기서 세우는 규칙은 `paths`가 뼈대에 이미 있는 web 워크스페이스를 가리킨다. 그래야 지침 검사를 지난다
  - 내용은 명세의 씨앗 셋이다. templates는 슬롯만이고 pages가 데이터를 채운다. 서버 데이터를 스토어에 복사하지 않는다. `isLoading`과 `isValidating`을 가른다. 앱과 뒤의 위젯에 함께 걸리는 판단이라 워크스페이스 층에 둔다
  - 이 명세가 정한 것 가운데 린터가 판정하지 못하는 것도 함께 둔다. TS 테스트의 이름은 행동을 말하는 한국어 문장이다. ESLint 규칙은 경로와 무관하게 쓰고 변이 테스트를 붙인다. 판정 범위에서 빼는 목록을 두지 않는다
  - 이 규칙이 앱의 실제 파일을 열 때 실리는지는 05가 본다. 관리 화면 앱에만 걸리는 규칙은 04의 것이다

### pre-commit과 CI

- [x] **pre-commit.**
  - 다섯째 명령을 도는 훅을 `always_run`으로 둔다. 파이썬 파일이 안 바뀐 커밋에서도 pyright·pytest가 도는 것과 같은 이유다. 파이썬 티켓의 `openapi.json` 변경이 생성물 최신성을 깨는 것도 이유다(03부터)
  - e2e는 넣지 않는다(ADR 0021 이력)
- [x] **`ci.yml`의 `verify` 잡.** Node 24와 pnpm 11 설정, `pnpm install --frozen-lockfile`, 다섯째 명령을 더한다. pnpm 스토어 캐시는 이 티켓이 본다. `claude-code-review.yml`은 바꾸지 않는다
- [ ] **claude-review의 코멘트 0개 가드.** 대기열 50이 먼저 병합됐으면 이 PR에서도 가드가 돈다. 아니면 가드가 꺼진다. `.github/workflows/` 아래 파일이 바뀌면 건너뛰기 때문이다. 그 경우 병합 전에 claude-review의 코멘트가 있는지 손으로 보고 PR에 적는다
- [x] **`ci.yml`을 함께 바꾸는 하네스 워크플로 PR이 있다**(러너와 마크다운 검사 둘을 CI에, 일지 2026-09-28-08의 "다음"). 뒤에 병합되는 쪽이 main을 받아 합친다

### 확인

- [ ] **실제 실행으로 확인한다**(`CLAUDE.md` 작업 규약 3)
  - pre-commit이 다섯째 명령을 실제로 돈다. 훅의 출력으로 본다
  - CI `verify` 잡의 로그에 web 단계가 있다. `gh run view`로 본다
  - 빨강은 `tools/mutate.py`로 본다
- [x] TS 테스트의 이름은 행동을 말하는 한국어 문장이다. tsconfig 검사의 테스트가 이 기능의 첫 TS 테스트다
- [x] `CLAUDE.md`의 검증 명령이 모두 초록이다
- [x] 이 기능의 첫 병합이면 `.scratch/plan.md`의 web-admin 행을 `in-progress`로 바꾼다

### 이 티켓이 정한 것 (2026-09-29, PR에서 사용자가 본다)

- **ESLint 설정은 `web/eslint.config.mjs`다.** ESLint 10은 `.ts` 설정을 읽으려면 jiti(새 의존성)나 불안정 플래그(`unstable_native_nodejs_ts_config`)를 요구했다. 판정 대상은 TS 파일이고, 설정의 행동은 변이 테스트가 잰다.
- **verify에 포맷 검사를 넣었다.** 차례는 린트, 포맷(`prettier --check .`), 타입, 단위 테스트, tsconfig 검사다. 명세는 넷을 들었다. 파이썬의 린트 명령이 `ruff format --check`를 함께 도는 자리와 같고, Prettier를 두기만 하고 보지 않으면 모양이 조용히 갈린다.
- **typescript-eslint는 8.70.1이다.** pnpm 11은 나온 지 하루가 안 된 판(8.71.0)을 받으려면 워크스페이스 파일에 `minimumReleaseAgeExclude`를 쌓는다. 예외를 두지 않고 기본 해석을 따랐다. ADR 0020의 탐침도 8.70.1이었다.
- **barrel은 `boundaries/dependencies`의 `fileInternalPath`로 판정한다.** boundaries 7의 `entry-point` 규칙은 폐기 예정이다. barrel이 드는 도메인 폴더는 09-20 씨앗의 셋(`api/`, `hooks/queries/`, `types/`)이다. 명세의 "barrel을 거르지 않는 import"는 도메인 폴더의 `index.ts`를 거치지 않는 깊은 import로 읽었다.
- **경계는 import 말고도 센다.** 다시 내보내기(`export … from`), 동적 import, `require`도 의존이다. boundaries의 기본은 import만이다.
- **`app/`의 외부 import는 `next`와 `react`만이다.** 명세는 서버 컴포넌트가 생성 클라이언트를 import하는 길을 층 경계로 막는다고 했다. 워크스페이스 패키지는 외부 모듈로 보일 수 있어 외부까지 판정한다(`checkAllOrigins`).
- **전역 `fetch`는 `globalThis`·`window`·`self`의 속성으로도 막는다**(`no-restricted-properties`). `no-restricted-globals`만으로는 속성 접근이 지나간다.
- **생성 클라이언트 패키지의 `fetch` 예외는 지금 둔다**(`**/packages/api-client/**`). 명세 문장이 "패키지 밖에서 막는다"이고, 03이 "이 패키지는 통과한다"를 실제 자리에서 다시 본다. 여기서는 초록 사례로 잰다.
- **`dangerouslySetInnerHTML`은 JSX 속성과 객체 속성(`createElement`의 props) 둘 다 막는다.**
- **Next 서버 파일 금지는 JS 확장자도 든다**(`route.js` 등). Next의 기본 페이지 확장자가 JS를 받는다.
- **중첩 지침 파일 검사는 루트의 `.venv`와 `.git`도 보지 않는다.** 명세는 `node_modules/`와 `.claude/worktrees/`를 들었다. `.venv`는 파이썬의 설치된 의존성이라 `node_modules`와 같은 자리이고, `.git`은 저장소의 내용이 아니다.
- **tsconfig 검사는 `tsc --showConfig`를 부르지 않고 TypeScript API로 `extends`를 푼다**(`parseJsonConfigFileContent`). 같은 해석이고 프로세스를 띄우지 않는다. strict 계열 아홉은 손으로 적었고, 테스트가 `tsc --showConfig`의 `strict: true` 전개와 대조한다. TypeScript를 올려 계열이 늘면 그 테스트가 먼저 빨개진다.
- **Vitest는 파일을 차례로 돈다**(`fileParallelism: false`). 판정자 테스트가 web/ 아래에 임시 트리를 쓰는 동안 tsconfig 검사의 저장소 상태 테스트가 web/을 훑으면, 쓰는 도중의 tsconfig를 읽을 수 있다.
- **TS 쪽 빨강은 `tools/mutate.py`가 아니라 테스트를 먼저 쓴 차례와 설정 변이로 봤다.** mutate.py는 pytest만 돈다.
  - 판정자의 빨강 사례는 규칙 없는 설정에서 빨간 것을 보고 규칙을 더했다. 리뷰 뒤에 더한 둘(설명 없는 `@ts-expect-error`, `app/`이 층 밖의 앱 파일을 import)은 설정 변이(타입 테스트 예외를 설명 없이도 허용, `workspace-app` 요소를 지움)에서 빨간 것을 봤다.
  - 초록 가드 여섯 가운데 다섯(`as const`, 타입 테스트의 설명 붙은 `@ts-expect-error`, barrel을 거친 import, organisms→atoms, `app/`→pages·templates)은 설정을 지나치게 넓힌 변이에서 빨간 것을 봤다. 여섯째(생성 클라이언트 패키지 안의 `fetch`)는 예외를 두기 전에 빨간 것을 봤다.
  - tsconfig 검사의 저장소 상태 테스트는 기준 tsconfig의 `strict`를 끈 변이에서 봤다.
  - 파이썬 쪽은 `.scratch/web-admin/probes/harness_mutations.toml`이다.
- **판정자 테스트의 임시 트리는 앱과 패키지마다 자기 tsconfig를 둔다**(`apps/admin/`, `apps/widget/`, `packages/api-client/`). 뿌리 하나에 두면 앱 폴더의 tsconfig를 가장 가까운 것으로 찾는 실제 배치를 재지 못한다.
- **아이콘 금지는 boundaries가 아니라 내장 `no-restricted-imports`다.** 명세는 boundaries의 몫으로 적었지만 "내장 규칙이나 이미 승인된 플러그인"이면 된다. 외부 모듈 이름 하나를 막는 데는 내장 규칙이 짧다.
- **PR 템플릿의 "변경된 영역"에 `web/` 줄을 더했다.** 판정자 설정을 바꾸면 사례를 더하는지, 경로와 무관하게 썼는지, 새 tsconfig가 기준을 extends하는지 본다.
