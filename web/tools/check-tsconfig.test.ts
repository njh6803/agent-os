// tsconfig 검사(check-tsconfig.ts)의 테스트. 순수 판정은 저장소 밖 임시 트리에서, 저장소 상태는 web/ 에서
// 재고, 변이는 테스트가 사본에 넣는다. 커밋한 tsconfig 에 위반을 두지 않는다.

import { spawnSync } from "node:child_process";
import { cpSync, mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { afterEach, describe, expect, test } from "vitest";
import { check, findTsconfigs, problemsOf, STRICT_FAMILY } from "./check-tsconfig.ts";

const WEB = dirname(import.meta.dirname);
const temporaries: string[] = [];

function temporaryTree(files: Readonly<Record<string, unknown>>): string {
  const root = mkdtempSync(join(tmpdir(), "check-tsconfig-"));
  temporaries.push(root);
  for (const [path, content] of Object.entries(files)) {
    mkdirSync(dirname(join(root, path)), { recursive: true });
    writeFileSync(
      join(root, path),
      typeof content === "string" ? content : JSON.stringify(content),
    );
  }
  return root;
}

afterEach(() => {
  for (const root of temporaries.splice(0)) {
    rmSync(root, { recursive: true, force: true });
  }
});

describe("한 tsconfig 의 판정", () => {
  test("strict: true 만 있으면 통과한다", () => {
    const root = temporaryTree({ "tsconfig.json": { compilerOptions: { strict: true } } });

    expect(problemsOf(join(root, "tsconfig.json"))).toEqual([]);
  });

  test("strict 가 없으면 실패한다", () => {
    const root = temporaryTree({ "tsconfig.json": { compilerOptions: {} } });

    expect(problemsOf(join(root, "tsconfig.json"))).toEqual([
      expect.stringContaining("strict 가 참이 아니다"),
    ]);
  });

  test("strict 가 거짓이면 실패한다", () => {
    const root = temporaryTree({ "tsconfig.json": { compilerOptions: { strict: false } } });

    expect(problemsOf(join(root, "tsconfig.json"))).toEqual([
      expect.stringContaining("strict 가 참이 아니다"),
    ]);
  });

  test("부모의 strict 를 extends 로 물려받으면 통과한다", () => {
    const root = temporaryTree({
      "tsconfig.base.json": { compilerOptions: { strict: true } },
      "app/tsconfig.json": { extends: "../tsconfig.base.json" },
    });

    expect(problemsOf(join(root, "app", "tsconfig.json"))).toEqual([]);
  });

  test("extends 로 물려받은 strict 를 자식이 끄면 실패한다", () => {
    const root = temporaryTree({
      "tsconfig.base.json": { compilerOptions: { strict: true } },
      "app/tsconfig.json": { extends: "../tsconfig.base.json", compilerOptions: { strict: false } },
    });

    expect(problemsOf(join(root, "app", "tsconfig.json"))).toEqual([
      expect.stringContaining("strict 가 참이 아니다"),
    ]);
  });

  test("strict: true 에 strictNullChecks: false 가 있으면 실패한다", () => {
    const root = temporaryTree({
      "tsconfig.json": { compilerOptions: { strict: true, strictNullChecks: false } },
    });

    expect(problemsOf(join(root, "tsconfig.json"))).toEqual([
      expect.stringContaining("strictNullChecks"),
    ]);
  });

  test("부모의 strict 아래에서 자식이 계열 플래그 하나를 끄면 실패한다", () => {
    // tsc --showConfig 가 부모의 strict: true 와 자식의 strictNullChecks: false 를 함께 드러낸 모양(명세 프로브)
    const root = temporaryTree({
      "tsconfig.base.json": { compilerOptions: { strict: true } },
      "app/tsconfig.json": {
        extends: "../tsconfig.base.json",
        compilerOptions: { useUnknownInCatchVariables: false },
      },
    });

    expect(problemsOf(join(root, "app", "tsconfig.json"))).toEqual([
      expect.stringContaining("useUnknownInCatchVariables"),
    ]);
  });

  test("풀 수 없는 extends 는 트레이스백이 아니라 이유로 보고한다", () => {
    const root = temporaryTree({ "tsconfig.json": { extends: "./없는.json" } });

    expect(problemsOf(join(root, "tsconfig.json"))).toEqual([
      expect.stringContaining("읽을 수 없다"),
    ]);
  });

  test("strict 계열 목록은 TypeScript 가 strict 로 켜는 플래그와 같다", () => {
    // 목록은 손으로 적었다. TypeScript 를 올려 계열이 늘면 이 테스트가 먼저 빨개진다.
    const root = temporaryTree({
      "tsconfig.json": { compilerOptions: { strict: true } },
      "a.ts": "export {};\n",
    });
    const tsc = join(WEB, "node_modules", "typescript", "bin", "tsc");

    const shown = spawnSync(process.execPath, [tsc, "--showConfig", "-p", root], {
      encoding: "utf-8",
    });
    const implied = Object.keys(parseCompilerOptions(shown.stdout)).filter(
      (name) => name !== "strict",
    );

    expect(shown.status).toBe(0);
    expect([...STRICT_FAMILY].sort()).toEqual(implied.sort());
  });
});

describe("web 워크스페이스", () => {
  test("web 의 실제 tsconfig 는 전부 통과하고, 검사는 그것들을 실제로 본다", () => {
    const found = findTsconfigs(WEB);

    expect(found).toEqual(expect.arrayContaining(["tsconfig.base.json", "tsconfig.json"]));
    expect(check(WEB)).toEqual([]);
  });

  test("기준 tsconfig 하나를 바꾼 사본은 실패한다", () => {
    const copy = copyOfWebTsconfigs();
    writeFileSync(
      join(copy, "tsconfig.base.json"),
      JSON.stringify({ compilerOptions: { strict: false } }),
    );

    expect(check(copy)).toEqual(
      expect.arrayContaining([expect.stringMatching(/^tsconfig\.base\.json: /)]),
    );
  });

  test("web 아래에 새로 둔 tsconfig 는 목록을 고치지 않아도 검사에 든다", () => {
    const copy = copyOfWebTsconfigs();
    mkdirSync(join(copy, "apps", "new"), { recursive: true });
    writeFileSync(join(copy, "apps", "new", "tsconfig.json"), JSON.stringify({}));

    expect(check(copy)).toEqual([expect.stringMatching(/^apps\/new\/tsconfig\.json: /)]);
  });

  test("node_modules 아래의 tsconfig 는 보지 않는다", () => {
    const root = temporaryTree({
      "tsconfig.json": { compilerOptions: { strict: true } },
      "node_modules/pkg/tsconfig.json": { compilerOptions: { strict: false } },
    });

    expect(findTsconfigs(root)).toEqual(["tsconfig.json"]);
  });

  test("CLI 진입점이 임시 트리의 빨강을 출력하고 1 로 끝난다", () => {
    const root = temporaryTree({ "tsconfig.json": { compilerOptions: { strict: false } } });

    const run = spawnSync(process.execPath, [join(WEB, "tools", "check-tsconfig.ts"), root], {
      encoding: "utf-8",
    });

    expect(run.status).toBe(1);
    expect(run.stdout).toContain("tsconfig.json: strict 가 참이 아니다");
  });
});

function copyOfWebTsconfigs(): string {
  const copy = temporaryTree({});
  for (const path of findTsconfigs(WEB)) {
    mkdirSync(dirname(join(copy, path)), { recursive: true });
    cpSync(join(WEB, path), join(copy, path));
  }
  return copy;
}

function parseCompilerOptions(text: string): Record<string, unknown> {
  const parsed: unknown = JSON.parse(text);
  if (!isRecord(parsed) || !isRecord(parsed["compilerOptions"])) {
    throw new Error(`--showConfig 출력에 compilerOptions 가 없다: ${text}`);
  }
  return parsed["compilerOptions"];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
