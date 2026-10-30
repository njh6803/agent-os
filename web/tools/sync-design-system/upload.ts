/**
 * 이번 올리기가 보낼 파일·지울 경로(design-reverse-sync 명세 "올리기"의 첫 올리기와 그 2026-10-22 주석, "찾았을 때"의
 * "덮어쓴다", design-card-build 명세 "올리기"). 기록 명령이 이 함수로 계획을 내고, 그 계획이 다음 기록
 * (`sync-record.ts` 의 `nextRecord`)의 입력이 된다.
 *
 * 보낼 파일은 맞대는 값(`file-hash.ts`)이 기록과 다른 이번 산출의 파일과, 사람이 "덮어쓴다"를 고른 확인이 찾은
 * 되돌릴 파일이다. 기록이 없으면(첫 올리기, 편집이 꺼진 동안 기록을 잃은 때) 아티팩트에서 받은 sha256 과 원 바이트로
 * 맞댄다. 지울 경로는 지난 산출에 있었고 이번 산출에 없는 경로와 웹에서 더한 경로다.
 *
 * 지난 산출 목록(이 폴더의 `previous-output.json`)은 마지막으로 다 보낸 올리기의 산출 경로(`project/…`) 전부이고,
 * 바뀌지 않아 보내지 않은 것도 든다. 올리기는 늘 짓기 명령의 산출 전체로 계획하며 이 목록을 주고, 다 보낸 뒤 그
 * 올리기에서 짓기 명령의 `--paths` 가 쓴 목록으로 바꿔 커밋한다(절차 `.claude/skills/sync-design-system/upload.md`).
 * 그 커밋이 병합되기 전에 다른 올리기가 돌면 옛 목록을 주어, 그사이 산출에만 있던 경로가 지워지지 않고 남을 뿐이다.
 * 짓기 명령이 짓지 않는 파일(옮기기가 더한 `migration-map.json`·`assets/notes/`, 화면이 만드는 `manifest.json`, 단독
 * 앱이 만든 `_ds_manifest.json`, 옛 고정폭 글꼴 28 개)은 목록에 없어 계획이 지우지 않는다. 목록을 주지 않은 계획
 * (`previousOutput` 이 null)은 산출이 전체가 아닐 수 있다고 보아 지난 산출에만 있던 경로를 지우지 않는다.
 *
 * 앞 기록에 `pending` 이 있으면(멈춘 올리기를 다시 하는 올리기) 확인이 그 경로마다 낸 분류를 받는다. 목표대로 이미
 * 보낸 파일은 로컬이 목표와 같으면 다시 보내지 않고(`landed`), 이미 지워진 경로는 기록에서만 뺀다(`gone`). 이번
 * 산출에 없는 보낸 목표는 목록을 주지 않은 계획이면 코드에 남았을 수 있어 목표대로 이어 적고, 목록을 준 계획이면
 * 코드가 뺀 것이라 지운다.
 *
 * 덮어쓰기의 되돌릴 파일(웹이 고친 것)과 웹이 지운 파일은 이번 산출에 있으면 보낸다. 이번 산출에 없으면 코드가 뺀
 * 경로로 알려진 것(지난 산출 목록이나 `pending` 의 지울 경로에 든 것)만 받아, 고친 것은 지우고 지운 것은 기록에서만
 * 뺀다. 그 밖은 산출이 빠뜨린 것인지 가를 수 없어 `input` 오류다.
 *
 * 짓기 명령의 정식 배치로 옮기는 올리기(design-card-build 명세 "올리기"의 "첫 정식 올리기와 `tokens.json`", "목록만
 * 옛것일 때", "나누기")도 여기서 가른다. 이번 산출에 정식 자리의 카드(`project/components/<이름>/preview.html`)가
 * 있고 받은 기록의 `files`(기록이 없으면 받은 sha256 목록)에 하나도 없으면 첫 정식 올리기다. 그때 `tokens.json` 은
 * 테마의 표시 이름만 바뀌어 지문이 같아도 보낸다. 기록의 `files` 는 마지막 호출이 받아들여질 때만 새 배치로
 * 바뀌므로, 끊긴 뒤 이어 받는 올리기도 같은 판정으로 다시 보내고 다 보낸 뒤의 올리기는 보내지 않는다. 정식 카드가
 * 없는 산출(짓기 명령 전의 배치)에서는 이 판정이 서지 않는다.
 *
 * 지난 산출 목록에서 온 지울 경로는 받은 기록의 `files` 에 든 것만 낸다. 다 보낸 뒤 목록을 커밋하기 전에 끊기면 그
 * 목록에는 마지막 호출이 이미 지워 기록에서 뺀 경로가 남는다. 기록이 없으면 목록대로 낸다.
 */

import { CommandError } from "./command.ts";
import { fileHash, isRecorded, TOKENS_PATH } from "./file-hash.ts";
import { sha256, sortedPaths } from "./io.ts";
import {
  RECORD_LIMIT,
  type PendingState,
  type RecordChanges,
  type SyncRecord,
} from "./sync-record.ts";

export interface UploadInput {
  readonly record: SyncRecord | null;
  /** 기록이 없을 때 맞댈 아티팩트의 파일마다의 sha256(원 바이트). */
  readonly artifactSha256: ReadonlyMap<string, string> | null;
  /** 이번 산출의 로컬 파일. 아티팩트 경로로 찾는다. */
  readonly output: ReadonlyMap<string, Uint8Array>;
  /** 지난 산출의 경로 목록. 절차는 늘 넘기고, null 이면 산출이 전체가 아닐 수 있는 계획으로 본다. */
  readonly previousOutput: readonly string[] | null;
  /** 코드의 판으로 되돌릴 파일(웹이 고친 것). */
  readonly revert: readonly string[];
  /** 웹에서 지운 경로. 덮어쓰기가 이번 산출의 판으로 되살린다. */
  readonly webRemoved: readonly string[];
  /** 웹에서 더한 경로. 덮어쓰기가 지운다. */
  readonly webAdded: readonly string[];
  readonly pendingState: PendingState | null;
}

/** 한 호출이 보낼 파일과 지울 경로. */
export interface UploadCall {
  readonly send: readonly string[];
  readonly delete: readonly string[];
}

export interface UploadPlan extends RecordChanges {
  /** 이번 산출에 있지만 기록에 들지 않아 이 계획이 다루지 않는 경로(기록, 색인, 페이지가 다시 짓는 파일). */
  readonly ignored: readonly string[];
  /** 첫 정식 올리기인가. 마지막 호출의 색인에 `upgraded` 를 더할지가 이것이다(`withUpgraded`). */
  readonly firstCanonical: boolean;
  /** 보낼 파일과 지울 경로를 호출마다 나눈 몫(`splitCalls`). */
  readonly calls: readonly UploadCall[];
}

/** 한 호출의 한도. 경로 255개와 16MiB 가운데 작은 쪽이다(Artifact 도구 설명과 형식 설명). */
export const CALL_PATHS = 255;
export const CALL_BYTES = 16 * 1024 * 1024;
/** 보낼 색인의 바이트 한도. 몫을 나눌 때 마지막 호출에 이만큼을 남기고, `record index` 가 넘으면 멈춘다. */
export const INDEX_LIMIT = 512_000;

const CANONICAL_CARD = /^project\/components\/[^/]+\/preview\.html$/;
export const BUNDLE_PATH = "project/components/bundle.js";

function hasCanonicalCard(paths: Iterable<string>): boolean {
  return [...paths].some((path) => CANONICAL_CARD.test(path));
}

interface CallItem {
  readonly path: string;
  readonly bytes: number;
  readonly kind: "send" | "delete";
}

function callOf(items: readonly CallItem[]): UploadCall {
  const paths = (kind: CallItem["kind"]): string[] =>
    sortedPaths(items.filter((item) => item.kind === kind).map((item) => item.path));
  return { send: paths("send"), delete: paths("delete") };
}

/**
 * 보낼 파일과 지울 경로를 호출 몫으로 나눈다(design-card-build 명세 "나누기", 절차 `upload.md` 의 6 의 4). 한 호출에
 * 들면 몫 하나가 기록과 색인을 함께 싣는다. 나누면 첫 호출이 `pending` 이 든 기록을, 마지막 호출이 기록과 색인을
 * 싣는다. 그 파일들도 경로로 세고, 바이트는 기록의 한도(`RECORD_LIMIT`)와 색인의 한도(`INDEX_LIMIT`)만큼 남긴다. 지울
 * 경로가 한도에 드는지는 재지 못해 경로 하나로 센다. 지울 경로는 뒤 몫으로 보낸다. 마지막 몫이 빌지
 * 않게 항목 하나를 남기되, 그 하나가 기록·색인과 함께 들지 않으면 따로 보내고 마지막 몫은 기록과 색인만 싣는다. 첫
 * 항목이 `pending` 이 든 기록과 함께 들지 않으면 첫 몫은 기록만 싣는다. 그래서 `limit` 오류는 기록도 색인도 싣지 않는
 * 호출에조차 들지 않는 파일에만 난다.
 *
 * 못 보는 것: 기록과 색인의 실제 크기는 보지 않고 한도만큼 남긴다.
 */
function splitCalls(send: readonly CallItem[], deletes: readonly CallItem[]): UploadCall[] {
  const items = [...send, ...deletes];
  const fits = (count: number, bytes: number, extraPaths: number, reserve: number): boolean =>
    count + extraPaths <= CALL_PATHS && bytes + reserve <= CALL_BYTES;
  const total = (part: readonly CallItem[]): number =>
    part.reduce((sum, item) => sum + item.bytes, 0);
  const lastFits = (part: readonly CallItem[]): boolean =>
    fits(part.length, total(part), 2, RECORD_LIMIT + INDEX_LIMIT);

  if (lastFits(items)) {
    return [callOf(items)];
  }
  const calls: UploadCall[] = [];
  let rest = items;
  for (;;) {
    if (calls.length > 0 && lastFits(rest)) {
      calls.push(callOf(rest));
      return calls;
    }
    const first = calls.length === 0;
    const take = (limit: number): number => {
      let taken = 0;
      let bytes = 0;
      for (const item of rest.slice(0, limit)) {
        if (!fits(taken + 1, bytes + item.bytes, first ? 1 : 0, first ? RECORD_LIMIT : 0)) {
          break;
        }
        bytes += item.bytes;
        taken += 1;
      }
      return taken;
    };
    // 마지막 몫이 빌지 않게 하나는 남긴다. 남은 하나가 마지막 몫에 들지 않으면 이 몫에 싣고, 마지막 몫은 기록과 색인만 싣는다
    const taken = take(rest.length - 1) || take(1);
    if (taken === 0) {
      const head = rest[0];
      // `!first` 는 뒤 조건과 동치다(첫 몫이 아니면 예약이 0 이라 `taken` 이 0 이면 `fits(1, head.bytes, 0, 0)` 도 거짓이다).
      // 변이 표(`.scratch/design-card-build/probes/upload_plan_mutations.toml`)가 이 줄의 원문을 겨누므로 남긴다
      if (head === undefined || !first || !fits(1, head.bytes, 0, 0)) {
        throw new CommandError(
          "limit",
          `${head?.path ?? ""} 가 한 호출(${String(CALL_PATHS)} 개, ${String(CALL_BYTES)} 바이트)에 들지 않는다`,
        );
      }
      // 첫 파일이 pending 이 든 기록과 함께 들지 않으면 첫 몫은 기록만 싣는다
    }
    calls.push(callOf(rest.slice(0, taken)));
    rest = rest.slice(taken);
  }
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
  const received = record === null ? (artifactSha256?.keys() ?? []) : record.files.keys();
  const firstCanonical = hasCanonicalCard(output.keys()) && !hasCanonicalCard(received);

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
    // 첫 정식 올리기의 tokens.json 은 앞 시도가 목표대로 보냈어도(`sent`) 다시 보낸다. 웹에 옛 이름이 남았을 수 있다
    if (firstCanonical && path === TOKENS_PATH) {
      send.push(path);
    } else if (revert.has(path) || kind === "edited" || kind === "claimed" || kind === "deleted") {
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
      // 지난 산출 목록을 준 산출에 없으면 코드가 뺀 것이라 지운다. 이어 적으면 마지막 기록이 지운 경로를 되살린다
      (input.previousOutput === null ? landed : droppedTargets).push(path);
    }
  }

  // 웹에 이미 없는 경로는 지우는 요청 없이 기록에서만 뺀다
  const gone = [
    ...pendingDelete.filter((path) => state.get(path) === "deleted"),
    ...input.webRemoved,
  ].filter((path) => !output.has(path));
  // 지난 목록에서 온 경로는 기록에 있을 때만 지운다. 기록에 없으면 앞 올리기가 이미 지운 것이다
  const previous = (input.previousOutput ?? []).filter(
    (path) => record === null || record.files.has(path),
  );
  const deletes = [...previous, ...input.webAdded, ...pendingDelete].filter(
    (path) => isRecorded(path) && !output.has(path) && !gone.includes(path),
  );

  const sendPaths = sortedPaths(send);
  const deletePaths = sortedPaths([...deletes, ...droppedTargets]);
  return {
    send: sendPaths,
    landed: sortedPaths(landed),
    unchanged: sortedPaths(unchanged),
    delete: deletePaths,
    gone: sortedPaths(gone),
    ignored: sortedPaths(ignored),
    firstCanonical,
    calls: splitCalls(
      sendPaths.map((path) => ({
        path,
        bytes: output.get(path)?.byteLength ?? 0,
        kind: "send" as const,
      })),
      deletePaths.map((path) => ({ path, bytes: 0, kind: "delete" as const })),
    ),
  };
}

/** 묶음이 있는 산출이 보낼 색인의 `libraries`. 페이지가 jsDelivr 에서 싣는다(형식 설명의 `libraries`). */
const LIBRARIES = [
  { name: "react", version: "18.3.1", global: "React" },
  { name: "react-dom", version: "18.3.1", global: "ReactDOM" },
] as const;

/**
 * 컴포넌트 묶음을 싣는 올리기의 색인을 짓는다(design-card-build 명세 "색인의 `libraries`"). `libraries` 를
 * React·ReactDOM 18.3.1 로 바꾸고 `source` 와 다른 칸은 그대로 둔다. `lastChange` 는 절차가 적는다.
 */
export function withLibraries(index: Readonly<Record<string, unknown>>): Record<string, unknown> {
  return { ...index, libraries: LIBRARIES.map((library) => ({ ...library })) };
}

/**
 * 첫 정식 올리기의 색인을 짓는다(design-card-build 명세 "`upgraded`"). `upgraded` 가 없을 때만 `{at}` 으로 더한다.
 * 페이지의 "No move is perfect" 배너를 거두는 표시다. 다른 칸은 그대로 둔다.
 */
export function withUpgraded(
  index: Readonly<Record<string, unknown>>,
  at: string,
): Record<string, unknown> {
  if (index.upgraded === undefined) {
    return { ...index, upgraded: { at } };
  }
  return { ...index };
}
