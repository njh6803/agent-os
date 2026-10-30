// 이번 올리기가 보낼 파일·지울 경로의 테스트(design-reverse-sync 명세 "올리기"의 첫 올리기와 그 2026-10-22 주석,
// "찾았을 때"의 "덮어쓴다").

import { describe, expect, test } from "vitest";
import { CommandError } from "./command.ts";
import { fileHash } from "./file-hash.ts";
import { sha256, sortedPaths } from "./io.ts";
import { RECORD_LIMIT, type FileEntry, type PendingClass, type SyncRecord } from "./sync-record.ts";
import {
  CALL_BYTES,
  CALL_PATHS,
  INDEX_LIMIT,
  planUpload,
  type UploadCall,
  type UploadInput,
  withLibraries,
  withUpgraded,
} from "./upload.ts";

function bytes(text: string): Uint8Array {
  return new TextEncoder().encode(text);
}

function entry(path: string, text: string): FileEntry {
  const data = bytes(text);
  return { hash: fileHash(path, data), bytes: data.byteLength };
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

const BUTTON = "project/components/Button/README.md";
const BADGE = "project/components/Badge/README.md";
const CARD = "project/components/Card/README.md";
const NOTES = "project/assets/notes/plan.md";

const INDEX = { assetGroups: null, blobs: null, docs: null, sections: null };

/** 앞 기록. 버튼·배지·카드 README 를 올렸다. */
function record(overrides: Partial<SyncRecord> = {}): SyncRecord {
  return {
    v: 1,
    commit: "1111111",
    at: "2026-10-26T00:00:00.000Z",
    files: new Map([
      [BUTTON, entry(BUTTON, "옛 버튼\n")],
      [BADGE, entry(BADGE, "배지\n")],
      [CARD, entry(CARD, "카드\n")],
    ]),
    baseline: {},
    index: INDEX,
    pending: null,
    claim: null,
    ...overrides,
  };
}

function output(files: Record<string, string>): Map<string, Uint8Array> {
  return new Map(Object.entries(files).map(([path, text]) => [path, bytes(text)]));
}

function input(partial: Partial<UploadInput>): UploadInput {
  return {
    record: record(),
    artifactSha256: null,
    output: new Map(),
    previousOutput: null,
    revert: [],
    webRemoved: [],
    webAdded: [],
    pendingState: null,
    ...partial,
  };
}

describe("보낼 파일과 지울 경로", () => {
  test("맞대는 값이 기록과 다른 파일만 보낸다", () => {
    const plan = planUpload(
      input({ output: output({ [BUTTON]: "새 버튼\n", [BADGE]: "배지\n" }) }),
    );

    expect(plan.send).toEqual([BUTTON]);
    expect(plan.unchanged).toEqual([BADGE]);
    expect(plan.delete).toEqual([]);
  });

  test("기록에 없는 새 파일은 보낸다", () => {
    const plan = planUpload(input({ output: output({ [NOTES]: "새 메모\n" }) }));

    expect(plan.send).toEqual([NOTES]);
  });

  test("되돌릴 파일은 코드가 그대로여도 보낸다", () => {
    const plan = planUpload(
      input({ output: output({ [BUTTON]: "새 버튼\n", [BADGE]: "배지\n" }), revert: [BADGE] }),
    );

    expect(plan.send).toEqual([BADGE, BUTTON]);
    expect(plan.unchanged).toEqual([]);
  });

  test("되돌릴 파일이 이번 산출에도 지울 경로에도 없으면 멈춘다", () => {
    const thrown = caught(() => planUpload(input({ output: output({}), revert: [BADGE] })));

    expect(thrown).toBeInstanceOf(CommandError);
    expect(thrown).toMatchObject({
      kind: "input",
      message: `되돌릴 ${BADGE} 가 이번 산출에 없고 지난 산출 목록과 pending 의 지울 경로에도 없다`,
    });
  });

  test("웹이 고친 파일을 코드가 뺐으면 덮어쓰기가 지운다", () => {
    const plan = planUpload(
      input({
        output: output({ [BUTTON]: "옛 버튼\n", [BADGE]: "배지\n" }),
        previousOutput: [BUTTON, BADGE, CARD],
        revert: [CARD],
      }),
    );

    expect(plan.delete).toEqual([CARD]);
    expect(plan.send).toEqual([]);
  });

  test("덮어쓰기는 웹이 지운 파일을 이번 산출의 판으로 되살린다", () => {
    const plan = planUpload(input({ output: output({ [BADGE]: "배지\n" }), webRemoved: [BADGE] }));

    expect(plan.send).toEqual([BADGE]);
    expect(plan.unchanged).toEqual([]);
  });

  test("웹이 지운 파일을 코드도 뺐으면 지우지 않고 기록에서만 뺀다", () => {
    const plan = planUpload(
      input({
        output: output({ [BUTTON]: "옛 버튼\n", [BADGE]: "배지\n" }),
        previousOutput: [BUTTON, BADGE, CARD],
        webRemoved: [CARD],
      }),
    );

    expect(plan.gone).toEqual([CARD]);
    expect(plan.delete).toEqual([]);
  });

  test("웹이 지운 파일이 이번 산출에도 지울 경로에도 없으면 멈춘다", () => {
    const thrown = caught(() => planUpload(input({ output: output({}), webRemoved: [CARD] })));

    expect(thrown).toBeInstanceOf(CommandError);
    expect(thrown).toMatchObject({
      kind: "input",
      message: `되돌릴 ${CARD} 가 이번 산출에 없고 지난 산출 목록과 pending 의 지울 경로에도 없다`,
    });
  });

  test("지난 산출에 있었고 이번 산출에 없는 경로를 지운다", () => {
    const plan = planUpload(
      input({
        output: output({ [BUTTON]: "옛 버튼\n", [BADGE]: "배지\n" }),
        previousOutput: [BUTTON, BADGE, CARD],
      }),
    );

    expect(plan.delete).toEqual([CARD]);
    expect(plan.send).toEqual([]);
  });

  test("지난 산출의 목록이 없는 부분 올리기는 산출에 없는 기록 파일을 지우지 않는다", () => {
    const plan = planUpload(input({ output: output({ [BUTTON]: "새 버튼\n" }) }));

    expect(plan.delete).toEqual([]);
  });

  test("덮어쓰기는 웹에서 더한 경로를 지운다", () => {
    const plan = planUpload(
      input({
        output: output({ [BUTTON]: "옛 버튼\n" }),
        webAdded: ["project/guidelines/web-only.md"],
      }),
    );

    expect(plan.delete).toEqual(["project/guidelines/web-only.md"]);
  });

  test("웹에서 더한 경로를 코드도 지으면 지우지 않고 코드의 판을 보낸다", () => {
    const plan = planUpload(
      input({ output: output({ [NOTES]: "코드의 메모\n" }), webAdded: [NOTES] }),
    );

    expect(plan.delete).toEqual([]);
    expect(plan.send).toEqual([NOTES]);
  });

  test("기록·색인·페이지가 다시 짓는 파일은 보내거나 지우지 않고 따로 알린다", () => {
    const plan = planUpload(
      input({
        output: output({
          "project/sync-record.json": "{}",
          "project/design-system.json": "{}",
          "project/tokens.css": ":root{}",
          "project/api/tokens.md": "카드",
          [BADGE]: "배지\n",
        }),
        previousOutput: ["project/manifest.json", BADGE],
        webAdded: ["project/api/icons.md"],
      }),
    );

    expect(plan.send).toEqual([]);
    expect(plan.delete).toEqual([]);
    expect(plan.ignored).toEqual([
      "project/api/tokens.md",
      "project/design-system.json",
      "project/sync-record.json",
      "project/tokens.css",
    ]);
  });

  test("tokens.json 은 꼴이 아니라 맞대는 몫으로 견준다", () => {
    const tokens = "project/tokens.json";
    const uploaded = '{"color":{"$type":"color"}}';
    const plan = planUpload(
      input({
        record: record({ files: new Map([[tokens, entry(tokens, uploaded)]]) }),
        output: output({ [tokens]: '{\n  "color": { "$type": "color" }\n}\n' }),
      }),
    );

    expect(plan.unchanged).toEqual([tokens]);
  });
});

describe("기록이 없는 올리기", () => {
  test("아티팩트에서 받은 sha256 과 원 바이트로 맞대 고른다", () => {
    const plan = planUpload(
      input({
        record: null,
        artifactSha256: new Map([
          [BUTTON, sha256(bytes("새 버튼\n"))],
          [BADGE, sha256(bytes("웹의 배지\n"))],
        ]),
        output: output({ [BUTTON]: "새 버튼\n", [BADGE]: "배지\n", [CARD]: "카드\n" }),
      }),
    );

    expect(plan.unchanged).toEqual([BUTTON]);
    expect(plan.send).toEqual([BADGE, CARD]);
  });

  test("되돌릴 파일은 아티팩트와 같아도 보낸다", () => {
    const plan = planUpload(
      input({
        record: null,
        artifactSha256: new Map([[BUTTON, sha256(bytes("새 버튼\n"))]]),
        output: output({ [BUTTON]: "새 버튼\n" }),
        revert: [BUTTON],
      }),
    );

    expect(plan.send).toEqual([BUTTON]);
  });

  test("기록도 아티팩트의 sha256 도 없으면 멈춘다", () => {
    const thrown = caught(() =>
      planUpload(input({ record: null, output: output({ [BUTTON]: "버튼\n" }) })),
    );

    expect(thrown).toBeInstanceOf(CommandError);
    expect(thrown).toMatchObject({
      kind: "usage",
      message: "기록이 없으면 아티팩트에서 받은 sha256 으로 맞대야 한다",
    });
  });
});

describe("멈춘 올리기를 다시 하는 올리기", () => {
  const TARGET_BUTTON = "목표 버튼\n";
  const OLD = "project/assets/notes/old.md";
  const pending = {
    files: new Map([
      [BUTTON, entry(BUTTON, TARGET_BUTTON)],
      [CARD, entry(CARD, "목표 카드\n")],
      [NOTES, entry(NOTES, "목표 메모\n")],
    ]),
    delete: [BADGE, OLD],
    index: INDEX,
  };

  /** 확인이 낸 pending 의 분류. 버튼은 보냈고, 카드와 메모는 아직이며, 배지는 아직 있고 old.md 는 지워졌다. */
  function state(
    overrides: Readonly<Record<string, PendingClass>> = {},
  ): Map<string, PendingClass> {
    return new Map<string, PendingClass>([
      [BUTTON, "sent"],
      [CARD, "unsent"],
      [NOTES, "unsent"],
      [BADGE, "remaining"],
      [OLD, "deleted"],
      ...Object.entries(overrides),
    ]);
  }

  test("목표대로 이미 보낸 파일은 다시 보내지 않고, 목표와 다른 로컬은 보낸다", () => {
    const plan = planUpload(
      input({
        record: record({ pending }),
        output: output({
          [BUTTON]: TARGET_BUTTON,
          [CARD]: "더 고친 카드\n",
          [NOTES]: "목표 메모\n",
        }),
        pendingState: state({ [CARD]: "sent" }),
      }),
    );

    expect(plan.landed).toEqual([BUTTON]);
    expect(plan.send).toEqual([NOTES, CARD]);
  });

  test("아직 보내지 않은 파일은 앞 해시와 맞대 고른다", () => {
    const plan = planUpload(
      input({
        record: record({ pending }),
        output: output({ [CARD]: "카드\n" }),
        pendingState: state(),
      }),
    );

    expect(plan.unchanged).toEqual([CARD]);
    expect(plan.send).toEqual([]);
  });

  test("웹이 고친 pending 의 파일은 보낸다", () => {
    const plan = planUpload(
      input({
        record: record({ pending }),
        output: output({ [CARD]: "카드\n" }),
        pendingState: state({ [CARD]: "edited" }),
      }),
    );

    expect(plan.send).toEqual([CARD]);
  });

  test("들이는 claim 의 것으로 가른 pending 의 파일은 코드가 그대로여도 보낸다", () => {
    const plan = planUpload(
      input({
        record: record({ pending }),
        output: output({ [CARD]: "카드\n" }),
        pendingState: state({ [CARD]: "claimed" }),
      }),
    );

    expect(plan.send).toEqual([CARD]);
  });

  test("이번 산출에 없는 보낸 목표는 목표대로 이어 적는다", () => {
    const plan = planUpload(
      input({ record: record({ pending }), output: output({}), pendingState: state() }),
    );

    expect(plan.landed).toEqual([BUTTON]);
    expect(plan.send).toEqual([]);
  });

  test("지난 산출 목록을 준 산출에 없는 보낸 목표는 이어 적지 않고 지운다", () => {
    const plan = planUpload(
      input({
        record: record({ pending }),
        output: output({ [CARD]: "카드\n" }),
        previousOutput: [BUTTON, CARD],
        pendingState: state(),
      }),
    );

    expect(plan.landed).toEqual([]);
    expect(plan.delete).toEqual([BADGE, BUTTON]);
  });

  test("멈춘 올리기가 더한 보낸 목표를 코드가 뺐으면 지난 산출 목록에 없어도 지운다", () => {
    const plan = planUpload(
      input({
        record: record({ pending }),
        output: output({ [BUTTON]: TARGET_BUTTON, [CARD]: "카드\n" }),
        previousOutput: [BUTTON, CARD],
        pendingState: state({ [NOTES]: "sent" }),
      }),
    );

    expect(plan.landed).toEqual([BUTTON]);
    expect(plan.delete).toEqual([NOTES, BADGE]);
  });

  test("지울 경로가 아직 있으면 지우고, 이미 지워졌으면 기록에서만 뺀다", () => {
    const plan = planUpload(
      input({
        record: record({ pending }),
        output: output({ [BUTTON]: TARGET_BUTTON }),
        previousOutput: [BADGE, OLD],
        pendingState: state(),
      }),
    );

    expect(plan.delete).toEqual([BADGE]);
    expect(plan.gone).toEqual([OLD]);
  });

  test("지워진 경로를 이번 산출이 지으면 보낸다", () => {
    const plan = planUpload(
      input({
        record: record({ pending }),
        output: output({ [BADGE]: "배지\n" }),
        pendingState: state({ [BADGE]: "deleted" }),
      }),
    );

    expect(plan.send).toEqual([BADGE]);
    expect(plan.gone).toEqual([OLD]);
  });

  test("웹이 고친 지울 경로는 덮어쓰기가 지운다", () => {
    const plan = planUpload(
      input({
        record: record({ pending }),
        output: output({}),
        revert: [BADGE],
        pendingState: state({ [BADGE]: "edited" }),
      }),
    );

    expect(plan.delete).toEqual([BADGE]);
    expect(plan.gone).toEqual([OLD]);
  });

  test("pending 이 든 기록에 확인의 분류가 없으면 멈춘다", () => {
    const thrown = caught(() =>
      planUpload(input({ record: record({ pending }), output: output({}) })),
    );

    expect(thrown).toBeInstanceOf(CommandError);
    expect(thrown).toMatchObject({
      kind: "usage",
      message: "앞 기록에 pending 이 있어 확인이 낸 pending 의 분류가 있어야 한다",
    });
  });

  test("확인의 분류가 pending 의 경로 하나를 빠뜨리면 멈춘다", () => {
    const partial = state();
    partial.delete(OLD);
    const thrown = caught(() =>
      planUpload(input({ record: record({ pending }), output: output({}), pendingState: partial })),
    );

    expect(thrown).toBeInstanceOf(CommandError);
    expect(thrown).toMatchObject({
      kind: "input",
      message: `확인의 pending 분류에 ${OLD} 가 없다`,
    });
  });
});

describe("한 경로가 드는 칸", () => {
  const CHIP = "project/components/Chip/README.md";
  const LOCAL = "로컬\n";
  const OTHER = "다른 판\n";
  const SLOTS = ["send", "landed", "unchanged", "delete", "gone", "ignored"] as const;
  /** 지난 산출 목록. 목록을 주지 않은 계획, 목록을 준 두 계획(그 경로가 없다·있다)이다. */
  const PREVIOUS: readonly (readonly string[] | null)[] = [null, [], [CHIP]];

  type Change = "removed" | "changed" | "added" | null;

  /**
   * 확인(`check.ts` 의 `classifyFile`)이 한 경로에 낼 수 있는 `pending` 의 자리, 분류, 웹의 바뀜의 짝. `removed`·`changed`
   * 는 기록에 있는 파일의, `added` 는 기록에 없는 파일의 바뀜이다. 그 함수가 짝을 더하면 이 표에도 더한다.
   */
  const VERDICTS: readonly {
    readonly role: "none" | "file" | "delete";
    readonly pending: PendingClass | null;
    readonly change: Change;
  }[] = [
    { role: "none", pending: null, change: null },
    { role: "none", pending: null, change: "removed" },
    { role: "none", pending: null, change: "changed" },
    { role: "none", pending: null, change: "added" },
    { role: "file", pending: "sent", change: null },
    { role: "file", pending: "unsent", change: null },
    { role: "file", pending: "edited", change: "removed" },
    { role: "file", pending: "edited", change: "changed" },
    { role: "file", pending: "edited", change: "added" },
    { role: "delete", pending: "deleted", change: null },
    { role: "delete", pending: "remaining", change: null },
    { role: "delete", pending: "edited", change: "changed" },
    { role: "delete", pending: "edited", change: "added" },
    // 들이는 중의 올리기는 claim 이 든 파일을 되돌릴 파일, 지운 경로, 더한 경로로 넘긴다
    { role: "file", pending: "claimed", change: null },
    { role: "file", pending: "claimed", change: "changed" },
    { role: "file", pending: "claimed", change: "removed" },
    { role: "file", pending: "claimed", change: "added" },
    { role: "delete", pending: "claimed", change: "changed" },
    { role: "delete", pending: "claimed", change: "added" },
  ];

  interface Case {
    readonly name: string;
    readonly given: UploadInput;
    /** 되돌릴 파일이 이번 산출에도, 코드가 뺀 경로로 알려진 자리(지난 산출 목록, `pending` 의 지울 경로)에도 없다. */
    readonly stray: boolean;
  }

  /** 앞 기록의 해시, 이번 산출, `pending` 의 목표, 확인의 짝, 지난 산출 목록의 모든 조합. */
  function cases(): Case[] {
    const found: Case[] = [];
    for (const before of [null, LOCAL, OTHER]) {
      for (const local of [null, LOCAL]) {
        for (const target of [LOCAL, OTHER]) {
          for (const verdict of VERDICTS) {
            for (const previousOutput of PREVIOUS) {
              const { role, change } = verdict;
              if (
                (role !== "file" && target === OTHER) ||
                (change !== null && (change === "added") !== (before === null))
              ) {
                continue;
              }
              const pending =
                role === "none"
                  ? null
                  : {
                      files: new Map(role === "file" ? [[CHIP, entry(CHIP, target)]] : []),
                      delete: role === "delete" ? [CHIP] : [],
                      index: INDEX,
                    };
              const given = input({
                record: record({
                  files: new Map(before === null ? [] : [[CHIP, entry(CHIP, before)]]),
                  pending,
                }),
                output: local === null ? new Map() : output({ [CHIP]: local }),
                previousOutput,
                revert: change === "changed" ? [CHIP] : [],
                webRemoved: change === "removed" ? [CHIP] : [],
                webAdded: change === "added" ? [CHIP] : [],
                pendingState: verdict.pending === null ? null : new Map([[CHIP, verdict.pending]]),
              });
              const shown = (text: string | null): string =>
                text === null ? "없음" : text === LOCAL ? "로컬" : "다른 판";
              found.push({
                name: `기록 ${shown(before)}, 산출 ${shown(local)}, 목표 ${shown(target)}, ${role}/${String(verdict.pending)}/${String(change)}, 지난 산출 ${JSON.stringify(previousOutput)}`,
                given,
                stray:
                  local === null &&
                  (change === "removed" || change === "changed") &&
                  role !== "delete" &&
                  previousOutput?.includes(CHIP) !== true,
              });
            }
          }
        }
      }
    }
    return found;
  }

  test("확인이 낼 수 있는 어느 조합에서도 한 경로는 많아야 한 칸에 든다", () => {
    const overlaps: string[] = [];
    for (const { name, given, stray } of cases()) {
      if (stray) {
        continue;
      }
      const plan = planUpload(given);
      const slots = SLOTS.filter((slot) => plan[slot].includes(CHIP));
      if (slots.length > 1) {
        overlaps.push(`${name}: ${slots.join(", ")}`);
      }
    }

    expect(overlaps).toEqual([]);
  });

  test("되돌릴 파일이 갈 데 없는 조합에서만 멈춘다", () => {
    const wrong = cases()
      .filter(
        ({ given, stray }) => caught(() => planUpload(given)) instanceof CommandError !== stray,
      )
      .map(({ name, stray }) => `${name}: ${stray ? "멈추지 않았다" : "멈췄다"}`);

    expect(wrong).toEqual([]);
  });
});

// design-card-build 명세 "올리기"의 "옛 별칭 지우기", "첫 정식 올리기와 `tokens.json`", "목록만 옛것일 때", "나누기",
// "색인의 `libraries`", "`upgraded`"와 Testing Decisions "올리기 시험"의 사례(티켓 03).

const TOKENS = "project/tokens.json";
const LAYERS = [
  ["atoms", ["Button", "Card", "Icon", "IconButton", "Progress", "StatusBadge"]],
  ["molecules", ["Alert", "Switch", "TextField"]],
] as const;
const NAMES = LAYERS.flatMap(([, names]) => names);

/**
 * 옛 배치에만 있는 옛 별칭 48개. 카드 36, `_preview/` 9, `_vendor/` 2, `_ds_sync.json` 이다. 옛 배치는 짓기 명령 전에
 * 올라간 배치이고, 카드가 `components/<무리>/<이름>/` 아래에 있다.
 */
const OLD_ALIASES = [
  ...LAYERS.flatMap(([layer, names]) =>
    names.flatMap((name) =>
      ["d.ts", "html", "jsx", "prompt.md"].map(
        (suffix) => `project/components/${layer}/${name}/${name}.${suffix}`,
      ),
    ),
  ),
  ...NAMES.map((name) => `project/_preview/${name}.js`),
  "project/_vendor/react-dom.js",
  "project/_vendor/react.js",
  "project/_ds_sync.json",
];

/** 두 배치가 함께 짓는 파일. 이름만 바뀐 `tokens.json` 도 지문이 같아 같은 바이트로 둔다. */
const SHARED: Readonly<Record<string, string>> = {
  "project/README.md": "# Agent OS\n",
  [TOKENS]: '{"name":"Agent OS"}',
  "project/_ds_bundle.js": "window.AgentOsUi={};",
  "project/_ds_bundle.css": ":root{}",
  "project/styles.css": '@import "./fonts/fonts.css";',
  "project/fonts/a.woff2": "글꼴",
};

/** 옛 배치. */
function oldLayout(): Record<string, string> {
  return { ...SHARED, ...Object.fromEntries(OLD_ALIASES.map((path) => [path, `옛 ${path}`])) };
}

/** 짓기 명령의 정식 배치. 카드는 `components/<이름>/preview.html` 이다. */
function canonical(): Record<string, string> {
  return {
    ...SHARED,
    "project/components/bundle.js": "window.AgentOsUi={};",
    "project/components/bundle.css": ":root{}",
    ...Object.fromEntries(
      NAMES.flatMap((name) => [
        [`project/components/${name}/preview.html`, `<!-- @dsCard group="atoms" -->${name}`],
        [`project/components/${name}/README.md`, `# ${name}\n`],
      ]),
    ),
  };
}

/** 그 파일들을 모두 보낸 기록. */
function recordOf(files: Readonly<Record<string, string>>): SyncRecord {
  return record({
    files: new Map(Object.entries(files).map(([path, text]) => [path, entry(path, text)])),
  });
}

function sha256Of(files: Readonly<Record<string, string>>): Map<string, string> {
  return new Map(Object.entries(files).map(([path, text]) => [path, sha256(bytes(text))]));
}

describe("옛 배치에서 정식 배치로 옮기는 올리기", () => {
  test("지난 목록과 기록에 든 옛 별칭 48개를 모두 지운다", () => {
    const plan = planUpload(
      input({
        record: recordOf(oldLayout()),
        output: output(canonical()),
        previousOutput: Object.keys(oldLayout()),
      }),
    );

    expect(OLD_ALIASES).toHaveLength(48);
    expect(plan.delete).toEqual(sortedPaths(OLD_ALIASES));
  });

  test("기록에 정식 카드가 없고 이번 산출에 있으면 첫 정식 올리기라 지문이 같아도 tokens.json 을 보낸다", () => {
    const plan = planUpload(
      input({
        record: recordOf(oldLayout()),
        output: output(canonical()),
        previousOutput: Object.keys(oldLayout()),
      }),
    );

    expect(plan.firstCanonical).toBe(true);
    expect(plan.send).toContain(TOKENS);
    expect(plan.unchanged).not.toContain(TOKENS);
  });

  test("앞 시도가 tokens.json 을 목표대로 보낸 이어 받는 올리기도 tokens.json 을 다시 보낸다", () => {
    const card = "project/components/Button/preview.html";
    const target = canonical();
    const pending = {
      files: new Map([
        [TOKENS, entry(TOKENS, target[TOKENS] ?? "")],
        [card, entry(card, target[card] ?? "")],
      ]),
      delete: OLD_ALIASES,
      index: INDEX,
    };
    const plan = planUpload(
      input({
        record: { ...recordOf(oldLayout()), pending },
        output: output(target),
        previousOutput: Object.keys(oldLayout()),
        pendingState: new Map<string, PendingClass>([
          [TOKENS, "sent"],
          [card, "sent"],
          ...OLD_ALIASES.map((path): [string, PendingClass] => [path, "remaining"]),
        ]),
      }),
    );

    expect(plan.firstCanonical).toBe(true);
    expect(plan.send).toContain(TOKENS);
    expect(plan.landed).toEqual([card]);
  });

  test("기록에 정식 카드가 있으면 첫 정식 올리기가 아니라 tokens.json 을 지문대로 다룬다", () => {
    const plan = planUpload(input({ record: recordOf(canonical()), output: output(canonical()) }));

    expect(plan.firstCanonical).toBe(false);
    expect(plan.unchanged).toContain(TOKENS);
    expect(plan.send).toEqual([]);
  });

  test("기록이 없으면 받은 sha256 목록에 정식 카드가 있는지로 가른다", () => {
    const fromBorrowed = planUpload(
      input({ record: null, artifactSha256: sha256Of(oldLayout()), output: output(canonical()) }),
    );
    const fromCanonical = planUpload(
      input({ record: null, artifactSha256: sha256Of(canonical()), output: output(canonical()) }),
    );

    expect(fromBorrowed.firstCanonical).toBe(true);
    expect(fromBorrowed.send).toContain(TOKENS);
    expect(fromCanonical.firstCanonical).toBe(false);
    expect(fromCanonical.unchanged).toContain(TOKENS);
  });

  test("다 보낸 뒤 지난 목록만 옛것이면 tokens.json 도 옛 경로도 다시 다루지 않는다", () => {
    const plan = planUpload(
      input({
        record: recordOf(canonical()),
        output: output(canonical()),
        previousOutput: Object.keys(oldLayout()),
      }),
    );

    expect(plan.firstCanonical).toBe(false);
    expect(plan.send).toEqual([]);
    expect(plan.delete).toEqual([]);
  });

  test("기록이 없으면 지난 목록대로 지운다", () => {
    const plan = planUpload(
      input({
        record: null,
        artifactSha256: sha256Of(oldLayout()),
        output: output(canonical()),
        previousOutput: Object.keys(oldLayout()),
      }),
    );

    expect(plan.delete).toEqual(sortedPaths(OLD_ALIASES));
  });
});

describe("정식 카드가 없는 산출", () => {
  test("정식 카드가 없는 산출은 첫 정식 올리기가 아니고 tokens.json 을 지문대로 다룬다", () => {
    const plan = planUpload(
      input({
        record: recordOf(oldLayout()),
        output: output(oldLayout()),
        previousOutput: Object.keys(oldLayout()),
      }),
    );

    expect(plan.firstCanonical).toBe(false);
    expect(plan.unchanged).toContain(TOKENS);
    expect(plan.send).toEqual([]);
    expect(plan.delete).toEqual([]);
  });

  test("기록에 든 지난 경로는 지우고, 기록에 없는 지난 경로만 내지 않는다", () => {
    const dropped = OLD_ALIASES.filter((path) => path.includes("/Switch/"));
    const now = Object.entries(oldLayout()).filter(([path]) => !dropped.includes(path));
    const plan = planUpload(
      input({
        record: recordOf(oldLayout()),
        output: output(Object.fromEntries(now)),
        previousOutput: [...Object.keys(oldLayout()), "project/guidelines/old.md"],
      }),
    );

    expect(plan.delete).toEqual(sortedPaths(dropped));
  });
});

describe("호출 몫", () => {
  /** 몫마다 센 경로 수. 나뉘면 첫 호출이 `pending` 이 든 기록을, 마지막 호출이 기록과 색인을 더 싣는다. */
  function pathCounts(calls: readonly UploadCall[]): number[] {
    return calls.map(
      (call, at) =>
        call.send.length +
        call.delete.length +
        (calls.length === 1 ? 2 : at === 0 ? 1 : at === calls.length - 1 ? 2 : 0),
    );
  }

  test("한 호출에 들면 몫이 하나이고 보낼 파일과 지울 경로를 모두 든다", () => {
    const plan = planUpload(
      input({
        record: recordOf(oldLayout()),
        output: output(canonical()),
        previousOutput: Object.keys(oldLayout()),
      }),
    );

    expect(plan.calls).toEqual([{ send: plan.send, delete: plan.delete }]);
  });

  test("빈 시스템에 글꼴 770개를 처음 올리면 몫마다 기록·색인을 세어 255개를 넘지 않게 넷으로 나눈다", () => {
    const files = canonical();
    for (let index = 0; index < 770; index += 1) {
      files[`project/fonts/noto-${String(index).padStart(3, "0")}.woff2`] = "글꼴";
    }
    const plan = planUpload(
      input({ record: null, artifactSha256: new Map(), output: output(files) }),
    );

    expect(plan.send.length).toBeGreaterThan(770);
    expect(plan.calls).toHaveLength(4);
    expect(Math.max(...pathCounts(plan.calls))).toBeLessThanOrEqual(CALL_PATHS);
    expect(sortedPaths(plan.calls.flatMap((call) => call.send))).toEqual(plan.send);
  });

  test("지울 경로도 몫에 세어 255개를 넘지 않는다", () => {
    const previous = Array.from(
      { length: 300 },
      (_, index) => `project/old/${String(index).padStart(3, "0")}.md`,
    );
    const plan = planUpload(
      input({
        record: recordOf(Object.fromEntries(previous.map((path) => [path, "옛것"]))),
        output: output(canonical()),
        previousOutput: previous,
      }),
    );

    expect(plan.delete).toHaveLength(300);
    expect(plan.calls.length).toBeGreaterThan(1);
    expect(Math.max(...pathCounts(plan.calls))).toBeLessThanOrEqual(CALL_PATHS);
    expect(sortedPaths(plan.calls.flatMap((call) => call.delete))).toEqual(plan.delete);
  });

  test("바이트가 16MiB 를 넘으면 기록·색인의 몫을 남기고 나눈다", () => {
    // 둘은 16MiB 에 들지만 기록의 몫을 더하면 넘는 크기다
    const size = CALL_BYTES / 2 - 100_000;
    const plan = planUpload(
      input({
        record: null,
        artifactSha256: new Map(),
        output: new Map(
          ["project/a.bin", "project/b.bin", "project/c.bin"].map((path) => [
            path,
            new Uint8Array(size),
          ]),
        ),
      }),
    );
    const sizes = plan.calls.map(
      (call, at) =>
        call.send.length * size +
        (at === 0 ? RECORD_LIMIT : 0) +
        (at === plan.calls.length - 1 ? RECORD_LIMIT + INDEX_LIMIT : 0),
    );

    expect(plan.calls.length).toBeGreaterThan(1);
    expect(Math.max(...sizes)).toBeLessThanOrEqual(CALL_BYTES);
  });

  /** 몫마다 보낼 파일의 바이트와, 그 호출이 싣는 기록·색인의 한도를 더한 값. */
  function callBytes(calls: readonly UploadCall[], sizes: ReadonlyMap<string, number>): number[] {
    return calls.map(
      (call, at) =>
        call.send.reduce((sum, path) => sum + (sizes.get(path) ?? 0), 0) +
        (calls.length === 1
          ? RECORD_LIMIT + INDEX_LIMIT
          : at === 0
            ? RECORD_LIMIT
            : at === calls.length - 1
              ? RECORD_LIMIT + INDEX_LIMIT
              : 0),
    );
  }

  test("남은 큰 파일이 기록·색인과 함께 들지 않으면 그 파일만 보내고 마지막 몫은 기록과 색인만 싣는다", () => {
    const sizes = new Map([
      ["project/a.bin", 1_000],
      ["project/b.bin", CALL_BYTES - RECORD_LIMIT],
    ]);
    const plan = planUpload(
      input({
        record: null,
        artifactSha256: new Map(),
        output: new Map([...sizes].map(([path, size]) => [path, new Uint8Array(size)])),
      }),
    );

    expect(plan.calls).toEqual([
      { send: ["project/a.bin"], delete: [] },
      { send: ["project/b.bin"], delete: [] },
      { send: [], delete: [] },
    ]);
    expect(Math.max(...callBytes(plan.calls, sizes))).toBeLessThanOrEqual(CALL_BYTES);
  });

  test("첫 파일이 pending 기록과 함께 들지 않으면 첫 몫은 기록만 싣는다", () => {
    const sizes = new Map([["project/huge.bin", CALL_BYTES - 100]]);
    const plan = planUpload(
      input({
        record: null,
        artifactSha256: new Map(),
        output: new Map([...sizes].map(([path, size]) => [path, new Uint8Array(size)])),
      }),
    );

    expect(plan.calls).toEqual([
      { send: [], delete: [] },
      { send: ["project/huge.bin"], delete: [] },
      { send: [], delete: [] },
    ]);
    expect(Math.max(...callBytes(plan.calls, sizes))).toBeLessThanOrEqual(CALL_BYTES);
  });

  test("한 파일이 한 호출에 들지 않으면 멈춘다", () => {
    const thrown = caught(() =>
      planUpload(
        input({
          record: null,
          artifactSha256: new Map(),
          output: new Map([["project/huge.bin", new Uint8Array(CALL_BYTES + 1)]]),
        }),
      ),
    );

    expect(thrown).toBeInstanceOf(CommandError);
    expect(thrown).toMatchObject({ kind: "limit" });
  });
});

describe("보낼 색인", () => {
  const RECEIVED = {
    v: 3,
    layout: "files",
    title: "Agent OS",
    libraries: [],
    source: { app: "claude-design", v: 1 },
    lastChange: { by: "Claude", via: "agent-os main@abc1234" },
  };

  test("묶음을 싣는 색인은 React 18.3.1 과 global 을 적고 source 와 다른 칸을 남긴다", () => {
    expect(withLibraries(RECEIVED)).toEqual({
      ...RECEIVED,
      libraries: [
        { name: "react", version: "18.3.1", global: "React" },
        { name: "react-dom", version: "18.3.1", global: "ReactDOM" },
      ],
    });
  });

  test("첫 정식 올리기의 색인은 upgraded 를 더하고 다른 칸을 남긴다", () => {
    expect(withUpgraded(RECEIVED, "2026-10-29T12:00:00.000Z")).toEqual({
      ...RECEIVED,
      upgraded: { at: "2026-10-29T12:00:00.000Z" },
    });
  });

  test("이미 있는 upgraded 는 그대로 둔다", () => {
    const upgraded = { at: "2026-10-01T00:00:00.000Z" };
    const sent = withUpgraded({ ...RECEIVED, upgraded }, "2026-10-29T12:00:00.000Z");

    expect(sent.upgraded).toEqual(upgraded);
  });
});
