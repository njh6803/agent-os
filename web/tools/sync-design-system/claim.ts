/**
 * 기록의 `claim` 을 쓰거나 비운 기록(design-reverse-sync 명세 "겹침"과 그 2026-10-22 주석들, "거꾸로 동기화"의 "티켓"
 * 주석). 기록 명령의 `record claim` 이 부른다. 들이기 뒤의 올리기가 마지막 기록에서 비우는 것은 `sync-record.ts` 의
 * `nextRecord` 다.
 *
 * 쓰는 것은 셋이다. 모두 파일 해시, 기준본, `pending` 을 앞 기록 그대로 둔다.
 *
 * - 새 `claim`. 웹 편집 있음의 확인 보고와 받은 폴더로 짓는다. `claim` 이 없는 기록이나, 사람이 남의 `claim` 을 지우기로
 *   골라 비운 뒤의 기록에 쓴다.
 * - 자기 `claim` 을 고쳐 쓰기. 들이는 중의 확인 보고가 자기 것이면 브랜치, 티켓, 시각을 새로 들고 사본과 해시를 지금
 *   웹으로 다시 쓴다(번호를 옮겨 브랜치와 티켓 경로가 바뀌었다, "웹에서 다시 고친다" 뒤다). 이어받은 기준본은 지킨다.
 *   번호를 옮긴 고쳐 쓰기의 확인 보고는 옛 브랜치를 `--branch` 로 준 것이다(`check-command.ts` 의 지금 브랜치 줄).
 * - 이어받기. 들이는 중의 확인 보고가 남의 것이면 이어받을 기준본(확인 명령이 쓴 파일)이 있어야 한다. 자기 브랜치와
 *   티켓, 지금 웹의 사본과 해시를 들고 그 기준본을 사본과 따로 든다.
 *
 * 고쳐 쓰기와 이어받기는 앞 `claim` 의 파일 목록과 더 고친 몫의 파일을 합친다. 그래서 이어받은 들이기를 병합한 뒤의
 * 올리기 한 번이 둘을 함께 보낸다. 합친 경로마다 웹에 있으면 해시를 지금 웹으로 다시 재고(웹에서 더한 경로였으면
 * 더한 것, 아니면 고친 것), 없으면 지운 것이다. 웹에서 더했다가 다시 지운 경로는 뺀다.
 *
 * 덮을 `claim` 은 입력이고, 기록의 `claim` 이 그것과 다르면 `input` 오류로 멈춘다(그사이 다른 세션이 쓰거나 지웠다).
 * 덮는 것은 셋뿐이다. `claim` 이 없을 때, 자기 `claim` 을 고쳐 쓸 때, 남의 `claim` 을 사람이 지우기로 골랐거나 병합된
 * 남의 `claim` 을 이어받을 때다. 남의 `claim` 을 지우는 것은 비우기이고, 그 뒤에 확인을 다시 돌려 새 `claim` 을 쓴다.
 *
 * 못 보는 것: 남의 `claim` 이 병합되었는지는 보지 않는다. 결정표(`decide.ts`)가 PR 상태로 이어받기를 고른 때만 부른다.
 */

import type { CheckReading, WebEdits } from "./check-report.ts";
import { CommandError } from "./command.ts";
import { fileHash, INDEX_PATH, TOKENS_PATH } from "./file-hash.ts";
import { jsonValue, parseJson, sortedPaths } from "./io.ts";
import { claimJson, indexLists, type Claim, type SyncRecord } from "./sync-record.ts";
import type { JsonValue } from "./tokens-json.ts";

/** 새로 쓰는 `claim` 의 머리. */
export interface ClaimHead {
  readonly branch: string;
  readonly ticket: string;
  readonly at: string;
}

export type ClaimChange =
  | { readonly kind: "clear" }
  | {
      readonly kind: "write";
      readonly head: ClaimHead;
      /** `check judge` 의 보고. 웹 편집 있음이나 들이는 중이다. */
      readonly reading: CheckReading;
      /** 확인이 판정한 받은 폴더의 파일. */
      readonly web: ReadonlyMap<string, Uint8Array>;
      /** 이어받을 기준본. 남의 `claim` 을 이어받을 때만 있다. */
      readonly inherit: JsonValue | null;
    };

export interface ClaimInput {
  /** 쓰기 직전에 다시 받은 기록. */
  readonly current: SyncRecord;
  /** 덮을 `claim`. 확인에 쓴 기록의 것이다. */
  readonly expected: Claim | null;
  readonly change: ClaimChange;
}

/** 두 `claim` 이 같은가. 기록에 쓰는 JSON 으로 견주어 파일 목록의 차례는 가리지 않는다. */
export function sameClaim(left: Claim | null, right: Claim | null): boolean {
  const shown = (claim: Claim | null): string =>
    claim === null ? "null" : JSON.stringify(claimJson(claim));
  return shown(left) === shown(right);
}

function decoded(data: Uint8Array): unknown {
  return parseJson(new TextDecoder().decode(data));
}

/** 받은 폴더의 `tokens.json` 내용. 없으면 null 이고, 풀리지 않으면 `input` 오류다. */
function webTokens(web: ReadonlyMap<string, Uint8Array>): JsonValue | null {
  const data = web.get(TOKENS_PATH);
  if (data === undefined) {
    return null;
  }
  const value = jsonValue(decoded(data));
  if (value === undefined) {
    throw new CommandError("input", `받은 ${TOKENS_PATH} 가 JSON 으로 풀리지 않는다`);
  }
  return value;
}

/** 이번에 `claim` 이 들 파일. 경로마다 웹에서 더한 것이었는지 함께 든다. */
function claimedPaths(previous: Claim | null, edits: WebEdits): Map<string, boolean> {
  const paths = new Map<string, boolean>();
  for (const path of [...(previous?.changed.keys() ?? []), ...(previous?.removed ?? [])]) {
    paths.set(path, false);
  }
  for (const path of [...edits.revert, ...edits.webRemoved]) {
    paths.set(path, paths.get(path) ?? false);
  }
  for (const path of [...(previous?.added.keys() ?? []), ...edits.webAdded]) {
    paths.set(path, true);
  }
  paths.delete(TOKENS_PATH);
  return paths;
}

function claimOf(
  head: ClaimHead,
  web: ReadonlyMap<string, Uint8Array>,
  paths: ReadonlyMap<string, boolean>,
  base: JsonValue | null,
): Claim {
  const changed = new Map<string, string>();
  const added = new Map<string, string>();
  const removed: string[] = [];
  for (const [path, wasAdded] of paths) {
    const data = web.get(path);
    if (data !== undefined) {
      (wasAdded ? added : changed).set(path, fileHash(path, data));
    } else if (!wasAdded) {
      removed.push(path);
    }
  }
  const index = web.get(INDEX_PATH);
  return {
    ...head,
    tokens: webTokens(web),
    changed,
    added,
    removed: sortedPaths(removed),
    index: indexLists(index === undefined ? null : decoded(index)),
    base,
  };
}

function nextClaim(expected: Claim | null, change: Extract<ClaimChange, { kind: "write" }>): Claim {
  const { reading, head, web, inherit } = change;
  switch (reading.result) {
    case "edited":
      if (expected !== null) {
        throw new CommandError(
          "input",
          "웹 편집 있음의 확인 보고인데 덮을 claim 이 있다. 확인에 쓴 기록을 덮을 claim 으로 준다",
        );
      }
      if (inherit !== null) {
        throw new CommandError("usage", "이어받을 기준본은 남의 claim 을 이어받을 때만 준다");
      }
      return claimOf(head, web, claimedPaths(null, reading.edits), null);
    case "importing":
      if (expected === null) {
        throw new CommandError(
          "input",
          "들이는 중의 확인 보고인데 덮을 claim 이 없다. 확인에 쓴 기록을 덮을 claim 으로 준다",
        );
      }
      if (reading.claim.own) {
        if (inherit !== null) {
          throw new CommandError(
            "usage",
            "자기 claim 을 고쳐 쓸 때는 이어받을 기준본을 주지 않는다",
          );
        }
        return claimOf(head, web, claimedPaths(expected, reading.further), expected.base);
      }
      if (inherit === null) {
        throw new CommandError(
          "usage",
          "남의 claim 은 이어받을 기준본(--inherit)이 있을 때만 이어받는다. 지우려면 --clear 로 비운다",
        );
      }
      return claimOf(head, web, claimedPaths(expected, reading.further), inherit);
    default:
      throw new CommandError(
        "usage",
        `확인 결과가 ${reading.result} 라 claim 을 쓰지 않는다. 웹 편집 있음이나 들이는 중의 확인 보고로 쓴다`,
      );
  }
}

/** `claim` 을 쓰거나 비운 기록. 기록의 `claim` 이 덮을 `claim` 과 다르면 `input` 오류다. */
export function claimedRecord(input: ClaimInput): SyncRecord {
  const { current, expected, change } = input;
  if (!sameClaim(current.claim, expected)) {
    const now = current.claim === null ? "없다" : `${current.claim.branch} 의 것이다`;
    throw new CommandError(
      "input",
      `기록의 claim 이 덮을 claim 과 다르다(지금 기록의 claim 은 ${now}). 그사이 다른 세션이 쓰거나 지웠으니 확인부터 다시 한다`,
    );
  }
  return {
    ...current,
    claim: change.kind === "clear" ? null : nextClaim(expected, change),
  };
}
