// 확인의 테스트(design-reverse-sync 명세 Testing Decisions "확인"과 그 2026-10-22 주석, `claim` 이 든 사례는 06 티켓의
// 것). 페이지의 저장 꼴은 02 가 임시 아티팩트에서 받은 시험 자료(`fixtures/`)다.

import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, test } from "vitest";
import type { CheckReport, EditLists, PendingReport } from "./check-report.ts";
import { judge, judgeWithInherit, nextFetch, type CheckContext, type WebFiles } from "./check.ts";
import { CommandError } from "./command.ts";
import {
  fileHash,
  humanPart,
  INDEX_PATH,
  README_PATH,
  RECORD_PATH,
  TOKENS_PATH,
} from "./file-hash.ts";
import { jsonValue } from "./io.ts";
import {
  serializeRecord,
  type Claim,
  type FileEntry,
  type IndexLists,
  type Pending,
  type SyncRecord,
} from "./sync-record.ts";
import { diffTokens, readTokens, type JsonValue } from "./tokens-json.ts";

function fixture(name: string): string {
  return readFileSync(join(import.meta.dirname, "fixtures", name), "utf-8");
}

/** 올린 tokens.json. 기준본이다. */
const UPLOADED = fixture("uploaded-tokens.json");
/** 사람이 값 하나(gray-50)와 설명 하나(radius-m)를 고친 뒤 페이지가 저장한 tokens.json. */
const PAGE_SAVED = fixture("page-saved-tokens.json");
/** 페이지가 저장한 꼴에서 사람이 고친 값만 되돌린 것. 올린 파일을 페이지가 꼴만 다시 쓴 것이다. */
const PAGE_REWRITTEN = PAGE_SAVED.replace('"#f0f4f8"', '"#f4f8fb"').replace(
  "버튼과 카드의 모서리",
  "",
);
/** 페이지가 저장한 꼴에서 설명만 되돌린 것. 멈춘 올리기가 값 하나를 바꿔 보낸 tokens.json 이다. */
const SENT_VALUE = PAGE_SAVED.replace("버튼과 카드의 모서리", "");
/** 사람 몫만 올린 README 에 페이지가 구분선과 생성 몫을 붙여 저장한 것. */
const PAGE_SAVED_README = fixture("page-saved-README.md");

const GUIDE = "project/guidelines/index.md";
const WEB_DESIGN = "project/guidelines/web-design.md";
const BUTTON = "project/components/Button/README.md";
const BADGE_HTML = "project/components/Badge/index.html";
const BADGE = "project/components/Badge/README.md";
const LIB = "project/components/lib/shared.js";
const API_NOTES = "project/api/notes.md";
const LOGO = "project/assets/logo.png";

const README = "# 디자인 시스템\n\n사람이 쓴 안내.\n";
const CONSUMING = "## Consuming this system (generated — do not edit)";
const QUICK_START = "## Quick start (generated from tokens.json — do not edit)";

function bytes(text: string): Uint8Array {
  return new TextEncoder().encode(text);
}

function entry(path: string, text: string): FileEntry {
  const data = bytes(text);
  return { hash: fileHash(path, data), bytes: data.byteLength };
}

function parsed(text: string): JsonValue {
  const raw: unknown = JSON.parse(text);
  const value = jsonValue(raw);
  if (value === undefined) {
    throw new Error("JSON 값이 아니다");
  }
  return value;
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

const LISTS: IndexLists = {
  assetGroups: { notes: { files: {}, name: "notes", order: [] } },
  blobs: {},
  docs: { readme: README_PATH, sections: [GUIDE, WEB_DESIGN] },
  sections: {},
};

/** 웹에 있는 마크다운과 그 내용. 올린 그대로다. */
const MARKDOWN: Readonly<Record<string, string>> = {
  [README_PATH]: README,
  [GUIDE]: "# 지침\n",
  [WEB_DESIGN]: "# 웹 디자인\n",
  [BUTTON]: "# 버튼\n",
  [API_NOTES]: "# API 메모\n",
};

/** 마지막 기록. 마크다운 다섯, 컴포넌트의 다른 파일 둘, 그림 하나, tokens.json 을 올렸다. */
function lastRecord(overrides: Partial<SyncRecord> = {}): SyncRecord {
  return {
    v: 1,
    commit: "1111111",
    at: "2026-10-26T00:00:00.000Z",
    files: new Map([
      ...Object.entries(MARKDOWN).map(([path, text]): [string, FileEntry] => [
        path,
        entry(path, text),
      ]),
      [BADGE_HTML, entry(BADGE_HTML, "<p>배지</p>")],
      [LIB, entry(LIB, "export {};")],
      [LOGO, entry(LOGO, "PNG")],
      [TOKENS_PATH, entry(TOKENS_PATH, UPLOADED)],
    ]),
    baseline: parsed(UPLOADED),
    index: LISTS,
    pending: null,
    claim: null,
    ...overrides,
  };
}

interface Artifact {
  /** 색인. 편집 켜짐이 기본이다. undefined 면 받지 못했다(없다). */
  readonly index?: JsonValue;
  /** 기록의 글. undefined 면 없다. */
  readonly record?: string;
  readonly tokens?: string;
  /** 웹의 파일. undefined 인 경로는 없다. */
  readonly files?: Readonly<Record<string, string | undefined>>;
  /** 받으려 했지만 없다는 까닭이 아닌 까닭으로 읽지 못한 경로와 그 문구. */
  readonly failed?: Readonly<Record<string, string>>;
}

/**
 * 받은 폴더. 첫 받기(tokens.json, 색인, 기록)와 그 뒤에 받을 경로를 모두 받은 것으로 짓는다. 내용이 없는 경로는
 * 없다는 까닭으로 읽지 못한 것이다.
 */
function web(artifact: Artifact): WebFiles {
  const files = new Map<string, Uint8Array>();
  const absent = new Set<string>();
  const failed = new Map(Object.entries(artifact.failed ?? {}));
  const put = (path: string, text: string | undefined): void => {
    if (failed.has(path)) {
      return;
    }
    if (text === undefined) {
      absent.add(path);
    } else {
      files.set(path, bytes(text));
    }
  };
  put(INDEX_PATH, artifact.index === undefined ? undefined : JSON.stringify(artifact.index));
  put(RECORD_PATH, artifact.record);
  put(TOKENS_PATH, artifact.tokens);
  const given = artifact.files ?? {};
  for (const [path, text] of Object.entries(given)) {
    put(path, text);
  }
  const first: WebFiles = { files, absent, failed };
  for (const path of nextFetch(first)) {
    if (!Object.hasOwn(given, path)) {
      put(path, undefined);
    }
  }
  return first;
}

function index(overrides: Readonly<Record<string, JsonValue>> = {}): JsonValue {
  return { v: 1, title: "Agent OS", ...LISTS, ...overrides };
}

/** 편집이 켜진 아티팩트. 마지막 기록과 그대로인 웹이다. */
function unchanged(overrides: Partial<Artifact> = {}): Artifact {
  return {
    index: index(),
    record: serializeRecord(lastRecord()),
    tokens: UPLOADED,
    files: MARKDOWN,
    ...overrides,
  };
}

const CLEAN: CheckReport = { result: "clean", editing: "on", record: "ok", pending: null };

function edited(partial: Partial<Extract<CheckReport, { result: "edited" }>>): CheckReport {
  return {
    result: "edited",
    tokens: [],
    tokensMixed: false,
    files: [],
    index: [],
    pending: null,
    ...partial,
  };
}

describe("받을 경로", () => {
  test("첫 받기 전에는 첫 받기의 경로를 낸다", () => {
    const empty: WebFiles = { files: new Map(), absent: new Set([RECORD_PATH]), failed: new Map() };

    expect(nextFetch(empty)).toEqual([INDEX_PATH, TOKENS_PATH]);
  });

  test("받을 경로를 다 받거나 읽지 못한 것으로 적으면 빈 목록이다", () => {
    expect(nextFetch(web(unchanged()))).toEqual([]);
  });

  test("기록의 api 밖 마크다운, 색인의 문서, 컴포넌트마다의 README 를 낸다", () => {
    const first: WebFiles = {
      files: new Map([
        [INDEX_PATH, bytes(JSON.stringify(index()))],
        [RECORD_PATH, bytes(serializeRecord(lastRecord()))],
        [TOKENS_PATH, bytes(UPLOADED)],
      ]),
      absent: new Set(),
      failed: new Map(),
    };

    expect(nextFetch(first)).toEqual([README_PATH, BADGE, BUTTON, GUIDE, WEB_DESIGN]);
  });

  test("묶음 폴더 아래의 컴포넌트는 묶음 폴더가 아니라 그 컴포넌트 폴더의 README 를 낸다", () => {
    // 첫 올리기(티켓 08)가 받은 아티팩트의 꼴이다. 짓기 명령 전의 옛 배치는 컴포넌트를 묶음 폴더 아래에 둔다.
    const grouped = "project/components/atoms/Button/Button.html";
    const record = lastRecord({ files: new Map([[grouped, entry(grouped, "<p>버튼</p>")]]) });
    const first: WebFiles = {
      files: new Map([
        [INDEX_PATH, bytes(JSON.stringify(index()))],
        [RECORD_PATH, bytes(serializeRecord(record))],
        [TOKENS_PATH, bytes(UPLOADED)],
      ]),
      absent: new Set(),
      failed: new Map(),
    };

    expect(nextFetch(first)).toEqual([
      README_PATH,
      "project/components/atoms/Button/README.md",
      GUIDE,
      WEB_DESIGN,
    ]);
  });

  test("색인에 든 문서는 기록에 없어도 낸다", () => {
    const first: WebFiles = {
      files: new Map([
        [
          INDEX_PATH,
          bytes(
            JSON.stringify(index({ docs: { readme: README_PATH, sections: ["project/new.md"] } })),
          ),
        ],
      ]),
      absent: new Set([RECORD_PATH, TOKENS_PATH]),
      failed: new Map(),
    };

    expect(nextFetch(first)).toEqual([README_PATH, "project/new.md"]);
  });

  test("pending 의 경로를 더한다", () => {
    const pending: Pending = {
      files: new Map([
        ["project/guidelines/new.md", entry("project/guidelines/new.md", "새 지침\n")],
      ]),
      delete: ["project/assets/notes/old.md"],
      index: LISTS,
    };
    const first: WebFiles = {
      files: new Map([
        [INDEX_PATH, bytes(JSON.stringify(index()))],
        [RECORD_PATH, bytes(serializeRecord(lastRecord({ pending })))],
      ]),
      absent: new Set([TOKENS_PATH]),
      failed: new Map(),
    };

    expect(nextFetch(first)).toContain("project/guidelines/new.md");
    expect(nextFetch(first)).toContain("project/assets/notes/old.md");
  });

  test("편집이 꺼진 색인에서는 pending 의 경로만 낸다", () => {
    const pending: Pending = {
      files: new Map([[BUTTON, entry(BUTTON, "목표\n")]]),
      delete: [],
      index: LISTS,
    };
    const first: WebFiles = {
      files: new Map([
        [INDEX_PATH, bytes(JSON.stringify(index({ editing: "off" })))],
        [RECORD_PATH, bytes(serializeRecord(lastRecord({ pending })))],
      ]),
      absent: new Set([TOKENS_PATH]),
      failed: new Map(),
    };

    expect(nextFetch(first)).toEqual([BUTTON]);
  });

  test("색인에 든 project 밖이나 이상한 경로는 받지 않는다", () => {
    const first: WebFiles = {
      files: new Map([
        [
          INDEX_PATH,
          bytes(
            JSON.stringify(
              index({ docs: { readme: "../secret.md", sections: ["project/../x.md", 3] } }),
            ),
          ),
        ],
      ]),
      absent: new Set([RECORD_PATH, TOKENS_PATH]),
      failed: new Map(),
    };

    expect(nextFetch(first)).toEqual([]);
  });
});

describe("웹 편집이 켜진 아티팩트", () => {
  test("올린 그대로면 웹 편집 없음이다", () => {
    expect(judge(web(unchanged()))).toEqual(CLEAN);
  });

  test("페이지가 저장한 tokens.json 의 사람 편집을 토큰 목록으로 낸다", () => {
    const report = judge(web(unchanged({ tokens: PAGE_SAVED })));

    expect(report).toEqual(
      edited({ tokens: diffTokens(readTokens(parsed(UPLOADED)), readTokens(parsed(PAGE_SAVED))) }),
    );
    expect(report.result === "edited" ? report.tokens : []).toHaveLength(2);
  });

  test("페이지가 꼴만 다시 쓴 tokens.json 은 웹 편집이 아니다", () => {
    expect(judge(web(unchanged({ tokens: PAGE_REWRITTEN })))).toEqual(CLEAN);
  });

  test.each([
    ["Consuming", CONSUMING],
    ["Quick start", QUICK_START],
  ])("README 에 페이지가 구분선과 생성 몫(%s 머리)만 붙인 것은 웹 편집이 아니다", (_name, head) => {
    const saved = `${README}\n\n---\n\n${head}\n\n생성된 글.\n`;

    expect(judge(web(unchanged({ files: { ...MARKDOWN, [README_PATH]: saved } })))).toEqual(CLEAN);
  });

  test("페이지가 실제로 저장한 README 는 사람 몫만 올린 기록과 같다", () => {
    const record = lastRecord({
      files: new Map([
        ...lastRecord().files,
        [README_PATH, entry(README_PATH, humanPart(PAGE_SAVED_README))],
      ]),
    });

    expect(
      judge(
        web(
          unchanged({
            record: serializeRecord(record),
            files: { ...MARKDOWN, [README_PATH]: PAGE_SAVED_README },
          }),
        ),
      ),
    ).toEqual(CLEAN);
  });

  test("생성 절이 든 README 를 읽어 적은 기록은 생성 몫이 달라도 같다", () => {
    const record = lastRecord({
      files: new Map([...lastRecord().files, [README_PATH, entry(README_PATH, PAGE_SAVED_README)]]),
    });
    const resaved = `${humanPart(PAGE_SAVED_README)}\n\n---\n\n${QUICK_START}\n\n다시 지은 글.\n`;

    expect(
      judge(
        web(
          unchanged({
            record: serializeRecord(record),
            files: { ...MARKDOWN, [README_PATH]: resaved },
          }),
        ),
      ),
    ).toEqual(CLEAN);
  });

  test("README 의 사람 몫을 고치면 웹 편집이다", () => {
    const saved = `${README}한 줄 더.\n\n---\n\n${CONSUMING}\n`;

    expect(judge(web(unchanged({ files: { ...MARKDOWN, [README_PATH]: saved } })))).toEqual(
      edited({ files: [{ path: README_PATH, change: "changed" }] }),
    );
  });

  test("마크다운 편집, 지운 것, 더한 것을 토큰 밖 목록으로 낸다", () => {
    const report = judge(
      web(
        unchanged({
          index: index({
            docs: {
              readme: README_PATH,
              sections: [GUIDE, WEB_DESIGN, "project/guidelines/new.md"],
            },
          }),
          files: {
            ...MARKDOWN,
            [GUIDE]: "# 지침\n\n웹에서 더한 줄.\n",
            [BUTTON]: undefined,
            "project/guidelines/new.md": "# 새 지침\n",
          },
        }),
      ),
    );

    expect(report).toEqual(
      edited({
        files: [
          { path: BUTTON, change: "removed" },
          { path: GUIDE, change: "changed" },
          { path: "project/guidelines/new.md", change: "added" },
        ],
        index: [
          {
            key: "docs",
            before: LISTS.docs,
            after: {
              readme: README_PATH,
              sections: [GUIDE, WEB_DESIGN, "project/guidelines/new.md"],
            },
          },
        ],
      }),
    );
  });

  test("색인의 그림 목록이 바뀌면 웹 편집이다", () => {
    const assetGroups = {
      notes: { files: { logo: "project/assets/logo.png" }, name: "notes", order: ["logo"] },
    };

    expect(judge(web(unchanged({ index: index({ assetGroups }) })))).toEqual(
      edited({ index: [{ key: "assetGroups", before: LISTS.assetGroups, after: assetGroups }] }),
    );
  });

  test("색인 목록의 키 차례만 바뀐 것은 웹 편집이 아니다", () => {
    const assetGroups = { notes: { order: [], name: "notes", files: {} } };

    expect(judge(web(unchanged({ index: index({ assetGroups }) })))).toEqual(CLEAN);
  });

  test("api 아래 마크다운과 마크다운이 아닌 파일은 맞대지 않는다", () => {
    expect(
      judge(
        web(unchanged({ files: { ...MARKDOWN, [API_NOTES]: "고친 메모\n", [LOGO]: "다른 그림" } })),
      ),
    ).toEqual(CLEAN);
  });
});

describe("멈춘 올리기가 남긴 pending", () => {
  const NEW_GUIDE = "project/guidelines/new.md";
  const OLD_NOTE = "project/assets/notes/old.md";

  function stopped(pending: Partial<Pending>): string {
    return serializeRecord(
      lastRecord({ pending: { files: new Map(), delete: [], index: LISTS, ...pending } }),
    );
  }

  test("목표와 같은 파일은 보낸 것이고, 앞 해시와 같은 파일은 아직 보내지 않은 것이다", () => {
    const record = stopped({
      files: new Map([
        [GUIDE, entry(GUIDE, "# 지침 새 판\n")],
        [BUTTON, entry(BUTTON, "# 버튼 새 판\n")],
        [NEW_GUIDE, entry(NEW_GUIDE, "# 새 지침\n")],
      ]),
    });

    expect(
      judge(
        web(
          unchanged({
            record,
            files: { ...MARKDOWN, [GUIDE]: "# 지침 새 판\n", [NEW_GUIDE]: undefined },
          }),
        ),
      ),
    ).toEqual({
      ...CLEAN,
      pending: { [BUTTON]: "unsent", [GUIDE]: "sent", [NEW_GUIDE]: "unsent" },
    });
  });

  test("목표와도 앞 해시와도 다른 파일이 섞이면 그것만 웹 편집이다", () => {
    const record = stopped({
      files: new Map([
        [GUIDE, entry(GUIDE, "# 지침 새 판\n")],
        [BUTTON, entry(BUTTON, "# 버튼 새 판\n")],
        [WEB_DESIGN, entry(WEB_DESIGN, "# 웹 디자인 새 판\n")],
      ]),
    });

    expect(
      judge(
        web(
          unchanged({
            record,
            files: {
              ...MARKDOWN,
              [GUIDE]: "# 지침 새 판\n",
              [WEB_DESIGN]: "# 웹에서 고친 웹 디자인\n",
            },
          }),
        ),
      ),
    ).toEqual(
      edited({
        files: [{ path: WEB_DESIGN, change: "changed" }],
        pending: { [BUTTON]: "unsent", [GUIDE]: "sent", [WEB_DESIGN]: "edited" },
      }),
    );
  });

  test("목표 해시와 앞 해시가 같은 파일은 웹 편집이 아니다", () => {
    const record = stopped({ files: new Map([[GUIDE, entry(GUIDE, MARKDOWN[GUIDE] ?? "")]]) });

    expect(judge(web(unchanged({ record })))).toEqual({ ...CLEAN, pending: { [GUIDE]: "sent" } });
  });

  test("지울 경로가 웹에 없으면 지워진 것이고, 있으면 아직 있는 것이다", () => {
    const record = stopped({ delete: [OLD_NOTE, BUTTON] });

    expect(
      judge(web(unchanged({ record, files: { ...MARKDOWN, [OLD_NOTE]: undefined } }))),
    ).toEqual({
      ...CLEAN,
      pending: { [OLD_NOTE]: "deleted", [BUTTON]: "remaining" },
    });
  });

  test("색인 목록이 pending 의 목표와 같으면 웹 편집이 아니다", () => {
    const docs = { readme: README_PATH, sections: [GUIDE] };
    const record = stopped({ index: { ...LISTS, docs } });

    expect(judge(web(unchanged({ record, index: index({ docs }) })))).toEqual({
      ...CLEAN,
      pending: {},
    });
  });

  test("페이지가 꼴만 다시 쓴 아직 보내지 않은 tokens.json 은 웹 편집이 아니다", () => {
    const record = stopped({ files: new Map([[TOKENS_PATH, entry(TOKENS_PATH, PAGE_SAVED)]]) });

    expect(judge(web(unchanged({ record, tokens: PAGE_REWRITTEN })))).toEqual({
      ...CLEAN,
      pending: { [TOKENS_PATH]: "unsent" },
    });
  });

  test("보낸 tokens.json 은 목표와 같으면 웹 편집이 아니다", () => {
    const record = stopped({ files: new Map([[TOKENS_PATH, entry(TOKENS_PATH, SENT_VALUE)]]) });

    expect(judge(web(unchanged({ record, tokens: SENT_VALUE })))).toEqual({
      ...CLEAN,
      pending: { [TOKENS_PATH]: "sent" },
    });
  });

  test("보낸 뒤 더 고친 tokens.json 은 기준본과 맞댄 목록에 보낸 값이 섞일 수 있다고 표시한다", () => {
    const record = stopped({ files: new Map([[TOKENS_PATH, entry(TOKENS_PATH, SENT_VALUE)]]) });

    expect(judge(web(unchanged({ record, tokens: PAGE_SAVED })))).toEqual(
      edited({
        tokens: diffTokens(readTokens(parsed(UPLOADED)), readTokens(parsed(PAGE_SAVED))),
        tokensMixed: true,
        pending: { [TOKENS_PATH]: "edited" },
      }),
    );
  });
});

describe("웹 편집이 꺼진 아티팩트", () => {
  const OFF = index({ editing: "off" });

  test("기록도 tokens.json 도 없으면 기록 전이다", () => {
    expect(judge(web({ index: OFF }))).toEqual({ result: "beforeRecord", editing: "off" });
  });

  test("기록은 없고 tokens.json 은 있으면 웹 편집 없음이다", () => {
    expect(judge(web({ index: OFF, tokens: UPLOADED }))).toEqual({
      result: "clean",
      editing: "off",
      record: "absent",
      pending: null,
    });
  });

  test("기록이 읽히지 않아도 웹 편집 없음이다", () => {
    expect(judge(web({ index: OFF, record: "{", tokens: UPLOADED }))).toEqual({
      result: "clean",
      editing: "off",
      record: "unreadable",
      pending: null,
    });
  });

  test("기록이 있으면 웹이 달라도 웹 편집 없음이다", () => {
    expect(
      judge(web(unchanged({ index: OFF, tokens: PAGE_SAVED, files: { [GUIDE]: "웹 글" } }))),
    ).toEqual({
      result: "clean",
      editing: "off",
      record: "ok",
      pending: null,
    });
  });

  test("앞 해시가 없는 첫 올리기가 멈춘 기록은 목표와 같은 파일을 보낸 것으로 가른다", () => {
    const record = serializeRecord({
      v: 1,
      commit: null,
      at: null,
      files: new Map(),
      baseline: null,
      index: null,
      pending: {
        files: new Map([
          [TOKENS_PATH, entry(TOKENS_PATH, UPLOADED)],
          [BUTTON, entry(BUTTON, "# 버튼\n")],
          [GUIDE, entry(GUIDE, "# 지침 새 판\n")],
        ]),
        delete: [],
        index: LISTS,
      },
      claim: null,
    });

    expect(
      judge(
        web({
          index: OFF,
          record,
          tokens: PAGE_REWRITTEN,
          files: { [BUTTON]: "# 버튼\n", [GUIDE]: "# 지침\n" },
        }),
      ),
    ).toEqual({
      result: "clean",
      editing: "off",
      record: "ok",
      pending: { [BUTTON]: "sent", [GUIDE]: "unsent", [TOKENS_PATH]: "sent" },
    });
  });
});

describe("판단할 수 없음", () => {
  function reason(report: CheckReport): string | null {
    return report.result === "undecidable" ? report.reason : null;
  }

  test("편집이 켜졌는데 기록이 없다", () => {
    expect(reason(judge(web(unchanged({ record: undefined }))))).toBe("noRecord");
  });

  test("기록이 JSON 으로 풀리지 않는다", () => {
    expect(reason(judge(web(unchanged({ record: '{"v": 1,' }))))).toBe("recordUnreadable");
  });

  test.each([
    ["다음 판", '{"v": 2}'],
    ["판 없음", '{"files": {}}'],
  ])("기록의 꼴 판을 모른다(%s)", (_name, record) => {
    expect(reason(judge(web(unchanged({ record }))))).toBe("unknownVersion");
  });

  test("기록의 꼴이 어긋났다", () => {
    expect(
      reason(
        judge(
          web(unchanged({ record: '{"v": 1, "files": {"../x.md": {"hash": "0", "bytes": 1}}}' })),
        ),
      ),
    ).toBe("recordMalformed");
  });

  test("기준본이 없다", () => {
    expect(
      reason(judge(web(unchanged({ record: serializeRecord(lastRecord({ baseline: null })) })))),
    ).toBe("noBaseline");
  });

  test("웹의 tokens.json 이 JSON 으로 풀리지 않는다", () => {
    expect(reason(judge(web(unchanged({ tokens: "{" }))))).toBe("tokensUnreadable");
  });

  test("색인이 없거나 풀리지 않는다", () => {
    expect(reason(judge(web(unchanged({ index: undefined }))))).toBe("noIndex");
    const broken: WebFiles = {
      files: new Map([[INDEX_PATH, bytes("{")]]),
      absent: new Set([RECORD_PATH, TOKENS_PATH]),
      failed: new Map(),
    };
    expect(reason(judge(broken))).toBe("indexUnreadable");
  });

  test("없다는 까닭이 아닌 까닭으로 읽지 못한 경로가 있으면 그 경로와 문구를 낸다", () => {
    const report = judge(web(unchanged({ failed: { [GUIDE]: "시간 초과" } })));

    expect(report).toEqual({
      result: "undecidable",
      reason: "readFailed",
      message: `${GUIDE}: 시간 초과`,
      paths: [GUIDE],
    });
  });

  test("기록을 읽지 못하면 편집이 꺼져 있어도 판단할 수 없음이다", () => {
    expect(
      reason(
        judge(
          web({
            index: index({ editing: "off" }),
            tokens: UPLOADED,
            failed: { [RECORD_PATH]: "권한 없음" },
          }),
        ),
      ),
    ).toBe("readFailed");
  });
});

describe("받은 폴더의 꼴", () => {
  test("받지 않은 경로가 있으면 멈춘다", () => {
    const partial: WebFiles = {
      files: new Map([
        [INDEX_PATH, bytes(JSON.stringify(index()))],
        [RECORD_PATH, bytes(serializeRecord(lastRecord()))],
        [TOKENS_PATH, bytes(UPLOADED)],
      ]),
      absent: new Set(),
      failed: new Map(),
    };
    const thrown = caught(() => judge(partial));
    const missing = nextFetch(partial);

    expect(missing).toContain(GUIDE);
    expect(thrown).toBeInstanceOf(CommandError);
    expect(thrown).toMatchObject({
      kind: "input",
      message: `받지 않은 경로가 있다: ${missing.join(", ")}. 받거나 읽지 못한 까닭을 적어 다시 부른다`,
    });
  });

  test("받은 파일을 없다고도 적으면 멈춘다", () => {
    const both = web(unchanged());
    const thrown = caught(() => judge({ ...both, absent: new Set([...both.absent, GUIDE]) }));

    expect(thrown).toBeInstanceOf(CommandError);
    expect(thrown).toMatchObject({
      kind: "input",
      message: `받은 파일과 읽지 못한 경로가 겹친다: ${GUIDE}`,
    });
  });
});

describe("들이기의 claim", () => {
  const ME = "feature/12-me";
  const OTHER = "feature/11-other";
  /** 웹이 값 하나를 더 고친 tokens.json. claim 의 사본(PAGE_SAVED) 뒤에 더 고친 몫이다. */
  const FURTHER = PAGE_SAVED.replace('"nokcheong-dark": "#f4f8fb"', '"nokcheong-dark": "#000000"');
  const WEB_BUTTON = "# 버튼\n\n웹에서 고친 글.\n";

  /** 웹의 tokens.json 과 버튼 README 를 들인 남의 claim. */
  function claimOf(overrides: Partial<Claim> = {}): Claim {
    return {
      branch: OTHER,
      ticket: ".scratch/x/issues/11-other.md",
      at: "2026-10-27T00:00:00.000Z",
      tokens: parsed(PAGE_SAVED),
      changed: new Map([[BUTTON, entry(BUTTON, WEB_BUTTON).hash]]),
      added: new Map(),
      removed: [],
      index: LISTS,
      base: null,
      ...overrides,
    };
  }

  function claimed(record: Partial<SyncRecord> = {}): string {
    return serializeRecord(lastRecord({ claim: claimOf(), ...record }));
  }

  /** claim 과 같은 웹. */
  function importing(overrides: Partial<Artifact> = {}): Artifact {
    return unchanged({
      record: claimed(),
      tokens: PAGE_SAVED,
      files: { ...MARKDOWN, [BUTTON]: WEB_BUTTON },
      ...overrides,
    });
  }

  function context(code: string = UPLOADED, branch: string = ME): CheckContext {
    return { branch, codeTokens: readTokens(parsed(code)) };
  }

  const NO_FURTHER: EditLists = { tokens: [], tokensMixed: false, files: [], index: [] };

  const SUMMARY = {
    branch: OTHER,
    ticket: ".scratch/x/issues/11-other.md",
    at: "2026-10-27T00:00:00.000Z",
    own: false,
    changed: [BUTTON, TOKENS_PATH],
    added: [],
    removed: [],
  };

  function inProgress(
    further: Partial<EditLists> = {},
    pending: PendingReport | null = null,
  ): CheckReport {
    return {
      result: "importing",
      claim: SUMMARY,
      further: { ...NO_FURTHER, ...further },
      pending,
      inherit: null,
    };
  }

  const STOPPED: Pending = {
    files: new Map([[TOKENS_PATH, entry(TOKENS_PATH, FURTHER)]]),
    delete: [],
    index: LISTS,
  };

  test("claim 과 같은 웹은 그 브랜치가 들이는 중이고 더 고친 몫이 없다", () => {
    expect(judge(web(importing()), context())).toEqual(inProgress());
  });

  test("페이지가 꼴만 다시 쓴 claim 과 같은 웹도 더 고친 몫이 없다", () => {
    const rewritten = JSON.stringify(JSON.parse(PAGE_SAVED), null, 4);

    expect(judge(web(importing({ tokens: rewritten })), context())).toEqual(inProgress());
  });

  test("claim 뒤에 더 고친 몫만 웹 편집으로 낸다", () => {
    const files = { ...MARKDOWN, [BUTTON]: WEB_BUTTON, [GUIDE]: "고침\n" };
    const report = judge(web(importing({ tokens: FURTHER, files })), context());

    expect(report).toEqual(
      inProgress({
        tokens: diffTokens(readTokens(parsed(PAGE_SAVED)), readTokens(parsed(FURTHER))),
        files: [{ path: GUIDE, change: "changed" }],
      }),
    );
  });

  test("claim 의 브랜치가 지금 브랜치와 같으면 자기 것이다", () => {
    expect(judge(web(importing()), context(UPLOADED, OTHER))).toEqual({
      ...inProgress(),
      claim: { ...SUMMARY, own: true },
    });
  });

  test("claim 이 지운 파일이 웹에 없으면 웹 편집이 아니다", () => {
    const record = claimed({ claim: claimOf({ removed: [GUIDE] }) });
    const files = { ...MARKDOWN, [BUTTON]: WEB_BUTTON, [GUIDE]: undefined };

    expect(judge(web(importing({ record, files })), context())).toEqual({
      ...inProgress(),
      claim: { ...SUMMARY, removed: [GUIDE] },
    });
  });

  test("claim 의 색인 목록과 같은 웹 색인은 웹 편집이 아니다", () => {
    const docs = { readme: README_PATH, sections: [GUIDE] };
    const record = claimed({ claim: claimOf({ index: { ...LISTS, docs } }) });

    expect(judge(web(importing({ record, index: index({ docs }) })), context())).toEqual(
      inProgress(),
    );
  });

  test("claim 이 있는데 지금 브랜치나 지금 코드의 tokens.json 이 없으면 usage 오류다", () => {
    expect(caught(() => judge(web(importing())))).toMatchObject({
      kind: "usage",
      message:
        "기록에 claim 이 있어 지금 브랜치(--branch)와 지금 코드에서 지은 tokens.json(--code-tokens)이 있어야 한다",
    });
  });

  test("pending 과 claim 이 함께 있고 tokens.json 이 pending 의 목표와 같으면 더 고친 몫이 아니다", () => {
    const record = claimed({ pending: STOPPED });

    expect(judge(web(importing({ record, tokens: FURTHER })), context())).toEqual(
      inProgress({}, { [TOKENS_PATH]: "sent" }),
    );
  });

  test("pending 과 claim 이 함께 있고 아직 보내지 않은 tokens.json 은 claim 의 것으로 가른다", () => {
    const record = claimed({ pending: STOPPED });

    expect(judge(web(importing({ record })), context())).toEqual(
      inProgress({}, { [TOKENS_PATH]: "claimed" }),
    );
  });

  test("병합된 claim 뒤에 웹이 코드와 같아진 몫은 더 고친 몫이 아니다", () => {
    expect(judge(web(importing({ tokens: FURTHER })), context(FURTHER))).toEqual(inProgress());
  });

  test("열린 PR 때 덮어써 웹이 기준본과 같아진 뒤 그 PR 이 병합되어도 더 고친 몫이 아니다", () => {
    const overwritten = importing({ tokens: UPLOADED, files: MARKDOWN });

    expect(judge(web(overwritten), context(PAGE_SAVED))).toEqual(inProgress());
  });

  test("남의 claim 에 더 고친 몫이 있으면 그 몫만 claim 의 사본 값으로 바꾼 이어받을 기준본을 낸다", () => {
    const { report, inherit } = judgeWithInherit(web(importing({ tokens: FURTHER })), context());

    expect(report.result).toBe("importing");
    expect(inherit === null ? null : readTokens(inherit)).toEqual(readTokens(parsed(PAGE_SAVED)));
  });

  test("자기 claim 이나 더 고친 몫이 없는 claim 은 이어받을 기준본을 내지 않는다", () => {
    const further = web(importing({ tokens: FURTHER }));

    expect(judgeWithInherit(further, context(UPLOADED, OTHER)).inherit).toBeNull();
    expect(judgeWithInherit(web(importing()), context()).inherit).toBeNull();
  });
});
