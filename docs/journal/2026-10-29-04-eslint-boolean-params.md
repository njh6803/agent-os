# 2026-10-29 (04) ESLint 가 불리언 매개변수를 잡는다 (harness 022)

next-session 지시문으로 연 새 세션이다. 나란히 여는 여덟 가운데 넷째라 `tidy-checkouts`는 돌지 않았고(묶음의 첫 세션이
돈다), 주 체크아웃에서 브랜치를 따지 않고 워크트리 `022-eslint-boolean-params`에 들어가 `chore/022-eslint-boolean-params`로
바꿨다. 일지 번호는 처음 19를 받았으나 형제 `023-widget-char-count-flake`가 같은 때 19를 써서 `tools/sibling_overlap.py
--move`로 22로 옮겼다(그 사이 20·21도 형제가 가져갔다). 셀프 리뷰를 반영한 뒤 커밋 전 검사에서 origin/main 이 일지
23(PR #415)을 들여, 이 일지가 이름순으로 앞서지 않게 다시 `--move`로 26으로 옮겼다.

> 사용자: "대기열 483을 티켓 .scratch/harness/issues/022-eslint-boolean-params.md로 쓰고 한다"

## 세 줄 계획

(1) `web/eslint.config.mjs`의 `RESTRICTED_SYNTAX`에 불리언 매개변수 selector 를 더하고 `web/eslint.config.test.ts`에
걸리는 사례와 지나는 사례를 먼저 쓴다. (2) 켜기 전 `web/`의 위반을 세어 고친다. (3) `CODING_STANDARDS.md`의 불리언 플래그
줄이 이 규칙을 가리키게 고친다. 계약(`sdk/`, `openapi.json`, 헌법)에는 닿지 않는다.

## 설계

- 잡는 자리는 파이썬의 ruff FBT001·FBT002 에 맞췄다. 함수 정의(`:function`, 곧 선언·함수 식·화살표 함수와 그 안에 든
  메서드)의 매개변수 가운데 주석이 `boolean`이거나 `boolean`을 든 유니온인 것, 그리고 기본값이 `true`·`false`인 것이다.
  이름 붙인 옵션 객체(`{ force }: { readonly force: boolean }`)는 파이썬의 키워드 전용 매개변수에 해당해 지나간다.
- 함수 타입과 메서드 시그니처는 보지 않는다. 디자인 시스템의 `Switch`가 `onChange?: (checked: boolean) => void`처럼
  값을 넘기는 콜백을 두고, ruff FBT001 도 `Callable[[bool], None]`은 보지 않는다. 본문 없는 선언과 오버로드, 생성자의
  매개변수 속성, 리터럴 타입 `true`·`false`도 이 코드베이스에 쓰는 자리가 없어 보지 않는다고 설정 주석에 적었다.
- selector 는 다섯 갈래다. 매개변수 자리(`:function > .params`와 기본값이 붙은 `AssignmentPattern`의 `.left`) 둘 ×
  타입(`TSBooleanKeyword`와 `TSUnionType > TSBooleanKeyword`) 둘, 그리고 주석 없는 기본값 리터럴
  (`AssignmentPattern.params:not([left.typeAnnotation]) > Literal.right[value=type(boolean)]`)이다. 주석과 리터럴
  기본값이 함께 있는 `b: boolean = false`는 `:not(...)`이 없으면 두 번 보고됐다. 갈래마다 어느 모양을 잡는지는 세션
  스크래치패드의 커밋하지 않은 스크립트(`selector_probe.mjs`, web 의 eslint 와 typescript-eslint 파서로 `Linter.verify`를
  부른다)로 스물다섯 모양을 넣어 손으로 봤다. 문자열 기본값 `"true"`, 옵션 객체, 함수 타입, 추론된 콜백, 나머지 매개변수,
  수 기본값, 매개변수 속성, `declare`, 오버로드, 제네릭 `T extends boolean`, 리터럴 타입 `true`는 아무 갈래에도 걸리지
  않았다.

## 검사

- 사례를 먼저 썼다. 걸리는 사례 여덟(주석 `boolean`, `?: boolean`, `boolean | undefined`, 주석 없는 `= false`, 주석과
  상수 기본값, 주석과 `= false`, 화살표 함수, 객체의 메서드)은 규칙 ID `no-restricted-syntax`의 메시지가 "불리언 매개변수"를
  든 한 개인지를 본다. 같은 규칙 ID 를 enum·`use server` 금지가 나눠 써서 메시지의 표지까지 보고, 한 개인지로 두 번 보고를
  막는다. 지나는 사례 셋은 옵션 객체, 함수 타입과 추론된 콜백, 불리언이 아닌 기본값(문자열 `"true"`, 수)이다.
- 규칙을 켜기 전 `pnpm -C web exec vitest run eslint.config.test.ts -t "불리언|지나보내는"`에서 걸리는 사례 여덟이
  `expected [] to deeply equal [ StringContaining "불리언 매개변수" ]`로 빨갰고 지나는 사례는 초록이었다(손으로 봤다).
  켠 뒤 같은 명령에 `빨갛게 보는 것`을 더해 69개가 초록이었다(손으로 봤다).

## 켜기 전 위반

규칙을 켠 채 `pnpm -C web lint`를 쳐 열두 곳(파일 열)이 나왔다(손으로 봤다).

| 파일 | 자리 | 고치는 길 |
|---|---|---|
| `web/apps/admin/api/plugins/index.ts` | `setPluginEnabled(…, enabled: boolean)` | 옵션 객체 `{ enabled }` |
| `web/apps/admin/hooks/queries/plugins/index.ts` | `usePlugins(active = true)`, `useSetPluginEnabled`의 콜백 `(kind, name, enabled: boolean)` | 옵션 객체. 콜백의 타입(`PluginList.tsx`의 `SetEnabled`)도 함께 |
| `web/apps/admin/components/organisms/RunDecision.tsx` | `decisionPlaceStands(trace, channelTokenEntered: boolean)`, `noticeOf(failure, channelTokenEntered: boolean)` | 옵션 객체 |
| `web/apps/admin/components/pages/HomePage.test.tsx` | 시험 도우미 `rowsWith(name, enabled: boolean)` | 옵션 객체 |
| `web/apps/widget/e2e/site.ts` | `page(…, intruders: boolean, …)` | 옵션 객체를 끝으로 |
| `web/packages/ui/src/styles/DesignTokens.stories.tsx` | `primaryBranchFailures(at, key, dark: boolean, value)` | 모드 유니온(`Mode`) |
| `web/tools/sync-design-system/claim.test.ts` | 시험 도우미 `importing(own: boolean, …)` | 옵션 객체 |
| `web/tools/sync-design-system/decide.test.ts` | 시험 도우미 `importing(owner, further: boolean)` | 옵션 객체 |
| `web/tools/sync-design-system/decide.ts` | `foundChoices(caller, inherit: boolean)` | 옵션 객체 |
| `web/tools/sync-design-system/tokens-json.ts` | `length(value, radius = false)` | `radiusLength`로 쪼갬 |

판정에서 뺄 자리는 없다고 정했다. 파이썬 쪽 대기열 285 가 위반 55곳을 모두 고치고 뺀 자리가 없었던 것과 같은 길이다.
`web/tools/sync-design-system/`의 넷과 `api/plugins/index.ts`를 고쳤다. 나머지는 아래 확인 때문에 멈췄다.

## 웹 편집 확인

`api/plugins/index.ts`를 고치자 계기 훅(`tools/hook_web_edit_check.py`)이 화면 코드를 처음 고쳤다고 알려
`/sync-design-system 확인`을 돌았다. `check judge`가 `importing`을 냈다. 다른 세션이 웹 편집을 들이는 중이다.

- 브랜치 `feature/11-web-edit-teal-accent-600`, 티켓 `.scratch/design-reverse-sync/issues/11-web-edit-teal-accent-600.md`,
  claim 시각 2026-10-27T19:24:40Z, 들이는 파일 `project/tokens.json`, 그 뒤에 더 고친 것 없음.
- `gh pr list --head feature/11-web-edit-teal-accent-600 --state all`이 빈 목록이었다. 결정표(`decide --caller screen`)는
  "그 들이기를 기다린다"와 "그 claim을 지운다"를 물었다.
- `git worktree list`에서 그 워크트리는 main 의 끝(5ccb51a0)에 있고 잠기지 않았으며, 그 브랜치에 main 밖의 커밋은 없고
  원격 브랜치도 없었다(`git ls-remote --heads origin feature/11-web-edit-teal-accent-600`이 빈 출력. 손으로 봤다).

> 사용자: "그 들이기를 기다린다" — 그 브랜치의 들이기가 PR 을 열 때까지 지금 일을 멈춘다

그래서 화면 코드(`web/apps/*`, `web/packages/ui`)를 더 고치지 않고 멈췄다. 이 세션이 고치는 화면 코드는 매개변수 모양만
바꾸고 디자인 토큰과 컴포넌트의 생김새에는 닿지 않는다. 커밋은 아직 없다. 규칙을 켠 채 위반이 남아 pre-commit 의 린트가
빨갛기 때문이다.

## 두 번째 확인

> 사용자: "feature/11-web-edit-teal-accent-600 이 PR 을 열었다. 웹 편집 확인을 다시 돌리고 이어 가라"

새 폴더로 확인을 처음부터 다시 돌았다. `gh pr list --head feature/11-web-edit-teal-accent-600 --state all`이 PR #413 을
MERGED 로 냈고(병합 커밋 `ad8a9c37`), 결정표는 묻지 않고 `continue`를 냈다. 이 브랜치의 HEAD 는 그 커밋을 품지 않아
(`git merge-base --is-ancestor`가 1) `git merge --ff-only origin/main`으로 main 을 합쳤다. 커밋 전의 변경은 그 병합이
바꾼 파일과 겹치지 않았다. 앱의 `sync_with_base_branch`는 커밋하지 않은 변경이 있으면 거부해 쓰지 않았다.

그 뒤 위 표의 남은 일곱 곳(관리 화면의 파일 셋에 다섯 곳, 위젯 e2e 의 사이트 한 곳, 디자인 토큰 판정 스토리 한 곳)을
고쳤다. 관리 화면의 켜고 끄기는
요청 함수, 훅의 콜백, organisms 의 처리기 타입(`SetEnabled`)이 같은 옵션 객체 `{ enabled }`를 한 줄로 넘긴다. 위젯 e2e 의
`page`는 옵션 객체를 끝 인자로 옮겼다. `primaryBranchFailures`는 `dark: boolean` 대신 이미 import 된 `Mode`를 받는다.
고친 화면 코드는 매개변수 모양만 바꾸고 디자인 토큰과 생김새에는 닿지 않는다.

- `pnpm -C web lint`와 `pnpm -C web typecheck`가 종료 0 이었다(손으로 봤다).
- `pnpm -C web exec vitest run apps/admin tools/sync-design-system eslint.config.test.ts`에서 25개 파일, 696개 시험이
  초록이었다(손으로 봤다).
- `pnpm -C web exec vitest run --project storybook packages/ui/src/styles/DesignTokens.stories.tsx`에서 Matrix 를 포함한
  8개가 초록이었다(손으로 봤다).

`CODING_STANDARDS.md`의 불리언 플래그 줄은 TypeScript 판정자가 잡는 자리(함수 정의의 매개변수 주석과 기본값)와 보지 못하는
자리(함수 타입과 메서드 시그니처, 옵션 객체로 옮겨 지나간 플래그, 인터페이스의 불리언 칸)를 적고 대기열 483 을 달았다.
대기열 483 은 이 티켓으로 닫았다.

## 셀프 리뷰

`/code-review origin/main`(base `ad8a9c37`, 커밋 0, 바뀐 파일 열여섯, 미추적 둘). 두 축을 함께 띄웠다.

### 표준 축

Critical·Major 는 없었다. 판정자 사례는 규칙 ID 로 거르고 메시지 표지를 한 개로 보며, 지나는 사례는 메시지가 빈 배열이라
같은 규칙 ID 의 다른 금지 구문이 섞여 지나갈 수 없다고 봤다. 실제 ESLint 와 `ruff --select FBT001`로 설정 주석과 일지의
주장(한 번만 보고, 보지 않는 자리, `Callable[[bool], None]`)을 대 봤고 맞았다.

- Minor 1: 반영 전의 `CODING_STANDARDS.md` 줄은 서버에 보낼 켜짐처럼 값 자체인 불리언을 플래그가 아니라고 적었는데(반영에서
  지웠다), 판정자는 함수 정의에서 값 불리언도 막는다(이 diff 가 `setPluginEnabled`를 옵션 객체로 고친 것이 그 예다).
  **고친다.**
- Minor 3: 값을 넘기는 콜백의 구현(`(x: boolean) => x`)도 걸린다. `SetEnabled`와 `useSetPluginEnabled`의 콜백이 옵션 객체가
  된 까닭이다. Minor 1 과 같은 뿌리라 함께 **고친다.** 판정자는 뜻(플래그인지 값인지)이 아니라 자리(함수 정의인지 함수
  타입인지)로 가른다는 일반 조항으로 적는다.
- Minor 2: 같은 줄이 옵션 객체로 옮겨 지나간 플래그가 갈래를 고르면 쪼갠다고 하는데, `decide.ts`의 `foundChoices(caller,
  { inherit })`와 위젯 e2e 의 `page(…, { intruders })`는 옵션 객체로 옮기기만 했다. **고친다.** `foundChoices`는 갈래마다의
  선택지를 데이터로 받고, `page`는 부르는 쪽이 끼어드는 프레임의 마크업을 넘긴다. 시험 도우미의 `own`·`further`·`enabled`와
  `setPluginEnabled`의 `enabled`, `decisionPlaceStands`의 `channelTokenEntered`는 갈래가 아니라 값을 싣는 칸이라 둔다.
- Nit: 설정 주석이 적지 않은 경계가 있다. 중첩 유니온 `string | (boolean | number)`, `boolean[]`·`Array<boolean>`·
  `Promise<boolean>`, 리터럴이 아닌 기본값(`!0`)은 지나가고, setter 와 생성자의 일반 매개변수는 걸린다. 주석이 말한 보지 않는
  자리(생성자의 매개변수 속성, 오버로드, `declare`, 리터럴 타입)는 사실이지만 시험 사례가 없다. **설정 주석에 보태고 지나는
  사례 하나로 고정한다.**
- Nit: `tokens-json.ts`의 `(raw) => radiusLength(raw)`는 옆 줄과 같은 꼴이라 둔다.

### 명세 축

Critical·Major 는 없었다. 고친 위반이 동작을 바꾸지 않았는지(`radiusLength`, `primaryBranchFailures`의 모드, `usePlugins()`의
기본값, `page`의 인자 순서)를 코드로 대 봤고, base 판의 열 파일을 지금 설정으로 린트해 열두 곳을 다시 셌다.

- Minor 1: 티켓이 든 걸리는 사례 "기본값 `true`·`false`" 가운데 주석 없는 `= true`가 사례에 없다. **사례를 더한다.**
- Minor 2: ruff FBT001·FBT002 에 맞춘다는 티켓과 어긋나는 자리가 있다. 주석이 boolean 이 아닌 매개변수의 리터럴 기본값
  (`x: Flag = false`의 별칭, `x: unknown = true`)이 `:not([left.typeAnnotation])` 때문에 지나가는데 ruff FBT002 는 둘 다
  잡는다. 중첩 유니온은 지나가는데 ruff 는 잡는다. 세터는 걸리는데 ruff 는 `@x.setter`를 보지 않는다. 생성자의 매개변수
  속성은 지나간다. **고친다.** 리터럴 기본값은 주석과 무관하게 잡고 주석이 boolean 인 자리는 기본값이 리터럴이 아닐 때만
  잡아 한 번만 보고한다. 세터는 뺀다. 중첩 유니온은 깊이를 정할 수 없고 유니온 속 함수 타입의 콜백까지 걸게 되어 보지 않는
  자리로 적는다. 매개변수 속성은 `web/tsconfig.base.json`의 `erasableSyntaxOnly`가 타입 검사에서 막는다고 적는다.
- Minor 3: 표준 축 Minor 2 와 같은 지적에 `noticeOf`의 `channelTokenEntered`와 `decide.test.ts` 도우미의 `further`를 더했다.
  `foundChoices`와 `page`는 위대로 쪼갠다. `channelTokenEntered`는 스토어의 상태를 그대로 넘기는 값이고 부르는 쪽이 고르는
  모드가 아니다. `further`는 결정표 시험이 `[false, true]`로 도는 표의 한 축이라 시험 자료의 값이다. 둘은 둔다.
- Minor 4: 요구는 그 줄이 규칙과 규칙이 보지 못하는 자리를 가리키는 것인데, 옛 줄의 판단을 바꿨다. 옵션 객체로 옮긴
  플래그를 "갈래를 고르면" 쪼갠다고 좁혔고 "값 자체인 불리언은 플래그가 아니다"를 새로 더했다. 승인 표지는 옛것 그대로다.
  **되돌린다.** 판단 문장은 옛 뜻 그대로 두고 TypeScript 의 짝(옵션 객체, 인터페이스, 문자열 유니온)만 붙인다. 판정자가 값을
  싣는 불리언도 함수 정의에서 막는다는 것은 규칙이 잡는 자리의 사실로 적는다. 이것으로 표준 축 Minor 1·3 의 모순 문장도
  사라진다.

### 반영

- selector: 함수를 `:function:not([kind="set"] > *)`로 좁혀 세터를 뺐다. 주석 갈래는 기본값 없는 매개변수와, 기본값이
  `true`·`false` 리터럴이 아닌(`:not([right.value=type(boolean)])`) 매개변수에만 건다. 리터럴 기본값 갈래는 주석과 무관하게
  건다. 세션 스크래치패드의 커밋하지 않은 스크립트(`selector_probe2.mjs`)로 스물여덟 모양을 넣어, 걸리는 모양은 모두 한
  번씩 보고되고 별칭 주석의 `= false`와 `unknown = true`가 이제 걸리며 세터(클래스, 객체)와 중첩 유니온·배열·`!0`·`declare`
  ·리터럴 타입은 지나가는 것을 손으로 봤다. 세터 안의 화살표 함수는 걸렸다. `:has(> …)`로 쓴 판과 결과가 같아 속성
  선택자 판을 골랐다. 메시지는 "갈래를 고르는 플래그면 함수를 둘로 쪼개고, 값이면 이름 붙인 옵션 객체로 받는다"로 바꿨다.
- 사례: 걸리는 쪽에 주석 없는 `= true`와 별칭 주석의 `= false`를, 지나는 쪽에 세터와 설정 주석이 보지 않는다고 적은 자리
  (본문 없는 선언, 메서드 시그니처, 리터럴 타입 `true`, 유니온 속 유니온, 배열과 제네릭 인자, `!0`)를 더했다. 걸리는 사례
  열, 지나는 사례 다섯이다. 옛 selector 에서 별칭 주석은 지나가고 세터는 걸린다는 것은 명세 축이 손으로 봤다.
- 쪼갬: `decide.ts`는 `ImportWay`(선택지 "먼저 들인다"와 덮어쓰기가 할 일)의 상수 `FRESH_IMPORT`·`INHERITED_IMPORT`를
  `foundChoices`에 넘긴다. 위젯 e2e 의 `page`는 끼어드는 프레임의 마크업(`intruderFrames`)이나 빈 글을 받고, 질의를
  읽는 `startSite`가 고른다.
- 표준 줄: 판단 문장을 옛 뜻(옵션 객체로 옮겨 지나간 플래그는 쪼갠다)으로 되돌리고 "값 자체인 불리언은 플래그가 아니다"를
  지웠다.
- 대기열 483 닫힘 표지: 사례 수(열·다섯), 세터 제외, 셀프 리뷰로 다시 쪼갠 둘을 고쳤다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장의 원문):

- `CODING_STANDARDS.md`: "TypeScript는 판정자(`web/eslint.config.mjs`의 `no-restricted-syntax`)가 함수 정의(세터는 빼고)의
  매개변수 가운데 주석이 `boolean`이거나 `boolean`을 바로 든 유니온인 것과 기본값이 `true`·`false` 리터럴인 것만 막는다.
  함수 타입과 메서드 시그니처의 매개변수, 유니온 속 유니온의 `boolean`, 호출에 넘긴 `true`/`false` 리터럴은 보지
  않고(보지 않는 자리의 목록은 그 설정의 주석), 플래그와 값을 가르지 못해 값을 싣는 불리언도 함수 정의의 매개변수면 막는다."
- `web/eslint.config.mjs` 설정 주석: "잡는 자리는 파이썬의 ruff FBT001·FBT002 에 맞춘다", "세터는 ruff 처럼 뺀다", "주석과
  리터럴 기본값이 함께 있으면 기본값 쪽에서 한 번만 보고한다", "보지 않는 자리는 … 본문 없는 선언과 오버로드, 리터럴 타입
  true·false, 유니온 속 유니온의 boolean, 배열과 제네릭 인자의 boolean, 리터럴이 아닌 기본값(`!0`), 호출에 넘긴
  true·false(ruff FBT003 의 자리)다", "생성자의 매개변수 속성은 … tsconfig.base.json 의 `erasableSyntaxOnly` 가 타입
  검사에서 막는다".
- 대기열 483 닫힘 표지: "걸리는 사례 열·지나는 사례 다섯", "갈래를 고르던 둘(`foundChoices`, 위젯 e2e 의 `page`)은 셀프
  리뷰를 받아 옵션 객체에서 다시 쪼갰다".

남긴 것: `noticeOf`의 `channelTokenEntered`와 `decide.test.ts` 도우미의 `further`(위 명세 축 Minor 3 의 까닭),
`tokens-json.ts`의 화살표 래퍼(표준 축 Nit).

다시 돌린 것: Prettier 뒤 `pnpm -C web lint`와 `pnpm -C web typecheck`가 종료 0 이었다(새 selector 가 기존 코드에서 새
위반을 찾지 않았다). `pnpm -C web exec vitest run eslint.config.test.ts tools/sync-design-system`에서 15개 파일, 524개
시험이 초록이었고, 불리언 사례만 이름과 함께 돌려 걸리는 열과 새 지나는 둘이 기대대로인 것을 봤다(손으로 봤다). 셀프 리뷰
전의 `uv run python tools/run_checks.py`는 모든 검사가 Passed 였다(pytest 1584초, web-verify 1001초. 다른 세션의 부하가
컸다). 반영 뒤의 손으로 치는 다섯은 커밋의 pre-commit 으로 갈음한다.

위젯 e2e(`pnpm -C web/apps/widget exec playwright test`, 반영 뒤): 첫 판은 전역 준비에서 `serve 가 서지 않았다`로 끝났다.
serve 가 60초(`STARTUP_MS`) 동안 아무것도 찍지 않았고, 사이트 서버(`startSite`)를 띄우기 전이다. 둘째 판은 15개 가운데
14개가 초록이었고 "첫 도구 줄을 결말 전에 보이고"(`widget.e2e.ts:33`)가 첫 도구 줄을 5초 안에 보지 못해 빨갰다. 그때의
화면 기록에서 사이트 페이지와 위젯이 섰고 실행이 시작되어 "부른 도구" 아래 진행 표시가 돌았으므로 토큰은 전달됐다. 같은
`page()`를 지나는 끼어드는 프레임 시험은 초록이었다. 그 시험 하나만 다시 돌리자 6.0초로 초록이었다(손으로 봤다). 다른
세션의 부하로 도구 호출이 늦은 것으로 보고 이 변경의 실패로 세지 않았다. `-m llm_widget`은 치지 않았다. 바꾼 것은 위젯 e2e
의 사이트 하네스이고 위젯·api-client·서버의 최종 사용자 경로가 아니며, 같은 `page()`를 위 e2e 가 지났다. 사진 비교
(`visual`, `visual:widget`)는 이 PC 의 Docker 데몬이 API 요청에 Internal Server Error 를 내 치지 못했고 CI 의 `visual` 잡에
맡긴다.

첫 커밋은 pre-commit 의 변이 표 검사(`tools/mutate.py --staged`)에 막혔다. 다른 기능의 변이 표 둘이 이 변경이 바꾼 원문을
글자 그대로 들고 있었다. `.scratch/admin-style/probes/organisms_props_mutations.toml`의 1·2번은 `RunPage.tsx`의
`usePlugins(…)` 줄을, `.scratch/design-reverse-sync/probes/claim_mutations.toml`의 21·24·26번은 `decide.ts`의 덮어쓰기 갈래,
`foundChoices(caller, false)`, 올리기 갈래의 줄을 들었다. 원문을 새 줄로 맞추고 바꿀 글을 같은 뜻의 새 꼴로 고쳤다(2번은
`usePlugins({ active: false })`, 21번은 `INHERITED_IMPORT`의 `overwrite: "overwrite"`). `tools/mutate.py`로 그 다섯을 돌려
모두 기대대로였다(1번 초록, 나머지 빨강. 손으로 봤다). 인용 대조 경고 둘(지운 옛 문구를 따옴표로 든 이 일지의 두 줄)은
따옴표를 떼었다. 커밋이 막혀 인계 계기의 `커밋 뒤` 경계에 온 것이 아니라 넘기지 않았다(next-session "인계할 때" 1).

## 인계

다시 친 커밋(3476d25d)이 pre-commit 을 지나(`Skipped`는 스테이지된 `.py`가 없는 ruff 둘, 카나리아 명세, 헌법 판) 인계
계기가 `커밋 뒤` 경계에서 왔다. 세션 컨텍스트가 인계 문턱(20만 토큰)을 넘었다. 인계하지 않는 때 다섯에 들지 않아(커밋이 성공했다, 요청 범위는 PR 과
병합까지다, 지시문의 이어받을 상태는 `없음`이었다, `인계 못함` 줄이 없다, `get_session`의 `self`에 `parentSessionId`가 없다)
넘긴다. 이 세션의 지금 제목은 `chore/022-eslint-boolean-params`이고 넘기기 전에 `(인계함)`을 붙인다. 이 절은 커밋하지
않았다. 새 세션이 이어 쓰고 커밋한다.

남은 단계: origin/main 을 합친다(PR #415 가 `web/apps/admin/components/pages/HomePage.test.tsx`와 `.scratch/retro-queue.md`를
함께 고쳤고 관리 화면 코드를 새로 들였다). 합친 뒤 `pnpm -C web lint`로 새로 들어온 코드가 새 규칙에 걸리는지 보고, 걸리면
위 "켜기 전 위반"과 같은 길로 고친다. 그 뒤 PR 직전 리뷰(밀 주장은 위 "반영" 절), PR, 봇 회차와 병합이다. PR 본문에는
packages/ui 의 스토리 파일을 고쳐 다음 디자인 시스템 올리기가 빌드를 요구한다는 것과, 이 PC 의 Docker 데몬이 응답하지 않아
사진 비교를 CI 의 `visual` 잡에 맡긴다는 것을 적는다.

인계 지시문:

다음 작업: .scratch/harness/issues/022-eslint-boolean-params.md. 대기열 483: web/eslint.config.mjs 가 타입이 boolean 인 함수 매개변수를 잡고 CODING_STANDARDS.md 의 그 줄이 이 규칙을 가리킨다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 483을 티켓 .scratch/harness/issues/022-eslint-boolean-params.md로 쓰고 한다
브랜치: chore/022-eslint-boolean-params
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/agents/issue-tracker.md
이어받을 상태: 인계: 커밋 뒤. 구현, 셀프 리뷰 반영, 위젯 e2e 까지 커밋했고 PR 은 없다. 남은 단계는 origin/main 합치기와 그 뒤의 web 린트, PR 직전 리뷰, PR, 봇 회차와 병합이고 할 일과 PR 본문에 적을 것은 일지의 "인계" 절이다. 일지의 "인계" 절은 커밋하지 않았다. 일지 docs/journal/2026-10-29-04-eslint-boolean-params.md
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지

open-session을 부른다 2026-10-28T09:44:15Z

## 이어받은 세션

> 사용자: "대기열 483을 티켓 .scratch/harness/issues/022-eslint-boolean-params.md로 쓰고 한다"

위 인계 지시문으로 연 새 세션이다. 제목을 `chore/022-eslint-boolean-params`로 바꾸고, 주 체크아웃에서 `tidy-checkouts`를 돈 뒤
`EnterWorktree(path)`로 이 워크트리에 들어왔다. `tidy-checkouts`는 루트를 `ad8a9c37`에서 `06a8f85b`(origin/main)로 당겼고,
병합된 워크트리 셋(`bug-perf-review-batch`, `measure-word-hook`, `design-card-build`)과 브랜치 하나
(`feature/03-admin-adopt-design-system`)를 지웠다. 휴지통에는 esbuild.exe 를 다른 프로세스가 올려 둔 `node_modules` 넷이 남았다(`tools/tidy_checkouts.py`의 출력을 손으로
봤다).

origin/main(PR #415)을 `git merge`로 합쳤다. `HomePage.test.tsx`와 `.scratch/retro-queue.md`는 자동으로 합쳐졌다. 합친 뒤
`pnpm -C web lint`와 `pnpm -C web typecheck`가 종료 0 이었고, PR #415 가 들인 관리 화면 파일(`.storybook/`, `EntryFrame.tsx`,
`AdminTokenForm.tsx`, `visual/`, `e2e/fonts.e2e.ts`)을 `eslint`에 직접 넘겨도 무시 경고 없이 종료 0 이었다. 새 규칙에 걸리는
새 코드는 없었다. `pnpm -C web exec vitest run apps/admin/components/pages/HomePage.test.tsx eslint.config.test.ts`에서
2개 파일, 131개 시험이 초록이었다(모두 손으로 봤다).

PR 직전 리뷰: `coderabbit auth status`가 `Seat: not assigned`라 CLI 대신 대체 둘(`/security-review`, `bug-perf-review`
서브에이전트)을 나란히 돌렸다.

- `/security-review`(origin/main 을 합친 뒤): 식별 서브태스크가 신뢰도 8 이상의 High·Medium 을 하나도 내지 않아 거를 후보가
  없었다. 보고 0건. 서브태스크는 코드를 읽어 런타임 코드 일곱 파일이 매개변수 모양만 바꿨다고 봤다. `setPluginEnabled`의 PUT
  본문은 그대로 `{ enabled }`이고, 관리 토큰이 없으면 읽지 않는 `usePlugins`의 조건과 `useSetPluginEnabled`의 이른 반환,
  `tokens-json.ts`의 길이 검증(`LENGTH` 정규식, 수의 유한성)이 그대로이며, `eslint.config.mjs`는 `ignores`를 바꾸지 않았다.
- `bug-perf-review`(기준 06a8f85b, 스무 파일): 열두 건 가운데 유효 둘(둘 다 Nit), 오탐 열. Critical·Major·Minor 는 없었다.
  서브에이전트는 변이 표 여덟을 `tools/mutate.py --check`로, 바뀐 변이 다섯을 `--since origin/main`으로 돌려 기대대로인 것을
  봤고, `eslint --stdin`으로 스물다섯 모양을 실제 설정에 넣었고, `ruff --select FBT001,FBT002`로 세터를 ruff 가 보지 않는
  것을 봤다(서브에이전트가 손으로 봤다). 오탐 열은 매개변수 모양을 바꾼 자리(`usePlugins()`의 기본값, `{ enabled }`,
  `decisionPlaceStands`·`noticeOf`, `FRESH_IMPORT`·`INHERITED_IMPORT`, `radiusLength`, 위젯 e2e `page`, `Mode`)의 동작이 같고
  새 selector 가 꺼지는 파일이 없다는 것이다(코드를 읽었다).
  - Nit 1: `.scratch/web-admin/probes/plugin_toggle_mutations.mjs:222`의 변이 원문이 옛 인자 `enabled`를 든다. 지금 훅은
    `change`를 넘긴다(Grep 으로 `hooks/queries/plugins/index.ts:91`을 손으로 봤다). **둔다.** 이 프로브는 티켓 06(2026-09-30)의
    옛 스크립트이고 159·166행이 이 PR 전부터 `setEnabled(`를 들어 지금의 `onSetEnabled(`와 맞지 않는다. 222행만 고쳐도 돌지
    않는다. 대기열 73 이 옛 프로브의 원문은 코드가 바뀌면 썩어도 된다고 정했고, pre-commit 의 `mutate.py --staged`는
    `*_mutations.toml`만 본다. 고치는 값은 한 줄이다.
  - Nit 2: 설정 주석의 보지 않는 자리 목록이 별칭 주석(기본값 없는 `Flag`), 교차 타입, 제네릭 제약(`T extends boolean`)을
    말하지 않는다. `true | false`와 `Readonly<boolean>`은 목록의 리터럴 타입과 제네릭 인자에 든다. **고쳤다.** 설정 주석에 셋을
    더하고 `unseen-boolean-param.ts` 지나는 사례에 세 모양을 더했다. `pnpm -C web exec vitest run eslint.config.test.ts`에서
    90개가 초록이었다(손으로 봤다). `CODING_STANDARDS.md`의 줄은 목록을 그 설정의 주석으로 가리켜 고치지 않았다.
  - 서브에이전트가 덧붙인 것: 설정 주석의 "오버로드"는 시험 사례가 없다. 두었다. 불리언과 다른 타입의 오버로드는
    `@typescript-eslint/unified-signatures`가 하나로 합치라고 할 수 있어 지나는 사례로 고정하려면 그 규칙까지 가려야 한다는
    어림이고, 돌려 보지 않았다.

Nit 2 를 고친 커밋(8bb8b0bb)의 pre-commit 이 모두 지났다(`Skipped`는 스테이지된 `.py`가 없는 ruff 둘, 카나리아 명세, 헌법 판.
pytest 1220초, web-verify 680초. 커밋 로그를 손으로 봤다). origin/main 을 합친 트리에서 손으로 치는 다섯이 이 pre-commit 으로
갈음된다. 푸시하고 PR #420 을 열었다.

## 인계 (PR 연 뒤)

PR #420 을 연 직후 인계 계기가 `PR 연 뒤` 경계에서 왔다. 세션 컨텍스트가 인계 문턱(20만 토큰)을 넘었다. 이 세션의 지시문의
이어받을 상태는 `인계: 커밋 뒤`라 같은 경계가 아니고, 커밋 뒤 경계에서는 그 까닭으로 넘기지 않았다. 나머지 넷(명령 성공, 요청
범위는 PR 과 병합까지, `인계 못함` 줄 없음, `get_session`의 `self`에 `parentSessionId` 없음)에도 들지 않아 넘긴다. 이 세션의
지금 제목은 `chore/022-eslint-boolean-params`이고 넘기기 전에 `(인계함)`을 붙인다. 이 절은 커밋하지 않았다. 새 세션이 이어
쓰고 커밋한다.

남은 단계: 첫 `@coderabbitai review` 코멘트, 봇 회차(next-session 순서 1의 2), 일지 마무리, 워크트리의 병합 길. PR 은 앱이
이 세션에 묶었고(`get_status`의 `bound: true`) 넘긴 뒤의 알림은 이 세션을 깨운다. 형제 일지 27(`023-widget-char-count-flake`)과
28(PR #417, `025-next-session-prune-check`)이 먼저 병합되면 이 일지가 이름순으로 앞서므로 `tools/sibling_overlap.py`의 출력대로
옮긴다.

인계 지시문:

다음 작업: .scratch/harness/issues/022-eslint-boolean-params.md. 대기열 483: web/eslint.config.mjs 가 타입이 boolean 인 함수 매개변수를 잡고 CODING_STANDARDS.md 의 그 줄이 이 규칙을 가리킨다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 483을 티켓 .scratch/harness/issues/022-eslint-boolean-params.md로 쓰고 한다
브랜치: chore/022-eslint-boolean-params
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/agents/issue-tracker.md
이어받을 상태: 인계: PR 연 뒤. PR #420 을 열었고 첫 `@coderabbitai review` 코멘트와 봇 회차(next-session 순서 1의 2)부터 한다. PR 직전 리뷰(대체 둘)의 결과와 남긴 것은 PR 본문 체크리스트와 일지에 있다. 일지의 "인계 (PR 연 뒤)" 절은 커밋하지 않았다. 일지 docs/journal/2026-10-29-04-eslint-boolean-params.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지

잠금 풀기는 `is not locked`로 넘어갔다.

open-session을 부른다 2026-10-28T10:56:40Z

## 이어받은 세션 (2)

> 사용자: "대기열 483을 티켓 .scratch/harness/issues/022-eslint-boolean-params.md로 쓰고 한다"

위 "인계 (PR 연 뒤)" 지시문으로 연 새 세션이다. 제목을 `chore/022-eslint-boolean-params`로 바꾸고 `EnterWorktree(path)`로 이
워크트리에 들어왔다(잠금 거부 없이 들어왔다). `gh pr view 420`의 `headRefOid`와 `git rev-parse HEAD`가 둘 다 `8bb8b0bb`라
푸시할 커밋은 없었다. 앱의 `get_status`는 이 세션에 묶인 PR 이 없다고 했고, 묶지 않았다(next-session "인계할 때" 6).

- 11:03:30Z 에 `@coderabbitai review` 코멘트를 남겼다. CodeRabbit 은 "Review triggered" 답글을 달았으나 리뷰 본문은 아직 없고
  (`gh pr view 420 --json comments,reviews`로 손으로 봤다. `reviews`는 빈 배열이었다),
  그 직후 `gh pr checks 420`의 CodeRabbit 줄은 `skipping`이었다. 나머지 여덟(verify, claude-review, e2e, e2e-widget, python,
  ticket, visual, web)은 `8bb8b0bb`에서 모두 pass 였다(손으로 봤다).
- claude-review 의 첫 회차(10:54:54Z, `8bb8b0bb`. 같은 명령으로 코멘트 본문을 손으로 봤다): Critical·Major·Minor 없음, Nit 하나. `tokens-json.ts`의
  `readFamily(…, (raw) => radiusLength(raw))`는 `radiusLength`를 그대로 넘겨도 같다는 지적이다. 셀프 리뷰 표준 축 Nit 에서
  "옆 줄과 같은 꼴이라 둔다"고 한 자리와 같다. 첫 회차라 지적마다 판단해야 하는데 아직 판단하지 않았고 PR 코멘트도 남기지 않았다.
- `uv run python tools/wait_ci.py 420`을 백그라운드로 띄웠다가 아래 요청으로 TaskStop 했다.

다른 세션(`주간한도 95% 초과 시 세션 전환`)이 계정 인계를 위해 마무리를 요청했다.

> 다른 세션: "주간 한도가 90%에 도달해 다른 계정으로 작업을 넘깁니다. … 새로 푸시하거나 병합하지 않습니다. PR 420은 열어 둔 채로 둡니다."

그래서 대기를 멈추고, 푸시·병합·새 세션 열기를 하지 않고 이 절과 아래 지시문을 남긴 뒤 멈춘다. 계기 인계(`hook_handoff`)가
아니라 결정표의 "작업을 마치지 못한 채 끊는다" 줄이라 "이어받을 상태"를 `인계:`로 시작하지 않았다. 이 절은 커밋하지 않았다.

남은 단계: `uv run python tools/wait_ci.py 420`을 다시 띄워 CodeRabbit 의 첫 리뷰를 기다리고(리뷰가 오지 않으면 요약 코멘트의
`Reviewing files … between` 범위를 본다), claude-review 첫 회차의 Nit 과 CodeRabbit 의 지적을 판단해 반영하고 보류한 것은 PR
코멘트에 이유를 남긴다. 일지(이 파일의 인계 절 셋 포함)를 마무리해 마지막 봇 회차의 커밋에 실어 푸시한다. 병합 전에
`uv run python tools/sibling_overlap.py`로 일지 번호를 보고(형제 일지 27·28 이 먼저 병합되면 옮긴다), `headRefOid` 대조 뒤
next-session "워크트리에서 병합할 때"의 길로 병합한다.

인계 지시문:

다음 작업: .scratch/harness/issues/022-eslint-boolean-params.md. 대기열 483: web/eslint.config.mjs 가 타입이 boolean 인 함수 매개변수를 잡고 CODING_STANDARDS.md 의 그 줄이 이 규칙을 가리킨다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 483을 티켓 .scratch/harness/issues/022-eslint-boolean-params.md로 쓰고 한다
브랜치: chore/022-eslint-boolean-params
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/agents/issue-tracker.md
이어받을 상태: 주간 한도 90% 도달로 끊었다(계기 인계가 아니다). PR #420 은 열려 있고 마지막 HEAD 는 8bb8b0bb 로 로컬과 같다. `@coderabbitai review` 코멘트는 남겼고 CodeRabbit 의 첫 리뷰는 아직 없다. claude-review 첫 회차의 Nit 하나(tokens-json.ts 의 화살표 래퍼)는 아직 판단하지 않았다. 봇 회차의 대기부터 한다. 커밋하지 않은 변경은 일지의 인계 절 셋뿐이다. 일지 docs/journal/2026-10-29-04-eslint-boolean-params.md
확인할 선행 조건: CodeRabbit 이 11:03:30Z 의 리뷰 요청에 실제로 리뷰를 냈는지 확인하지 못했다(검사 줄은 skipping, 답글은 Review triggered)
이번 요청 범위: PR과 병합까지

## 이어받은 세션 (3)

> 사용자: "대기열 483을 티켓 .scratch/harness/issues/022-eslint-boolean-params.md로 쓰고 한다"

위 "이어받은 세션 (2)"의 지시문으로 연 새 세션이다(2026-10-29). 제목을 `chore/022-eslint-boolean-params`로 바꾸고
`EnterWorktree(path)`로 이 워크트리에 들어왔다. 커밋하지 않은 변경은 이 일지 하나였다(`git status --short`를 손으로 봤다).

- 선행 조건: CodeRabbit 은 리뷰를 냈다. 요약 코멘트가 "No actionable comments were generated in the recent review"와
  PR 의 기준과 `06a8f85b`~`8bb8b0bb` 사이에서 바뀐 파일을 리뷰했다는 범위 줄(`Reviewing files … between`, 파일 20개)을 들었다. `reviews`가
  빈 배열이었던 것은 지적이 없어 리뷰를 남기지 않은 것이다(`gh pr view 420 --json comments`로 요약 코멘트를 손으로 봤다).
  CodeRabbit 첫 회차는 고칠 지적이 없다.
- main 합치기: PR 이 `BEHIND`였다. origin/main 이 네 커밋(#419, #416, #417, #421) 앞섰고 바뀐 파일은 모두 하네스와 문서이며
  `web/`에는 닿지 않았다(`git diff --name-only HEAD...origin/main`을 손으로 봤다). `git merge origin/main`이
  `.scratch/retro-queue.md`를 충돌 없이 합쳤다(출력을 손으로 봤다). #421(harness 027)이 next-session 을 넷으로 나눠, Skill 도구의 옛 사본 대신
  디스크의 `SKILL.md`와 `merge.md`를 Read 로 열어 따랐다.
- 일지 번호: main 에 2026-10-29-02 가 들어와 이 일지(2026-10-28-26)가 이름순으로 앞섰다. `tools/sibling_overlap.py --move`로
  2026-10-29-04 로 옮겼다. 그 명령은 Bash 의 기본 제한 120초를 넘겨 백그라운드로 넘어갔고 종료 0 으로 끝났다. 도구가 쓴 PR
  본문을 지금 본문과 `diff`로 견주어 일지 경로 밖의 차이가 없는 것을 보고 `gh api`로 올렸다(손으로 봤다).
- claude-review 첫 회차의 Nit(`tokens-json.ts`의 화살표 래퍼): **고쳤다.** `readFamily`는 `read(own(item, "value"))`로 인자
  하나만 넘기고, `length`와 `radiusLength`는 둘 다 `(value: unknown) => string | undefined`라 그대로 넘겨도 같다(코드를 읽었다). 셀프 리뷰
  표준 축 Nit 에서 "옆 줄과 같은 꼴이라 둔다"고 한 옆 줄(spacing 의 `(raw) => length(raw)`)도 이 PR 이 `length`의 둘째
  매개변수를 지워 같은 자국이 되었으므로 함께 고쳤다. 같은 함수가 `plainValue`를 그대로 넘기는 자리와 꼴이 같다. 변이 표와
  프로브는 그 두 줄을 원문으로 들지 않는다(`.scratch`의 `*.toml`·`*.mjs`·`*.py`를 Grep 도구로 찾아 손으로 봤다). Prettier 가
  두 호출을 한 줄씩으로 접었다(`git diff`를 손으로 봤다).
  `pnpm -C web exec eslint tools/sync-design-system/tokens-json.ts`가 종료 0 이었고,
  `pnpm -C web exec vitest run tools/sync-design-system`에서 14개 파일, 434개 시험이 초록이었다(손으로 봤다). 위 "반영" 절의
  남긴 것 가운데 화살표 래퍼는 이것으로 남지 않는다.

## 회고

후보 여섯, 승인 0, 기각 여섯, 넘김 0. 이 티켓의 앞 세션들은 회고를 돌지 않아 일지 전체를 원천으로 봤다.

- CodeRabbit 이 리뷰를 냈는지 앞 세션이 확인하지 못하고 선행 조건으로 넘겼다. 기각. `merge.md` 2 의 대기가 이미 그 길(끝났는데
  코멘트가 없으면 요약 코멘트의 `Reviewing files … between` 범위를 본다)을 적는다. 앞 세션은 대기 도중 계정 인계로 끊겨 그
  단계에 닿지 않았고, 이 세션은 그 길로 바로 확인했다.
- 위젯 e2e 가 다른 세션의 부하 아래에서 serve 60초(`STARTUP_MS`)와 첫 도구 줄 5초를 넘겨 빨갰고, 그 시험만 다시 돌리면
  초록이었다(위 "반영" 절). 기각. retro 스킬이 끝이 열린 결함 종류의 예로 드는 대기열 306(부하에서만 빨간 시간 시험)이
  받아들여 닫은 종류의 새 사례라 일지에만 적는다. 306 의 첫 사례는 pre-commit 의 pytest 이고 이 사례는 손으로 친 e2e 라
  자리는 다르다.
- 첫 커밋이 다른 기능의 변이 표가 이 변경이 바꾼 원문을 글자 그대로 들어 `tools/mutate.py --staged`에 막혔다. 기각. 있는
  검사가 그 자리에서 막았다.
- 일지 번호를 네 번 옮겼다(19 → 22 → 26 → 2026-10-29-04). 기각. 형제가 먼저 번호를 쓰거나 병합될 때마다
  `tools/sibling_overlap.py`가 알렸고 `--move`가 옮겼다.
- `tools/sibling_overlap.py --move`가 Bash 의 기본 제한 120초를 넘겼다. 기각. 결과를 잃지 않고 백그라운드 알림으로 이어졌고,
  같은 세션에서 `--move` 없이 친 실행은 제한 안에 끝났다. 실수가 아니라 고칠 층이 서지 않는다.
- 셀프 리뷰가 "둔다"고 판단한 화살표 래퍼를 claude-review 가 다시 짚어 고쳤다. 기각. 셀프 리뷰가 그 자리를 보고 판단을 적었고,
  바뀐 것은 판단이지 놓친 지적이 아니다.

만료: `uv run python tools/queue_open_rows.py`와 `--ref origin/main`(`git fetch origin` 뒤)의 "만료할 행"이 둘 다 없음이었다
(출력을 손으로 봤다). 306 의 행 원문은 `.scratch/retro-queue.md`의 320줄을 grep 으로 손으로 봤다.

## 다음

harness 022 는 이 PR 로 닫힌다. 다음은 next-session 결정표의 harness 티켓 PR 줄대로 `plan.md`의 프론티어에서 고른다. 같은 묶음의
형제 가운데 열린 것은 각자 도는 중이라 다음 작업에 넣지 않는다. `web/packages/ui/src/styles/DesignTokens.stories.tsx`를
고쳤으므로 다음 디자인 시스템 올리기(`/sync-design-system 올리기`)가 빌드를 요구한다(PR 본문).

## 인계 (커밋 뒤, 봇 첫 회차 반영)

봇 첫 회차 반영과 위 회고·다음을 실은 커밋(747ac693)이 pre-commit 을 지났다(`Skipped`는 스테이지된 `.py`가 없는 ruff 둘,
카나리아 명세, 헌법 판. pytest 472초, web-verify 521초. 커밋 출력을 손으로 봤다). 인용 대조 경고 하나(커밋 해시를 줄여 옮긴
따옴표 인용)는 커밋 뒤 이 일지에서 따옴표를 떼어 고쳤고 커밋하지 않았다. 그 뒤 인계 계기가 `커밋 뒤` 경계에서 왔다. 세션
컨텍스트가 223,442 토큰으로 인계 문턱(20만 토큰)을 넘었다. 인계하지 않는 때 다섯에 들지 않아(커밋이 성공했다, 요청 범위는
PR 과 병합까지다, 지시문의 이어받을 상태는 `인계:`로 시작하지 않았다, `인계 못함` 줄이 없다, `get_session`의 `self`에
`parentSessionId`가 없다) 넘긴다. 이 세션의 지금 제목은 `chore/022-eslint-boolean-params`이고 넘기기 전에 `(인계함)`을 붙인다.
이 절은 커밋하지 않았다.

남은 단계: 이 절을 이어 쓰고 커밋해 747ac693 과 함께 한 번에 푸시한다(따로 푸시하면 claude-review 가 한 번 더 돈다). 그 뒤
`@coderabbitai review` 코멘트, `merge.md` 2 의 대기와 둘째 회차(봇마다 둘째 회차다. Critical·Major 만 고치고 나머지는 PR 코멘트에
보류 이유), `headRefOid` 대조 뒤 "워크트리에서 병합할 때"의 길이다. 형제 `design-card-build-spec`의 일지 2026-10-29-05 가
먼저 병합되면 `tools/sibling_overlap.py`의 출력대로 이 일지를 옮긴다.

인계 지시문:

다음 작업: .scratch/harness/issues/022-eslint-boolean-params.md. 대기열 483: web/eslint.config.mjs 가 타입이 boolean 인 함수 매개변수를 잡고 CODING_STANDARDS.md 의 그 줄이 이 규칙을 가리킨다
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 483을 티켓 .scratch/harness/issues/022-eslint-boolean-params.md로 쓰고 한다
브랜치: chore/022-eslint-boolean-params
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/agents/issue-tracker.md
이어받을 상태: 인계: 커밋 뒤. main 합치기와 봇 첫 회차 반영(CodeRabbit 지적 없음, claude-review Nit 하나를 고침), 일지의 회고와 "다음"까지 747ac693 으로 커밋했고 아직 푸시하지 않았다. 일지의 "인계 (커밋 뒤, 봇 첫 회차 반영)" 절은 커밋하지 않았다. 그 절을 이어 써 커밋한 뒤 함께 한 번에 푸시하고 봇 둘째 회차와 병합으로 간다. 남은 단계는 그 절의 "남은 단계". 일지 docs/journal/2026-10-29-04-eslint-boolean-params.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지

잠금 풀기는 `is not locked`로 넘어갔다.

open-session을 부른다 2026-10-29T07:17:58Z

## 이어받은 세션 (4)

> 사용자: "대기열 483을 티켓 .scratch/harness/issues/022-eslint-boolean-params.md로 쓰고 한다"

위 "인계 (커밋 뒤, 봇 첫 회차 반영)" 지시문으로 연 새 세션이다(2026-10-29). 제목을 `chore/022-eslint-boolean-params`로
바꾸고 `EnterWorktree(path)`로 이 워크트리에 들어왔다(잠금 거부 없이 들어왔다). 커밋하지 않은 변경은 이 일지 하나였고,
`git fetch origin` 뒤 origin/main 은 84542f52 그대로라 합칠 커밋이 없었다. `uv run python tools/sibling_overlap.py`는 번호
겹침 없음이었고, 이 일지를 이름순으로 앞서는 형제는 아직 열린 `design-card-build-spec`의 2026-10-29-05 하나였다(모두 출력을
손으로 봤다). 이 절을 더해 747ac693 과 함께 한 번에 푸시하고 봇 둘째 회차로 간다. 둘째 회차는 Critical·Major 만 고치고
나머지는 PR 코멘트에 보류 이유를 남긴다.
