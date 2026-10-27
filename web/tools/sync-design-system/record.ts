/**
 * 기록 명령. 올리기의 계획(보낼 파일과 지울 경로, `upload.ts`)과 빌드가 필요한지를 내고, 올린 뒤의 기록
 * (`sync-record.ts`)을 쓰며, 들이기의 `claim` 을 쓰거나 비운다(`claim.ts`)(design-reverse-sync 명세 "기록", "올리기",
 * "찾았을 때"의 "덮어쓴다", "겹침").
 *
 * 하위 명령은 다섯이다. 산출 폴더는 아티팩트의 `project/` 아래에 놓일 내용(빌드의 `ds-bundle/` 에서
 * `.design-sync/upload-output.mjs` 가 올릴 항목만 옮긴 폴더 등)이다. 확인 보고는 `check judge` 의 보고 JSON 이고
 * `check-report.ts` 로 읽는다.
 *
 * - `record plan --local <산출 폴더> (--record <기록> | --artifact-sha256 <sha256 표>) [--check <확인 보고>]
 *   [--overwrite | --claim-merged [--overwrite]] [--previous-output <지난 산출 목록>]`. 이번 올리기가 보낼 파일(`send`),
 *   목표대로 이미 보낸 파일(`landed`), 그대로인 파일(`unchanged`), 지울 경로(`delete`), 이미 지워진 경로(`gone`),
 *   다루지 않는 경로(`ignored`)와, 확인 보고에서 고른 되돌릴 파일(`revert`, 웹이 고친 것), 웹에서 지운 경로
 *   (`webRemoved`), 웹에서 더한 경로(`webAdded`), 마지막 기록이 `claim` 을 비우는지(`clearClaim`)를 낸다. 기록은
 *   아티팩트에서 받은 기록 파일이고, 없거나 읽히지 않으면(편집이 꺼진 동안) 대신 아티팩트의 파일마다의 sha256 을 JSON
 *   객체 `{경로: sha256}` 로 준다. 앞 기록에 `pending` 이 있으면 확인 보고가 있어야 한다(`upload.ts`). 지난 산출 목록은
 *   빌드 산출 전체를 맞춘 올리기만 주는 JSON 경로 배열이다. 확인 결과마다 계획을 내는 때는 아래와 같다.
 *   - 웹 편집 없음·기록 전: 그대로 낸다.
 *   - 웹 편집 있음: 사람이 "덮어쓴다"를 고른 `--overwrite` 가 있을 때만 낸다. 확인이 찾은 고친 파일과, 토큰 편집이
 *     있으면 `tokens.json` 을 되돌리고, 지운 파일을 되살리고, 웹에서 더한 파일을 지운다.
 *   - 들이는 중: `claim` 이 든 파일(코드가 그대로여도)과 더 고친 몫을 위와 같이 되돌린다. 결정표가 병합된 `claim` 의
 *     올리기를 고른 `--claim-merged` 면 마지막 기록이 `claim` 을 비운다. 더 고친 몫이 있거나 병합되지 않은 `claim`
 *     이면 사람이 "덮어쓴다"를 고른 `--overwrite` 도 있어야 한다. 그때 병합되지 않은 `claim` 은 비우지 않는다.
 *   - 판단할 수 없음: 내지 않는다.
 * - `record needs-build --changed <바뀐 경로> [--check <확인 보고> (--overwrite | --claim-merged [--overwrite])]`. 바뀐
 *   경로는 기록의 커밋 뒤에 바뀐 저장소 경로의 줄 목록(`git -c core.quotePath=false diff --name-only` 의 출력)이다.
 *   빌드가 필요한지(`needed`)와 그 까닭(`because`)을 낸다. 확인 보고와 두 선택은 `record plan` 과 같게 준다.
 * - `record write --local <산출 폴더> --plan <계획 보고> --index <색인> --out <기록> [--record <앞 기록>]
 *   [--artifact <받은 폴더>] (--first-call | --commit <SHA> --at <시각>)`. 계획 보고는 `record plan` 의 보고 JSON,
 *   색인은 이번 올리기가 보내는 색인이다. 받은 폴더는 첫 올리기가 아티팩트에서 읽은, 빌드 산출에 없는 파일을 아티팩트
 *   경로 그대로(`project/…`) 둔 폴더다. 여러 호출로 나뉜 올리기의 첫 호출은 `--first-call` 로 `pending` 이 든 기록을,
 *   마지막 호출(한 호출로 끝나는 올리기 포함)은 올린 main 커밋과 시각으로 `pending` 없는 기록을 쓴다. 계획의
 *   `clearClaim` 이면 마지막 기록이 `claim` 을 비운다. 보고는 쓴 파일의 절대 경로(`out`), 기록의 파일 수(`files`),
 *   바이트 수(`bytes`), `pending` 이 들었는지(`pending`), `claim` 이 들었는지(`claim`)다.
 * - `record claim --record <다시 받은 기록> --expect <확인에 쓴 기록> --out <기록> (--clear | --check <확인 보고>
 *   --web <받은 폴더> --branch <브랜치> --ticket <티켓 경로> --at <시각> [--inherit <이어받을 기준본>])`. 들이기가
 *   `claim` 을 쓰거나(`claim.ts` 의 셋) 사람이 지우기로 고른 `claim` 을 비운 기록을 쓴다. 다시 받은 기록의 `claim` 이
 *   확인에 쓴 기록의 것과 다르면 `input` 오류다. 받은 폴더와 확인 보고는 같은 `check judge` 의 것이다. 보고는
 *   `record write` 와 같다.
 * - `record base --record <기록> --out <기준본>`. 들이기 명령(`import --base`)에 넘길 기준본을 쓴다. `claim` 이
 *   이어받은 기준본을 들면 그것이고, 아니면 기록의 기준본이다(명세 "겹침"의 "병합됐으면" 주석). `claim` 의 사본은
 *   기준본이 아니다. 둘 다 없으면 `input` 오류다. 보고는 쓴 파일의 절대 경로(`out`)와 어디서 골랐는지(`from`,
 *   `claim` 이나 `record`)다. 스킬이 기록의 JSON 에서 칸을 손으로 고르지 않게 07 이 더했다.
 *
 * 못 보는 것: 확인 보고와 계획 보고가 이번 산출과 같은 때의 것인지는 보지 않는다. 스킬이 한 올리기 안에서 이어 준다.
 * `--claim-merged` 가 실제로 병합된 `claim` 인지는 보지 않는다. 결정표가 스킬이 받은 PR 상태로 고른다. 덮어쓰기가
 * 되돌리는 색인 목록은 이 명령이 다루지 않는다. 스킬이 보내는 색인에 기록의 목록을 다시 적는다. 웹이 더한
 * 그림·글꼴은 확인 보고의 `index` 에만 나와(`check.ts` 의 못 보는 것) 덮어쓰기가 그 파일을 지우지 않는다.
 */

import { parseArgs } from "node:util";
import { isEmpty, readCheckReport, type WebEdits } from "./check-report.ts";
import { claimedRecord, type ClaimChange } from "./claim.ts";
import { CommandError, parsedArgs, readInput, writeOutput, type ReportFields } from "./command.ts";
import {
  inputError,
  isArtifactPath,
  isRecord,
  jsonValue,
  readFolder,
  readJson,
  readPathList,
  sortedPaths,
  stringList,
} from "./io.ts";
import {
  indexLists,
  nextRecord,
  readRecord,
  serializeRecord,
  type PendingState,
  type RecordChanges,
  type SyncRecord,
} from "./sync-record.ts";
import { needsBuild, planUpload } from "./upload.ts";

/** 아티팩트에서 받은 기록. 꼴 판 1 로 읽히지 않으면 `input` 오류다. */
function recordFrom(path: string): SyncRecord {
  const read = readRecord(readInput(path));
  if (read.kind !== "ok") {
    const why = read.kind === "malformed" ? read.message : read.kind;
    throw inputError(
      path,
      `읽히는 기록이 아니다(${why}). 기록이 없거나 읽히지 않으면 --artifact-sha256 으로 맞댄다`,
    );
  }
  return read.record;
}

const SHA256 = /^[0-9a-f]{64}$/;

function readSha256Table(path: string): Map<string, string> {
  const raw = readJson(path);
  if (!isRecord(raw)) {
    throw inputError(path, "경로마다 sha256 을 든 JSON 객체가 아니다");
  }
  const table = new Map<string, string>();
  for (const [artifactPath, hash] of Object.entries(raw)) {
    if (!isArtifactPath(artifactPath) || typeof hash !== "string" || !SHA256.test(hash)) {
      throw inputError(
        path,
        `${JSON.stringify(artifactPath)} 의 project/ 아래 경로와 sha256(16 진수 64 자)을 들지 않는다`,
      );
    }
    table.set(artifactPath, hash);
  }
  return table;
}

/** 확인 보고에서 이번 올리기에 넘길 것. */
interface CheckDecision {
  readonly pending: PendingState | null;
  readonly revert: readonly string[];
  readonly webRemoved: readonly string[];
  readonly webAdded: readonly string[];
  readonly clearClaim: boolean;
}

const NO_DECISION: CheckDecision = {
  pending: null,
  revert: [],
  webRemoved: [],
  webAdded: [],
  clearClaim: false,
};

function merged(left: WebEdits, right: WebEdits): Omit<CheckDecision, "pending" | "clearClaim"> {
  return {
    revert: sortedPaths([...left.revert, ...right.revert]),
    webRemoved: sortedPaths([...left.webRemoved, ...right.webRemoved]),
    webAdded: sortedPaths([...left.webAdded, ...right.webAdded]),
  };
}

/**
 * `--check`, `--overwrite`, `--claim-merged` 로 이번 올리기에 넘길 것을 고른다. 웹 편집 있음은 덮어쓰기를 고른 때만,
 * 들이는 중은 병합된 `claim` 이고 더 고친 몫이 없거나 덮어쓰기를 고른 때만 넘긴다.
 */
function decisionOf(values: Values): CheckDecision {
  const overwrite = values.overwrite === true;
  const claimMerged = values["claim-merged"] === true;
  if (values.check === undefined) {
    if (overwrite || claimMerged) {
      throw new CommandError(
        "usage",
        `${overwrite ? "--overwrite" : "--claim-merged"} 에는 되돌릴 것을 고를 --check <확인 보고> 가 있어야 한다`,
      );
    }
    return NO_DECISION;
  }
  const reading = readCheckReport(values.check);
  if (claimMerged && reading.result !== "importing") {
    throw new CommandError("usage", "--claim-merged 는 들이는 중의 확인 보고에만 준다");
  }
  switch (reading.result) {
    case "clean":
    case "beforeRecord":
      return { ...NO_DECISION, pending: reading.pending };
    case "edited":
      if (!overwrite) {
        throw new CommandError(
          "usage",
          "확인이 웹 편집을 찾았다. 사람이 덮어쓰기를 고른 때만 --overwrite 로 올린다",
        );
      }
      return { ...NO_DECISION, pending: reading.pending, ...merged(reading.edits, reading.edits) };
    case "importing": {
      if (!overwrite && (!claimMerged || !isEmpty(reading.further))) {
        throw new CommandError(
          "usage",
          "확인이 들이는 중이다. 병합된 claim 에 더 고친 몫이 없으면 --claim-merged 로, 아니면 사람이 덮어쓰기를 고른 때만 --overwrite 를 더해 올린다",
        );
      }
      const { claim } = reading;
      const claimed: WebEdits = {
        revert: claim.changed,
        webRemoved: claim.removed,
        webAdded: claim.added,
        tokens: 0,
        index: [],
      };
      return {
        pending: reading.pending,
        ...merged(claimed, reading.further),
        clearClaim: claimMerged,
      };
    }
    case "undecidable":
      throw new CommandError(
        "usage",
        `확인 결과가 판단할 수 없음(${reading.reason})이라 올리지 않는다. 웹 편집 없음, 기록 전, 덮어쓰기를 고른 웹 편집 있음, 들이는 중만 올린다`,
      );
  }
}

const OPTIONS = {
  local: { type: "string" },
  record: { type: "string" },
  "artifact-sha256": { type: "string" },
  check: { type: "string" },
  overwrite: { type: "boolean" },
  "claim-merged": { type: "boolean" },
  "previous-output": { type: "string" },
  changed: { type: "string" },
  plan: { type: "string" },
  index: { type: "string" },
  out: { type: "string" },
  artifact: { type: "string" },
  "first-call": { type: "boolean" },
  commit: { type: "string" },
  at: { type: "string" },
  expect: { type: "string" },
  clear: { type: "boolean" },
  web: { type: "string" },
  branch: { type: "string" },
  ticket: { type: "string" },
  inherit: { type: "string" },
} as const;

type Values = ReturnType<typeof parseValues>["values"];

function parseValues(args: readonly string[]) {
  return parsedArgs(() =>
    parseArgs({ args: [...args], options: OPTIONS, strict: true, allowPositionals: true }),
  );
}

/** 하위 명령이 받지 않는 인자가 있으면 `usage` 오류다. */
function onlyOptions(
  action: string,
  values: Values,
  allowed: readonly (keyof typeof OPTIONS)[],
): void {
  const extra = Object.keys(values).filter((key) => !allowed.some((name) => name === key));
  if (extra.length > 0) {
    throw new CommandError(
      "usage",
      `record ${action} 는 ${extra.map((key) => `--${key}`).join(", ")} 를 받지 않는다`,
    );
  }
}

function required(action: string, name: string, value: string | undefined): string {
  if (value === undefined) {
    throw new CommandError("usage", `record ${action} 에는 --${name} 가 있어야 한다`);
  }
  return value;
}

function plan(values: Values): ReportFields {
  onlyOptions("plan", values, [
    "local",
    "record",
    "artifact-sha256",
    "check",
    "overwrite",
    "claim-merged",
    "previous-output",
  ]);
  const local = required("plan", "local <산출 폴더>", values.local);
  if ((values.record === undefined) === (values["artifact-sha256"] === undefined)) {
    throw new CommandError(
      "usage",
      "record plan 에는 --record <기록> 와 --artifact-sha256 <sha256 표> 가운데 하나를 준다",
    );
  }
  const decision = decisionOf(values);
  const previousOutput = values["previous-output"];
  const result = planUpload({
    record: values.record === undefined ? null : recordFrom(values.record),
    artifactSha256:
      values["artifact-sha256"] === undefined ? null : readSha256Table(values["artifact-sha256"]),
    output: readFolder(local, "project/"),
    previousOutput: previousOutput === undefined ? null : readPathList(previousOutput),
    revert: decision.revert,
    webRemoved: decision.webRemoved,
    webAdded: decision.webAdded,
    pendingState: decision.pending,
  });
  return {
    action: "plan",
    ...result,
    revert: sortedPaths(decision.revert),
    webRemoved: sortedPaths(decision.webRemoved),
    webAdded: sortedPaths(decision.webAdded),
    clearClaim: decision.clearClaim,
  };
}

function changedPaths(path: string): string[] {
  const lines = readInput(path)
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line !== "");
  const quoted = lines.find((line) => line.startsWith('"'));
  if (quoted !== undefined) {
    throw inputError(
      path,
      `따옴표로 싼 줄 ${quoted} 을 든다. git -c core.quotePath=false diff --name-only 로 짓는다`,
    );
  }
  return lines;
}

function buildNeed(values: Values): ReportFields {
  onlyOptions("needs-build", values, ["changed", "check", "overwrite", "claim-merged"]);
  const changed = changedPaths(required("needs-build", "changed <바뀐 경로>", values.changed));
  const decision = decisionOf(values);
  const need = needsBuild(changed, [...decision.revert, ...decision.webRemoved]);
  return { action: "needs-build", needed: need.needed, because: need.because };
}

/** `record plan` 의 보고에서 기록에 합칠 것과 `claim` 을 비우는지를 읽는다. */
function readPlan(path: string): RecordChanges & { readonly clearClaim: boolean } {
  const raw = readJson(path);
  if (!isRecord(raw) || raw.command !== "record" || raw.ok !== true || raw.action !== "plan") {
    throw inputError(path, "record plan 의 성공 보고가 아니다");
  }
  const list = (key: string): string[] => {
    const paths = stringList(raw[key]);
    if (paths === undefined || !paths.every(isArtifactPath)) {
      throw inputError(path, `${key} 로 project/ 아래 경로의 배열을 들지 않는다`);
    }
    return paths;
  };
  if (typeof raw.clearClaim !== "boolean") {
    throw inputError(path, "clearClaim 으로 참거짓을 들지 않는다");
  }
  return {
    send: list("send"),
    landed: list("landed"),
    unchanged: list("unchanged"),
    delete: list("delete"),
    gone: list("gone"),
    clearClaim: raw.clearClaim,
  };
}

const COMMIT = /^[0-9a-f]{7,40}$/;

function checkedAt(at: string): string {
  if (Number.isNaN(Date.parse(at))) {
    throw new CommandError("usage", `--at ${at} 이 시각이 아니다`);
  }
  return at;
}

/** 기록을 쓰고 보고의 칸을 낸다. 한도를 넘으면 `limit` 오류다. */
function written(action: string, out: string, next: SyncRecord): ReportFields {
  const text = serializeRecord(next);
  return {
    action,
    out: writeOutput(out, text),
    files: next.files.size,
    bytes: new TextEncoder().encode(text).byteLength,
    pending: next.pending !== null,
    claim: next.claim !== null,
  };
}

function write(values: Values): ReportFields {
  onlyOptions("write", values, [
    "local",
    "plan",
    "index",
    "out",
    "record",
    "artifact",
    "first-call",
    "commit",
    "at",
  ]);
  const local = required("write", "local <산출 폴더>", values.local);
  const planPath = required("write", "plan <계획 보고>", values.plan);
  const indexPath = required("write", "index <색인>", values.index);
  const out = required("write", "out <기록>", values.out);
  const firstCall = values["first-call"] === true;
  const { commit, at } = values;
  if (
    firstCall ? commit !== undefined || at !== undefined : commit === undefined || at === undefined
  ) {
    throw new CommandError(
      "usage",
      "record write 에는 --first-call 이나 --commit <SHA> 와 --at <시각> 가운데 하나를 준다",
    );
  }
  if (commit !== undefined && !COMMIT.test(commit)) {
    throw new CommandError("usage", `--commit ${commit} 이 16 진수 커밋 SHA 가 아니다`);
  }
  if (at !== undefined) {
    checkedAt(at);
  }
  const index = readJson(indexPath);
  if (!isRecord(index)) {
    throw inputError(indexPath, "JSON 객체가 아니다");
  }
  const artifact =
    values.artifact === undefined ? new Map<string, Uint8Array>() : readFolder(values.artifact, "");
  const { clearClaim, ...changes } = readPlan(planPath);
  const next = nextRecord({
    previous: values.record === undefined ? null : recordFrom(values.record),
    output: readFolder(local, "project/"),
    artifact: new Map([...artifact].filter(([path]) => isArtifactPath(path))),
    changes,
    index: indexLists(index),
    call:
      commit === undefined || at === undefined ? { kind: "first" } : { kind: "last", commit, at },
    clearClaim,
  });
  return written("write", out, next);
}

function claimChange(values: Values): ClaimChange {
  if (values.clear === true) {
    const extra = (["check", "web", "branch", "ticket", "at", "inherit"] as const).filter(
      (key) => values[key] !== undefined,
    );
    if (extra.length > 0) {
      throw new CommandError(
        "usage",
        `record claim --clear 는 ${extra.map((key) => `--${key}`).join(", ")} 를 받지 않는다`,
      );
    }
    return { kind: "clear" };
  }
  const inherit = values.inherit;
  const inherited = inherit === undefined ? null : jsonValue(readJson(inherit));
  if (inherited === undefined) {
    throw inputError(inherit ?? "", "JSON 값이 아니다");
  }
  return {
    kind: "write",
    head: {
      branch: required("claim", "branch <브랜치>", values.branch),
      ticket: required("claim", "ticket <티켓 경로>", values.ticket),
      at: checkedAt(required("claim", "at <시각>", values.at)),
    },
    reading: readCheckReport(required("claim", "check <확인 보고>", values.check)),
    web: readFolder(required("claim", "web <받은 폴더>", values.web), ""),
    inherit: inherited,
  };
}

function claim(values: Values): ReportFields {
  onlyOptions("claim", values, [
    "record",
    "expect",
    "out",
    "clear",
    "check",
    "web",
    "branch",
    "ticket",
    "at",
    "inherit",
  ]);
  const current = recordFrom(required("claim", "record <다시 받은 기록>", values.record));
  const expected = recordFrom(required("claim", "expect <확인에 쓴 기록>", values.expect));
  const out = required("claim", "out <기록>", values.out);
  const next = claimedRecord({ current, expected: expected.claim, change: claimChange(values) });
  return written("claim", out, next);
}

/** 들이기 명령에 넘길 기준본. `claim` 이 이어받은 기준본이 있으면 그것, 없으면 기록의 기준본이다. */
function base(values: Values): ReportFields {
  onlyOptions("base", values, ["record", "out"]);
  const path = required("base", "record <기록>", values.record);
  const out = required("base", "out <기준본>", values.out);
  const record = recordFrom(path);
  const inherited = record.claim?.base ?? null;
  const chosen = inherited ?? record.baseline;
  if (chosen === null) {
    throw inputError(path, "기준본을 들지 않는다. 들이기는 첫 올리기 뒤에만 한다");
  }
  return {
    action: "base",
    out: writeOutput(out, `${JSON.stringify(chosen, null, 2)}\n`),
    from: inherited === null ? "record" : "claim",
  };
}

/** 기록 명령. */
export function runRecord(args: readonly string[]): ReportFields {
  const { values, positionals } = parseValues(args);
  const [action, ...rest] = positionals;
  if (rest.length > 0) {
    throw new CommandError("usage", "record 는 하위 명령 하나를 받는다");
  }
  switch (action) {
    case "plan":
      return plan(values);
    case "needs-build":
      return buildNeed(values);
    case "write":
      return write(values);
    case "claim":
      return claim(values);
    case "base":
      return base(values);
    default:
      throw new CommandError(
        "usage",
        "record 는 plan, needs-build, write, claim, base 가운데 하나를 받는다",
      );
  }
}
