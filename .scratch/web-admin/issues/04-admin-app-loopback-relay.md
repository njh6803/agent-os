# 04: 관리 화면이 루프백에만 서서 `/api`를 파이썬 서버로 중계한다

**What to build:** 운영자가 관리 화면을 띄우면 `127.0.0.1`이나 `::1`에만 선다. 다른 호스트를 주면 구성 오류로 끝나고, 진단이 허용되는 두 주소와 SSH 포트 포워딩을 안내한다. 같은 출처의 `/api/*`는 압축 없이 루프백의 파이썬 서버(상류)로 넘어간다. 상류가 루프백이 아니면 설정이 읽힐 때 구성 오류다. `next dev`는 앱 폴더에 `AGENTS.md`와 `CLAUDE.md`를 만들지 않는다. 화면은 아직 자리표시 하나다. 확인은 이렇게 한다. 운영자가 `serve`와 관리 화면을 띄운다. 관리 토큰을 헤더에 실은 요청을 관리 화면의 출처로 보낸다. 파이썬 서버의 JSON이 그대로 돌아온다.

**나누지 않는 짝 둘이 이 티켓이다.** 짝의 한쪽만 main에 병합되면 ADR의 약속이 그동안 빈다.

- `dev`·`start` 스크립트, 시작 래퍼, `agentRules: false`. 나뉘면 `next dev`가 `0.0.0.0`에 서고(ADR 0019), 앱 폴더에 지침 파일이 생긴다(ADR 0021)
- `rewrites`, `compress: false`, 상류의 루프백 판정. 중계가 루프백에 서도 상류가 다른 호스트면 토큰이 그 사이를 평문으로 지난다(ADR 0011의 CWE-319)

토큰을 저장하고 싣는 화면(05)은 이 티켓 뒤다. 생성 클라이언트를 쓰지 않으므로 02·03에 막히지 않고 그 둘과 나란히 돈다. 03과 lockfile이 부딪히면 뒤에 병합되는 쪽이 main을 받아 다시 설치한다.

근거는 `.scratch/web-admin/spec.md`의 "관리 화면 — 중계와 시작 래퍼", "좁은 이음매"의 루프백 판정, "판정자와 검사" 절이다. ADR 0019, ADR 0011의 2026-09-28 이력, ADR 0021, `next_measure.mjs`도 근거다.

**Blocked by:** 01

**Status:** ready-for-agent

### 앱

- [ ] **`apps/admin`은 Next 16과 React 19다.** 앱의 tsconfig는 01의 기준 tsconfig를 `extends`한다. `app/**/page.tsx`는 라우팅과 레이아웃만 한다
- [ ] **앱의 규칙 파일**(`.claude/rules/web-*.md` + `paths`, 이 앱 경로)을 세운다
  - Next 코드를 쓰기 전에 `node_modules/next/dist/docs/`의 가이드를 읽는다
  - `agentRules: false`가 끈 블록의 요지를 한 줄로 옮긴다(ADR 0021)
- [ ] **01이 경로와 무관하게 쓴 규칙이 실제 배치에서 빨간지 다시 본다.** 01의 변이를 앱의 실제 자리에 넣는다. 대상은 여섯이다
  - Next 서버 파일 넷(`route`, `middleware`, `proxy`, `instrumentation`)
  - `"use server"`
  - 전역 `fetch`
  - `dangerouslySetInnerHTML`
  - `app/`의 파일이 pages·templates 밖을 import하는 것
  - 층 경계
- [ ] **01이 재지 못한 것을 실제 앱에서 본다.** 타입 기반 규칙이 앱 자리의 파일에 도는지다
- [ ] **설치된 Next 16.3.6이 16.3.3과 같은지 다시 본다.** 명세 검토는 16.3.3의 코드를 읽었다. `rewrites`가 빌드 산출물에 박히는지, 서버 파일 관례가 같은지를 본다. 어긋나면 설정을 고친다. 새 결정이 필요하면 멈추고 ADR의 이력을 제안한다

### 시작 래퍼 (짝 하나)

- [ ] **`dev`와 `start`는 래퍼를 거친다.** 래퍼는 바인딩 호스트가 `127.0.0.1`이나 `::1`이 아니면 구성 오류로 끝난다. 진단은 `serve`처럼 SSH 포트 포워딩을 안내한다. 선례는 `tests/test_main.py`의 `test_루프백이_아닌_호스트는_서버가_뜨지_않고_진단이_SSH_포트_포워딩을_안내한다`다
- [ ] **판정은 순수 함수이고 `serve`의 규칙과 같다.** 허용 목록은 둘이고 문자열 그대로 비교한다
  - `127.0.0.1`과 `::1`은 통과한다
  - `0.0.0.0`, `::`, `localhost`, LAN 주소, 호스트 이름은 구성 오류다. 진단이 허용되는 두 주소와 SSH 포트 포워딩을 말한다
  - `localhost`는 `::1`로도 풀릴 수 있어 루프백이라는 보장이 없다(`test_허용되는_루프백_주소_둘이_진단에_그대로_적혀_있다`)
- [ ] **래퍼의 테스트.** 루프백이 아닌 호스트로 띄우면 포트를 열지 않고 실패 종료 코드로 끝난다. 운영자가 `next`를 직접 다른 인자로 띄우는 것은 막지 못한다(ADR 0019)
- [ ] **래퍼와 두 판정의 테스트는 윈도우와 CI의 ubuntu에서 모두 돈다.** 운영체제별 명령(설계 측정의 taskkill, netstat 같은 것)에 기대지 않는다. 이 저장소의 개발 기계는 윈도우다
- [ ] **`agentRules: false`.** 앱 폴더에 `AGENTS.md`와 `CLAUDE.md`가 생기지 않는 것은 01의 중첩 지침 검사가 결과로 판정한다. 에이전트 세션에서 `next dev`를 한 번 실제로 띄워 두 파일이 생기지 않는 것을 본다(`CLAUDE.md` 작업 규약 3)

### 중계 (짝 둘)

- [ ] **`rewrites`는 같은 출처의 `/api/*`를 상류로 넘기고 `compress: false`다.** 기본 압축은 SSE를 끝에 몰았다. 끄면 500ms 간격 그대로 흘렀다(`next_measure.mjs`). `Authorization`, `OPTIONS`, 클라이언트의 끊김은 그대로 상류로 간다
- [ ] **상류도 루프백이다.** 호스트가 `127.0.0.1`이나 `::1`이 아니면 설정이 읽힐 때 구성 오류로 끝낸다. 판정은 설정 파일 안이다. `dev`와 `build`와 `start`가 모두 그 파일을 읽으므로 한 자리에서 막힌다. 판정은 래퍼와 같은 순수 함수이고 같은 표로 잰다
- [ ] **상류 기본값은 `http://127.0.0.1:8000`이다**(`serve`의 기본 포트). 상류 입력의 이름은 이 티켓이 정한다
- [ ] **`rewrites`는 빌드 산출물에 박힌다.** 상류 입력은 빌드 때의 값이고, 보안은 빌드 때의 판정이 지킨다. 빌드 때 판정을 통과한 값만 박힌다
- [ ] **`compress: false`의 회귀를 잡는 테스트는 08이 받는다.** 결정 e2e가 재개 스트림이 조각으로 오는지 본다. 그 사이에 이 설정이 빠져도 아무것도 빨개지지 않는다. SSE를 중계로 받는 화면이 08 전에는 없기 때문이다. 그 사실을 PR에 적는다

### README

- [ ] **관리 화면을 띄우는 법을 적는다.**
  - 파이썬 `serve`와 상류 포트를 맞춘다
  - 상류 포트를 바꾸면 다시 빌드한다
  - 루프백에만 서고, 원격은 SSH 포트 포워딩이다
  - 토큰을 넣는 줄은 05(관리)와 08(채널)이 더한다

### 01이 남긴 메모

- **타입 기반 규칙은 앱 자리에서 돌았다.** 01은 web/ 아래 임시 트리의 `apps/admin/`에 기준 tsconfig를 `extends`하는 자기 tsconfig를 두고 그 아래 파일에 쟀다. 프로젝트 서비스는 파일에서 가장 가까운 tsconfig를 찾는다. 어느 tsconfig에도 들지 않는 파일은 규칙이 아니라 파싱 오류로 빨개진다. 위 "앱" 절의 "01이 재지 못한 것" 상자는 그래서 Next가 쓰는 실제 tsconfig(Next가 고쳐 쓰는 `compilerOptions`와 `include`)에서 다시 보는 일이 된다
- **typecheck와 Vitest의 범위.** 01의 `pnpm run typecheck`는 루트 `web/tsconfig.json`(루트의 파일과 `tools/`)만 돈다. 앱의 tsconfig도 verify가 돌게 한다(03과 같은 일이다. 먼저 하는 쪽의 모양을 따른다). Vitest는 루트 설정 하나이고 파일을 차례로 돈다(`fileParallelism: false`. 판정자 테스트가 web/ 아래에 임시 트리를 쓰고 tsconfig 검사가 web/을 훑는다). jsdom 환경은 앱 쪽 설정이 든다
- **빌드 산출물.** `pnpm run lint`(ESLint)와 `prettier --check .`는 web/ 전체를 보고, tsconfig 검사(`web/tools/check-tsconfig.ts`)도 `node_modules`만 빼고 web/을 훑는다. `.next/`에 Next가 생성한 `.ts`나 tsconfig 류 파일이 생기면 셋 다 그것을 본다(PR #99 CodeRabbit Nit). Prettier는 web/의 `.gitignore`만 읽고 저장소 루트의 것은 읽지 않는다. 빌드 산출물을 어떻게 다룰지 정하되, 소스를 판정 범위에서 빼는 목록이 되지 않게 한다
- **`app/`의 import.** 01의 정책은 `app/`의 파일이 pages·templates와 외부의 `next`·`react`만 import하게 한다. 같은 요소 안의 import는 보지 않으므로 `app/globals.css`는 된다. `app/` 밖의 CSS를 import하면 막힌다
- **아이콘.** lucide-react 1.48에는 `exports` 맵이 없다. 서브패스 import의 모양과 그 타입이 서는지 본다. 01은 `lucide-react`를 통째로 import하는 것만 막았다

### 확인

- [ ] TS 테스트의 이름은 행동을 말하는 한국어 문장이다
- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이다
