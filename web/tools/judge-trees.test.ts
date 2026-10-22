// 판정자 임시 트리 청소(judge-trees.ts)의 테스트. 남은 트리는 저장소 밖 임시 디렉터리에 흉내 내고, 링크 대상도
// 그 안에 둔다. 청소가 링크를 따라가더라도 지워지는 것은 이 테스트가 만든 파일뿐이다.

import { spawnSync } from "node:child_process";
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  symlinkSync,
  writeFileSync,
} from "node:fs";
import { tmpdir } from "node:os";
import { basename, dirname, join } from "node:path";
import { afterEach, describe, expect, test } from "vitest";
import { MARKER, makeJudgeTree, removeLeftoverJudgeTrees } from "./judge-trees.ts";

const WEB = dirname(import.meta.dirname);
const TOOL = join(import.meta.dirname, "judge-trees.ts");
const temporaries: string[] = [];

/** web/ 자리와 그 바깥의 링크 대상 패키지를 함께 둔 임시 디렉터리. */
function temporaryRoot(): { web: string; outside: string } {
  const root = mkdtempSync(join(tmpdir(), "judge-trees-"));
  temporaries.push(root);
  const web = join(root, "web");
  const outside = join(root, "api-client");
  mkdirSync(web);
  mkdirSync(outside);
  writeFileSync(join(outside, "package.json"), "{}\n");
  return { web, outside };
}

/**
 * 판정자 테스트가 쓰는 모양의 트리. 표지, 위반 사례 파일 하나, 앱의 node_modules 에서 패키지로 가는 junction 하나.
 */
function leftoverTree(web: string, name: string, outside: string): string {
  const tree = join(web, name);
  mkdirSync(join(tree, "apps/admin/lib"), { recursive: true });
  writeFileSync(join(tree, MARKER), "");
  writeFileSync(join(tree, "apps/admin/lib/any.ts"), "export const 값: any = 1;\n");
  mkdirSync(join(tree, "apps/admin/node_modules/@agent-os"), { recursive: true });
  symlinkSync(outside, join(tree, "apps/admin/node_modules/@agent-os/api-client"), "junction");
  return tree;
}

afterEach(() => {
  for (const root of temporaries.splice(0)) {
    rmSync(root, { recursive: true, force: true });
  }
});

describe("남은 판정자 트리 지우기", () => {
  test("앞 실행이 남긴 판정자 트리를 지우고 그 경로를 돌려준다", () => {
    const { web, outside } = temporaryRoot();
    const tree = leftoverTree(web, "judge-O2Bymh", outside);

    expect(removeLeftoverJudgeTrees(web)).toEqual([tree]);
    expect(existsSync(tree)).toBe(false);
  });

  test("트리 안의 junction 을 따라가지 않아 링크 대상의 파일이 남는다", () => {
    const { web, outside } = temporaryRoot();
    leftoverTree(web, "judge-vZhAvt", outside);

    removeLeftoverJudgeTrees(web);

    expect(readFileSync(join(outside, "package.json"), "utf-8")).toBe("{}\n");
  });

  test("남은 트리가 여럿이면 모두 지운다", () => {
    const { web, outside } = temporaryRoot();
    const trees = [
      leftoverTree(web, "judge-aaaaaa", outside),
      leftoverTree(web, "judge-B1c2D3", outside),
    ];

    expect(removeLeftoverJudgeTrees(web).toSorted()).toEqual(trees.toSorted());
  });

  test("남은 트리가 없으면 아무것도 지우지 않는다", () => {
    const { web } = temporaryRoot();

    expect(removeLeftoverJudgeTrees(web)).toEqual([]);
  });

  test("판정자 트리 이름의 모양이 아닌 디렉터리는 표지가 있어도 남긴다", () => {
    const { web } = temporaryRoot();
    const kept = [
      "judge-notes",
      "judge-abcdefg",
      "judge-ab-cde",
      "xjudge-abcdef",
      "Judge-abcdef",
      "judge",
    ];
    for (const name of kept) {
      mkdirSync(join(web, name));
      writeFileSync(join(web, name, MARKER), "");
    }

    expect(removeLeftoverJudgeTrees(web)).toEqual([]);
    for (const name of kept) {
      expect(existsSync(join(web, name))).toBe(true);
    }
  });

  test("이름이 판정자 트리의 모양이어도 표지가 없는 디렉터리는 안의 파일과 함께 남긴다", () => {
    // 사람이 지은 여섯 글자 이름(judge-config)도 이름의 모양에는 맞는다. 표지가 디렉터리이거나 링크여도 남긴다.
    const { web, outside } = temporaryRoot();
    mkdirSync(join(web, "judge-config"));
    writeFileSync(join(web, "judge-config", "notes.md"), "커밋하지 않은 메모\n");
    mkdirSync(join(web, "judge-Dir123", MARKER), { recursive: true });
    writeFileSync(join(outside, MARKER), "");
    mkdirSync(join(web, "judge-Lnk123"));
    symlinkSync(join(outside, MARKER), join(web, "judge-Lnk123", MARKER), "file");

    expect(removeLeftoverJudgeTrees(web)).toEqual([]);
    expect(readFileSync(join(web, "judge-config", "notes.md"), "utf-8")).toBe(
      "커밋하지 않은 메모\n",
    );
    expect(existsSync(join(web, "judge-Dir123", MARKER))).toBe(true);
    expect(existsSync(join(web, "judge-Lnk123"))).toBe(true);
  });

  test("판정자 트리 이름의 링크는 링크도 대상도 남긴다", () => {
    const { web, outside } = temporaryRoot();
    writeFileSync(join(outside, MARKER), "");
    symlinkSync(outside, join(web, "judge-Qw12Er"), "junction");

    expect(removeLeftoverJudgeTrees(web)).toEqual([]);
    expect(existsSync(join(web, "judge-Qw12Er", "package.json"))).toBe(true);
    expect(existsSync(join(outside, "package.json"))).toBe(true);
  });

  test("판정자 트리 이름의 파일은 남긴다", () => {
    const { web } = temporaryRoot();
    writeFileSync(join(web, "judge-abc123"), "메모\n");

    expect(removeLeftoverJudgeTrees(web)).toEqual([]);
    expect(existsSync(join(web, "judge-abc123"))).toBe(true);
  });
});

describe("새 판정자 트리", () => {
  test("새로 만든 판정자 트리는 다음 실행이 남은 트리로 지우는 이름과 표지를 갖는다", () => {
    const { web } = temporaryRoot();
    const tree = makeJudgeTree(web);

    expect(dirname(tree)).toBe(web);
    expect(basename(tree)).toMatch(/^judge-/);
    expect(existsSync(join(tree, MARKER))).toBe(true);
    expect(removeLeftoverJudgeTrees(web)).toEqual([tree]);
  });
});

describe("명령으로 부르기", () => {
  test("명령은 준 자리의 남은 트리를 지우고 지운 경로를 한 줄씩 쓴다", () => {
    const { web, outside } = temporaryRoot();
    const tree = leftoverTree(web, "judge-O2Bymh", outside);

    const run = spawnSync(process.execPath, [TOOL, web], { encoding: "utf-8" });

    expect(run.status).toBe(0);
    expect(run.stdout).toContain(tree);
    expect(existsSync(tree)).toBe(false);
    expect(existsSync(join(outside, "package.json"))).toBe(true);
  });

  test("명령은 루트를 주지 않으면 자기 tools 폴더의 부모를 web 으로 보고 거기의 남은 트리를 지운다", () => {
    // verify 의 청소 단계는 루트 없이 부른다. 진짜 web/ 를 건드리지 않게 모듈을 임시 web/tools/ 에 옮겨 부르고,
    // 작업 디렉터리도 임시 자리에 둔다.
    const { web, outside } = temporaryRoot();
    const tree = leftoverTree(web, "judge-O2Bymh", outside);
    mkdirSync(join(web, "tools"));
    const copied = join(web, "tools", "judge-trees.ts");
    copyFileSync(TOOL, copied);

    const run = spawnSync(process.execPath, [copied], { cwd: dirname(web), encoding: "utf-8" });

    expect(run.status).toBe(0);
    expect(run.stdout).toContain(tree);
    expect(existsSync(tree)).toBe(false);
  });

  test("verify 는 린트와 Prettier 보다 먼저 남은 판정자 트리를 지운다", () => {
    // 남은 트리의 위반 사례 파일은 린트를, 한 줄로 쓴 tsconfig.json 은 Prettier 를 먼저 빨갛게 해, 시험 단계의
    // beforeAll 까지 가지 못한다.
    const steps = verifySteps();
    const cleaning = steps.indexOf("pnpm run clean:judge-trees");

    expect(cleaning).toBeGreaterThanOrEqual(0);
    expect(cleaning).toBeLessThan(steps.indexOf("pnpm run lint"));
    expect(cleaning).toBeLessThan(steps.indexOf("pnpm run format"));
    expect(scripts()["clean:judge-trees"]).toBe("node tools/judge-trees.ts");
  });
});

function verifySteps(): string[] {
  const verify = scripts()["verify"];
  if (typeof verify !== "string") {
    throw new Error("package.json 에 scripts.verify 가 없다");
  }
  return verify.split(" && ");
}

function scripts(): Record<string, unknown> {
  const manifest: unknown = JSON.parse(readFileSync(join(WEB, "package.json"), "utf-8"));
  if (isRecord(manifest) && isRecord(manifest["scripts"])) {
    return manifest["scripts"];
  }
  throw new Error("package.json 에 scripts 가 없다");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
