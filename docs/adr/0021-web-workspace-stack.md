---
status: accepted
date: 2026-09-28
---

# web 워크스페이스의 스택과 API 클라이언트는 계약에서 생성해 커밋한다

`tech.md`는 웹을 "Next.js, pnpm 워크스페이스, `web/`"까지만 적고 나머지는 슬라이스 3 인터뷰로 넘겼다. 넘긴 것은 pages의 자리와 일지 2026-09-19의 09-20 절이 남긴 스택 선택이다. 의존성을 더하려면 ADR을 남긴다. **`web/`은 pnpm 11 워크스페이스이고 Node 24, TypeScript 5.9다(ADR 0020). 관리 화면은 Next 16과 React 19다. 스타일은 Tailwind와 직접 만든 atoms이고 아이콘은 lucide-react를 서브패스로 import한다. 서버 데이터는 SWR, 클라이언트 상태는 Zustand다(persist를 sessionStorage에 걸고 토큰만 partialize). `packages/api-client`는 openapi-typescript와 openapi-fetch로 `openapi.json`에서 생성하고, 생성물을 커밋해 최신성을 검사한다. 린트는 ESLint(typescript-eslint, eslint-plugin-boundaries)이고 포맷은 Prettier다. 테스트는 Vitest(jsdom)와 MSW이고, 끝에서 끝은 픽스처로 띄운 `agent-os serve`에 대고 Playwright가 돈다.** 생성물을 커밋하는 이유는 `openapi.json`을 커밋하는 이유와 같다(ADR 0010). 계약을 바꾸는 PR에 생성 diff가 함께 보이고, 설치하지 않은 리뷰어와 봇도 그것을 읽는다.

## Considered Options

- **@hey-api/openapi-ts.** 3.1 원본을 받고 재귀 `Json`도 정상이며 SSE 클라이언트를 함께 낸다. 그러나 그 클라이언트는 409와 끊김에 `POST /runs`를 다시 보내, 실행을 일으키는 요청이 두 번 갔다. 생성물에 `any` 4줄과 `as` 35줄이 있어 판정 범위에서 빼야 한다(`.scratch/web-admin/probes/gen_run.mjs`). 재시도 상한은 기본값이 없다. 이것은 재지 않고 생성된 `core/serverSentEvents.gen.ts`를 읽은 것이다. `sseMaxRetryAttempts`를 주지 않으면 상한 검사를 건너뛴다. 거부했다.
- **orval(SWR 훅까지 생성).** 손으로 쓰는 훅 층이 사라진다. 그러나 `itemSchema`에서 3.1 원본을 거부하므로 앱이 3.2.0을 선언해야 하고(계약 변경), 그렇게 해도 SSE의 200이 타입에서 빠진다. 거부했다. openapi-generator는 3.1을 거부하고 3.2를 아예 모르며, 판별자 없는 `PluginRow`를 두 필드가 모두 required인 인터페이스 하나로 만든다. 거부했다.
- **TanStack Query.** 쓰기 뒤 무효화가 SWR보다 편하다. 그러나 09-20 씨앗의 훅 규칙(키 팩토리, null 키 조건부 요청, `isLoading`과 `isValidating`의 구분)이 SWR의 말로 적혀 있고, 이 화면의 쓰기는 스위치와 결정 둘뿐이다. 거부했다.
- **Zustand 없이 작은 스토어.** 클라이언트 상태가 토큰 둘뿐이라 의존성 하나를 아낀다. 사용자가 씨앗 그대로(persist와 partialize)를 골랐다.
- **shadcn/ui를 atoms로.** 빠르다. 그러나 Radix 의존성이 위젯과 나눌 공유 atoms(`packages/ui`)로 따라가는데, 위젯의 기술은 아직 정해지지 않았다. 거부했다. CSS Modules는 디자인 토큰과 유틸을 직접 써야 해서 거부했다.
- **Biome 하나.** 린트와 포맷이 한 도구다. 그러나 아토믹 층 경계를 전용 규칙 없이 경로별 import 제한으로 적어야 하고, 원칙 III의 판정은 typescript-eslint가 한다(ADR 0020). 거부했다.
- **생성물을 커밋하지 않는다.** 설치나 빌드 때 생성한다. 저장소는 가벼워지지만 리뷰어와 봇이 생성 결과를 보지 못한다. 거부했다.
- **Storybook을 처음부터 들인다.** atoms마다 스토리를 같은 폴더에 둔다(씨앗). 그러나 의존성 트리와 Next 통합 설정이 들고, 공유 atoms가 실제로 생기는 것은 위젯이다. 거부했다. 슬라이스 4에서 다시 본다.

## Consequences

- **계약 파일은 바뀌지 않는다.** openapi-typescript는 3.1.0 선언을 그대로 받고, 3.1과 3.2의 생성물이 바이트까지 같다. 기본 모드에서는 태그가 생성물을 바꾸지 않아 태그도 붙이지 않는다(ADR 0010의 2026-09-28 이력). `--immutable`로 필드가 readonly가 되고, 열거는 리터럴 유니온이다.
- **SSE는 손으로 받는다.** 잰 생성기 넷 중 `itemSchema`를 쓰는 것이 없다. openapi-fetch는 기본 설정에서 SSE 200에 `SyntaxError`를 던지므로 `parseAs: "stream"`으로 받아 `data:` 줄을 파싱한다. `JSON.parse`의 `any`는 `no-unsafe-*`가 막으므로(ADR 0020), 항목은 판별자만 보는 타입 술어로 `Event`가 된다. 객체인지, `type`이 계약의 종류 중 하나인지만 본다. 종류 목록은 `satisfies Record<Event["type"], true>`로 두어 컴파일러가 생성 타입과 대조한다. 손으로 쓴 목록이지만 어긋날 수 없다.
- **브랜드 식별자를 두지 않는다.** `as`가 금지되어 브랜드를 만드는 길은 패턴을 보는 타입 술어뿐이고, 그러면 서버의 식별자 패턴이 TS에 한 번 더 산다. 09-20 씨앗의 Brand 규칙은 채택하지 않는다.
- **화면은 `components/pages/`의 클라이언트 컴포넌트이고, `app/**/page.tsx`는 라우팅과 레이아웃만 한다.** 데이터를 브라우저가 가져오므로(ADR 0019) 화면은 클라이언트 컴포넌트다. 그래서 09-20 씨앗의 근거(서버 컴포넌트는 Vitest가 보지 못한다)가 그대로 서고, `tech.md` 프론트 구성 행의 미결이 이것으로 닫힌다.
- **09-20 씨앗은 강제력 높은 층부터 들인다.** 층 경계와 앱 간 import, barrel import, TS `enum` 금지, 아이콘 서브패스 import는 ESLint 설정이 판정한다. 판단 기준만 `.claude/rules/web-*.md` + `paths`에 둔다. 스토리 규칙은 Storybook을 들이는 날 다시 보고, Brand 규칙은 위와 같이 채택하지 않는다.
- **검증 명령이 다섯이 된다.** `pnpm -C web verify`(린트, 타입, 단위 테스트, 생성물 최신성)를 늘 친다. 파이썬 티켓도 `openapi.json`을 바꾸면 생성물의 최신성을 깨기 때문이다. e2e는 별도 명령이다. pre-commit과 CI의 `verify` 잡이 둘 다 돌고, 필수 검사는 `verify` 하나 그대로다. 워크플로 변경은 별도 PR로 먼저 병합한다(`operations.md`).
- **`next dev`의 에이전트 파일을 끈다.** `next dev`는 에이전트를 감지하면 앱 폴더에 `AGENTS.md`와 `@AGENTS.md` 한 줄짜리 `CLAUDE.md`를 만들거나 그 안에 블록을 끼워 넣는다(Next 16.3.6 `server/lib/start-server.js`, 설정 `agentRules`, 기본 true). 중첩 `CLAUDE.md`와 `@` 임포트는 지침을 `.claude/rules/*.md` + `paths`에 둔다는 결정을 조용히 우회하므로 `agentRules: false`로 끈다. 블록의 요지(Next 코드를 쓰기 전에 `node_modules/next/dist/docs/`의 해당 가이드를 읽는다)는 web 규칙 한 줄로 옮긴다.
- **화면 문구는 한국어이고 용어집의 말을 쓴다.** 예를 들어 실행 상태 "결말 없음"을 "실행 중"으로 옮기지 않는다.

## 이력

### 2026-09-28 CI의 web 단계는 뼈대와 같은 PR에 들고, e2e도 `verify` 잡이 돈다

`web-admin` 명세가 정했다. 위 Consequences의 "워크플로 변경은 별도 PR로 먼저 병합한다(`operations.md`)"는
전제가 좁았다.

- `operations.md`가 별도 PR을 요구하는 것은 `claude-code-review.yml` 하나다. 자기 파일을 바꾼 PR에서 리뷰가
  건너뛰기 때문이다. `ci.yml`만 바꾼 PR은 건너뛰지 않는다(PR #43).
- `web/`이 없는 main에 `pnpm -C web verify`를 먼저 넣으면 필수 검사 `verify`가 빨개진다. 경로 가드로 피하면
  "미매칭은 skip이 아니라 실패"를 어긴다.
- 지침 검사는 아무것도 가리키지 않는 `paths`를 빨강으로 본다. 그래서 web 규칙은 `web/`이 실재하는 커밋에서만 선다.

**`ci.yml`의 Node·pnpm 단계와 `pnpm -C web verify`는 web 워크스페이스의 뼈대를 만드는 첫 티켓의 PR에 함께
든다.** 이 기능은 `claude-code-review.yml`을 바꾸지 않는다.

**e2e는 CI `verify` 잡의 한 단계다.** 필수 검사는 `verify` 하나 그대로이고 e2e가 그 안에 든다. pre-commit에는
넣지 않는다. e2e는 여전히 `pnpm -C web verify` 밖의 별도 명령이다. 로컬에서는 중계, 시작 래퍼, api-client, 서버
라우트를 건드렸을 때 친다. 키도 비용도 들지 않으므로 LLM 테스트처럼 손에만 맡길 이유가 없다. 실제 `serve`,
중계의 SSE, 루프백 래퍼를 함께 보는 테스트는 이것 하나다. 대가는 CI 시간(브라우저 설치와 Next 빌드)이다.

거부한 안은 셋이다.

- **별도 PR을 먼저 병합하고 가드를 둔다.** 규칙에 예외가 는다.
- **뼈대 뒤에 별도 PR.** 한 PR 동안 다섯째 게이트가 CI에 없다.
- **e2e를 필수가 아닌 별도 잡으로.** 빨개도 병합을 막지 못한다. 초록 착시(`operations.md`)와 같은 자리다.

### 2026-09-28 화면을 그리는 테스트는 Testing Library로 쓰고 dev 의존성으로 선언한다

`web-admin` 명세를 쓰며 열렸다. 명세의 주 이음매는 `components/pages/`의 클라이언트 컴포넌트를 jsdom에
그리고 MSW에 붙인 것이다. 위 결정의 테스트 스택은 Vitest와 MSW까지이고, 컴포넌트를 그리고 역할과 글자로
찾는 층이 비어 있었다. **`@testing-library/react`와 그 피어 `@testing-library/dom`, 그리고
`@testing-library/user-event`를 `apps/admin`의 dev 의존성으로 선언한다.** 런타임 의존성은 바뀌지 않는다.

ADR 0010의 2026-09-22 이력이 `httpx`를 들인 것과 같은 자리다. 그리는 코드를 손으로 짜는 안(`react-dom/client`와
`act`)은 거부했다. 그 코드가 곧 자기는 테스트되지 않는 둘째 렌더러가 된다. 찾는 기준이 역할과 글자라서
테스트가 운영자가 보는 것을 단언하게 된다. 클래스 이름이나 구조를 단언하지 않는다. `@testing-library/jest-dom`의
단언은 편의라 들이지 않는다. Playwright의 컴포넌트 테스트는 실험 단계이고 브라우저가 필요해 거부했다.

### 2026-09-29 `next dev`가 만드는 파일이 실리는 길

위 Consequences는 중첩 `CLAUDE.md`와 `@` 임포트가 "지침을 `.claude/rules/*.md` + `paths`에 둔다는 결정을 조용히
우회하므로"라고 적었다. 이것을 공식 memory 문서와 `claude -p` 2.1.281 실측으로 좁힌다(일지 2026-09-29-03·04).

- Claude Code는 2.1.277부터 `AGENTS.md`를 직접 읽는다. 그러나 작업 디렉터리나 조상에 `CLAUDE.md`가 있으면 기본
  설정에서 읽지 않는다. 이 저장소는 루트에 `CLAUDE.md`가 있으므로, `next dev`가 만든 `AGENTS.md`는 곧바로 실리지
  않는다. 같이 생기는 `@AGENTS.md` 한 줄짜리 `CLAUDE.md`를 거쳐, 그 앱 폴더의 파일을 Read할 때 들어온다.
- 우회되는 것은 로드 시점이 아니라 루트 지침에 거는 검사(줄 수, 임포트 허용 목록)다. 그 안의 `@` 임포트가 따라와
  통째로 실리기 때문이다.
- `agentRules: false`와 결과를 보는 검사(`tools/check_instructions.py`의 중첩 지침 파일)는 그대로다. `next dev`의
  파일 생성은 이 체크아웃에 Next가 없어 다시 재지 않았다. 앱을 세우는 티켓(04)이 본다. (2026-09-30, 04가 쟀다.
  에이전트 세션에서 래퍼로 띄운 `next dev`가 `agentRules: false`로는 두 파일을 만들지 않았고, `true`로는 만들었으며
  중첩 지침 파일 검사가 둘을 빨갛게 봤다. 일지 2026-09-30-01)

### 2026-09-29 `--immutable`을 거둔다 — openapi-fetch가 readonly 배열을 배열로 보지 못한다

생성 클라이언트 티켓(03)이 구현하며 쟀다. 위 Consequences의 "`--immutable`로 필드가 readonly가 되고"는 생성물만
보고 정했고, 생성 타입이 openapi-fetch를 지난 뒤의 모양은 재지 않았다.

- openapi-fetch 0.17.0(최신)은 응답을 헬퍼 `openapi-typescript-helpers` 0.1.0의 `Readable<T>`로 감싼다. 배열을
  `T extends (infer E)[]`로 알아보는데 `readonly E[]`는 여기 들지 않고, 키를 재매핑하는 객체 갈래가 배열성을 지운다.
- 그래서 `GET /plugins`의 `data`를 순회할 수 없다(TS2488). 트레이스 상세의 `events`, 에러 봉투의 `violations`도
  같다. 가변 생성물에서는 셋 다 배열이다(`.scratch/web-admin/probes/immutable_readable.sh`, 스크립트로 쟀다).

**`--immutable` 없이 생성한다.** 열거는 그대로 리터럴 유니온이다(`--enum`을 주지 않는 기본값). 잃는 것은 생성
타입의 readonly다. 화면 코드가 서버 데이터를 제자리에서 바꾸는 실수를 타입이 막지 못한다.

거부한 안은 둘이다.

- **pnpm patch로 헬퍼의 `Readable`·`Writable`에 readonly 배열 갈래를 더한다.** 쟀을 때 세 자리가 모두 풀렸다(같은 프로브).
  그러나 판을 올릴 때마다 볼 패치가 생기고, 막을 것(제자리 변경)을 요구하는 화면이 아직 없다.
- **생성물을 두 벌(가변 `paths`, 불변 `components`)로 둔다.** 같은 계약의 타입이 두 벌이다.

**다시 켜는 조건.** openapi-fetch가 readonly 배열을 배열로 보면 다시 켠다. 클라이언트 타입 테스트
(`web/packages/api-client/src/clients.test-d.ts`)의 배열 순회가 그 자리다.
