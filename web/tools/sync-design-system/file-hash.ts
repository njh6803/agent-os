/**
 * 파일 종류마다 맞대는 값과 기록에 드는 경로. 기록의 해시, `pending` 의 목표 해시, 확인이 모두 이 모듈로 잰다
 * (design-reverse-sync 명세 "기록"의 2026-10-22 주석의 넷째, "맞대는 것"의 2026-10-22 주석). `claim` 의 해시(06)도
 * 이 함수를 쓴다.
 *
 * - `project/tokens.json` 은 맞대는 몫을 정규 꼴로 적은 것의 sha256(`tokens-json.ts` 의 `comparisonHash`)이다.
 *   그래서 페이지가 꼴만 다시 쓴 파일은 값이 같다. JSON 으로 풀리지 않으면 바이트의 sha256 이다.
 * - 뿌리 README(`project/README.md`)는 페이지가 저장할 때 붙이는 생성 몫을 뗀 사람 몫의 sha256 이다. 페이지는 뿌리
 *   README 에만 생성 몫을 붙이고 그 README 만 사람 몫으로 견준다.
 * - 나머지는 바이트의 sha256 이다.
 *
 * 경로는 아티팩트의 경로(`project/` 로 시작한다)다. 기록에 들지 않는 것은 기록 자신, 색인(목록만 따로 적는다),
 * 페이지가 저장할 때마다 다시 짓는 파일(`tokens.css`, `api/` 의 생성 카드, `manifest.json`), `project/` 밖이다.
 *
 * 페이지 쪽 판정(사람 몫 가르기, 생성 카드의 경로)은 Design System 형식 판 1792564314-af13 의 `artifact-type/app.js`
 * 에서 옮겼고, 디자인 시스템 아티팩트의 판 1792715827-ef57 에서 받은 `app.js` 에서도 같은 것을 손으로 봤다(2026-10-26.
 * 받은 사본의 sha256 과 찾은 문구는 일지 2026-10-27-01 의 "셀프 리뷰" 절).
 * 페이지가 생성 머리나 생성 카드의 경로를 바꾸면, 모든 README 가 웹 편집으로 보이거나 생성 카드가 기록에 든다. 그때
 * 그 판의 `app.js` 에서 `Read this README first` 와 `api\/(?:icons` 를 찾아 다시 옮긴다.
 */

import { createHash } from "node:crypto";
import { comparisonHash, readTokens } from "./tokens-json.ts";

export const RECORD_PATH = "project/sync-record.json";
export const TOKENS_PATH = "project/tokens.json";
export const INDEX_PATH = "project/design-system.json";
export const README_PATH = "project/README.md";

const PROJECT = "project/";

/** 페이지가 저장할 때마다 다시 짓는 파일. `project/` 를 뗀 경로로 본다. */
const GENERATED_CARD = /^api\/(?:icons\.md|tokens\.md|(?:tokens|components|assets)\/[^/]+\.md)$/;
const PAGE_BUILT = ["tokens.css", "manifest.json"];

/** 기록에 드는 경로인가. */
export function isRecorded(path: string): boolean {
  if (!path.startsWith(PROJECT) || path === RECORD_PATH || path === INDEX_PATH) {
    return false;
  }
  const inProject = path.slice(PROJECT.length);
  return !PAGE_BUILT.includes(inProject) && !GENERATED_CARD.test(inProject);
}

const CONSUMING = "## Consuming this system (generated — do not edit)";
const QUICK_START = "## Quick start (generated from tokens.json — do not edit)";
const READ_FIRST =
  "Read this README first; the manifest below lists the files to read and every asset — read tokens.css or components/bundle.js only if the page you build uses them, and read_asset an asset id only if you need that asset.";

function escaped(text: string): string {
  return text.replace(/[.*+?^$(){}|[\]\\]/g, "\\$&");
}

const SEPARATOR = "\\r?\\n\\r?\\n---\\r?\\n\\r?\\n";
const FENCE = "```";
const HEADS = `${escaped(CONSUMING)}|${escaped(QUICK_START)}`;
const MANIFEST_BLOCK = `${FENCE}json\\r?\\n\\{\\s*"manifestVersion"`;
/** 구분선 뒤나 파일 머리의 생성 머리. */
const HEAD_AT = new RegExp(`(?:${SEPARATOR}|^)(?:${HEADS})`);
/** 읽기 안내나 manifest 블록 앞의 구분선. 그 뒤가 생성 몫으로 끝나는지는 따로 본다. */
const TAIL_SEPARATOR = new RegExp(`${SEPARATOR}(?=${escaped(READ_FIRST)}|${MANIFEST_BLOCK})`, "g");
const MANIFEST = new RegExp(MANIFEST_BLOCK);
const GENERATED_NEXT = new RegExp(
  `${SEPARATOR}(?:${HEADS}|${escaped(READ_FIRST)}|${MANIFEST_BLOCK})`,
);

/** manifest 블록 뒤가 비었거나 다시 생성 몫인 구분선의 자리. 없으면 -1. 구분선 후보는 앞의 64 개만 본다. */
function manifestTail(text: string): number {
  let seen = 0;
  for (const match of text.matchAll(TAIL_SEPARATOR)) {
    seen += 1;
    if (seen > 64) {
      break;
    }
    const block = text.indexOf(`${FENCE}json`, match.index);
    if (
      block === -1 ||
      block - match.index > 600 ||
      !MANIFEST.test(text.slice(block, block + 64))
    ) {
      continue;
    }
    const close = text.indexOf(`\n${FENCE}`, block + 8);
    if (close === -1) {
      continue;
    }
    const rest = text.slice(close + 1 + FENCE.length);
    if (rest.trim() === "" || GENERATED_NEXT.test(rest)) {
      return match.index;
    }
  }
  return -1;
}

/** README 의 사람 몫. 생성 몫이 시작하는 가장 앞의 자리에서 자르고, 생성 몫이 없으면 글 그대로다. */
export function humanPart(text: string): string {
  const cuts = [HEAD_AT.exec(text)?.index ?? -1, manifestTail(text)].filter((at) => at !== -1);
  return cuts.length === 0 ? text : text.slice(0, Math.min(...cuts));
}

/** 바이트의 sha256(16 진수). */
export function sha256(bytes: Uint8Array): string {
  return createHash("sha256").update(bytes).digest("hex");
}

/** JSON 글을 푼다. 풀리지 않으면 undefined. */
export function parseJson(text: string): unknown {
  try {
    const parsed: unknown = JSON.parse(text);
    return parsed;
  } catch {
    return undefined;
  }
}

/** 파일의 맞대는 값(16 진수 64 자). */
export function fileHash(path: string, bytes: Uint8Array): string {
  if (path === TOKENS_PATH) {
    const parsed = parseJson(new TextDecoder().decode(bytes));
    if (parsed !== undefined) {
      return comparisonHash(readTokens(parsed));
    }
  }
  if (path === README_PATH) {
    return sha256(new TextEncoder().encode(humanPart(new TextDecoder().decode(bytes))));
  }
  return sha256(bytes);
}
