// 판정자(eslint.config.mjs)의 변이 테스트. 원칙 III 의 TS 판정자(ADR 0020)와 web 의 층 경계(ADR 0021).
//
// 위반을 담은 코드는 이 테스트가 web/ 아래 임시 트리에 쓰고 끝나면 지운다. 앞 실행이 끝나기 전에 멈춰 남긴 트리는
// 시작할 때 지운다(tools/judge-trees.ts). 커밋한 파일에 위반을 두면 그
// 파일을 판정에서 빼는 목록이 생긴다(ADR 0013 이 경계한 모양).
//
// 임시 트리는 워크스페이스의 자리(apps/<이름>/…, packages/<이름>/…)를 흉내 내고, 앱과 패키지마다 기준
// tsconfig 를 extends 하는 자기 tsconfig 를 둔다. 타입 기반 규칙의 프로젝트 서비스는 파일에서 가장 가까운
// tsconfig 를 찾는다. 어느 tsconfig 에도 들지 않는 파일은 규칙이 아니라 파싱 오류로 빨개진다(2026-09-29
// 실측). 그래서 사례마다 "빨갛다"가 아니라 기대한 규칙이 보고됐는지를 본다.

import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { dirname, join, relative, sep } from "node:path";
import { ESLint, type Linter } from "eslint";
import { afterAll, beforeAll, describe, expect, test } from "vitest";
import { GENERATED } from "./tools/generate-api-client.ts";
import { makeJudgeTree, removeLeftoverJudgeTrees } from "./tools/judge-trees.ts";

const WEB = import.meta.dirname;
const ESLINT_BIN = join(WEB, "node_modules", "eslint", "bin", "eslint.js");
const API_CLIENT = join(WEB, "packages", "api-client");

// 자기 tsconfig 를 두는 자리. 임시 트리 뿌리에는 tsconfig 가 없다.
const PROJECTS = ["apps/admin", "apps/widget", "packages/api-client", "packages/ui", "cli"];

// 경로 참조(`/// <reference path>`). 디자인 시스템 패키지의 Icon.tsx 에서만 푼다.
const PATH_REFERENCE = '/// <reference path="./glyphs.d.ts" />\nexport const 아이콘 = 1;\n';

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
  "apps/admin/lib/event-source.ts": 'export const 연결 = new EventSource("/api/runs");\n',
  "apps/admin/lib/window-event-source.ts":
    'export const 연결 = new window.EventSource("/api/runs");\n',
  "apps/admin/lib/xhr.ts": "export const 요청 = new XMLHttpRequest();\n",
  "apps/admin/lib/raw-client.ts":
    'import createClient from "openapi-fetch";\n\nexport const 만든다 = createClient;\n',
  "apps/admin/components/organisms/DeepClient.ts":
    'import { createAdminClient } from "../../../../packages/api-client/src/clients";\n\nexport const 관리 = createAdminClient;\n',
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
  "apps/admin/components/atoms/Api.ts":
    'import { createAdminClient } from "@agent-os/api-client";\n\nexport const 관리 = createAdminClient;\n',
  "apps/admin/components/molecules/Api.ts":
    'import { createAdminClient } from "@agent-os/api-client";\n\nexport const 관리 = createAdminClient;\n',
  "apps/admin/components/organisms/Api.ts":
    'import { createAdminClient } from "@agent-os/api-client";\n\nexport const 관리 = createAdminClient;\n',
  "apps/admin/components/organisms/Panel.ts":
    'import { 라벨 } from "../atoms/Label";\n\nexport const 판 = 라벨;\n',
  // organisms 는 요청 함수가 든 api 도메인과 hooks/queries 를 부르지 않으므로 barrel 의 판정은 부를 수 있는 pages 에서 잰다.
  "apps/admin/components/pages/DeepApi.ts":
    'import { 실행_목록 } from "../../api/runs/listRuns";\n\nexport const 깊이 = 실행_목록;\n',
  "apps/admin/components/pages/DeepQuery.ts":
    'import { 실행_훅 } from "../../hooks/queries/runs/useRuns";\n\nexport const 깊이 = 실행_훅;\n',
  "apps/admin/components/organisms/Query.ts":
    'import { 실행_훅 } from "../../hooks/queries/runs";\n\nexport const 훅 = 실행_훅;\n',
  "apps/admin/components/organisms/Store.ts":
    'import { 토큰 } from "../../stores/tokens";\n\nexport const 받은_토큰 = 토큰;\n',
  "apps/admin/components/organisms/InlineType.ts":
    'import { type 알림 } from "../../stores/tokens";\n\nexport type 받은_알림 = 알림;\n',
  "apps/admin/components/organisms/TypeOnly.ts":
    'import type { 알림 } from "../../stores/tokens";\n\nexport type 받은_알림 = 알림;\n',
  "apps/admin/components/templates/Query.ts":
    'import { 실행_훅 } from "../../hooks/queries/runs";\n\nexport const 훅 = 실행_훅;\n',
  "apps/admin/components/templates/Runs.ts":
    'import { 실행_목록 } from "../../api/runs";\n\nexport const 실행들 = 실행_목록;\n',
  "apps/admin/components/molecules/Store.ts":
    'import { 토큰 } from "../../stores/tokens";\n\nexport const 받은_토큰 = 토큰;\n',
  "apps/admin/components/pages/Connected.ts":
    'import { 실행_훅 } from "../../hooks/queries/runs";\nimport { 토큰 } from "../../stores/tokens";\n\nexport const 연결 = [실행_훅, 토큰];\n',
  "apps/admin/components/organisms/DeepType.ts":
    'import { 실행_종류 } from "../../types/run/kinds";\n\nexport const 깊이 = 실행_종류;\n',
  "apps/admin/components/organisms/Runs.ts":
    'import { 실행_목록 } from "../../api/runs";\n\nexport const 실행들 = 실행_목록;\n',
  "apps/admin/components/organisms/RunsType.ts":
    'import type { 실행_목록 } from "../../api/runs";\n\nexport type 목록 = typeof 실행_목록;\n',
  "apps/admin/components/organisms/Failure.ts":
    'import { 풀이 } from "../../api/failure";\n\nexport const 실패 = 풀이;\n',
  "apps/admin/components/pages/Runs.ts":
    'import { 실행_목록 } from "../../api/runs";\n\nexport const 실행들 = 실행_목록;\n',
  "apps/admin/components/pages/Home.ts": "export const 홈 = 1;\n",
  "apps/admin/components/pages/Remote.ts":
    'import { 위젯 } from "../../../widget/lib/widget";\n\nexport const 원격 = 위젯;\n',
  "apps/admin/components/templates/Shell.ts": "export const 틀 = 1;\n",
  "apps/admin/api/failure/index.ts": "export const 풀이 = 1;\n",
  "apps/admin/api/runs/index.ts": 'export { 실행_목록 } from "./listRuns";\n',
  "apps/admin/api/runs/listRuns.ts": "export const 실행_목록 = 1;\n",
  "apps/admin/hooks/queries/runs/index.ts": 'export { 실행_훅 } from "./useRuns";\n',
  "apps/admin/hooks/queries/runs/useRuns.ts": "export const 실행_훅 = 1;\n",
  "apps/admin/stores/tokens.ts":
    "export const 토큰 = 1;\n\nexport interface 알림 {\n  readonly 글: string;\n}\n",
  "apps/admin/types/run/index.ts": 'export { 실행_종류 } from "./kinds";\n',
  "apps/admin/types/run/kinds.ts": 'export const 실행_종류 = ["완료", "실패"] as const;\n',
  "apps/admin/app/page.ts":
    'import { 홈 } from "../components/pages/Home";\nimport { 틀 } from "../components/templates/Shell";\n\nexport const 첫_화면 = [홈, 틀];\n',
  "apps/admin/app/runs/page.ts":
    'import { 카드 } from "../../components/organisms/Card";\n\nexport const 화면 = 카드;\n',
  "apps/admin/app/layout.ts":
    'import { createAdminClient } from "@agent-os/api-client";\n\nexport const 틀 = createAdminClient;\n',
  "apps/admin/app/server/page.ts":
    'import { readFileSync } from "node:fs";\n\nexport const 읽기 = readFileSync;\n',
  "apps/admin/lib/boolean-param.ts":
    'export function 고른다(이름: string, 덮어쓴다: boolean): string {\n  return 덮어쓴다 ? 이름 : "";\n}\n',
  "apps/admin/lib/optional-boolean-param.ts":
    "export function 고른다(덮어쓴다?: boolean): boolean {\n  return 덮어쓴다 === true;\n}\n",
  "apps/admin/lib/union-boolean-param.ts":
    "export function 고른다(덮어쓴다: boolean | undefined): boolean {\n  return 덮어쓴다 === true;\n}\n",
  "apps/admin/lib/default-boolean-param.ts":
    "export function 고른다(덮어쓴다 = false): boolean {\n  return 덮어쓴다;\n}\n",
  "apps/admin/lib/annotated-default-boolean-param.ts":
    "const 기본값 = true;\n\nexport function 고른다(덮어쓴다: boolean = 기본값): boolean {\n  return 덮어쓴다;\n}\n",
  "apps/admin/lib/literal-default-boolean-param.ts":
    "export function 고른다(덮어쓴다: boolean = false): boolean {\n  return 덮어쓴다;\n}\n",
  "apps/admin/lib/true-default-boolean-param.ts":
    "export function 고른다(덮어쓴다 = true): boolean {\n  return !덮어쓴다;\n}\n",
  "apps/admin/lib/alias-default-boolean-param.ts":
    "type 켜짐 = boolean;\n\nexport function 고른다(덮어쓴다: 켜짐 = false): boolean {\n  return 덮어쓴다;\n}\n",
  "apps/admin/lib/arrow-boolean-param.ts":
    "export const 고른다 = (덮어쓴다: boolean): boolean => !덮어쓴다;\n",
  "apps/admin/lib/method-boolean-param.ts":
    "export const 판정 = {\n  고른다(덮어쓴다: boolean): boolean {\n    return !덮어쓴다;\n  },\n};\n",
  "apps/admin/lib/options-param.ts":
    "export function 고른다({ 덮어쓴다 }: { readonly 덮어쓴다: boolean }): boolean {\n  return 덮어쓴다;\n}\n",
  "apps/admin/lib/value-callback.ts":
    "export type 바뀜 = (켜짐: boolean) => void;\n\nexport const 뒤집힘 = [true].map((켜짐) => !켜짐);\n",
  "apps/admin/lib/other-default-param.ts":
    'export function 고른다(이름 = "true", 수 = 1): string {\n  return 이름 + String(수);\n}\n',
  "apps/admin/lib/setter-param.ts":
    "export class 상자 {\n  #켜짐 = false;\n\n  get 켜짐(): boolean {\n    return this.#켜짐;\n  }\n\n  set 켜짐(값: boolean) {\n    this.#켜짐 = 값;\n  }\n}\n",
  "apps/admin/lib/unseen-boolean-param.ts": [
    "export declare function 선언(덮어쓴다: boolean): boolean;\n",
    "export interface 받는쪽 {\n  고른다(덮어쓴다: boolean): void;\n}\n",
    "export function 참만(값: true): boolean {\n  return 값;\n}\n",
    "export function 섞임(값: string | (boolean | number)): string {\n  return String(값);\n}\n",
    "export function 목록(값들: readonly boolean[], 약속: Promise<boolean>): number {\n  void 약속;\n  return 값들.length;\n}\n",
    "export function 식(값 = !0): boolean {\n  return 값;\n}\n",
  ].join("\n"),
  "apps/admin/lib/kinds.ts": 'export const 종류 = ["plugins", "runs"] as const;\n',
  "apps/admin/lib/kinds.test-d.ts":
    "// @ts-expect-error: 숫자는 문자열 자리에 들어가지 않는다\nexport const 틀린_값: string = 1;\n",
  "apps/admin/lib/bare.test-d.ts": "// @ts-expect-error\nexport const 틀린_값: string = 1;\n",
  "apps/admin/app/settings/page.ts":
    'import { 종류 } from "../../lib/kinds";\n\nexport const 설정 = 종류;\n',
  "apps/widget/lib/widget.ts": "export const 위젯 = 1;\n",
  "packages/api-client/src/client.ts":
    'export function 부른다(): Promise<Response> {\n  return fetch("/api/runs");\n}\n',
  "packages/api-client/src/global-fetch.ts":
    'export function 부른다(): Promise<Response> {\n  return globalThis.fetch("/api/runs");\n}\n',
  "packages/ui/src/components/atoms/glyphs.d.ts":
    'declare module "glyphs/*" {\n  const 그림: number;\n  export default 그림;\n}\n',
  "packages/ui/src/components/atoms/Icon.tsx": PATH_REFERENCE,
  "packages/ui/src/components/atoms/Button.tsx": PATH_REFERENCE,
  "apps/admin/components/atoms/Glyph.tsx": PATH_REFERENCE,
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
  { name: "EventSource", path: "apps/admin/lib/event-source.ts", rule: "no-restricted-globals" },
  {
    name: "window 로 부른 EventSource",
    path: "apps/admin/lib/window-event-source.ts",
    rule: "no-restricted-properties",
  },
  { name: "XMLHttpRequest", path: "apps/admin/lib/xhr.ts", rule: "no-restricted-globals" },
  {
    name: "앱이 openapi-fetch 로 클라이언트를 직접 만든다",
    path: "apps/admin/lib/raw-client.ts",
    rule: "no-restricted-imports",
  },
  {
    name: "상대 경로로 생성 클라이언트 패키지 안을 import",
    path: "apps/admin/components/organisms/DeepClient.ts",
    rule: "no-restricted-imports",
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
    path: "apps/admin/components/pages/DeepApi.ts",
    rule: BOUNDARIES,
  },
  {
    name: "hooks/queries 도메인의 barrel 을 거치지 않는 import",
    path: "apps/admin/components/pages/DeepQuery.ts",
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
  {
    name: "app/ 이 노드 내장 모듈을 import",
    path: "apps/admin/app/server/page.ts",
    rule: BOUNDARIES,
  },
  {
    name: "atoms 가 생성 클라이언트 패키지를 import",
    path: "apps/admin/components/atoms/Api.ts",
    rule: BOUNDARIES,
  },
  {
    name: "molecules 가 생성 클라이언트 패키지를 import",
    path: "apps/admin/components/molecules/Api.ts",
    rule: BOUNDARIES,
  },
  {
    name: "molecules 가 stores 를 import",
    path: "apps/admin/components/molecules/Store.ts",
    rule: BOUNDARIES,
  },
  // 서버 데이터와 토큰을 읽는 것은 pages 다(ADR 0021 의 2026-10-27 이력). organisms 와 templates 는 props 로 받는다.
  {
    name: "organisms 가 생성 클라이언트 패키지를 import",
    path: "apps/admin/components/organisms/Api.ts",
    rule: BOUNDARIES,
  },
  {
    name: "organisms 가 hooks/queries 를 barrel 로 import",
    path: "apps/admin/components/organisms/Query.ts",
    rule: BOUNDARIES,
  },
  {
    name: "organisms 가 stores 를 import",
    path: "apps/admin/components/organisms/Store.ts",
    rule: BOUNDARIES,
  },
  {
    // verbatimModuleSyntax 에서 이 줄은 지워지지 않고 모듈을 싣는다. 타입 지정자만 든 것은 import type 뿐이다.
    name: "organisms 가 같은 줄의 type 지정자로 stores 를 import",
    path: "apps/admin/components/organisms/InlineType.ts",
    rule: BOUNDARIES,
  },
  {
    name: "templates 가 hooks/queries 를 barrel 로 import",
    path: "apps/admin/components/templates/Query.ts",
    rule: BOUNDARIES,
  },
  {
    name: "organisms 가 요청 함수가 든 api 도메인을 barrel 로 import",
    path: "apps/admin/components/organisms/Runs.ts",
    rule: BOUNDARIES,
  },
  {
    name: "templates 가 요청 함수가 든 api 도메인을 barrel 로 import",
    path: "apps/admin/components/templates/Runs.ts",
    rule: BOUNDARIES,
  },
  // 생성 클라이언트 패키지는 fetch 를 직접 부르지 않는다. openapi-fetch 가 부른다. 그래서 예외가 없다.
  {
    name: "생성 클라이언트 패키지 안의 전역 fetch",
    path: "packages/api-client/src/client.ts",
    rule: "no-restricted-globals",
  },
  {
    name: "생성 클라이언트 패키지 안에서 globalThis 로 부른 fetch",
    path: "packages/api-client/src/global-fetch.ts",
    rule: "no-restricted-properties",
  },
  {
    name: "디자인 시스템 패키지의 Icon.tsx 밖의 경로 참조",
    path: "packages/ui/src/components/atoms/Button.tsx",
    rule: "@typescript-eslint/triple-slash-reference",
  },
  {
    name: "앱의 atoms 에 둔 경로 참조",
    path: "apps/admin/components/atoms/Glyph.tsx",
    rule: "@typescript-eslint/triple-slash-reference",
  },
];

// 불리언 매개변수는 다른 금지 구문과 규칙 ID 를 나눠 쓰므로 메시지의 표지까지 보고, 매개변수 하나가 한 번만 보고되는지도 본다.
const BOOLEAN_PARAMETER = "불리언 매개변수";

const BOOLEAN_PARAMETER_RED: readonly { readonly name: string; readonly path: string }[] = [
  { name: "주석이 boolean 인 매개변수", path: "apps/admin/lib/boolean-param.ts" },
  { name: "선택 매개변수 ?: boolean", path: "apps/admin/lib/optional-boolean-param.ts" },
  { name: "boolean 을 든 유니온 매개변수", path: "apps/admin/lib/union-boolean-param.ts" },
  { name: "주석 없이 기본값이 false 인 매개변수", path: "apps/admin/lib/default-boolean-param.ts" },
  {
    name: "주석이 boolean 이고 기본값이 상수인 매개변수",
    path: "apps/admin/lib/annotated-default-boolean-param.ts",
  },
  {
    name: "주석이 boolean 이고 기본값이 false 인 매개변수",
    path: "apps/admin/lib/literal-default-boolean-param.ts",
  },
  {
    name: "주석 없이 기본값이 true 인 매개변수",
    path: "apps/admin/lib/true-default-boolean-param.ts",
  },
  {
    name: "주석이 boolean 의 별칭이고 기본값이 false 인 매개변수",
    path: "apps/admin/lib/alias-default-boolean-param.ts",
  },
  { name: "화살표 함수의 boolean 매개변수", path: "apps/admin/lib/arrow-boolean-param.ts" },
  { name: "메서드의 boolean 매개변수", path: "apps/admin/lib/method-boolean-param.ts" },
];

const GREEN: readonly { readonly name: string; readonly path: string }[] = [
  {
    name: "이름 붙인 옵션 객체로 받은 boolean",
    path: "apps/admin/lib/options-param.ts",
  },
  {
    name: "함수 타입의 boolean 매개변수와 추론된 콜백 매개변수",
    path: "apps/admin/lib/value-callback.ts",
  },
  {
    name: "불리언이 아닌 기본값(문자열 true, 수)",
    path: "apps/admin/lib/other-default-param.ts",
  },
  { name: "세터의 boolean 매개변수", path: "apps/admin/lib/setter-param.ts" },
  {
    name: "설정 주석이 보지 않는다고 적은 자리(본문 없는 선언, 메서드 시그니처, 리터럴 타입 true, 유니온 속 유니온, 배열과 제네릭 인자, 리터럴이 아닌 기본값)",
    path: "apps/admin/lib/unseen-boolean-param.ts",
  },
  { name: "as const", path: "apps/admin/lib/kinds.ts" },
  { name: "타입 테스트 파일의 설명 붙은 @ts-expect-error", path: "apps/admin/lib/kinds.test-d.ts" },
  { name: "barrel 을 거친 import", path: "apps/admin/components/pages/Runs.ts" },
  { name: "organisms 가 atoms 를 import", path: "apps/admin/components/organisms/Panel.ts" },
  { name: "app/ 이 pages 와 templates 를 import", path: "apps/admin/app/page.ts" },
  {
    name: "organisms 가 stores 의 타입만 import type 으로 받는다",
    path: "apps/admin/components/organisms/TypeOnly.ts",
  },
  {
    name: "pages 가 hooks/queries 와 stores 를 import",
    path: "apps/admin/components/pages/Connected.ts",
  },
  {
    name: "organisms 가 api 도메인의 타입만 import type 으로 받는다",
    path: "apps/admin/components/organisms/RunsType.ts",
  },
  {
    name: "organisms 가 요청 함수가 없는 api/failure 를 import",
    path: "apps/admin/components/organisms/Failure.ts",
  },
  {
    name: "디자인 시스템 패키지의 Icon.tsx 가 아이콘 모듈 선언을 경로로 참조",
    path: "packages/ui/src/components/atoms/Icon.tsx",
  },
];

let fixture = "";
const messages = new Map<string, readonly Linter.LintMessage[]>();

beforeAll(async () => {
  // 앞 실행이 afterAll 전에 멈춰 남긴 트리를 junction 을 따라가지 않고 지운다(tools/judge-trees.ts).
  removeLeftoverJudgeTrees(WEB);
  fixture = makeJudgeTree(WEB);
  for (const project of PROJECTS) {
    mkdirSync(join(fixture, project), { recursive: true });
    writeFileSync(join(fixture, project, "tsconfig.json"), projectTsconfig(project));
  }
  for (const [path, source] of Object.entries(SOURCES)) {
    mkdirSync(dirname(join(fixture, path)), { recursive: true });
    writeFileSync(join(fixture, path), source);
  }
  // 앱이 워크스페이스 의존성으로 생성 클라이언트를 들면 pnpm 이 이렇게 링크한다(윈도우는 junction). 링크가 없으면
  // import 가 풀리지 않아 초록 사례가 타입 기반 규칙으로 빨개진다.
  mkdirSync(join(fixture, "apps/admin/node_modules/@agent-os"), { recursive: true });
  symlinkSync(
    API_CLIENT,
    join(fixture, "apps/admin/node_modules/@agent-os/api-client"),
    "junction",
  );
  const results = await judge.lintFiles([join(fixture, "apps"), join(fixture, "packages")]);
  for (const result of results) {
    messages.set(relative(fixture, result.filePath).split(sep).join("/"), result.messages);
  }
});

afterAll(() => {
  if (fixture !== "") {
    rmSync(fixture, { recursive: true, force: true });
  }
});

// 판정자 하나를 모든 테스트가 쓴다. 커밋된 파일의 자리에서 재는 테스트는 위반을 파일에 쓰지 않고 lintText 로 그 경로에 넣는다.
const judge = new ESLint({ cwd: WEB });

// TypeScript 프로그램을 새로 세우는 테스트(판정자가 관리 화면 앱의 자리를 처음 린트하는 것, verify 의 린트 명령을 자식으로
// 띄우는 것)의 제한. 프로그램을 세우는 동안은 이벤트 루프가 막혀 vitest 의 제한이 테스트를 끊지 못하고, 끝난 뒤에야 넘김으로
// 알린다. 그래서 60초 제한은 멈춘 테스트를 막지 못한 채 부하에서 빨갛기만 했다(pre-commit 에서 67·110·144초, ADR 0035 의
// 2026-10-20 이력 "TypeScript 프로그램을 처음 세우는 eslint 테스트에 넉넉한 제한을 준다"). 자식 eslint 는 같은 값으로 끊는다.
const PROGRAM_TIMEOUT_MS = 600_000;

async function ruleIdsAt(path: string, source: string): Promise<(string | null)[]> {
  const [result] = await judge.lintText(source, { filePath: path });
  return (result?.messages ?? []).map((message) => message.ruleId);
}

function linted(path: string): readonly Linter.LintMessage[] {
  const found = messages.get(path);
  if (found === undefined) {
    throw new Error(`${path} 가 린트되지 않았다. 판정 범위 밖이다`);
  }
  return found;
}

function reported(path: string): readonly (string | null)[] {
  return linted(path).map((message) => message.ruleId);
}

describe("판정자가 빨갛게 보는 것", () => {
  for (const { name, path, rule } of RED) {
    test(`${name} 은 ${rule} 로 빨갛다`, () => {
      expect(reported(path)).toContain(rule);
    });
  }
});

describe("판정자가 불리언 매개변수로 빨갛게 보는 것", () => {
  for (const { name, path } of BOOLEAN_PARAMETER_RED) {
    test(`${name} 은 ${RESTRICTED_SYNTAX} 의 불리언 매개변수로 한 번 빨갛다`, () => {
      const found = linted(path)
        .filter((message) => message.ruleId === RESTRICTED_SYNTAX)
        .map((message) => message.message);
      expect(found).toEqual([expect.stringContaining(BOOLEAN_PARAMETER)]);
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

// 임시 트리가 아니라 커밋된 파일의 자리에서 잰다.
describe("실제 생성 클라이언트 자리", () => {
  test("커밋된 생성물은 판정 범위 안이고 아무것도 보고되지 않는다", async () => {
    // 판정에서 빠진 파일을 이름으로 주면 ESLint 는 "무시된 파일" 경고 하나를 낸다. 빈 목록이 범위 안이라는 뜻이다.
    const [result] = await judge.lintFiles([GENERATED]);

    expect(result?.messages).toEqual([]);
  });

  test("커밋된 생성물의 재귀 Json 자리에 any 가 들면 판정자가 빨갛게 본다", async () => {
    const generated = readFileSync(GENERATED, "utf-8");
    expect(generated.split("Json: unknown;").length - 1).toBe(1);

    const found = await ruleIdsAt(GENERATED, generated.replace("Json: unknown;", "Json: any;"));

    expect(found).toContain("@typescript-eslint/no-explicit-any");
  });

  test("생성 클라이언트 패키지의 실제 파일은 openapi-fetch 를 import 해도 아무것도 보고되지 않는다", async () => {
    // 클라이언트 셋을 만드는 유일한 자리라 판정자가 여기서만 그 import 를 푼다. 임시 트리에는 openapi-fetch 가
    // 설치되지 않아 타입 기반 규칙이 풀리지 않은 import 를 빨갛게 보므로 실제 자리에서 잰다.
    const path = join(API_CLIENT, "src", "clients.ts");
    const source = readFileSync(path, "utf-8");
    expect(source).toContain('from "openapi-fetch"');

    expect(await ruleIdsAt(path, source)).toEqual([]);
  });

  test("생성 클라이언트 패키지의 실제 파일에서도 전역 fetch 는 빨갛다", async () => {
    const path = join(API_CLIENT, "src", "clients.ts");
    const source = `${readFileSync(path, "utf-8")}\nexport const 부른다 = (): Promise<Response> => fetch("/api/runs");\n`;

    expect(await ruleIdsAt(path, source)).toContain("no-restricted-globals");
  });
});

// 관리 화면 앱의 실제 자리. 임시 트리에는 next 와 react 가 설치되지 않고 tsconfig 도 손으로 지은 것이라, 실제
// node_modules 와 Next 가 읽는 tsconfig 에 기대는 것은 여기서 잰다. 파일이 있는 자리만 쓴다. 없는 경로를 주면
// 프로젝트 서비스가 그 파일을 찾지 못해 규칙이 아니라 파싱 오류가 난다(2026-09-30 실측, 일지 2026-09-30-01).
describe("실제 관리 화면 자리", { timeout: PROGRAM_TIMEOUT_MS }, () => {
  const ADMIN = join(WEB, "apps", "admin");
  const LAYOUT = join(ADMIN, "app", "layout.tsx");

  test("app/ 이 next 와 react 를 import 하는 것은 아무것도 보고되지 않는다", async () => {
    // 앱의 node_modules 로 풀린 next 는 workspace-app 요소로도 분류된다. 로컬로 좁히기 전에는 이것이 빨갰다.
    const source = [
      'import type { Metadata } from "next";',
      'import { notFound } from "next/navigation";',
      'import type { ReactNode } from "react";',
      "",
      "export const 정보: Metadata = {};",
      "export const 없음 = notFound;",
      "export type 자식 = ReactNode;",
      "",
    ].join("\n");

    expect(await ruleIdsAt(LAYOUT, source)).toEqual([]);
  });

  test("app/ 이 next·react 밖의 외부 모듈을 import 하면 빨갛다", async () => {
    const source =
      'import { createPortal } from "react-dom";\n\nexport const 포털 = createPortal;\n';

    expect(await ruleIdsAt(LAYOUT, source)).toContain(BOUNDARIES);
  });

  test("app/ 이 pages·templates 밖의 앱 파일을 import 하면 빨갛다", async () => {
    const source =
      'import { DEFAULT_HOST } from "../tools/loopback.ts";\n\nexport const 호스트 = DEFAULT_HOST;\n';

    expect(await ruleIdsAt(LAYOUT, source)).toContain(BOUNDARIES);
  });

  test("타입 기반 규칙이 앱의 실제 파일에서 돈다", async () => {
    // 파싱 오류(규칙 ID null)가 아니라 타입 정보가 있어야 도는 규칙이 보고된다.
    const path = join(ADMIN, "components", "pages", "HomePage.tsx");
    const source = 'export const 수: number = JSON.parse("1");\n';

    expect(await ruleIdsAt(path, source)).toEqual(["@typescript-eslint/no-unsafe-assignment"]);
  });

  // 서버 데이터를 읽는 것은 pages 다(ADR 0021 의 2026-10-27 이력). 임시 트리에는 swr 가 설치되지 않아 여기서 잰다.
  const ORGANISM = join(ADMIN, "components", "organisms", "PluginList.tsx");

  test("organisms 가 swr 를 import 하면 빨갛다", async () => {
    const source = 'import useSWR from "swr";\n\nexport const 읽기 = useSWR;\n';

    expect(await ruleIdsAt(ORGANISM, source)).toContain(BOUNDARIES);
  });

  test("organisms 가 swr 의 서브패스를 import 하면 빨갛다", async () => {
    const source =
      'import useSWRInfinite from "swr/infinite";\n\nexport const 더_읽기 = useSWRInfinite;\n';

    expect(await ruleIdsAt(ORGANISM, source)).toContain(BOUNDARIES);
  });

  test("organisms 가 swr 의 타입만 import type 으로 받는 것은 아무것도 보고되지 않는다", async () => {
    const source =
      'import type { SWRResponse } from "swr";\n\nexport type 읽은_것 = SWRResponse<number>;\n';

    expect(await ruleIdsAt(ORGANISM, source)).toEqual([]);
  });

  test("앱의 요청 함수 자리에서 openapi-fetch 로 클라이언트를 직접 만들면 빨갛다", async () => {
    const path = join(ADMIN, "api", "plugins", "index.ts");
    const source = `${readFileSync(path, "utf-8")}\nimport createClient from "openapi-fetch";\nexport const 만든다 = createClient;\n`;

    expect(await ruleIdsAt(path, source)).toContain("no-restricted-imports");
  });
});

// 판정자가 빼는 것은 저장소의 .gitignore 가 무시하는 것(빌드 산출물)뿐이다. 그 파일에 소스를 덮는 줄이 들어가도
// 판정 범위가 조용히 줄지 않게, git 이 추적하는 파일로 잰다.
describe("판정 범위", () => {
  const LINTED = /\.(ts|tsx|mts|cts|js|mjs|cjs)$/;

  test("git 이 추적하는 web/ 의 코드 파일은 하나도 판정에서 빠지지 않는다", async () => {
    // pre-commit 이 워크트리에서 돌면 git 이 훅 자식에 GIT_DIR 을 내보낸다. GIT_WORK_TREE 없는 GIT_DIR 은 cwd 를
    // 작업 트리의 뿌리로 삼아 경로가 web/ 기준이 아니게 되고, 이 테스트가 빨개졌다(2026-09-30, 일지 2026-09-30-06).
    // tests/conftest.py 가 파이썬 쪽에서 벗기는 것과 같은 까닭이다. 여기서는 GIT_ 로 시작하는 것을 다 벗긴다.
    const env = Object.fromEntries(
      Object.entries(process.env).filter(([name]) => !name.startsWith("GIT_")),
    );
    const tracked = spawnSync("git", ["ls-files", "-z", "--", "."], {
      cwd: WEB,
      encoding: "utf-8",
      env,
    });
    expect(tracked.status).toBe(0);
    const files = tracked.stdout.split("\0").filter((path) => LINTED.test(path));
    // 이 파일 자신이 있다. git 이 아무것도 내놓지 않는데 초록이 되지 않게 한다.
    expect(files).toContain("eslint.config.test.ts");

    const ignored: string[] = [];
    for (const path of files) {
      if (await judge.isPathIgnored(join(WEB, path))) {
        ignored.push(path);
      }
    }

    expect(ignored).toEqual([]);
  });

  test("Next 의 빌드 산출물은 판정에서 빠진다", async () => {
    // .next/types/validator.ts 는 Next 가 빌드마다 다시 쓰고 as 와 @ts-ignore 를 싣는다(2026-09-30 실측, 일지 2026-09-30-01).
    const built = join(WEB, "apps", "admin", ".next", "types", "validator.ts");

    expect(await judge.isPathIgnored(built)).toBe(true);
  });

  test("git 이 추적하기 전인 소스 자리도 .gitignore 의 파이썬 산출물 이름에 걸리지 않는다", async () => {
    // 추적 파일 가드는 git 도 무시해 추적되지 못한 파일을 보지 못한다. 앵커 없는 traces/ 는 관리 화면의 실행 목록
    // 자리(티켓 07)를 git 과 판정자에서 함께 뺐다(2026-09-30 셀프 리뷰가 찾았다).
    for (const name of ["traces", "dist"]) {
      const source = join(WEB, "apps", "admin", "app", name, "page.tsx");

      expect(await judge.isPathIgnored(source)).toBe(false);
    }
  });
});

describe("끄기 주석", { timeout: PROGRAM_TIMEOUT_MS }, () => {
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
    { cwd: WEB, encoding: "utf-8", timeout: PROGRAM_TIMEOUT_MS },
  );
  if (run.error !== undefined) {
    throw run.error;
  }
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
