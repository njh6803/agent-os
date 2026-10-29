// 결정표의 테스트(design-reverse-sync 06 티켓 "결정표 함수", 명세 "확인"·"찾았을 때"·"겹침"과 그 2026-10-22 주석들).
// 들이는 중의 칸은 부르는 쪽 셋 × claim(자기, 남의) × PR 상태 다섯 × 더 고친 몫을 표 하나로 두고, 칸마다 낸 할 일이나
// 선택지 라벨을 글자로 맞댄다.

import { describe, expect, test } from "vitest";
import { NO_EDITS, type CheckReading } from "./check-report.ts";
import { CommandError } from "./command.ts";
import { CALLERS, decide, prStateOf, type Caller, type Decision, type PrState } from "./decide.ts";

const OWNERS = ["own", "other"] as const;
const PRS = ["open", "merged", "closed", "none", "failed"] as const;

type Owner = (typeof OWNERS)[number];
type Pr = (typeof PRS)[number];

function prState(pr: Pr): PrState {
  switch (pr) {
    case "open":
    case "merged":
    case "closed":
      return { kind: pr, number: 7, url: "https://github.com/o/r/pull/7", mergeCommit: null };
    case "none":
      return { kind: "none" };
    case "failed":
      return { kind: "failed", message: "gh: 인증이 없다" };
  }
}

function importing(
  owner: Owner,
  { further }: { readonly further: boolean },
): Extract<CheckReading, { result: "importing" }> {
  return {
    result: "importing",
    pending: null,
    claim: {
      branch: "feature/11-web-edit",
      ticket: ".scratch/x/issues/11-web-edit.md",
      at: "2026-10-27T09:00:00.000Z",
      own: owner === "own",
      changed: ["project/README.md"],
      added: [],
      removed: [],
    },
    further: further ? { ...NO_EDITS, revert: ["project/guidelines/index.md"] } : NO_EDITS,
    inherit: further && owner === "other" ? "/tmp/inherit.json" : null,
  };
}

/** 낸 것을 한 줄로 줄인다. 할 일은 `act:<할 일>`, 선택지는 `ask:<라벨>|<라벨>` 이다. */
function shown(decision: Decision): string {
  return decision.kind === "act"
    ? `act:${decision.act}`
    : `ask:${decision.choices.map((choice) => choice.label).join("|")}`;
}

const FOUND_SCREEN = "ask:먼저 들인다|지금 코드 값으로 계속한다";
const FOUND_UPLOAD = "ask:먼저 들인다|웹 편집을 버리고 코드로 덮어쓴다";
const CLEAR = "그 claim을 지운다";
const CLEAR_IMPORT = "그 claim을 지우고 이 세션이 다시 들인다";

/** `<claim>/<PR>/<더 고친 몫>` 마다 화면 작업, 올리기, 들이기가 낼 것. */
const TABLE: Readonly<Record<string, readonly [string, string, string]>> = {
  "own/open/no": ["act:resumeImport", "act:resumeImport", "act:resumeImport"],
  "own/open/yes": ["act:resumeImport", "act:resumeImport", "act:resumeImport"],
  "own/merged/no": ["act:continue", "act:uploadClaimMerged", "act:handToUpload"],
  "own/merged/yes": [FOUND_SCREEN, FOUND_UPLOAD, "act:stop"],
  "own/closed/no": [`ask:멈춘다|${CLEAR}`, `ask:멈춘다|${CLEAR}`, `ask:멈춘다|${CLEAR_IMPORT}`],
  "own/closed/yes": [`ask:멈춘다|${CLEAR}`, `ask:멈춘다|${CLEAR}`, `ask:멈춘다|${CLEAR_IMPORT}`],
  "own/none/no": ["act:resumeImport", "act:resumeImport", "act:resumeImport"],
  "own/none/yes": ["act:resumeImport", "act:resumeImport", "act:resumeImport"],
  "own/failed/no": ["act:stop", "act:stop", "act:stop"],
  "own/failed/yes": ["act:stop", "act:stop", "act:stop"],
  "other/open/no": [
    "ask:그 들이기의 병합을 기다린다|지금 코드 값으로 계속한다",
    "ask:그 병합 뒤에 올린다|웹 편집을 버리고 코드로 덮어쓴다",
    "act:stop",
  ],
  "other/open/yes": [
    "ask:그 들이기의 병합을 기다린다|지금 코드 값으로 계속한다",
    "ask:그 병합 뒤에 올린다|웹 편집을 버리고 코드로 덮어쓴다",
    "act:stop",
  ],
  "other/merged/no": ["act:continue", "act:uploadClaimMerged", "act:handToUpload"],
  "other/merged/yes": [FOUND_SCREEN, FOUND_UPLOAD, "act:inheritImport"],
  "other/closed/no": [
    `ask:그 들이기를 기다린다|${CLEAR}`,
    `ask:그 들이기를 기다린다|${CLEAR}`,
    `ask:그 들이기를 기다린다|${CLEAR_IMPORT}`,
  ],
  "other/closed/yes": [
    `ask:그 들이기를 기다린다|${CLEAR}`,
    `ask:그 들이기를 기다린다|${CLEAR}`,
    `ask:그 들이기를 기다린다|${CLEAR_IMPORT}`,
  ],
  "other/none/no": [
    `ask:그 들이기를 기다린다|${CLEAR}`,
    `ask:그 들이기를 기다린다|${CLEAR}`,
    `ask:그 들이기를 기다린다|${CLEAR_IMPORT}`,
  ],
  "other/none/yes": [
    `ask:그 들이기를 기다린다|${CLEAR}`,
    `ask:그 들이기를 기다린다|${CLEAR}`,
    `ask:그 들이기를 기다린다|${CLEAR_IMPORT}`,
  ],
  "other/failed/no": ["act:stop", "act:stop", "act:stop"],
  "other/failed/yes": ["act:stop", "act:stop", "act:stop"],
};

interface Cell {
  readonly key: string;
  readonly caller: Caller;
  readonly owner: Owner;
  readonly pr: Pr;
  readonly further: boolean;
}

function cells(): Cell[] {
  return OWNERS.flatMap((owner) =>
    PRS.flatMap((pr) =>
      [false, true].flatMap((further) =>
        CALLERS.map((caller) => ({
          key: `${owner}/${pr}/${further ? "yes" : "no"}`,
          caller,
          owner,
          pr,
          further,
        })),
      ),
    ),
  );
}

function caught(run: () => unknown): unknown {
  try {
    run();
  } catch (error) {
    return error;
  }
  return null;
}

describe("들이는 중의 결정표", () => {
  test("표의 칸은 부르는 쪽 × claim × PR 상태 × 더 고친 몫을 모두 덮는다", () => {
    expect(Object.keys(TABLE).sort()).toEqual([...new Set(cells().map((cell) => cell.key))].sort());
  });

  test.each(cells())("$key 에서 $caller 가 낼 것", (cell) => {
    const decision = decide({
      caller: cell.caller,
      reading: importing(cell.owner, { further: cell.further }),
      pr: prState(cell.pr),
    });

    expect(shown(decision)).toBe(TABLE[cell.key]?.[CALLERS.indexOf(cell.caller)]);
  });

  test("남의 열린 PR 에서 덮어쓰는 선택지는 병합 뒤 다시 올라간다고 설명하고 claim 을 비우지 않는다", () => {
    const decision = decide({
      caller: "upload",
      reading: importing("other", { further: false }),
      pr: prState("open"),
    });

    expect(decision.kind === "ask" ? decision.choices[1] : null).toEqual({
      label: "웹 편집을 버리고 코드로 덮어쓴다",
      effect:
        "웹 편집을 코드의 판으로 되돌려 올린다. claim 은 남아, 그 PR 이 병합되면 들인 값이 그 뒤의 올리기로 다시 올라간다",
      act: "overwrite",
    });
  });

  test("남의 열린 PR 의 들이기는 브랜치와 PR 을 보이고 멈추며, 더 고친 몫이 있으면 병합 뒤에 다시 부르라고 적는다", () => {
    const decision = decide({
      caller: "import",
      reading: importing("other", { further: true }),
      pr: prState("open"),
    });

    expect(decision.notes).toEqual([
      "feature/11-web-edit 가 들이는 중이다(티켓 .scratch/x/issues/11-web-edit.md, 2026-10-27T09:00:00.000Z)",
      "claim 뒤에 더 고친 몫: project/guidelines/index.md",
      "PR #7 https://github.com/o/r/pull/7 가 열려 있다",
      "티켓을 쓰지 않고 멈춘다",
      "더 고친 몫은 그 병합 뒤에 다시 부른다",
    ]);
  });

  test("병합된 claim 에 더 고친 몫이 있으면 먼저 들인다가 이어받는 들이기이고, 덮어쓰기는 claim 을 비운다", () => {
    const decision = decide({
      caller: "upload",
      reading: importing("other", { further: true }),
      pr: prState("merged"),
    });

    expect(decision.kind === "ask" ? decision.choices.map((choice) => choice.act) : []).toEqual([
      "inheritImport",
      "overwriteClaimMerged",
    ]);
  });

  test("병합된 남의 claim 에 더 고친 몫이 있는데 이어받을 기준본이 없으면 들이기는 멈추고 다시 돌리라고 적는다", () => {
    const reading: CheckReading = { ...importing("other", { further: true }), inherit: null };
    const decision = decide({ caller: "import", reading, pr: prState("merged") });

    expect(decision).toMatchObject({ kind: "act", act: "stop" });
    expect(decision.notes.at(-1)).toBe(
      "이어받을 기준본이 없다. check judge 를 --inherit-out 과 함께 다시 돌린다",
    );
  });

  test("병합된 자기 브랜치의 들이기는 이어받지 않고 새 티켓 브랜치에서 다시 하라고 적는다", () => {
    const decision = decide({
      caller: "import",
      reading: importing("own", { further: true }),
      pr: prState("merged"),
    });

    expect(decision.notes.at(-1)).toBe(
      "병합된 자기 브랜치에서는 이어받지 않는다. 새 티켓 브랜치에서 확인부터 다시 한다",
    );
  });

  test("gh 가 실패하면 까닭을 보이고 멈춘다", () => {
    const decision = decide({
      caller: "screen",
      reading: importing("other", { further: false }),
      pr: prState("failed"),
    });

    expect(decision.notes.at(-1)).toBe("PR 상태를 보지 못했다: gh: 인증이 없다");
  });

  test("병합된 claim 은 병합 커밋을 보이고, 더 고친 몫이 있어 물어도 병합 커밋을 품었는지 보라고 적는다", () => {
    const pr: PrState = { kind: "merged", number: 7, url: null, mergeCommit: "abc1234" };
    const decision = decide({
      caller: "upload",
      reading: importing("other", { further: true }),
      pr,
    });

    expect(decision).toMatchObject({ kind: "ask" });
    expect(decision.notes).toContain("PR #7 가 병합됐다(병합 커밋 abc1234)");
    expect(decision.notes).toContain(
      "그 병합 커밋이 지금 HEAD 의 조상이 아니면 origin/main 을 다시 받아 처음부터 한다",
    );
  });

  test("들이는 중인데 PR 상태가 없으면 usage 오류다", () => {
    const error = caught(() =>
      decide({ caller: "upload", reading: importing("own", { further: false }), pr: null }),
    );

    expect(error).toBeInstanceOf(CommandError);
    expect(error).toMatchObject({
      kind: "usage",
      message: "확인이 들이는 중이라 claim 의 브랜치의 PR 상태(--pr 이나 --pr-error)가 있어야 한다",
    });
  });
});

describe("claim 이 없는 결정표", () => {
  const CLEAN: CheckReading = { result: "clean", pending: null };
  const FOUND: CheckReading = { result: "edited", pending: null, edits: NO_EDITS };

  test.each([
    ["웹 편집 없음", CLEAN, ["act:continue", "act:upload", "act:stop"]],
    [
      "기록 전",
      { result: "beforeRecord", pending: null },
      ["act:continue", "act:upload", "act:stop"],
    ],
    ["웹 편집 있음", FOUND, [FOUND_SCREEN, FOUND_UPLOAD, "act:import"]],
    [
      "기록에서 온 판단할 수 없음",
      { result: "undecidable", reason: "noRecord", message: "기록이 없다" },
      ["ask:확인 없이 계속한다|멈춘다", "ask:코드로 덮어쓰고 기록을 새로 쓴다|멈춘다", "act:stop"],
    ],
    [
      "아티팩트를 읽지 못한 판단할 수 없음",
      { result: "undecidable", reason: "readFailed", message: "artifact not found" },
      ["ask:확인 없이 계속한다|멈춘다", "act:stop", "act:stop"],
    ],
  ] satisfies [string, CheckReading, string[]][])("%s", (_name, reading, expected) => {
    expect(CALLERS.map((caller) => shown(decide({ caller, reading, pr: null })))).toEqual(expected);
  });

  test("판단할 수 없음은 까닭과 문구를 보인다", () => {
    const reading: CheckReading = {
      result: "undecidable",
      reason: "readFailed",
      message: "artifact not found",
    };

    expect(decide({ caller: "upload", reading, pr: null }).notes[0]).toBe(
      "확인이 판단할 수 없다(readFailed): artifact not found",
    );
  });

  test("들이는 중이 아닌데 PR 상태를 주면 usage 오류다", () => {
    expect(
      caught(() => decide({ caller: "upload", reading: CLEAN, pr: { kind: "none" } })),
    ).toMatchObject({
      kind: "usage",
      message: "PR 상태는 확인 결과가 들이는 중일 때만 준다",
    });
  });
});

describe("PR 상태 고르기", () => {
  test("열림, 병합, 닫힘 차례로 앞서고 빈 배열은 PR 없음이다", () => {
    const merged = { number: 2, state: "MERGED", url: "u2", mergeCommit: { oid: "abc" } };

    expect(prStateOf("pr.json", [])).toEqual({ kind: "none" });
    expect(prStateOf("pr.json", [{ number: 1, state: "CLOSED" }, merged])).toEqual({
      kind: "merged",
      number: 2,
      url: "u2",
      mergeCommit: "abc",
    });
    expect(prStateOf("pr.json", [merged, { number: 3, state: "OPEN" }])).toMatchObject({
      kind: "open",
      number: 3,
    });
  });

  test("모르는 state 나 배열이 아닌 JSON 은 input 오류다", () => {
    const draft = caught(() => prStateOf("pr.json", [{ state: "DRAFT" }]));
    const single = caught(() => prStateOf("pr.json", { state: "OPEN" }));

    expect(draft).toMatchObject({ kind: "input" });
    expect(draft instanceof Error ? draft.message : "").toContain(
      "PR 의 state 가 OPEN, MERGED, CLOSED 가운데 하나가 아니다",
    );
    expect(single).toMatchObject({ kind: "input" });
    expect(single instanceof Error ? single.message : "").toContain(
      "gh pr list 의 JSON 배열이 아니다",
    );
  });
});
