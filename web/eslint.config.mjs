// web 워크스페이스의 ESLint 설정. 원칙 III 의 TypeScript 판정자(ADR 0020)와 web 의 층 경계(ADR 0021)다.
//
// - 판정 범위에서 빼는 목록을 두지 않는다(ADR 0013). 대상은 TS 파일 전부이고 `.d.ts` 와 생성물도 든다.
// - 인라인 설정 주석은 끈다(`noInlineConfig`). 끄기 주석은 에러가 아니라 경고로 보고되므로 린트 명령이
//   `--max-warnings 0` 이어야 게이트다(package.json 의 lint). 정당한 예외는 이 파일에 경로와 함께 둔다.
// - 경로에 기대는 규칙은 경로와 무관하게 쓴다. 앱이 어느 배치(`app/`, `src/app/`)를 쓰든 걸린다.
//   boundaries 의 요소 패턴은 경로의 끝에서부터 맞추므로(partialMatch) 앞의 디렉터리와 무관하다.
// - 새 플러그인을 들이지 않는다. 내장 규칙, typescript-eslint, eslint-plugin-boundaries 뿐이다.
//
// 각 규칙이 실제로 잡는지는 eslint.config.test.ts 가 위반을 만들어 넣어 잰다.
//
// 설정 파일이 .mjs 인 이유: ESLint 10 은 .ts 설정에 jiti(새 의존성)나 불안정 플래그를 요구한다.

import { defineConfig } from "eslint/config";
import boundaries from "eslint-plugin-boundaries";
import tseslint from "typescript-eslint";

const TYPESCRIPT = ["**/*.{ts,tsx,mts,cts}"];

// no-restricted-syntax 는 파일마다 한 번만 설정된다. 뒤 블록이 이 규칙을 다시 적으면 앞 목록을 통째로
// 덮으므로, 금지 구문은 이 상수 하나에 두고 서버 파일 블록도 이것을 펼쳐 쓴다.
const RESTRICTED_SYNTAX = [
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

// 생성 클라이언트 패키지(ADR 0021). 앱이 워크스페이스 의존성으로 든다.
const API_CLIENT = "@agent-os/api-client";

// 아토믹 층. 아래 층은 위 층을 import 하지 않고, atoms·molecules 는 API 를 부르지 않는다(tech.md 프론트 구성).
const LAYER_POLICIES = [
  ["atom", ["molecule", "organism", "template", "page", "route", "api", "query"]],
  ["molecule", ["organism", "template", "page", "route", "api", "query"]],
  ["organism", ["template", "page", "route"]],
  ["template", ["page", "route"]],
  ["page", ["route"]],
].map(([from, above]) => ({
  from: { element: { type: from } },
  disallow: { to: { element: { types: { anyOf: above } } } },
}));

export default defineConfig(
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
        // 도메인 폴더. 밖에서는 index.ts barrel 로만 들어온다.
        { type: "api", pattern: "api/*" },
        { type: "query", pattern: "hooks/queries/*" },
        { type: "types", pattern: "types/*" },
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
      "no-restricted-globals": ["error", { name: "fetch", message: FETCH_MESSAGE }],
      "no-restricted-properties": [
        "error",
        ...["globalThis", "window", "self"].map((object) => ({
          object,
          property: "fetch",
          message: FETCH_MESSAGE,
        })),
      ],
      "no-restricted-imports": [
        "error",
        {
          paths: [
            {
              name: "lucide-react",
              message: "아이콘은 세트가 아니라 아이콘 하나의 서브패스로 import 한다(ADR 0021)",
            },
          ],
        },
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
                "atoms 와 molecules 는 순수하다. 생성 클라이언트는 organisms 이상만 부른다(tech.md 프론트 구성)",
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
                  { element: { types: { noneOf: ["page", "template"] } } },
                  { module: { origin: "external", source: "!{next,react}" } },
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
    // Next 서버가 돌리는 파일. 앱의 어느 자리에 두어도 막는다(ADR 0019).
    files: ["**/{route,middleware,proxy,instrumentation}.{ts,tsx,mts,cts,js,jsx,mjs,cjs}"],
    rules: {
      "no-restricted-syntax": ["error", ...RESTRICTED_SYNTAX, SERVER_FILE],
    },
  },
);
