/**
 * 아티팩트의 기록(`project/sync-record.json`)의 꼴과 다음 기록 짓기(design-reverse-sync 명세 "기록"과 그 2026-10-22
 * 주석 둘). 기록은 마지막으로 올린 것을 적어, 확인이 웹 편집을 가르고 올리기가 바뀐 파일만 보내게 한다.
 *
 * 꼴 판 1 의 칸은 넷의 묶음이다.
 *
 * - `v`(1), 올린 main 커밋 `commit` 과 시각 `at`. 앞 기록이 없는 첫 올리기가 첫 호출에서 멈추면 둘 다 null 이다.
 * - `files`: `project/` 아래 파일마다의 맞대는 값(`hash`, `file-hash.ts`)과 바이트 수(`bytes`). 경로 차례로 적는다.
 *   기록 자신, 색인, 페이지가 다시 짓는 파일은 들지 않는다(`isRecorded`).
 * - `baseline`: 기준본. 마지막으로 올린 `tokens.json` 의 내용(푼 JSON 값)이다. `index`: 올린 뒤 색인의 그림과 문서
 *   목록(`assetGroups`, `blobs`, `docs`, `sections`. 색인에 없는 칸은 null). 페이지가 저장할 때 색인을 다시 계산하므로
 *   해시하지 않고 목록만 적는다.
 * - `pending`: 여러 호출로 나뉜 올리기의 첫 호출이 적는 목표. 이번에 보낼 파일의 목표(`files`), 지울 경로(`delete`),
 *   색인 목록의 목표(`index`)다. 마지막 호출이 비운다(null). `claim`: 들이기가 쓰는 겹침 표지(06). 이 모듈은 받은
 *   그대로 지킨다.
 *
 * 기록은 들여쓰기 없는 JSON 으로 쓰고, 512,000 바이트를 넘으면 쓰지 않고 `limit` 오류다. 형식 설명이 표 밖 파일마다
 * "≤512 KB" 라고 적고 KB 의 단위를 밝히지 않아 작은 쪽으로 본다(티켓 05).
 */

import { CommandError } from "./command.ts";
import { fileHash, isRecorded, parseJson, TOKENS_PATH } from "./file-hash.ts";
import { byPath, isArtifactPath, isRecord, jsonValue, sortedPaths, stringList } from "./io.ts";
import type { JsonValue } from "./tokens-json.ts";

export const RECORD_VERSION = 1;

/** 기록의 한도(바이트). */
export const RECORD_LIMIT = 512_000;

export interface FileEntry {
  readonly hash: string;
  readonly bytes: number;
}

export const INDEX_KEYS = ["assetGroups", "blobs", "docs", "sections"] as const;

export type IndexKey = (typeof INDEX_KEYS)[number];

/** 색인의 그림과 문서 목록. 색인에 없는 칸은 null 이다. */
export type IndexLists = Readonly<Record<IndexKey, JsonValue>>;

export interface Pending {
  readonly files: ReadonlyMap<string, FileEntry>;
  readonly delete: readonly string[];
  readonly index: IndexLists;
}

export interface SyncRecord {
  readonly v: 1;
  readonly commit: string | null;
  readonly at: string | null;
  readonly files: ReadonlyMap<string, FileEntry>;
  readonly baseline: JsonValue | null;
  readonly index: IndexLists | null;
  readonly pending: Pending | null;
  readonly claim: JsonValue | null;
}

/** 기록 읽기의 결과. */
export type RecordRead =
  | { readonly kind: "ok"; readonly record: SyncRecord }
  | { readonly kind: "unreadable" }
  | { readonly kind: "unknownVersion"; readonly version: JsonValue }
  | { readonly kind: "malformed"; readonly message: string };

/** 색인(푼 JSON)의 그림과 문서 목록. */
export function indexLists(index: unknown): IndexLists {
  const source = isRecord(index) ? index : {};
  const pick = (key: IndexKey): JsonValue =>
    Object.hasOwn(source, key) ? (jsonValue(source[key]) ?? null) : null;
  return {
    assetGroups: pick("assetGroups"),
    blobs: pick("blobs"),
    docs: pick("docs"),
    sections: pick("sections"),
  };
}

const HASH = /^[0-9a-f]{64}$/;

/** 꼴이 어긋났을 때 그 까닭. */
class Malformed extends Error {}

function fileEntries(value: unknown, where: string): Map<string, FileEntry> {
  if (!isRecord(value)) {
    throw new Malformed(`${where} 가 객체가 아니다`);
  }
  const entries = new Map<string, FileEntry>();
  for (const [path, raw] of Object.entries(value)) {
    if (!isArtifactPath(path)) {
      throw new Malformed(`${where} 의 ${JSON.stringify(path)} 가 project/ 아래 경로가 아니다`);
    }
    const hash = isRecord(raw) ? raw.hash : undefined;
    const bytes = isRecord(raw) ? raw.bytes : undefined;
    if (
      typeof hash !== "string" ||
      !HASH.test(hash) ||
      typeof bytes !== "number" ||
      !Number.isSafeInteger(bytes) ||
      bytes < 0
    ) {
      throw new Malformed(
        `${where} 의 ${path} 가 hash(16 진수 64 자)와 bytes(0 이상의 정수)를 들지 않는다`,
      );
    }
    entries.set(path, { hash, bytes });
  }
  return entries;
}

function nullableText(value: unknown, where: string): string | null {
  if (value === null || typeof value === "string") {
    return value;
  }
  throw new Malformed(`${where} 가 문자열이나 null 이 아니다`);
}

function storedIndex(value: unknown, where: string): IndexLists {
  if (!isRecord(value)) {
    throw new Malformed(`${where} 가 객체가 아니다`);
  }
  return indexLists(value);
}

function storedPending(value: unknown): Pending | null {
  if (value === null) {
    return null;
  }
  if (!isRecord(value)) {
    throw new Malformed("pending 이 객체나 null 이 아니다");
  }
  const deletes = stringList(value.delete);
  if (deletes === undefined || !deletes.every(isArtifactPath)) {
    throw new Malformed("pending.delete 가 project/ 아래 경로의 배열이 아니다");
  }
  return {
    files: fileEntries(value.files, "pending.files"),
    delete: deletes,
    index: storedIndex(value.index, "pending.index"),
  };
}

function storedJson(value: unknown, where: string): JsonValue {
  const converted = jsonValue(value);
  if (converted === undefined) {
    throw new Malformed(`${where} 가 JSON 값이 아니다`);
  }
  return converted;
}

/** 기록의 글을 읽는다. */
export function readRecord(text: string): RecordRead {
  const parsed = parseJson(text);
  if (parsed === undefined) {
    return { kind: "unreadable" };
  }
  const version = isRecord(parsed) && Object.hasOwn(parsed, "v") ? parsed.v : null;
  if (!isRecord(parsed) || version !== RECORD_VERSION) {
    return { kind: "unknownVersion", version: jsonValue(version) ?? null };
  }
  try {
    const index = parsed.index ?? null;
    return {
      kind: "ok",
      record: {
        v: RECORD_VERSION,
        commit: nullableText(parsed.commit ?? null, "commit"),
        at: nullableText(parsed.at ?? null, "at"),
        files: fileEntries(parsed.files, "files"),
        baseline: storedJson(parsed.baseline ?? null, "baseline"),
        index: index === null ? null : storedIndex(index, "index"),
        pending: storedPending(parsed.pending ?? null),
        claim: storedJson(parsed.claim ?? null, "claim"),
      },
    };
  } catch (error) {
    if (error instanceof Malformed) {
      return { kind: "malformed", message: error.message };
    }
    throw error;
  }
}

function entriesJson(entries: ReadonlyMap<string, FileEntry>): JsonValue {
  return Object.fromEntries(
    [...entries]
      .sort(([left], [right]) => byPath(left, right))
      .map(([path, entry]) => [path, { hash: entry.hash, bytes: entry.bytes }]),
  );
}

function recordJson(record: SyncRecord): JsonValue {
  const { pending } = record;
  return {
    v: record.v,
    commit: record.commit,
    at: record.at,
    files: entriesJson(record.files),
    baseline: record.baseline,
    index: record.index,
    pending:
      pending === null
        ? null
        : { files: entriesJson(pending.files), delete: [...pending.delete], index: pending.index },
    claim: record.claim,
  };
}

/** 기록의 글. 들여쓰기 없는 JSON 이다. 한도를 넘으면 `limit` 오류다. */
export function serializeRecord(record: SyncRecord): string {
  const text = JSON.stringify(recordJson(record));
  const size = new TextEncoder().encode(text).byteLength;
  if (size > RECORD_LIMIT) {
    throw new CommandError(
      "limit",
      `기록이 ${String(size)} 바이트로 한도 ${String(RECORD_LIMIT)} 바이트를 넘어 쓰지 않는다`,
    );
  }
  return text;
}

/**
 * 이번 올리기가 아티팩트에 하는 일. 경로는 아티팩트 경로다.
 *
 * - `send`: 보내는 파일. `unchanged`: 보내지 않는 이번 산출의 파일(웹이 이미 같다).
 * - `landed`: 멈춘 올리기가 이미 목표대로 보내 다시 보내지 않는 파일. 이번 산출에 있으면 로컬 값, 없으면 앞 기록의
 *   `pending` 목표로 적는다.
 * - `delete`: 지우는 경로. `gone`: 멈춘 올리기가 이미 지워 기록에서만 빼는 경로.
 */
export interface RecordChanges {
  readonly send: readonly string[];
  readonly landed: readonly string[];
  readonly unchanged: readonly string[];
  readonly delete: readonly string[];
  readonly gone: readonly string[];
}

/** 여러 호출의 첫 호출, 또는 마지막 호출(한 호출로 끝나는 올리기 포함)과 그 커밋·시각. */
export type RecordCall =
  | { readonly kind: "first" }
  | { readonly kind: "last"; readonly commit: string; readonly at: string };

export interface NextRecordInput {
  readonly previous: SyncRecord | null;
  /** 이번 산출의 로컬 파일. 아티팩트 경로로 찾는다. */
  readonly output: ReadonlyMap<string, Uint8Array>;
  /** 첫 올리기가 아티팩트에서 읽은 파일(빌드 산출에 없는 것). 마지막 기록에 그대로 해시해 넣는다. */
  readonly artifact: ReadonlyMap<string, Uint8Array>;
  readonly changes: RecordChanges;
  /** 이번 올리기가 보내는 색인의 그림과 문서 목록. */
  readonly index: IndexLists;
  readonly call: RecordCall;
}

function entryOf(path: string, data: Uint8Array): FileEntry {
  return { hash: fileHash(path, data), bytes: data.byteLength };
}

function sortedEntries(entries: ReadonlyMap<string, FileEntry>): Map<string, FileEntry> {
  return new Map([...entries].sort(([left], [right]) => byPath(left, right)));
}

/** 이번 산출의 tokens.json 내용. 없으면 undefined 이고, JSON 으로 풀리지 않으면 `input` 오류다. */
function outputBaseline(output: ReadonlyMap<string, Uint8Array>): JsonValue | undefined {
  const data = output.get(TOKENS_PATH);
  if (data === undefined) {
    return undefined;
  }
  const parsed = jsonValue(parseJson(new TextDecoder().decode(data)));
  if (parsed === undefined) {
    throw new CommandError("input", `이번 산출의 ${TOKENS_PATH} 가 JSON 으로 풀리지 않는다`);
  }
  return parsed;
}

/**
 * 다음 기록. 첫 호출은 앞 기록에 이번 목표를 `pending` 으로 얹고, 마지막 호출은 앞 기록에 이번에 보낸 것과 지운 것을
 * 합치고 `pending` 을 비운다. `claim` 은 앞 기록의 것을 그대로 지킨다. 보낼 파일이 이번 산출에 없거나, 마지막 기록에
 * 기준본이 없으면 `input` 오류다.
 */
export function nextRecord(input: NextRecordInput): SyncRecord {
  const { previous, output, changes, call } = input;
  const entry = (path: string): FileEntry => {
    const data = output.get(path);
    if (data !== undefined) {
      return entryOf(path, data);
    }
    const target = previous?.pending?.files.get(path);
    if (target !== undefined && changes.landed.includes(path)) {
      return target;
    }
    throw new CommandError("input", `기록에 적을 ${path} 가 이번 산출에 없다`);
  };
  const claim = previous?.claim ?? null;

  if (call.kind === "first") {
    const targets = sortedPaths([...changes.send, ...changes.landed]).filter(isRecorded);
    return {
      v: RECORD_VERSION,
      commit: previous?.commit ?? null,
      at: previous?.at ?? null,
      files: previous?.files ?? new Map(),
      baseline: previous?.baseline ?? null,
      index: previous?.index ?? null,
      pending: {
        files: new Map(targets.map((path) => [path, entry(path)])),
        // 이미 지워진 경로도 이어 적어야, 이 호출에서 다시 멈췄을 때 확인이 그 경로를 웹 편집이 아니라 지운 것으로 본다
        delete: sortedPaths([...changes.delete, ...changes.gone]),
        index: input.index,
      },
      claim,
    };
  }

  const files = new Map(previous?.files ?? []);
  for (const [path, data] of input.artifact) {
    if (isRecorded(path)) {
      files.set(path, entryOf(path, data));
    }
  }
  for (const path of [...changes.delete, ...changes.gone]) {
    files.delete(path);
  }
  for (const path of [...changes.send, ...changes.landed, ...changes.unchanged]) {
    if (isRecorded(path)) {
      files.set(path, entry(path));
    }
  }
  const baseline = outputBaseline(output) ?? previous?.baseline ?? null;
  if (baseline === null) {
    throw new CommandError(
      "input",
      `기준본이 없다: 이번 산출에 ${TOKENS_PATH} 가 없고 앞 기록에도 없다`,
    );
  }
  return {
    v: RECORD_VERSION,
    commit: call.commit,
    at: call.at,
    files: sortedEntries(files),
    baseline,
    index: input.index,
    pending: null,
    claim,
  };
}
