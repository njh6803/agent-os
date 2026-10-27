# 01: 명암비 모듈 — 패키지가 명암비 계산과 짝 표를 한 파일 모듈로 내보내고, `web/tools`의 스크립트가 그것으로 판정한다

**What to build:** 디자인 시스템 패키지(`@agent-os/ui`)가 상대 import 없는 한 파일 모듈을 새 경로로 내보낸다. 그 모듈에는 명암비 계산(`contrastRatio`, 반투명을 겹치는 `composite`와 그 도우미), 쓰임새 토큰 목록, 반투명 목록, 짝 표, 판정 함수(`contrastFailures`)가 든다. 판정 스토리 Matrix와 테스트 도우미(`@agent-os/ui/testing`)는 그 모듈에서 불러 쓰고, 루트 `web/package.json`이 패키지를 작업 공간 의존으로 들여 `web/tools`의 스크립트가 같은 짝 표와 같은 공식으로 판정할 수 있다. 화면과 사진은 바뀌지 않는다.

근거는 `.scratch/design-reverse-sync/spec.md`의 "명암비 계산을 부르는 길"과 그 프로브 `probes/tools_import.mjs`(Node 24.19.0, pnpm 11.24.0, TypeScript 5.9.3, 커밋 `14efe41d`에서 상대 import 없는 한 파일을 내보내자 루트 타입 검사가 초록이고 실행이 짝 43개를 판정했다), 그리고 Further Notes의 2026-10-22 명세 검토 주석이다. 결정은 ADR 0025의 2026-10-21 이력 "명세가 정할 것 (6)"이다.

이 티켓은 패키지의 `exports`라는 티켓 사이의 이음매를 만들어 04(들이기 명령)를 막는다. 계약(`sdk/`, `openapi.json`, 헌법)에는 닿지 않는다. 02와 파일이 겹치지 않아 나란히 돈다.

**Blocked by:** None (can start immediately)

**Status:** done

### 모듈과 내보내기

- [x] **새 모듈은 상대 import가 하나도 없는 한 파일이다.** 지금 짝 표 파일(`src/styles/contrast.ts`)을 그대로 내보내면 루트 타입 검사가 확장자 없는 import에서 TS2834·TS2835로 빨갛고, Node가 첫 import를 폴더 import로 읽어 `ERR_UNSUPPORTED_DIR_IMPORT`로 멈췄다(프로브). 그 둘을 먼저 빨강으로 본 뒤 한 파일로 옮긴다. 지금 짝 표 파일은 계산 함수와 `Mode` 타입도 상대 경로로 들이므로, 한 파일에 그 정의를 함께 둔다. `Mode`는 `themes.ts`의 `MODES`에서 나오므로 `MODES`와 함께 새 모듈로 옮기고 `themes.ts`가 새 모듈에서 들여, 정의가 두 벌로 갈라지지 않게 한다(새 모듈은 상대 import가 없어야 하므로 들이는 쪽이 `themes.ts`다)
- [x] **`testing`의 DOM 쪽 함수(`sheetsDefining`, `classesWithoutRules`, `arbitraryClasses`)는 새 모듈에 넣지 않는다.** DOM 타입을 써서 DOM 없는 루트 설정(`lib` es2024)의 타입 검사에서 빨갈 것으로 본다(명세의 어림). 새 모듈이 루트 타입 검사를 지나는 것으로 확인한다
- [x] **판정 스토리 Matrix와 `testing`이 새 모듈에서 불러 쓰고, 짝 표와 공식이 한 벌만 남는다.** 같은 함수의 사본이 둘이면 이 티켓의 뜻이 없다
- [x] **짝 표 파일 머리의 "패키지 밖으로 내보내지 않는다"를 고친다**(명세의 같은 절)
- [x] **루트 `web/package.json`이 `@agent-os/ui`를 작업 공간 의존(`workspace:*`)으로 들이고, `pnpm-lock.yaml`의 변화가 그 한 줄의 의존뿐이다**

### 시험

- [x] **`web/tools` 아래 vitest node 프로젝트의 시험 하나가 새 모듈을 패키지 이름으로 불러 판정 함수를 부른다.** 값은 합성한다. 쓰임새 토큰을 모두 검은 값으로 주면 짝 43개가 모두 걸리고(프로브의 `self-contained` 갈래와 같다), 글자로만 쓰이는 토큰 하나(`text-muted` 등)만 흰 값으로 바꾸면 그 토큰을 글자로 드는 짝이 걸린 목록에서 빠지고 다른 짝은 그대로인 것을 본다(초록만 보는 시험은 어떤 구현에서도 초록이다). 바탕으로도 쓰이는 토큰(`accent`는 `on-accent` 짝의 바탕이다)을 바꾸면 다른 짝도 함께 바뀌므로 고르지 않는다(셀프 리뷰가 짝 표 파일을 읽었다). 지금 디자인 토큰 CSS의 여덟 벌을 판정하는 것은 파서가 서는 04가 본다. 이 티켓은 디자인 토큰 CSS를 풀지 않는다
- [x] **같은 시험 파일을 루트 타입 검사(`tsc --noEmit`)가 지난다.** 프로브가 잰 소비 지점이 타입 검사와 실행 둘이기 때문이다(`docs/agents/issue-tracker.md`의 소비 지점)
- [x] **판정 스토리 Matrix가 그대로 초록이다**(`pnpm -C web verify`의 storybook 프로젝트)

### 검증과 기능

- [x] **원칙 III를 지킨다**(TypeScript의 타입 단언과 `any` 없이)
- [x] 검증 명령이 모두 초록이다. 패키지를 건드리므로 사진 비교(`pnpm -C web visual`, Docker)를 로컬에서 한 번 돌려 바뀐 사진이 없는 것을 본다(`CLAUDE.md`의 web 괄호)
- [x] 이 기능의 첫 병합이면 `.scratch/plan.md`의 design-reverse-sync 행을 `in-progress`로 바꾼다. 02와 나란히 돌므로 병합 직전에 `git fetch` 뒤 origin/main의 그 행이 아직 `todo`인지 보고 판정하며, main을 다시 합치면 다시 본다
- [x] **기능을 닫지 않는다.** 이 티켓은 04를 막는다
