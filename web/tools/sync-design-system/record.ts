/**
 * 기록 명령. 올리기의 계획(보낼 파일과 지울 경로, `upload.ts`)과 빌드가 필요한지를 내고, 올린 뒤의 기록
 * (`sync-record.ts`)을 쓴다(design-reverse-sync 명세 "기록", "올리기", "찾았을 때"의 "덮어쓴다").
 *
 * 하위 명령은 셋이다. 산출 폴더는 아티팩트의 `project/` 아래에 놓일 내용(빌드의 `ds-bundle/` 등)이다.
 *
 * - `record plan --local <산출 폴더> (--record <기록> | --artifact-sha256 <sha256 표>) [--check <확인 보고>]
 *   [--overwrite] [--previous-output <지난 산출 목록>]`. 이번 올리기가 보낼 파일(`send`), 목표대로 이미 보낸
 *   파일(`landed`), 그대로인 파일(`unchanged`), 지울 경로(`delete`), 이미 지워진 경로(`gone`), 다루지 않는 경로
 *   (`ignored`)와, 확인 보고에서 고른 되돌릴 파일(`revert`, 웹이 고친 것), 웹에서 지운 경로(`webRemoved`), 웹에서 더한
 *   경로(`webAdded`)를 낸다. 기록은 아티팩트에서 받은 기록 파일이고, 없거나 읽히지 않으면(편집이 꺼진 동안) 대신
 *   아티팩트의 파일마다의 sha256 을 JSON 객체 `{경로: sha256}` 로 준다. 확인 보고는 `check judge` 의 보고 JSON 이고,
 *   결과가 웹 편집 없음·기록 전이거나 웹 편집 있음에 `--overwrite`(사람이 "덮어쓴다"를 고른 것)를 준 때만 계획을 낸다.
 *   앞 기록에 `pending` 이 있으면 확인 보고가 있어야 한다(`upload.ts`). 덮어쓰기는 확인이 찾은 고친 파일과, 토큰 편집이
 *   있으면 `tokens.json` 을 되돌리고, 지운 파일을 되살리고, 웹에서 더한 파일을 지운다(이번 산출에 없는 경로는
 *   `upload.ts`). 지난 산출 목록은 빌드 산출 전체를 맞춘 올리기만 주는 JSON 경로 배열이다.
 * - `record needs-build --changed <바뀐 경로> [--check <확인 보고> --overwrite]`. 바뀐 경로는 기록의 커밋 뒤에 바뀐
 *   저장소 경로의 줄 목록(`git -c core.quotePath=false diff --name-only` 의 출력)이다. 빌드가 필요한지(`needed`)와 그
 *   까닭(`because`)을 낸다.
 * - `record write --local <산출 폴더> --plan <계획 보고> --index <색인> --out <기록> [--record <앞 기록>]
 *   [--artifact <받은 폴더>] (--first-call | --commit <SHA> --at <시각>)`. 계획 보고는 `record plan` 의 보고 JSON,
 *   색인은 이번 올리기가 보내는 색인이다. 받은 폴더는 첫 올리기가 아티팩트에서 읽은, 빌드 산출에 없는 파일을 아티팩트
 *   경로 그대로(`project/…`) 둔 폴더다. 여러 호출로 나뉜 올리기의 첫 호출은 `--first-call` 로 `pending` 이 든 기록을,
 *   마지막 호출(한 호출로 끝나는 올리기 포함)은 올린 main 커밋과 시각으로 `pending` 없는 기록을 쓴다. 보고는 쓴 파일의
 *   절대 경로(`out`), 기록의 파일 수(`files`), 바이트 수(`bytes`), `pending` 이 들었는지(`pending`)다.
 *
 * 못 보는 것: 확인 보고와 계획 보고가 이번 산출과 같은 때의 것인지는 보지 않는다. 스킬이 한 올리기 안에서 이어 준다.
 * 덮어쓰기가 되돌리는 색인 목록은 이 명령이 다루지 않는다. 스킬이 보내는 색인에 기록의 목록을 다시 적는다. 웹이 더한
 * 그림·글꼴은 확인 보고의 `index` 에만 나와(`check.ts` 의 못 보는 것) 덮어쓰기가 그 파일을 지우지 않는다.
 */

import { parseArgs } from "node:util";
import { CommandError, parsedArgs, readInput, writeOutput, type ReportFields } from "./command.ts";
import { TOKENS_PATH } from "./file-hash.ts";
import {
  inputError,
  isArtifactPath,
  isRecord,
  readFolder,
  readJson,
  readPathList,
  sortedPaths,
  stringList,
  unknownList,
} from "./io.ts";
import {
  indexLists,
  nextRecord,
  readRecord,
  serializeRecord,
  type RecordChanges,
  type SyncRecord,
} from "./sync-record.ts";
import { needsBuild, planUpload, type PendingClass, type PendingState } from "./upload.ts";

const PENDING_CLASSES: readonly PendingClass[] = [
  "sent",
  "unsent",
  "edited",
  "deleted",
  "remaining",
];

function isPendingClass(value: unknown): value is PendingClass {
  return PENDING_CLASSES.some((known) => known === value);
}

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

/** 확인 보고의 웹 편집. 고친 것은 되돌리고, 지운 것은 되살리고, 더한 것은 지운다. */
interface WebEdits {
  readonly revert: readonly string[];
  readonly webRemoved: readonly string[];
  readonly webAdded: readonly string[];
}

/** 확인 보고에서 이번 올리기에 넘길 것. */
interface CheckDecision extends WebEdits {
  readonly pending: PendingState | null;
}

const NO_DECISION: CheckDecision = { pending: null, revert: [], webRemoved: [], webAdded: [] };

/** 확인 보고에서 읽은 것. 웹 편집 있음이면 그 편집도 읽는다. */
type CheckReading =
  | { readonly result: "clean" | "beforeRecord"; readonly pending: PendingState | null }
  | { readonly result: "edited"; readonly pending: PendingState | null; readonly edits: WebEdits };

function pendingOf(path: string, value: unknown): PendingState | null {
  if (value === null) {
    return null;
  }
  if (!isRecord(value)) {
    throw inputError(path, "pending 으로 경로마다의 분류나 null 을 들지 않는다");
  }
  const classes = new Map<string, PendingClass>();
  for (const [artifactPath, kind] of Object.entries(value)) {
    if (!isArtifactPath(artifactPath) || !isPendingClass(kind)) {
      throw inputError(
        path,
        `pending 의 ${JSON.stringify(artifactPath)} 가 project/ 아래 경로와 분류가 아니다`,
      );
    }
    classes.set(artifactPath, kind);
  }
  return classes;
}

/** 웹 편집 있음 보고의 `files` 와 `tokens`. 토큰 편집이 있으면 `tokens.json` 도 되돌린다. */
function webEdits(path: string, raw: Readonly<Record<string, unknown>>): WebEdits {
  const files = unknownList(raw.files);
  if (files === undefined) {
    throw inputError(path, "files 로 바뀐 파일의 배열을 들지 않는다");
  }
  if (!Array.isArray(raw.tokens)) {
    throw inputError(path, "tokens 로 토큰 차이의 배열을 들지 않는다");
  }
  const revert: string[] = [];
  const webRemoved: string[] = [];
  const webAdded: string[] = [];
  for (const item of files) {
    const editPath = isRecord(item) ? item.path : undefined;
    const change = isRecord(item) ? item.change : undefined;
    if (typeof editPath !== "string" || !isArtifactPath(editPath)) {
      throw inputError(path, "files 의 항목이 project/ 아래 경로를 들지 않는다");
    }
    if (change === "changed") {
      revert.push(editPath);
    } else if (change === "removed") {
      webRemoved.push(editPath);
    } else if (change === "added") {
      webAdded.push(editPath);
    } else {
      throw inputError(
        path,
        `files 의 ${editPath} 가 모르는 바뀜 ${JSON.stringify(change)} 을 든다`,
      );
    }
  }
  if (raw.tokens.length > 0 && !revert.includes(TOKENS_PATH)) {
    revert.push(TOKENS_PATH);
  }
  return { revert, webRemoved, webAdded };
}

/** `check judge` 의 보고를 읽는다. 올릴 수 없는 결과면 `usage` 오류다. */
function readCheck(path: string): CheckReading {
  const raw = readJson(path);
  if (!isRecord(raw) || raw.command !== "check" || raw.ok !== true || raw.action !== "judge") {
    throw inputError(path, "check judge 의 성공 보고가 아니다");
  }
  const { result } = raw;
  switch (result) {
    case "beforeRecord":
      return { result, pending: null };
    case "clean":
      return { result, pending: pendingOf(path, raw.pending) };
    case "edited":
      return { result, pending: pendingOf(path, raw.pending), edits: webEdits(path, raw) };
    default:
      throw new CommandError(
        "usage",
        `확인 결과가 ${JSON.stringify(result)} 라 올리지 않는다. 웹 편집 없음, 기록 전, 덮어쓰기를 고른 웹 편집 있음만 올린다`,
      );
  }
}

/** `--check` 와 `--overwrite` 로 이번 올리기에 넘길 것을 고른다. 웹 편집 있음은 덮어쓰기를 고른 때만 넘긴다. */
function decisionOf(values: Values): CheckDecision {
  const overwrite = values.overwrite === true;
  if (values.check === undefined) {
    if (overwrite) {
      throw new CommandError(
        "usage",
        "--overwrite 에는 되돌릴 것을 고를 --check <확인 보고> 가 있어야 한다",
      );
    }
    return NO_DECISION;
  }
  const reading = readCheck(values.check);
  if (reading.result !== "edited") {
    return { ...NO_DECISION, pending: reading.pending };
  }
  if (!overwrite) {
    throw new CommandError(
      "usage",
      "확인이 웹 편집을 찾았다. 사람이 덮어쓰기를 고른 때만 --overwrite 로 올린다",
    );
  }
  return { pending: reading.pending, ...reading.edits };
}

const OPTIONS = {
  local: { type: "string" },
  record: { type: "string" },
  "artifact-sha256": { type: "string" },
  check: { type: "string" },
  overwrite: { type: "boolean" },
  "previous-output": { type: "string" },
  changed: { type: "string" },
  plan: { type: "string" },
  index: { type: "string" },
  out: { type: "string" },
  artifact: { type: "string" },
  "first-call": { type: "boolean" },
  commit: { type: "string" },
  at: { type: "string" },
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
  onlyOptions("needs-build", values, ["changed", "check", "overwrite"]);
  const changed = changedPaths(required("needs-build", "changed <바뀐 경로>", values.changed));
  const decision = decisionOf(values);
  const need = needsBuild(changed, [...decision.revert, ...decision.webRemoved]);
  return { action: "needs-build", needed: need.needed, because: need.because };
}

/** `record plan` 의 보고에서 기록에 합칠 것을 읽는다. */
function readPlan(path: string): RecordChanges {
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
  return {
    send: list("send"),
    landed: list("landed"),
    unchanged: list("unchanged"),
    delete: list("delete"),
    gone: list("gone"),
  };
}

const COMMIT = /^[0-9a-f]{7,40}$/;

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
  if (at !== undefined && Number.isNaN(Date.parse(at))) {
    throw new CommandError("usage", `--at ${at} 이 시각이 아니다`);
  }
  const index = readJson(indexPath);
  if (!isRecord(index)) {
    throw inputError(indexPath, "JSON 객체가 아니다");
  }
  const artifact =
    values.artifact === undefined ? new Map<string, Uint8Array>() : readFolder(values.artifact, "");
  const next = nextRecord({
    previous: values.record === undefined ? null : recordFrom(values.record),
    output: readFolder(local, "project/"),
    artifact: new Map([...artifact].filter(([path]) => isArtifactPath(path))),
    changes: readPlan(planPath),
    index: indexLists(index),
    call:
      commit === undefined || at === undefined ? { kind: "first" } : { kind: "last", commit, at },
  });
  const text = serializeRecord(next);
  return {
    action: "write",
    out: writeOutput(out, text),
    files: next.files.size,
    bytes: new TextEncoder().encode(text).byteLength,
    pending: next.pending !== null,
  };
}

/** 기록 명령. */
export function record(args: readonly string[]): ReportFields {
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
    default:
      throw new CommandError("usage", "record 는 plan, needs-build, write 가운데 하나를 받는다");
  }
}
