/**
 * 결정표(design-reverse-sync 명세 "확인"의 "기록이 없거나 읽히지 않을 때"·"아티팩트를 읽지 못할 때", "찾았을 때",
 * "겹침"과 그 2026-10-22 주석들, "이음매"의 2026-10-22 주석). 부르는 쪽, 확인의 결과, 스킬이 본 `claim` 브랜치의 PR
 * 상태로 사람에게 보일 선택지나 묻지 않고 할 일을 낸다. 선택지의 라벨은 명세의 낱말 그대로이고(명세가 `claim` 을
 * 코드 꼴로 적은 자리는 꼴을 떼고 적는다), 고르면 할 일(`act`)과 그 설명(`effect`)이 함께 붙는다. 명세가 낱말을 주지
 * 않은 화면 작업과 올리기의 지우는 선택지만 "그 claim을 지운다"로 이 티켓(06)이 정했다. 병합된 자기 `claim` 에 더
 * 고친 몫이 있는 들이기도 명세가 가르지 않아, 병합된 브랜치에서 이어받지 않고 멈추는 것으로 이 티켓이 정했다.
 *
 * 명령: `decide --caller <screen|upload|import> --check <확인 보고> [--pr <PR 목록> | --pr-error <문구>]`. 부르는 쪽은
 * 화면 작업, 올리기, 들이기다. PR 목록은 스킬이 `gh pr list --head <claim 의 브랜치> --state all --json
 * number,state,url,mergeCommit` 으로 받은 JSON 배열이고, `gh` 가 실패하면 대신 그 문구를 준다. 둘은 확인 결과가 들이는
 * 중일 때만 있어야 한다. 배열에 열린 PR 이 있으면 열림, 없고 병합된 PR 이 있으면 병합, 닫힌 PR 만 있으면 닫힘, 비면
 * 없음이다. 보고는 `kind`(`ask` 나 `act`), `choices` 나 `act`, 사람에게 함께 보일 `notes` 다.
 *
 * 못 보는 것: 지금 브랜치가 병합 커밋을 품었는지, 지금 계정이 누구인지는 보지 않는다. 앞의 것은 화면 작업과 올리기의
 * 할 일에 적고 스킬이 git 으로 본다. 뒤의 것은 아티팩트를 읽지 못한 까닭과 함께 스킬이 보인다.
 */

import { parseArgs } from "node:util";
import { isEmpty, readCheckReport, RECORD_REASONS, type CheckReading } from "./check-report.ts";
import { CommandError, parsedArgs, type ReportFields } from "./command.ts";
import { TOKENS_PATH } from "./file-hash.ts";
import { inputError, isRecord, readJson, unknownList } from "./io.ts";

export const CALLERS = ["screen", "upload", "import"] as const;

export type Caller = (typeof CALLERS)[number];

/** 고르거나 묻지 않고 할 일. */
export const ACTS = [
  /** 하던 일을 잇는다(화면 작업). */
  "continue",
  /** 확인이 고른 대로 올린다. */
  "upload",
  /** 웹 편집을 버리고 코드로 덮어쓴다(`record plan --overwrite`). `claim` 은 비우지 않는다. */
  "overwrite",
  /** 병합된 `claim` 의 파일과 더 고친 몫을 코드로 덮어쓰고 `claim` 을 비운다(`--claim-merged --overwrite`). */
  "overwriteClaimMerged",
  /** 병합된 `claim` 의 파일을 보내고 `claim` 을 비운다(`--claim-merged`). */
  "uploadClaimMerged",
  /** 기록 없이 아티팩트의 sha256 과 맞대 올리고 기록을 새로 쓴다(`--artifact-sha256`). */
  "rewriteRecord",
  /** 새 들이기를 연다. */
  "import",
  /** 자기 `claim` 의 들이기를 잇는다. */
  "resumeImport",
  /** 병합된 `claim` 을 이어받는 들이기를 연다(확인이 낸 이어받을 기준본으로). */
  "inheritImport",
  /** 들일 것이 없어 티켓을 쓰지 않고 올리기로 넘어간다. */
  "handToUpload",
  /** `claim` 을 비우고(`record claim --clear`) 확인을 다시 돌려 다시 묻는다. */
  "clearClaim",
  /** 그 들이기를 기다린다. 지금 일은 멈춘다. */
  "wait",
  /** 멈춘다. */
  "stop",
] as const;

export type Act = (typeof ACTS)[number];

export interface Choice {
  readonly label: string;
  readonly effect: string;
  readonly act: Act;
}

export type Decision =
  | { readonly kind: "ask"; readonly choices: readonly Choice[]; readonly notes: readonly string[] }
  | { readonly kind: "act"; readonly act: Act; readonly notes: readonly string[] };

/** 스킬이 본 PR 상태. 확인 결과가 들이는 중일 때만 있다. */
export type PrState =
  | {
      readonly kind: "open" | "merged" | "closed";
      readonly number: number | null;
      readonly url: string | null;
      readonly mergeCommit: string | null;
    }
  | { readonly kind: "none" }
  | { readonly kind: "failed"; readonly message: string };

export interface DecideInput {
  readonly caller: Caller;
  readonly reading: CheckReading;
  readonly pr: PrState | null;
}

const IMPORT_FIRST = "먼저 들인다";
const KEEP_CODE = "지금 코드 값으로 계속한다";
const OVERWRITE = "웹 편집을 버리고 코드로 덮어쓴다";
const STOP = "멈춘다";
const WAIT = "그 들이기를 기다린다";

function ask(choices: readonly Choice[], notes: readonly string[] = []): Decision {
  return { kind: "ask", choices, notes };
}

function act(what: Act, notes: readonly string[] = []): Decision {
  return { kind: "act", act: what, notes };
}

const STOP_CHOICE: Choice = { label: STOP, effect: "지금 일을 하지 않고 멈춘다", act: "stop" };

/** "찾았을 때"의 "먼저 들인다" 선택지와 덮어쓰기가 할 일. 들이기의 길마다 하나다. */
interface ImportWay {
  readonly importFirst: Choice;
  readonly overwrite: Act;
}

/** 웹 편집을 새로 들인다. */
const FRESH_IMPORT: ImportWay = {
  importFirst: {
    label: IMPORT_FIRST,
    effect: "들이기를 열어 웹 편집을 코드에 들인다",
    act: "import",
  },
  overwrite: "overwrite",
};

/** 병합된 `claim` 을 이어받아 그 뒤에 더 고친 몫을 들인다. */
const INHERITED_IMPORT: ImportWay = {
  importFirst: {
    label: IMPORT_FIRST,
    effect: "병합된 claim 을 이어받는 들이기를 열어 더 고친 몫을 코드에 들인다",
    act: "inheritImport",
  },
  overwrite: "overwriteClaimMerged",
};

/** "찾았을 때"의 선택지. "먼저 들인다"와 덮어쓰기는 들이기의 길(`way`)을 따른다. */
function foundChoices(caller: "screen" | "upload", way: ImportWay): Choice[] {
  if (caller === "screen") {
    return [
      way.importFirst,
      {
        label: KEEP_CODE,
        effect:
          "웹 편집을 들이지 않고 지금 코드 값으로 화면 작업을 잇는다. 웹 편집은 다음 확인이 다시 찾는다",
        act: "continue",
      },
    ];
  }
  return [
    way.importFirst,
    { label: OVERWRITE, effect: "웹 편집을 코드의 판으로 되돌려 올린다", act: way.overwrite },
  ];
}

/** 남의 `claim` 을 지우는 선택지. 지운 뒤에는 확인을 다시 돌려 "찾았을 때"의 선택지로 다시 묻는다. */
function clearChoice(caller: Caller): Choice {
  if (caller === "import") {
    return {
      label: "그 claim을 지우고 이 세션이 다시 들인다",
      effect: "기록의 claim 을 비우고 확인을 다시 돌려 이 세션이 들인다",
      act: "clearClaim",
    };
  }
  const next = caller === "screen" ? KEEP_CODE : OVERWRITE;
  return {
    label: "그 claim을 지운다",
    effect: `기록의 claim 을 비우고 확인을 다시 돌려 "${IMPORT_FIRST}"와 "${next}" 가운데 다시 묻는다`,
    act: "clearClaim",
  };
}

type Importing = Extract<CheckReading, { result: "importing" }>;

function claimNote(reading: Importing): string {
  const { branch, ticket, at } = reading.claim;
  return `${branch} 가 들이는 중이다(티켓 ${ticket}, ${at})`;
}

function prNote(pr: Extract<PrState, { number: number | null }>): string {
  const name = pr.number === null ? "PR" : `PR #${String(pr.number)}`;
  return pr.url === null ? name : `${name} ${pr.url}`;
}

function furtherNote(reading: Importing): string[] {
  const { further } = reading;
  if (isEmpty(further)) {
    return [];
  }
  const parts = [
    ...(further.tokens > 0 ? [`토큰 ${String(further.tokens)}곳`] : []),
    ...[...further.revert, ...further.webRemoved, ...further.webAdded].filter(
      (path) => path !== TOKENS_PATH || further.tokens === 0,
    ),
    ...further.index.map((key) => `색인 ${key}`),
  ];
  return [`claim 뒤에 더 고친 몫: ${parts.join(", ")}`];
}

/** PR 이 열린 남의 `claim`. */
function otherOpen(caller: Caller, reading: Importing, notes: readonly string[]): Decision {
  switch (caller) {
    case "screen":
      return ask(
        [
          {
            label: "그 들이기의 병합을 기다린다",
            effect: "그 PR 이 병합될 때까지 화면 작업을 멈춘다",
            act: "wait",
          },
          {
            label: KEEP_CODE,
            effect: "들이는 값 없이 지금 코드 값으로 화면 작업을 잇는다",
            act: "continue",
          },
        ],
        notes,
      );
    case "upload":
      return ask(
        [
          {
            label: "그 병합 뒤에 올린다",
            effect: "그 PR 이 병합될 때까지 올리기를 멈춘다",
            act: "wait",
          },
          {
            label: OVERWRITE,
            effect:
              "웹 편집을 코드의 판으로 되돌려 올린다. claim 은 남아, 그 PR 이 병합되면 들인 값이 그 뒤의 올리기로 다시 올라간다",
            act: "overwrite",
          },
        ],
        notes,
      );
    case "import":
      return act("stop", [
        ...notes,
        "티켓을 쓰지 않고 멈춘다",
        ...(isEmpty(reading.further) ? [] : ["더 고친 몫은 그 병합 뒤에 다시 부른다"]),
      ]);
  }
}

/** 병합된 `claim`. 더 고친 몫이 없으면 묻지 않는다. */
function merged(caller: Caller, reading: Importing, notes: readonly string[]): Decision {
  const further = !isEmpty(reading.further);
  switch (caller) {
    case "screen": {
      const base = [...notes, "지금 브랜치가 그 병합 커밋을 품지 않았으면 main 을 합친 뒤 잇는다"];
      return further ? ask(foundChoices("screen", INHERITED_IMPORT), base) : act("continue", base);
    }
    case "upload": {
      const base = [
        ...notes,
        "그 병합 커밋이 지금 HEAD 의 조상이 아니면 origin/main 을 다시 받아 처음부터 한다",
      ];
      return further
        ? ask(foundChoices("upload", INHERITED_IMPORT), base)
        : act("uploadClaimMerged", base);
    }
    case "import":
      if (!further) {
        return act("handToUpload", [...notes, "들일 것이 없어 티켓을 쓰지 않고 올리기로 넘어간다"]);
      }
      if (reading.claim.own) {
        return act("stop", [
          ...notes,
          "병합된 자기 브랜치에서는 이어받지 않는다. 새 티켓 브랜치에서 확인부터 다시 한다",
        ]);
      }
      return reading.inherit === null
        ? act("stop", [
            ...notes,
            "이어받을 기준본이 없다. check judge 를 --inherit-out 과 함께 다시 돌린다",
          ])
        : act("inheritImport", [...notes, `이어받을 기준본: ${reading.inherit}`]);
  }
}

/** PR 이 없거나 닫힌 `claim`. 자기 것이면 기다릴 들이기가 자신이라 "멈춘다"를 보인다. */
function abandoned(caller: Caller, reading: Importing, notes: readonly string[]): Decision {
  const hold: Choice = reading.claim.own
    ? STOP_CHOICE
    : { label: WAIT, effect: "그 브랜치의 들이기가 PR 을 열 때까지 지금 일을 멈춘다", act: "wait" };
  return ask([hold, clearChoice(caller)], notes);
}

function importing(caller: Caller, reading: Importing, pr: PrState | null): Decision {
  if (pr === null) {
    throw new CommandError(
      "usage",
      "확인이 들이는 중이라 claim 의 브랜치의 PR 상태(--pr 이나 --pr-error)가 있어야 한다",
    );
  }
  const notes = [claimNote(reading), ...furtherNote(reading)];
  switch (pr.kind) {
    case "failed":
      return act("stop", [...notes, `PR 상태를 보지 못했다: ${pr.message}`]);
    case "merged": {
      const commit = pr.mergeCommit === null ? "" : `(병합 커밋 ${pr.mergeCommit})`;
      return merged(caller, reading, [...notes, `${prNote(pr)} 가 병합됐다${commit}`]);
    }
    case "open":
      return reading.claim.own
        ? act("resumeImport", [...notes, `${prNote(pr)} 가 열려 있다`])
        : otherOpen(caller, reading, [...notes, `${prNote(pr)} 가 열려 있다`]);
    case "closed":
      return abandoned(caller, reading, [...notes, `${prNote(pr)} 가 병합되지 않고 닫혔다`]);
    case "none":
      return reading.claim.own
        ? act("resumeImport", notes)
        : abandoned(caller, reading, [...notes, "그 브랜치에 PR 이 없다"]);
  }
}

function undecidable(
  caller: Caller,
  reading: Extract<CheckReading, { result: "undecidable" }>,
): Decision {
  const notes = [`확인이 판단할 수 없다(${reading.reason}): ${reading.message}`];
  const fromRecord = RECORD_REASONS.some((reason) => reason === reading.reason);
  const unchecked: Choice = {
    label: "확인 없이 계속한다",
    effect:
      "확인 없이 화면 작업을 잇는다. 올리기의 확인이 다시 돌아 웹 편집이 말없이 덮이지 않는다",
    act: "continue",
  };
  switch (caller) {
    case "screen":
      return ask([unchecked, STOP_CHOICE], notes);
    case "upload":
      return fromRecord
        ? ask(
            [
              {
                label: "코드로 덮어쓰고 기록을 새로 쓴다",
                effect: "아티팩트의 sha256 과 맞대 보낼 것을 고르고 기록을 새로 쓴다",
                act: "rewriteRecord",
              },
              STOP_CHOICE,
            ],
            notes,
          )
        : act("stop", [...notes, "아티팩트를 읽지 못해 올리지 않는다"]);
    case "import":
      return act("stop", [...notes, "판단할 수 없어 들이지 않는다"]);
  }
}

/** 웹 편집 없음과 기록 전. */
function nothingFound(caller: Caller): Decision {
  switch (caller) {
    case "screen":
      return act("continue");
    case "upload":
      return act("upload");
    case "import":
      return act("stop", ["들일 웹 편집이 없다"]);
  }
}

/** 부르는 쪽, 확인 결과, PR 상태로 선택지나 할 일을 낸다. */
export function decide(input: DecideInput): Decision {
  const { caller, reading, pr } = input;
  if (pr !== null && reading.result !== "importing") {
    throw new CommandError("usage", "PR 상태는 확인 결과가 들이는 중일 때만 준다");
  }
  switch (reading.result) {
    case "clean":
    case "beforeRecord":
      return nothingFound(caller);
    case "edited":
      return caller === "import" ? act("import") : ask(foundChoices(caller, FRESH_IMPORT));
    case "importing":
      return importing(caller, reading, pr);
    case "undecidable":
      return undecidable(caller, reading);
  }
}

function prField(item: Readonly<Record<string, unknown>>): {
  number: number | null;
  url: string | null;
  mergeCommit: string | null;
} {
  const commit = isRecord(item.mergeCommit) ? item.mergeCommit.oid : undefined;
  return {
    number: typeof item.number === "number" ? item.number : null,
    url: typeof item.url === "string" ? item.url : null,
    mergeCommit: typeof commit === "string" ? commit : null,
  };
}

/** `gh pr list --json number,state,url,mergeCommit` 의 배열에서 PR 상태를 고른다. 열림, 병합, 닫힘 차례로 앞선다. */
export function prStateOf(path: string, raw: unknown): PrState {
  const items = unknownList(raw);
  if (items === undefined || !items.every(isRecord)) {
    throw inputError(path, "gh pr list 의 JSON 배열이 아니다");
  }
  const states = [
    ["OPEN", "open"],
    ["MERGED", "merged"],
    ["CLOSED", "closed"],
  ] as const;
  if (!items.every((item) => states.some(([state]) => state === item.state))) {
    throw inputError(path, "PR 의 state 가 OPEN, MERGED, CLOSED 가운데 하나가 아니다");
  }
  for (const [state, kind] of states) {
    const found = items.find((item) => item.state === state);
    if (found !== undefined) {
      return { kind, ...prField(found) };
    }
  }
  return { kind: "none" };
}

/** `--pr` 이나 `--pr-error` 로 준 PR 상태. 둘 다 없으면 null. */
function prStateFrom(pr: string | undefined, prError: string | undefined): PrState | null {
  if (pr !== undefined && prError !== undefined) {
    throw new CommandError("usage", "decide 에는 --pr 과 --pr-error 가운데 하나만 준다");
  }
  if (pr !== undefined) {
    return prStateOf(pr, readJson(pr));
  }
  return prError === undefined ? null : { kind: "failed", message: prError };
}

function decisionJson(decision: Decision): ReportFields {
  return decision.kind === "ask"
    ? {
        kind: "ask",
        choices: decision.choices.map((choice) => ({ ...choice })),
        notes: [...decision.notes],
      }
    : { kind: "act", act: decision.act, notes: [...decision.notes] };
}

/** 결정표 명령. */
export function runDecide(args: readonly string[]): ReportFields {
  const { values, positionals } = parsedArgs(() =>
    parseArgs({
      args: [...args],
      options: {
        caller: { type: "string" },
        check: { type: "string" },
        pr: { type: "string" },
        "pr-error": { type: "string" },
      },
      strict: true,
      allowPositionals: true,
    }),
  );
  if (positionals.length > 0) {
    throw new CommandError("usage", "decide 는 하위 명령을 받지 않는다");
  }
  const caller = CALLERS.find((name) => name === values.caller);
  if (caller === undefined) {
    throw new CommandError("usage", "decide 에는 --caller <screen|upload|import> 가 있어야 한다");
  }
  if (values.check === undefined) {
    throw new CommandError("usage", "decide 에는 --check <확인 보고> 가 있어야 한다");
  }
  const pr = prStateFrom(values.pr, values["pr-error"]);
  return decisionJson(decide({ caller, reading: readCheckReport(values.check), pr }));
}
