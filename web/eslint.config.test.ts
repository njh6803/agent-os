// 판정자(eslint.config.mjs)의 변이 테스트. 원칙 III 의 TS 판정자(ADR 0020)와 web 의 층 경계(ADR 0021).
//
// 위반을 담은 코드는 이 테스트가 web/ 아래 임시 트리에 쓰고 끝나면 지운다. 커밋한 파일에 위반을 두면 그
// 파일을 판정에서 빼는 목록이 생긴다(ADR 0013 이 경계한 모양).
//
// 임시 트리는 워크스페이스의 자리(apps/<이름>/…, packages/<이름>/…)를 흉내 내고, 앱과 패키지마다 기준
// tsconfig 를 extends 하는 자기 tsconfig 를 둔다. 타입 기반 규칙의 프로젝트 서비스는 파일에서 가장 가까운
// tsconfig 를 찾는다. 어느 tsconfig 에도 들지 않는 파일은 규칙이 아니라 파싱 오류로 빨개진다(2026-09-29
// 실측). 그래서 사례마다 "빨갛다"가 아니라 기대한 규칙이 보고됐는지를 본다.

import { spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join, relative, sep } from "node:path";
import { ESLint, type Linter } from "eslint";
import { afterAll, beforeAll, describe, expect, test } from "vitest";

const WEB = import.meta.dirname;
const ESLINT_BIN = join(WEB, "node_modules", "eslint", "bin", "eslint.js");

// 자기 tsconfig 를 두는 자리. 임시 트리 뿌리에는 tsconfig 가 없다.
const PROJECTS = ["apps/admin", "apps/widget", "packages/api-client", "cli"];

function projectTsconfig(project: string): string {
  const base = relative(join(fixture, project), join(WEB, "tsconfig.base.json"));
  return JSON.stringify({
    extends: base.split(sep).join("/"),
    compilerOptions: {
      module: "preserve",
      moduleResolution: "bundler",
      jsx: "preserve",
      lib: ["es2024", "dom"],
      types: [],
    },
    include: ["**/*"],
  });
}

// 임시 트리의 파일. 빨강과 초록 사례가 가리키고, import 되는 쪽도 여기 있다.
const SOURCES: Readonly<Record<string, string>> = {
  "apps/admin/lib/any.ts": "export function 받는다(값: any): void {\n  void 값;\n}\n",
  "apps/admin/lib/as.ts": 'export const 수 = JSON.parse("1") as number;\n',
  "apps/admin/lib/angle.ts": "export const 수 = <number>(<unknown>1);\n",
  "apps/admin/lib/non-null.ts":
    "export function 첫째(목록: readonly string[]): string {\n  return 목록[0]!;\n}\n",
  "apps/admin/lib/ts-ignore.ts": "// @ts-ignore: 옛 코드\nexport const 수: number = 1;\n",
  "apps/admin/lib/ts-nocheck.ts": "// @ts-nocheck\nexport const 수 = 1;\n",
  "apps/admin/lib/expect-error.ts":
    "// @ts-expect-error: 숫자는 문자열 자리에 들어가지 않는다\nexport const 글: string = 1;\n",
  "apps/admin/lib/enum.ts": "export enum 색 {\n  빨강,\n}\n",
  "apps/admin/lib/fetch.ts":
    'export async function 부른다(): Promise<Response> {\n  return fetch("/api/runs");\n}\n',
  "apps/admin/lib/global-fetch.ts":
    'export async function 부른다(): Promise<Response> {\n  return globalThis.fetch("/api/runs");\n}\n',
  "apps/admin/lib/global.d.ts": "export declare const 값: any;\n",
  "apps/admin/lib/actions.ts":
    '"use server";\n\nexport async function 저장(): Promise<void> {\n  await Promise.resolve();\n}\n',
  "apps/admin/lib/inline-action.ts":
    'export async function 저장(): Promise<void> {\n  "use server";\n  await Promise.resolve();\n}\n',
  "apps/admin/components/atoms/Html.tsx":
    'export function 글(): unknown {\n  return <div dangerouslySetInnerHTML={{ __html: "<b>굵게</b>" }} />;\n}\n',
  "apps/admin/app/api/runs/route.ts": "export const 값 = 1;\n",
  "apps/admin/middleware.ts": "export const 값 = 1;\n",
  "apps/admin/src/proxy.ts": "export const 값 = 1;\n",
  "apps/admin/src/instrumentation.ts": "export const 값 = 1;\n",
  "apps/admin/components/atoms/Button.ts":
    'import { 카드 } from "../organisms/Card";\n\nexport const 버튼 = 카드;\n',
  "apps/admin/components/atoms/Label.ts": "export const 라벨 = 1;\n",
  "apps/admin/components/atoms/Icon.ts":
    'import { Camera } from "lucide-react";\n\nexport const 아이콘 = Camera;\n',
  "apps/admin/components/organisms/Card.ts": "export const 카드 = 1;\n",
  "apps/admin/components/organisms/Panel.ts":
    'import { 라벨 } from "../atoms/Label";\n\nexport const 판 = 라벨;\n',
  "apps/admin/components/organisms/DeepApi.ts":
    'import { 실행_목록 } from "../../api/runs/listRuns";\n\nexport const 깊이 = 실행_목록;\n',
  "apps/admin/components/organisms/DeepQuery.ts":
    'import { 실행_훅 } from "../../hooks/queries/runs/useRuns";\n\nexport const 깊이 = 실행_훅;\n',
  "apps/admin/components/organisms/DeepType.ts":
    'import { 실행_종류 } from "../../types/run/kinds";\n\nexport const 깊이 = 실행_종류;\n',
  "apps/admin/components/organisms/Runs.ts":
    'import { 실행_목록 } from "../../api/runs";\n\nexport const 실행들 = 실행_목록;\n',
  "apps/admin/components/pages/Home.ts": "export const 홈 = 1;\n",
  "apps/admin/components/pages/Remote.ts":
    'import { 위젯 } from "../../../widget/lib/widget";\n\nexport const 원격 = 위젯;\n',
  "apps/admin/components/templates/Shell.ts": "export const 틀 = 1;\n",
  "apps/admin/api/runs/index.ts": 'export { 실행_목록 } from "./listRuns";\n',
  "apps/admin/api/runs/listRuns.ts": "export const 실행_목록 = 1;\n",
  "apps/admin/hooks/queries/runs/index.ts": 'export { 실행_훅 } from "./useRuns";\n',
  "apps/admin/hooks/queries/runs/useRuns.ts": "export const 실행_훅 = 1;\n",
  "apps/admin/types/run/index.ts": 'export { 실행_종류 } from "./kinds";\n',
  "apps/admin/types/run/kinds.ts": 'export const 실행_종류 = ["완료", "실패"] as const;\n',
  "apps/admin/app/page.ts":
    'import { 홈 } from "../components/pages/Home";\nimport { 틀 } from "../components/templates/Shell";\n\nexport const 첫_화면 = [홈, 틀];\n',
  "apps/admin/app/runs/page.ts":
    'import { 카드 } from "../../components/organisms/Card";\n\nexport const 화면 = 카드;\n',
  "apps/admin/app/layout.ts":
    'import { 클라이언트 } from "@agent-os/api-client";\n\nexport const 틀 = 클라이언트;\n',
  "apps/admin/lib/kinds.ts": 'export const 종류 = ["plugins", "runs"] as const;\n',
  "apps/admin/lib/kinds.test-d.ts":
    "// @ts-expect-error: 숫자는 문자열 자리에 들어가지 않는다\nexport const 틀린_값: string = 1;\n",
  "apps/admin/lib/bare.test-d.ts": "// @ts-expect-error\nexport const 틀린_값: string = 1;\n",
  "apps/admin/app/settings/page.ts":
    'import { 종류 } from "../../lib/kinds";\n\nexport const 설정 = 종류;\n',
  "apps/widget/lib/widget.ts": "export const 위젯 = 1;\n",
  "packages/api-client/src/client.ts":
    'export function 부른다(): Promise<Response> {\n  return fetch("/api/runs");\n}\n',
  // 끄기 주석. CLI 로 따로 돈다.
  "cli/next-line.ts":
    "// eslint-disable-next-line @typescript-eslint/no-explicit-any\nexport function 받는다(값: any): void {\n  void 값;\n}\n",
  "cli/whole-file.ts":
    "/* eslint-disable */\nexport function 받는다(값: any): void {\n  void 값;\n}\n",
  "cli/lone.ts": "// eslint-disable-next-line no-console\nexport const 값 = 1;\n",
};

interface RedCase {
  readonly name: string;
  readonly path: string;
  readonly rule: string;
}

const RESTRICTED_SYNTAX = "no-restricted-syntax";
const BOUNDARIES = "boundaries/dependencies";

const RED: readonly RedCase[] = [
  { name: ".ts 의 any", path: "apps/admin/lib/any.ts", rule: "@typescript-eslint/no-explicit-any" },
  {
    name: "as 단언",
    path: "apps/admin/lib/as.ts",
    rule: "@typescript-eslint/consistent-type-assertions",
  },
  {
    name: "꺾쇠 단언",
    path: "apps/admin/lib/angle.ts",
    rule: "@typescript-eslint/consistent-type-assertions",
  },
  {
    name: "비null 단언",
    path: "apps/admin/lib/non-null.ts",
    rule: "@typescript-eslint/no-non-null-assertion",
  },
  {
    name: "@ts-ignore",
    path: "apps/admin/lib/ts-ignore.ts",
    rule: "@typescript-eslint/ban-ts-comment",
  },
  {
    name: "@ts-nocheck",
    path: "apps/admin/lib/ts-nocheck.ts",
    rule: "@typescript-eslint/ban-ts-comment",
  },
  {
    name: "타입 테스트가 아닌 파일의 설명 붙은 @ts-expect-error",
    path: "apps/admin/lib/expect-error.ts",
    rule: "@typescript-eslint/ban-ts-comment",
  },
  {
    name: "타입 테스트 파일의 설명 없는 @ts-expect-error",
    path: "apps/admin/lib/bare.test-d.ts",
    rule: "@typescript-eslint/ban-ts-comment",
  },
  { name: "TS enum", path: "apps/admin/lib/enum.ts", rule: RESTRICTED_SYNTAX },
  {
    name: "생성 클라이언트 밖의 전역 fetch",
    path: "apps/admin/lib/fetch.ts",
    rule: "no-restricted-globals",
  },
  {
    name: "globalThis 로 부른 fetch",
    path: "apps/admin/lib/global-fetch.ts",
    rule: "no-restricted-properties",
  },
  {
    name: ".d.ts 의 any",
    path: "apps/admin/lib/global.d.ts",
    rule: "@typescript-eslint/no-explicit-any",
  },
  { name: '파일 머리의 "use server"', path: "apps/admin/lib/actions.ts", rule: RESTRICTED_SYNTAX },
  {
    name: '함수 안의 "use server"',
    path: "apps/admin/lib/inline-action.ts",
    rule: RESTRICTED_SYNTAX,
  },
  {
    name: ".tsx 의 dangerouslySetInnerHTML",
    path: "apps/admin/components/atoms/Html.tsx",
    rule: RESTRICTED_SYNTAX,
  },
  {
    name: "라우트 핸들러 route",
    path: "apps/admin/app/api/runs/route.ts",
    rule: RESTRICTED_SYNTAX,
  },
  { name: "앱 뿌리의 middleware", path: "apps/admin/middleware.ts", rule: RESTRICTED_SYNTAX },
  { name: "src 아래의 proxy", path: "apps/admin/src/proxy.ts", rule: RESTRICTED_SYNTAX },
  {
    name: "src 아래의 instrumentation",
    path: "apps/admin/src/instrumentation.ts",
    rule: RESTRICTED_SYNTAX,
  },
  {
    name: "atoms 가 organisms 를 import",
    path: "apps/admin/components/atoms/Button.ts",
    rule: BOUNDARIES,
  },
  { name: "앱 사이의 import", path: "apps/admin/components/pages/Remote.ts", rule: BOUNDARIES },
  {
    name: "api 도메인의 barrel 을 거치지 않는 import",
    path: "apps/admin/components/organisms/DeepApi.ts",
    rule: BOUNDARIES,
  },
  {
    name: "hooks/queries 도메인의 barrel 을 거치지 않는 import",
    path: "apps/admin/components/organisms/DeepQuery.ts",
    rule: BOUNDARIES,
  },
  {
    name: "types 도메인의 barrel 을 거치지 않는 import",
    path: "apps/admin/components/organisms/DeepType.ts",
    rule: BOUNDARIES,
  },
  {
    name: "아이콘 세트를 통째로 import",
    path: "apps/admin/components/atoms/Icon.ts",
    rule: "no-restricted-imports",
  },
  { name: "app/ 이 organisms 를 import", path: "apps/admin/app/runs/page.ts", rule: BOUNDARIES },
  {
    name: "app/ 이 층 밖의 앱 파일을 import",
    path: "apps/admin/app/settings/page.ts",
    rule: BOUNDARIES,
  },
  {
    name: "app/ 이 생성 클라이언트 패키지를 import",
    path: "apps/admin/app/layout.ts",
    rule: BOUNDARIES,
  },
];

const GREEN: readonly { readonly name: string; readonly path: string }[] = [
  { name: "as const", path: "apps/admin/lib/kinds.ts" },
  { name: "타입 테스트 파일의 설명 붙은 @ts-expect-error", path: "apps/admin/lib/kinds.test-d.ts" },
  { name: "barrel 을 거친 import", path: "apps/admin/components/organisms/Runs.ts" },
  { name: "organisms 가 atoms 를 import", path: "apps/admin/components/organisms/Panel.ts" },
  { name: "app/ 이 pages 와 templates 를 import", path: "apps/admin/app/page.ts" },
  { name: "생성 클라이언트 패키지 안의 전역 fetch", path: "packages/api-client/src/client.ts" },
];

let fixture = "";
const messages = new Map<string, readonly Linter.LintMessage[]>();

beforeAll(async () => {
  fixture = mkdtempSync(join(WEB, "judge-"));
  for (const project of PROJECTS) {
    mkdirSync(join(fixture, project), { recursive: true });
    writeFileSync(join(fixture, project, "tsconfig.json"), projectTsconfig(project));
  }
  for (const [path, source] of Object.entries(SOURCES)) {
    mkdirSync(dirname(join(fixture, path)), { recursive: true });
    writeFileSync(join(fixture, path), source);
  }
  const results = await new ESLint({ cwd: WEB }).lintFiles([
    join(fixture, "apps"),
    join(fixture, "packages"),
  ]);
  for (const result of results) {
    messages.set(relative(fixture, result.filePath).split(sep).join("/"), result.messages);
  }
});

afterAll(() => {
  if (fixture !== "") {
    rmSync(fixture, { recursive: true, force: true });
  }
});

function reported(path: string): readonly (string | null)[] {
  const found = messages.get(path);
  if (found === undefined) {
    throw new Error(`${path} 가 린트되지 않았다. 판정 범위 밖이다`);
  }
  return found.map((message) => message.ruleId);
}

describe("판정자가 빨갛게 보는 것", () => {
  for (const { name, path, rule } of RED) {
    test(`${name} 은 ${rule} 로 빨갛다`, () => {
      expect(reported(path)).toContain(rule);
    });
  }
});

describe("판정자가 지나보내는 것", () => {
  for (const { name, path } of GREEN) {
    test(`${name} 은 아무것도 보고되지 않는다`, () => {
      expect(messages.get(path)).toEqual([]);
    });
  }
});

describe("끄기 주석", () => {
  test("끄기 주석이 끄려던 위반은 verify 의 린트 명령에서 그대로 보고되고 빨갛다", () => {
    const run = lintWithVerifyCommand(["cli/next-line.ts", "cli/whole-file.ts"]);

    // 규칙 ID 가 아니라 위반의 메시지를 센다. 규칙이 없는 설정에서는 끄기 주석의 "규칙 정의를 찾을 수 없다"
    // 오류에도 규칙 ID 가 찍혀 거짓 초록이 됐다(2026-09-29).
    expect(run.status).toBe(1);
    expect(run.stdout.split("Unexpected any.").length - 1).toBe(2);
  });

  test("가릴 위반이 없는 끄기 주석 하나만으로도 verify 의 린트 명령은 빨갛다", () => {
    // 인라인 설정 주석은 noInlineConfig 에서 에러가 아니라 경고다. ESLint 는 경고만 있으면 종료 코드 0 이라
    // 경고 0 이 게이트다(--max-warnings 0).
    const run = lintWithVerifyCommand(["cli/lone.ts"]);

    expect(run.status).toBe(1);
    expect(run.stdout).toContain("noInlineConfig");
  });
});

/** package.json 의 lint 스크립트 그대로(`eslint` 뒤의 인자)로 파일을 린트한다. */
function lintWithVerifyCommand(paths: readonly string[]): {
  status: number | null;
  stdout: string;
} {
  const [command, ...args] = lintScript().split(/\s+/);
  expect(command).toBe("eslint");
  const run = spawnSync(
    process.execPath,
    [ESLINT_BIN, ...args, ...paths.map((path) => join(fixture, path))],
    { cwd: WEB, encoding: "utf-8" },
  );
  return { status: run.status, stdout: run.stdout };
}

function lintScript(): string {
  const manifest: unknown = JSON.parse(readFileSync(join(WEB, "package.json"), "utf-8"));
  if (isRecord(manifest) && isRecord(manifest["scripts"])) {
    const lint = manifest["scripts"]["lint"];
    if (typeof lint === "string") {
      return lint;
    }
  }
  throw new Error("package.json 에 scripts.lint 가 없다");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
