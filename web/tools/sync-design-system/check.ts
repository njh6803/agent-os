/**
 * 확인의 판정. 아티팩트에서 받은 파일을 기록(`sync-record.ts`)과 맞대 웹 편집이 있는지 가른다(design-reverse-sync 명세
 * "확인"과 그 2026-10-22 주석 둘, "기록", "겹침"). 명령의 인자는 `check-command.ts`, 결과의 꼴은 `check-report.ts` 다.
 *
 * 받기는 두 번이다. 처음 `nextFetch` 는 첫 받기(`tokens.json`, 색인, 기록)를, 다음은 첫 받기의 내용으로 고른 그 뒤에
 * 받을 경로를 낸다. 그 뒤에 받을 경로는 편집이 켜졌으면 기록에 든 마크다운 가운데 `api/` 밖, 색인 `docs` 의
 * `readme`·`sections`, 기록의 컴포넌트 폴더마다의 README(`lib` 은 뺀다), 기록의 `pending` 과 `claim` 이 든 경로다.
 * 편집이 꺼졌으면 `pending` 이 든 경로만이다.
 *
 * 편집이 꺼진 동안(색인의 `editing` 이 `"off"`)에는 사람이 고칠 수 없어 맞대지 않는다. 기록이 없거나 읽히지 않아도
 * 웹 편집 없음이고, 그때 보낼 것은 `upload.ts` 가 아티팩트의 sha256 과 맞대 고른다. `claim` 도 쓰이지 않는다.
 *
 * 맞대는 값은 `file-hash.ts` 의 것이다. 파일마다 `pending` 의 목표 해시, `claim` 의 해시, 기록의 앞 해시 차례로 맞대고
 * 어디와도 다르면 웹 편집이다. `tokens.json` 은 목표 해시와 다르면 토큰·벌마다 `claim` 의 사본, 기록의 기준본 차례로
 * 대 보아 어디와도 다른 몫만 웹 편집이다. 색인 목록은 객체의 키 차례를 가리지 않고 기록, `pending` 의 목표,
 * `claim` 의 목록과 맞댄다.
 *
 * 기록에 `claim` 이 있으면 결과는 들이는 중이다. `claim` 의 브랜치가 지금 브랜치와 같으면 자기 것이다. 더 고친 몫은
 * 위 차례로 웹 편집인 몫이고, `tokens.json` 은 그 가운데 지금 코드에서 지은 `tokens.json` 과도 다른 몫만 든다(웹이
 * 코드와 같은 몫은 들인 것과 같다). 남의 `claim` 에 더 고친 몫이 있으면 이어받을 기준본(`tokens-overlay.ts`)도 짓는다.
 * 브랜치의 PR 상태는 보지 않는다. 그것은 결정표(`decide.ts`)가 스킬이 넘긴 PR 상태로 가른다.
 *
 * 못 보는 것: 마크다운이 아닌 파일(그림, 글꼴, 카드의 HTML)과 `api/` 아래 마크다운의 웹 편집, 기록에도 색인 `docs` 에도
 * `claim` 에도 없고 기록의 컴포넌트 폴더의 README 도 아닌 경로에 웹이 더한 파일(웹이 새 컴포넌트 폴더에 둔 README 가
 * 그 예다. 명세는 색인이 드는 컴포넌트마다의 README 를 받으라 하지만 2026-10-26 에 받은 색인에는 컴포넌트 목록이
 * 없었다), 색인의 목록 밖 칸(제목, `lastChange` 등)의 편집. 웹이 더한 그림·글꼴은 색인 목록(`index`)의 편집으로만
 * 나오고 `files` 에는 들지 않는다. 웹 편집이 없을 때 아직 보내지 않은 `pending` 파일의 분류는 웹의 파일이 앞 기록의
 * 값과 같은지로만 가른다. `claim` 이 든 토큰이나 마크다운을 사람이 웹에서 기준본이나 앞 해시의 값으로 되돌린 편집은
 * 보이지 않는다(명세 "`pending` 과 함께 있으면"의 주석이 받은 값이다). 더 고친 몫의 마크다운은 지금 코드와 맞대지
 * 않는다(명세는 `tokens.json` 만 코드와 맞댄다).
 */

import {
  type CheckReport,
  type ClaimSummary,
  type EditLists,
  type FileChange,
  type FileEdit,
  type IndexEdit,
  type PendingReport,
  type RecordStatus,
  type UndecidableReason,
} from "./check-report.ts";
import { CommandError } from "./command.ts";
import { fileHash, INDEX_PATH, isRecorded, RECORD_PATH, TOKENS_PATH } from "./file-hash.ts";
import { byPath, isArtifactPath, isRecord, parseJson, sortedPaths, unknownList } from "./io.ts";
import {
  INDEX_KEYS,
  indexLists,
  readRecord,
  type Claim,
  type IndexLists,
  type PendingClass,
  type RecordRead,
  type SyncRecord,
} from "./sync-record.ts";
import {
  comparisonHash,
  diffTokens,
  readTokens,
  type CanonicalTokens,
  type JsonValue,
  type TokenDiff,
  valueAt,
} from "./tokens-json.ts";
import { inheritedBaseline } from "./tokens-overlay.ts";

/** 받은 파일과 읽지 못한 경로. 경로는 아티팩트 경로다. */
export interface WebFiles {
  readonly files: ReadonlyMap<string, Uint8Array>;
  /** 없다는 까닭으로 읽지 못한 경로. */
  readonly absent: ReadonlySet<string>;
  /** 다른 까닭으로 읽지 못한 경로와 그 문구. */
  readonly failed: ReadonlyMap<string, string>;
}

/** `claim` 을 가르는 데 드는 이 체크아웃의 것. `claim` 이 든 기록을 판정할 때만 있어야 한다. */
export interface CheckContext {
  /** 지금 브랜치. */
  readonly branch: string | null;
  /** 지금 코드에서 지은 `tokens.json` 의 정규 꼴. */
  readonly codeTokens: CanonicalTokens | null;
}

export const NO_CONTEXT: CheckContext = { branch: null, codeTokens: null };

/** 판정과 이어받을 기준본. 기준본은 남의 `claim` 에 더 고친 몫이 있을 때만 있다. */
export interface Judged {
  readonly report: CheckReport;
  readonly inherit: JsonValue | null;
}

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
  return read === null ? "absent" : read.kind;
}

function pendingPaths(record: SyncRecord | null): string[] {
  const pending = record?.pending ?? null;
  return pending === null ? [] : [...pending.files.keys(), ...pending.delete];
}

function claimPaths(claim: Claim | null): string[] {
  return claim === null ? [] : [...claim.changed.keys(), ...claim.added.keys(), ...claim.removed];
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

/**
 * 기록의 컴포넌트 폴더마다의 README. 컴포넌트 폴더는 `project/components/` 아래 파일이 든 폴더다. 번들 변환기는
 * 컴포넌트를 묶음 폴더 아래에 두어(`components/atoms/Button/`) 첫 칸을 이름으로 읽으면 묶음 폴더의 README 를
 * 낸다(design-reverse-sync 티켓 08 결과). 공용 폴더 `lib` 아래와 `components/` 바로 아래의 파일은 뺀다.
 */
function componentReadmes(record: SyncRecord): string[] {
  const folders = new Set<string>();
  for (const path of record.files.keys()) {
    const [root, folder, first, ...rest] = path.split("/");
    if (
      root === "project" &&
      folder === "components" &&
      first !== undefined &&
      first !== "lib" &&
      rest.length > 0
    ) {
      folders.add(path.slice(0, path.lastIndexOf("/")));
    }
  }
  return [...folders].map((component) => `${component}/README.md`);
}

/** 첫 받기의 뒤에 받을 경로. 경로 차례다. */
function fetchList(web: WebFiles): string[] {
  const index = readIndex(web);
  const read = recordOf(web);
  const record = read?.kind === "ok" ? read.record : null;
  const paths = new Set(pendingPaths(record));
  if (!(index.kind === "ok" && editingOff(index.index))) {
    for (const path of [...docPaths(index), ...claimPaths(record?.claim ?? null)]) {
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

/** 파일 하나를 `pending` 의 목표, `claim`, 기록의 앞 해시 차례로 맞댄다. */
function classifyFile(path: string, data: Uint8Array | undefined, record: SyncRecord): FileVerdict {
  const before = record.files.get(path)?.hash ?? null;
  const target = record.pending?.files.get(path)?.hash ?? null;
  const toDelete = record.pending?.delete.includes(path) ?? false;
  const { claim } = record;
  const claimed = claim?.changed.get(path) ?? claim?.added.get(path) ?? null;
  const inPending = target !== null || toDelete;
  /** 웹 편집이 아닌 것. */
  const quiet = (pending: PendingClass): FileVerdict => ({
    pending: inPending ? pending : null,
    change: null,
  });
  const edit = (change: FileChange): FileVerdict => ({
    pending: inPending ? "edited" : null,
    change,
  });

  if (data === undefined) {
    if (toDelete) {
      return quiet("deleted");
    }
    if (claim?.removed.includes(path) === true) {
      return quiet("claimed");
    }
    return before === null ? quiet("unsent") : edit("removed");
  }
  const hash = fileHash(path, data);
  if (hash === target) {
    return quiet("sent");
  }
  if (hash === claimed) {
    return quiet("claimed");
  }
  if (hash === before) {
    return quiet(toDelete ? "remaining" : "unsent");
  }
  if (before === null) {
    return toDelete ? quiet("remaining") : edit("added");
  }
  return edit("changed");
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

/**
 * 기준본과 다른 웹의 차이 가운데 `claim` 의 사본과도, 지금 코드와도 다른 것. `claim` 의 사본과 같은 자리가 있었는지도
 * 낸다. `claim` 이 없으면 차이 그대로다.
 */
function beyondClaim(
  diffs: readonly TokenDiff[],
  claim: Claim | null,
  code: CanonicalTokens | null,
): { readonly diffs: readonly TokenDiff[]; readonly claimed: boolean } {
  if (claim === null) {
    return { diffs, claimed: false };
  }
  const copy = claim.tokens === null ? null : readTokens(claim.tokens);
  const unclaimed = diffs.filter((diff) => copy === null || !holds(copy, diff));
  const further = code === null ? unclaimed : unclaimed.filter((diff) => !holds(code, diff));
  return { diffs: further, claimed: unclaimed.length < diffs.length };
}

/** `tokens` 의 그 차이 자리가 차이의 뒤 값과 같은가. */
function holds(tokens: CanonicalTokens, diff: TokenDiff): boolean {
  return JSON.stringify(valueAt(tokens, diff)) === JSON.stringify(diff.after);
}

/** 웹의 tokens.json 을 `pending` 의 목표, `claim` 의 사본, 기준본 차례로 맞댄다. */
function judgeTokens(
  web: WebFiles,
  record: SyncRecord,
  code: CanonicalTokens | null,
): TokensVerdict {
  const target = record.pending?.files.get(TOKENS_PATH);
  const judged = (pending: PendingClass, edit: TokensEdit = NO_TOKEN_EDIT): TokensVerdict => ({
    kind: "judged",
    pending: target === undefined ? null : pending,
    ...edit,
  });
  const data = web.files.get(TOKENS_PATH);
  if (data === undefined) {
    if (!record.files.has(TOKENS_PATH)) {
      return judged("unsent");
    }
    return record.claim !== null && record.claim.tokens === null
      ? judged("claimed")
      : judged("edited", { ...NO_TOKEN_EDIT, removed: true });
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
  const { diffs, claimed } = beyondClaim(
    diffTokens(readTokens(record.baseline), tokens),
    record.claim,
    code,
  );
  if (diffs.length === 0) {
    return judged(claimed ? "claimed" : "unsent");
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

/** 기록, `pending` 의 목표, `claim` 의 목록과 모두 다른 색인 목록. 기록에 색인 목록이 없으면 맞대지 않는다. */
function indexEdits(index: Readonly<Record<string, unknown>>, record: SyncRecord): IndexEdit[] {
  const before = record.index;
  if (before === null) {
    return [];
  }
  const after = indexLists(index);
  const others: IndexLists[] = [record.pending?.index, record.claim?.index].filter(
    (lists): lists is IndexLists => lists !== undefined,
  );
  return INDEX_KEYS.filter(
    (key) =>
      !sameJson(after[key], before[key]) &&
      others.every((lists) => !sameJson(after[key], lists[key])),
  ).map((key) => ({ key, before: before[key], after: after[key] }));
}

/** 들이는 중의 `claim`. `tokens.json` 은 사본이 있으면 고친 것, 없고 기록에 있으면 지운 것으로 든다. */
function claimSummary(claim: Claim, record: SyncRecord, branch: string | null): ClaimSummary {
  const tokensRemoved = claim.tokens === null && record.files.has(TOKENS_PATH);
  return {
    branch: claim.branch,
    ticket: claim.ticket,
    at: claim.at,
    own: claim.branch === branch,
    changed: sortedPaths([
      ...claim.changed.keys(),
      ...(claim.tokens === null ? [] : [TOKENS_PATH]),
    ]),
    added: sortedPaths(claim.added.keys()),
    removed: sortedPaths([...claim.removed, ...(tokensRemoved ? [TOKENS_PATH] : [])]),
  };
}

function editsEmpty(edits: EditLists): boolean {
  return edits.tokens.length === 0 && edits.files.length === 0 && edits.index.length === 0;
}

function recordOrUndecidable(read: RecordRead | null): CheckReport | SyncRecord {
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
      return read.record;
  }
}

function judgeOn(
  web: WebFiles,
  index: Readonly<Record<string, unknown>>,
  read: RecordRead | null,
  context: CheckContext,
): Judged {
  const record = recordOrUndecidable(read);
  if ("result" in record) {
    return { report: record, inherit: null };
  }
  const { claim } = record;
  if (claim !== null && (context.branch === null || context.codeTokens === null)) {
    throw new CommandError(
      "usage",
      "기록에 claim 이 있어 지금 브랜치(--branch)와 지금 코드에서 지은 tokens.json(--code-tokens)이 있어야 한다",
    );
  }
  const paths = fetchList(web);
  requireFetched(web, paths);
  const failed = failedReads(web, paths);
  if (failed !== null) {
    return { report: failed, inherit: null };
  }

  const tokens = judgeTokens(web, record, context.codeTokens);
  if (tokens.kind === "undecidable") {
    return { report: tokens.report, inherit: null };
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
  const edits: EditLists = {
    tokens: tokens.diffs,
    tokensMixed: tokens.mixed,
    files: files.sort((left, right) => byPath(left.path, right.path)),
    index: indexEdits(index, record),
  };

  if (claim !== null) {
    const summary = claimSummary(claim, record, context.branch);
    const webTokens = web.files.get(TOKENS_PATH);
    const inherit =
      summary.own || editsEmpty(edits) || webTokens === undefined
        ? null
        : inheritedBaseline(parseJson(text(webTokens)), claim.tokens, edits.tokens);
    return {
      report: { result: "importing", claim: summary, further: edits, pending, inherit: null },
      inherit,
    };
  }
  if (editsEmpty(edits)) {
    return { report: { result: "clean", editing: "on", record: "ok", pending }, inherit: null };
  }
  return { report: { result: "edited", ...edits, pending }, inherit: null };
}

/** 받은 파일을 기록과 맞댄 결과와 이어받을 기준본. 받을 경로를 다 받지 않았으면 `input` 오류다. */
export function judgeWithInherit(web: WebFiles, context: CheckContext = NO_CONTEXT): Judged {
  checkConsistent(web);
  requireFetched(web, FIRST);
  const failed = failedReads(web, FIRST);
  if (failed !== null) {
    return { report: failed, inherit: null };
  }
  const index = readIndex(web);
  if (index.kind === "absent") {
    return { report: undecidable("noIndex", "색인이 없다", [INDEX_PATH]), inherit: null };
  }
  if (index.kind === "unreadable") {
    return {
      report: undecidable("indexUnreadable", "색인이 JSON 객체로 풀리지 않는다", [INDEX_PATH]),
      inherit: null,
    };
  }
  const read = recordOf(web);
  return editingOff(index.index)
    ? { report: judgeOff(web, read), inherit: null }
    : judgeOn(web, index.index, read, context);
}

/** 받은 파일을 기록과 맞댄 결과. */
export function judge(web: WebFiles, context: CheckContext = NO_CONTEXT): CheckReport {
  return judgeWithInherit(web, context).report;
}
