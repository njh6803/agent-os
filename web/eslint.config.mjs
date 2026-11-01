// web 워크스페이스의 ESLint 설정. 원칙 III 의 TypeScript 판정자(ADR 0020)와 web 의 층 경계(ADR 0021)다.
//
// - 판정 범위에서 빼는 목록을 두지 않는다(ADR 0013). 대상은 TS 파일 전부이고 `.d.ts` 와 커밋하는 생성물도 든다.
//   빠지는 것은 저장소의 `.gitignore` 가 무시하는 빌드 산출물(`.next/` 등)뿐이고, 그 파일을 그대로 읽는다. 그래서
//   목록이 둘이 되지 않는다(ADR 0020 의 2026-09-30 이력). 추적하는 파일이 하나도 빠지지 않는다는 것은
//   eslint.config.test.ts 가 git 으로 재고, 아직 추적되지 않은 소스 자리의 반례(`app/traces/`)도 거기 있다.
// - 인라인 설정 주석은 끈다(`noInlineConfig`). 끄기 주석은 에러가 아니라 경고로 보고되므로 린트 명령이
//   `--max-warnings 0` 이어야 게이트다(package.json 의 lint). 정당한 예외는 이 파일에 경로와 함께 둔다.
// - 경로에 기대는 규칙은 경로와 무관하게 쓴다. 앱이 어느 배치(`app/`, `src/app/`)를 쓰든 걸린다.
//   boundaries 의 요소 패턴은 경로의 끝에서부터 맞추므로(partialMatch) 앞의 디렉터리와 무관하다.
// - 새 플러그인을 들이지 않는다. 내장 규칙, typescript-eslint, eslint-plugin-boundaries 뿐이다.
//
// 각 규칙이 실제로 잡는지는 eslint.config.test.ts 가 위반을 만들어 넣어 잰다.
//
// 설정 파일이 .mjs 인 이유: ESLint 10 은 .ts 설정에 jiti(새 의존성)나 불안정 플래그를 요구한다.

import { join } from "node:path";
import { defineConfig, includeIgnoreFile } from "eslint/config";
import boundaries from "eslint-plugin-boundaries";
import tseslint from "typescript-eslint";

const TYPESCRIPT = ["**/*.{ts,tsx,mts,cts}"];
// 저장소 뿌리의 .gitignore. git 의 해석 그대로(자기 디렉터리 기준) 읽는다.
const GITIGNORE = join(import.meta.dirname, "..", ".gitignore");

// 불리언 플래그 매개변수(CODING_STANDARDS.md). 잡는 자리는 파이썬의 ruff FBT001·FBT002 에 맞춘다. 함수 정의(선언,
// 함수 식, 화살표 함수, 메서드. 세터는 ruff 처럼 뺀다)의 매개변수 가운데 주석이 boolean 이거나 boolean 을 바로 든
// 유니온인 것과, 주석과 무관하게 기본값이 true·false 리터럴인 것을 잡는다. 주석과 리터럴 기본값이 함께 있으면 기본값
// 쪽에서 한 번만 보고한다. 판정자는 플래그와 값을 가르지 못해, 값을 싣는 불리언(서버에 보낼 켜짐, 콜백의 구현)도
// 함수 정의의 매개변수면 잡는다. 이름 붙인 옵션 객체(`{ force }: { readonly force: boolean }`)는 파이썬의 키워드 전용
// 매개변수처럼 지나간다. 보지 않는 자리는 함수 타입과 메서드 시그니처(값을 넘기는 콜백 `(checked: boolean) => void`),
// 본문 없는 선언과 오버로드, 리터럴 타입 true·false, 유니온 속 유니온의 boolean, 배열과 제네릭 인자의 boolean,
// boolean 의 별칭 주석(`type Flag = boolean`. 기본값이 true·false 리터럴이면 그 기본값으로 잡는다), 교차 타입의
// boolean, 제네릭 제약(`T extends boolean`), 리터럴이 아닌 기본값(`!0`), 호출에 넘긴 true·false(ruff FBT003 의
// 자리)다. 생성자의 매개변수 속성은 판정자가 아니라 tsconfig.base.json 의 `erasableSyntaxOnly` 가 타입 검사에서
// 막는다.
const DEFINED_FUNCTION = ':function:not([kind="set"] > *)';
const BOOLEAN_ANNOTATIONS = ["TSBooleanKeyword", "TSUnionType > TSBooleanKeyword"];
const BOOLEAN_PARAMETER = {
  selector: [
    ...BOOLEAN_ANNOTATIONS.map(
      (type) => `${DEFINED_FUNCTION} > .params > TSTypeAnnotation > ${type}`,
    ),
    ...BOOLEAN_ANNOTATIONS.map(
      (type) =>
        `${DEFINED_FUNCTION} > AssignmentPattern.params:not([right.value=type(boolean)]) > Identifier.left > TSTypeAnnotation > ${type}`,
    ),
    `${DEFINED_FUNCTION} > AssignmentPattern.params > Literal.right[value=type(boolean)]`,
  ].join(", "),
  message:
    "불리언 매개변수를 두지 않는다. 갈래를 고르는 플래그면 함수를 둘로 쪼개고, 값이면 이름 붙인 옵션 객체로 받는다(CODING_STANDARDS.md)",
};

// maxRetries 없는 재귀 rmSync(대기열 543). 윈도우에서 `rmSync(경로, { recursive: true })` 는 다른 프로세스가 그 안의
// 파일을 잠깐 쥐고 있으면 `EPERM` 으로 끝난다. 시험의 `afterAll` 이면 시험이 다 지나도 실행이 1로 끝나고 임시 폴더가
// 남는다. 사례마다 그 자리를 고쳐 온 것이 종류를 없애지 못해(65·379·543) 판정자가 종류를 막는다. 잡는 자리는
// `rmSync(…)` 와 `<객체>.rmSync(…)` 호출의 옵션 객체 리터럴이 `recursive: true` 를 갖고 `maxRetries` 가 없거나 0 인 것이다.
// `force` 와 `retryDelay` 는 보지 않는다. 키는 식별자(`recursive`)와 문자열(`"recursive"`) 둘 다 읽는다. 보지 못하는 자리는
// 옵션을 변수로 넘기거나 `...펼침` 을 든 호출(펼친 쪽이 `maxRetries` 를 줄 수 있어 뺀다), 값이 리터럴이 아닌
// `recursive`·`maxRetries`(변수, `!0`, `undefined`, 음수), 약식 속성(`{ recursive }`), `satisfies` 로 감싼 옵션, 별칭으로
// 부른 `rmSync`, 괄호 접근(`fs["rmSync"]`), `rmdirSync`, 비동기 `rm` 이 대표적이고 이 목록이 전부는 아니다. 옵션
// 객체 리터럴의 직계 속성만 보므로 안쪽 객체의 `maxRetries` 에 속지 않는다. `maxRetries` 는 일시 잠김을 다시 시도해 넘길 뿐이라, 다른 프로세스가 그 폴더를 작업 폴더로 쥔 경우는 못 푼다.
const RM_CALL =
  ":matches(CallExpression[callee.name='rmSync'], CallExpression[callee.property.name='rmSync'])";
const optionKey = (name) => `:matches(Property[key.name='${name}'], Property[key.value='${name}'])`;
const RECURSIVE_RM_WITHOUT_RETRIES = {
  selector: `${RM_CALL} > ObjectExpression.arguments:has(> ${optionKey("recursive")}[value.value=true]):not(:has(> SpreadElement)):not(:has(> ${optionKey("maxRetries")}:not([value.value=0])))`,
  message:
    "재귀 rmSync 는 maxRetries 를 준다(예: `maxRetries: 5`). 윈도우에서 다른 프로세스가 쥔 파일 때문에 EPERM 으로 끝난다(대기열 543)",
};

// no-restricted-syntax 는 파일마다 한 번만 설정된다. 뒤 블록이 이 규칙을 다시 적으면 앞 목록을 통째로
// 덮으므로, 금지 구문은 이 상수 하나에 두고 서버 파일 블록도 이것을 펼쳐 쓴다.
const RESTRICTED_SYNTAX = [
  BOOLEAN_PARAMETER,
  RECURSIVE_RM_WITHOUT_RETRIES,
  {
    selector: "TSEnumDeclaration",
    message: "TS enum 을 쓰지 않는다. `as const` 배열과 그 유니온을 쓴다(ADR 0021)",
  },
  {
    selector:
      "JSXAttribute[name.name='dangerouslySetInnerHTML'], Property[key.name='dangerouslySetInnerHTML']",
    message: "HTML 로 렌더하지 않는다. 서버가 준 글자는 글자로 그린다(ADR 0019)",
  },
  {
    selector: "ExpressionStatement[directive='use server']",
    message: "Server Actions 를 두지 않는다. API 는 브라우저가 생성 클라이언트로 부른다(ADR 0019)",
  },
];

const SERVER_FILE = {
  selector: "Program",
  message:
    "Next 서버가 돌리는 파일(route, middleware, proxy, instrumentation)을 두지 않는다. API 를 부르는 서버 코드가 없다(ADR 0019)",
};

// 생성 클라이언트 패키지도 예외가 아니다. fetch 를 부르는 것은 그 안의 openapi-fetch 다.
const FETCH_MESSAGE = "HTTP 는 생성 클라이언트로 부른다. 전역 fetch 를 직접 쓰지 않는다(ADR 0021)";

// fetch 밖에서 HTTP 를 내는 브라우저 전역. SSE 는 생성 클라이언트가 `parseAs: "stream"` 으로 받는다(ADR 0021).
// 티켓 03 의 셀프 리뷰가 판정자가 막지 않는 길로 찾았고, 앱 코드가 처음 API 를 부르는 티켓 05 가 막았다.
const HTTP_GLOBALS = [
  { name: "fetch", message: FETCH_MESSAGE },
  ...["EventSource", "XMLHttpRequest"].map((name) => ({
    name,
    message: `HTTP 는 생성 클라이언트로 부른다. ${name} 을 쓰지 않는다(ADR 0021)`,
  })),
];

// 생성 클라이언트 패키지(ADR 0021). 앱이 워크스페이스 의존성으로 든다.
const API_CLIENT = "@agent-os/api-client";

// no-restricted-imports 도 파일마다 한 번만 설정된다. 생성 클라이언트 패키지의 블록이 목록을 다시 적으므로 항목을
// 상수로 둔다.
const ICON_SET_IMPORT = {
  name: "lucide-react",
  message: "아이콘은 세트가 아니라 아이콘 하나의 서브패스로 import 한다(ADR 0021)",
};
const OPENAPI_FETCH_IMPORT = {
  name: "openapi-fetch",
  message: `클라이언트를 직접 만들지 않는다. 토큰을 고르는 것은 ${API_CLIENT} 의 클라이언트 셋이다(ADR 0021·0024)`,
};
// 상대 경로로 패키지 안을 import 하면 로컬로 분류되어 층 경계의 모듈 이름 정책을 피한다(티켓 03 의 셀프 리뷰).
const API_CLIENT_INTERNALS = {
  group: ["**/packages/api-client/**"],
  message: `생성 클라이언트는 패키지 이름(${API_CLIENT})으로만 import 한다. 층 경계가 그 이름을 본다`,
};

// 아토믹 층. 아래 층은 위 층을 import 하지 않고, atoms·molecules 는 API 와 스토어를 부르지 않는다(tech.md 프론트 구성).
const LAYER_POLICIES = [
  ["atom", ["molecule", "organism", "template", "page", "route", "api", "query", "store"]],
  ["molecule", ["organism", "template", "page", "route", "api", "query", "store"]],
  ["organism", ["template", "page", "route"]],
  ["template", ["page", "route"]],
  ["page", ["route"]],
].map(([from, above]) => ({
  from: { element: { type: from } },
  disallow: { to: { element: { types: { anyOf: above } } } },
}));

export default defineConfig(
  includeIgnoreFile(GITIGNORE, { gitignoreResolution: true, name: ".gitignore 가 무시하는 것" }),
  {
    linterOptions: { noInlineConfig: true },
  },
  {
    files: TYPESCRIPT,
    extends: [tseslint.configs.strictTypeChecked],
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    rules: {
      // 원칙 III: 타입 단언(as, 꺾쇠)을 쓰지 않는다. `as const` 는 단언이 아니라 이 설정이 면제한다.
      "@typescript-eslint/consistent-type-assertions": ["error", { assertionStyle: "never" }],
      // 원칙 III: 억제 주석을 쓰지 않는다. strict 설정은 설명 붙은 @ts-expect-error 를 어디서나 허용한다.
      "@typescript-eslint/ban-ts-comment": [
        "error",
        { "ts-expect-error": true, "ts-ignore": true, "ts-nocheck": true },
      ],
    },
  },
  {
    // @ts-expect-error 는 억제가 아니라 "이 코드는 컴파일되면 안 된다"는 단언이다. 타입 테스트에서만 쓴다.
    files: ["**/*.test-d.ts"],
    rules: {
      "@typescript-eslint/ban-ts-comment": [
        "error",
        {
          "ts-expect-error": "allow-with-description",
          "ts-ignore": true,
          "ts-nocheck": true,
          minimumDescriptionLength: 10,
        },
      ],
    },
  },
  {
    plugins: { boundaries },
    settings: {
      "import/resolver": { node: { extensions: [".ts", ".tsx", ".d.ts", ".mts", ".cts", ".js"] } },
      // 기본은 import 만 본다. 다시 내보내기와 동적 import 로 경계를 넘는 길도 닫는다.
      "boundaries/dependency-nodes": ["import", "export", "dynamic-import", "require"],
      "boundaries/elements": [
        { type: "atom", pattern: "components/atoms" },
        { type: "molecule", pattern: "components/molecules" },
        { type: "organism", pattern: "components/organisms" },
        { type: "template", pattern: "components/templates" },
        { type: "page", pattern: "components/pages" },
        // Next 의 app 디렉터리. 라우팅과 레이아웃만 한다(ADR 0021).
        { type: "route", pattern: "app" },
        // 도메인 폴더. 밖에서는 index.ts barrel 로만 들어온다. api 는 도메인 이름을 잡아 organisms 에 요청 함수가
        // 없는 api/failure 만 연다(아래 정책).
        { type: "api", pattern: "api/*", capture: ["domain"] },
        { type: "query", pattern: "hooks/queries/*" },
        { type: "types", pattern: "types/*" },
        // 클라이언트 상태. 토큰 스토어(Zustand)와 문서 뿌리를 원천으로 읽는 테마가 여기 있다.
        { type: "store", pattern: "stores" },
        // 앱 하나(apps/<이름>). 층 폴더 밖의 앱 파일(lib/ 등)도 요소가 되어 아래 app/ 정책이 그것을 막는다.
        // 이 요소가 없으면 그 파일은 알 수 없는 로컬이라 정책 밖이다.
        { type: "workspace-app", pattern: "apps/*" },
      ],
      // 앱 이름은 경로의 앞쪽이라 요소가 아니라 파일 범주로 잡는다. 파일 범주는 경로 전체로 맞춘다.
      "boundaries/files": [
        { category: "in-app", pattern: "**/apps/*/**", capture: ["before", "app", "within"] },
      ],
    },
    rules: {
      "no-restricted-syntax": ["error", ...RESTRICTED_SYNTAX],
      "no-restricted-globals": ["error", ...HTTP_GLOBALS],
      "no-restricted-properties": [
        "error",
        ...["globalThis", "window", "self"].flatMap((object) =>
          HTTP_GLOBALS.map(({ name, message }) => ({ object, property: name, message })),
        ),
      ],
      "no-restricted-imports": [
        "error",
        { paths: [ICON_SET_IMPORT, OPENAPI_FETCH_IMPORT], patterns: [API_CLIENT_INTERNALS] },
      ],
      "boundaries/dependencies": [
        "error",
        {
          default: "allow",
          checkAllOrigins: true,
          policies: [
            ...LAYER_POLICIES,
            {
              // pnpm 링크(윈도우는 junction)로 풀린 워크스페이스 패키지는 external 로 분류된다(2026-09-29 실측. 판정자
              // 테스트가 그 링크를 둔다). 상대 경로로 패키지 안을 import 하면 로컬이라 이 정책이 보지 못한다.
              from: { element: { types: { anyOf: ["atom", "molecule"] } } },
              disallow: { to: { module: { origin: "external", source: API_CLIENT } } },
              message:
                "atoms 와 molecules 는 순수하다. 생성 클라이언트를 부르지 않는다(tech.md 프론트 구성)",
            },
            {
              // 서버 데이터와 토큰을 읽고 처리기를 만드는 것은 pages 다. 값으로 싣는 import 만 막는다. 같은 줄의
              // `type` 지정자(`import { type X }`)는 verbatimModuleSyntax 에서 모듈을 그대로 실어 값으로 센다.
              // 모듈의 source 는 서브패스를 뗀 패키지 이름과 맞춘다(swr/infinite 도 swr 다. 판정자 테스트가 잰다).
              // api 도메인 가운데 failure 만 지난다. 요청 함수가 없고 실패 해석만 낸다.
              from: { element: { types: { anyOf: ["organism", "template"] } } },
              disallow: [
                { to: { element: { types: { anyOf: ["query", "store"] } } } },
                { to: { element: { type: "api", captured: { domain: "!failure" } } } },
                { to: { module: { origin: "external", source: `{${API_CLIENT},swr}` } } },
              ].map((selector) => ({ ...selector, dependency: { kind: "value" } })),
              message:
                "organisms 와 templates 는 hooks/queries, stores, swr, 생성 클라이언트, api/failure 밖의 api 를 부르지 않는다. pages 가 읽어 organisms 에 props 로 넘긴다(ADR 0021 의 2026-10-27 이력)",
            },
            {
              from: { file: { categories: "in-app" } },
              disallow: {
                to: {
                  file: {
                    categories: "in-app",
                    captured: { app: "!{{ from.file.captured.app }}" },
                  },
                },
              },
              message: "앱 사이에서 import 하지 않는다. 함께 쓸 것은 packages/ 로 옮긴다",
            },
            {
              to: { element: { types: { anyOf: ["api", "query", "types"] } } },
              disallow: { to: { element: { fileInternalPath: "!index.{ts,tsx}" } } },
              message: "도메인 폴더(api, hooks/queries, types)는 index.ts barrel 로만 import 한다",
            },
            {
              from: { element: { type: "route" } },
              disallow: {
                to: [
                  // 로컬로 좁힌다. 앱의 node_modules 로 풀린 외부 모듈(next, react)은 경로가 apps/<이름>/ 아래라
                  // workspace-app 요소로도 분류돼, 좁히지 않으면 "pages·templates 가 아니다"에 걸렸다(티켓 04 가 실제
                  // app/layout.tsx 에서 봤다. 임시 트리에는 next 가 설치되지 않아 드러나지 않았다).
                  {
                    module: { origin: "local" },
                    element: { types: { noneOf: ["page", "template"] } },
                  },
                  // 노드 내장 모듈(core)도 막는다. app/ 의 파일이 서버에서 도는 코드를 부르는 길이다.
                  { module: { origin: "{external,core}", source: "!{next,react}" } },
                ],
              },
              message:
                "app/ 의 파일은 components/pages 와 components/templates 만 import 한다. 라우팅과 레이아웃만 한다(ADR 0021)",
            },
          ],
        },
      ],
    },
  },
  {
    // 생성 클라이언트 패키지는 openapi-fetch 로 클라이언트 셋을 만드는 유일한 자리다. 여기서만 그 import 를 푼다.
    files: ["**/packages/api-client/**"],
    rules: {
      "no-restricted-imports": [
        "error",
        { paths: [ICON_SET_IMPORT], patterns: [API_CLIENT_INTERNALS] },
      ],
    },
  },
  {
    // 디자인 시스템 패키지의 아이콘. lucide-react 서브패스의 모듈 선언(ADR 0024)은 앰비언트라 import 로 끌어올 수 없고,
    // 패키지를 소스로 import 하는 앱의 tsc 에는 그 선언이 실리지 않는다(2026-10-07 스크래치 tsc 로 손으로 봤다: TS2307).
    // 그것을 쓰는 이 파일의 경로 참조만이 앱의 프로그램에 선언을 싣는다. 이 파일에서만 경로 참조를 푼다.
    files: ["**/packages/ui/src/components/atoms/Icon.tsx"],
    rules: {
      "@typescript-eslint/triple-slash-reference": [
        "error",
        { path: "always", types: "prefer-import", lib: "always" },
      ],
    },
  },
  {
    // Next 서버가 돌리는 파일. 앱의 어느 자리에 두어도 막는다(ADR 0019).
    files: ["**/{route,middleware,proxy,instrumentation}.{ts,tsx,mts,cts,js,jsx,mjs,cjs}"],
    rules: {
      "no-restricted-syntax": ["error", ...RESTRICTED_SYNTAX, SERVER_FILE],
    },
  },
);
