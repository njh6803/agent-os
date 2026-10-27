/**
 * 이번 올리기가 보낼 파일·지울 경로와 빌드가 필요한지(design-reverse-sync 명세 "올리기"의 빌드가 필요한 올리기·필요
 * 없는 올리기·첫 올리기와 그 2026-10-22 주석, "찾았을 때"의 "덮어쓴다"). 기록 명령이 이 함수로 계획을 내고, 그
 * 계획이 다음 기록(`sync-record.ts` 의 `nextRecord`)의 입력이 된다.
 *
 * 보낼 파일은 맞대는 값(`file-hash.ts`)이 기록과 다른 이번 산출의 파일과, 사람이 "덮어쓴다"를 고른 확인이 찾은
 * 되돌릴 파일이다. 기록이 없으면(첫 올리기, 편집이 꺼진 동안 기록을 잃은 때) 아티팩트에서 받은 sha256 과 원 바이트로
 * 맞댄다. 지울 경로는 지난 산출에 있었고 이번 산출에 없는 경로와 웹에서 더한 경로다. 지난 산출의 목록은 빌드 산출
 * 전체를 맞춘 올리기만 넘긴다. 몇 파일만 보내는 올리기의 산출에는 빌드 산출이 없어, 그 목록과 맞대면 다 지운다.
 *
 * 앞 기록에 `pending` 이 있으면(멈춘 올리기를 다시 하는 올리기) 확인이 그 경로마다 낸 분류를 받는다. 목표대로 이미
 * 보낸 파일은 로컬이 목표와 같으면 다시 보내지 않고(`landed`), 이미 지워진 경로는 기록에서만 뺀다(`gone`). 이번
 * 산출에 없는 보낸 목표는 몇 파일만 보내는 올리기면 코드에 남았을 수 있어 목표대로 이어 적고, 빌드 산출 전체를 맞춘
 * 올리기면 코드가 뺀 것이라 지운다.
 *
 * 덮어쓰기의 되돌릴 파일(웹이 고친 것)과 웹이 지운 파일은 이번 산출에 있으면 보낸다. 이번 산출에 없으면 코드가 뺀
 * 경로로 알려진 것(지난 산출 목록이나 `pending` 의 지울 경로에 든 것)만 받아, 고친 것은 지우고 지운 것은 기록에서만
 * 뺀다. 그 밖은 몇 파일만 보내는 산출이 빠뜨린 것인지 가를 수 없어 `input` 오류다.
 */

import { CommandError } from "./command.ts";
import { fileHash, isRecorded, RECORD_PATH, TOKENS_PATH } from "./file-hash.ts";
import { sha256, sortedPaths } from "./io.ts";
import type { PendingState, RecordChanges, SyncRecord } from "./sync-record.ts";

export interface UploadInput {
  readonly record: SyncRecord | null;
  /** 기록이 없을 때 맞댈 아티팩트의 파일마다의 sha256(원 바이트). */
  readonly artifactSha256: ReadonlyMap<string, string> | null;
  /** 이번 산출의 로컬 파일. 아티팩트 경로로 찾는다. */
  readonly output: ReadonlyMap<string, Uint8Array>;
  /** 지난 산출의 경로 목록. 빌드 산출 전체를 맞춘 올리기만 넘기고, 몇 파일만 보내는 올리기는 null 이다. */
  readonly previousOutput: readonly string[] | null;
  /** 코드의 판으로 되돌릴 파일(웹이 고친 것). */
  readonly revert: readonly string[];
  /** 웹에서 지운 경로. 덮어쓰기가 이번 산출의 판으로 되살린다. */
  readonly webRemoved: readonly string[];
  /** 웹에서 더한 경로. 덮어쓰기가 지운다. */
  readonly webAdded: readonly string[];
  readonly pendingState: PendingState | null;
}

export interface UploadPlan extends RecordChanges {
  /** 이번 산출에 있지만 기록에 들지 않아 이 계획이 다루지 않는 경로(기록, 색인, 페이지가 다시 짓는 파일). */
  readonly ignored: readonly string[];
}

function checkedState(record: SyncRecord | null, given: PendingState | null): PendingState {
  const pending = record?.pending ?? null;
  if (pending === null) {
    return new Map();
  }
  if (given === null) {
    throw new CommandError(
      "usage",
      "앞 기록에 pending 이 있어 확인이 낸 pending 의 분류가 있어야 한다",
    );
  }
  const missing = [...pending.files.keys(), ...pending.delete].filter((path) => !given.has(path));
  if (missing.length > 0) {
    throw new CommandError("input", `확인의 pending 분류에 ${missing.join(", ")} 가 없다`);
  }
  return given;
}

/** 되돌리거나 되살릴 경로. 이번 산출에 없으면 코드가 뺀 경로로 알려진 것만 받고, 아니면 `input` 오류다. */
function checkedReverts(input: UploadInput): Set<string> {
  const pendingDelete = input.record?.pending?.delete ?? [];
  const leftByCode = new Set([...(input.previousOutput ?? []), ...pendingDelete]);
  const revert = new Set([...input.revert, ...input.webRemoved]);
  const stray = [...revert].filter((path) => !input.output.has(path) && !leftByCode.has(path));
  if (stray.length > 0) {
    throw new CommandError(
      "input",
      `되돌릴 ${sortedPaths(stray).join(", ")} 가 이번 산출에 없고 지난 산출 목록과 pending 의 지울 경로에도 없다`,
    );
  }
  return revert;
}

/**
 * 이번 올리기가 보낼 파일과 지울 경로. 확인이 웹 편집(`edited`)이나 들이는 `claim` 의 것(`claimed`)으로 가른 `pending`
 * 파일은 웹의 값이 코드와 다를 수 있어 늘 보낸다.
 */
export function planUpload(input: UploadInput): UploadPlan {
  const { record, output, artifactSha256 } = input;
  const state = checkedState(record, input.pendingState);
  if (record === null && artifactSha256 === null) {
    throw new CommandError("usage", "기록이 없으면 아티팩트에서 받은 sha256 으로 맞대야 한다");
  }
  const pendingDelete = record?.pending?.delete ?? [];
  const revert = checkedReverts(input);

  const unchangedOnWeb = (path: string, data: Uint8Array): boolean => {
    if (record === null) {
      return artifactSha256?.get(path) === sha256(data);
    }
    const before = record.files.get(path);
    return before !== undefined && before.hash === fileHash(path, data);
  };

  const send: string[] = [];
  const landed: string[] = [];
  const unchanged: string[] = [];
  const ignored: string[] = [];
  const droppedTargets: string[] = [];
  for (const [path, data] of output) {
    if (!isRecorded(path)) {
      ignored.push(path);
      continue;
    }
    const kind = state.get(path);
    if (revert.has(path) || kind === "edited" || kind === "claimed" || kind === "deleted") {
      send.push(path);
    } else if (kind === "sent") {
      const target = record?.pending?.files.get(path);
      (target !== undefined && target.hash === fileHash(path, data) ? landed : send).push(path);
    } else {
      (unchangedOnWeb(path, data) ? unchanged : send).push(path);
    }
  }
  for (const path of record?.pending?.files.keys() ?? []) {
    if (!output.has(path) && state.get(path) === "sent") {
      // 빌드 산출 전체를 맞춘 산출에 없으면 코드가 뺀 것이라 지운다. 이어 적으면 마지막 기록이 지운 경로를 되살린다
      (input.previousOutput === null ? landed : droppedTargets).push(path);
    }
  }

  // 웹에 이미 없는 경로는 지우는 요청 없이 기록에서만 뺀다
  const gone = [
    ...pendingDelete.filter((path) => state.get(path) === "deleted"),
    ...input.webRemoved,
  ].filter((path) => !output.has(path));
  const deletes = [...(input.previousOutput ?? []), ...input.webAdded, ...pendingDelete].filter(
    (path) => isRecorded(path) && !output.has(path) && !gone.includes(path),
  );

  return {
    send: sortedPaths(send),
    landed: sortedPaths(landed),
    unchanged: sortedPaths(unchanged),
    delete: sortedPaths([...deletes, ...droppedTargets]),
    gone: sortedPaths(gone),
    ignored: sortedPaths(ignored),
  };
}

/** 빌드가 필요한 까닭. 패키지 아래, 빌린 빌드의 설정, 빌드가 짓는 되돌릴 파일이다. */
export type BuildReason = "package" | "buildConfig" | "revert";

export interface BuildNeed {
  readonly needed: boolean;
  readonly because: readonly { readonly path: string; readonly reason: BuildReason }[];
}

const PACKAGE = "web/packages/ui/";
const BUILD_CONFIG = ".design-sync/";
/** 빌린 빌드의 설정 폴더 가운데 빌드를 다시 하지 않아도 되는 것. 기초 카드 원본과 사람의 노트다. */
const NOT_BUILD_CONFIG = [".design-sync/foundations/", ".design-sync/NOTES.md"];
/** 빌드 없이 보내는 아티팩트 경로. 빌드가 저장소 원본을 그대로 옮기는 다섯(기초 카드 넷과 지침 문서)이다. */
const COPIED = ["project/foundations/", "project/guidelines/web-design.md"];

function startsWithAny(path: string, prefixes: readonly string[]): boolean {
  return prefixes.some(
    (prefix) => path === prefix || (prefix.endsWith("/") && path.startsWith(prefix)),
  );
}

/**
 * 빌드가 필요한지. `changed` 는 기록의 커밋 뒤에 바뀐 저장소 경로(`git -c core.quotePath=false diff --name-only`),
 * `revert` 는 코드의 판으로 되돌리거나 되살릴 아티팩트 경로(웹이 고치거나 지운 것)다. `tokens.json`, 기록, 그대로
 * 옮기는 다섯만 바뀌거나 되돌리면 빌드가 필요 없다.
 */
export function needsBuild(changed: readonly string[], revert: readonly string[]): BuildNeed {
  const because: { path: string; reason: BuildReason }[] = [];
  for (const path of changed) {
    if (path.startsWith(PACKAGE)) {
      because.push({ path, reason: "package" });
    } else if (path.startsWith(BUILD_CONFIG) && !startsWithAny(path, NOT_BUILD_CONFIG)) {
      because.push({ path, reason: "buildConfig" });
    }
  }
  for (const path of revert) {
    if (path !== TOKENS_PATH && path !== RECORD_PATH && !startsWithAny(path, COPIED)) {
      because.push({ path, reason: "revert" });
    }
  }
  return { needed: because.length > 0, because };
}
