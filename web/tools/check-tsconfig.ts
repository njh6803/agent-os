/**
 * tsconfig 검사. tsconfig 의 strict 를 끄는 것도 원칙 III 의 우회다(ADR 0020). 타입 기반 린트는
 * 타입 정보에 기대므로 설정 한 줄이 파일 하나의 단언보다 세다. ESLint 규칙이 아니라 설정을 읽는
 * 검사라 판정자(typescript-eslint)와 별개이고, `pnpm -C web verify` 의 한 단계다.
 *
 * - 검사할 tsconfig 는 목록으로 적지 않고 web/ 아래를 훑어 찾는다(`node_modules` 제외). 목록이면 뒤
 *   티켓의 tsconfig 가 조용히 빠진다(ADR 0013 이 경계한 "범위를 손으로 두 곳에").
 * - 찾은 tsconfig 마다 TypeScript 가 `extends` 를 푼다. 부모의 `strict: true` 아래에서 자식이
 *   `strictNullChecks: false` 한 줄로 계열 하나를 끌 수 있어서, `strict` 가 참인지와 함께 계열의
 *   개별 플래그 가운데 거짓으로 덮인 것이 없는지 본다.
 *
 * 못 보는 것: 명령줄 플래그(`tsc --strict false`)와 도구가 tsconfig 밖에서 넘기는 설정. 파일 목록은
 * 풀지 않는다(`include` 가 아무것도 가리키지 않아도 여기서는 문제가 아니다 — 그것은 타입 검사가 본다).
 *
 * 사용: node tools/check-tsconfig.ts [루트]. 루트를 주지 않으면 web/ 다. 문제가 있으면 한 줄씩 쓰고 1.
 */

import { readdirSync } from "node:fs";
import { dirname, join, relative, sep } from "node:path";
import ts from "typescript";

/**
 * `strict` 가 켜는 플래그. `tsc --showConfig` 가 `strict: true` 에서 풀어 내는 것과 같아야 하고,
 * 테스트가 설치된 TypeScript 와 대조한다.
 */
export const STRICT_FAMILY = [
  "noImplicitAny",
  "noImplicitThis",
  "strictNullChecks",
  "strictFunctionTypes",
  "strictBindCallApply",
  "strictPropertyInitialization",
  "strictBuiltinIteratorReturn",
  "alwaysStrict",
  "useUnknownInCatchVariables",
] as const satisfies readonly (keyof ts.CompilerOptions)[];

const TSCONFIG = /^tsconfig(\..+)?\.json$/;
// "No inputs were found in config file". 파일 목록을 풀지 않으므로 늘 난다.
const NO_INPUTS = 18003;

// 파일 목록은 풀지 않는다. extends 를 따라가는 읽기만 실제 파일시스템으로 한다.
const HOST: ts.ParseConfigHost = {
  useCaseSensitiveFileNames: ts.sys.useCaseSensitiveFileNames,
  readDirectory: () => [],
  fileExists: (path) => ts.sys.fileExists(path),
  readFile: (path) => ts.sys.readFile(path),
};

/** `root` 아래의 tsconfig 경로들. `root` 기준 상대 경로이고 `/` 로 가르며 정렬돼 있다. */
export function findTsconfigs(root: string): string[] {
  const found: string[] = [];
  const walk = (directory: string): void => {
    for (const entry of readdirSync(directory, { withFileTypes: true })) {
      if (entry.isDirectory()) {
        if (entry.name !== "node_modules") {
          walk(join(directory, entry.name));
        }
      } else if (TSCONFIG.test(entry.name)) {
        found.push(relative(root, join(directory, entry.name)).split(sep).join("/"));
      }
    }
  };
  walk(root);
  return found.sort();
}

/** TypeScript 가 푼 옵션에서 strict 계열의 문제. 없으면 비어 있다. */
export function strictProblems(options: ts.CompilerOptions): string[] {
  const problems: string[] = [];
  if (options.strict !== true) {
    problems.push("strict 가 참이 아니다. 기준 tsconfig 를 extends 하거나 strict: true 를 둔다");
  }
  for (const flag of STRICT_FAMILY) {
    if (options[flag] === false) {
      problems.push(`${flag} 가 거짓으로 덮였다. strict 계열을 하나씩 끄는 것도 우회다`);
    }
  }
  return problems;
}

/** tsconfig 파일 하나의 문제. `extends` 는 TypeScript 가 푼다. */
export function problemsOf(path: string): string[] {
  const read = ts.readConfigFile(path, (file) => ts.sys.readFile(file));
  if (read.error !== undefined) {
    return [`읽을 수 없다: ${flatten(read.error)}`];
  }
  const parsed = ts.parseJsonConfigFileContent(read.config, HOST, dirname(path), undefined, path);
  const errors = parsed.errors.filter((error) => error.code !== NO_INPUTS);
  if (errors.length > 0) {
    return errors.map((error) => `읽을 수 없다: ${flatten(error)}`);
  }
  return strictProblems(parsed.options);
}

/** `root` 아래 tsconfig 전부의 문제. 한 줄마다 `상대 경로: 이유` 다. */
export function check(root: string): string[] {
  return findTsconfigs(root).flatMap((path) =>
    problemsOf(join(root, path)).map((problem) => `${path}: ${problem}`),
  );
}

function flatten(diagnostic: ts.Diagnostic): string {
  return ts.flattenDiagnosticMessageText(diagnostic.messageText, " ");
}

if (import.meta.main) {
  const root = process.argv[2] ?? dirname(import.meta.dirname);
  const problems = check(root);
  for (const problem of problems) {
    console.log(problem);
  }
  process.exitCode = problems.length > 0 ? 1 : 0;
}
