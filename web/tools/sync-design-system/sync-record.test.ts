// 기록의 꼴과 다음 기록 짓기의 테스트(design-reverse-sync 명세 "기록"과 그 2026-10-22 주석 둘, Testing Decisions
// "기록"에서 `claim` 을 넣고 비우는 것(06)을 뺀 것).

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { describe, expect, test } from "vitest";
import { buildTokensFile, buildTokensJson } from "./build.ts";
import { CommandError } from "./command.ts";
import { fileHash } from "./file-hash.ts";
import {
  indexLists,
  nextRecord,
  readRecord,
  RECORD_LIMIT,
  serializeRecord,
  type FileEntry,
  type IndexLists,
  type RecordChanges,
  type SyncRecord,
} from "./sync-record.ts";
import { jsonValue } from "./io.ts";
import type { JsonValue } from "./tokens-json.ts";

const WEB = dirname(dirname(import.meta.dirname));
const CSS = readFileSync(join(WEB, "packages", "ui", "src", "styles", "theme.css"), "utf-8");
const TOKENS = buildTokensJson(CSS);

function bytes(text: string): Uint8Array {
  return new TextEncoder().encode(text);
}

function entry(path: string, text: string): FileEntry {
  const data = bytes(text);
  return { hash: fileHash(path, data), bytes: data.byteLength };
}

/** JSON 글을 JSON 값으로 푼다. */
function parsed(text: string): JsonValue {
  const raw: unknown = JSON.parse(text);
  const value = jsonValue(raw);
  if (value === undefined) {
    throw new Error("JSON 값이 아니다");
  }
  return value;
}

function jsonObject(value: JsonValue): value is { readonly [key: string]: JsonValue } {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

/** 던진 오류. 던지지 않으면 null. */
function caught(run: () => unknown): unknown {
  try {
    run();
  } catch (error) {
    return error;
  }
  return null;
}

const INDEX: IndexLists = {
  assetGroups: { notes: { files: {}, name: "notes", order: [] } },
  blobs: {},
  docs: { readme: "project/README.md", sections: ["project/guidelines/index.md"] },
  sections: {},
};

function changes(partial: Partial<RecordChanges>): RecordChanges {
  return { send: [], landed: [], unchanged: [], delete: [], gone: [], ...partial };
}

/** 앞 기록. 카드 둘, README, tokens.json 을 올렸다. */
function previousRecord(overrides: Partial<SyncRecord> = {}): SyncRecord {
  return {
    v: 1,
    commit: "1111111",
    at: "2026-10-26T00:00:00.000Z",
    files: new Map([
      ["project/README.md", entry("project/README.md", "# 사람 몫\n")],
      [
        "project/components/Button/README.md",
        entry("project/components/Button/README.md", "옛 버튼\n"),
      ],
      ["project/components/Card/README.md", entry("project/components/Card/README.md", "카드\n")],
      ["project/tokens.json", entry("project/tokens.json", TOKENS)],
    ]),
    baseline: parsed(TOKENS),
    index: INDEX,
    pending: null,
    claim: null,
    ...overrides,
  };
}

const OUTPUT = new Map<string, Uint8Array>([
  ["project/components/Button/README.md", bytes("새 버튼\n")],
  ["project/tokens.json", bytes(TOKENS)],
]);

describe("다음 기록", () => {
  test("앞 기록에 이번에 보낸 것과 지운 것을 합치고 해시는 보낸 파일의 로컬 바이트로 잰다", () => {
    const next = nextRecord({
      previous: previousRecord(),
      output: OUTPUT,
      artifact: new Map(),
      changes: changes({
        send: ["project/components/Button/README.md"],
        unchanged: ["project/tokens.json"],
        delete: ["project/components/Card/README.md"],
      }),
      index: INDEX,
      call: { kind: "last", commit: "2222222", at: "2026-10-26T01:00:00.000Z" },
    });

    expect([...next.files.keys()]).toEqual([
      "project/README.md",
      "project/components/Button/README.md",
      "project/tokens.json",
    ]);
    expect(next.files.get("project/components/Button/README.md")).toEqual(
      entry("project/components/Button/README.md", "새 버튼\n"),
    );
    expect(next.files.get("project/README.md")).toEqual(entry("project/README.md", "# 사람 몫\n"));
    expect(next.commit).toBe("2222222");
    expect(next.at).toBe("2026-10-26T01:00:00.000Z");
    expect(next.pending).toBeNull();
  });

  test("기록 자신, 색인, 페이지가 다시 짓는 파일은 해시하지 않고 색인은 그림과 문서 목록만 적는다", () => {
    const output = new Map<string, Uint8Array>([
      ...OUTPUT,
      ["project/sync-record.json", bytes("{}")],
      ["project/design-system.json", bytes("{}")],
      ["project/tokens.css", bytes(":root{}")],
      ["project/manifest.json", bytes("{}")],
      ["project/api/tokens.md", bytes("# 토큰\n")],
    ]);
    const next = nextRecord({
      previous: null,
      output,
      artifact: new Map([["project/migration-map.json", bytes("{}")]]),
      changes: changes({ send: [...output.keys()] }),
      index: indexLists({ ...INDEX, title: "제목", editing: "off", lastChange: { via: "x" } }),
      call: { kind: "last", commit: "2222222", at: "2026-10-26T01:00:00.000Z" },
    });

    expect([...next.files.keys()]).toEqual([
      "project/components/Button/README.md",
      "project/migration-map.json",
      "project/tokens.json",
    ]);
    expect(next.index).toEqual(INDEX);
  });

  test("색인에 없는 목록 칸은 null 로 적는다", () => {
    expect(indexLists({ docs: { readme: "project/README.md" } })).toEqual({
      assetGroups: null,
      blobs: null,
      docs: { readme: "project/README.md" },
      sections: null,
    });
  });

  test("기준본은 이번 산출의 tokens.json 내용이다", () => {
    const changed = TOKENS.replace('"#f4f8fb"', '"#f0f4f8"');
    expect(changed).not.toBe(TOKENS);
    const next = nextRecord({
      previous: previousRecord(),
      output: new Map([["project/tokens.json", bytes(changed)]]),
      artifact: new Map(),
      changes: changes({ send: ["project/tokens.json"] }),
      index: INDEX,
      call: { kind: "last", commit: "2222222", at: "2026-10-26T01:00:00.000Z" },
    });

    expect(next.baseline).toEqual(parsed(changed));
  });

  test("여러 호출의 첫 기록은 pending 에 목표를 넣고 파일 해시와 기준본은 앞 기록 그대로 둔다", () => {
    const previous = previousRecord();
    const target = { ...INDEX, docs: { readme: "project/README.md", sections: [] } };
    const first = nextRecord({
      previous,
      output: OUTPUT,
      artifact: new Map(),
      changes: changes({
        send: ["project/components/Button/README.md"],
        unchanged: ["project/tokens.json"],
        delete: ["project/components/Card/README.md"],
      }),
      index: target,
      call: { kind: "first" },
    });

    expect(first.files).toEqual(previous.files);
    expect(first.baseline).toEqual(previous.baseline);
    expect(first.index).toEqual(previous.index);
    expect(first.commit).toBe(previous.commit);
    expect(first.pending).toEqual({
      files: new Map([
        [
          "project/components/Button/README.md",
          entry("project/components/Button/README.md", "새 버튼\n"),
        ],
      ]),
      delete: ["project/components/Card/README.md"],
      index: target,
    });
  });

  test("마지막 기록은 pending 을 비운다", () => {
    const first = nextRecord({
      previous: previousRecord(),
      output: OUTPUT,
      artifact: new Map(),
      changes: changes({ send: ["project/components/Button/README.md"] }),
      index: INDEX,
      call: { kind: "first" },
    });
    const last = nextRecord({
      previous: first,
      output: OUTPUT,
      artifact: new Map(),
      changes: changes({ send: ["project/components/Button/README.md"] }),
      index: INDEX,
      call: { kind: "last", commit: "2222222", at: "2026-10-26T01:00:00.000Z" },
    });

    expect(first.pending).not.toBeNull();
    expect(last.pending).toBeNull();
  });

  test("다시 한 올리기가 목표와 같아 보내지 않은 파일도 새 pending 과 마지막 기록에 목표 해시로 든다", () => {
    // 멈춘 올리기가 Button 의 README 를 이미 보냈다(확인이 목표 해시와 같다고 냈다). 이번 산출의 로컬 값도 같아 다시
    // 보내지 않는다. 멈춘 올리기가 보냈지만 이번 산출에 없는 Badge 도 웹에 있으므로 그 목표를 이어 적는다.
    const interrupted = previousRecord({
      pending: {
        files: new Map([
          [
            "project/components/Button/README.md",
            entry("project/components/Button/README.md", "새 버튼\n"),
          ],
          [
            "project/components/Badge/README.md",
            entry("project/components/Badge/README.md", "배지\n"),
          ],
        ]),
        delete: [],
        index: INDEX,
      },
    });
    const landed = ["project/components/Badge/README.md", "project/components/Button/README.md"];
    const call = { kind: "first" } as const;
    const again = nextRecord({
      previous: interrupted,
      output: OUTPUT,
      artifact: new Map(),
      changes: changes({ landed, unchanged: ["project/tokens.json"] }),
      index: INDEX,
      call,
    });
    const last = nextRecord({
      previous: again,
      output: OUTPUT,
      artifact: new Map(),
      changes: changes({ landed, unchanged: ["project/tokens.json"] }),
      index: INDEX,
      call: { kind: "last", commit: "2222222", at: "2026-10-26T01:00:00.000Z" },
    });

    const button = entry("project/components/Button/README.md", "새 버튼\n");
    const badge = entry("project/components/Badge/README.md", "배지\n");
    expect(again.pending?.files.get("project/components/Button/README.md")).toEqual(button);
    expect(again.pending?.files.get("project/components/Badge/README.md")).toEqual(badge);
    expect(last.files.get("project/components/Button/README.md")).toEqual(button);
    expect(last.files.get("project/components/Badge/README.md")).toEqual(badge);
  });

  test("이미 지워진 pending 의 지울 경로는 지우는 요청 없이 기록에서 뺀다", () => {
    const next = nextRecord({
      previous: previousRecord(),
      output: OUTPUT,
      artifact: new Map(),
      changes: changes({ gone: ["project/components/Card/README.md"] }),
      index: INDEX,
      call: { kind: "last", commit: "2222222", at: "2026-10-26T01:00:00.000Z" },
    });

    expect(next.files.has("project/components/Card/README.md")).toBe(false);
  });

  test("다시 한 올리기의 첫 기록은 이미 지워진 지울 경로도 pending 에 이어 적는다", () => {
    // 멈춘 올리기가 Card 의 README 를 이미 지웠다. 이번 첫 호출 뒤에 또 멈추면, 다음 확인은 기록의 파일에 남은 Card 를
    // pending 의 지울 경로로 보아 지운 것(deleted)으로 가른다. 지울 경로에서 빠지면 웹이 지운 파일(removed)로 낸다.
    const interrupted = previousRecord({
      pending: { files: new Map(), delete: ["project/components/Card/README.md"], index: INDEX },
    });
    const again = nextRecord({
      previous: interrupted,
      output: OUTPUT,
      artifact: new Map(),
      changes: changes({ gone: ["project/components/Card/README.md"] }),
      index: INDEX,
      call: { kind: "first" },
    });

    expect(again.files.has("project/components/Card/README.md")).toBe(true);
    expect(again.pending?.delete).toEqual(["project/components/Card/README.md"]);
  });

  test("claim 칸은 받은 그대로 지킨다", () => {
    const claim = { branch: "feature/11-web-edit-gray", at: "2026-10-26T00:30:00.000Z" };
    const previous = previousRecord({ claim });
    for (const call of [
      { kind: "first" } as const,
      { kind: "last", commit: "2222222", at: "2026-10-26T01:00:00.000Z" } as const,
    ]) {
      const next = nextRecord({
        previous,
        output: OUTPUT,
        artifact: new Map(),
        changes: changes({}),
        index: INDEX,
        call,
      });
      expect(next.claim).toEqual(claim);
    }
  });

  test("보낼 파일이 이번 산출에 없으면 input 오류다", () => {
    const thrown = caught(() =>
      nextRecord({
        previous: previousRecord(),
        output: OUTPUT,
        artifact: new Map(),
        changes: changes({ send: ["project/components/Missing/README.md"] }),
        index: INDEX,
        call: { kind: "last", commit: "2222222", at: "2026-10-26T01:00:00.000Z" },
      }),
    );
    expect(thrown).toBeInstanceOf(CommandError);
    expect(thrown).toMatchObject({
      kind: "input",
      message: "기록에 적을 project/components/Missing/README.md 가 이번 산출에 없다",
    });
  });

  test("이번 산출에도 앞 기록에도 기준본이 없으면 input 오류다", () => {
    const thrown = caught(() =>
      nextRecord({
        previous: null,
        output: new Map([["project/components/Button/README.md", bytes("버튼\n")]]),
        artifact: new Map(),
        changes: changes({ send: ["project/components/Button/README.md"] }),
        index: INDEX,
        call: { kind: "last", commit: "2222222", at: "2026-10-26T01:00:00.000Z" },
      }),
    );
    expect(thrown).toBeInstanceOf(CommandError);
    expect(thrown).toMatchObject({
      kind: "input",
      message: "기준본이 없다: 이번 산출에 project/tokens.json 가 없고 앞 기록에도 없다",
    });
  });
});

describe("기록 읽기와 쓰기", () => {
  test("쓴 기록을 다시 읽으면 같은 기록이고 들여쓰기 없는 JSON 이다", () => {
    const record = previousRecord({
      claim: { branch: "feature/11-web-edit-gray" },
      pending: { files: new Map(), delete: ["project/a.md"], index: INDEX },
    });
    const text = serializeRecord(record);

    expect(text).not.toContain("\n");
    expect(readRecord(text)).toEqual({ kind: "ok", record });
  });

  test("파일 목록은 경로 차례로 적는다", () => {
    const record = previousRecord();
    const files = new Map([...record.files].reverse());
    const text = serializeRecord({ ...record, files });
    const parsed: unknown = JSON.parse(text);
    if (typeof parsed !== "object" || parsed === null || !("files" in parsed)) {
      throw new Error("기록에 files 가 없다");
    }
    const written = parsed.files;
    if (typeof written !== "object" || written === null) {
      throw new Error("files 가 객체가 아니다");
    }
    expect(Object.keys(written)).toEqual([...record.files.keys()].sort());
  });

  test("JSON 으로 풀리지 않는 기록은 읽히지 않는 것이다", () => {
    expect(readRecord("{ 깨진")).toEqual({ kind: "unreadable" });
  });

  test("꼴 판이 1 이 아니거나 없으면 모르는 꼴 판이다", () => {
    expect(readRecord(JSON.stringify({ v: 2, files: {} }))).toEqual({
      kind: "unknownVersion",
      version: 2,
    });
    expect(readRecord(JSON.stringify({ files: {} }))).toEqual({
      kind: "unknownVersion",
      version: null,
    });
    expect(readRecord("[]")).toEqual({ kind: "unknownVersion", version: null });
  });

  test("꼴 판은 1 인데 칸이 어긋나면 어긋난 꼴이다", () => {
    const good = parsed(serializeRecord(previousRecord()));
    if (!jsonObject(good)) {
      throw new Error("기록이 객체가 아니다");
    }
    const cases: [string, unknown][] = [
      ["짧은 해시", { ...good, files: { "project/a.md": { hash: "짧다", bytes: 1 } } }],
      [
        "음수 바이트 수",
        { ...good, files: { "project/a.md": { hash: "a".repeat(64), bytes: -1 } } },
      ],
      [
        "점 둘 경로",
        { ...good, files: { "project/../밖.md": { hash: "a".repeat(64), bytes: 1 } } },
      ],
      [
        "project 밖 경로",
        { ...good, files: { "artifact-type/app.js": { hash: "a".repeat(64), bytes: 1 } } },
      ],
      ["수 커밋", { ...good, commit: 7 }],
      ["수가 든 지울 경로", { ...good, pending: { files: {}, delete: [3], index: INDEX } }],
      ["색인 없는 pending", { ...good, pending: { files: {}, delete: [] } }],
    ];
    for (const [label, item] of cases) {
      expect(readRecord(JSON.stringify(item)).kind, label).toBe("malformed");
    }
  });
});

describe("기록의 크기", () => {
  /** 설명이 한국어 40 자씩 든 tokens.json. 03 이 설명 주석을 넣은 뒤의 크기를 어림한다. */
  function describedTokens(): JsonValue {
    const file = buildTokensFile(CSS);
    const usage = "가".repeat(40);
    const described = {
      ...file,
      color: { ...file.color, tokens: file.color.tokens.map((token) => ({ ...token, usage })) },
      spacing: {
        ...file.spacing,
        tokens: file.spacing.tokens.map((token) => ({ ...token, usage })),
      },
      radius: { ...file.radius, tokens: file.radius.tokens.map((token) => ({ ...token, usage })) },
    };
    return parsed(JSON.stringify(described));
  }

  /** 경로 52 자의 파일 1,024 개. */
  function manyFiles(seed: string): Map<string, FileEntry> {
    const files = new Map<string, FileEntry>();
    for (let index = 0; index < 1024; index += 1) {
      const path = `project/components/${seed}${String(index).padStart(4, "0")}/`.padEnd(49, "x");
      files.set(`${path}.md`, { hash: "f".repeat(64), bytes: 123_456 });
    }
    return files;
  }

  test("1,024 개 파일, 기준본, pending, tokens.json 사본과 이어받은 기준본을 든 claim 의 기록이 512,000 바이트 이하다", () => {
    const tokens = describedTokens();
    const files = manyFiles("a");
    expect([...files.keys()].every((path) => path.length === 52)).toBe(true);
    const record: SyncRecord = {
      v: 1,
      commit: "0123456789abcdef0123456789abcdef01234567",
      at: "2026-10-26T01:00:00.000Z",
      files,
      baseline: tokens,
      index: INDEX,
      pending: {
        files: manyFiles("b"),
        delete: [...manyFiles("c").keys()].slice(0, 64),
        index: INDEX,
      },
      claim: {
        branch: "feature/11-web-edit-gray-50",
        ticket: ".scratch/design-reverse-sync/issues/11-web-edit-gray-50.md",
        at: "2026-10-26T00:30:00.000Z",
        tokens,
        baseline: tokens,
        files: { "project/README.md": "e".repeat(64) },
        added: [],
        removed: [],
      },
    };
    const text = serializeRecord(record);
    const size = new TextEncoder().encode(text).byteLength;

    expect(size).toBeLessThanOrEqual(RECORD_LIMIT);
    expect(size).toBeGreaterThan(300_000);
  });

  test("한도는 512,000 바이트이고 넘는 기록은 쓰지 않고 limit 오류다", () => {
    expect(RECORD_LIMIT).toBe(512_000);
    const record = previousRecord();
    const room = RECORD_LIMIT - new TextEncoder().encode(serializeRecord(record)).byteLength;
    // claim 의 글 하나로 꼭 한도까지 채운다. 따옴표 둘과 null 을 바꾼 몫을 뺀다.
    const filler = "x".repeat(room + "null".length - 2);
    const atLimit = { ...record, claim: filler };

    expect(new TextEncoder().encode(serializeRecord(atLimit)).byteLength).toBe(RECORD_LIMIT);
    const thrown = caught(() => serializeRecord({ ...record, claim: `${filler}x` }));
    expect(thrown).toBeInstanceOf(CommandError);
    expect(thrown).toMatchObject({
      kind: "limit",
      message: "기록이 512001 바이트로 한도 512000 바이트를 넘어 쓰지 않는다",
    });
  });
});
