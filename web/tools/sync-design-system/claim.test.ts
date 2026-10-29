// 기록의 claim 을 쓰고 비우는 테스트(design-reverse-sync 06 티켓 "기록 명령의 claim", 명세 "겹침"과 그 2026-10-22
// 주석들). 확인 보고는 기록 명령이 다시 읽은 꼴(`CheckReading`)로 짓는다.

import { describe, expect, test } from "vitest";
import { NO_EDITS, type CheckReading, type ClaimSummary, type WebEdits } from "./check-report.ts";
import { claimedRecord, sameClaim, type ClaimHead } from "./claim.ts";
import { CommandError } from "./command.ts";
import { fileHash, INDEX_PATH, TOKENS_PATH } from "./file-hash.ts";
import type { Claim, IndexLists, Pending, SyncRecord } from "./sync-record.ts";

const BUTTON = "project/components/Button/README.md";
const CARD = "project/components/Card/README.md";
const GUIDE = "project/guidelines/index.md";
const NEW = "project/guidelines/new.md";
const NOTE = "project/assets/notes/note.md";

const LISTS: IndexLists = { assetGroups: {}, blobs: {}, docs: null, sections: {} };

function bytes(text: string): Uint8Array {
  return new TextEncoder().encode(text);
}

function hash(path: string, text: string): string {
  return fileHash(path, bytes(text));
}

const PENDING: Pending = {
  files: new Map([[GUIDE, { hash: hash(GUIDE, "# 목표\n"), bytes: 6 }]]),
  delete: [NOTE],
  index: LISTS,
};

function record(claim: Claim | null = null): SyncRecord {
  return {
    v: 1,
    commit: "abc1234",
    at: "2026-10-26T00:00:00.000Z",
    files: new Map([[BUTTON, { hash: hash(BUTTON, "# 버튼\n"), bytes: 9 }]]),
    baseline: { families: [] },
    index: LISTS,
    pending: PENDING,
    claim,
  };
}

const TOKENS = { families: [{ name: "color", tokens: [] }] };

/** 받은 폴더. 웹이 버튼 README 를 고치고 새 지침을 더했다. */
function web(extra: Readonly<Record<string, string>> = {}): Map<string, Uint8Array> {
  return new Map(
    Object.entries({
      [TOKENS_PATH]: JSON.stringify(TOKENS),
      [INDEX_PATH]: JSON.stringify({ v: 1, ...LISTS }),
      [BUTTON]: "# 버튼\n\n웹에서 고침.\n",
      [NEW]: "# 새 지침\n",
      ...extra,
    }).map(([path, text]): [string, Uint8Array] => [path, bytes(text)]),
  );
}

function edits(partial: Partial<WebEdits>): WebEdits {
  return { ...NO_EDITS, ...partial };
}

const FOUND: CheckReading = {
  result: "edited",
  pending: null,
  edits: edits({ revert: [BUTTON], webAdded: [NEW] }),
};

function head(branch: string): ClaimHead {
  return {
    branch,
    ticket: `.scratch/x/issues/${branch.slice(8)}.md`,
    at: "2026-10-27T00:00:00.000Z",
  };
}

const SUMMARY: ClaimSummary = {
  branch: "feature/11-a",
  ticket: ".scratch/x/issues/11-a.md",
  at: "2026-10-27T00:00:00.000Z",
  own: false,
  changed: [BUTTON],
  added: [NEW],
  removed: [],
};

function importing({
  own,
  further = {},
}: {
  readonly own: boolean;
  readonly further?: Partial<WebEdits>;
}): CheckReading {
  return {
    result: "importing",
    pending: null,
    claim: { ...SUMMARY, own },
    further: edits(further),
    inherit: null,
  };
}

/** 웹 편집 있음에서 쓴 claim. */
function written(): Claim {
  const next = claimedRecord({
    current: record(),
    expected: null,
    change: {
      kind: "write",
      head: head("feature/11-a"),
      reading: FOUND,
      web: web(),
      inherit: null,
    },
  });
  if (next.claim === null) {
    throw new Error("claim 이 쓰이지 않았다");
  }
  return next.claim;
}

function caught(run: () => unknown): unknown {
  try {
    run();
  } catch (error) {
    return error;
  }
  return null;
}

describe("기록의 claim", () => {
  test("웹 편집으로 claim 을 쓰면 웹의 tokens.json, 고친 파일과 더한 파일의 해시, 색인 목록을 들고 나머지는 그대로다", () => {
    const next = claimedRecord({
      current: record(),
      expected: null,
      change: {
        kind: "write",
        head: head("feature/11-a"),
        reading: FOUND,
        web: web(),
        inherit: null,
      },
    });

    expect(next).toEqual({
      ...record(),
      claim: {
        ...head("feature/11-a"),
        tokens: TOKENS,
        changed: new Map([[BUTTON, hash(BUTTON, "# 버튼\n\n웹에서 고침.\n")]]),
        added: new Map([[NEW, hash(NEW, "# 새 지침\n")]]),
        removed: [],
        index: LISTS,
        base: null,
      },
    });
  });

  test("claim 을 비우면 pending 과 나머지는 그대로다", () => {
    const next = claimedRecord({
      current: record(written()),
      expected: written(),
      change: { kind: "clear" },
    });

    expect(next).toEqual(record());
  });

  test("이어받는 claim 은 앞 claim 의 파일 목록과 더 고친 몫을 합치고 이어받을 기준본을 사본과 따로 든다", () => {
    const base = { families: [{ name: "inherited", tokens: [] }] };
    const next = claimedRecord({
      current: record(written()),
      expected: written(),
      change: {
        kind: "write",
        head: head("feature/12-b"),
        reading: importing({ own: false, further: { revert: [CARD], webRemoved: [GUIDE] } }),
        web: web({ [CARD]: "# 카드\n" }),
        inherit: base,
      },
    });

    expect(next.claim).toEqual({
      ...head("feature/12-b"),
      tokens: TOKENS,
      changed: new Map([
        [BUTTON, hash(BUTTON, "# 버튼\n\n웹에서 고침.\n")],
        [CARD, hash(CARD, "# 카드\n")],
      ]),
      added: new Map([[NEW, hash(NEW, "# 새 지침\n")]]),
      removed: [GUIDE],
      index: LISTS,
      base,
    });
    expect(next.pending).toEqual(PENDING);
  });

  test("자기 claim 을 고쳐 쓰면 머리와 사본을 새로 쓰고 이어받은 기준본은 그대로다", () => {
    const base = { families: [] };
    const inherited: Claim = { ...written(), base };
    const next = claimedRecord({
      current: record(inherited),
      expected: inherited,
      change: {
        kind: "write",
        head: head("feature/13-a"),
        reading: importing({ own: true }),
        web: web({ [BUTTON]: "# 버튼\n\n다시 고침.\n" }),
        inherit: null,
      },
    });

    expect(next.claim).toMatchObject({
      branch: "feature/13-a",
      changed: new Map([[BUTTON, hash(BUTTON, "# 버튼\n\n다시 고침.\n")]]),
      base,
    });
  });

  test("웹에서 더했다가 다시 지운 경로는 claim 에서 뺀다", () => {
    const files = web();
    files.delete(NEW);
    const next = claimedRecord({
      current: record(written()),
      expected: written(),
      change: {
        kind: "write",
        head: head("feature/11-a"),
        reading: importing({ own: true }),
        web: files,
        inherit: null,
      },
    });

    expect(next.claim?.added).toEqual(new Map());
    expect(next.claim?.removed).toEqual([]);
  });

  test("기록의 claim 이 덮을 claim 과 다르면 input 오류다", () => {
    const error = caught(() =>
      claimedRecord({ current: record(written()), expected: null, change: { kind: "clear" } }),
    );

    expect(error).toBeInstanceOf(CommandError);
    expect(error).toMatchObject({
      kind: "input",
      message:
        "기록의 claim 이 덮을 claim 과 다르다(지금 기록의 claim 은 feature/11-a 의 것이다). 그사이 다른 세션이 쓰거나 지웠으니 확인부터 다시 한다",
    });
  });

  test("남의 claim 은 이어받을 기준본 없이 덮지 않는다", () => {
    const error = caught(() =>
      claimedRecord({
        current: record(written()),
        expected: written(),
        change: {
          kind: "write",
          head: head("feature/12-b"),
          reading: importing({ own: false }),
          web: web(),
          inherit: null,
        },
      }),
    );

    expect(error).toMatchObject({
      kind: "usage",
      message:
        "남의 claim 은 이어받을 기준본(--inherit)이 있을 때만 이어받는다. 지우려면 --clear 로 비운다",
    });
  });

  test("웹 편집 없음의 확인 보고로는 claim 을 쓰지 않는다", () => {
    const error = caught(() =>
      claimedRecord({
        current: record(),
        expected: null,
        change: {
          kind: "write",
          head: head("feature/11-a"),
          reading: { result: "clean", pending: null },
          web: web(),
          inherit: null,
        },
      }),
    );

    expect(error).toMatchObject({
      kind: "usage",
      message:
        "확인 결과가 clean 라 claim 을 쓰지 않는다. 웹 편집 있음이나 들이는 중의 확인 보고로 쓴다",
    });
  });

  test("파일 목록의 차례만 다른 두 claim 은 같다", () => {
    const claim = written();
    const reordered: Claim = { ...claim, changed: new Map([...claim.changed].reverse()) };

    expect(sameClaim(claim, reordered)).toBe(true);
    expect(sameClaim(claim, { ...claim, at: "2026-10-28T00:00:00.000Z" })).toBe(false);
    expect(sameClaim(null, claim)).toBe(false);
  });
});
