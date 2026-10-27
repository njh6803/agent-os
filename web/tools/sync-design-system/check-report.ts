/**
 * 확인 보고의 꼴(design-reverse-sync 명세 "확인"의 "결과는 다섯이다", "겹침"). 확인(`check.ts`)이 이 꼴로 결과를 짓고
 * `reportFields` 로 보고 JSON 의 칸에 옮기며, 그 보고를 받는 기록 명령(`record.ts`)과 결정표(`decide.ts`)는
 * `readCheckReport` 로 다시 읽는다. 결과나 바뀜의 이름을 바꾸면 이 모듈의 타입과 읽기를 함께 고친다(05 의 셀프 리뷰가
 * 짓기와 읽기가 두 파일에 갈린 것을 Shotgun Surgery 로 짚어 06 이 모았다).
 *
 * 결과는 다섯이다(`result`).
 *
 * - `clean`(웹 편집 없음). `record` 는 기록의 상태, `pending` 은 `pending` 의 경로마다의 분류이고 `pending` 이 없으면
 *   null 이다.
 * - `edited`(웹 편집 있음). `tokens` 는 기준본과 맞댄 토큰의 차이(`tokens-json.ts` 의 `diffTokens`), `files` 는 파일의
 *   편집(`changed`, `added`, `removed`. 웹이 `tokens.json` 을 지웠으면 그것도 `removed` 로 든다), `index` 는 기록과 다른
 *   색인 목록이다. `tokensMixed` 는 웹의 `tokens.json` 이 `pending` 의 목표와도 기준본과도 달라, 멈춘 올리기가 보낸
 *   값이 `tokens` 에 섞일 수 있다는 표시다.
 * - `importing`(들이는 중). 기록에 들이기의 `claim` 이 있다. `claim` 은 그 브랜치, 티켓 경로, 시각, 지금 브랜치의
 *   것인지(`own`), 든 파일이다. `further` 는 더 고친 몫으로 `edited` 의 넷과 같은 꼴이다. `inherit` 은 확인이 쓴
 *   이어받을 기준본 파일의 절대 경로이고 쓰지 않았으면 null 이다.
 * - `beforeRecord`(기록 전). 편집이 꺼진 색인에 기록도 `tokens.json` 도 없다.
 * - `undecidable`(판단할 수 없음). `reason` 이 까닭, `message` 가 문구, `paths` 가 걸린 경로다.
 */

import type { ReportFields } from "./command.ts";
import { TOKENS_PATH } from "./file-hash.ts";
import { inputError, isArtifactPath, isRecord, readJson, stringList, unknownList } from "./io.ts";
import {
  INDEX_KEYS,
  isPendingClass,
  type IndexKey,
  type PendingClass,
  type PendingState,
} from "./sync-record.ts";
import type { JsonValue, TokenDiff } from "./tokens-json.ts";

export type RecordStatus = "ok" | "absent" | "unreadable" | "unknownVersion" | "malformed";

/** 기록에서 온 판단할 수 없음의 까닭. 올리기는 기록을 새로 쓸 수 있다. */
export const RECORD_REASONS = [
  "noRecord",
  "recordUnreadable",
  "unknownVersion",
  "recordMalformed",
  "noBaseline",
] as const;

/** 아티팩트를 읽지 못해 난 판단할 수 없음의 까닭. 올리기는 멈춘다. */
export const READ_REASONS = [
  "readFailed",
  "noIndex",
  "indexUnreadable",
  "tokensUnreadable",
] as const;

export type UndecidableReason = (typeof RECORD_REASONS)[number] | (typeof READ_REASONS)[number];

export const FILE_CHANGES = ["changed", "added", "removed"] as const;

export type FileChange = (typeof FILE_CHANGES)[number];

export type FileEdit = { readonly path: string; readonly change: FileChange };

export type IndexEdit = {
  readonly key: IndexKey;
  readonly before: JsonValue;
  readonly after: JsonValue;
};

/** `pending` 의 경로마다의 분류. */
export type PendingReport = Readonly<Record<string, PendingClass>>;

/** 웹 편집의 넷. 웹 편집 있음의 결과와 들이는 중의 더 고친 몫이 같은 꼴이다. */
export interface EditLists {
  readonly tokens: readonly TokenDiff[];
  readonly tokensMixed: boolean;
  readonly files: readonly FileEdit[];
  readonly index: readonly IndexEdit[];
}

/** 들이는 중의 `claim`. 파일 목록은 경로 차례다. */
export interface ClaimSummary {
  readonly branch: string;
  readonly ticket: string;
  readonly at: string;
  /** `claim` 의 브랜치가 지금 브랜치와 같다. */
  readonly own: boolean;
  /** 웹이 고친 파일. `claim` 이 웹의 `tokens.json` 사본을 들면 `tokens.json` 도 든다. */
  readonly changed: readonly string[];
  /** 웹에서 더한 경로. */
  readonly added: readonly string[];
  /** 웹에서 지운 경로. */
  readonly removed: readonly string[];
}

export type CheckReport =
  | {
      readonly result: "clean";
      readonly editing: "on" | "off";
      readonly record: RecordStatus;
      readonly pending: PendingReport | null;
    }
  | ({ readonly result: "edited"; readonly pending: PendingReport | null } & EditLists)
  | {
      readonly result: "importing";
      readonly claim: ClaimSummary;
      readonly further: EditLists;
      readonly pending: PendingReport | null;
      readonly inherit: string | null;
    }
  | { readonly result: "beforeRecord"; readonly editing: "off" }
  | {
      readonly result: "undecidable";
      readonly reason: UndecidableReason;
      readonly message: string;
      readonly paths: readonly string[];
    };

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

function editsJson(edits: EditLists): JsonValue {
  return {
    tokens: edits.tokens.map(diffJson),
    tokensMixed: edits.tokensMixed,
    files: edits.files.map((edit) => ({ ...edit })),
    index: edits.index.map((edit) => ({ ...edit })),
  };
}

/** 확인 결과의 보고 칸. */
export function reportFields(report: CheckReport): ReportFields {
  switch (report.result) {
    case "edited":
      return { ...report, tokens: report.tokens.map(diffJson) };
    case "importing":
      return {
        ...report,
        claim: { ...report.claim },
        further: editsJson(report.further),
      };
    default:
      return report;
  }
}

/**
 * 보고에서 다시 읽은 웹 편집. 고친 것(`revert`)은 되돌리고, 지운 것(`webRemoved`)은 되살리고, 더한 것(`webAdded`)은
 * 지운다. 토큰 차이가 있으면 `tokens.json` 도 되돌린다. `tokens` 는 토큰 차이의 수, `index` 는 바뀐 색인 목록의 키다.
 */
export interface WebEdits {
  readonly revert: readonly string[];
  readonly webRemoved: readonly string[];
  readonly webAdded: readonly string[];
  readonly tokens: number;
  readonly index: readonly string[];
}

export const NO_EDITS: WebEdits = {
  revert: [],
  webRemoved: [],
  webAdded: [],
  tokens: 0,
  index: [],
};

/** 웹 편집이 하나도 없는가. */
export function isEmpty(edits: WebEdits): boolean {
  return (
    edits.revert.length === 0 &&
    edits.webRemoved.length === 0 &&
    edits.webAdded.length === 0 &&
    edits.index.length === 0
  );
}

/** 다시 읽은 확인 보고. */
export type CheckReading =
  | { readonly result: "clean" | "beforeRecord"; readonly pending: PendingState | null }
  | { readonly result: "edited"; readonly pending: PendingState | null; readonly edits: WebEdits }
  | {
      readonly result: "importing";
      readonly pending: PendingState | null;
      readonly claim: ClaimSummary;
      readonly further: WebEdits;
      readonly inherit: string | null;
    }
  | {
      readonly result: "undecidable";
      readonly reason: UndecidableReason;
      readonly message: string;
    };

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

/** 웹 편집의 넷(`files`, `tokens`, `index`)을 읽는다. `where` 는 문구에 쓰는 자리다. */
function editsOf(path: string, raw: Readonly<Record<string, unknown>>, where: string): WebEdits {
  const files = unknownList(raw.files);
  if (files === undefined) {
    throw inputError(path, `${where}files 로 바뀐 파일의 배열을 들지 않는다`);
  }
  const tokens = unknownList(raw.tokens);
  if (tokens === undefined) {
    throw inputError(path, `${where}tokens 로 토큰 차이의 배열을 들지 않는다`);
  }
  const index = unknownList(raw.index);
  const keys = index?.map((item) => (isRecord(item) ? item.key : undefined));
  if (keys === undefined || !keys.every((key) => INDEX_KEYS.some((known) => known === key))) {
    throw inputError(path, `${where}index 로 바뀐 색인 목록의 배열을 들지 않는다`);
  }
  const lists: Record<FileChange, string[]> = { changed: [], added: [], removed: [] };
  for (const item of files) {
    const editPath = isRecord(item) ? item.path : undefined;
    const change = isRecord(item) ? item.change : undefined;
    if (typeof editPath !== "string" || !isArtifactPath(editPath)) {
      throw inputError(path, `${where}files 의 항목이 project/ 아래 경로를 들지 않는다`);
    }
    const known = FILE_CHANGES.find((name) => name === change);
    if (known === undefined) {
      throw inputError(
        path,
        `${where}files 의 ${editPath} 가 모르는 바뀜 ${JSON.stringify(change)} 을 든다`,
      );
    }
    lists[known].push(editPath);
  }
  if (tokens.length > 0 && !lists.changed.includes(TOKENS_PATH)) {
    lists.changed.push(TOKENS_PATH);
  }
  return {
    revert: lists.changed,
    webRemoved: lists.removed,
    webAdded: lists.added,
    tokens: tokens.length,
    index: keys.map(String),
  };
}

function pathsOf(path: string, value: unknown, where: string): string[] {
  const paths = stringList(value);
  if (paths === undefined || !paths.every(isArtifactPath)) {
    throw inputError(path, `${where} 로 project/ 아래 경로의 배열을 들지 않는다`);
  }
  return paths;
}

function claimOf(path: string, value: unknown): ClaimSummary {
  if (!isRecord(value)) {
    throw inputError(path, "claim 으로 들이는 중의 claim 을 들지 않는다");
  }
  const { branch, ticket, at, own } = value;
  if (
    typeof branch !== "string" ||
    typeof ticket !== "string" ||
    typeof at !== "string" ||
    typeof own !== "boolean"
  ) {
    throw inputError(path, "claim 이 branch, ticket, at, own 을 들지 않는다");
  }
  return {
    branch,
    ticket,
    at,
    own,
    changed: pathsOf(path, value.changed, "claim.changed"),
    added: pathsOf(path, value.added, "claim.added"),
    removed: pathsOf(path, value.removed, "claim.removed"),
  };
}

function reasonOf(path: string, value: unknown): UndecidableReason {
  const reason = [...RECORD_REASONS, ...READ_REASONS].find((known) => known === value);
  if (reason === undefined) {
    throw inputError(path, `모르는 판단할 수 없음의 까닭 ${JSON.stringify(value)} 을 든다`);
  }
  return reason;
}

/** `check judge` 의 성공 보고를 읽는다. 아니면 `input` 오류다. */
export function readCheckReport(path: string): CheckReading {
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
      return { result, pending: pendingOf(path, raw.pending), edits: editsOf(path, raw, "") };
    case "importing": {
      const further = isRecord(raw.further) ? raw.further : undefined;
      if (further === undefined) {
        throw inputError(path, "further 로 더 고친 몫을 들지 않는다");
      }
      const inherit = raw.inherit ?? null;
      if (inherit !== null && typeof inherit !== "string") {
        throw inputError(path, "inherit 으로 파일 경로나 null 을 들지 않는다");
      }
      return {
        result,
        pending: pendingOf(path, raw.pending),
        claim: claimOf(path, raw.claim),
        further: editsOf(path, further, "further."),
        inherit,
      };
    }
    case "undecidable":
      return {
        result,
        reason: reasonOf(path, raw.reason),
        message: typeof raw.message === "string" ? raw.message : "",
      };
    default:
      throw inputError(path, `모르는 확인 결과 ${JSON.stringify(result)} 를 든다`);
  }
}
