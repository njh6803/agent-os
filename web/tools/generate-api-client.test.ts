// 생성 스크립트(generate-api-client.ts)의 테스트. 재귀 Json 변환은 순수 함수로, 생성물 최신성은 저장소 상태와
// 계약 사본의 변이로 잰다. 변이는 저장소 밖 임시 사본에 넣는다. 커밋한 계약과 생성물을 건드리지 않는다.

import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { afterEach, describe, expect, test } from "vitest";
import { CONTRACT, GENERATED, generate, replaceRecursiveJson } from "./generate-api-client.ts";

const WEB = dirname(import.meta.dirname);
const TOOL = join(import.meta.dirname, "generate-api-client.ts");

// openapi-typescript 7.13.0 이 낸 재귀 Json 의 자리 그대로다. 들여쓰기도 생성기의 것이다.
const 재귀_Json = [
  'Json: string | number | boolean | components["schemas"]["Json"][] | {',
  '            [key: string]: components["schemas"]["Json"];',
  "        } | null;",
].join("\n");

const temporaries: string[] = [];

afterEach(() => {
  for (const root of temporaries.splice(0)) {
    rmSync(root, { recursive: true, force: true });
  }
});

describe("재귀 Json 변환", () => {
  test("openapi-typescript 가 낸 재귀 Json 자리만 unknown 이 되고 나머지 바이트는 그대로다", () => {
    const 앞 = "export interface components {\n    schemas: {\n        ";
    const 뒤 = '\n        Health: {\n            status: "ok";\n        };\n    };\n}\n';

    expect(replaceRecursiveJson(앞 + 재귀_Json + 뒤)).toBe(`${앞}Json: unknown;${뒤}`);
  });

  test("재귀 Json 자리가 없으면 조용히 지나가지 않고 실패한다", () => {
    expect(() => replaceRecursiveJson("export interface components {}\n")).toThrow(
      /재귀 Json 자리/,
    );
  });

  test("재귀 Json 자리가 둘이면 어느 것을 바꿀지 고르지 않고 실패한다", () => {
    expect(() => replaceRecursiveJson(`${재귀_Json}\n${재귀_Json}\n`)).toThrow(/재귀 Json 자리/);
  });
});

/** 설명 한 줄을 바꾼 계약 사본에 최신성 검사를 CLI 로 돌린다. */
function checkWithEditedDescription(): { status: number | null; stdout: string } {
  const 설명 = "살아 있다는 것만 답한다. 내부 구성을 싣지 않는다.";
  const 계약 = readFileSync(CONTRACT, "utf-8");
  expect(계약.split(설명).length - 1).toBe(1);
  const root = mkdtempSync(join(tmpdir(), "generate-api-client-"));
  temporaries.push(root);
  const 사본 = join(root, "openapi.json");
  writeFileSync(사본, 계약.replace(설명, "살아 있는지만 답한다."));
  const run = spawnSync(process.execPath, [TOOL, "--check", 사본], { cwd: WEB, encoding: "utf-8" });
  return { status: run.status, stdout: run.stdout };
}

describe("생성물 최신성", () => {
  test("이 저장소의 생성물은 루트 openapi.json 에서 다시 생성한 것과 바이트까지 같다", async () => {
    expect(await generate(CONTRACT)).toBe(readFileSync(GENERATED, "utf-8"));
  });

  test("openapi.json 의 설명 한 줄을 바꾼 사본에서 최신성 검사가 빨갛고 다시 생성하라고 말한다", () => {
    const run = checkWithEditedDescription();

    expect(run.status).toBe(1);
    expect(run.stdout).toContain("pnpm -C web run generate:api-client");
  });

  test("최신성 검사는 어긋남을 찾아도 커밋된 생성물을 고쳐 쓰지 않는다", async () => {
    checkWithEditedDescription();

    // 실행 직전의 파일과 비교하지 않는다. 앞 테스트가 이미 고쳐 썼다면 둘이 같아 초록이 된다.
    expect(readFileSync(GENERATED, "utf-8")).toBe(await generate(CONTRACT));
  });
});
