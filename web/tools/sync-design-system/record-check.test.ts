// 기록과 확인 명령을 스크립트 진입으로 돌린 테스트. 스킬이 하듯 보고 JSON 을 파일로 이어 주며 첫 올리기, 확인, 웹
// 편집과 덮어쓰기, 여러 호출로 나뉜 올리기를 차례로 본다(design-reverse-sync 명세 "이음매", "기록", "확인", "올리기").

import { spawnSync } from "node:child_process";
import { cpSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { afterEach, beforeEach, describe, expect, test } from "vitest";
import { buildTokensJson } from "./build.ts";
import { isRecord } from "./io.ts";

const WEB = dirname(dirname(import.meta.dirname));
const MAIN = join(import.meta.dirname, "main.ts");
const CSS = readFileSync(join(WEB, "packages", "ui", "src", "styles", "theme.css"), "utf-8");

let scratch = "";

beforeEach(() => {
  scratch = mkdtempSync(join(tmpdir(), "sync-record-check-"));
});

afterEach(() => {
  rmSync(scratch, { recursive: true, force: true });
});

interface Outcome {
  readonly status: number | null;
  readonly report: Readonly<Record<string, unknown>>;
}

function invoke(...args: string[]): Outcome {
  const result = spawnSync(process.execPath, [MAIN, ...args], { encoding: "utf-8", cwd: scratch });
  const lines = result.stdout.split("\n").filter((line) => line !== "");
  const report: unknown = JSON.parse(lines.at(-1) ?? "null");
  if (!isRecord(report)) {
    throw new Error(`보고가 객체가 아니다: ${result.stdout}${result.stderr}`);
  }
  return { status: result.status, report };
}

/** 성공한 보고를 파일에 적어 다음 명령에 넘긴다. */
function saved(name: string, outcome: Outcome): string {
  expect(outcome).toMatchObject({ status: 0, report: { ok: true } });
  writeFileSync(join(scratch, name), JSON.stringify(outcome.report));
  return name;
}

function put(folder: string, files: Readonly<Record<string, string>>): void {
  for (const [path, text] of Object.entries(files)) {
    const absolute = join(scratch, folder, ...path.split("/"));
    mkdirSync(dirname(absolute), { recursive: true });
    writeFileSync(absolute, text);
  }
}

const README = "# Agent OS 디자인 시스템\n";
const BUTTON = "# 버튼\n";
const GUIDE = "# 웹 디자인\n";

const INDEX = {
  v: 1,
  title: "Agent OS",
  assetGroups: {},
  blobs: {},
  docs: { readme: "project/README.md", sections: ["project/guidelines/web-design.md"] },
  sections: {},
};

/** 빌드 산출. 아티팩트의 `project/` 아래에 놓인다. */
function bundle(folder: string, overrides: Readonly<Record<string, string>> = {}): string {
  put(folder, {
    "tokens.json": buildTokensJson(CSS),
    "README.md": README,
    "components/Button/README.md": BUTTON,
    "components/Button/index.html": "<p>버튼</p>",
    "guidelines/web-design.md": GUIDE,
    ...overrides,
  });
  return folder;
}

/** 받은 폴더. 산출을 아티팩트 경로로 옮기고 색인과 기록을 더한다. */
function webFolder(
  folder: string,
  from: string,
  editing: "on" | "off",
  record: string | null,
): string {
  cpSync(join(scratch, from), join(scratch, folder, "project"), { recursive: true });
  put(folder, {
    "project/design-system.json": JSON.stringify(editing === "off" ? { ...INDEX, editing } : INDEX),
  });
  if (record !== null) {
    cpSync(join(scratch, record), join(scratch, folder, "project", "sync-record.json"));
  }
  return folder;
}

/**
 * 스킬처럼 확인을 돌린다. `paths` 가 빌 때까지 낸 경로를 받는다. 폴더에 이미 둔 파일은 받은 것이고, 낸 경로는 폴더에
 * 없으니 없다는 까닭으로 읽지 못한 것으로 적는다.
 */
function judged(folder: string): Outcome {
  const reads = `${folder}-reads.json`;
  const absent: string[] = [];
  writeFileSync(join(scratch, reads), JSON.stringify({ absent }));
  for (let round = 0; round < 3; round += 1) {
    const paths = invoke("check", "paths", "--web", folder, "--reads", reads);
    expect(paths.status).toBe(0);
    const listed = Array.isArray(paths.report.paths)
      ? paths.report.paths.map((path: unknown) => String(path))
      : [];
    if (listed.length === 0) {
      return invoke("check", "judge", "--web", folder, "--reads", reads);
    }
    absent.push(...listed);
    writeFileSync(join(scratch, reads), JSON.stringify({ absent }));
  }
  throw new Error("받을 경로가 세 번째에도 비지 않았다");
}

describe("기록과 확인 명령", () => {
  test("첫 올리기의 기록 뒤 확인은 웹 편집 없음이고, 웹이 README 를 고치고 지침을 지우면 덮어쓰기만 올린다", () => {
    bundle("bundle");
    writeFileSync(join(scratch, "index.json"), JSON.stringify(INDEX));
    writeFileSync(join(scratch, "sha.json"), "{}");
    mkdirSync(join(scratch, "empty"));

    const first = judged(webFolder("before", "empty", "off", null));
    expect(first.report).toMatchObject({ ok: true, result: "beforeRecord" });

    const plan = invoke(
      "record",
      "plan",
      "--local",
      "bundle",
      "--artifact-sha256",
      "sha.json",
      "--check",
      saved("check.json", first),
    );
    expect(plan.report).toMatchObject({
      ok: true,
      send: [
        "project/README.md",
        "project/components/Button/README.md",
        "project/components/Button/index.html",
        "project/guidelines/web-design.md",
        "project/tokens.json",
      ],
      delete: [],
    });

    const written = invoke(
      "record",
      "write",
      "--local",
      "bundle",
      "--plan",
      saved("plan.json", plan),
      "--index",
      "index.json",
      "--out",
      "record.json",
      "--commit",
      "abc1234",
      "--at",
      "2026-10-26T12:00:00.000Z",
    );
    expect(written.report).toMatchObject({ ok: true, files: 5, pending: false });

    const clean = judged(webFolder("after", "bundle", "on", "record.json"));
    expect(clean.report).toMatchObject({
      ok: true,
      result: "clean",
      editing: "on",
      record: "ok",
      pending: null,
    });

    const edited = judged(webFolder("edited", "bundle", "on", "record.json"));
    expect(edited.report).toMatchObject({ result: "clean" });
    put("edited", { "project/README.md": `${README}웹에서 더한 줄.\n` });
    rmSync(join(scratch, "edited", "project", "guidelines", "web-design.md"));
    const found = judged("edited");
    expect(found.report).toMatchObject({
      result: "edited",
      tokens: [],
      files: [
        { path: "project/README.md", change: "changed" },
        { path: "project/guidelines/web-design.md", change: "removed" },
      ],
    });

    const refused = invoke(
      "record",
      "plan",
      "--local",
      "bundle",
      "--record",
      "record.json",
      "--check",
      saved("found.json", found),
    );
    expect(refused).toMatchObject({
      status: 1,
      report: {
        ok: false,
        error: {
          kind: "usage",
          message: "확인이 웹 편집을 찾았다. 사람이 덮어쓰기를 고른 때만 --overwrite 로 올린다",
        },
      },
    });

    const overwrite = invoke(
      "record",
      "plan",
      "--local",
      "bundle",
      "--record",
      "record.json",
      "--check",
      "found.json",
      "--overwrite",
    );
    expect(overwrite.report).toMatchObject({
      ok: true,
      send: ["project/README.md", "project/guidelines/web-design.md"],
      revert: ["project/README.md"],
      webRemoved: ["project/guidelines/web-design.md"],
      webAdded: [],
    });
  });

  test("여러 호출로 나뉜 올리기가 멈추면 보낸 파일은 웹 편집이 아니고, 다시 한 올리기가 이어 적는다", () => {
    bundle("bundle");
    writeFileSync(join(scratch, "index.json"), JSON.stringify(INDEX));
    writeFileSync(join(scratch, "sha.json"), "{}");
    const plan = invoke("record", "plan", "--local", "bundle", "--artifact-sha256", "sha.json");
    invoke(
      "record",
      "write",
      "--local",
      "bundle",
      "--plan",
      saved("plan.json", plan),
      "--index",
      "index.json",
      "--out",
      "record.json",
      "--commit",
      "abc1234",
      "--at",
      "2026-10-26T12:00:00.000Z",
    );

    bundle("next", {
      "README.md": `${README}새 안내.\n`,
      "guidelines/web-design.md": `${GUIDE}새 지침.\n`,
    });
    const nextPlan = invoke("record", "plan", "--local", "next", "--record", "record.json");
    expect(nextPlan.report).toMatchObject({
      send: ["project/README.md", "project/guidelines/web-design.md"],
    });
    const firstCall = invoke(
      "record",
      "write",
      "--local",
      "next",
      "--plan",
      saved("next-plan.json", nextPlan),
      "--index",
      "index.json",
      "--out",
      "pending.json",
      "--record",
      "record.json",
      "--first-call",
    );
    expect(firstCall.report).toMatchObject({ ok: true, pending: true });

    // 첫 호출은 README 만 보내고 멈췄다.
    webFolder("stopped", "bundle", "on", "pending.json");
    put("stopped", { "project/README.md": `${README}새 안내.\n` });
    const stopped = judged("stopped");
    expect(stopped.report).toMatchObject({
      result: "clean",
      pending: { "project/README.md": "sent", "project/guidelines/web-design.md": "unsent" },
    });

    const again = invoke(
      "record",
      "plan",
      "--local",
      "next",
      "--record",
      "pending.json",
      "--check",
      saved("stopped.json", stopped),
    );
    expect(again.report).toMatchObject({
      landed: ["project/README.md"],
      send: ["project/guidelines/web-design.md"],
    });
    const last = invoke(
      "record",
      "write",
      "--local",
      "next",
      "--plan",
      saved("again.json", again),
      "--index",
      "index.json",
      "--out",
      "last.json",
      "--record",
      "pending.json",
      "--commit",
      "def5678",
      "--at",
      "2026-10-26T13:00:00.000Z",
    );
    expect(last.report).toMatchObject({ ok: true, pending: false });

    webFolder("done", "next", "on", "last.json");
    expect(judged("done").report).toMatchObject({ result: "clean", pending: null });
  });

  test("빌드가 필요한지는 바뀐 경로의 줄 목록으로 가른다", () => {
    writeFileSync(
      join(scratch, "changed.txt"),
      ".claude/rules/web-design.md\r\nweb/packages/ui/src/Button.tsx\n\n",
    );

    expect(invoke("record", "needs-build", "--changed", "changed.txt").report).toMatchObject({
      ok: true,
      needed: true,
      because: [{ path: "web/packages/ui/src/Button.tsx", reason: "package" }],
    });
  });

  test("따옴표로 싼 경로 줄은 받지 않는다", () => {
    const quoted = '"web/packages/ui/src/\\353\\262\\204\\355\\212\\274.tsx"';
    writeFileSync(join(scratch, "changed.txt"), `${quoted}\n`);

    expect(invoke("record", "needs-build", "--changed", "changed.txt")).toMatchObject({
      status: 1,
      report: {
        ok: false,
        error: {
          kind: "input",
          message: `changed.txt 가 따옴표로 싼 줄 ${quoted} 을 든다. git -c core.quotePath=false diff --name-only 로 짓는다`,
        },
      },
    });
  });

  test("웹 편집 있음 보고에 바뀐 파일의 배열이 없으면 덮어쓰기를 계획하지 않는다", () => {
    const report = {
      command: "check",
      ok: true,
      action: "judge",
      result: "edited",
      tokens: [],
      pending: null,
    };
    writeFileSync(join(scratch, "no-files.json"), JSON.stringify(report));

    expect(
      invoke(
        "record",
        "plan",
        "--local",
        "b",
        "--record",
        "r",
        "--check",
        "no-files.json",
        "--overwrite",
      ),
    ).toMatchObject({
      status: 1,
      report: {
        ok: false,
        error: {
          kind: "input",
          message: "no-files.json 가 files 로 바뀐 파일의 배열을 들지 않는다",
        },
      },
    });
  });

  test.each([
    [
      "모르는 하위 명령",
      ["record", "erase"],
      "record 는 plan, needs-build, write 가운데 하나를 받는다",
    ],
    [
      "하위 명령이 받지 않는 인자",
      ["record", "needs-build", "--changed", "x", "--out", "y"],
      "record needs-build 는 --out 를 받지 않는다",
    ],
    [
      "첫 호출과 커밋을 함께 준 기록",
      [
        "record",
        "write",
        "--local",
        "b",
        "--plan",
        "p",
        "--index",
        "i",
        "--out",
        "o",
        "--first-call",
        "--commit",
        "abc1234",
        "--at",
        "2026-10-26",
      ],
      "record write 에는 --first-call 이나 --commit <SHA> 와 --at <시각> 가운데 하나를 준다",
    ],
    [
      "기록과 sha256 표를 함께 준 계획",
      ["record", "plan", "--local", "b", "--record", "r", "--artifact-sha256", "s"],
      "record plan 에는 --record <기록> 와 --artifact-sha256 <sha256 표> 가운데 하나를 준다",
    ],
    [
      "확인 보고 없는 덮어쓰기",
      ["record", "plan", "--local", "b", "--record", "r", "--overwrite"],
      "--overwrite 에는 되돌릴 것을 고를 --check <확인 보고> 가 있어야 한다",
    ],
    [
      "받은 폴더 없는 확인",
      ["check", "judge"],
      "check judge 에는 --web <받은 폴더> 가 있어야 한다",
    ],
    ["모르는 확인 동작", ["check", "erase", "--web", "w"], "check 는 paths 나 judge 하나를 받는다"],
  ])("%s 는 usage 오류로 끝난다", (_name, args, message) => {
    expect(invoke(...args)).toMatchObject({
      status: 1,
      report: { ok: false, error: { kind: "usage", message } },
    });
  });
});
