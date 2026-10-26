// 스크립트 진입의 테스트. 명령의 입력과 출력은 파일이고, 보고는 표준 출력의 JSON 하나다. 실패는 0 이 아닌 종료 코드와
// 그 JSON 의 오류 칸이다(design-reverse-sync 명세 "이음매").

import { spawnSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { afterEach, beforeEach, describe, expect, test } from "vitest";
import { buildTokensJson } from "./build.ts";
import { comparisonHash, readTokens } from "./tokens-json.ts";

const WEB = dirname(dirname(import.meta.dirname));
const MAIN = join(import.meta.dirname, "main.ts");
const CSS = readFileSync(join(WEB, "packages", "ui", "src", "styles", "theme.css"), "utf-8");

let scratch = "";

beforeEach(() => {
  scratch = mkdtempSync(join(tmpdir(), "sync-design-system-"));
});

afterEach(() => {
  rmSync(scratch, { recursive: true, force: true });
});

interface Outcome {
  readonly status: number | null;
  readonly report: unknown;
  readonly lines: number;
}

function invoke(...args: string[]): Outcome {
  const result = spawnSync(process.execPath, [MAIN, ...args], { encoding: "utf-8", cwd: scratch });
  const lines = result.stdout.split("\n").filter((line) => line !== "");
  const report: unknown = JSON.parse(lines.at(-1) ?? "null");
  return { status: result.status, report, lines: lines.length };
}

/** 보고의 오류 문구. 없으면 빈 글이다. */
function errorMessage(report: unknown): string {
  if (typeof report !== "object" || report === null || !("error" in report)) {
    return "";
  }
  const { error } = report;
  if (typeof error !== "object" || error === null || !("message" in error)) {
    return "";
  }
  return typeof error.message === "string" ? error.message : "";
}

describe("스크립트 진입", () => {
  test("짓기는 지은 tokens.json 을 출력 파일에 쓰고 보고 JSON 하나를 낸 뒤 0 으로 끝난다", () => {
    const css = join(scratch, "theme.css");
    writeFileSync(css, CSS);
    const outcome = invoke("build", "--css", css, "--out", "out/tokens.json");
    const written = readFileSync(join(scratch, "out", "tokens.json"), "utf-8");
    const expected = buildTokensJson(CSS);
    const parsed: unknown = JSON.parse(expected);

    expect(written).toBe(expected);
    expect(outcome).toEqual({
      status: 0,
      lines: 1,
      report: {
        command: "build",
        ok: true,
        out: join(scratch, "out", "tokens.json"),
        themes: 8,
        tokens: 112,
        hash: comparisonHash(readTokens(parsed)),
      },
    });
  });

  test("CSS 를 주지 않으면 패키지의 디자인 토큰 CSS 를 읽는다", () => {
    const outcome = invoke("build", "--out", "tokens.json");

    expect(outcome.status).toBe(0);
    expect(readFileSync(join(scratch, "tokens.json"), "utf-8")).toBe(buildTokensJson(CSS));
  });

  test("한도를 넘는 입력은 1 로 끝나고 보고의 오류 칸에 limit 을 낸다", () => {
    const css = join(scratch, "theme.css");
    const filler = Array.from(
      { length: 54 },
      (_, index) => `  --spacing-${String(100 + index)}: 1px;\n`,
    ).join("");
    writeFileSync(css, CSS.replace("  --spacing-0: 0px;", `${filler}  --spacing-0: 0px;`));
    const outcome = invoke("build", "--css", css, "--out", "tokens.json");

    expect(outcome.status).toBe(1);
    expect(outcome.report).toMatchObject({ command: "build", ok: false, error: { kind: "limit" } });
    expect(errorMessage(outcome.report)).toContain("간격 토큰 수가 61 개로");
  });

  test("읽을 수 없는 입력 파일은 input 오류다", () => {
    const outcome = invoke("build", "--css", join(scratch, "없다.css"), "--out", "tokens.json");

    expect(outcome.status).toBe(1);
    expect(outcome.report).toMatchObject({ command: "build", ok: false, error: { kind: "input" } });
    expect(errorMessage(outcome.report)).toContain("없다.css 를 읽을 수 없다");
  });

  test("출력 파일을 쓸 수 없으면 output 오류다", () => {
    // 출력 경로가 폴더(작업 폴더)라 쓰지 못한다.
    const outcome = invoke("build", "--out", ".");

    expect(outcome.status).toBe(1);
    expect(outcome.report).toMatchObject({
      command: "build",
      ok: false,
      error: { kind: "output" },
    });
    expect(errorMessage(outcome.report)).toContain(". 를 쓸 수 없다");
  });

  test("출력 파일을 주지 않으면 usage 오류다", () => {
    const outcome = invoke("build");

    expect(outcome.status).toBe(1);
    expect(outcome.report).toMatchObject({ command: "build", ok: false, error: { kind: "usage" } });
    expect(errorMessage(outcome.report)).toContain("--out <tokens.json>");
  });

  test("모르는 옵션은 usage 오류다", () => {
    const outcome = invoke("build", "--bogus", "x", "--out", "tokens.json");

    expect(outcome.status).toBe(1);
    expect(outcome.report).toMatchObject({
      command: "build",
      ok: false,
      error: { kind: "usage" },
    });
    expect(errorMessage(outcome.report)).toContain("bogus");
  });

  test("모르는 명령은 usage 오류이고 아는 명령을 문구에 든다", () => {
    // 명령 이름에 build 가 들지 않아야 문구의 build 가 아는 명령 목록에서 온 것이다.
    const outcome = invoke("deploy");

    expect(outcome.status).toBe(1);
    expect(outcome.report).toMatchObject({
      command: "deploy",
      ok: false,
      error: { kind: "usage" },
    });
    expect(errorMessage(outcome.report)).toContain("build");
  });
});
