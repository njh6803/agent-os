# 2026-09-30 (02) 관리 토큰과 플러그인 목록 — 페이지 이음매와 첫 e2e

web-admin 티켓 05. 일지 2026-09-30-01의 "다음"(05가 페이지 이음매와 첫 e2e를 세운다)을 이어 새 세션에서 했다. 브랜치는
`feature/05-admin-token-plugin-list-first-e2e`, 주 체크아웃이다. 요청 범위는 구현·리뷰·커밋·PR·병합까지다. 지시문이 넘긴
상태 하나는 원칙 III의 "생성물도 판정 범위에서 빼지 않는다" 문구다. 04의 리뷰 셋이 짚었고 사용자가 그대로 두기로 했다.
이 티켓의 리뷰가 다시 짚어도 새 결정이 아니고, 고칠지는 사용자가 정한다.

## 한 것

- **첫 화면.** `components/pages/HomePage.tsx`가 관리 토큰이 없으면 넣는 자리(`organisms/AdminTokenForm`)를, 있으면 플러그인
  목록(`organisms/PluginList`)을 그린다. 틀은 `templates/AdminFrame`(슬롯만), 실패는 `molecules/FailureNotice`다.
- **토큰.** `stores/tokens.ts`의 Zustand 스토어가 관리 토큰을 들고 persist를 sessionStorage에 건다. `partialize`로 토큰만
  저장하고 넣는 자리의 알림과 받아들인 횟수는 저장하지 않는다. 받아들이기, 거부(내려놓기), 판정하지 못함, 지우기가 있다.
- **요청과 훅.** `api/plugins`(요청 함수, 데이터가 아니면 `RequestFailure`), `api/failure`(봉투로 좁히기와 화면의 문구),
  `hooks/queries/plugins`(목록 훅, 토큰 확인, 읽기 정책 `READ`), `hooks/useHydrated.ts`(서버가 미리 그린 그림에서 토큰으로
  갈리는 화면을 그리지 않는다).
- **페이지 이음매.** Vitest를 `node`와 `pages`(jsdom) 두 프로젝트로 갈랐다. `testing/`의 셋(MSW 서버와 생성 타입, 그리기와
  SWR 캐시, 격리)과 페이지 테스트 22(셀프 리뷰 뒤 하나를 더했다). 핸들러의 응답 본문은 생성 타입으로 적었다.
- **판정자.** `EventSource`·`XMLHttpRequest`, 앱의 `openapi-fetch` import, 상대 경로로 패키지 안을 import하는 것을 막았다(03의
  메모). 판정자 테스트 51 → 58.
- **첫 e2e.** `e2e/stack.ts`(globalSetup)가 임시 플러그인 루트, 토큰 둘, `serve --port 0`, 그 주소를 상류로 한 `next build`,
  시작 래퍼의 `next start`를 차례로 세우고 `kill()`로 거둔다. `e2e/admin-token.e2e.ts`가 틀린 토큰의 거부, 종류별 목록, 표지,
  꺼짐, 효과 없음, 새로 고침 뒤의 토큰, 넣는 칸이 번쩍이지 않는 것, 저장소·주소·문서·콘솔의 토큰, 지우기를 본다.
- **CI.** `ci.yml`의 `verify` 잡이 web 검증 뒤에 Playwright 판으로 캐시한 헤드리스 셸을 깔고 e2e를 돈다.
- **파이썬 테스트 둘.** 다른 출처의 preflight가 관리·채널 경로 모두 토큰 없이 401(`tests/test_server.py`), keepalive 간격이
  중계의 침묵 한도 30초보다 짧다(`tests/channel/http/test_router.py`, "바깥 행동만"의 예외라고 독스트링에 적었다).
- **문서와 하네스.** `CLAUDE.md` 검증 명령 절의 e2e 괄호, `operations.md` 가드레일(e2e가 셋째 예외, 헌법 3.0.2),
  `.claude/rules/http.md`와 `tests/test_main.py` 독스트링 둘(실제 `serve`를 띄우는 것이 둘), README(트리와 관리 토큰 줄),
  게이트 훅의 독스트링·테스트·페이로드 셋, 프로브 셋과 그 README 행, 06~08의 "05가 남긴 메모".

## 잰 것

- **MSW 3.0.0.** 명세의 `onUnhandledRequest`는 `onUnhandledFrame`으로 이름이 바뀌었다. `"error"` 전략은 요청을 네트워크
  에러로 끝내고 콘솔에 찍기만 한다(설치본의 `interceptor-source.js`를 읽었다). 콜백으로 바꾸면 기본값이 찍기만 하고 요청을
  실제 네트워크로 흘린다. 그래서 전략은 `"error"`로 두고 `request:unhandled` 사건을 받아 적는다.
- **SWR 2.5.1.** 포커스 재검증은 마운트한 때부터 `focusThrottleInterval`(5초) 동안 흘려보낸다(`use-swr` 소스). 포커스
  리스너를 `setTimeout.bind(...)`로 걸어 이벤트 객체가 지연 값 자리에 들어가고, Node가 `TimeoutNaNWarning`을 한 번 찍는다.
  동작에는 영향이 없다.
- **Zustand 5.0.15.** `createJSONStorage`는 저장소를 얻다 던지면 저장소 없이 선다(서버의 한 번 그리기). `useStore`는
  hydration에서 서버 스냅숏으로 `getInitialState()`를 준다.
- **실제 앱.** `transpilePackages` 없이 `next build`가 워크스페이스 패키지의 TS 원본을 번역했다(Turbopack). 빌드는 tsconfig를
  고쳐 쓰지 않았다. molecules가 생성 클라이언트를 import하면 실제 앱의 링크에서도 `boundaries/dependencies`로 빨갛다.
- **e2e의 프로세스(`probes/e2e_process_tree.mjs`).** 래퍼의 `next start`는 자식이 `conhost.exe`뿐이다. `.venv\Scripts\python.exe`는
  기반 인터프리터를 자식으로 띄우지만 런처를 `kill()` 하자 함께 죽었다. e2e 뒤 남은 프로세스가 없었다.
- **브라우저가 없을 때.** 빈 디렉터리를 `PLAYWRIGHT_BROWSERS_PATH`로 주자 `browserType.launch: Executable doesn't exist`로
  `1 failed`, 종료 1이었다. 건너뛰지 않는다. 이 기계에는 1.63.0의 Chromium(1243)이 이미 있었다.
- **web 규칙이 실리는지.** 사용자 설정을 뺀 새 `claude -p` 세션(명령은 일지 2026-09-30-01)에 이 티켓의 파일을 Read로 열게
  하고 `web-workspace.md` 본문의 카나리아를 물었다. 템플릿·스토어·페이지·요청 함수·`useHydrated`는 Haiku가 답했다. SWR
  훅은 Haiku가 세 번 중 두 번 "없음"이라 Sonnet으로 세 번 다시 물었고 세 번 다 답했다. 대조군(`tools/mutate.py`)은 두 모델
  모두 "없음". 실리는데 작은 모델의 답이 흔들린 것으로 읽었다. `paths`는 고치지 않았다.
- **e2e의 서버 출력.** `test-results/serve.log`와 `admin.log`에 토큰이 없었다.

## TDD와 변이

- 페이지 테스트 19를 먼저 쓰고 빨강을 봤다. 모두 "관리 토큰 라벨이 없다"로 빨갰다. 그 빨강은 각 테스트가 지키는 행동의
  빨강이 아니라서 행동마다 변이를 넣었다. 구현 뒤 테스트 둘(이미 보인 행이 실패로 지워진다, 재연결로 다시 읽지 않는다)과
  단언 하나(거부된 뒤 칸이 비었다)를 더했다. 재연결은 변이 목록을 짜다 지키는 테스트가 없다는 것을 알았다.
- `probes/admin_pages_mutations.mjs`(25). 처음 돌렸을 때 24가 기대대로 빨갛고 hydration 가드 하나가 초록이었다. 가드가 두
  그림의 어긋남을 막는다는 독스트링이 틀렸다. 어긋남은 zustand가 막고, 가드가 막는 것은 미리 그린 HTML에 박힌 넣는 칸이
  새로 고칠 때 번쩍이는 것이다. 독스트링을 고치고 e2e가 `addInitScript`의 `MutationObserver`로 그 칸이 문서에 붙는지 보게
  했다(처음 방문에서는 붙는다는 대조를 함께 단언한다). 다시 돌려 25 모두 기대대로 빨강.
- 판정자의 새 빨강 여섯은 설정 파일만 main의 것으로 되돌려 모두 빨간 것을 봤다. 실제 패키지 자리의 초록 하나는 변이(예외
  블록을 다른 경로로)로 빨강을 봤다.
- 파이썬 둘은 `probes/relay_server_mutations.toml`(미들웨어가 `OPTIONS`를 통과, FastAPI의 `_PING_INTERVAL` 30). 둘 다 빨강.
- 게이트 훅은 `tools/run_hooks.py`로 페이로드 34건 모두 기대대로다. 새 셋은 실제 e2e 명령의 파이프(발동), 단독(조용),
  브라우저 설치의 파이프(조용)다.

## 셀프 리뷰

`/code-review main`(base `c7dff2e`, 추적 파일 24개 변경, 커밋 0, 미추적 21). 표준 축 10과 냄새 다섯, 명세 축 9(범위 밖
하나 포함). 두 축 모두 수 주장(페이지 테스트, 판정자 테스트, 변이, 페이로드)과 설치본을 근거로 든 주장을 맞다고 했다.

고친 것:

- **토큰 확인이 스토어에 쓰면서 실패를 돌려줬다**(표준, CQS와 "실패의 형태는 층마다 하나"). 판정을 따로 빼고 결과를 모두
  스토어에 남긴다. 받아들임은 토큰, 거부와 판정하지 못함은 넣는 자리의 알림(`adminTokenNotice`)이다.
- **"지금의 토큰일 때만 내려놓는다"와 "봉투가 온 실패면 받아들인다"에 테스트가 없었다**(표준). 앞의 것을 재는 테스트(지운
  토큰의 늦은 401)를 짜다 **진짜 결함이 드러났다.** SWR 키에 토큰을 싣지 않아, 토큰을 지우고 2초 안에 새 토큰을 넣으면 새
  목록이 옛 토큰의 진행 중인 요청을 중복 제거로 나눠 받아 그 401을 보였다. 테스트가 그 이유로 빨간 것을 본 뒤 키에 토큰을
  받아들인 횟수(`adminTokenGeneration`)를 실었다. 뒤의 것은 운영자 파일 테스트에 "넣는 자리가 아니라 목록 자리가 말하고
  토큰이 저장됐다"는 단언을 더했다. 변이 셋을 더해 28.
- **"요청 식별자"**(명세). 스토리 37과 `http.md`의 말은 "추적 식별자"이고, 용어집에서 요청은 실행의 입력 문자열이다.
- **헌법 3.0.2의 "예외가 셋"**(두 축). 커밋 메시지 검사도 pre-commit에만 있다. 닫힌 수를 쓰지 않고 다시 적었다.
- **`operations.md`의 "CI에는 다음 워크플로 PR에서 더한다"**(표준). 이 PR이 워크플로 PR이라 훅 러너를 CI에 더했다. 01(PR
  #99)이 지나친 약속이다. 러너는 임시 저장소를 `git init`만 해서 CI의 git 신원이 필요 없다.
- **`CLAUDE.md`의 게이트 수**(두 축)를 열하나로, **`tech.md`의 미래형 괄호**를 거뒀다.
- **`stack.ts`**(두 축). 머리 주석의 어긋남("`serve`의 환경에만"과 "워커에 넘긴다", "`kill()` 하나"와 SIGKILL), 같은 모양의
  폴링 둘, 이어 붙이기만 하는 인자 둘. 셸의 환경에 `serve`의 토큰 변수가 있으면 Next가 물려받던 것을 벗겼다(그 환경으로
  e2e를 한 번 더 돌려 초록).
- **명세·티켓의 옛 MSW 이름**(명세). 명세 574행과 티켓에 2026-09-30 주석을 달았다.
- **ubuntu 항목을 CI 전에 체크했다**(명세). CI가 돈 뒤 체크한다.
- **아이콘 메모가 사라졌다**(표준). 06~08의 "05가 남긴 메모"로 넘겼다.
- `testing/network.ts`의 타입 별칭 두 벌을 요청 함수 쪽 것으로 모았다.

남긴 것:

- **층 판정의 공백**(표준 Nit). `stores/`, `hooks/useHydrated.ts`, `testing/`은 `workspace-app` 요소일 뿐이라 atoms·molecules가
  스토어를 import하는 것, 제품 코드가 `testing/`(MSW)을 import하는 것, 컴포넌트가 `useSWR`을 부르는 것을 판정자가 막지
  않는다. 어겨진 적은 없다. 교정 루프의 순서로는 린트가 먼저인 자리라 회고 후보로 올린다.
- **다시 읽다 실패하면 행을 지우는 것**(명세 b). 포커스 때 네트워크가 잠깐 끊겨도 목록이 사라진다. 스토리 16의 논리를 다시
  읽기에 건 결정이라 두고, 티켓의 "이 티켓이 정한 것"에 적어 PR에서 사용자가 본다.
- **`vars(fastapi.routing)["_PING_INTERVAL"]`**(표준 Nit). 사적 이름 하나를 읽는 것이 명세가 적은 예외이고, 값을 `object`로
  받아 `isinstance`로 좁힌다. 기존 테스트가 같은 이름을 문자열로 줄여 쓴다.
- **`servePlugins`가 `Response`를 받는다**(명세 Nit). 생성 타입은 호출하는 쪽의 상수와 `envelope()`가 지킨다. 봉투가 아닌
  500과 네트워크 에러를 같은 자리에서 내야 해서 둔다.
- **`pluginKeys`가 키 하나뿐이다**(냄새). 씨앗의 키 팩토리이고 06이 플러그인 하나의 키를 더한다.
- **`READ`를 plugins 도메인에 둔다**(냄새). 두 도메인이 함께 쓰게 되면 옮긴다고 07 메모에 적었다.
- **`sdk.md`의 `paths`(`plugins/**`)가 web의 `plugins` 도메인 폴더에 걸린다**(명세, 범위 밖). web 파일을 열면 파이썬 규칙이
  실린다. 이 티켓의 폴더 이름이 드러낸 하네스 문제라 따로 떼었다(칩).

## 검사

반영 뒤 검증 명령을 모두 다시 돌렸다. pytest 1015, ruff check·format, pyright 0, lint-imports, 지침 검사, 타입 우회 검사,
훅 러너(페이로드 34, 어긋남 0), `pnpm -C web verify`(테스트 167), e2e 1이 초록이다. 변이 28도 다시 돌려 모두 기대대로
빨갛다. `src/`를 바꾸지 않아 `-m llm`은 돌리지 않았다.

첫 게이트 실행에서 판정자 테스트의 뒷정리(`afterAll`의 `rmSync`)가 `EPERM`으로 실패했다. 테스트 58개는 모두 통과했고, 그
시각에 ruff를 나란히 돌리고 있었다. 혼자 다시 돌리자 초록이었다. 남은 임시 트리(`web/judge-*`)에는 생성 클라이언트 패키지로
가는 junction이 있어, Git Bash의 `rm -rf`가 아니라 Node의 `rmSync`로 지웠다. 링크를 따라 실제 패키지를 지우지 않는다.

## PR 리뷰

PR #103. PR 직전 CodeRabbit CLI는 돌리지 않았다(`Plan: Free`, `Seat: not assigned`).

- **CI 첫 실행**(`73e77ee`, 캐시 없음). `verify` 잡 2분 14초. 브라우저 설치(`--with-deps --only-shell chromium`) 23초, e2e
  9초(`1 passed (8.5s)`), 훅 러너 1초(34건, 어긋남 0). 캐시 `playwright-Linux-1.63.0`을 저장했다. e2e와 훅 러너가 ubuntu에서
  처음 돌았고 둘 다 초록이다.
- **claude-review**(48초, 코멘트 있음). 이 PR은 `ci.yml`을 바꿔 코멘트 0개 가드가 꺼지므로 손으로 봤다. Minor 하나: 판정이
  `RequestFailure`가 아닌 예외를 다시 던지면 `enter`가 reject되어 "넣기" 버튼이 막힌 채 남는다. 예외는 결함이라 삼키지 않고,
  넣는 자리가 `finally`로 버튼을 푼다. Nit 하나(던지는 뜻)는 `verdictOf`에 주석으로 밝혔다. 이 길을 여는 방법(요청 함수는
  모든 실패를 `RequestFailure`로 던진다)이 없어 테스트는 두지 않았다.

## 회고

후보 넷을 냈고 넷 모두 승인됐다.

> 사용자(질문에 답): "판정자 층 공백 (새 항목),임시 트리 뒷정리 EPERM (새 항목),63에 회차 (rules 확인법),61에 회차 (측정과 설치의 판)"

- **64(새로).** 판정자가 `stores/`·`testing/`·`hooks/useHydrated.ts`와 컴포넌트의 `swr` 직접 import를 보지 않는다. 셀프 리뷰의
  표준 축이 찾았다. 어겨진 적은 없지만 기계로 판정할 수 있는 규칙이라 지침보다 린트가 먼저다.
- **65(새로).** 판정자 테스트의 뒷정리가 윈도우에서 다른 프로세스와 겹쳐 `EPERM`으로 실패하고 junction이 든 트리를 남겼다.
- **63(2회차).** 카나리아 탐침에서 Haiku가 실린 파일에도 "없음"이라 답했다(SWR 훅 세 번 중 두 번). Sonnet은 세 번 다 맞았다.
- **61(3회차).** 명세가 적은 MSW 옵션(`onUnhandledRequest`)은 설계 측정의 msw 2.15.0 것이었고, 설치된 3.0.0은 이름과
  `"error"`의 뜻이 달랐다. 측정한 판과 설치하는 판이 major로 다르면 그 측정을 다시 본다.

기각한 것(일지에만 남긴다):

- "CI에는 다음 워크플로 PR에서 더한다"는 약속(main의 `operations.md`)을 01이 지나친 것. 셀프 리뷰 브리프의 미래형 grep이
  이번에 잡았으니 새 장치를 두지 않는다.
- hydration 가드의 독스트링이 재지 않은 이유를 적은 것. 구현 스킬의 변이 규칙이 커밋 전에 잡았다.

회고를 돈 뒤 이 절과 "다음" 절을 적어 넣는 편집에 retro 계기 훅이 다시 걸렸다. 대기열 62가 적은 모양이라 회고를 다시 돌지
않았다. 62에 회차를 더할지는 사용자에게 알린다.

## 다음

- **web-admin의 06이 다음이다.** 06(플러그인 하나와 켜고 끄기)은 05를 기다렸고 05가 병합된다. 05가 06~08에 넘긴 것은 각
  티켓의 "05가 남긴 메모"에 있다.
- 대기열 61이 3회차가 됐다. web-admin의 마지막 티켓(08) 뒤의 chore 배치 대상이다.
- 칩 하나(`sdk.md`의 `paths`가 web의 `plugins` 도메인 폴더에 걸린다)는 사용자가 띄우면 따로 돈다.
