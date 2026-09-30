# 03: 생성 클라이언트 — 계약에서 타입을 생성하고, 관리·채널 클라이언트가 각자 제 토큰만 싣는다

**What to build:** web 코드가 파이썬 서버를 부를 때는 루트 `openapi.json`에서 생성한 타입만 지난다. 생성물은 커밋된다. 파이썬 티켓이 계약을 바꾸고 다시 생성하지 않으면 다섯째 명령이 빨개져, 생성물이 같은 PR에 담긴다. 클라이언트는 둘이다. 관리 클라이언트는 관리 토큰만, 채널 클라이언트는 채널 토큰만 싣는다. 한 토큰이 맡지 않은 경로에 실리는 실수는 타입이 막는다. 재개 스트림(SSE)은 손으로 받아 판별자 술어로 생성 타입 `Event`로 좁힌다. 술어를 지나지 못한 프레임은 버리지 않고 원문으로 넘긴다. 화면은 아직 없다. 관리 클라이언트는 05부터, 채널 클라이언트와 SSE는 08이 쓴다.

02가 결정 본문을 바꾼 뒤에 생성한다. 그래서 생성물이 옛 본문으로 한 번 서는 일이 없다. 이 기능의 web 티켓 가운데 생성물을 쓰는 것은 모두 이 티켓 뒤다.

근거는 `.scratch/web-admin/spec.md`의 "생성 클라이언트", "판정자와 검사"의 생성물 최신성, "좁은 이음매 — 순수 함수" 절이다. ADR 0021, ADR 0010의 2026-09-28 이력, `jsdom_sse.sh`도 근거다.

**Blocked by:** 01(워크스페이스, 판정자, `verify`), 02(결정 본문의 자리)

**Status:** done

### 생성

- [x] **openapi-typescript로 생성한다.** 열거는 리터럴 유니온이다. 생성물을 커밋하고, 손으로 고치지 않는다. `--immutable`은 거뒀다. openapi-fetch 0.17.0이 readonly 배열을 배열로 보지 못해 응답을 순회할 수 없었다(ADR 0021의 2026-09-29 이력, 구현 중에 사용자가 골랐다)
- [x] **재귀 `Json`은 생성 스크립트가 `unknown`으로 바꾼다.** openapi-typescript는 `Json`이 제 자신을 가리키는 한 자리에서 TS2502를 내고 그것을 `any`로 둔다. 변환은 순수 함수이고 그 자리 하나만 바꾼다. 다른 곳에 `any`가 생기면 판정자가 빨개지도록 둔다
  - 테스트: openapi-typescript가 낸 그 자리만 `unknown`이 되고 다른 바이트는 그대로다
  - 테스트: 기대한 자리가 없으면 조용히 지나가지 않고 실패한다. 생성기를 올려 모양이 바뀌면 알아야 한다
- [x] **생성물 최신성은 `pnpm -C web verify`의 한 단계다.** 루트 `openapi.json`에서 다시 생성한 결과가 커밋된 생성물과 같은지 본다. 저장소는 `* text=auto eol=lf`라서 윈도우와 CI가 같은 바이트를 본다
  - 저장소 상태 테스트: 지금 통과한다
  - 변이: `openapi.json`의 설명 한 줄을 바꾼 사본에서 실패한다. 스토리 75(파이썬 티켓이 계약을 바꾸면 다섯째 명령이 빨갛다)가 이것이다
- [x] **생성물은 판정 범위 안이다.** 판정자가 커밋된 생성물을 무시하지 않는다는 것을 변이로 본다. 빼는 목록을 두지 않는다(ADR 0020). 바꾼 뒤의 생성물에 `any`가 없다는 것도 판정자가 본다

### 클라이언트 둘

- [x] **토큰은 요청의 경로를 보고 고르지 않고, 클라이언트가 고른다.** 둘 다 openapi-fetch이고 생성된 `paths`를 쓴다
  - 관리 클라이언트는 관리 토큰을 싣는다. 그 타입은 생성된 `paths`에서 채널의 경로 둘을 뺀 것이다
  - 채널 클라이언트는 채널 토큰을 싣는다. 그 타입은 결정 경로 하나만 안다
- [x] **타입 테스트**(`*.test-d.ts`, 설명 붙은 `@ts-expect-error`). 관리 클라이언트로 채널 경로를 부르면 컴파일이 실패한다. 채널 클라이언트로 관리 경로를 불러도 실패한다. 계약에 채널 경로가 늘면 관리 클라이언트의 타입에 새 경로가 보여, 그 목록을 고칠 자리가 컴파일러 앞에 선다
- [x] **헤더의 행동은 페이지 테스트가 잰다.** 관리 요청은 05, 결정 요청은 08의 몫이다. 이 티켓에 둘 수도 있지만 받는 쪽이 둘이다
- [x] **`baseUrl`은 `location.origin`에서 만든 절대 주소다.** 상대 경로 `/api`는 jsdom에서 `Failed to parse URL`로 섰다(`jsdom_sse.sh`). 한 모양이어야 테스트가 제품 코드를 본다

### SSE

- [x] **`parseAs: "stream"`으로 받아 `data:` 줄을 파싱한다.** 프레임 파서는 순수 함수다
  - 조각 경계가 프레임 한가운데서 갈려도 프레임 하나다. 한 조각에 프레임이 여럿이어도 된다
  - 주석 줄(keepalive `:`)은 이벤트가 아니다
  - 줄 끝은 `\r\n`과 `\n`을 모두 받는다
  - `data:` 뒤의 공백 하나는 값이 아니다. 파이썬 쪽 선례는 `tests/test_main.py`의 `test_스트림을_가를_때_keepalive_주석은_이벤트로_읽지_않는다`다
- [x] **판별자 술어는 판별자만 본다.** 계약의 종류마다 참이다. 모르는 `type`, 객체가 아닌 것, `type`이 없는 것은 거짓이다. 종류 목록은 `satisfies Record<Event["type"], true>`로 두어 컴파일러가 생성 타입과 대조한다. 목록이 생성 타입과 어긋나면 컴파일이 실패한다는 것을 타입 테스트 파일에서 `@ts-expect-error`로 고정한다
- [x] **술어를 지나지 못한 프레임은 버리지 않는다.** `JSON.parse`에 실패한 것도 같다. 원문 그대로 넘기고 스트림을 계속 읽는다. 화면이 그것을 글자로 보이는 것은 08이다
- [x] **에러 응답은 JSON 봉투다.** 스트림 경로에서도 에러는 스트림이 시작되기 전에 JSON으로 나간다(`.claude/rules/http.md`). openapi-fetch는 `parseAs: "stream"`에서도 409 봉투를 `error`에 파싱했다(`jsdom_sse.sh`)

### 판정자와 지침

- [x] **01이 경로와 무관하게 쓴 전역 `fetch` 금지를 실제 패키지 자리에서 다시 본다.** 이 패키지는 `fetch`를 직접 부르지 않아(부르는 것은 openapi-fetch다) 01의 예외를 거뒀다. 그래서 패키지 밖에서도 안에서도 빨갛고, 커밋된 패키지는 통과한다
- [x] 이 패키지 경로에만 걸리는 판단 기준이 생기면 `.claude/rules/web-*.md` + `paths`로 둔다. 생성물을 손으로 고치지 않는다는 것은 최신성 검사가 판정하므로 적지 않는다. 생기지 않았다. 결정을 `Decision` 타입 값으로 넘겨야 한다는 것은 어기면 `readFrames`에서 컴파일이 실패한다

### 01이 남긴 메모

- **판정 범위와 tsconfig.** 01의 판정자는 어느 tsconfig에 든 파일만 타입 기반 규칙으로 본다. 어느 tsconfig에도 들지 않는 파일은 규칙이 아니라 파싱 오류로 빨개진다. 이 패키지는 기준 tsconfig를 `extends`하는 자기 tsconfig를 두고 생성물도 그 안에 든다. 01의 `pnpm run typecheck`는 루트 `web/tsconfig.json`(루트의 파일과 `tools/`)만 돈다. 이 패키지의 tsconfig도 verify가 돌게 한다(04와 같은 일이다. 먼저 하는 쪽의 모양을 따른다)
- **fetch 예외는 이미 있다.** 01이 `web/eslint.config.mjs`에 `**/packages/api-client/**`의 전역 `fetch` 예외를 두었다. 초록 사례는 `web/eslint.config.test.ts`에 있다. 이 패키지가 `fetch`를 직접 부르지 않으면 예외를 거둔다
- **atoms·molecules가 이 패키지를 import하지 못하게.** 01의 층 경계는 로컬 요소만 이름으로 안다. 패키지 이름이 정해지면 `boundaries/dependencies`에 atoms·molecules에서 이 패키지로 가는 import 금지를 더하고 사례를 붙인다. `checkAllOrigins`는 이미 켜져 있다. `app/`에서는 `next`·`react` 밖의 외부 import가 이미 막혀 있다
- **web verify가 늘 도는 둘째 이유.** 최신성 단계가 서면 파이썬 티켓의 `openapi.json` 변경이 web verify를 빨갛게 한다. `.pre-commit-config.yaml`의 web-verify 주석과 `operations.md` 가드레일의 `always_run` 문장에 이 이유를 더한다. 01은 생성물이 없어 적지 않았다
- **verify의 단계가 적힌 곳.** 원천은 `web/package.json`의 `verify`다. 도구 이름으로 다시 적은 곳은 `operations.md` 가드레일의 web 문장 하나다(`CLAUDE.md`, PR 템플릿, pre-commit은 `package.json`을 가리킨다). 최신성 단계를 더하면 그 문장도 고친다

### 확인

- [x] TS 테스트의 이름은 행동을 말하는 한국어 문장이다
- [x] `CLAUDE.md`의 검증 명령이 모두 초록이다

### 이 티켓이 정한 것 (2026-09-29, PR에서 사용자가 본다)

- **`--immutable`을 거뒀다.** 구현 중에 사용자가 골랐다(ADR 0021의 2026-09-29 이력). openapi-fetch 0.17.0(최신)의 응답
  타입 `Readable<T>`가 `readonly E[]`를 배열로 알아보지 못해 목록 응답을 순회할 수 없었다(TS2488). 근거는
  `probes/immutable_readable.sh`다. 다시 켜는 조건의 판정 자리는 `clients.test-d.ts`의 배열 순회다. 가변 배열과 같은지가
  아니라 순회할 수 있는지와 원소가 생성 스키마에 들어가는지를 봐서, 고쳐진 뒤 다시 켜면 readonly 배열이어도 초록이다.
- **생성 스크립트는 `web/tools/generate-api-client.ts`다.** Node에서 도는 도구는 `web/tools/`(루트 tsconfig, node 타입)에
  두고, 패키지는 브라우저 코드만 든다(패키지 tsconfig는 `lib: dom`에 `types: []`). 그래서 openapi-typescript는 루트의 dev
  의존성이고 openapi-fetch는 패키지의 의존성이다. CLI가 아니라 API를 부른다. CLI는 머리 주석을 붙이고 Redocly 설정을
  따로 찾는다(`redocly.yaml`, 없으면 `minimal`). API는 operationId 중복을 에러로 보는 기본 설정이다. 이 계약에서 두 출력은
  머리 주석 밖에서 바이트까지 같았다(같은 프로브). 머리 주석은 한국어로 바꿔 다시 생성하는 명령을 적었다. Prettier도
  스크립트가 돌린다. 생성물도 `prettier --check .`의 범위라서다.
- **생성물은 `.d.ts`가 아니라 `packages/api-client/src/generated/openapi.ts`다.** 기준 tsconfig가 `skipLibCheck: true`라
  `.d.ts`는 tsc가 보지 않는다. 가공하지 않은 생성물의 TS2502가 tsc에서 보이는 것도 `.ts`여서다.
- **verify의 첫 단계가 최신성이다.** `pnpm run check:api-client && pnpm run lint && …`. 생성물이 낡으면 뒤 단계의 실패가 그
  결과일 수 있어, 바로 고칠 수 있는 진단("다시 생성해 같은 커밋에 담는다")이 먼저 나온다. 같은 판정을 Vitest의 저장소 상태
  테스트도 한다. tsconfig 검사와 같은 짝이다.
- **typecheck는 `tsc --noEmit && pnpm -r exec tsc --noEmit`다.** 워크스페이스 패키지마다 제 tsconfig로 돈다. 목록이 없어서
  04의 앱도 저절로 든다. tsconfig가 없는 패키지에서는 tsc가 도움말을 내고 1로 끝나 조용히 빠지지 않는다(쟀다). 루트 도구를
  PATH에 싣는 것은 pnpm이다.
- **atoms·molecules의 import 금지는 모듈 이름으로 건다.** `{ module: { origin: "external", source: "@agent-os/api-client" } }`.
  pnpm 링크(윈도우는 junction)로 풀린 워크스페이스 패키지를 boundaries가 external로 분류했다(쟀다). 판정자 테스트는 임시
  트리의 앱 자리에서 실제 패키지로 junction을 두고 잰다. 링크가 없으면 초록 사례의 import가 풀리지 않아 타입 기반 규칙으로
  빨개진다. 상대 경로로 패키지 안을 import하는 길은 로컬로 분류되어 이 규칙이 보지 못한다(05의 메모).
- **채널의 경로 둘은 `/runs`와 `/runs/{run_id}/approval`이다.** 관리 클라이언트는 나머지 여섯(`/health` 포함)을 안다.
  클라이언트는 토큰 문자열을 만들 때 받고, 요청마다 `Authorization: Bearer <토큰>`을 싣는다. 두 토큰을 바꿔 넣는 실수는
  타입이 막지 않는다. 브랜드 식별자를 두지 않는다는 ADR 0021의 결정 그대로다.
- **`baseUrl`은 실행 테스트가 잰다(`clients.test.ts`).** 헤더는 티켓대로 05·08의 몫이라 여기서는 주소만 본다. openapi-fetch는
  클라이언트를 만들 때 전역 `fetch`를 쥐므로 가짜를 먼저 건다.
- **스트림의 프레임은 `{ kind: "event", event }` 또는 `{ kind: "raw", raw }`다.** `raw`는 그 프레임의 `data` 값이다.
  트레이스 상세의 `UnknownEvent`를 빌려 쓰지 않았다. 그것은 판별자만 모르는 줄이고 원문이 유효한 JSON이다
  (`adapters/jsonl.py`의 `_require_raw_run`). 여기 원문은 JSON이 아닐 수 있다.
- **스트림이 프레임 한가운데서 끝나면 남은 것을 프레임 하나로 닫아 넘긴다.** 술어를 지나면 이벤트이고, 못 지나면 원문이다.
  SSE 명세는 끝나지 않은 프레임을 버리지만, 재접속이 없고 기록의 원천은 스트림이 끝난 뒤 다시 읽는 트레이스다.
- **파서는 SSE의 규칙대로 읽는다.** `data` 줄이 여럿이면 줄바꿈으로 잇고, 콜론이 없는 줄은 이름이 줄 전체이고, 다른
  필드(`event`, `id`, `retry`)는 값에 들지 않는다. 홀로 선 `\r`은 줄 끝으로 받지 않는다(서버가 보내지 않는다).
  **못 보는 것:** `data` 줄이 없는 블록은 프레임이 아니다. keepalive 주석과 `retry:`·`id:` 제어 블록이 그렇고, 모르는 필드
  이름의 줄(`data:` 접두사가 빠진 JSON 한 줄)만 든 블록도 조용히 사라진다. 원문으로 넘기면 제어 블록이 잡음이 된다. 서버는
  그런 블록을 보내지 않는다.
- **스트림의 수명은 부른 쪽의 것이다.** 연결을 끊는 길은 요청에 준 `signal`(AbortController)이다. 끊으면 다음 조각을
  기다리던 읽기가 그 에러로 끝나고 `readFrames`가 그 에러를 던지며 잠금을 푼다. 반복자의 `return()`으로는 끊지 못한다.
  기다리던 읽기가 풀린 뒤에야 닿고, 그동안 스트림이 잠겨 `stream.cancel()`도 거부된다(PR #101 CodeRabbit). 새 API를
  두지 않은 이유는 요청의 `signal`이 응답이 오기 전 단계까지 덮기 때문이다.
- **끝나지 않은 프레임의 크기에 상한을 두지 않는다.** 상류는 운영자의 루프백 서버다(ADR 0019·0011). 상한을 두면 큰
  `llm_called` 같은 정상 이벤트가 잘리고, 넘쳤을 때의 동작을 새로 정해야 한다(PR #101 CodeRabbit이 1MiB를 권했다).
  위젯처럼 믿지 못할 상류 앞에 설 때 다시 본다.
- **변이는 `probes/api_client_mutations.mjs`가 넣는다.** `tools/mutate.py`가 pytest만 돌아서 같은 규약(원문이 한 번, 기준선,
  바이트 그대로 되돌리기, 오류는 빨강이 아니다)을 따르는 러너를 프로브로 두었다. 25 모두 기대대로 빨강이다. 처음 돌렸을 때
  하나가 초록이라(조각 경계가 `data:` 줄과 빈 줄 사이에 온다) 테스트를 더했다. (2026-10-01) 도구가 pytest 밖의 명령을
  돌게 되며 `probes/api_client_mutations.toml`로 옮겼다(대기열 59).
- **명세의 세 문장을 고쳤다.** 생성 절의 `--immutable`, 판정자 절의 "전역 `fetch`는 생성 클라이언트 패키지 밖에서", 첫
  티켓 변이 목록의 "생성 클라이언트 밖의 전역 `fetch`"다. 닫힌 티켓 01, 일지, ADR 0021 본문의 옛 문장은 그때의 기록이라
  두었다.
