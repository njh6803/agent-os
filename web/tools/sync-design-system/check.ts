/**
 * 확인 명령. 아티팩트에서 받은 파일을 기록(`sync-record.ts`)과 맞대 웹 편집이 있는지 가른다(design-reverse-sync 명세
 * "확인"과 그 2026-10-22 주석 둘, "기록"). 받기는 두 번이다. 스킬은 이 명령의 `paths` 가 낸 경로를 받고 읽지 못한 것을
 * 적기를 `paths` 가 빌 때까지 되풀이한 뒤 `judge` 로 결과를 얻는다. 처음 `paths` 는 첫 받기(`tokens.json`, 색인, 기록)를,
 * 다음 `paths` 는 첫 받기의 내용으로 고른 그 뒤에 받을 경로를 낸다. 스킬은 받을 경로를 손으로 짓지 않는다.
 *
 * 그 뒤에 받을 경로는 편집이 켜졌으면 기록에 든 마크다운 가운데 `api/` 밖, 색인 `docs` 의 `readme`·`sections`, 기록의
 * 컴포넌트 폴더마다의 README(`lib` 은 뺀다), 기록의 `pending` 이 든 경로다. 편집이 꺼졌으면 `pending` 이 든 경로만이다.
 *
 * 결과는 넷 가운데 하나다(`result`). 명세의 다섯째인 들이는 중(`importing`)은 06 이 더한다.
 *
 * - `clean`(웹 편집 없음). `record` 는 기록의 상태, `pending` 은 `pending` 의 경로마다의 분류(`upload.ts` 의
 *   `PendingClass`)이고 `pending` 이 없으면 null 이다.
 * - `edited`(웹 편집 있음). `tokens` 는 기준본과 맞댄 토큰의 차이(`tokens-json.ts` 의 `diffTokens`), `files` 는 파일의
 *   편집(`changed`, `added`, `removed`. 웹이 `tokens.json` 을 지웠으면 그것도 `removed` 로 든다), `index` 는 기록과 다른
 *   색인 목록이다. `tokensMixed` 는 웹의 `tokens.json` 이 `pending` 의 목표와도 기준본과도 달라, 멈춘 올리기가 보낸
 *   값이 `tokens` 에 섞일 수 있다는 표시다.
 * - `beforeRecord`(기록 전). 편집이 꺼진 색인에 기록도 `tokens.json` 도 없다.
 * - `undecidable`(판단할 수 없음). `reason` 이 까닭이다. 편집이 켜진 뒤 기록이 없거나(`noRecord`), JSON 으로 풀리지
 *   않거나(`recordUnreadable`), 꼴 판을 모르거나(`unknownVersion`), 꼴이 어긋났거나(`recordMalformed`), 들이기의
 *   `claim` 이 들었거나(`claim`. 06 이 가른다), 기준본이 없거나(`noBaseline`), 웹의 `tokens.json` 이 풀리지 않거나
 *   (`tokensUnreadable`), 색인이 없거나 풀리지 않거나(`noIndex`, `indexUnreadable`), 없다는 까닭이 아닌 까닭으로 읽지
 *   못한 경로가 있다(`readFailed`). 확인은 스스로 덮어쓰지 않고 멈춰 사람에게 묻는다.
 *
 * 편집이 꺼진 동안(색인의 `editing` 이 `"off"`)에는 사람이 고칠 수 없어 맞대지 않는다. 기록이 없거나 읽히지 않아도
 * 웹 편집 없음이고, 그때 보낼 것은 `upload.ts` 가 아티팩트의 sha256 과 맞대 고른다. `claim` 도 쓰이지 않는다.
 *
 * 맞대는 값은 `file-hash.ts` 의 것이다. `tokens.json` 은 기준본과 정규 꼴로 맞대고, 색인 목록은 객체의 키 차례를
 * 가리지 않고 맞댄다. `pending` 이 있으면 파일마다 목표 해시, 앞 해시 차례로 맞대고, 색인 목록은 그 목표와도 맞댄다.
 *
 * 명령: `check paths --web <받은 폴더> [--reads <읽지 못한 것>]`, `check judge --web <받은 폴더> [--reads <읽지 못한 것>]`.
 * 받은 폴더는 받은 파일을 아티팩트 경로 그대로(`project/…`) 둔 폴더다. 읽지 못한 것은 JSON
 * `{"absent": [경로, …], "failed": {경로: 문구}}` 이고, `absent` 는 없다는 까닭으로 읽지 못한 경로, `failed` 는 다른
 * 까닭으로 읽지 못한 경로와 그 문구다. `judge` 는 받을 경로가 폴더에도 읽지 못한 것에도 없으면 `input` 오류다. 보고는
 * `paths` 면 아직 받지 않은 경로(`paths`), `judge` 면 위 결과의 칸이다.
 *
 * 못 보는 것: 마크다운이 아닌 파일(그림, 글꼴, 카드의 HTML)과 `api/` 아래 마크다운의 웹 편집, 기록에도 색인 `docs` 에도
 * 없고 기록의 컴포넌트 폴더의 README 도 아닌 경로에 웹이 더한 파일(웹이 새 컴포넌트 폴더에 둔 README 가 그 예다.
 * 명세는 색인이 드는 컴포넌트마다의 README 를 받으라 하지만 2026-10-26 에 받은 색인에는 컴포넌트 목록이 없었다), 색인의 목록 밖
 * 칸(제목, `lastChange` 등)의 편집. 웹이 더한 그림·글꼴은 색인 목록(`index`)의 편집으로만 나오고 `files` 에는 들지
 * 않는다. 웹 편집이 없을 때 아직 보내지 않은 `pending` 파일의 분류는 웹의 파일이 앞 기록의 값과 같은지로만 가른다.
 */

import { parseArgs } from "node:util";
import { CommandError, parsedArgs, type ReportFields } from "./command.ts";
import {
  fileHash,
  INDEX_PATH,
  isRecorded,
  parseJson,
  RECORD_PATH,
  TOKENS_PATH,
} from "./file-hash.ts";
import {
  byPath,
  inputError,
  isArtifactPath,
  isRecord,
  readFolder,
  readJson,
  sortedPaths,
  stringList,
  unknownList,
} from "./io.ts";
import {
  INDEX_KEYS,
  indexLists,
  readRecord,
  type IndexKey,
  type RecordRead,
  type SyncRecord,
} from "./sync-record.ts";
import {
  comparisonHash,
  diffTokens,
  readTokens,
  type JsonValue,
  type TokenDiff,
} from "./tokens-json.ts";
import type { PendingClass } from "./upload.ts";

/** 받은 파일과 읽지 못한 경로. 경로는 아티팩트 경로다. */
export interface WebFiles {
  readonly files: ReadonlyMap<string, Uint8Array>;
  /** 없다는 까닭으로 읽지 못한 경로. */
  readonly absent: ReadonlySet<string>;
  /** 다른 까닭으로 읽지 못한 경로와 그 문구. */
  readonly failed: ReadonlyMap<string, string>;
}

export type RecordStatus = "ok" | "absent" | "unreadable" | "unknownVersion" | "malformed";

export type UndecidableReason =
  | "readFailed"
  | "noIndex"
  | "indexUnreadable"
  | "noRecord"
  | "recordUnreadable"
  | "unknownVersion"
  | "recordMalformed"
  | "claim"
  | "noBaseline"
  | "tokensUnreadable";

export type FileChange = "changed" | "added" | "removed";

export type FileEdit = { readonly path: string; readonly change: FileChange };

export type IndexEdit = {
  readonly key: IndexKey;
  readonly before: JsonValue;
  readonly after: JsonValue;
};

/** `pending` 의 경로마다의 분류. */
export type PendingReport = Readonly<Record<string, PendingClass>>;

export type CheckReport =
  | {
      readonly result: "clean";
      readonly editing: "on" | "off";
      readonly record: RecordStatus;
      readonly pending: PendingReport | null;
    }
  | {
      readonly result: "edited";
      readonly tokens: readonly TokenDiff[];
      readonly tokensMixed: boolean;
      readonly files: readonly FileEdit[];
      readonly index: readonly IndexEdit[];
      readonly pending: PendingReport | null;
    }
  | { readonly result: "beforeRecord"; readonly editing: "off" }
  | {
      readonly result: "undecidable";
      readonly reason: UndecidableReason;
      readonly message: string;
      readonly paths: readonly string[];
    };

/** 첫 받기의 경로. */
const FIRST = [INDEX_PATH, RECORD_PATH, TOKENS_PATH];

const MARKDOWN = /\.mdx?$/i;
const API = "project/api/";

function text(data: Uint8Array): string {
  return new TextDecoder().decode(data);
}

function undecidable(
  reason: UndecidableReason,
  message: string,
  paths: readonly string[],
): CheckReport {
  return { result: "undecidable", reason, message, paths };
}

/** 받은 파일과 읽지 못한 경로가 겹치면 `input` 오류다. */
function checkConsistent(web: WebFiles): void {
  const clash = [
    ...[...web.absent].filter((path) => web.files.has(path) || web.failed.has(path)),
    ...[...web.failed.keys()].filter((path) => web.files.has(path)),
  ];
  if (clash.length > 0) {
    throw new CommandError(
      "input",
      `받은 파일과 읽지 못한 경로가 겹친다: ${sortedPaths(clash).join(", ")}`,
    );
  }
}

/** 받을 경로 가운데 폴더에도 읽지 못한 것에도 없는 것이 있으면 `input` 오류다. */
function requireFetched(web: WebFiles, paths: readonly string[]): void {
  const missing = unfetched(web, paths);
  if (missing.length > 0) {
    throw new CommandError(
      "input",
      `받지 않은 경로가 있다: ${missing.join(", ")}. 받거나 읽지 못한 까닭을 적어 다시 부른다`,
    );
  }
}

/** 다른 까닭으로 읽지 못한 경로가 있으면 판단할 수 없음, 없으면 null. */
function failedReads(web: WebFiles, paths: readonly string[]): CheckReport | null {
  const failed = paths.filter((path) => web.failed.has(path));
  if (failed.length === 0) {
    return null;
  }
  const message = failed.map((path) => `${path}: ${web.failed.get(path) ?? ""}`).join("; ");
  return undecidable("readFailed", message, failed);
}

type IndexRead =
  | { readonly kind: "absent" }
  | { readonly kind: "unreadable" }
  | { readonly kind: "ok"; readonly index: Readonly<Record<string, unknown>> };

function readIndex(web: WebFiles): IndexRead {
  const data = web.files.get(INDEX_PATH);
  if (data === undefined) {
    return { kind: "absent" };
  }
  const index = parseJson(text(data));
  return isRecord(index) ? { kind: "ok", index } : { kind: "unreadable" };
}

function editingOff(index: Readonly<Record<string, unknown>>): boolean {
  return index.editing === "off";
}

/** 기록을 읽은 것. 기록이 없으면 null. */
function recordOf(web: WebFiles): RecordRead | null {
  const data = web.files.get(RECORD_PATH);
  return data === undefined ? null : readRecord(text(data));
}

function statusOf(read: RecordRead | null): RecordStatus {
  if (read === null) {
    return "absent";
  }
  return read.kind;
}

function pendingPaths(record: SyncRecord | null): string[] {
  const pending = record?.pending ?? null;
  return pending === null ? [] : [...pending.files.keys(), ...pending.delete];
}

/** 색인 `docs` 의 `readme`·`sections` 가운데 아티팩트 경로인 것. */
function docPaths(index: IndexRead): string[] {
  const docs = index.kind === "ok" ? index.index.docs : undefined;
  if (!isRecord(docs)) {
    return [];
  }
  const listed = [docs.readme, ...(unknownList(docs.sections) ?? [])];
  return listed.filter((path): path is string => typeof path === "string" && isArtifactPath(path));
}

/** 기록의 컴포넌트 폴더마다의 README. 공용 폴더 `lib` 은 뺀다. */
function componentReadmes(record: SyncRecord): string[] {
  const names = new Set<string>();
  for (const path of record.files.keys()) {
    const [root, folder, name, ...rest] = path.split("/");
    if (
      root === "project" &&
      folder === "components" &&
      name !== undefined &&
      name !== "lib" &&
      rest.length > 0
    ) {
      names.add(name);
    }
  }
  return [...names].map((name) => `project/components/${name}/README.md`);
}

/** 첫 받기의 뒤에 받을 경로. 경로 차례다. */
function fetchList(web: WebFiles): string[] {
  const index = readIndex(web);
  const read = recordOf(web);
  const record = read?.kind === "ok" ? read.record : null;
  const paths = new Set(pendingPaths(record));
  if (!(index.kind === "ok" && editingOff(index.index))) {
    for (const path of docPaths(index)) {
      paths.add(path);
    }
    if (record !== null) {
      for (const path of record.files.keys()) {
        if (MARKDOWN.test(path) && !path.startsWith(API)) {
          paths.add(path);
        }
      }
      for (const path of componentReadmes(record)) {
        paths.add(path);
      }
    }
  }
  return [...paths].filter((path) => !FIRST.includes(path) && isRecorded(path)).sort(byPath);
}

function unfetched(web: WebFiles, paths: readonly string[]): string[] {
  return paths.filter(
    (path) => !web.files.has(path) && !web.absent.has(path) && !web.failed.has(path),
  );
}

/**
 * 아직 받지 않은 경로. 첫 받기를 다 받기 전에는 첫 받기의 경로를, 그 뒤에는 첫 받기의 내용으로 고른 경로 가운데
 * 받지 않은 것을 낸다. 비면 판정할 수 있다. 경로 차례다.
 */
export function nextFetch(web: WebFiles): string[] {
  checkConsistent(web);
  const first = unfetched(web, FIRST);
  return first.length > 0 ? first.sort(byPath) : unfetched(web, fetchList(web));
}

function sortedReport(classes: ReadonlyMap<string, PendingClass>): PendingReport {
  return Object.fromEntries([...classes].sort(([left], [right]) => byPath(left, right)));
}

function judgeOff(web: WebFiles, read: RecordRead | null): CheckReport {
  if (read === null && !web.files.has(TOKENS_PATH)) {
    return { result: "beforeRecord", editing: "off" };
  }
  const pending = read?.kind === "ok" ? read.record.pending : null;
  if (pending === null) {
    return { result: "clean", editing: "off", record: statusOf(read), pending: null };
  }
  const paths = [...pending.files.keys(), ...pending.delete];
  requireFetched(web, paths);
  const failed = failedReads(web, paths);
  if (failed !== null) {
    return failed;
  }
  // 편집이 꺼진 동안 사람은 고칠 수 없어, 목표와 다른 파일은 아직 보내지 않은 것이다.
  const classes = new Map<string, PendingClass>();
  for (const [path, target] of pending.files) {
    const data = web.files.get(path);
    classes.set(
      path,
      data !== undefined && fileHash(path, data) === target.hash ? "sent" : "unsent",
    );
  }
  for (const path of pending.delete) {
    classes.set(path, web.files.has(path) ? "remaining" : "deleted");
  }
  return { result: "clean", editing: "off", record: "ok", pending: sortedReport(classes) };
}

/** 파일 하나를 가른 것. 분류는 `pending` 의 경로에만 붙는다. */
interface FileVerdict {
  readonly pending: PendingClass | null;
  readonly change: FileChange | null;
}

function classifyFile(path: string, data: Uint8Array | undefined, record: SyncRecord): FileVerdict {
  const before = record.files.get(path)?.hash ?? null;
  const target = record.pending?.files.get(path)?.hash ?? null;
  const toDelete = record.pending?.delete.includes(path) ?? false;
  if (data === undefined) {
    if (toDelete) {
      return { pending: "deleted", change: null };
    }
    if (before === null) {
      return { pending: target === null ? null : "unsent", change: null };
    }
    return { pending: target === null ? null : "edited", change: "removed" };
  }
  const hash = fileHash(path, data);
  if (target !== null && hash === target) {
    return { pending: "sent", change: null };
  }
  if (hash === before || (before === null && toDelete)) {
    return { pending: toDelete ? "remaining" : target === null ? null : "unsent", change: null };
  }
  return {
    pending: target === null && !toDelete ? null : "edited",
    change: before === null ? "added" : "changed",
  };
}

/** 웹의 tokens.json 편집. `mixed` 는 `diffs` 에 멈춘 올리기가 보낸 값이 섞일 수 있다는 표시다. */
interface TokensEdit {
  readonly diffs: readonly TokenDiff[];
  readonly mixed: boolean;
  readonly removed: boolean;
}

const NO_TOKEN_EDIT: TokensEdit = { diffs: [], mixed: false, removed: false };

/** 웹의 tokens.json 을 가른 것. `pending` 은 `pending` 의 목표가 있을 때만의 분류다. */
type TokensVerdict =
  | ({ readonly kind: "judged"; readonly pending: PendingClass | null } & TokensEdit)
  | { readonly kind: "undecidable"; readonly report: CheckReport };

/** 웹의 tokens.json 을 기준본과 `pending` 의 목표와 맞댄다. */
function judgeTokens(web: WebFiles, record: SyncRecord): TokensVerdict {
  const target = record.pending?.files.get(TOKENS_PATH);
  const judged = (pending: PendingClass, edit: TokensEdit = NO_TOKEN_EDIT): TokensVerdict => ({
    kind: "judged",
    pending: target === undefined ? null : pending,
    ...edit,
  });
  const data = web.files.get(TOKENS_PATH);
  if (data === undefined) {
    return record.files.has(TOKENS_PATH)
      ? judged("edited", { ...NO_TOKEN_EDIT, removed: true })
      : judged("unsent");
  }
  const parsed = parseJson(text(data));
  if (parsed === undefined) {
    return {
      kind: "undecidable",
      report: undecidable("tokensUnreadable", `웹의 ${TOKENS_PATH} 가 JSON 으로 풀리지 않는다`, [
        TOKENS_PATH,
      ]),
    };
  }
  const tokens = readTokens(parsed);
  if (target !== undefined && comparisonHash(tokens) === target.hash) {
    return judged("sent");
  }
  if (record.baseline === null) {
    return {
      kind: "undecidable",
      report: undecidable(
        "noBaseline",
        `기록에 기준본이 없어 웹의 ${TOKENS_PATH} 와 맞댈 수 없다`,
        [RECORD_PATH],
      ),
    };
  }
  const diffs = diffTokens(readTokens(record.baseline), tokens);
  if (diffs.length === 0) {
    return judged("unsent");
  }
  return judged("edited", { diffs, mixed: target !== undefined, removed: false });
}

function isJsonArray(value: JsonValue): value is readonly JsonValue[] {
  return Array.isArray(value);
}

/** 객체의 키를 차례대로 놓은 값. 배열의 차례는 그대로다. */
function canonical(value: JsonValue): JsonValue {
  if (isJsonArray(value)) {
    return value.map(canonical);
  }
  if (typeof value === "object" && value !== null) {
    return Object.fromEntries(
      Object.entries(value)
        .sort(([left], [right]) => byPath(left, right))
        .map(([key, item]) => [key, canonical(item)]),
    );
  }
  return value;
}

function sameJson(left: JsonValue, right: JsonValue): boolean {
  return JSON.stringify(canonical(left)) === JSON.stringify(canonical(right));
}

/** 기록과도 `pending` 의 목표와도 다른 색인 목록. 기록에 색인 목록이 없으면 맞대지 않는다. */
function indexEdits(index: Readonly<Record<string, unknown>>, record: SyncRecord): IndexEdit[] {
  const before = record.index;
  if (before === null) {
    return [];
  }
  const after = indexLists(index);
  const target = record.pending?.index ?? null;
  return INDEX_KEYS.filter(
    (key) =>
      !sameJson(after[key], before[key]) && (target === null || !sameJson(after[key], target[key])),
  ).map((key) => ({ key, before: before[key], after: after[key] }));
}

function judgeOn(
  web: WebFiles,
  index: Readonly<Record<string, unknown>>,
  read: RecordRead | null,
): CheckReport {
  if (read === null) {
    return undecidable("noRecord", "웹 편집이 켜졌는데 기록이 없어 웹 편집을 가를 수 없다", [
      RECORD_PATH,
    ]);
  }
  switch (read.kind) {
    case "unreadable":
      return undecidable("recordUnreadable", "기록이 JSON 으로 풀리지 않는다", [RECORD_PATH]);
    case "unknownVersion":
      return undecidable(
        "unknownVersion",
        `기록의 꼴 판 ${JSON.stringify(read.version)} 을 모른다`,
        [RECORD_PATH],
      );
    case "malformed":
      return undecidable("recordMalformed", `기록의 꼴이 어긋났다: ${read.message}`, [RECORD_PATH]);
    case "ok":
      break;
  }
  const { record } = read;
  if (record.claim !== null) {
    return undecidable("claim", "기록에 들이기의 claim 이 있다. claim 을 가르는 것은 06 이다", [
      RECORD_PATH,
    ]);
  }
  const paths = fetchList(web);
  requireFetched(web, paths);
  const failed = failedReads(web, paths);
  if (failed !== null) {
    return failed;
  }

  const tokens = judgeTokens(web, record);
  if (tokens.kind === "undecidable") {
    return tokens.report;
  }
  const classes = new Map<string, PendingClass>();
  if (tokens.pending !== null) {
    classes.set(TOKENS_PATH, tokens.pending);
  }
  const files: FileEdit[] = tokens.removed ? [{ path: TOKENS_PATH, change: "removed" }] : [];
  for (const path of paths) {
    const verdict = classifyFile(path, web.files.get(path), record);
    if (verdict.pending !== null) {
      classes.set(path, verdict.pending);
    }
    if (verdict.change !== null) {
      files.push({ path, change: verdict.change });
    }
  }
  const pending = record.pending === null ? null : sortedReport(classes);
  const changedIndex = indexEdits(index, record);
  if (tokens.diffs.length === 0 && files.length === 0 && changedIndex.length === 0) {
    return { result: "clean", editing: "on", record: "ok", pending };
  }
  return {
    result: "edited",
    tokens: tokens.diffs,
    tokensMixed: tokens.mixed,
    files: files.sort((left, right) => byPath(left.path, right.path)),
    index: changedIndex,
    pending,
  };
}

/** 받은 파일을 기록과 맞댄 결과. 받을 경로를 다 받지 않았으면 `input` 오류다. */
export function judge(web: WebFiles): CheckReport {
  checkConsistent(web);
  requireFetched(web, FIRST);
  const failed = failedReads(web, FIRST);
  if (failed !== null) {
    return failed;
  }
  const index = readIndex(web);
  if (index.kind === "absent") {
    return undecidable("noIndex", "색인이 없다", [INDEX_PATH]);
  }
  if (index.kind === "unreadable") {
    return undecidable("indexUnreadable", "색인이 JSON 객체로 풀리지 않는다", [INDEX_PATH]);
  }
  const read = recordOf(web);
  return editingOff(index.index) ? judgeOff(web, read) : judgeOn(web, index.index, read);
}

function diffJson(diff: TokenDiff): JsonValue {
  const fields: Record<string, JsonValue> = { kind: diff.kind, family: diff.family };
  for (const key of ["token", "theme", "group", "field"] as const) {
    const value = diff[key];
    if (value !== undefined) {
      fields[key] = value;
    }
  }
  return { ...fields, before: diff.before, after: diff.after };
}

/** 확인 결과의 보고 칸. */
export function reportFields(report: CheckReport): ReportFields {
  return report.result === "edited" ? { ...report, tokens: report.tokens.map(diffJson) } : report;
}

/** 읽지 못한 것의 파일. 주지 않으면 비었다. */
function readReads(path: string | undefined): Pick<WebFiles, "absent" | "failed"> {
  if (path === undefined) {
    return { absent: new Set(), failed: new Map() };
  }
  const raw = readJson(path);
  if (!isRecord(raw) || Object.keys(raw).some((key) => key !== "absent" && key !== "failed")) {
    throw inputError(path, "absent 와 failed 만 든 JSON 객체가 아니다");
  }
  const absent = raw.absent === undefined ? [] : stringList(raw.absent);
  if (absent === undefined || !absent.every(isArtifactPath)) {
    throw inputError(path, "absent 로 project/ 아래 경로의 배열을 들지 않는다");
  }
  const failedRaw = raw.failed ?? {};
  if (!isRecord(failedRaw)) {
    throw inputError(path, "failed 로 경로마다 문구를 든 객체를 들지 않는다");
  }
  const failed = new Map<string, string>();
  for (const [failedPath, message] of Object.entries(failedRaw)) {
    if (!isArtifactPath(failedPath) || typeof message !== "string") {
      throw inputError(
        path,
        `failed 의 ${JSON.stringify(failedPath)} 가 project/ 아래 경로와 문구가 아니다`,
      );
    }
    failed.set(failedPath, message);
  }
  return { absent: new Set(absent), failed };
}

/** 확인 명령. */
export function runCheck(args: readonly string[]): ReportFields {
  const { values, positionals } = parsedArgs(() =>
    parseArgs({
      args: [...args],
      options: { web: { type: "string" }, reads: { type: "string" } },
      strict: true,
      allowPositionals: true,
    }),
  );
  const [action, ...rest] = positionals;
  if ((action !== "paths" && action !== "judge") || rest.length > 0) {
    throw new CommandError("usage", "check 는 paths 나 judge 하나를 받는다");
  }
  if (values.web === undefined) {
    throw new CommandError("usage", `check ${action} 에는 --web <받은 폴더> 가 있어야 한다`);
  }
  const web: WebFiles = { files: readFolder(values.web, ""), ...readReads(values.reads) };
  return action === "paths"
    ? { action, paths: nextFetch(web) }
    : { action, ...reportFields(judge(web)) };
}
